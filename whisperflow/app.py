import threading
import time
import traceback
from enum import Enum

import rumps

from .cleaner import Cleaner
from .config import CONFIG
from .hotkey import DoubleTapListener, HotkeyListener
from .injector import inject
from .overlay import Overlay
from .recorder import Recorder
from .transcriber import Transcriber


class State(str, Enum):
    LOADING = "Lade Modell…"
    IDLE = "Bereit"
    RECORDING = "Aufnahme"
    TRANSCRIBING = "Transkribiere"
    CLEANING = "Poliere"
    INJECTING = "Einfügen"


_ICON = {
    State.LOADING: "⏳",
    State.IDLE: "🎤",
    State.RECORDING: "🔴",
    State.TRANSCRIBING: "✍️",
    State.CLEANING: "✨",
    State.INJECTING: "📋",
}


class WhisperFlowApp(rumps.App):
    def __init__(self):
        super().__init__("WhisperFlow", title=f"{_ICON[State.LOADING]}", quit_button=None)
        self._state = State.LOADING
        self._state_lock = threading.Lock()
        self._pipeline_lock = threading.Lock()

        self.recorder = Recorder()
        self.transcriber = Transcriber()
        self.cleaner = Cleaner()
        self.overlay = Overlay()

        self._status_item = rumps.MenuItem(f"Status: {self._state.value}")
        _trigger_label = "Doppeltipp" if CONFIG.trigger == "double_tap" else "halten"
        self._hotkey_item = rumps.MenuItem(f"Hotkey: {CONFIG.hotkey_name} ({_trigger_label})")
        self._cleanup_item = rumps.MenuItem(
            "Cleanup aktiv" if CONFIG.cleanup_enabled and self.cleaner.available else "Cleanup aus",
            callback=self.toggle_cleanup,
        )
        self._cleanup_enabled = CONFIG.cleanup_enabled and self.cleaner.available
        self._cleanup_item.state = 1 if self._cleanup_enabled else 0

        self.menu = [
            self._status_item,
            self._hotkey_item,
            None,
            self._cleanup_item,
            None,
            rumps.MenuItem("Beenden", callback=lambda _: rumps.quit_application()),
        ]

        if CONFIG.trigger == "double_tap":
            self.hotkey = DoubleTapListener(on_toggle=self._on_toggle)
        else:
            self.hotkey = HotkeyListener(
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
            )

        # ~25 fps overlay driver — runs on the main thread (UI-safe)
        self._overlay_timer = rumps.Timer(self._overlay_tick, 0.04)
        self._overlay_timer.start()

        threading.Thread(target=self._warmup_async, daemon=True).start()

    def _overlay_tick(self, _timer) -> None:
        if self._state == State.RECORDING:
            self.overlay.show(self.recorder.level)
        else:
            self.overlay.hide()

    def _set_state(self, state: State) -> None:
        with self._state_lock:
            self._state = state
        self.title = _ICON[state]
        self._status_item.title = f"Status: {state.value}"

    def _warmup_async(self) -> None:
        try:
            self.transcriber.warmup()
            self._set_state(State.IDLE)
            self.hotkey.start()
            print(f"[app] ready, hotkey={CONFIG.hotkey_name}", flush=True)
        except Exception as e:
            print(f"[app] warmup failed: {e}", flush=True)
            traceback.print_exc()
            self._set_state(State.IDLE)
            self.hotkey.start()

    def toggle_cleanup(self, sender) -> None:
        if not self.cleaner.available:
            rumps.notification("WhisperFlow", "Cleanup",
                               "Kein ANTHROPIC_API_KEY in .env gesetzt.")
            return
        self._cleanup_enabled = not self._cleanup_enabled
        sender.state = 1 if self._cleanup_enabled else 0
        sender.title = "Cleanup aktiv" if self._cleanup_enabled else "Cleanup aus"

    def _on_hotkey_press(self) -> None:
        if self._state != State.IDLE:
            return
        try:
            self.recorder.start()
            self._set_state(State.RECORDING)
        except Exception as e:
            print(f"[app] recorder start failed: {e}", flush=True)
            traceback.print_exc()

    def _on_hotkey_release(self) -> None:
        if self._state != State.RECORDING:
            return
        threading.Thread(target=self._pipeline, daemon=True).start()

    def _on_toggle(self) -> None:
        # Double-tap: 1st toggle starts recording, 2nd stops + transcribes.
        if self._state == State.IDLE:
            self._on_hotkey_press()
        elif self._state == State.RECORDING:
            self._on_hotkey_release()
        # busy (transcribing/cleaning/injecting) → ignore

    def _pipeline(self) -> None:
        if not self._pipeline_lock.acquire(blocking=False):
            return
        try:
            audio = self.recorder.stop()
            if audio.size < CONFIG.sample_rate * 0.2:
                print("[app] clip too short, ignored", flush=True)
                self._set_state(State.IDLE)
                return

            self._set_state(State.TRANSCRIBING)
            t0 = time.time()
            text = self.transcriber.transcribe(audio)
            t_transcribe = time.time() - t0
            audio_s = audio.size / CONFIG.sample_rate
            print(f"[app] raw: {text!r}  (transcribe {t_transcribe:.1f}s for {audio_s:.1f}s audio)", flush=True)
            if not text:
                self._set_state(State.IDLE)
                return

            if self._cleanup_enabled:
                self._set_state(State.CLEANING)
                try:
                    t1 = time.time()
                    text = self.cleaner.clean(text)
                    print(f"[app] cleaned: {text!r}  (cleanup {time.time() - t1:.1f}s)", flush=True)
                except Exception as e:
                    print(f"[app] cleanup failed: {e}", flush=True)

            self._set_state(State.INJECTING)
            inject(text)
        except Exception as e:
            print(f"[app] pipeline error: {e}", flush=True)
            traceback.print_exc()
        finally:
            self._set_state(State.IDLE)
            self._pipeline_lock.release()
