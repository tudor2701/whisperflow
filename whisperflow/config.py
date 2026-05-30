import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from pynput import keyboard

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _parse_key(name: str):
    name = name.strip().lower()
    special = {
        "alt_r": keyboard.Key.alt_r,
        "alt_l": keyboard.Key.alt_l,
        "ctrl_r": keyboard.Key.ctrl_r,
        "ctrl_l": keyboard.Key.ctrl_l,
        "cmd_r": keyboard.Key.cmd_r,
        "cmd_l": keyboard.Key.cmd_l,
        "shift_r": keyboard.Key.shift_r,
        "shift_l": keyboard.Key.shift_l,
        "f13": keyboard.Key.f13,
        "f14": keyboard.Key.f14,
        "f15": keyboard.Key.f15,
        "f16": keyboard.Key.f16,
        "f17": keyboard.Key.f17,
        "f18": keyboard.Key.f18,
        "f19": keyboard.Key.f19,
    }
    if name in special:
        return special[name]
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    raise ValueError(f"Unknown hotkey: {name}")


@dataclass(frozen=True)
class Config:
    hotkey_name: str
    hotkey: object
    trigger: str
    model_name: str
    sample_rate: int
    language: str | None
    cleanup_enabled: bool
    cleanup_model: str
    anthropic_api_key: str | None


def load_config() -> Config:
    hotkey_name = os.getenv("WHISPERFLOW_HOTKEY", "alt_r")
    trigger = os.getenv("WHISPERFLOW_TRIGGER", "hold").strip().lower()
    if trigger not in ("hold", "double_tap"):
        trigger = "hold"
    return Config(
        hotkey_name=hotkey_name,
        hotkey=_parse_key(hotkey_name),
        trigger=trigger,
        model_name=os.getenv(
            "WHISPERFLOW_MODEL", "mlx-community/whisper-large-v3-mlx"
        ),
        sample_rate=int(os.getenv("WHISPERFLOW_SAMPLE_RATE", "16000")),
        language=os.getenv("WHISPERFLOW_LANGUAGE") or None,
        cleanup_enabled=os.getenv("WHISPERFLOW_CLEANUP", "1") not in ("0", "false", "False"),
        cleanup_model=os.getenv(
            "WHISPERFLOW_CLEANUP_MODEL", "claude-haiku-4-5-20251001"
        ),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )


CONFIG = load_config()
