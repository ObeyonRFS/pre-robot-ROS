import os
import shutil

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


FIRMWARE_FOLDER = "esp32_firmware"
SKETCH_NAME = "esp32_firmware_binary"
PORT = "/dev/ttyUSB0"

os.chdir(FIRMWARE_FOLDER)

cmd = f"esptool --chip esp32 --port {PORT} --baud 921600 write-flash -z "\
        f"0x1000 ./{SKETCH_NAME}.ino.bootloader.bin " \
        f"0x8000 ./{SKETCH_NAME}.ino.partitions.bin " \
        f"0x10000 ./{SKETCH_NAME}.ino.bin"

os.system(cmd)



# Change working directory to that
# os.chdir(script_dir)
# os.chdir("./MotorController")
# os.chdir("./build/esp32.esp32.esp32da")

# print("Current Directory: ")
# print(os.getcwd())
# print()
# os.system("esptool --chip esp32 --port /dev/ttyUSB0 --baud 921600 write-flash -z 0x1000 ./MotorController.ino.bootloader.bin 0x8000 ./MotorController.ino.partitions.bin 0x10000 ./MotorController.ino.bin")