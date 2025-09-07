import rclpy
from rclpy.node import Node

from std_msgs.msg import String
import serial

#this script must be shipped in setup.py too...sadly
# import ports_finder


class MiddlewareNode(Node):

    def __init__(self):
        super().__init__('middleware_serial_comunicator')
        self.subscription = self.create_subscription(
            String,
            'pre_robot/serial/inject',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info('Recevied from Publisher: "%s"' % msg.data)
        # Send to ESP32 via serial
        try:
            with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
                ser.write((msg.data + '\n').encode('utf-8'))
                self.get_logger().info(f'Sent to ESP32: "{msg.data}"')
        except serial.SerialException as e:
            self.get_logger().error(f'Error opening/writing to serial port: {e}')


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MiddlewareNode()

    rclpy.spin(minimal_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()