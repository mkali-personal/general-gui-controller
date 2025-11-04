from core.general_gui_controller import *

SLEEP_BETWEEN_ACTIONS = 0.5
for i in range (1, 32):

    number_filter_position = detect_template_and_act(r"tafnit - number filter.png", relative_position=(0.552, -0.364),
                                                     sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    paste_value(str(i))
    pyautogui.press('enter')
    pyautogui.press('enter')
    sleep(1)
    detect_template_and_act(r"tafnit - first result after search.png", relative_position=(0.71, -1.2),
                            sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"category_1 main.png", relative_position=(-1.340, 0.429),
                            sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"tafnit - category - lo madai", sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    category_2_position = detect_template_and_act(r"tafnit - category 2 - main.png", relative_position=(-0.821, 0.440),
                                                  sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    pyautogui.moveTo(category_2_position[0], category_2_position[1] + 30)
    sleep(SLEEP_BETWEEN_ACTIONS)
    pyautogui.scroll(-3 * 40)
    sleep(SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"tafnit - category 2 - tsorchei misrad", sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"category 3 - main.png", relative_position=(-0.804, 0.571),
                            sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"tafnit - category 3 - different office items", sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act('adken shura', click=True, sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    detect_template_and_act(r"reshimat pritim.png", sleep_after_action=SLEEP_BETWEEN_ACTIONS)
    sleep(5)