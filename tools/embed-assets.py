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
# target page: default index.html (v1), or pass one as argv[1]
PAGE = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else "index.html")

FILES = {
    "logo":     "decantx-logo.png",
    "creed":    "creed-absolu-aventus.png",
    "gaultier": "jpg-le-beau-le-parfum.png",
    "delina":   "pdm-delina-exclusif.png",
    "baccarat": "mfk-baccarat-rouge-540.png",
    "basketFront": "basket-front.png",
    "basketBack":  "basket-back.png",
    "cursor":   "hand-cursor.png",
    "atomBlack": "atomizer-black.png",
    "atomGold":  "atomizer-gold.png",
    "atomNavy":  "atomizer-navy.png",
    "atomPink":  "atomizer-pink.png",
    "atomRed":   "atomizer-red.png",
    # v3's unbranded flacons: photographic, supplied pre-cut
    "pSmoked":  "photo-bottle-smoked.png",
    "pNavy":    "photo-bottle-navy.png",
    "pOval":    "photo-bottle-oval.png",
    "pAmber":   "photo-bottle-amber.png",
}


def png_size(raw):
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    return struct.unpack(">II", raw[16:24])


def asset_uri(path, raw):
    """PNG or SVG -> (data URI, width, height)."""
    if path.endswith(".svg"):
        txt = raw.decode("utf-8")
        m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', txt)
        if not m:
            raise SystemExit(f"{path}: no viewBox to size from")
        w, h = (round(float(m.group(1))), round(float(m.group(2))))
        mime = "image/svg+xml"
    else:
        w, h = png_size(raw)
        mime = "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii")), w, h


page_src = open(PAGE, encoding="utf-8").read()
shell = re.sub(r'<script id="asset-data".*?</script>', "", page_src, flags=re.S)
USED = {k: v for k, v in FILES.items() if re.search(r"\b%s\b" % re.escape(k), shell)}
skipped = sorted(set(FILES) - set(USED))
if skipped:
    print(f"  skipping unreferenced: {', '.join(skipped)}")

data = {}
for key, name in USED.items():
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        raise SystemExit(f"missing asset: {path}")
    raw = open(path, "rb").read()
    uri, w, h = asset_uri(path, raw)
    data[key] = {"src": uri, "w": w, "h": h}

block = json.dumps(data, separators=(",", ":"))

FONT_DIR = os.path.join(ASSETS, "fonts")

# (file, weight, style) — subset to the glyphs the page actually renders.
# Keep in step with FACES in tools/fetch-fonts.py.
FONTS = [
    ("poppins-400.woff2",  400, "normal"),
    ("poppins-400i.woff2", 400, "italic"),
    ("poppins-600.woff2",  600, "normal"),
    ("poppins-700i.woff2", 700, "italic"),
    ("poppins-900.woff2",  900, "normal"),
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
print(f"embedded {len(USED)} assets + {len(FONTS)} Poppins faces "
      f"({font_bytes/1024:.1f} KB) -> page is now {len(new)/1024:.0f} KB")
