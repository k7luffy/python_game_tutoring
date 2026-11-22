#!/bin/bash
# Double-click launcher for Python Maze Adventure (macOS / Linux).
# First run creates .venv and installs the packages; later runs start immediately.
set -u
cd "$(dirname "$0")" || exit 1

PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "First run: creating a Python environment (this can take a minute)..."
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found. Install Python 3.10 or newer from python.org and try again."
    read -r -p "Press Enter to close..."
    exit 1
  fi
  python3 -m venv .venv || { echo "Could not create .venv."; read -r -p "Press Enter to close..."; exit 1; }
  "$PY" -m pip install --upgrade pip >/dev/null 2>&1
  if ! "$PY" -m pip install -r game/requirements.txt; then
    echo "Could not install the game packages. Check the internet connection for the first run."
    read -r -p "Press Enter to close..."
    exit 1
  fi
fi

"$PY" game/main.py
status=$?
if [ "$status" -ne 0 ]; then
  echo
  echo "The game stopped with an error (code $status)."
  read -r -p "Press Enter to close..."
fi
exit "$status"
