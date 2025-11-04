from core.general_gui_controller import *
from matplotlib import use
use('TkAgg')
# %%
# record_gui_template(file_name='vpn - Start button - 3840X2160')
# %%
pyautogui.FAILSAFE = False

edge_icon_location = detect_template_and_act('vpn - edge icon', click=True, sleep_after_action=0.5)
pyautogui.hotkey('alt', 'd')
pyautogui.write(r"https://evpn.weizmann.ac.il/my.policy")
sleep(1)
pyautogui.press('enter')

detect_template_and_act('vpn - click here button', click=True, sleep_after_action=1)
pyautogui.press('enter')

detect_template_and_act('vpn - chrome icon', click=True, sleep_after_action=0.5)
pyautogui.hotkey('ctrl', 't')
sleep(0.1)
detect_template_and_act(['vpn - messages icon', 'vpn - messages icon - gray'], click=True, sleep_after_action=0.5)
# input("kaki")
# %%
detect_template_and_act('vpn - WISOTP', click=True, sleep_after_action=0.5)

otp_location = detect_template_and_act(r"vpn - wisotp message", relative_position=(1.2, 0.5), click=False,
                                       multiple_matches_sorter=np.array([0.2, -1]))
pyautogui.doubleClick(otp_location)
pyautogui.hotkey('ctrl', 'c')

# Alt tab tack to edge:
detect_template_and_act(click=True, sleep_after_action=1,
                        override_coordinates=edge_icon_location)  # , override_coordinates=edge_icon_location
pyautogui.hotkey('ctrl', 'v')
pyautogui.press('enter')

detect_template_and_act(r"vpn - Start button", click=True)

