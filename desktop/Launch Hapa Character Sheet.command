#!/bin/zsh
set -euo pipefail

SCRIPT_PATH="${0:A}"
DESKTOP_DIR="${SCRIPT_PATH:h}"

exec "$DESKTOP_DIR/launch-desktop.sh"
