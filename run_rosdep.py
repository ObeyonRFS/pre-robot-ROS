import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
os.system('colcon build')
os.system('rosdep install -i --from-path src --ignore-src -r --rosdistro jazzy -y')