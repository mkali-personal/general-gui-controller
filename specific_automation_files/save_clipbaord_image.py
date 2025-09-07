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
# %%

from utilities.automations.utils import *
save_clipboard_image_to_desktop()