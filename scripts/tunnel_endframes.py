# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (vibrato mode at its last, C3) for the tunnel: the dark teal arch in the golden pyramid, with the
pale blue rim on its left and the acorn frog and green bush sitting in its mouth.

    uv run scripts/tunnel_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (2950, 1350, 1000, 900)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/vib-mode/endframes'
p, outlined, circle, ellipse, tube, bez, crescent = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.crescent
INK = 16
TUNNEL = 'f219'
IN_FRONT = ['f201', 'f206', 'f207', 'f209', 'f210', 'f211', 'f212', 'f213', 'f214', 'f215', 'f216', 'f217', 'f220']
VP = (3420.0, 1820.0)  # where the tunnel recedes to


def tunnel_d() -> str:
    return m.FILLS[TUNNEL]


def clipped(body: str, cid: str = 'tun') -> str:
    return f'<defs><clipPath id="{cid}"><path d="{tunnel_d()}"/></clipPath></defs><g clip-path="url(#{cid})">{body}</g>'


def draw(front: str, colour: str | None = None, over: str = '') -> Image.Image:
    m.FRONT = IN_FRONT
    m.FRONT_INK = sorted({s for f in IN_FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front, fill_colour={TUNNEL: colour} if colour else None)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def scaled(d: str, s: float, c=VP) -> str:
    return m.warp_path(d, lambda x, y: (c[0] + (x - c[0]) * s, c[1] + (y - c[1]) * s))


def star(cx, cy, r, col) -> str:
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return outlined(m.smooth(pts) if False else 'M' + 'L'.join(p(*q) for q in pts) + 'Z', col, INK * 0.9)


def v1_train() -> Image.Image:
    """Train: a big candy steam engine noses out of the tunnel, round pink boiler face, a headlamp blazing, a
    striped cowcatcher and a puffing stack."""
    x, y = 3470.0, 1700.0
    out = outlined(f'M{p(x - 60, y - 260)}L{p(x + 60, y - 260)}L{p(x + 40, y - 140)}L{p(x - 40, y - 140)}Z', '#3b3b5c', INK)
    out += outlined(ellipse(x, y - 275, 90, 30), '#3b3b5c', INK)
    out += outlined(circle(x, y, 190), '#f64c76', INK * 1.2)
    out += outlined(circle(x, y, 130), '#ff9fc4', INK)
    out += outlined(circle(x, y - 10, 62), '#ffe066', INK)
    out += outlined(circle(x - 18, y - 28, 20), '#ffffff', INK * 0.6)
    for k in range(5):
        x0 = x - 200 + k * 80
        out += outlined(f'M{p(x0, y + 150)}L{p(x0 + 80, y + 150)}L{p(x0 + 60, y + 260)}L{p(x0 + 20, y + 260)}Z', ['#ffe066', '#f64c76'][k % 2], INK)
    return draw('<g/>', '#1f3f4c', out)


def v2_eyes() -> Image.Image:
    """Eyes in the dark: the tunnel goes deep night-blue and two big glowing eyes open in it, looking out."""
    out = ''
    for x, y, r in [(3530, 1625, 78), (3280, 1805, 74)]:
        out += outlined(ellipse(x, y, r * 1.1, r), '#ffe066', INK)
        out += outlined(ellipse(x, y, r * 0.75, r * 0.7), '#ffb84d', INK * 0.6)
        out += f'<path d="{ellipse(x + 8, y + 5, r * 0.22, r * 0.62)}" fill="#000"/>'
        out += outlined(circle(x + r * 0.4, y - r * 0.4, r * 0.16), '#ffffff', INK * 0.5)
    return draw(clipped(out), '#141a3a')


def v3_rings() -> Image.Image:
    """Rainbow rings: the tunnel's arch repeats inward in candy bands, a rainbow tunnel receding into the pyramid."""
    d = tunnel_d()
    cols = ['#f64c76', '#ff9f43', '#ffe066', '#7fd36b', '#2DFFF4', '#b44cff', '#1f3f4c']
    out = ''
    for k, col in enumerate(cols):
        out += outlined(scaled(d, 1 - 0.13 * (k + 1)), col, INK)
    return draw(clipped(out), cols[0])


def edge_pts(fid, which='top', n=40):
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', m.FILLS[fid])]
    P = list(zip(nums[0::2], nums[1::2]))
    xs = [q[0] for q in P]
    x0, x1 = min(xs), max(xs)
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        near = [q[1] for q in P if abs(q[0] - x) < (x1 - x0) / n]
        if near:
            out.append((x, min(near) if which == 'top' else max(near)))
    return out


def v4_mouth() -> Image.Image:
    """Singing mouth: the tunnel becomes a wide open singing mouth, deep red inside, a row of big teeth along its
    arch and a fat pink tongue lolling out over the rim."""
    top = [q for q in edge_pts(TUNNEL) if 3180 < q[0] < 3700]
    out = ''
    for (x, y) in top[1::3]:
        out += outlined(f'M{p(x - 42, y - 20)}L{p(x + 42, y - 20)}L{p(x + 38, y + 70)}C{p(x + 30, y + 100)} {p(x - 30, y + 100)} {p(x - 38, y + 70)}Z', '#ffffff', INK)
    tongue = (f'M{p(3330, 1760)}C{p(3250, 1720)} {p(3100, 1760)} {p(3060, 1870)}C{p(3030, 1960)} {p(3110, 2020)} {p(3190, 1990)}'
              f'C{p(3240, 1970)} {p(3290, 1900)} {p(3330, 1860)}Z')
    over = outlined(tongue, '#ff7fa8', INK * 1.2)
    over += outlined(f'M{p(3290, 1790)}C{p(3220, 1800)} {p(3150, 1850)} {p(3120, 1930)}C{p(3170, 1870)} {p(3230, 1830)} {p(3290, 1810)}Z', '#e0466a', INK * 0.6)
    return draw(clipped(out), '#7a1846', over)


def v5_night() -> Image.Image:
    """Starry night: the tunnel opens onto a night sky inside the pyramid, a big crescent moon and fat candy stars."""
    out = ''
    moon = f'M{p(3540, 1540)}A100 100 0 1 0 {p(3540, 1740)}A80 80 0 1 1 {p(3540, 1540)}Z'
    out += outlined(moon, '#fff3b0', INK)
    for x, y, r, col in [(3300, 1790, 70, '#ffe066'), (3420, 1700, 50, '#ff9fc4'), (3630, 1680, 48, '#2DFFF4'), (3200, 1880, 45, '#ffffff')]:
        out += star(x, y, r, col)
    return draw(clipped(out), '#1b2a5a')


def v5_flower() -> Image.Image:
    """Tunnel flower: big candy petals open out round the tunnel's arch and rim, so the tunnel becomes the heart of a
    flower on the pyramid's face."""
    d = m.FILLS['f218'] + m.FILLS[TUNNEL]
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', d)]
    P = list(zip(nums[0::2], nums[1::2]))
    cx = sum(q[0] for q in P) / len(P)
    cy = sum(q[1] for q in P) / len(P)
    out = ''
    cols = ['#f64c76', '#ffe066', '#ff9fc4', '#ff9f43', '#c4a3f0']
    for k in range(11):
        a = math.radians(-200 + k * 22)
        # the arch's edge in that direction: the farthest outline point near the ray
        best = max(P, key=lambda q: ((q[0] - cx) * math.cos(a) + (q[1] - cy) * math.sin(a)) - 4 * abs(-(q[0] - cx) * math.sin(a) + (q[1] - cy) * math.cos(a)))
        bx, by = best
        tx, ty = bx + math.cos(a) * 230, by + math.sin(a) * 230
        nx, ny = -math.sin(a) * 105, math.cos(a) * 105
        petal = (f'M{p(bx - math.cos(a) * 40, by - math.sin(a) * 40)}C{p(bx + nx, by + ny)} {p(tx + nx * 0.6, ty + ny * 0.6)} {p(tx, ty)}'
                 f'C{p(tx - nx * 0.6, ty - ny * 0.6)} {p(bx - nx, by - ny)} {p(bx - math.cos(a) * 40, by - math.sin(a) * 40)}Z')
        out += outlined(petal, cols[k % len(cols)], INK)
    m.FRONT = IN_FRONT + ['f218', TUNNEL]
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        return m.compose(front=out)
    finally:
        m.FRONT, m.FRONT_INK = [], []


VERSIONS = [
    ('1-train', 'Train', v1_train),
    ('2-eyes-in-the-dark', 'Eyes in the dark', v2_eyes),
    ('3-rainbow-rings', 'Rainbow rings', v3_rings),
    ('4-singing-mouth', 'Singing mouth', v4_mouth),
    ('5-tunnel-flower', 'Tunnel flower', v5_flower),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (V1)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.45
    tw, th = int(w * s), int(h * s)
    sheet = Image.new('RGB', (tw * 3 + 40, (th + 60) * 2 + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = 10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 60)
        d.text((x, y), label, fill='black', font=font)
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
    sheet.save(OUT / 'sheet.png')
    print('wrote', OUT / 'sheet.png')


if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    main()
