#!/usr/bin/env python3
import subprocess

def run(cmd):
    print(f"\n>>> Running: {cmd}\n")
    subprocess.run(cmd, shell=True, check=True)

def main():
    # 1. Setup sources
    run("sudo apt update && sudo apt install -y software-properties-common curl gnupg lsb-release")
    run("sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key "
        "-o /usr/share/keyrings/ros-archive-keyring.gpg")
    run('echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] '
        'http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | '
        'sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null')

    # 2. Install ROS 2 Jazzy Desktop
    run("sudo apt update")
    run("sudo apt install -y ros-jazzy-desktop")

    # 3. Environment setup
    run('echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc')

    # 4. Build tools & rosdep
    run("sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-vcstool build-essential")
    run("sudo rosdep init || true")  # `|| true` to ignore if already initialized
    run("rosdep update")

    print("\n✅ ROS 2 Jazzy installation complete!")
    print("👉 Restart your terminal or run: source ~/.bashrc")

if __name__ == "__main__":
    main()