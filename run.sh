#!/bin/bash
set -e
cd "$(dirname "$0")"
echo ""
echo "========================================"
echo "       DRAG WEAR IRON — MAC"
echo "========================================"
echo ""
if command -v python3.11 >/dev/null 2>&1; then PYTHON="$(command -v python3.11)"; elif command -v python3 >/dev/null 2>&1; then PYTHON="$(command -v python3)"; else echo "ERROR: Python 3 not found."; exit 1; fi
echo "Python: $PYTHON"
if [ ! -d ".venv" ]; then echo "[1/3] Creating local environment..."; "$PYTHON" -m venv .venv; fi
source .venv/bin/activate
echo "[2/3] Checking dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "[3/3] Starting DRAG WEAR IRON..."
echo "Keep this Terminal window open."
python app.py
