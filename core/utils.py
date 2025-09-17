import os
import time
from typing import Optional
import cv2
import pyperclip
from PIL import ImageGrab
from datetime import datetime


def wait_for_path_from_clipboard(filetype: Optional[str] = None, poll_interval=0.5, verbose=True,
                                 instructions_message=None):
    if instructions_message is not None:
        print(instructions_message + '\n')

    I = 0
    while True:
        clipboard = pyperclip.paste().strip().strip('"')  # Strip whitespace and quotes

        if os.path.isfile(clipboard) or os.path.isdir(clipboard):
            filetype_lower = filetype.lower() if filetype else None

            if filetype_lower in ['video', 'media']:
                # Try to open as a video
                cap = cv2.VideoCapture(clipboard)
                if cap.isOpened():
                    cap.release()
                    if verbose:
                        print(f"✔ Detected valid video path: {clipboard}")
                    return clipboard
                cap.release()

            if filetype_lower in ['image', 'media']:
                # Try to read as an image
                img = cv2.imread(clipboard)
                if img is not None:
                    if verbose:
                        print(f"✔ Detected valid image path: {clipboard}")
                    return clipboard

            if filetype_lower == 'excel':
                if clipboard.endswith('.xlsx') or clipboard.endswith('.xls'):
                    if verbose:
                        print(f"✔ Detected valid CSV path: {clipboard}")
                    return clipboard

            if filetype_lower in ['table', 'tabular']:
                if clipboard.endswith('.csv') or clipboard.endswith('.xlsx') or clipboard.endswith('.xls'):
                    if verbose:
                        print(f"✔ Detected valid table path: {clipboard}")
                    return clipboard

            if filetype_lower in ['folder', 'directory', 'dir']:
                if os.path.isdir(clipboard):
                    if verbose:
                        print(f"✔ Detected valid directory path: {clipboard}")
                    return clipboard

            if filetype is not None:
                if clipboard.endswith(f'.{filetype_lower}'):
                    if verbose:
                        print(f"✔ Detected valid CSV path: {clipboard}")
                    return clipboard

            if filetype is None:
                # No specific filetype validation
                if verbose:
                    print(f"✔ Detected path: {clipboard}")
                return clipboard

        if verbose:
            number_of_dots = I % 3 + 1
            dots = '.' * number_of_dots
            print(f"Waiting for path to be copied{dots}", end="\r")
            I += 1
        time.sleep(poll_interval)


def save_clipboard_image_to_desktop():
    # Get current timestamp
    now = datetime.now()
    current_time = now.strftime("%y%m%d%H%M%S")

    # Grab image from clipboard
    im = ImageGrab.grabclipboard()

    # Get the user's desktop path
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Construct full path for saving the image
    save_path = os.path.join(desktop_path, f"{current_time}.png")

    # Save the image
    if im:
        im.save(save_path)
        print(f"Image saved to: {save_path}")
    else:
        print("No image found in clipboard.")

