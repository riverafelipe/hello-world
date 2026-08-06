#!/usr/bin/env python3
"""Draw four unbranded luxury flacons as standalone SVG.

V3 needs bottles with no house on them, so these are drawn rather than
photographed. They ship as SVG (not PNG) so they stay crisp at any size and
cost the page almost nothing; the embed step inlines them like any other
asset. Each fills its viewBox top to bottom, so the page's --s height knob
compares them directly.

Realism here comes from three things stacked in order: a body gradient that
is bright at the two edges and thin through the middle (how thick glass
actually reads), juice with a meniscus, and blurred specular streaks.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

# each bottle's glass tint, juice ramp, and metal ramp
# Clear glass is mostly transparent — only the two edges catch light, where
# the curve turns away and you look through the most material. Filling the
# middle with white is what makes drawn glass read as milk.
GLASS = """
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"    stop-color="#ffffff" stop-opacity=".08"/>
      <stop offset="0.05" stop-color="#ffffff" stop-opacity=".52"/>
      <stop offset="0.16" stop-color="{edge}"  stop-opacity=".14"/>
      <stop offset="0.50" stop-color="{core}"  stop-opacity=".05"/>
      <stop offset="0.84" stop-color="{edge}"  stop-opacity=".17"/>
      <stop offset="0.95" stop-color="#ffffff" stop-opacity=".58"/>
      <stop offset="1"    stop-color="#ffffff" stop-opacity=".10"/>
    </linearGradient>"""

# the oval is deliberately frosted, so it keeps a milky core
FROST = """
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"    stop-color="#ffffff" stop-opacity=".22"/>
      <stop offset="0.05" stop-color="#ffffff" stop-opacity=".68"/>
      <stop offset="0.16" stop-color="{edge}"  stop-opacity=".46"/>
      <stop offset="0.50" stop-color="{core}"  stop-opacity=".28"/>
      <stop offset="0.84" stop-color="{edge}"  stop-opacity=".48"/>
      <stop offset="0.95" stop-color="#ffffff" stop-opacity=".72"/>
      <stop offset="1"    stop-color="#ffffff" stop-opacity=".26"/>
    </linearGradient>"""

JUICE = """
    <linearGradient id="j" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"    stop-color="{top}"/>
      <stop offset="0.42" stop-color="{mid}"/>
      <stop offset="1"    stop-color="{bot}"/>
    </linearGradient>"""

METAL = """
    <linearGradient id="m" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"    stop-color="{d}"/>
      <stop offset="0.14" stop-color="{l}"/>
      <stop offset="0.32" stop-color="{h}"/>
      <stop offset="0.54" stop-color="{l}"/>
      <stop offset="0.80" stop-color="{d}"/>
      <stop offset="1"    stop-color="{s}"/>
    </linearGradient>"""

BLUR = """
    <filter id="soft" x="-40%" y="-20%" width="180%" height="140%">
      <feGaussianBlur stdDeviation="{r}"/>
    </filter>"""

GOLD = dict(d="#8A6A24", l="#E3C87C", h="#FBF4D6", s="#6E5219")
STEEL = dict(d="#7C868C", l="#D5DDE1", h="#FBFDFE", s="#5C666C")
DARK = dict(d="#1E1E20", l="#5A5A5F", h="#9A9AA0", s="#101012")


def head(w, h, glass, juice, metal, blur=13, frost=False):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">\n  <defs>'
        + (FROST if frost else GLASS).format(**glass)
        + JUICE.format(**juice)
        + METAL.format(**metal)
        + BLUR.format(r=blur)
        + '\n    <clipPath id="c"><path d="{body}"/></clipPath>\n  </defs>\n'
    )


def build(name, w, h, glass, juice, metal, body, parts, frost=False):
    # An inner shadow hugging the silhouette is what gives glass its wall
    # thickness: stroke the outline wide, clipped to the body, so only the
    # inward half survives. Injected under the speculars so they stay on top.
    inner = (f'  <g clip-path="url(#c)">\n'
             f'    <path d="{body}" fill="none" stroke="#3B3B42" '
             f'stroke-opacity=".20" stroke-width="30"/>\n  </g>\n')
    parts = parts.replace('  <g filter="url(#soft)">', inner + '  <g filter="url(#soft)">')
    svg = head(w, h, glass, juice, metal, frost=frost).replace("{body}", body) + parts + "</svg>\n"
    path = os.path.join(OUT, name)
    open(path, "w", encoding="utf-8").write(svg)
    print(f"  -> {name:24s} {w}x{h}  {len(svg)/1024:5.1f} KB  (ratio {w/h:.4f})")


# ---------------------------------------------------------------- 1. flacon
# tall rectangular, squared shoulders, gold cap
W, H = 430, 1000
body = ("M44 452 C44 412 62 388 94 364 C126 340 178 330 178 304 L252 304 "
        "C252 330 304 340 336 364 C368 388 386 412 386 452 L386 944 "
        "Q386 980 350 980 L80 980 Q44 980 44 944 Z")
build("bottle-flacon.svg", W, H,
      dict(edge="#DCE6EA", core="#93A6B0"),
      dict(top="#F0C976", mid="#DBA43C", bot="#A96C15"), GOLD, body,
      f"""  <rect x="150" y="10" width="130" height="200" rx="10" fill="url(#m)"/>
  <rect x="164" y="24" width="102" height="14" rx="7" fill="#fff" opacity=".34"/>
  <rect x="158" y="210" width="114" height="28" rx="5" fill="url(#m)"/>
  <rect x="180" y="238" width="70" height="70" fill="url(#g)" opacity=".9"/>
  <path d="{body}" fill="url(#g)"/>
  <g clip-path="url(#c)">
    <rect x="0" y="560" width="{W}" height="{H}" fill="url(#j)"/>
    <ellipse cx="215" cy="560" rx="176" ry="20" fill="#F5D590" opacity=".75"/>
    <rect x="0" y="560" width="{W}" height="26" fill="#fff" opacity=".16"/>
  </g>
  <path d="{body}" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="4"/>
  <g filter="url(#soft)">
    <rect x="66" y="430" width="26" height="500" rx="13" fill="#fff" opacity=".55"/>
    <rect x="344" y="450" width="16" height="450" rx="8" fill="#fff" opacity=".34"/>
    <ellipse cx="150" cy="620" rx="34" ry="150" fill="#fff" opacity=".13"/>
  </g>""")

# ------------------------------------------------------------------ 2. cube
# squat faceted block, smoky glass, black cap
W, H = 760, 1000
body = ("M60 430 L120 336 L640 336 L700 430 L700 900 "
        "Q700 966 634 966 L126 966 Q60 966 60 900 Z")
build("bottle-cube.svg", W, H,
      dict(edge="#C8CDD2", core="#5E656C"),
      dict(top="#C98A3E", mid="#A5651F", bot="#6E3D08"), DARK, body,
      f"""  <rect x="286" y="16" width="188" height="180" rx="12" fill="url(#m)"/>
  <rect x="302" y="30" width="156" height="12" rx="6" fill="#fff" opacity=".22"/>
  <rect x="298" y="196" width="164" height="30" rx="6" fill="url(#m)"/>
  <rect x="330" y="226" width="100" height="112" fill="url(#g)" opacity=".9"/>
  <path d="{body}" fill="url(#g)"/>
  <g clip-path="url(#c)">
    <rect x="0" y="520" width="{W}" height="{H}" fill="url(#j)"/>
    <ellipse cx="380" cy="520" rx="330" ry="22" fill="#D89A50" opacity=".72"/>
    <rect x="0" y="520" width="{W}" height="28" fill="#fff" opacity=".14"/>
  </g>
  <path d="M120 336 L120 966 M640 336 L640 966" stroke="#fff" stroke-opacity=".26" stroke-width="5"/>
  <path d="{body}" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width="5"/>
  <g filter="url(#soft)">
    <rect x="86" y="420" width="30" height="500" rx="15" fill="#fff" opacity=".5"/>
    <rect x="656" y="440" width="18" height="450" rx="9" fill="#fff" opacity=".3"/>
    <ellipse cx="250" cy="600" rx="52" ry="150" fill="#fff" opacity=".1"/>
  </g>""")

# ------------------------------------------------------------------ 3. oval
# soft teardrop, frosted rose glass, domed steel cap
W, H = 560, 1000
body = ("M280 300 C420 300 512 430 512 640 C512 848 420 964 280 964 "
        "C140 964 48 848 48 640 C48 430 140 300 280 300 Z")
build("bottle-oval.svg", W, H,
      dict(edge="#F3DDE3", core="#C79AA6"),
      dict(top="#F0AFC0", mid="#DE8098", bot="#B4526C"), STEEL, body,
      f"""  <path d="M212 40 Q280 -6 348 40 L356 178 L204 178 Z" fill="url(#m)"/>
  <rect x="206" y="176" width="148" height="30" rx="8" fill="url(#m)"/>
  <rect x="228" y="206" width="104" height="110" fill="url(#g)" opacity=".9"/>
  <path d="{body}" fill="url(#g)"/>
  <g clip-path="url(#c)">
    <rect x="0" y="560" width="{W}" height="{H}" fill="url(#j)"/>
    <ellipse cx="280" cy="560" rx="230" ry="24" fill="#F6C3D1" opacity=".8"/>
    <rect x="0" y="560" width="{W}" height="26" fill="#fff" opacity=".18"/>
  </g>
  <path d="{body}" fill="none" stroke="#ffffff" stroke-opacity=".62" stroke-width="4"/>
  <g filter="url(#soft)">
    <ellipse cx="128" cy="600" rx="34" ry="190" fill="#fff" opacity=".5"/>
    <ellipse cx="440" cy="660" rx="20" ry="150" fill="#fff" opacity=".3"/>
    <ellipse cx="300" cy="380" rx="150" ry="40" fill="#fff" opacity=".2"/>
  </g>""", frost=True)

# ---------------------------------------------------------------- 4. column
# slim tapered cylinder, ruby glass, gold cap
W, H = 360, 1000
body = ("M104 330 L256 330 C284 330 300 372 302 470 L316 906 "
        "Q318 968 258 968 L102 968 Q42 968 44 906 L58 470 "
        "C60 372 76 330 104 330 Z")
build("bottle-column.svg", W, H,
      dict(edge="#F0D2D2", core="#9B5B5B"),
      dict(top="#D9536A", mid="#B32F45", bot="#7A1526"), GOLD, body,
      f"""  <rect x="118" y="12" width="124" height="188" rx="10" fill="url(#m)"/>
  <rect x="132" y="26" width="96" height="12" rx="6" fill="#fff" opacity=".34"/>
  <rect x="124" y="200" width="112" height="26" rx="5" fill="url(#m)"/>
  <rect x="142" y="226" width="76" height="108" fill="url(#g)" opacity=".9"/>
  <path d="{body}" fill="url(#g)"/>
  <g clip-path="url(#c)">
    <rect x="0" y="540" width="{W}" height="{H}" fill="url(#j)"/>
    <ellipse cx="180" cy="540" rx="128" ry="18" fill="#E97C90" opacity=".72"/>
    <rect x="0" y="540" width="{W}" height="24" fill="#fff" opacity=".16"/>
  </g>
  <path d="{body}" fill="none" stroke="#ffffff" stroke-opacity=".58" stroke-width="4"/>
  <g filter="url(#soft)">
    <rect x="76" y="420" width="22" height="500" rx="11" fill="#fff" opacity=".55"/>
    <rect x="272" y="460" width="14" height="420" rx="7" fill="#fff" opacity=".32"/>
    <ellipse cx="140" cy="640" rx="24" ry="150" fill="#fff" opacity=".12"/>
  </g>""")

print("\nfour generic flacons written to assets/")
