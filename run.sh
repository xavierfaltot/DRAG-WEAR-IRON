#!/bin/bash
set -e
cd "$(dirname "$0")"
echo ""
echo "========================================"
echo " DRAG WEAR IRON v0.18 — WEAR IT ALL"
echo "========================================"
echo ""
if command -v python3.11 >/dev/null 2>&1; then PYTHON="$(command -v python3.11)"; elif command -v python3 >/dev/null 2>&1; then PYTHON="$(command -v python3)"; else echo "ERROR: Python 3 not found."; exit 1; fi
echo "Python: $PYTHON"
if [ ! -d ".venv" ]; then echo "[1/3] Creating local environment..."; "$PYTHON" -m venv .venv; fi
source .venv/bin/activate
if python - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3,10) else 1)
PY
then :; else
  echo "Old Python environment detected. Rebuilding .venv..."
  deactivate 2>/dev/null || true
  rm -rf .venv
  "$PYTHON" -m venv .venv
  source .venv/bin/activate
fi
echo "[2/3] Checking dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "[3/3] Starting DRAG WEAR IRON v0.18..."
echo "Keep this Terminal window open."
python app_v018.py
