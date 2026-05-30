# WhisperFlow

Push-to-talk dictation for macOS. Hold a hotkey, speak, release — polished text
gets typed into whatever app you're focused on. 100% local transcription via
`mlx-whisper` (Apple Silicon), optional LLM polishing via Claude Haiku 4.5.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Platform: macOS Apple Silicon](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-black)

## Pipeline

```
Hotkey hold  →  mic capture  →  mlx-whisper (large-v3)
             →  Claude Haiku cleanup  →  Cmd+V into focused app
```

## Requirements

- macOS on Apple Silicon (M1 / M2 / M3 / M4)
- [`uv`](https://docs.astral.sh/uv/) — handles Python 3.12 and all dependencies
  (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- ~3 GB free disk for the Whisper large-v3 model (auto-downloaded on first use)
- Optional: an `ANTHROPIC_API_KEY` for grammar/punctuation cleanup

## Setup

```bash
git clone https://github.com/tudor2701/whisperflow.git
cd whisperflow
uv sync                 # creates the venv and installs everything
cp .env.example .env     # then add your API key — see below
uv run python -m whisperflow
```

<details>
<summary>Prefer plain <code>pip</code> instead of <code>uv</code>?</summary>

A pinned `requirements.txt` is generated from the lockfile:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m whisperflow
```

`uv sync` remains the recommended path — it also pins the Python version.
Regenerate the requirements file after changing dependencies:
`uv export --format requirements-txt --no-hashes --no-emit-project -o requirements.txt`
</details>

The first launch will:

1. Add a 🎤 icon to your menu bar.
2. Download the Whisper model (~3 GB, one-time).
3. Trigger macOS permission prompts.

## API key (for cleanup)

Cleanup polishes grammar and punctuation via Claude. It's **optional** — without
a key you still get raw local transcription.

1. Create a key at <https://console.anthropic.com/> → **API Keys**.
2. Open `.env` and replace the placeholder:

   ```dotenv
   ANTHROPIC_API_KEY=sk-ant-...your-key...
   ```

3. Restart WhisperFlow. The menu bar should show **Cleanup aktiv**.

> Your key lives only in the local, git-ignored `.env`. Never commit it. If a key
> ever leaks, rotate it in the Anthropic console.

## Run continuously (auto-start at login)

WhisperFlow is a menu-bar app, so it keeps running as long as the process is
alive. To make it start automatically at login and restart if it crashes,
install the bundled LaunchAgent:

```bash
./scripts/install-launchagent.sh
```

This generates `~/Library/LaunchAgents/com.whisperflow.agent.plist` with the
correct paths for your machine and loads it. Logs go to
`~/Library/Logs/whisperflow.log`.

To remove it:

```bash
./scripts/uninstall-launchagent.sh
```

> **Permissions note:** macOS ties Microphone / Accessibility / Input Monitoring
> permissions to the launching binary. When launched by `launchctl` instead of
> your terminal, you may be re-prompted on first login — grant them, then run
> `./scripts/install-launchagent.sh` once more.

## Grant macOS permissions

You will need to add **your terminal** (or whatever launches `uv run`) to:

- **System Settings → Privacy & Security → Microphone**
- **System Settings → Privacy & Security → Accessibility**
- **System Settings → Privacy & Security → Input Monitoring**

After granting, quit and relaunch the terminal so the new permissions apply.

## Usage

1. Wait for the menu bar icon to switch from ⏳ to 🎤.
2. Click into any text field.
3. Trigger recording (two modes — pick one via `WHISPERFLOW_TRIGGER`):
   - **Hold** (default): hold the hotkey, speak, release.
   - **Double-tap**: double-tap the hotkey to start, speak, double-tap again to stop.
4. Your transcribed (and optionally polished) text appears at the cursor.

The default hotkey is **Right Option (⌥)** in hold mode. Change both the key and
the mode in `.env` — e.g. double-tap Left Control:

```dotenv
WHISPERFLOW_HOTKEY=ctrl_l
WHISPERFLOW_TRIGGER=double_tap
```

Icon states:

| Icon | Meaning |
|------|---------|
| ⏳ | Loading model |
| 🎤 | Idle, ready |
| 🔴 | Recording |
| ✍️ | Transcribing |
| ✨ | LLM cleanup |
| 📋 | Pasting |

## Configuration

All knobs live in `.env`. See `.env.example` for the full list. Common tweaks:

- Change hotkey: `WHISPERFLOW_HOTKEY=f13`
- Switch trigger mode: `WHISPERFLOW_TRIGGER=double_tap` (or `hold`)
- Force language: `WHISPERFLOW_LANGUAGE=de`
- Skip cleanup: `WHISPERFLOW_CLEANUP=0`
- Smaller model: `WHISPERFLOW_MODEL=mlx-community/whisper-medium-mlx`

## Standalone module tests

```bash
# Mic recording sanity check
uv run python -m whisperflow.recorder

# Text injection sanity check (focus a text field within 3 s)
uv run python -m whisperflow.injector "Hello from WhisperFlow"
```

## Project layout

```
whisperflow/
├── config.py        env + defaults
├── recorder.py      sounddevice mic capture
├── transcriber.py   mlx-whisper wrapper
├── cleaner.py       Claude Haiku 4.5 polish
├── injector.py      clipboard + Cmd+V via Quartz
├── hotkey.py        pynput global push-to-talk listener
├── app.py           rumps menu-bar app + state machine
└── __main__.py      entry point
```

## Out of scope (v1)

- Windows / Linux
- Streaming partial transcripts
- Per-app behaviour
- Signed `.app` bundle
