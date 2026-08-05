#!/usr/bin/env python3
"""Key the studio background out of the product shots and tint the logo.

Flood-fill from the corners rather than matching the background colour
globally, so pale parts of a product (the pink Delina, the glass on the
Gaultier) survive even though they're close to white.
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP = os.path.join(ROOT, "assets", "source")
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

MAGIC = (255, 0, 255)


def probe(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    corners = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    print(f"  {os.path.basename(path):16s} {w}x{h} corners={corners}")
    return im


def trim_to_silhouette(im, bg, solid_d, scope="all", margin=3, bottom_frac=0.22):
    """Drop the studio drop-shadow by clipping each row to the product itself.

    A row's real product is the span between its outermost strongly-coloured
    pixels; anything opaque outside that span is shadow. Clipping per row (not
    by colour) keeps interior highlights - white label text, gold specular -
    that a brightness threshold would eat.
    """
    im = im.copy()
    w, h = im.size
    px = im.load()

    def d(c):
        return abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2])

    rows = {}
    for y in range(h):
        lo, hi = None, None
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 40 and d((r, g, b)) >= solid_d:
                if lo is None:
                    lo = x
                hi = x
        if lo is not None:
            rows[y] = (lo, hi)

    if not rows:
        return im
    top, bottom = min(rows), max(rows)
    start = top if scope == "all" else int(bottom - (bottom - top) * bottom_frac)

    for y in range(h):
        if y > bottom:                      # nothing below the product survives
            for x in range(w):
                px[x, y] = px[x, y][:3] + (0,)
            continue
        if y < start or y not in rows:
            continue
        lo, hi = rows[y]
        for x in range(w):
            if x < lo - margin or x > hi + margin:
                px[x, y] = px[x, y][:3] + (0,)
    return im


def cutout(path, out_name, thresh, max_side=560, feather=1.0,
           trim=None, solid_d=300, trim_scope="all"):
    src = Image.open(path)

    # Some sources already ship an alpha channel (or palette transparency).
    # Keying those again would destroy a cutout that is already correct.
    existing = None
    if src.mode in ("RGBA", "LA") or (src.mode == "P" and "transparency" in src.info):
        rgba = src.convert("RGBA")
        a = rgba.getchannel("A")
        lo, hi = a.getextrema()
        if lo < 250:                       # genuinely transparent somewhere
            existing = rgba
            print(f"  {out_name}: source already has alpha (min={lo}), keeping it")

    if existing is not None:
        im = existing.crop(existing.getbbox())
        if max(im.size) > max_side:
            s = max_side / max(im.size)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        dest = os.path.join(OUT, out_name)
        im.save(dest, "PNG", optimize=True)
        print(f"  -> {out_name:22s} {im.width}x{im.height}  "
              f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {im.width/im.height:.3f})")
        return im

    im = src.convert("RGB")
    w, h = im.size

    work = im.copy()
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
               (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)):
        try:
            ImageDraw.floodfill(work, xy, MAGIC, thresh=thresh)
        except ValueError:
            pass

    # opaque wherever the flood didn't reach
    px = work.load()
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] == MAGIC:
                ap[x, y] = 0

    # pull the edge in a hair so no white fringe survives, then soften it
    alpha = alpha.filter(ImageFilter.MinFilter(3))
    if feather:
        alpha = alpha.filter(ImageFilter.GaussianBlur(feather))

    im = im.convert("RGBA")
    im.putalpha(alpha)

    if trim:
        im = trim_to_silhouette(im, trim, solid_d, scope=trim_scope)
        # re-soften the edge the trim just cut
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(0.7))
        im.putalpha(a)

    im = im.crop(im.getbbox())

    if max(im.size) > max_side:
        s = max_side / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)

    dest = os.path.join(OUT, out_name)
    im.save(dest, "PNG", optimize=True)
    kb = os.path.getsize(dest) / 1024
    print(f"  -> {out_name:22s} {im.width}x{im.height}  {kb:6.1f} KB  (ratio {im.width/im.height:.3f})")
    return im


def logo(path, out_name, rgb, max_side=640):
    """Black marks on white -> solid colour with alpha from ink density."""
    im = Image.open(path).convert("L")
    alpha = ImageChops.invert(im)                       # ink -> opaque
    # clip the faint scanner haze in the white field to fully transparent
    alpha = alpha.point(lambda v: 0 if v < 26 else min(255, int((v - 26) * 255 / 210)))
    out = Image.new("RGBA", im.size, rgb + (255,))
    out.putalpha(alpha)
    out = out.crop(out.getbbox())
    if max(out.size) > max_side:
        s = max_side / max(out.size)
        out = out.resize((round(out.width * s), round(out.height * s)), Image.LANCZOS)
    dest = os.path.join(OUT, out_name)
    out.save(dest, "PNG", optimize=True)
    print(f"  -> {out_name:22s} {out.width}x{out.height}  "
          f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {out.width/out.height:.3f})")


print("probe:")
for f in sorted(os.listdir(UP)):
    if f.lower().endswith((".jpg", ".jpeg", ".png")) and "7581" not in f:
        probe(os.path.join(UP, f))

print("\ncutouts:")
# Creed: light-grey seamless, black bottle -> trim the whole height.
cutout(f"{UP}/creed-absolu-aventus.jpeg", "creed-absolu-aventus.png", thresh=38,
       trim=(230, 229, 225), solid_d=300, trim_scope="all")
# Gaultier: already cut out at source.
cutout(f"{UP}/jpg-le-beau-le-parfum.png",  "jpg-le-beau-le-parfum.png", thresh=26)
# Delina: pale pink on white, so key gently and leave the silhouette alone.
cutout(f"{UP}/pdm-delina-exclusif.jpeg", "pdm-delina-exclusif.png",  thresh=20)
# Baccarat: gold cap overlaps the reflection in brightness, so only trim the
# bottom, keyed on the deep red glass.
cutout(f"{UP}/mfk-baccarat-rouge-540.png",  "mfk-baccarat-rouge-540.png", thresh=28,
       trim=(255, 255, 255), solid_d=400, trim_scope="bottom")

print("\nlogo:")
logo(f"{UP}/decantx-logo.jpg",
     "decantx-logo.png", (0, 0, 0))


def recolour_caps(im, target=(221, 140, 69)):
    """The handle pivots ship in magenta; bring them into the orange family
    at their original brightness so they stop reading as a mistake."""
    px = im.load()
    w, h = im.size
    tl = 0.299 * target[0] + 0.587 * target[1] + 0.114 * target[2]
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 20 and b > g + 14 and r > g + 8:
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                k = lum / tl
                px[x, y] = (min(255, int(target[0] * k)),
                            min(255, int(target[1] * k)),
                            min(255, int(target[2] * k)), a)
                n += 1
    print(f"  recoloured {n} magenta pixels on the handle pivots")
    return im


def basket(path, out_name, width=1200):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getbbox())
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im = recolour_caps(im)
    dest = os.path.join(OUT, out_name)
    im.save(dest, "PNG", optimize=True)
    print(f"  -> {out_name:22s} {im.width}x{im.height}  "
          f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {im.width/im.height:.4f})")


def cursor(path, out_name, ink=(234, 139, 69), width=420):
    """Repaint the charcoal outline orange, leaving the white fill alone.
    Blending by darkness keeps the antialiased edge clean."""
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getbbox())
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            t = max(0.0, min(1.0, (255 - lum) / (255 - 70)))
            px[x, y] = (round(255 + (ink[0] - 255) * t),
                        round(255 + (ink[1] - 255) * t),
                        round(255 + (ink[2] - 255) * t), a)
    dest = os.path.join(OUT, out_name)
    im.save(dest, "PNG", optimize=True)
    print(f"  -> {out_name:22s} {im.width}x{im.height}  "
          f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {im.width/im.height:.4f})")


def basket_pair(front_src, back_src, width=1200):
    """The two halves are hand-separated and already registered to each
    other, so they must be cropped and scaled identically or the front
    wires will drift off the back ones."""
    ims = {k: Image.open(p).convert("RGBA") for k, p in
           (("front", front_src), ("back", back_src))}
    boxes = [im.getbbox() for im in ims.values()]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))
    print(f"  shared crop {box}")
    for key, im in ims.items():
        im = im.crop(box)
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im = recolour_caps(im)
        name = f"basket-{key}.png"
        dest = os.path.join(OUT, name)
        im.save(dest, "PNG", optimize=True)
        print(f"  -> {name:22s} {im.width}x{im.height}  "
              f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {im.width/im.height:.4f})")


print("\nbasket + cursor:")
basket_pair(f"{UP}/basket-front.png", f"{UP}/basket-back.png")
cursor(f"{UP}/hand-cursor.png", "hand-cursor.png")



def cutout_atomizer(path, out_name, t=22, min_run=8, margin=40,
                    max_side=460, feather=0.8):
    """Key an atomizer off the studio seamless.

    A global flood fill can't do these: the pink one's edge stands only ~28
    off the background, which itself drifts ~25 across the frame, so any
    single threshold either eats the bottle or keeps the backdrop. Instead
    the background is estimated per row from the outer margins, and because
    an atomizer is a convex cylinder, each row is filled between its
    outermost solid runs. That also drops the soft base shadow, which never
    forms a run.
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    alpha = Image.new("L", (w, h), 0)
    ap = alpha.load()
    spans = {}

    def mid(vals):
        vals = sorted(vals)
        return vals[len(vals) // 2]

    for y in range(h):
        edge = [px[x, y] for x in range(margin)] + [px[x, y] for x in range(w - margin, w)]
        br, bg_, bb = mid([e[0] for e in edge]), mid([e[1] for e in edge]), mid([e[2] for e in edge])
        lo = hi = None
        run = 0
        for x in range(w):
            r, g, b = px[x, y]
            if abs(r - br) + abs(g - bg_) + abs(b - bb) > t:
                run += 1
                if run >= min_run:
                    if lo is None:
                        lo = x - run + 1
                    hi = x
            else:
                run = 0
        spans[y] = (lo, hi) if (lo is not None and hi is not None and hi > lo) else None

    rows = [y for y, sp in spans.items() if sp]
    if not rows:
        raise SystemExit(f"no subject found in {path}")

    # An atomizer is a constant-width cylinder, so the body's own x-range is
    # the truth. The surface highlight at the base spills outside it.
    core = rows[len(rows) // 4: len(rows) * 3 // 4]
    los = sorted(spans[y][0] for y in core)
    his = sorted(spans[y][1] for y in core)
    bl, bh = los[len(los) // 2], his[len(his) // 2]
    cx = (bl + bh) // 2

    # the real base is the last row whose centre is still solid bottle
    base = max(y for y in rows
               if abs(px[cx, y][0] - mid([px[x, y][0] for x in range(margin)])) +
                  abs(px[cx, y][1] - mid([px[x, y][1] for x in range(margin)])) +
                  abs(px[cx, y][2] - mid([px[x, y][2] for x in range(margin)])) > 60)

    for y in rows:
        if y > base:
            continue
        lo, hi = spans[y]
        for x in range(max(lo, bl - 2), min(hi, bh + 2) + 1):
            ap[x, y] = 255

    if feather:
        alpha = alpha.filter(ImageFilter.GaussianBlur(feather))
    im = im.convert("RGBA")
    im.putalpha(alpha)
    im = im.crop(im.getbbox())
    if max(im.size) > max_side:
        sc = max_side / max(im.size)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    dest = os.path.join(OUT, out_name)
    im.save(dest, "PNG", optimize=True)
    print(f"  -> {out_name:22s} {im.width}x{im.height}  "
          f"{os.path.getsize(dest)/1024:6.1f} KB  (ratio {im.width/im.height:.4f})")


print("\natomizers:")
for name in ("black", "gold", "navy", "pink", "red"):
    cutout_atomizer(f"{UP}/atomizer-{name}.png", f"atomizer-{name}.png")
