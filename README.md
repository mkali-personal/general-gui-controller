# General GUI controller
The module uses simple image recognition (cv2.matchTemplate) to find the location of a given image on the screen, and act on it (click, type, paste, etc...). It can be used to automate tasks by locating buttons or other UI elements in applications.
OCR was used but didn't perform well, so it was deprecated.
Since it uses image recognition, it can handle any application, not just web browsers.

To record a patch of the screen, to be searched for later, use the `core.general_gui_controller.record_gui_template` function (or just take a print screen and crop it).

`detect_template` can search for the next types of templates:
1) A simple image (the coordinate of the center of the image is returned).
2) A relative coordinate with respect to a simple image (the coordinate of the center of the image plus the relative offset is returned).
3) A list of images (the location of first one that is found will be used)
4) A complex template\list of complex templates, where first one is being searched for, and then the second image is searched for in the area around the first image. The coordinate of the center of the second image is returned.
5) A sorter to handle multiple detections (e.g., to return the lowest one, or the one closest to a given point).

`detect_template_and_act`:
Combines `detect_template` with a set of actions to be performed when the template is found. Actions can include mouse clicks, keyboard input, waiting for a certain time.

`kalifcode.start_voice_listener`:
Continuously listens for a voice command, and when it hears defined keywords, it runs a corresponding function. - good for work in the lab where the hands are pre-occupied.

### Note:
The directory is organized such that the core of the code is in the `core` folder, while the actual automations files are in the main folder. This is intentional, and allows to run the script from the main folder both from the IDE and directly from the os system, without having to reconfigure the current working directory. 
