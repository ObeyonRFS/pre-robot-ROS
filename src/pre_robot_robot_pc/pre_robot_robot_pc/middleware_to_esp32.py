import json
import threading
import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from nav_msgs.msg import Odometry
import serial


#this script must be shipped in setup.py too...sadly
# import ports_finder


class MiddlewareNode(Node):

    def __init__(self):
        super().__init__('middleware_serial_comunicator')
        self.esp32_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        if self.esp32_serial.is_open:
            self.get_logger().info(f'Serial port {self.esp32_serial.port} opened successfully.')
        else:
            self.get_logger().error(f'Failed to open serial port {self.esp32_serial.port}.')

        self.subscription = self.create_subscription(
            String,
            'pre_robot/serial/inject',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        # self.odom_pub = self.create_publisher(Odometry, 'pre_robot/odom', 10)
        # self.timer = self.create_timer(0.1, self.timer_callback)

        self.read_serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.read_serial_thread.start()
        

    def listener_callback(self, msg):
        self.get_logger().info('Recevied from Publisher: "%s"' % msg.data)
        # Send to ESP32 via serial
        try:
            with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
                ser.write((msg.data + '\n').encode('utf-8'))
                self.get_logger().info(f'Sent to ESP32: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Error opening/writing to serial port: {e}')

    def read_serial(self):
        while rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if not line:
                    continue
                data=json.loads(line)
                self.get_logger().info(f'Received from ESP32: {data}')
            except Exception as e:
                print(e)
                continue
            # try:
            #     if self.esp32_serial.in_waiting > 0:
            #         line = self.esp32_serial.readline().decode('utf-8').rstrip()
            #         if line:
            #             self.get_logger().info(f'Received from ESP32: "{line}"')
            #             # Process the received line (assuming it's JSON formatted for Odometry)
            #             try:
            #                 data = json.loads(line)
            #                 odom_msg = Odometry()
            #                 # Fill in the odom_msg fields based on the received data
            #                 # This is a placeholder; actual implementation depends on the data format
            #                 odom_msg.header.stamp = self.get_clock().now().to_msg()
            #                 odom_msg.header.frame_id = "odom"
            #                 odom_msg.child_frame_id = "base_link"
            #                 odom_msg.pose.pose.position.x = data.get('x', 0.0)
            #                 odom_msg.pose.pose.position.y = data.get('y', 0.0)
            #                 odom_msg.pose.pose.position.z = data.get('z', 0.0)
            #                 odom_msg.pose.pose.orientation.x = data.get('qx', 0.0)
            #                 odom_msg.pose.pose.orientation.y = data.get('qy', 0.0)
            #                 odom_msg.pose.pose.orientation.z = data.get('qz', 0.0)
            #                 odom_msg.pose.pose.orientation.w = data.get('qw', 1.0)
            #                 # Publish the Odometry message
            #                 # self.odom_pub.publish(odom_msg)
            #             except json.JSONDecodeError:
            #                 self.get_logger().error(f'Failed to decode JSON from ESP32: "{line}"')
            # except serial.SerialException as e:
            #     self.get_logger().error(f'Serial communication error: {e}')
            #     break
            


def main(args=None):
    rclpy.init(args=args)

    node = MiddlewareNode()

    rclpy.spin(node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()