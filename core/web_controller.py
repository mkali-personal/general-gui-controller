"""Control web pages in Chrome through their HTML elements, instead of screenshots.

The web counterpart of general_gui_controller.py. Instead of matching a picture of a button
on the screen, the browser is asked directly for "the button with text X" or "the field next to
the label Y", in every open tab, pop-up window and frame (a page embedded inside a page).
Window size, zoom, theme and screen do not matter, and the window does not need to be in front.

Typical use:
    page = connect_to_chrome()
    open_url("https://...")
    fill('שם משתמש', 'me')
    click('כניסה')

Targets are given as the text you see on the page. A Playwright selector also works when text is
not enough, e.g. 'css=input[type=password]' or 'xpath=//table//input[3]'.

To find out how to name an element, run list_elements() while the page is open, or run
`playwright codegen <url>` in a terminal (it opens a browser and writes code for each click you
make - the web counterpart of record_gui_template).
"""
import socket
import subprocess
import time
import winsound
from pathlib import Path
from typing import Iterator

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Locator, Page, sync_playwright

# Constants
CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
CHROME_DEBUG_PORT = 9222
# Chrome refuses remote control of the everyday profile, so automation runs in its own profile
# folder. Log-ins made there (once) are remembered between runs.
CHROME_PROFILE_DIR = str(Path.home() / "automations-chrome-profile")
DEFAULT_TIMEOUT_SECONDS = 15
RETRY_SLEEP_SECONDS = 0.2
# When an element is not found: True - beep and let the user do that step by hand, then continue.
# False - raise an exception.
ASK_USER_IF_NOT_FOUND = True

SELECTOR_PREFIXES = ('css=', 'xpath=', 'text=', 'id=', 'internal:', '//')
FIELD_TAGS = "self::input[not(@type='hidden') and not(@type='button') and not(@type='submit')] or self::textarea or self::select"
BUTTON_TAGS = "self::button or self::input[@type='button' or @type='submit' or @type='image'] or self::a or self::img"

_playwright = None
_context: BrowserContext | None = None
_page: Page | None = None  # the tab that open_url / press / type_text act on
# Tabs searched besides _page: the pop-up windows opened after connecting (or all tabs, when
# connected without a new tab). Older tabs are left alone, so leftovers of earlier runs are never touched.
_own_pages: list[Page] = []


# --- Connecting -------------------------------------------------------------

def _port_is_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def connect_to_chrome(port: int = CHROME_DEBUG_PORT, profile_dir: str = CHROME_PROFILE_DIR,
                      new_tab: bool = True) -> Page:
    """Connect to the automation Chrome window, starting it first if it is not running.

    Returns the tab that later calls act on (a new tab if new_tab, else the last open one)."""
    global _playwright, _context, _page
    if not _port_is_open(port):
        subprocess.Popen([CHROME_PATH, f'--remote-debugging-port={port}', f'--user-data-dir={profile_dir}',
                          '--no-first-run', '--no-default-browser-check'])
        deadline = time.time() + 20
        while not _port_is_open(port):
            if time.time() > deadline:
                raise TimeoutError(f"[ERROR] Chrome did not open remote-control port {port}.")
            time.sleep(RETRY_SLEEP_SECONDS)

    _playwright = sync_playwright().start()
    browser = _playwright.chromium.connect_over_cdp(f'http://127.0.0.1:{port}')
    _context = browser.contexts[0]
    _context.on('dialog', _handle_dialog)
    _own_pages.clear()
    if not new_tab:
        _own_pages.extend(_context.pages)
    _context.on('page', lambda page: _own_pages.append(page))
    _page = _context.new_page() if new_tab or not _context.pages else _context.pages[-1]
    _page.bring_to_front()
    return _page


def _handle_dialog(dialog) -> None:
    """Browser pop-up messages (alert / confirm / prompt) are shown in the console instead."""
    if dialog.type == 'alert':
        print(f"[PAGE MESSAGE] {dialog.message}")
        dialog.accept()
        return
    winsound.Beep(880, 500)
    answer = input(f"[PAGE ASKS] {dialog.message}\nPress Enter to approve (OK), or n to cancel: ")
    if answer.strip().lower() == 'n':
        dialog.dismiss()
    else:
        dialog.accept()


def current_page() -> Page:
    if _page is None:
        raise RuntimeError("[ERROR] Call connect_to_chrome() first.")
    return _page


def open_url(url: str) -> None:
    current_page().goto(url)


# --- Finding elements -------------------------------------------------------

def _xpath_literal(text: str) -> str:
    return f"'{text}'" if '"' in text else f'"{text}"'


def _next_to_label_xpath(label: str, tags: str) -> str:
    """The first element of the given kind that comes after the visible text `label`."""
    return f"xpath=//*[text()[contains(normalize-space(.), {_xpath_literal(label)})]]/following::*[{tags}][1]"


def _pages() -> list[Page]:
    """The current tab first, then the open pop-up windows, newest first."""
    pages = [p for p in reversed(_own_pages) if p is not _page and not p.is_closed()]
    return [current_page()] + pages


def _text_variants(target: str) -> list[str]:
    """Some old sites (e.g. Tafnit's side menu) store Hebrew text in reversed order, so Hebrew
    targets are also searched for reversed."""
    if any('֐' <= ch <= '׿' for ch in target):
        return [target, target[::-1]]
    return [target]


def _candidate_locators(target: str, kind: str) -> Iterator[Locator]:
    for page in _pages():
        for frame in page.frames:
            if target.startswith(SELECTOR_PREFIXES):
                yield frame.locator(target)
                continue
            texts = _text_variants(target)
            if kind == 'field':
                for text in texts:
                    yield frame.get_by_label(text)
                    yield frame.get_by_placeholder(text)
                    yield frame.locator(_next_to_label_xpath(text, FIELD_TAGS))
            elif kind == 'button_next_to':
                for text in texts:
                    yield frame.locator(_next_to_label_xpath(text, BUTTON_TAGS))
            else:  # 'clickable' or 'text': exact matches first, then partial ones
                for exact in (True, False):
                    for text in texts:
                        yield frame.get_by_role('button', name=text, exact=exact)
                        yield frame.get_by_role('link', name=text, exact=exact)
                        yield frame.get_by_text(text, exact=exact)


def find(target: str, kind: str = 'clickable', timeout: float = DEFAULT_TIMEOUT_SECONDS,
         required: bool = True) -> Locator | None:
    """Wait until an element matching `target` is visible in any tab or frame, and return it.

    kind: 'clickable' (button / link / text), 'field' (text box or drop-down by its label),
    'button_next_to' (the button after a label). If not found within `timeout` seconds: returns
    None when not required, otherwise asks the user (ASK_USER_IF_NOT_FOUND) or raises."""
    deadline = time.time() + timeout
    while True:
        for locator in _candidate_locators(target, kind):
            try:
                visible = locator.filter(visible=True)
                if visible.count() > 0:
                    return visible.first
            except PlaywrightError:
                continue  # frame was navigating or closed while we looked at it
        if time.time() >= deadline:
            break
        time.sleep(RETRY_SLEEP_SECONDS)

    if not required:
        return None
    message = f"Could not find {kind} '{target}' on the page."
    if not ASK_USER_IF_NOT_FOUND:
        raise TimeoutError(f"[ERROR] {message}")
    winsound.Beep(440, 700)
    while True:
        answer = input(f"[NOT FOUND] {message}\n"
                       f"Do this step by hand in Chrome and press Enter to continue, "
                       f"r to search again, or l to list the elements on the page: ").strip().lower()
        if answer == 'l':
            list_elements()
        elif answer == 'r':
            return find(target, kind, timeout, required)
        else:
            return None


def wait_until(js_condition: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> bool:
    """Wait until the JavaScript expression `js_condition` is true in the current tab, e.g. a
    site's own "page finished loading" flag. Returns False if it is still false after `timeout`."""
    deadline = time.time() + timeout
    while True:
        try:
            if current_page().evaluate(f'() => !!({js_condition})'):
                return True
        except PlaywrightError:
            pass  # the page was navigating while we checked
        if time.time() >= deadline:
            return False
        time.sleep(RETRY_SLEEP_SECONDS)


def exists(target: str, timeout: float = 0) -> bool:
    return find(target, 'clickable', timeout=timeout, required=False) is not None


def wait_for(target: str, timeout: float = DEFAULT_TIMEOUT_SECONDS, required: bool = True) -> Locator | None:
    """Wait until the text / element `target` appears."""
    return find(target, 'clickable', timeout=timeout, required=required)


# --- Actions ----------------------------------------------------------------

def click(target: str, next_to: bool = False, timeout: float = DEFAULT_TIMEOUT_SECONDS,
          required: bool = True) -> Locator | None:
    """Click a button / link / text. With next_to=True, click the button that comes after the
    label `target` (e.g. the small "open window" button beside a field)."""
    element = find(target, 'button_next_to' if next_to else 'clickable', timeout, required)
    if element is not None:
        element.click()
    return element


def fill(field: str, value, timeout: float = DEFAULT_TIMEOUT_SECONDS, required: bool = True) -> Locator | None:
    """Put `value` into the text box (or choose it in the drop-down) labelled `field`.
    Existing content is replaced."""
    element = find(field, 'field', timeout, required)
    if element is None:
        return None
    if element.evaluate('e => e.tagName') == 'SELECT':
        element.select_option(label=str(value))
    else:
        element.fill(str(value))
    return element


def choose(field: str, option: str, timeout: float = DEFAULT_TIMEOUT_SECONDS, required: bool = True) -> Locator | None:
    """Choose `option` in the drop-down labelled `field`. Works for real drop-downs and for
    home-made ones (click the field, then click the option text)."""
    element = find(field, 'field', timeout, required)
    if element is None:
        return None
    if element.evaluate('e => e.tagName') == 'SELECT':
        element.select_option(label=option)
    else:
        element.click()
        click(option, timeout=timeout, required=required)
    return element


def read_value(field: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str | None:
    """Return what is currently written in the field labelled `field`."""
    element = find(field, 'field', timeout, required=False)
    return None if element is None else element.input_value()


def upload_file(target: str, path: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
    """Upload `path` through the file field or "choose file" button `target`, without the
    Windows file dialog."""
    element = find(target, 'clickable', timeout)
    if element is None:
        return
    if element.evaluate("e => e.tagName === 'INPUT' && e.type === 'file'"):
        element.set_input_files(path)
        return
    with element.page.expect_file_chooser() as chooser_info:
        element.click()
    chooser_info.value.set_files(path)


def press(key: str, target: str | None = None) -> None:
    """Press a key (e.g. 'Enter', 'Tab', 'Control+A') in the element `target`, or in whatever
    has the keyboard focus in the current tab."""
    if target is None:
        current_page().keyboard.press(key)
    else:
        element = find(target, 'field')
        if element is not None:
            element.press(key)


def type_text(text) -> None:
    """Type `text` into whatever has the keyboard focus."""
    current_page().keyboard.insert_text(str(text))


# --- Inspecting -------------------------------------------------------------

_LIST_ELEMENTS_JS = """() => {
    const visible = e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
    const els = document.querySelectorAll('button, a, input, select, textarea, [onclick], [role=button]');
    return Array.from(els).filter(e => visible(e) && e.type !== 'hidden').map(e => {
        const label = e.labels && e.labels.length ? e.labels[0].innerText : '';
        const text = (e.innerText || e.value || e.alt || '').trim().slice(0, 60);
        return [e.tagName.toLowerCase() + (e.type ? '[' + e.type + ']' : ''), text, label,
                e.name || '', e.id || '', e.placeholder || ''];
    });
}"""


def list_elements() -> None:
    """Print every visible button, link and field in all tabs and frames, to help name targets."""
    for page in _pages():
        print(f"\n=== Tab: {page.title()}  ({page.url})")
        for frame in page.frames:
            try:
                rows = frame.evaluate(_LIST_ELEMENTS_JS)
            except PlaywrightError:
                continue
            if not rows:
                continue
            print(f"--- Frame: {frame.name or frame.url}")
            for tag, text, label, name, element_id, placeholder in rows:
                details = '  '.join(f"{k}={v!r}" for k, v in
                                    [('text', text), ('label', label), ('name', name), ('id', element_id),
                                     ('placeholder', placeholder)] if v)
                print(f"  {tag:<18} {details}")
