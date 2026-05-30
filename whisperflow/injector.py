import time

import pyperclip
import Quartz

_KEY_V = 9
_CMD_FLAG = Quartz.kCGEventFlagMaskCommand


def _post_cmd_v() -> None:
    src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateCombinedSessionState)
    down = Quartz.CGEventCreateKeyboardEvent(src, _KEY_V, True)
    up = Quartz.CGEventCreateKeyboardEvent(src, _KEY_V, False)
    Quartz.CGEventSetFlags(down, _CMD_FLAG)
    Quartz.CGEventSetFlags(up, _CMD_FLAG)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def inject(text: str, restore_clipboard: bool = True) -> None:
    if not text:
        return
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = None
    pyperclip.copy(text)
    time.sleep(0.05)
    _post_cmd_v()
    if restore_clipboard and previous is not None:
        time.sleep(0.15)
        try:
            pyperclip.copy(previous)
        except Exception:
            pass


if __name__ == "__main__":
    import sys

    payload = sys.argv[1] if len(sys.argv) > 1 else "Hello from WhisperFlow"
    print(f"Injecting in 3 s: {payload!r}")
    print("Focus a text field now...")
    time.sleep(3)
    inject(payload)
    print("Done.")
