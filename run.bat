@echo off
REM ── PDF Page Cutter — run from source ────────────────────────────────────
REM Installs any missing dependencies, then launches the app.
cd /d "%~dp0"

echo Checking dependencies...
python -c "import sys" 2>nul
if errorlevel 1 (
    py -3 -c "import sys" 2>nul
    if errorlevel 1 (
        echo.
        echo ERROR: Python was not found on this machine.
        echo Install it from https://www.python.org/downloads/ and tick
        echo "Add python.exe to PATH" during setup, then run this file again.
        echo.
        pause
        exit /b 1
    )
    set PY=py -3
) else (
    set PY=python
)

%PY% -m pip install --quiet --disable-pip-version-check pypdf pypdfium2 Pillow PyMuPDF
if errorlevel 1 (
    echo.
    echo WARNING: dependency install failed. Trying to start anyway...
    echo.
)

echo Starting PDF Page Cutter...
%PY% pdf_cutter.py
if errorlevel 1 (
    echo.
    echo The app exited with an error. The message above explains why.
    echo.
    pause
)
