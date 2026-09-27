#!/bin/bash
# ── Rebuild the macOS app bundle and .dmg ───────────────────────────────────
set -e
cd "$(dirname "$0")"

PY=python3
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: Tkinter is missing. On macOS: brew install python-tk"
    exit 1
fi

echo "=== Installing build dependencies ==="
"$PY" -m pip install --quiet --disable-pip-version-check \
    pypdf pypdfium2 Pillow PyMuPDF pyinstaller

echo
echo "=== Building the icon (pdf_cutter.icns) ==="
"$PY" make_icon_mac.py

echo
echo "=== Building the app bundle ==="
rm -rf build dist
"$PY" -m PyInstaller --noconfirm "PDF Page Cutter.spec"

APP="dist/PDF Page Cutter.app"
if [ ! -d "$APP" ]; then
    echo "*** BUILD FAILED — no .app produced ***"
    exit 1
fi

echo
echo "=== Building the .dmg ==="
mkdir -p installer_output
DMG="installer_output/PDFPageCutter_Mac.dmg"
rm -f "$DMG"
STAGE=$(mktemp -d)
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "PDF Page Cutter" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"

echo
echo "=== Done ==="
echo "App:  $APP"
echo "DMG:  $DMG"
