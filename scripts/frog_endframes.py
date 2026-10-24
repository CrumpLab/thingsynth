# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (complex tonewheels on) for the acorn frog: the pale yellow body with a little blue head and two
acorns on its back.

    uv run scripts/frog_endframes.py
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
m.CROP = (3000, 1650, 950, 800)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-complex/endframes'
p, outlined, circle, ellipse, tube, bez, crescent, comp = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.crescent, g.comp
INK = 14
YEL, HEAD, NUT, CAP, PINK = '#F8FF8F', '#7DB3DB', '#E4DE75', '#A4763E', '#FF7580'
LEAF = '#7fd36b'
BODY = ['f206', 'f207', 'f201']
ACORNS = ['f212', 'f214', 'f211', 'f213']
TOPS = [(3490.0, 1838.0), (3705.0, 2005.0)]  # the acorn caps' tops
NUTS = [(3486.0, 1960.0, 80.0), (3703.0, 2150.0, 95.0)]  # nut centres and half widths


def leaf(x, y, ang, L, W) -> str:
    """A lobed oak leaf from (x, y) pointing at ang degrees: its outline wobbles in rounded lobes."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for side in (1, -1):
        rng = range(0, 25) if side == 1 else range(24, -1, -1)
        for i in rng:
            u = i / 24
            w = W * math.sin(u * math.pi) * (0.75 + 0.25 * abs(math.sin(u * math.pi * 3.5)))
            lx, ly = u * L, side * w
            pts.append((x + lx * ca - ly * sa, y + lx * sa + ly * ca))
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def v1_sprouts() -> Image.Image:
    """Sprouting: each acorn cracks into life and a little oak seedling curls up out of its cap, with lobed leaves."""
    out = ''
    for (x, y), h, lean in [(TOPS[0], 230, -1), (TOPS[1], 200, 1)]:
        P = bez((x, y + 20), (x + 20 * lean, y - h * 0.3), (x - 40 * lean, y - h * 0.7), (x + 10 * lean, y - h), 20)
        out += outlined(tube(P, 13, 8), LEAF, INK * 0.8)
        for k, (u, ang, L) in enumerate([(0.45, -150, 110), (0.6, -30, 120), (1.0, -90 + 25 * lean, 130)]):
            i = int(u * (len(P) - 1))
            out += outlined(leaf(*P[i], ang, L, 34), ['#7fd36b', '#9be36b', '#6cc35b'][k], INK * 0.8)
    return comp(out, [])


def face(x, y, s, look=0.0) -> str:
    out = ''
    for dx in (-0.35, 0.35):
        out += outlined(circle(x + dx * s, y, s * 0.24), '#ffffff', INK * 0.7)
        out += f'<path d="{circle(x + dx * s + look * s * 0.08, y + s * 0.04, s * 0.11)}" fill="#000"/>'
    mouth = f'M{p(x - s * 0.25, y + s * 0.32)}C{p(x - s * 0.15, y + s * 0.62)} {p(x + s * 0.15, y + s * 0.62)} {p(x + s * 0.25, y + s * 0.32)}Z'
    out += outlined(mouth, '#e0466a', INK * 0.7)
    return out


def v2_friends() -> Image.Image:
    """Acorn friends: the two acorns wake up with faces and reach out little arms to hold hands across its back."""
    (x0, y0, s0), (x1, y1, s1) = NUTS
    out = face(x0, y0 - 5, s0, 1) + face(x1, y1 - 10, s1, -1)
    arm = bez((x0 + s0 * 0.85, y0 + 20), (x0 + s0 * 1.4, y0 + 30), (x1 - s1 * 1.5, y1 - 40), (x1 - s1 * 0.85, y1 - 10), 20)
    out += outlined(tube(arm, 13, 13), NUT, INK * 0.8)
    mid = arm[len(arm) // 2]
    out += outlined(circle(mid[0], mid[1], 22), NUT, INK * 0.8)
    other = bez((x0 - s0 * 0.85, y0 + 20), (x0 - s0 * 1.3, y0), (x0 - s0 * 1.5, y0 - 60), (x0 - s0 * 1.35, y0 - 110), 16)
    out += outlined(tube(other, 13, 13), NUT, INK * 0.8) + outlined(circle(*other[-1], 22), NUT, INK * 0.8)
    return comp('', [], out)


def v3_croak() -> Image.Image:
    """Croak: a big pink throat sac balloons out under the little blue head, its eye pops wide, and sound rings
    spread from it."""
    out = outlined(circle(3245, 2225, 85), '#ff9fc4', INK)
    out += f'<path d="{ellipse(3212, 2190, 26, 15, -35)}" fill="#ffffff" fill-opacity="0.9"/>'
    over = outlined(circle(3288, 2112, 34), '#ffffff', INK * 0.8) + f'<path d="{circle(3280, 2116, 15)}" fill="#000"/>'
    for k in range(3):
        over += outlined(crescent(3245, 2225, 140 + 50 * k, 130, 230, 26 - 4 * k), '#ffffff', INK * 0.7)
    return comp(out, [], over)


def acorn(x, y, s, rot=0.0) -> str:
    """An acorn the painting's way: a pale nut, a brown cap with a scalloped rim and a little stalk."""
    a = math.radians(rot)
    R = lambda dx, dy: (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))
    nut = 'M' + 'L'.join(p(*R(math.cos(t) * s * 0.95, s * 0.1 + math.sin(t) * s * (1.05 if math.sin(t) > 0 else 0.4))) for t in [i / 40 * 2 * math.pi for i in range(41)]) + 'Z'
    cap_pts = [R(math.cos(t) * s * 1.05, -math.sin(t) * s * 0.75) for t in [i / 30 * math.pi for i in range(31)]]
    rim = [R(-s * 1.05 + 2.1 * s * i / 30, 0.12 * s * abs(math.sin(i / 30 * math.pi * 5))) for i in range(31)]
    cap = 'M' + 'L'.join(p(*q) for q in cap_pts) + 'L' + 'L'.join(p(*q) for q in rim) + 'Z'
    stalk = tube([R(0, -s * 0.7), R(s * 0.1, -s * 1.0)], s * 0.1, s * 0.08)
    return outlined(nut, NUT, INK * 0.8) + outlined(stalk, CAP, INK * 0.7) + outlined(cap, CAP, INK * 0.8)


def v4_pile() -> Image.Image:
    """Acorn pile: more and more acorns tumble on until it carries a heap of them."""
    out = ''
    for x, y, s, r in [(3600, 1880, 58, 22), (3540, 2075, 64, -10), (3455, 2165, 56, -25), (3840, 2060, 52, 15), (3420, 1930, 50, -30), (3640, 2235, 54, 8), (3790, 1950, 46, 30)]:
        out += acorn(x, y, s, r)
    return comp(out, ACORNS)


def v5_legs() -> Image.Image:
    """Frog legs: big yellow hind legs and little front legs push out from under the body, with round toe pads,
    ready to leap."""
    out = ''
    # back leg: from under the body's right end, the knee bent up, the shin folded back to a foot with toe pads
    thigh = bez((3570, 2220), (3660, 2250), (3740, 2250), (3790, 2205), 16)
    shin = bez((3790, 2205), (3830, 2280), (3760, 2330), (3680, 2340), 16)
    for ang in (160, 190, 220):
        a = math.radians(ang)
        P = [(3685, 2340), (3685 + math.cos(a) * 85, 2340 - math.sin(a) * 70)]
        out += outlined(tube(P, 15, 13), YEL, INK * 0.8) + outlined(circle(*P[-1], 17), '#ffd166', INK * 0.8)
    out += outlined(tube(shin, 34, 28), YEL, INK) + outlined(tube(thigh, 50, 40), YEL, INK) + outlined(circle(3790, 2208, 44), YEL, INK)
    # front leg from under the head
    fl = bez((3330, 2225), (3330, 2290), (3310, 2330), (3285, 2350), 12)
    for dx in (-50, -12, 26):
        P = [(3285, 2350), (3285 + dx, 2395)]
        out += outlined(tube(P, 12, 10), YEL, INK * 0.8) + outlined(circle(*P[-1], 15), '#ffd166', INK * 0.8)
    out += outlined(tube(fl, 28, 22), YEL, INK)
    return comp('', [], out)


VERSIONS = [
    ('1-sprouting', 'Sprouting', v1_sprouts),
    ('2-acorn-friends', 'Acorn friends', v2_friends),
    ('3-croak', 'Croak', v3_croak),
    ('4-acorn-pile', 'Acorn pile', v4_pile),
    ('5-frog-legs', 'Frog legs', v5_legs),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (pure)', m.compose())]
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
