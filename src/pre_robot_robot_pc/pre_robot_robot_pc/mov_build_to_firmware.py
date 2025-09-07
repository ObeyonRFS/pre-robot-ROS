import os
import shutil

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

SKETCTH_NAME = "MotorControllerWithROS"
BUILD_FOLDER = "build/esp32.esp32.esp32da"


FIRMWARE_FOLDER = "esp32_firmware"
NEW_SKETCH_NAME = "esp32_firmware_binary"


for old_filename in os.listdir(os.path.join(SKETCTH_NAME,BUILD_FOLDER)):
    # old_filepath = os.path.abspath(old_filename)
    old_filepath = os.path.join(
        SKETCTH_NAME,
        BUILD_FOLDER,
        old_filename
    )
    new_filename = old_filename.replace(SKETCTH_NAME,NEW_SKETCH_NAME)
    new_filepath = os.path.join(
        FIRMWARE_FOLDER,
        new_filename
    )
    shutil.copy(old_filepath,new_filepath)