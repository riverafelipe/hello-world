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

html = open(PAGE, encoding="utf-8").read()
new, n = re.subn(
    r'(<script id="asset-data" type="application/json">).*?(</script>)',
    lambda m: m.group(1) + block + m.group(2),
    html,
    flags=re.S,
)
if n != 1:
    raise SystemExit("could not find the asset-data block in index.html")

open(PAGE, "w", encoding="utf-8").write(new)
print(f"embedded {len(FILES)} assets -> {len(block)/1024:.0f} KB of JSON, "
      f"page is now {len(new)/1024:.0f} KB")
