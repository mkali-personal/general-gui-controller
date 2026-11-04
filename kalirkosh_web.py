"""Fill a Tafnit purchase request from a quote file - web version of kalirkosh.py.

Instead of screenshots, it finds Tafnit's buttons and fields by their fixed internal names (the
HTML ids), through Chrome's remote control (see core/web_controller.py). It runs in its own Chrome
window (a separate Chrome profile), which it opens by itself. Outside the institute, the VPN must
be on.

The names below were read from the real Tafnit screens on 2026-10-29. Steps marked "not checked
yet" were not reached then; if one of them is not found, the script beeps and lets you do that
step by hand.
"""
import sys
import traceback


def exception_handler(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    input("\nPress Enter to exit...")


sys.excepthook = exception_handler

from time import sleep
import winsound

import numpy as np
import pandas as pd

from core.general_gui_controller import pick_file
from core.quote_parsing import load_tabular_data, parse_quote_table
from core.web_controller import (choose, click, connect_to_chrome, exists, fill, open_url, press, read_value,
                                 type_text, upload_file, wait_for, wait_until)
from local_config import REPETETIV_FOOD_ORDER_PATH, TAFNIT_PASSWORD, TAFNIT_USER_NAME

TAFNIT_URL = r"https://tafnit.weizmann.ac.il/MENU1/LOGINNoD.CSP"
ROW_PAUSE_SECONDS = 2


def menu_entry(code: str) -> str:
    """Side-menu entry by its menu code (shown in its tooltip). Codes are unique, texts are not:
    'עברית' and 'יזם' appear several times in the menu."""
    return f'css=#dtree a.node:has(font[title^="{code} "])'


def tab(name: str) -> str:
    return f'css=input[name={name}]'


# --- Tafnit element names ------------------------------------------------------------------------
# Side menu: עברית > יזם > עברית > קליטה > (form)
MENU_PATH = ['EBYAZAM', 'YYAZAM', 'YEBYAZAM', 'YYYAZAM']
MENU_SCIENTIFIC = '^WBOKDRSHTAK:DoNotAHD=1'                   # דרישה לרכש
MENU_FOOD = '^WBOKDRSHTAK:MHTD=2,Ifyun2=5,DoNotAHD=1'         # הזמנה כספית שירותים
# Form tabs
TAB_ITEMS, TAB_NOTES, TAB_SUPPLIER, TAB_ATTACHMENTS = tab('ITEMS'), tab('REMARKS'), tab('SUPPLIER'), tab('NISPAH')
SUPPLIER_LOOKUP = 'css=#sSPK'                                  # the "open window" button of ספק
# Attachments tab > שרותי ארכיב panel > upload window
ARCHIVE_SERVICES = tab('BOpenArchiveUtilWin')
DOCUMENT_DESCRIPTION = 'css=#DESC'                             # תאור מסמך
UPLOAD_TO_SERVER = tab('BUploadFile')                          # העלאה לשרת (opens the upload window)
UPLOAD_FILE_FIELD = 'css=input[type=file]'                     # behind בחר קובץ
UPLOAD_APPROVE = tab('FUP')                                    # אישור
# Notes tab
WEIGHT_ESTIMATION = 'css=#SpecialRemarks1'                     # הערכת מידות ומשקל להזמנה
EXTRA_NOTES = 'css=#SpecialRemarks2'                           # הערות נוספות
# Items tab
ITEM_DESCRIPTION = 'css=#DescLarge'                            # תאור
ITEM_QUANTITY = 'css=#Quan'                                    # כמות
ITEM_PRICE = 'css=#Scm'                                        # מחיר במטבע
ITEM_DISCOUNT = 'css=#Pre'                                     # % הנחה
ITEM_SUPPLIER_ID = 'css=#CatSpk'                               # מק"ט ספק
ITEM_NOTE = 'css=#Remarks'                                     # הערות
UPDATE_ROW = tab('KSVLIN')                                     # עדכן שורה
CATEGORY_FIELDS = ['css=#KitlugFLD0A', 'css=#KitlugFLD0B', 'css=#KitlugFLD0C']   # קטגוריה 1-3
CATEGORIES_SCIENTIFIC = ['Scientific Equipment', 'Laboratory Instruments']
CATEGORIES_FOOD = ['שירותים', 'אירועים, כיבוד, וארוח', 'כיבוד קל']
# Save, and the customs form (customs steps not checked yet)
SAVE = tab('KSAVE')                                            # שמירה
CUSTOMS = tab('KNISCUSTOM')                                    # טופס הצהרה למכס
MANUAL_FORM = 'טופס ידני'
ITEMS_USAGE = 'שימוש'
CUSTOMS_CONFIRM = 'אישור'


def wait_for_tafnit_page() -> None:
    """Tafnit ignores clicks (and shows "טעינת הדף טרם הסתיימה") until its page script has loaded;
    this is the check Tafnit itself uses (PageNotLoadedYet in SCRBrokerHTML5V4.js)."""
    if not wait_until("typeof cspHyperevents !== 'undefined'", timeout=60):
        beep_and_ask("Tafnit is still loading. Wait until the page is ready, then press Enter to continue")


def beep_and_ask(message: str) -> str:
    winsound.Beep(880, 500)
    return input(message)


def stop_if_requested(answer: str) -> None:
    if answer.strip().lower() in ('s', 'e'):
        exit()


# %% Purchase type
scientific_or_food_text = beep_and_ask("If this is a scientific purchase, press s, and if it is a food purchase, press f.\n")
if scientific_or_food_text.lower() == 's':
    scientific = True
elif scientific_or_food_text.lower() == 'f':
    scientific = False
else:
    print("Invalid input. Please enter 's' for scientific or 'f' for food.")
    exit()

# %% Tafnit login
connect_to_chrome()
open_url(TAFNIT_URL)
fill('css=#Username', TAFNIT_USER_NAME, timeout=60)
fill('css=input[name=Password]', TAFNIT_PASSWORD)
press('Enter', 'css=input[name=Password]')

# %% Main menu navigation
# Clicking an open menu entry closes it, so an entry is clicked only if the next one is not shown yet.
wait_for(menu_entry(MENU_PATH[0]), timeout=60)
menu_path = MENU_PATH + [MENU_SCIENTIFIC if scientific else MENU_FOOD]
for code, next_code in zip(menu_path, menu_path[1:]):
    if not exists(menu_entry(next_code)):
        click(menu_entry(code))
        wait_for(menu_entry(next_code), timeout=30)  # sub-menus are loaded only when opened
click(menu_entry(menu_path[-1]))
wait_for(TAB_SUPPLIER, timeout=60)  # exists only on the form, so the check below runs on the new page
wait_for_tafnit_page()

# %% Supplier selection
click(TAB_SUPPLIER)
click(SUPPLIER_LOOKUP)
stop_if_requested(beep_and_ask("Choose the supplier in the Tafnit window that opened, come back here, "
                               "and press Enter to continue or s to stop and exit\n"))

# %% Upload quote
if scientific:
    print("Choose the quote file (e.g. the supplier's PDF).")
    quote_path = pick_file()
else:
    repetitive_food_order = beep_and_ask("Do you want to use the repetitive food orders excel? (y/n)")
    quote_path = REPETETIV_FOOD_ORDER_PATH if repetitive_food_order.lower() == 'y' else pick_file()
quote_path = quote_path.replace('/', '\\')

click(TAB_ATTACHMENTS)
click(ARCHIVE_SERVICES)
fill(DOCUMENT_DESCRIPTION, 'quote')
click(UPLOAD_TO_SERVER)
upload_file(UPLOAD_FILE_FIELD, quote_path, timeout=30)
sleep(2)
# "File already exists on the server" questions are browser messages - the console asks about them.
click(UPLOAD_APPROVE)

# %% Add note
click(TAB_NOTES, timeout=30)
if scientific:
    fill(WEIGHT_ESTIMATION, '30cmX30cmX30cm  5kg')
    beep_and_ask("Put the actual dimensions in Tafnit, then come back here and press Enter to continue")
    click(TAB_ITEMS)
else:
    tomorrow = (pd.Timestamp.now() + pd.Timedelta(days=1)).strftime('%d/%m/%Y')
    fill(EXTRA_NOTES, f'נשמח להזמנה {tomorrow}-ל בשעה 12:30. שם איש קשר - מיכאל קלי. טלפון - 0545952783. '
                      f'איש קשר נוסף: ניב: 0528028099. מכון ויצמן, בניין פיזיקה, כניסה ראשית.')
    beep_and_ask("Put the actual date and contact details in Tafnit, then come back here and press Enter to continue")
    final_note = read_value(EXTRA_NOTES) or ''
    click(TAB_ITEMS)
    fill(ITEM_NOTE, final_note)


# %% Items
def fill_item_row(row) -> None:
    """Fill one item of the quote into the Tafnit item form and update the row."""
    print(row)
    fill(ITEM_DESCRIPTION, row['description'])
    fill(ITEM_QUANTITY, row['quantity'])
    fill(ITEM_PRICE, f"{row['price']:.2f}")
    if row['discount'] is not None and row['discount'] != 0:
        fill(ITEM_DISCOUNT, int(np.round(row['discount'])))
    if not scientific and 'note' in row and pd.notna(row['note']):
        fill(ITEM_NOTE, row['note'])
    if scientific:
        fill(ITEM_SUPPLIER_ID, row['id'])
    # Each category list is filled by Tafnit only after the one before it is chosen.
    for field, option in zip(CATEGORY_FIELDS, CATEGORIES_SCIENTIFIC if scientific else CATEGORIES_FOOD):
        choose(field, option)
    click(UPDATE_ROW)
    # Tafnit warnings that are browser messages are shown in the console by web_controller.


rosh_electroptics_format = False
if scientific:
    rosh_electroptics_format = beep_and_ask(
        "You will now be prompted to choose the csv/excel file containing the items to be ordered.\n"
        "make sure the file has the following columns: ['id', 'description', 'quantity', 'price', 'discount'] (Capitalization of letters does not matter)\n"
        "There is no need to remove strings from the values. that is, No need to change '10 %' to 10 and '250.00 USD' to 250.\n"
        "Notice that in Microsoft Excel you can choose Data -> Get Data -> From file -> From PDF to automaticall import tables from a PDF file to you excel.\n"
        "Before choosing the file, please specify if the file is in rosh electroptics format (y/n): ")
    if rosh_electroptics_format.lower() == 'y':
        rosh_electroptics_format = True
    elif rosh_electroptics_format.lower() == 'n':
        rosh_electroptics_format = False
    else:
        print("Invalid input. Please enter 'y' for rosh electroptics format or 'n' for other formats.")
        exit()
    items_path = pick_file(filetypes=(("CSV and Excel", "*.csv *.xls *.xlsx"),))
else:
    items_path = quote_path

df = load_tabular_data(items_path)
df = parse_quote_table(df, rosh_electroptics_format=rosh_electroptics_format, scientific=scientific)

for _, item_row in df.iterrows():
    fill_item_row(item_row)
    sleep(ROW_PAUSE_SECONDS)

# %% Save and customs form
continue_keyword = beep_and_ask("Would you like to save and continue? press y to save and continue, or n to exit without saving.\n")
if continue_keyword.lower() == 'n':
    exit()
click(SAVE)
sleep(1)
wait_for_tafnit_page()
if scientific:
    click(TAB_ATTACHMENTS, timeout=30)
    click(CUSTOMS)
    click(MANUAL_FORM)
    type_text("optics equipment")
    fill(ITEMS_USAGE, "Will be used to run optics experiments in the physics department. non-military usage")
    click(CUSTOMS_CONFIRM)

for _ in range(3):
    winsound.Beep(880, 500)
    sleep(0.5)
