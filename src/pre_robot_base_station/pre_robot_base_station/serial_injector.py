import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading


class SerialPublisher(Node):

    def __init__(self):
        super().__init__('serial_injector_publisher')
        self.publisher_ = self.create_publisher(String, 'pre_robot/serial/inject', 10)
        self.i = 0

    def publish_text(self, text: str):
        msg = String()
        msg.data = text
        self.publisher_.publish(msg)


def input_loop(node: SerialPublisher):
    while rclpy.ok():   # keeps running until ROS shutdown
        text = input("Enter message: ")
        if text.strip().lower() == "quit":
            rclpy.shutdown()
            break
        node.publish_text(text)
        node.get_logger().info(f'Publishing user input: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = SerialPublisher()

    # Start input thread
    threading.Thread(target=input_loop, args=(node,), daemon=True).start()

    # ROS spinning in main thread
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
