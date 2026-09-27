#!/bin/bash
# ── PDF Page Cutter — run from source (macOS / Linux) ───────────────────────
# Installs any missing dependencies, then launches the app.
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo
    echo "ERROR: Python 3 was not found on this machine."
    echo "Install it from https://www.python.org/downloads/ (or"
    echo "'brew install python-tk' on macOS) and run this script again."
    echo
    exit 1
fi

# macOS's own /usr/bin/python3 ships without Tkinter. If Tk isn't
# importable, tell the person how to fix it instead of failing obscurely.
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo
    echo "ERROR: Python's Tkinter module is missing."
    echo "On macOS, install it with:  brew install python-tk"
    echo "Then run this script again."
    echo
    exit 1
fi

echo "Checking dependencies..."
"$PY" -m pip install --quiet --disable-pip-version-check pypdf pypdfium2 Pillow PyMuPDF || {
    echo
    echo "WARNING: dependency install failed. Trying to start anyway..."
    echo
}

echo "Starting PDF Page Cutter..."
"$PY" pdf_cutter.py
