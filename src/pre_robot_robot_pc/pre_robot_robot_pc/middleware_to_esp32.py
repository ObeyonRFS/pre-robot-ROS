import json
import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from nav_msgs.msg import Odometry
import serial

import asyncio, serial_asyncio, json


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
        self.odom_pub = self.create_publisher(Odometry, 'pre_robot/odom', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        

    def listener_callback(self, msg):
        self.get_logger().info('Recevied from Publisher: "%s"' % msg.data)
        # Send to ESP32 via serial
        try:
            with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
                ser.write((msg.data + '\n').encode('utf-8'))
                self.get_logger().info(f'Sent to ESP32: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Error opening/writing to serial port: {e}')


async def serial_reader(node: MiddlewareNode):
    reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyUSB0', baudrate=115200)
    while True:
        line = await reader.readline()
        try:
            data=json.loads(line.decode('utf-8').strip())
            


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