import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
os.system('colcon build')
os.system('''
sudo sh -c 'echo "yaml https://raw.githubusercontent.com/ObeyonRFS/pre-robot-ROS/main/rosdep/python.yaml" > /etc/ros/rosdep/sources.list.d/50-pre-robot-custom.list'
''')
os.system('rosdep update')
os.system('rosdep install -i --from-path src --ignore-src -r --rosdistro jazzy -y')