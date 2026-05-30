#!/usr/bin/env bash
# Stop WhisperFlow and remove its LaunchAgent.
set -euo pipefail

LABEL="com.whisperflow.agent"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [[ -f "$PLIST" ]]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed LaunchAgent -> $PLIST"
else
  echo "No LaunchAgent found at $PLIST (nothing to do)."
fi
