@echo off
REM ── Rebuild the executable and (if Inno Setup is present) the installer ────
cd /d "%~dp0"

python -c "import sys" 2>nul
if errorlevel 1 (set PY=py -3) else (set PY=python)

echo === Installing build dependencies ===
%PY% -m pip install --quiet --disable-pip-version-check pypdf pypdfium2 Pillow PyMuPDF pyinstaller
if errorlevel 1 goto fail

echo.
echo === Building the executable ===
%PY% -m PyInstaller --noconfirm "PDF Page Cutter.spec"
if errorlevel 1 goto fail

echo.
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo === Building the installer ===
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
) else (
    echo Inno Setup not found at the default path - skipping installer build.
)

echo.
echo === Done ===
dir /b /s "dist\*.exe" "installer_output\*.exe" 2>nul
echo.
pause
exit /b 0

:fail
echo.
echo *** BUILD FAILED - see the messages above ***
echo.
pause
exit /b 1
