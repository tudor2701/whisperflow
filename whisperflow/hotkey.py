import time
from typing import Callable

from pynput import keyboard

from .config import CONFIG


class DoubleTapListener:
    """Fires on_toggle when the target key is tapped twice within `window` seconds."""

    def __init__(
        self,
        on_toggle: Callable[[], None],
        target=CONFIG.hotkey,
        window: float = 0.4,
    ):
        self._on_toggle = on_toggle
        self._target = target
        self._window = window
        self._last_press = 0.0
        self._listener: keyboard.Listener | None = None

    def _matches(self, key) -> bool:
        if key == self._target:
            return True
        try:
            if hasattr(key, "char") and hasattr(self._target, "char"):
                return key.char == self._target.char
        except Exception:
            pass
        return False

    def _handle_press(self, key):
        if not self._matches(key):
            return
        now = time.time()
        if now - self._last_press <= self._window:
            self._last_press = 0.0  # reset so a third tap doesn't re-trigger
            try:
                self._on_toggle()
            except Exception as e:
                print(f"[hotkey] on_toggle error: {e}", flush=True)
        else:
            self._last_press = now

    def start(self) -> None:
        self._listener = keyboard.Listener(on_press=self._handle_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
