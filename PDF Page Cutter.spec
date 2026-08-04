# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# pypdfium2 ships pdfium.dll inside the pypdfium2_raw package; make sure the
# binary and its version metadata are bundled so page previews work in the .exe.
pdfium_binaries = collect_dynamic_libs('pypdfium2_raw')
pdfium_datas = collect_data_files('pypdfium2_raw')

# PyMuPDF performs the partial-page redaction; it carries a compiled MuPDF core.
pdfium_binaries += collect_dynamic_libs('pymupdf')

a = Analysis(
    ['pdf_cutter.py'],
    pathex=[],
    binaries=pdfium_binaries,
    datas=pdfium_datas,
    hiddenimports=['pypdfium2', 'pypdfium2_raw', 'PIL.ImageTk', 'PIL._tkinter_finder',
                   'pymupdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PDF Page Cutter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pdf_cutter.ico'],
)
