#!/bin/zsh
set -euo pipefail

SCRIPT_PATH="${0:A}"
DESKTOP_DIR="${SCRIPT_PATH:h}"
ROOT="${DESKTOP_DIR:h}"

if [[ ! -f "$ROOT/outputs/hapa-character-sheet-prototype.html" ]]; then
  echo "Could not find Hapa Character Sheet outputs from $ROOT" >&2
  exit 1
fi

cd "$ROOT/desktop"

if [[ ! -x "node_modules/.bin/electron" ]]; then
  echo "Installing desktop runtime dependencies..."
  npm install
fi

ROUTE="${HAPA_CHARACTER_SHEET_ROUTE:-presentation-hero}"
exec ./node_modules/.bin/electron . --route="$ROUTE"
