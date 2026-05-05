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
        self.wheel_radius = (68.55/100/100)/2 #diameter(mm->cm->m)/2
        self.distance_between_wheels = (17.3*2/100) #distance between wheels (cm->m)
        self.distance_wheel_to_base = self.distance_between_wheels/2

        # --- State variables ---
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = time.time()

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
        self.odom_wheel_pub = self.create_publisher(Odometry, 'pre_robot/odom_with_wheel', 10)
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
        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"

        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0

        q = quaternion_from_euler(0, 0, self.theta)
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

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        if dt == 0:
            return

        # Convert RPM to m/s
        v_L = 2 * math.pi * self.wheel_radius * (rpm_L / 60.0)
        v_R = 2 * math.pi * self.wheel_radius * (rpm_R / 60.0)

        # Compute linear and angular velocity
        v = (v_R + v_L) / 2.0
        omega = (v_R - v_L) / (self.distance_wheel_to_base)

        # Integrate position
        self.x += v * math.cos(self.theta) * dt
        self.y += v * math.sin(self.theta) * dt
        self.theta += omega * dt

        # Publish odometry
        self.publish_odometry(v, omega)

    def publish_odometry(self, v, omega):
        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"

        # Position
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        # Orientation
        q = quaternion_from_euler(0, 0, self.theta)
        odom_msg.pose.pose.orientation = Quaternion(
            x=q[0], y=q[1], z=q[2], w=q[3]
        )

        # Velocity
        odom_msg.twist.twist.linear.x = v
        odom_msg.twist.twist.angular.z = omega

        self.odom_wheel_pub.publish(odom_msg)
        self.broadcast_tf()

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
