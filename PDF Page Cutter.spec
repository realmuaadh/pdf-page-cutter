# -*- mode: python ; coding: utf-8 -*-
import sys

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

IS_MAC = sys.platform == 'darwin'

# pypdfium2 ships its native binary inside the pypdfium2_raw package; make
# sure it and its version metadata are bundled so page previews work.
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

if IS_MAC:
    # macOS: a one-folder build collected into a proper "PDF Page Cutter.app"
    # bundle, with its own .icns icon and Info.plist.
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='PDF Page Cutter',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe, a.binaries, a.datas,
        strip=False, upx=True, upx_exclude=[], name='PDF Page Cutter',
    )
    app = BUNDLE(
        coll,
        name='PDF Page Cutter.app',
        icon='pdf_cutter.icns',
        bundle_identifier='com.muaadhalhamdi.pdfpagecutter',
        info_plist={
            'CFBundleName': 'PDF Page Cutter',
            'CFBundleDisplayName': 'PDF Page Cutter',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': 'Muaadh Alhamdi',
        },
    )
else:
    # Windows: unchanged single-file .exe.
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
