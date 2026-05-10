import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import threading
import sys, termios, tty, select
import json


class RobotControllerGetchCmdVel(Node):

    def __init__(self):
        super().__init__('robot_controller_getch')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

    def publish_cmd_vel(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z

        self.publisher_.publish(msg)
        self.get_logger().info(
            f'linear={linear_x:.2f}, angular={angular_z:.2f}'
        )


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


def input_loop(node: RobotControllerGetchCmdVel):

    print("WASD to move, SPACE to stop, Q to quit")

    linear = 0.0
    angular = 0.0

    while rclpy.ok():

        key = getch()

        

        if key:

            if key == 'q':
                rclpy.shutdown()
                break

            elif key == 'w':
                linear += 0.09/2

            elif key == 's':
                linear += -0.09/2

            elif key == 'a':
                angular += 0.37/3

            elif key == 'd':
                angular += -0.37/3

            elif key == ' ':
                linear = 0.0
                angular = 0.0

            node.publish_cmd_vel(linear, angular)


def main(args=None):
    rclpy.init(args=args)
    node = RobotControllerGetchCmdVel()

    # Start input thread
    threading.Thread(target=input_loop, args=(node,), daemon=True).start()

    # ROS spinning in main thread
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
