"""Generates a simple scissors-on-red icon as pdf_cutter.ico"""
import struct, zlib, os

def _png(w, h, pixels_rgba):
    def chunk(tag, data):
        c = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    raw = b""
    for row in range(h):
        raw += b"\x00"
        for col in range(w):
            raw += bytes(pixels_rgba[row * w + col][:3])
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend

def make_icon(path="pdf_cutter.ico"):
    sizes = [16, 32, 48, 64, 128, 256]
    pngs = []
    for sz in sizes:
        pixels = []
        for r in range(sz):
            for c in range(sz):
                # Blue background
                bg = [37, 99, 235]
                # White rounded rectangle (document shape)
                margin = sz // 6
                if margin <= r <= sz - margin - 1 and margin <= c <= sz - margin - 1:
                    # Inner cut line (horizontal, mid-height scissors line)
                    mid = sz // 2
                    if abs(r - mid) <= max(1, sz // 20):
                        pixels.append([255, 255, 255])
                    else:
                        pixels.append([255, 255, 255])
                else:
                    pixels.append(bg)
        pngs.append(_png(sz, sz, pixels))

    # ICO format
    count = len(sizes)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + count * 16
    entries = b""
    for i, sz in enumerate(sizes):
        data = pngs[i]
        w = 0 if sz == 256 else sz
        h = 0 if sz == 256 else sz
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        offset += len(data)

    with open(path, "wb") as f:
        f.write(header + entries + b"".join(pngs))

if __name__ == "__main__":
    make_icon()
    print("Icon created: pdf_cutter.ico")
