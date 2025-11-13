from core.general_gui_controller import *
from local_config import TAFNIT_PASSWORD, TAFNIT_USER_NAME
SHORT_SLEEP = 0.1

# %%
# record_gui_template('wsos - login logo - 3840X2160')

# %%

detect_template_and_act('vpn - chrome icon', click=True, sleep_after_action=0.5)
detect_template(r"chrome - chrome is opened - 3840X2160")
pyautogui.hotkey('ctrl', 't')
sleep(SHORT_SLEEP)
paste_value(r"https://feinberg.weizmann.ac.il/course/view.php?id=1520")
pyautogui.press('enter')

login_button = detect_template_and_act(r"wsos - login button - 3840X2160", max_waiting_time_seconds=3)
if login_button is not None:
    detect_template(r"wsos - login logo - 3840X2160")
    pyautogui.press('tab')
    paste_value(TAFNIT_USER_NAME)
    pyautogui.press('tab')
    paste_value(TAFNIT_PASSWORD)
    pyautogui.press('tab')
    pyautogui.press('enter')
