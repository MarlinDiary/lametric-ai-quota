#!/bin/sh
set -eu

mkdir -p \
  "$HOME" \
  "$CODEX_HOME" \
  "$CLAUDE_CONFIG_DIR" \
  "$(dirname "$CODEXBAR_CONFIG")"
chmod 700 "$HOME" "$CODEX_HOME" "$CLAUDE_CONFIG_DIR" "$(dirname "$CODEXBAR_CONFIG")"

exec "$@"
