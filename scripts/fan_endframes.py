# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (key click release at its loudest) for the fan hand: the broad yellow-green fan, lower right, with
rows of pale pill-shaped fingers pointing up and to the right.

    uv run scripts/fan_endframes.py          # the five end frames and sheet
    uv run scripts/fan_endframes.py pop      # the chosen popcorn: progression strip and end frame
    uv run scripts/fan_endframes.py export   # docs/objects/tg-click-release/build.json
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


# ---- chosen: popcorn -----------------------------------------------------------------------------------------------
# Picked under 5a: the fingers themselves morph (a click on release = a pop), physical and celebratory, and each kernel
# is the size of the painting's shapes. Release Click from 0 to 1 pops the fingers one after another, base row first and
# out toward the tips (the pale finger fading as its kernel swells over it), then two kernels fly off up and to the
# right. Each kernel is lumpy puffs pushed out from its middle in a stagger, over a bigger puff that swells first and
# sinks back behind them (the overshoot), a fill-only core that melts the inner joins, two creased puffs on top and a
# little golden hull last.
CREAM, CREAM2, HULL, HULL2 = '#fffbe0', '#fff3cf', '#ffc93c', '#ff9f43'
DUR = 0.22
# (centre, radius, start, the finger fill it replaces, where it grows from)
KERNELS = [
    ((3392, 3165), 100, 0.00, 'f088', None),  # base row, upper
    ((3415, 3335), 96, 0.07, 'f091', None),   # base row, lower
    ((3520, 3048), 94, 0.18, None, None),     # middle, upper (painted on the body)
    ((3548, 3225), 94, 0.25, None, None),     # middle, lower
    ((3625, 2975), 88, 0.36, 'f089', None),   # tip, upper
    ((3700, 3100), 88, 0.43, 'f090', None),   # tip, lower
    ((3830, 2795), 80, 0.62, None, (3660, 2950)),  # flies off the upper tip
    ((3925, 2960), 74, 0.74, None, (3740, 3080)),  # flies off the lower tip
]
ROLE = {'f088': 'finger-base-upper', 'f091': 'finger-base-lower', 'f089': 'finger-tip-upper', 'f090': 'finger-tip-lower'}


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0) -> str:
    """A lumpy, hand-drawn round shape: n bumps round (x, y), a closed Catmull-Rom curve."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def it(d, fill, edge, at, s, e, out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': 'scale'}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


def kernel(c, r, s, seed, origin=None) -> list[dict]:
    """One popcorn kernel popping at c over [s, s + DUR]. With an origin, it grows out of that point instead (flies)."""
    x, y = c
    rnd = random.Random(seed)
    T = lambda u: s + u * DUR
    flies = origin is not None
    at = lambda q: origin if flies else q
    items = []
    if not flies:  # the overshoot: a big puff that swells first and sinks back behind the others
        items.append(it(lump(x, y, r * 1.18, seed * 7 + 1, 0.12, 7), CREAM, INK, c, T(0), T(0.28), (T(0.32), T(0.8))))
    # five or six big uneven puffs round a lopsided middle, pushed out from it one after another
    n = 5 + seed % 2
    rot = rnd.random() * math.pi
    cx, cy = x + (rnd.random() - 0.5) * r * 0.2, y + (rnd.random() - 0.5) * r * 0.2
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.6
        d = r * (0.42 + rnd.random() * 0.2)
        lr = r * (0.42 + rnd.random() * 0.24)
        lx, ly = cx + math.cos(a) * d, cy + math.sin(a) * d
        u0 = 0.03 + 0.42 * k / n
        items.append(it(lump(lx, ly, lr, seed * 31 + k, 0.17, 7, a), CREAM if k % 3 else CREAM2, INK * 0.9,
                        at(c), T(u0), T(u0 + 0.4)))
    items.append(it(lump(cx, cy, r * 0.62, seed * 13, 0.12, 7), CREAM, 0, at(c), T(0.42), T(0.78)))
    # one puff in front, off to one side, so its outline shows as a crease across the kernel
    a = rot + 0.5
    fx, fy = cx + math.cos(a) * r * 0.36, cy + math.sin(a) * r * 0.36
    items.append(it(lump(fx, fy, r * 0.42, seed * 17, 0.18, 7, a), CREAM2, INK * 0.8, at((fx, fy)), T(0.6), T(0.92)))
    # the golden hull, a little flat nub tucked in at its rim, a different side on each kernel
    a = math.radians((95, 215, 160, 265, 125, 200, 240, 150)[seed % 8])
    hx, hy = cx + math.cos(a) * r * 0.66, cy + math.sin(a) * r * 0.66
    hull = ellipse(hx, hy, r * 0.27, r * 0.17, math.degrees(a) + 90)
    items.append(it(hull, HULL, INK * 0.75, at((hx, hy)), T(0.76), T(1.0)))
    items.append(it(ellipse(hx - math.cos(a) * r * 0.03, hy - math.sin(a) * r * 0.03, r * 0.12, r * 0.06, math.degrees(a) + 90), HULL2, 0,
                    at((hx, hy)), T(0.82), T(1.0)))
    if flies:  # two puffs of steam left behind on its way out, sinking away again
        ox, oy = origin
        for k, u in enumerate((0.3, 0.62)):
            px, py = ox + (x - ox) * u, oy + (y - oy) * u
            items.insert(0, it(lump(px, py, r * (0.3 + 0.1 * k), seed * 29 + k, 0.2, 6), '#ffffff', INK * 0.7, (px, py),
                               T(0.15 + 0.15 * k), T(0.5 + 0.15 * k), (T(0.75 + 0.1 * k), T(1.15 + 0.1 * k))))
    return items


def pop_items() -> list[dict]:
    items = []
    for k, (c, r, s, _, origin) in enumerate(KERNELS):
        items += kernel(c, r, s, k + 3, origin)
    return items


def pop_vanish() -> list[dict]:
    """Each finger fades as its kernel swells over it."""
    return [{'effect': 'vanish', 'parts': [ROLE[f]], 'span': [round(s + 0.03, 3), round(s + 0.12, 3)]}
            for _, _, s, f, _ in KERNELS if f]


def vanish_ink(fid: str) -> list[str]:
    """The ink the app's vanish takes with a fill: the object's own ink lying within 40 px of the fill's box."""
    fills = ['f071', 'f088', 'f089', 'f090', 'f091']
    boxes = [m.FP[f]['bbox'] for f in fills]
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[0] + b[2] for b in boxes), max(b[1] + b[3] for b in boxes)
    w, h = x1 - x0, y1 - y0
    fx, fy, fw, fh = m.FP[fid]['bbox']
    out = []
    for s in m.FP[fid]['ink']:
        bx, by, bw, bh = m.IP[s]['bbox']
        own = bx >= x0 - 0.1 * w and by >= y0 - 0.1 * h and bx + bw <= x1 + 0.1 * w and by + bh <= y1 + 0.1 * h
        if own and bx >= fx - 40 and by >= fy - 40 and bx + bw <= fx + fw + 40 and by + bh <= fy + fh + 40:
            out.append(s)
    return out


def pop_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    gone = [f for _, _, s, f, _ in KERNELS if f and t >= s + 0.075]  # past the middle of its fade
    im = m.compose(fill_over={f: 'M0 0Z' for f in gone}, ink_over={i: 'M0 0Z' for f in gone for i in vanish_ink(f)})
    im.alpha_composite(m.svg(g.sprite_svg(pop_items(), t)))
    return im


def pop_main() -> None:
    out = OUT.parent / 'popcorn'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [pop_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * 5 + 60, th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.2f}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    print('wrote', out)


if __name__ == '__main__' and 'pop' in __import__('sys').argv[1:]:
    pop_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The fan hand: drag for Release Click; its fingers pop into popcorn one after another and two kernels fly off',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': pop_items()}] + pop_vanish(),
        'objectParts': {ROLE[f]: [f] for f in ROLE},
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(pop_items()), 'shapes')
