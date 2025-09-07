import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
import sys, termios, tty, select
import json


class RobotControllerGetch(Node):

    def __init__(self):
        super().__init__('robot_controller_getch')
        self.publisher_ = self.create_publisher(String, 'pre_robot/serial/inject', 10)

    def publish_text(self, text: str):
        msg = String()
        msg.data = text
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing user input: "{msg.data}"')


def getch():
    """Read one character without waiting for Enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)  # raw mode (no Enter needed)
        [i, o, e] = select.select([sys.stdin], [], [], 0.1)
        if i:
            return sys.stdin.read(1)
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def input_loop(node: RobotControllerGetch):
    print("Press keys to send commands. Press 'q' to quit.")
    while rclpy.ok():
        key = getch()
        message={
            "command": "set_motor_speed",
            "parameters": {
                "L": 0,
                "R": 0,
            }
        }
        if key:
            if key == 'q':
                rclpy.shutdown()
                break
            if key == 'a':
                message["parameters"]["L"] = -18
                message["parameters"]["R"] = 18
            if key == 'd':
                message["parameters"]["L"] = 18
                message["parameters"]["R"] = -18
            if key == 'w':
                message["parameters"]["L"] = 24
                message["parameters"]["R"] = 24
            if key == 's':
                message["parameters"]["L"] = -24
                message["parameters"]["R"] = -24
            if key == ' ':
                message["parameters"]["L"] = 0
                message["parameters"]["R"] = 0
            node.publish_text(json.dumps(message))


def main(args=None):
    rclpy.init(args=args)
    node = RobotControllerGetch()

    # Start input thread
    threading.Thread(target=input_loop, args=(node,), daemon=True).start()

    # ROS spinning in main thread
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
