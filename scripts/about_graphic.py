# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "resvg-py>=0.1"]
# ///
"""The about page's graphic: Tonewheel's real panel above the painting, with arrows from its controls to the objects
they drive. The painting is dimmed and each object's visible part is lit, edged in its arrow's colour; the numbers
match the list under it in web/about.html.

    uv run scripts/about_graphic.py

Reads docs/about/tonewheel-panel.png (the plugin, captured at 2x from SynthLand's site) and the painting; writes
web/public/about-tonewheel-painting.webp.
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

import resvg_py
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'art/golden-pyramid-with-tunnel-celebration'
OUT = ROOT / 'web/public/about-tonewheel-painting.webp'

W = 2000
PANEL_K = W / 1956  # panel capture px -> graphic px
PANEL_H = round(918 * PANEL_K)
SIZE = 1560  # the painting's side
X0, Y0 = 220, PANEL_H + 170  # the painting's top left
H = Y0 + SIZE + 40
PAINTED = 375, 4200  # the painting's origin and side in canvas px
K = SIZE / PAINTED[1]
BG = '#0e0b0a'
INK = '#000'

#: every fill in painting order, so a later one covers an earlier one
FILLS = dict(re.findall(r'<path id="(f\d+)"[^>]* d="([^"]*)"', (ART / 'layers/fills.svg').read_text()))
DIM = 0.36  # how far the painting sinks towards the background
OBJECTS = json.loads((ART / 'objects.json').read_text())['objects']


def panel(x: float, y: float) -> tuple[float, float]:
    return x * PANEL_K, y * PANEL_K


def art(x: float, y: float) -> tuple[float, float]:
    return X0 + (x - PAINTED[0]) * K, Y0 + (y - PAINTED[0]) * K


def fills_of(obj: str) -> list[str]:
    return [obj[1:]] if obj.startswith('#') else sorted({f for r in OBJECTS[obj]['parts'].values() for f in r})


# number, colour, object, control centre and ring radius (panel px), where the arrow leaves, its bezier handles and
# its end (graphic px for the handles, canvas px for the end), and where the two numbers sit.
LINKS = [
    dict(n=1, colour='#ffe600', obj='stalk-left', ring=(81, 560, 64), start=(81, 626),
         c1=(70, 1000), c2=(300, 1270), end=(1190, 960), b1=(150, 440), b2=(-74, 60)),
    dict(n=2, colour='#ff4fb0', obj='left-cushion', ring=(680, 335, 56), start=(672, 392),
         c1=(590, 820), c2=(560, 1800), end=(1000, 3330), b1=(610, 250), b2=(-46, -52)),
    dict(n=3, colour='#7cff4a', obj='#f227', ring=(695, 868, 42), start=(712, 900),
         c1=(740, 1060), c2=(860, 1290), end=(2460, 1600), b1=(640, 900), b2=(74, -44)),
    dict(n=4, colour='#00e5ff', obj='horned-ghost', ring=(1046, 195, 56), start=(1050, 252),
         c1=(1075, 640), c2=(1115, 1110), end=(2960, 1040), b1=(1112, 262), b2=(66, -44)),
    dict(n=5, colour='#ff8a1f', obj='tunnel', ring=(1700, 350, 66), start=(1688, 418),
         c1=(1660, 820), c2=(1470, 1300), end=(3440, 1760), b1=(1610, 430), b2=(72, -38)),
    dict(n=6, colour='#c9a2ff', obj='big-eye', ring=(1780, 176, 84), start=(1866, 190),
         c1=(1985, 640), c2=(1985, 1750), end=(4470, 2880), b1=(1668, 96), b2=(60, 18)),
    dict(n=7, colour='#ffffff', obj='coral-tongue', ring=(1870, 727, 54), start=(1868, 786),
         c1=(1850, 1050), c2=(1720, 1500), end=(3990, 2090), b1=(1790, 780), b2=(70, -30)),
]


def bezier_end(p0, c1, c2, p3) -> tuple[float, float]:
    """The arrow's direction where it arrives."""
    dx, dy = p3[0] - c2[0], p3[1] - c2[1]
    d = math.hypot(dx, dy) or 1
    return dx / d, dy / d


def badge(x: float, y: float, colour: str) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="35" fill="{colour}" stroke="{INK}" stroke-width="9"/>'


def link_svg(l: dict) -> tuple[str, str, list[tuple[float, float, int]]]:
    colour = l['colour']
    rx, ry, rr = l['ring']
    cx, cy = panel(rx, ry)
    p0 = panel(*l['start'])
    p3 = art(*l['end'])
    ux, uy = bezier_end(p0, l['c1'], l['c2'], p3)
    tail = p3[0] - ux * 44, p3[1] - uy * 44  # the line stops inside the head
    d = f'M{p0[0]:.1f} {p0[1]:.1f}C{l["c1"][0]} {l["c1"][1]} {l["c2"][0]} {l["c2"][1]} {tail[0]:.1f} {tail[1]:.1f}'
    nx, ny = -uy, ux
    head = [(p3[0] + ux * 16, p3[1] + uy * 16), (p3[0] - ux * 62 + nx * 42, p3[1] - uy * 62 + ny * 42),
            (p3[0] - ux * 62 - nx * 42, p3[1] - uy * 62 - ny * 42)]
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in head)
    ring = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr}" fill="none" stroke="{INK}" stroke-width="20"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr}" fill="none" stroke="{colour}" stroke-width="10"/>')
    arrow = (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="26" stroke-linecap="round"/>'
             f'<polygon points="{pts}" fill="{INK}" stroke="{INK}" stroke-width="18" stroke-linejoin="round"/>'
             f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="13" stroke-linecap="round"/>'
             f'<polygon points="{pts}" fill="{colour}"/>')
    b1 = panel(*l['b1'])
    b2 = p3[0] + l['b2'][0], p3[1] + l['b2'][1]
    return ring + arrow + badge(*b1, colour) + badge(*b2, colour), [(b1[0], b1[1], l['n']), (b2[0], b2[1], l['n'])]


def visible(obj: str) -> Image.Image:
    """The part of the object nothing covers: every fill in painting order, the object's white and the rest black."""
    own = set(fills_of(obj))
    body = ''.join(f'<path d="{d}" fill="{"#fff" if f in own else "#000"}"/>' for f, d in FILLS.items())
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{PAINTED[0]} {PAINTED[0]} {PAINTED[1]} {PAINTED[1]}" '
           f'width="{SIZE}" height="{SIZE}"><rect x="0" y="0" width="4950" height="4950" fill="#000"/>{body}</svg>')
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).convert('L')


def grow(mask: Image.Image, px: int) -> Image.Image:
    return mask.filter(ImageFilter.GaussianBlur(px)).point(lambda v: 255 if v > 30 else 0)


def main() -> None:
    im = Image.new('RGB', (W, H), BG)
    im.paste(Image.open(ROOT / 'docs/about/tonewheel-panel.png').convert('RGB').resize((W, PANEL_H), Image.LANCZOS), (0, 0))
    painting = Image.open(ART / 'golden-pyramid-with-tunnel-celebration.jpg').convert('RGB')
    s = painting.width / 4950
    a, b = round(PAINTED[0] * s), round((PAINTED[0] + PAINTED[1]) * s)
    bright = painting.crop((a, a, b, b)).resize((SIZE, SIZE), Image.LANCZOS)
    lit = Image.blend(bright, Image.new('RGB', (SIZE, SIZE), BG), DIM)
    arrows, numbers = '', []
    for l in LINKS:
        r, n = link_svg(l)
        arrows += r
        numbers += n
        mask = visible(l['obj'])
        rim = grow(mask, 7)
        halo = grow(mask, 12)
        lit.paste(Image.new('RGB', (SIZE, SIZE), INK), mask=ImageChops.subtract(halo, mask))
        lit.paste(Image.new('RGB', (SIZE, SIZE), l['colour']), mask=ImageChops.subtract(rim, mask))
        lit.paste(bright, mask=mask)
    im.paste(lit, (X0, Y0))
    doc = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{arrows}</svg>'
    layer = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).convert('RGBA')
    im = im.convert('RGBA')
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=46)
    for x, y, n in numbers:
        d.text((x, y), str(n), fill=INK, font=font, anchor='mm', stroke_width=1, stroke_fill=INK)
    im.convert('RGB').save(OUT, quality=86, method=6)
    print('wrote', OUT, OUT.stat().st_size // 1024, 'KB', im.size)


if __name__ == '__main__':
    main()
