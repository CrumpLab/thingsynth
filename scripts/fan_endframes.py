# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (key click release at its loudest) for the fan hand: the broad yellow-green fan, lower right, with
rows of pale pill-shaped fingers pointing up and to the right.

    uv run scripts/fan_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (2950, 2650, 1200, 1050)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-click-release/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
PILLS = [(3611, 2988), (3690, 3104), (3525, 3055), (3405, 3150), (3550, 3220), (3428, 3324)]
ANG = -50.0
FAN_BASE = (3260.0, 3420.0)


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def popcorn(x, y, r, seed) -> str:
    rnd = random.Random(seed)
    out = ''
    for k in range(6):
        a = k / 6 * 2 * math.pi + rnd.random() * 0.4
        out += outlined(circle(x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, r * (0.5 + rnd.random() * 0.12)), '#fffbe6', INK * 0.9)
    out += f'<path d="{circle(x, y, r * 0.7)}" fill="#fffbe6"/>'
    out += outlined(ellipse(x + r * 0.1, y + r * 0.35, r * 0.28, r * 0.18), '#ffd23f', INK * 0.7)
    return out


def v1_popcorn() -> Image.Image:
    """Popcorn: every pale finger pops into a big puffy popcorn kernel, a few flying off."""
    out = ''.join(popcorn(x, y, 78, k) for k, (x, y) in enumerate(PILLS))
    out += popcorn(3800, 2880, 62, 9) + popcorn(3730, 2780, 50, 10)
    return draw('', [], out)


def v2_paper_fan() -> Image.Image:
    """Folding fan: a big candy paper fan unfolds out of it, pleat after pleat, spreading behind the fingers."""
    x, y = FAN_BASE
    out = ''
    cols = ['#ff9fc4', '#ffe066', '#7fe0c8', '#c4a3f0']
    n = 9
    for k in range(n):
        a0, a1 = math.radians(-100 + k * 10), math.radians(-100 + (k + 1) * 10)
        R0, R1 = 120, 680
        d = (f'M{p(x + math.cos(a0) * R0, y + math.sin(a0) * R0)}L{p(x + math.cos(a0) * R1, y + math.sin(a0) * R1)}'
             f'A{R1} {R1} 0 0 1 {p(x + math.cos(a1) * R1, y + math.sin(a1) * R1)}L{p(x + math.cos(a1) * R0, y + math.sin(a1) * R0)}Z')
        out += outlined(d, cols[k % 4], INK)
    out += outlined(circle(x, y, 60), '#a4763e', INK)
    return draw(out, ['f071', 'f088', 'f089', 'f090', 'f091'], '')


def v3_caterpillars() -> Image.Image:
    """Caterpillars: the rows of fingers join up into two fat green caterpillars with round faces, crawling up."""
    out = ''
    for row, col in [([(3405, 3150), (3525, 3055), (3611, 2988)], '#8fe36b'), ([(3428, 3324), (3550, 3220), (3690, 3104)], '#5cd6b8')]:
        segs = []
        for (ax, ay), (bx, by) in zip(row, row[1:]):
            segs += [(ax + (bx - ax) * u, ay + (by - ay) * u) for u in (0, 0.5)]
        segs.append(row[-1])
        for k, (x, y) in enumerate(segs):
            out += outlined(circle(x, y, 70), col, INK)
            out += outlined(ellipse(x - 10, y + 62, 14, 24), '#2b6b3a', INK * 0.6)
        hx, hy = segs[-1][0] + 90, segs[-1][1] - 75
        out += outlined(circle(hx, hy, 85), col, INK)
        for dx in (-28, 28):
            out += outlined(circle(hx + dx, hy - 10, 22), '#ffffff', INK * 0.6) + f'<path d="{circle(hx + dx + 5, hy - 8, 10)}" fill="#000"/>'
            out += outlined(tube([(hx + dx, hy - 70), (hx + dx * 1.6, hy - 150)], 10, 8), col, INK * 0.6) + outlined(circle(hx + dx * 1.6, hy - 155, 18), '#f64c76', INK * 0.6)
        out += outlined(f'M{p(hx - 30, hy + 25)}C{p(hx - 10, hy + 50)} {p(hx + 10, hy + 50)} {p(hx + 30, hy + 25)}Z', '#e0466a', INK * 0.6)
    return draw('', [], out)


def v4_pea_pod() -> Image.Image:
    """Pea pod: the fan splits open like a pod along its middle and big round peas roll out of it, bouncing."""
    x, y = 3500.0, 3150.0
    a = math.radians(ANG)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x + ca * u - sa * v, y + sa * u + ca * v)
    pod = f'M{p(*R(-420, 0))}C{p(*R(-200, -230))} {p(*R(200, -230))} {p(*R(420, 0))}C{p(*R(200, -60))} {p(*R(-200, -60))} {p(*R(-420, 0))}Z'
    pod2 = f'M{p(*R(-420, 0))}C{p(*R(-200, 230))} {p(*R(200, 230))} {p(*R(420, 0))}C{p(*R(200, 60))} {p(*R(-200, 60))} {p(*R(-420, 0))}Z'
    out = outlined(pod, '#7fd36b', INK) + outlined(pod2, '#6cc35b', INK)
    for k, u in enumerate((-250, -80, 90, 260)):
        out += outlined(circle(*R(u, 0), 80), '#a8ec6b', INK)
        out += outlined(ellipse(*R(u - 25, -30), 20, 12, ANG), '#ffffff', INK * 0.5)
    for cx, cy in ((3850, 2860), (3940, 3000)):
        out += outlined(circle(cx, cy, 70), '#a8ec6b', INK)
    return draw('', [], out)


def v5_fingers() -> Image.Image:
    """Painted nails: each pale finger stretches long out of its place, curling a little, tipped with a candy nail."""
    out = ''
    cols = ['#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b']
    for k, (x, y) in enumerate(PILLS):
        ang = ANG + (k - 2.5) * 6
        a = math.radians(ang)
        L = 300
        P = bez((x - math.cos(a) * 50, y - math.sin(a) * 50), (x + math.cos(a) * L * 0.4, y + math.sin(a) * L * 0.4),
                (x + math.cos(a) * L * 0.8, y + math.sin(a) * L * 0.8 - 20), (x + math.cos(a + 0.25) * L, y + math.sin(a + 0.25) * L), 14)
        out += outlined(tube(P, 50, 44), '#fffed0', INK)
        nx, ny = P[-1]
        b = math.atan2(ny - P[-3][1], nx - P[-3][0])
        out += outlined(ellipse(nx - math.cos(b) * 20, ny - math.sin(b) * 20, 34, 42, math.degrees(b) + 90), cols[k], INK * 0.8)
    return draw('', [], out)


VERSIONS = [
    ('1-popcorn', 'Popcorn', v1_popcorn),
    ('2-folding-fan', 'Folding fan', v2_paper_fan),
    ('3-caterpillars', 'Caterpillars', v3_caterpillars),
    ('4-pea-pod', 'Pea pod', v4_pea_pod),
    ('5-painted-nails', 'Painted nails', v5_fingers),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (no release)', m.compose())]
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
