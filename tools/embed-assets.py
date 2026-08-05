#!/usr/bin/env python3
"""Inline assets/*.png into index.html as data: URIs.

The page has to stay a single self-contained file: it is published as an
artifact, where a strict CSP blocks every external request, and it is also
opened straight off disk. So the PNGs live in assets/ for editing, and this
script folds them into the page's asset-data block.

Run after tools/build-assets.py.
"""
import base64
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
PAGE = os.path.join(ROOT, "index.html")

FILES = {
    "logo":     "decantx-logo.png",
    "creed":    "creed-absolu-aventus.png",
    "gaultier": "jpg-le-beau-le-parfum.png",
    "delina":   "pdm-delina-exclusif.png",
    "baccarat": "mfk-baccarat-rouge-540.png",
    "basketFront": "basket-front.png",
    "basketBack":  "basket-back.png",
    "cursor":   "hand-cursor.png",
}


def png_size(raw):
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    return struct.unpack(">II", raw[16:24])


data = {}
for key, name in FILES.items():
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        raise SystemExit(f"missing asset: {path}")
    raw = open(path, "rb").read()
    w, h = png_size(raw)
    data[key] = {
        "src": "data:image/png;base64," + base64.b64encode(raw).decode("ascii"),
        "w": w,
        "h": h,
    }

block = json.dumps(data, separators=(",", ":"))

FONT_DIR = os.path.join(ASSETS, "fonts")

# (file, weight, style) — subset to the glyphs the page actually renders
FONTS = [
    ("poppins-400.woff2",  400, "normal"),
    ("poppins-400i.woff2", 400, "italic"),
    ("poppins-600.woff2",  600, "normal"),
    ("poppins-700.woff2",  700, "normal"),
    ("poppins-700i.woff2", 700, "italic"),
]

html = open(PAGE, encoding="utf-8").read()
new, n = re.subn(
    r'(<script id="asset-data" type="application/json">).*?(</script>)',
    lambda m: m.group(1) + block + m.group(2),
    html,
    flags=re.S,
)
if n != 1:
    raise SystemExit("could not find the asset-data block in index.html")

faces, font_bytes = [], 0
for fname, weight, style in FONTS:
    fpath = os.path.join(FONT_DIR, fname)
    raw = open(fpath, "rb").read()
    if raw[:4] != b"wOF2":
        raise SystemExit(f"{fpath} is not a woff2")
    font_bytes += len(raw)
    uri = "data:font/woff2;base64," + base64.b64encode(raw).decode("ascii")
    faces.append(
        '@font-face{font-family:"Poppins";font-style:%s;font-weight:%d;'
        'font-display:swap;src:url(%s) format("woff2")}' % (style, weight, uri)
    )

new, fn = re.subn(
    r"(/\* poppins:start \*/).*?(/\* poppins:end \*/)",
    lambda m: m.group(1) + "".join(faces) + m.group(2),
    new,
    flags=re.S,
)
if fn != 1:
    raise SystemExit("could not find the poppins marker block in index.html")

open(PAGE, "w", encoding="utf-8").write(new)
print(f"embedded {len(FILES)} assets + {len(FONTS)} Poppins faces "
      f"({font_bytes/1024:.1f} KB) -> page is now {len(new)/1024:.0f} KB")
