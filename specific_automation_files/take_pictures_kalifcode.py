import os
import sys

# Get the directory of the current script
current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)

# Go to the parent of the parent directory
desired_working_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))

# Set it as the current working directory
os.chdir(desired_working_dir)

# Optional: add it to sys.path if you import other modules from there
if desired_working_dir not in sys.path:
    sys.path.insert(0, desired_working_dir)

from utilities.automations.auto_operate_microscope import *
from utilities.automations.kalifcode import *

locations_dict = memorize_locations()
callback_map = {'twenty ten': lambda: take_all_images(ROC=2422, magnification=10, locations_dict=locations_dict),
                'twenty twenty': lambda: take_all_images(ROC=2422, magnification=20, locations_dict=locations_dict),
                'five ten': lambda: take_all_images(ROC=549, magnification=10, locations_dict=locations_dict),
                'five twenty': lambda: take_all_images(ROC=549, magnification=20, locations_dict=locations_dict),
                'exposure one': lambda: insert_exposure_time(1, 0, 0, locations_dict=locations_dict),
                'exposure two': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure to': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure three': lambda: insert_exposure_time(3, 0, 0, locations_dict=locations_dict)}

start_voice_listener(command_map=callback_map)