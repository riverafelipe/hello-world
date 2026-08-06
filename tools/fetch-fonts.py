#!/usr/bin/env python3
"""Download the Poppins faces the poster needs, subset to the glyphs it draws.

The artifact CSP blocks font CDNs, so the faces get inlined as data: URIs by
tools/embed-assets.py. Full Poppins is ~150 KB a face; passing `text=` to the
css2 API cuts each one to a few KB, which matters when five faces ride along
inside a single self-contained HTML file.

GLYPHS has to cover everything the page can render, including the sr-only live
region — a missing glyph silently falls back to a system font mid-word.
"""
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "fonts")

# (weight, italic) -> filename stem. Only faces the pages actually set are
# listed: every one of them gets inlined into all three posters, so an unused
# face is dead weight paid for three times over.
FACES = [
    (400, False, "poppins-400"),    # body, and "FLASH SALE"
    (400, True,  "poppins-400i"),   # "ADDED TO CART", the reset chip
    (600, False, "poppins-600"),    # phone status bar
    (700, True,  "poppins-700i"),   # "ADD TO CART"
    (900, False, "poppins-900"),    # "20% OFF"
]

GLYPHS = (
    " !\"#$%&'()*+,-./0123456789:;<=>?@"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "‘’“”–—"   # curly quotes, en/em dash
)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fetch(weight, italic, stem):
    # css2 wants ital,wght pairs sorted; a single face keeps the reply to one block
    axis = f"ital,wght@{1 if italic else 0},{weight}"
    url = ("https://fonts.googleapis.com/css2?family=Poppins:" + axis +
           "&text=" + urllib.parse.quote(GLYPHS, safe="") + "&display=swap")
    css = get(url).decode("utf-8")

    urls = re.findall(r"src:\s*url\((https://[^)]+)\)\s*format\('woff2'\)", css)
    if len(urls) != 1:
        raise SystemExit(f"{stem}: expected 1 woff2 in the reply, got {len(urls)}\n{css}")

    raw = get(urls[0])
    if raw[:4] != b"wOF2":
        raise SystemExit(f"{stem}: server did not return a woff2")

    dest = os.path.join(OUT, stem + ".woff2")
    open(dest, "wb").write(raw)
    print(f"  -> {stem + '.woff2':22s} {len(raw)/1024:6.1f} KB")


os.makedirs(OUT, exist_ok=True)
print(f"fetching {len(FACES)} Poppins faces, subset to {len(GLYPHS)} glyphs:")
for weight, italic, stem in FACES:
    fetch(weight, italic, stem)
