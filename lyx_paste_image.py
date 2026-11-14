"""Paste the image on the clipboard into the LyX document that is open right now, at LyX's cursor.

  1. If the clipboard holds no image, the script stops and changes nothing.
  2. The image is saved as a png in an "images" folder next to the open .lyx file (made if missing),
     named by the current time, e.g. images/20261114_153012.png.
  3. LyX is told (through the LyX server, see lyx_resize_images.py) to insert a graphics inset with
     that file at its cursor. LyX keeps its cursor while another window has the focus, so the image
     lands where the cursor was when you left LyX.
  4. The image gets the same size as lyx_resize_images.py gives: width 65col% in the PDF, and a
     lyxscale that shows it about LYX_DISPLAY_WIDTH_PIXELS wide on screen.
The document is not saved - the insert is an ordinary change in LyX that can be undone with Ctrl+Z.
"""
import os
from datetime import datetime

from PIL import Image, ImageGrab

from lyx_resize_images import PDF_WIDTH, lyxscale_for, open_lyx_document, send_lyx_command

IMAGES_FOLDER_NAME = 'images'


def unique_image_path(folder: str) -> str:
    """A path in `folder` named by the current time, with a counter added if that name is taken."""
    stem = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(folder, f'{stem}.png')
    counter = 2
    while os.path.exists(path):
        path = os.path.join(folder, f'{stem}_{counter}.png')
        counter += 1
    return path


def main() -> None:
    image = ImageGrab.grabclipboard()  # an Image, a list of copied file paths, or None
    if not isinstance(image, Image.Image):
        print("No image on the clipboard - nothing was done.")
        return

    lyx_file, _ = open_lyx_document()
    print(f"Open LyX document: {lyx_file}")
    images_folder = os.path.join(os.path.dirname(lyx_file), IMAGES_FOLDER_NAME)
    os.makedirs(images_folder, exist_ok=True)
    image_path = unique_image_path(images_folder)
    image.save(image_path)
    print(f"Image saved to: {image_path}")

    # LyX reads 'filename' up to the end of the line (so paths with spaces work), and a server
    # command must be one line - so the filename goes last. LyX saves it relative to the document.
    params = [f'width {PDF_WIDTH}']
    scale = lyxscale_for(image_path)
    if scale is not None:
        params.append(f'lyxscale {scale}')
    params.append(f"filename {image_path.replace(os.sep, '/')}")
    send_lyx_command('inset-insert', 'graphics ' + ' '.join(params))
    print("Image inserted at LyX's cursor.")


if __name__ == '__main__':
    main()
