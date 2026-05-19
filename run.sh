#!/usr/bin/env bash
# Run from anywhere: bash /path/to/Task1_Re5/run.sh
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium
python terminal_main.py
