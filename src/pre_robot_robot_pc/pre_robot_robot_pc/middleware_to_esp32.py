import json
import threading
import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from nav_msgs.msg import Odometry
import serial


class MiddlewareNode(Node):
    def __init__(self):
        super().__init__('middleware_serial_communicator')

        # --- Open Serial Port Once ---
        try:
            self.esp32_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            self.get_logger().info(f'Serial port {self.esp32_serial.port} opened successfully.')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.esp32_serial = None

        # --- ROS2 Subscribers & Publishers ---
        self.subscription = self.create_subscription(
            String,
            'pre_robot/serial/inject',
            self.listener_callback,
            10
        )

        # Example publisher (if you want to publish decoded serial messages)
        self.odom_pub = self.create_publisher(Odometry, 'pre_robot/odom', 10)

        # --- Serial Reading Thread ---
        self.read_serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.read_serial_thread.start()

    # --- Send message from ROS to Serial ---
    def listener_callback(self, msg):
        if not self.esp32_serial or not self.esp32_serial.is_open:
            self.get_logger().error('Serial port not available.')
            return

        data_to_send = (msg.data + '\n').encode('utf-8')
        try:
            self.esp32_serial.write(data_to_send)
            self.get_logger().info(f'Sent to ESP32: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to write to serial: {e}')

    # --- Read Serial Data in Background Thread ---
    def read_serial(self):
        if not self.esp32_serial:
            return

        while rclpy.ok():
            try:
                if self.esp32_serial.in_waiting > 0:
                    line = self.esp32_serial.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    self.get_logger().info(f'Received raw: "{line}"')

                    try:
                        data = json.loads(line)
                        self.get_logger().info(f'Parsed JSON from ESP32: {data}')
                        self.publish_odometry(data)
                    except json.JSONDecodeError:
                        self.get_logger().warn(f'Non-JSON message: "{line}"')

            except serial.SerialException as e:
                self.get_logger().error(f'Serial error: {e}')
                break
            except Exception as e:
                self.get_logger().error(f'Unexpected error: {e}')
                continue

    # --- Example function to convert received JSON into Odometry message ---
    def publish_odometry(self, data):
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"

        msg.pose.pose.position.x = data.get('x', 0.0)
        msg.pose.pose.position.y = data.get('y', 0.0)
        msg.pose.pose.position.z = data.get('z', 0.0)
        msg.pose.pose.orientation.x = data.get('qx', 0.0)
        msg.pose.pose.orientation.y = data.get('qy', 0.0)
        msg.pose.pose.orientation.z = data.get('qz', 0.0)
        msg.pose.pose.orientation.w = data.get('qw', 1.0)

        self.odom_pub.publish(msg)

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
