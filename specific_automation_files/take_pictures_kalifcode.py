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
callback_map = {'twenty ten': lambda: take_all_images(magnification=10, side=2422, locations_dict=locations_dict),
                'twenty twenty': lambda: take_all_images(magnification=20, side=2422, locations_dict=locations_dict),
                'five ten': lambda: take_all_images(magnification=10, side=549, locations_dict=locations_dict),
                'five twenty': lambda: take_all_images(magnification=20, side=549, locations_dict=locations_dict),
                'convex ten': lambda: take_all_images(magnification=10, side='Convex', locations_dict=locations_dict),
                'convex twenty': lambda: take_all_images(magnification=20, side='Convex', locations_dict=locations_dict),
                'concave ten': lambda: take_all_images(magnification=10, side='Concave', locations_dict=locations_dict),
                'concave twenty': lambda: take_all_images(magnification=20, side='Concave', locations_dict=locations_dict),
                'change window': lambda: alt_tab,
                'zoom in': lambda: zoom_in(3),
                'zoom out': lambda: zoom_in(-3),
                'exposure one': lambda: insert_exposure_time(1, 0, 0, locations_dict=locations_dict),
                'exposure two': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure to': lambda: insert_exposure_time(2, 0, 0, locations_dict=locations_dict),
                'exposure five': lambda: insert_exposure_time(5, 0, 0, locations_dict=locations_dict),
                'exposure four': lambda: insert_exposure_time(5, 0, 0, locations_dict=locations_dict),
                'exposure three': lambda: insert_exposure_time(3, 0, 0, locations_dict=locations_dict)}

start_voice_listener(command_map=callback_map)