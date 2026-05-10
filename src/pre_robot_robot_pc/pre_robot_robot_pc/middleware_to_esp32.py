import json
import threading
import time
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion
import serial
# from tf_transformations import quaternion_from_euler  # available in ROS tf-transformations
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


import math

def quaternion_from_euler(roll, pitch, yaw):
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return (qx, qy, qz, qw)



class MiddlewareNode(Node):
    def __init__(self):
        super().__init__('middleware_serial_communicator')

        # --- Robot constants ---
        self.wheel_radius = (68.55/10/100)/2 #diameter(mm->cm->m)/2
        self.distance_between_wheels = (17.3*2/100) #distance between wheels (cm->m)
        self.distance_wheel_to_base = self.distance_between_wheels/2

        # --- State variables ---
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now().nanoseconds / 1e9

        self.left_wheel_rotation = 0 #in radian
        self.right_wheel_rotation = 0 #in radian

        # --- Serial setup ---
        try:
            self.esp32_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            self.get_logger().info(f'Serial port {self.esp32_serial.port} opened successfully.')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.esp32_serial = None

        # --- ROS setup ---
        self.serial_injection_subscription = self.create_subscription(
            String,
            'pre_robot/serial/inject',
            self.serial_injection_listener_callback,
            10
        )
        #ros2 topic echo /pre_robot/odom_with_wheel
        self.odom_wheel_pub = self.create_publisher(Odometry, 'pre_robot/odom_with_wheel', 10)
        #ros2 topic pub /pre_robot/reset_odom std_msgs/msg/String "{}" -1
        self.reset_odom_value_sub = self.create_subscription(
            String,
            'pre_robot/reset_odom',
            self.reset_odom_callback,
            10
        )
        # self.set_robot_vel_subscription = self.create_subscription(
        #     String,
        #     'pre_robot/set_robot_vel',
        #     self.set_robot_vel_callback,
        #     10
        # )

        # --- Serial reading thread ---
        self.read_serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.read_serial_thread.start()

        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)
        self.broadcast_static_transforms()

    def broadcast_static_transforms(self):
        #base_footprint -> base_link
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "base_footprint"
        t.child_frame_id = "base_link"
        t.transform.translation.x = 9.7/100
        t.transform.translation.y = 0.0
        t.transform.translation.z = 14/100
        q = quaternion_from_euler(0, 0, 0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.static_tf_broadcaster.sendTransform(t)

        #base_link -> caster_wheel_link
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "base_link"
        t.child_frame_id = "caster_wheel_link"
        t.transform.translation.x = 10.5/100
        t.transform.translation.y = 0.0
        t.transform.translation.z = -14/100+self.wheel_radius
        q = quaternion_from_euler(0, 0, 0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.static_tf_broadcaster.sendTransform(t)

        #base_link -> laser_link
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "base_link"
        t.child_frame_id = "laser_link"
        t.transform.translation.x = -2.4/100
        t.transform.translation.y = 0.0
        t.transform.translation.z = 12.0/100
        q = quaternion_from_euler(0, 0, 0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.static_tf_broadcaster.sendTransform(t)

    # ----------------------------------------------------------
    # ROS2 -> ESP32
    # ----------------------------------------------------------
    def serial_injection_listener_callback(self, msg):
        if not self.esp32_serial or not self.esp32_serial.is_open:
            self.get_logger().error('Serial port not available.')
            return

        try:
            self.esp32_serial.write((msg.data + '\n').encode('utf-8'))
            self.get_logger().info(f'Sent to ESP32: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to write to serial: {e}')
    

    # ----------------------------------------------------------
    # ESP32 -> ROS2
    # ----------------------------------------------------------
    def read_serial(self):
        if not self.esp32_serial:

            return

        while rclpy.ok():
            try:
                if self.esp32_serial.in_waiting > 0:
                    line = self.esp32_serial.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if data.get("feedback_type") == "motor_rpm":
                        self.process_motor_feedback(data["data"])

            except Exception as e:
                self.get_logger().error(f'Serial read error: {e}')
                continue


    def broadcast_tf(self):
        #odom -> base_footprint
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_footprint"
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        q = quaternion_from_euler(0, 0, self.theta)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

        #base_link -> left_wheel_link
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "base_link"
        t.child_frame_id = "left_wheel_link"
        t.transform.translation.x = -9.7/100
        t.transform.translation.y = +self.distance_between_wheels/2
        t.transform.translation.z = -14/100+self.wheel_radius
        q = quaternion_from_euler(0, self.left_wheel_rotation, 0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

        #base_link -> right_wheel_link
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "base_link"
        t.child_frame_id = "right_wheel_link"
        t.transform.translation.x = -9.7/100
        t.transform.translation.y = -self.distance_between_wheels/2
        t.transform.translation.z = -14/100+self.wheel_radius
        q = quaternion_from_euler(0, self.right_wheel_rotation, 0)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

    # ----------------------------------------------------------
    # Process motor feedback and publish odometry
    # ----------------------------------------------------------
    def process_motor_feedback(self, rpm_data):
        rpm_L = rpm_data.get('L', 0.0)
        rpm_R = rpm_data.get('R', 0.0)
        # Convert RPM (round per minute) to RPS (radian per second)
        rps_L = rpm_L * (2 * math.pi / 60.0) 
        rps_R = rpm_R * (2 * math.pi / 60.0)

        now = self.get_clock().now().nanoseconds / 1e9
        dt = now - self.last_time
        self.last_time = now

        if dt == 0:
            return

        # Convert RPM to m/s
        v_L = rps_L * self.wheel_radius
        v_R = rps_R * self.wheel_radius

        # Compute linear and angular velocity
        v = (v_R + v_L) / 2.0
        # omega = (v_R - v_L) / (self.distance_wheel_to_base)
        # Don't know, in rviz have rotation problem
        # omega = (v_R - v_L) / (self.distance_wheel_to_base) * (4+4/3)
        omega = (v_R - v_L) / self.distance_between_wheels


        # Integrate position
        self.x += v * math.cos(self.theta) * dt
        self.y += v * math.sin(self.theta) * dt
        self.theta += omega * dt
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        self.left_wheel_rotation += rps_L * dt
        self.right_wheel_rotation += rps_R * dt

        # Publish odometry
        self.publish_odometry(v, omega)

    def publish_odometry(self, v, omega):
        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_footprint"

        # Position
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        # Orientation
        q = quaternion_from_euler(0, 0, self.theta)
        odom_msg.pose.pose.orientation = Quaternion(
            x=q[0], y=q[1], z=q[2], w=q[3]
        )

        #Covariance
        odom_msg.pose.covariance = [
            0.01, 0, 0, 0, 0, 0,
            0, 0.01, 0, 0, 0, 0,
            0, 0, 99999.0, 0, 0, 0,
            0, 0, 0, 99999.0, 0, 0,
            0, 0, 0, 0, 99999.0, 0,
            0, 0, 0, 0, 0, 0.05
        ]

        # Velocity
        odom_msg.twist.twist.linear.x = v
        odom_msg.twist.twist.angular.z = omega

        self.odom_wheel_pub.publish(odom_msg)
        self.broadcast_tf()


    def reset_odom_callback(self, msg):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.get_logger().info('Odometry reset.')

    def destroy_node(self):
        if self.esp32_serial and self.esp32_serial.is_open:
            self.esp32_serial.close()
            self.get_logger().info('Serial port closed.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MiddlewareNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('KeyboardInterrupt received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
