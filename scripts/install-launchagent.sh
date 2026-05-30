#!/usr/bin/env bash
# Install WhisperFlow as a macOS LaunchAgent so it starts at login and
# stays running. Re-run this script any time to refresh the configuration.
set -euo pipefail

LABEL="com.whisperflow.agent"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"

UV_BIN="$(command -v uv || true)"
if [[ -z "$UV_BIN" ]]; then
  echo "error: 'uv' not found on PATH. Install it first: https://docs.astral.sh/uv/" >&2
  exit 1
fi
UV_DIR="$(dirname "$UV_BIN")"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${UV_BIN}</string>
    <string>run</string>
    <string>python</string>
    <string>-m</string>
    <string>whisperflow</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${PROJECT_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>${UV_DIR}:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/whisperflow.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/whisperflow.err.log</string>
</dict>
</plist>
PLIST_EOF

# Reload cleanly: unload an old copy if present, then load the new one.
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"

echo "Installed LaunchAgent -> $PLIST"
echo "WhisperFlow is now running and will start automatically at login."
echo "Logs: $LOG_DIR/whisperflow.log"
echo
echo "NOTE: macOS attaches Microphone / Accessibility / Input Monitoring"
echo "permissions to the launching binary. The first login launch may"
echo "re-prompt for these. Grant them, then run this script once more."
