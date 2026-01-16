from core.general_gui_controller import *

# %%

sleep(2)
paste_value(r"https://feinberg.weizmann.ac.il/course/view.php?id=1520")
pyautogui.press('enter')
login_button = detect_template_and_act(r"wsos - login button", sleep_before_detection=2, max_waiting_time_seconds=5)

# asd = record_gui_template(r"asd")