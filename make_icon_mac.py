"""Generates the macOS app icon (pdf_cutter.icns) from the same blue/white
document design as make_icon.py's Windows .ico, plus the red cut line that
appears in the app itself. macOS 11+ applies its own squircle mask and
shadow to app icons, so this stays a plain full-bleed square — no rounded
corners baked in here.

Requires Pillow (already a runtime dependency of the app) and, to assemble
the final .icns, the `iconutil` command line tool that ships with Xcode /
the Command Line Tools (macOS only).
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

BLUE = (37, 99, 235, 255)
WHITE = (255, 255, 255, 255)
RED = (220, 38, 38, 255)

# macOS .iconset needs each of these exact file names.
SIZES = [16, 32, 128, 256, 512]


def draw_icon(size):
    img = Image.new("RGBA", (size, size), BLUE)
    draw = ImageDraw.Draw(img)
    margin = size // 6
    draw.rectangle([margin, margin, size - margin - 1, size - margin - 1], fill=WHITE)
    # A red "cut line" through the document, matching the app's own accent.
    line_h = max(1, size // 24)
    mid = size // 2
    draw.rectangle([margin, mid - line_h // 2, size - margin - 1, mid + line_h // 2], fill=RED)
    return img


def make_icns(out_path="pdf_cutter.icns", iconset_dir="pdf_cutter.iconset"):
    if shutil.which("iconutil") is None:
        print("iconutil not found (needs macOS + Xcode Command Line Tools) — "
              "skipping .icns build.")
        return False

    if os.path.isdir(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir)

    # (filename, pixel size to render at)
    variants = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    for name, px in variants:
        draw_icon(px).save(os.path.join(iconset_dir, name))

    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", out_path], check=True)
    shutil.rmtree(iconset_dir)
    print(f"Icon created: {out_path}")
    return True


if __name__ == "__main__":
    ok = make_icns()
    sys.exit(0 if ok else 1)
