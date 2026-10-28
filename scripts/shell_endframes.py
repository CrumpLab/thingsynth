# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (tonewheel tuning on Equal) for the striped shell: the brown oval shell at the bottom centre, a
salmon band with a dark wavy stripe swooping across it, sitting on a dark green mound that runs off the painting's
bottom edge, with a yellow ring on its right that the pale trunk of the creature beside it drinks from.

    uv run scripts/shell_endframes.py          # the five end frames and sheet
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
m.CROP = (1950, 3500, 1300, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/tg-tuning/endframes'
p, outlined, circle, ellipse, tube, bez, spiral = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.spiral
INK = 17  # the shell's own outlines measure 17-20 px
BROWN, SALMON, GREEN, YELLOW = '#A58A74', '#E18876', '#74A576', '#FFFB64'
SHELL = ['f027', 'f028', 'f029', 'f030']
RING = (2706.0, 4319.0)  # the yellow ring's centre, where the trunk drinks
# the pale trunk of the creature on the right (f042 is see-through: its purple is the wash showing through)
TRUNK = ['f042', 'f031', 'f032', 'f033', 'f034', 'f039', 'f043']
WASHED = {'f042'}
TAGS = {re.search(r'id="(f\d+)"', t).group(1): t for t in m.FILL_TAGS}
CANDY12 = ['#ff5e7a', '#ff8a3d', '#ffb13d', '#ffe066', '#d4f55a', '#7fd36b', '#5cd6b8', '#2DFFF4', '#7bb7f3',
           '#a98bf0', '#d77bf0', '#ff7fc8']


SHELL_INK = ['i0978', 'i0162', 'i0979', 'i0163', 'i1562', 'i0719', 'i0980', 'i0164', 'i0984', 'i0168']
BODY_INK = ['i0978', 'i0162', 'i0979', 'i0163', 'i1562', 'i0719']  # the oval's outline and its wavy stripe


def draw(front: str = '', again: list[str] | None = None, over: str = '', hide: list[str] | None = None,
         hide_ink: list[str] | None = None) -> Image.Image:
    """The painting (less the fills in `hide` and the ink in `hide_ink`) with `front` drawn over it, then the
    painted shapes in `again` (and their ink, and the wash inside the see-through trunk) laid back on top, then
    `over`."""
    im = m.compose(front=front or '<g/>', fill_over={f: 'M0 0Z' for f in hide or []},
                   ink_over={i: 'M0 0Z' for i in hide_ink or []})
    again = again or []
    if again:
        washed = ''.join(f'<path d="{m.FILLS[f]}" fill="#fff"/>' for f in again if f in WASHED)
        if washed:
            mask = m.svg(washed).getchannel('A')
            w = m.WASH.copy()
            w.putalpha(Image.composite(m.WASH.getchannel('A'), Image.new('L', w.size, 0), mask))
            im.alpha_composite(w)
        im.alpha_composite(m.svg(''.join(TAGS[f] for f in TAGS if f in again)))
        clip = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#fff"/>' for f in again)).getchannel('A')
        sc = m.SCRIB.copy()
        sc.putalpha(Image.composite(m.SCRIB.getchannel('A'), Image.new('L', sc.size, 0), clip))
        im.alpha_composite(sc)
        ink = sorted({s for f in again for s in m.own_ink(f)} | ({*SHELL_INK} if {'f028', 'f029'} & {*again} else set()))
        im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink) + '</g>'))
    if over:
        im.alpha_composite(m.svg(over))
    return im


def closed(P) -> str:
    """A closed Catmull-Rom curve through the points P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, rx, ry, seed, wob=0.1, n=9, rot=0.0) -> str:
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * math.cos(rot) - v * math.sin(rot), y + u * math.sin(rot) + v * math.cos(rot)))
    return closed(P)


def poly(P) -> str:
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


# ---- 1. nautilus: the shell coils into an even spiral, twelve equal chambers to the turn -----------------------------
NC = (2515.0, 4285.0)   # coil centre
NB = 0.11               # growth per radian: each whorl is e^(2 pi b) = 2.4 times the last (an octave a turn)
NR = 320.0              # the outer whorl's radius at its mouth
NROT = math.radians(22)  # the mouth faces down and to the right, onto the yellow ring


def npt(th: float, f: float = 1.0):
    wob = 1 + 0.03 * math.sin(th * 3.1 + 0.7) + 0.02 * math.sin(th * 5.3 + 2) + 0.012 * math.sin(th * 9.7)
    r = NR * math.exp(NB * th) * wob * f
    return NC[0] + math.cos(th + NROT) * r, NC[1] + math.sin(th + NROT) * r


def arc(t0, t1, f=1.0, n=10):
    return [npt(t0 + (t1 - t0) * i / n, f) for i in range(n + 1)]


def septum(t, n=8):
    """A septum across the whorl at angle t, from the outer wall in to the turn below, bowed toward the mouth."""
    a, b = npt(t, 0.92), npt(t - 2 * math.pi)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    tx, ty = -math.sin(t + NROT), math.cos(t + NROT)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    c = (mx + tx * L * 0.22, my + ty * L * 0.22)
    return [((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0],
             (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]) for u in (i / n for i in range(n + 1))]


def chamber(t0: float, t1: float) -> str:
    return poly(septum(t0) + arc(t0, t1, 0.92)[1:] + septum(t1)[::-1][1:] + arc(t1 - 2 * math.pi, t0 - 2 * math.pi)[1:])


def wall(t0: float, t1: float) -> str:
    """The shell's outer wall: a brown band along the outside of the coil."""
    return poly(arc(t0, t1, 1.0, 60) + arc(t1, t0, 0.9, 60))


def nautilus_svg() -> str:
    out = ''
    # the green the shell sat on carries on under where the old oval was (stroked to close the old outline's gap)
    out += ''.join(f'<path d="{m.FILLS[f]}" fill="{GREEN}" stroke="{GREEN}" stroke-width="26" stroke-linejoin="round"/>'
                   for f in ('f028', 'f029'))
    # each turn an octave of twelve equal candy chambers, the inner turns smaller, coiling in to a yellow eye
    out += outlined(circle(*NC, NR * math.exp(NB * -8 * math.pi) * 1.6), YELLOW, INK * 0.7)
    for turn in (3, 2):
        t0 = -2 * math.pi * (turn + 1)
        out += outlined(poly(arc(t0, t0 + 2 * math.pi, 1.0, 60) + arc(t0, t0 - 2 * math.pi, 1.0, 60)[::-1]),
                        (BROWN, SALMON)[turn % 2], INK * 0.8)
    for turn in (1, 0):
        for k in range(12):
            t0 = -2 * math.pi * (turn + 1) + k * math.pi / 6
            out += outlined(chamber(t0, t0 + math.pi / 6), CANDY12[k], INK * 0.9)
    for turn in (1, 0):
        out += outlined(wall(-2 * math.pi * (turn + 1), -2 * math.pi * turn), BROWN, INK * 0.9)
    return out


def v1_nautilus() -> Image.Image:
    """Nautilus: the shell coils into an even spiral, each turn an octave split into twelve equal candy chambers,
    its mouth on the yellow ring (equal temperament is a logarithmic spiral)."""
    return draw(nautilus_svg(), ['f030'] + TRUNK, hide=['f028', 'f029'], hide_ink=BODY_INK)


# ---- 2. snail: what lives in it comes out: a green head with eyes on stalks, smiling --------------------------------
def v2_snail() -> Image.Image:
    """Snail: the green it sits on is a snail's foot; its head rises out in front, up and to the left, two tall
    stalks with round eyes looking about, and a wide smile."""
    X = 65  # everything shifted right of the lying creature's grey eye
    out = ''
    # neck and head: one lumpy limb rising out from under the shell's left end (drawn head-down, so the tube's
    # round cap is tucked under the shell)
    neck = bez((2215 + X, 4080), (2190 + X, 4220), (2240 + X, 4330), (2330 + X, 4400), 24)
    out += outlined(tube(neck, 105, 95), GREEN, INK)
    head = lump(2222 + X, 4030, 125, 105, 4, 0.06, 10)
    for (bx, by), (c1, c2, tip) in [((2165, 3965), ((2140, 3900), (2090, 3840), (2060, 3770))),
                                    ((2275, 3960), ((2300, 3890), (2350, 3830), (2385, 3765)))]:
        P = bez((bx + X, by + 30), (c1[0] + X, c1[1]), (c2[0] + X, c2[1]), (tip[0] + X, tip[1]), 18)
        out += outlined(tube(P, 30, 24), GREEN, INK * 0.9)
    out += outlined(head, GREEN, INK)
    out += f'<path d="{tube(neck, 88, 80)}" fill="{GREEN}"/>'
    for ex, ey, dx in ((2060 + X, 3730, 14), (2385 + X, 3725, -10)):
        out += outlined(circle(ex, ey, 62), '#ffffff', INK)
        out += outlined(circle(ex + dx + 10, ey + 8, 30), '#3b2a52', INK * 0.6)
        out += f'<path d="{circle(ex + dx + 20, ey - 4, 10)}" fill="#fff"/>'
    sm = (f'M{p(2150 + X, 4050)}C{p(2180 + X, 4130)} {p(2280 + X, 4130)} {p(2305 + X, 4040)}'
          f'C{p(2260 + X, 4075)} {p(2195 + X, 4078)} {p(2150 + X, 4050)}Z')
    out += outlined(sm, '#e0466a', INK * 0.8)
    out += outlined(ellipse(2140 + X, 4005, 26, 18), '#ff9fc4', INK * 0.6)
    return draw(out, ['f028', 'f029', 'f030'] + TRUNK)


# ---- 3. streamers: its stripes peel up off it as fat curling candy ribbons ------------------------------------------
FAN_C = (2560.0, 4250.0)


def rib(a0: float, a1: float, r0: float, r1: float, seed: int) -> str:
    """One rib of a scallop fan: a long wedge from near the hinge out to a rounded, lumpy scallop at its rim."""
    rnd = random.Random(seed)
    x, y = FAN_C
    am = (a0 + a1) / 2
    R = r1 * (1 + (rnd.random() - 0.5) * 0.06)
    P = [(x + math.cos(a0) * r0, y + math.sin(a0) * r0)]
    for i in range(1, 6):
        u = i / 6
        a = a0 + (rnd.random() - 0.5) * 0.02
        P.append((x + math.cos(a) * (r0 + (R * 0.93 - r0) * u), y + math.sin(a) * (r0 + (R * 0.93 - r0) * u)))
    for i in range(9):  # the rounded scallop tip
        a = a0 + (a1 - a0) * i / 8
        bump = math.sin(math.pi * i / 8) * (R * 0.07)
        P.append((x + math.cos(a) * (R * 0.93 + bump), y + math.sin(a) * (R * 0.93 + bump)))
    for i in range(5, 0, -1):
        u = i / 6
        a = a1 + (rnd.random() - 0.5) * 0.02
        P.append((x + math.cos(a) * (r0 + (R * 0.93 - r0) * u), y + math.sin(a) * (r0 + (R * 0.93 - r0) * u)))
    P.append((x + math.cos(a1) * r0, y + math.sin(a1) * r0))
    return closed(P)


def v3_scallop() -> Image.Image:
    """Scallop fan: a big scallop shell fans open behind it, twelve equal candy ribs, like a peacock's tail."""
    out = ''
    lo, hi = math.radians(-172), math.radians(-8)
    step = (hi - lo) / 12
    for k in range(12):
        a0 = lo + k * step
        out += outlined(rib(a0 - step * 0.06, a0 + step * 1.06, 30, 540 - abs(k - 5.5) * 14, k), CANDY12[k], INK)
    return draw(out, ['f028', 'f029', 'f030'] + TRUNK)


# ---- 4. violin scroll: the shell's coil rises into a scroll, with four tuning pegs ----------------------------------
def v4_scroll() -> Image.Image:
    """Tuning pegs: the shell's left end rises into a fiddle's scroll, curled like a snail, and four fat tuning
    pegs stick out of its neck, two a side."""
    out = ''
    # pegs behind the neck, staggered like a fiddle's pegbox, each shaft starting inside the neck
    dx = -50  # the whole pegbox sits a little left of the shell's middle, clear of the trunk
    pegs = [(2400 + dx, 4090, -1, 8), (2400 + dx, 3950, -1, -6), (2495 + dx, 4020, 1, -8), (2490 + dx, 3880, 1, 6)]
    for x, y, s, tilt in pegs:
        a = math.radians(tilt)
        R = lambda u, v: (x + s * (u * math.cos(a) - v * math.sin(a)), y + u * math.sin(a) * s + v * math.cos(a))
        out += outlined(poly([R(0, -20), R(110, -17), R(110, 17), R(0, 20)]), '#6e4b3a', INK * 0.8)
        head = closed([R(125, -10), R(150, -62), R(210, -70), R(242, -30), R(232, 30), R(192, 66), R(142, 52), R(128, 12)])
        out += outlined(head, '#6e4b3a', INK)
        out += outlined(ellipse(*R(118, 0), 18, 32), YELLOW, INK * 0.7)
    # the neck: a broad brown tower from the shell's top
    neck = closed([(2370 + dx, 4230), (2365 + dx, 4050), (2380 + dx, 3900), (2440 + dx, 3845), (2505 + dx, 3900),
                   (2520 + dx, 4050), (2540 + dx, 4220)])
    out += outlined(neck, BROWN, INK)
    out += outlined(closed([(2405 + dx, 4200), (2410 + dx, 4040), (2430 + dx, 3920), (2455 + dx, 3920),
                            (2480 + dx, 4040), (2490 + dx, 4200)]), SALMON, INK * 0.7)
    # the scroll: a fat spiral curling over the top
    P = spiral(2445 + dx, 3880, math.radians(-160), 95, 1.55, 0.72, 1, 60)
    out += outlined(tube(P, 68, 34), BROWN, INK)
    out += f'<path d="{tube(P[6:], 28, 14)}" fill="{SALMON}"/>'
    out += outlined(circle(*P[-1], 30), SALMON, INK * 0.7)
    return draw(out, ['f028', 'f029', 'f030'] + TRUNK)


# ---- 5. spire: the shell stacks up into a tall turreted spire, whorl on whorl ---------------------------------------
def whorl(x, y, w, h, seed, tilt=-7.0) -> str:
    """One turn of the spire: a lumpy brown bun, sloping like a coil, with the shell's salmon band and dark wavy
    stripe across its lower half."""
    a = math.radians(tilt)
    d = lump(x, y, w / 2, h / 2, seed, 0.05, 11, a)
    R = lambda u, v: (x + u * w / 2 * math.cos(a) - v * h / 2 * math.sin(a), y + u * w / 2 * math.sin(a) + v * h / 2 * math.cos(a))
    band = closed([R(-1.1, 0.0), R(-0.5, -0.12), R(0.1, 0.05), R(0.6, -0.05), R(1.1, 0.1), R(1.1, 1.2), R(-1.1, 1.2)])
    stripe = closed([R(-0.8, 0.42), R(-0.3, 0.3), R(0.2, 0.5), R(0.75, 0.4), R(0.2, 0.62), R(-0.3, 0.44)])
    return (outlined(d, BROWN, INK) + f'<clipPath id="c{seed}"><path d="{d}"/></clipPath><g clip-path="url(#c{seed})">'
            + outlined(band, SALMON, INK * 0.8) + f'<path d="{stripe}" fill="#000"/></g>'
            + f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>')


def v5_spire() -> Image.Image:
    """Spire: the shell coils up into a tall turreted spire, whorl on whorl, each smaller and banded, to a point."""
    out = ''
    tip = closed([(2392, 3560), (2440, 3660), (2420, 3700), (2365, 3695), (2352, 3660)])
    out += outlined(tip, SALMON, INK)
    for x, y, w, h, s in [(2400, 3710, 130, 80, 1), (2425, 3785, 195, 105, 2), (2455, 3880, 270, 130, 3),
                          (2490, 3995, 350, 155, 4), (2530, 4120, 430, 180, 5)]:
        out += whorl(x, y, w, h, s)
    return draw(out, ['f028', 'f029', 'f030'] + TRUNK)


VERSIONS = [
    ('1-nautilus', 'Nautilus', v1_nautilus),
    ('2-snail', 'Snail', v2_snail),
    ('3-scallop-fan', 'Scallop fan', v3_scallop),
    ('4-tuning-pegs', 'Tuning pegs', v4_scroll),
    ('5-spire', 'Spire', v5_spire),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Gear)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.5
    tw, th = int(w * s), int(h * s)
    sheet = Image.new('RGB', (tw * 3 + 40, (th + 46) * 2 + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = 10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 46)
        d.text((x, y), label, fill='black', font=font)
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 32))
    sheet.save(OUT / 'sheet.png')
    print('wrote', OUT / 'sheet.png')


if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    main()


# ---- chosen: nautilus ----------------------------------------------------------------------------------------------
# Picked (on its own) under 5a: the shell changes in its own nature, coiling into a nautilus, and it reads Equal
# literally: equal temperament is a logarithmic spiral, each turn an octave, twelve equal chambers to the turn. Softened
# from the end frame's colour wheel: the shell's own browns and salmon for most chambers, a few candy accents, lumpier
# septa, a wider outer wall. On an 800 ms glide: the oval swells into the coil's outer wall (0-0.28), the coil winds in
# from its mouth with a sweep, one turn after another (0.22-0.74), then the chambers pop in from the outside inward,
# their outlines laying down the septa, twelve to a turn (0.62-1). The yellow ring stays the coil's mouth, with the
# trunk still drinking from it: placed around, the ring and the trunk's shapes in front.
TAN, DEEP = '#C7A487', '#8A6C58'
WALL = 0.83                 # the outer wall: the outer 17% of the outer turn
OVAL_C = (2580.0, 4290.0)   # the old oval's middle, where the coil swells from
MOUTH = -math.degrees(NROT)  # the mouth's direction in the app's angles (0 = right, 90 = up)
# (band colour, the odd chambers' colours by k) per turn, outside in; k counts from the inner end of the turn to its mouth
TURNS = [
    (SALMON, {1: TAN, 3: '#ff7fc8', 5: TAN, 7: '#ffe066', 9: TAN, 11: '#2DFFF4'}),
    (TAN, {1: SALMON, 3: SALMON, 5: '#d4f55a', 7: SALMON, 9: SALMON, 11: '#c4a3f0'}),
    (SALMON, {k: DEEP for k in (1, 3, 5, 7, 9, 11)}),
    (DEEP, {}),
]
SWEEP = [(0.22, 0.48), (0.36, 0.58), (0.46, 0.66), (0.54, 0.72)]
POPS = [(0.62, 0.84), (0.71, 0.92), (0.79, 1.0)]  # the window each turn's chambers pop across
ROLE_RING = 'ring'


def outer(j: int) -> float:
    return WALL if j == 0 else 1.0


def lumpy_septum(t: float, j: int, seed: int, n=10) -> list:
    """A septum across turn j at angle t, from its outer edge in to the turn below: bowed toward the mouth, and
    wobbling like a hand-drawn line."""
    rnd = random.Random(seed)
    a, b = npt(t, outer(j)), npt(t - 2 * math.pi)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    tx, ty = -math.sin(t + NROT), math.cos(t + NROT)  # toward the mouth
    a1, a2 = (rnd.random() - 0.5) * 0.16, (rnd.random() - 0.5) * 0.12
    P = []
    for i in range(n + 1):
        u = i / n
        off = L * (0.2 * 4 * u * (1 - u) + math.sin(math.pi * u) * (a1 * math.sin(math.pi * u) + a2 * math.sin(2 * math.pi * u)))
        P.append((a[0] + ux * L * u + tx * off, a[1] + uy * L * u + ty * off))
    return P


def band(j: int) -> str:
    t0, t1 = -2 * math.pi * (j + 1), -2 * math.pi * j
    return poly(arc(t0, t1, outer(j), 80) + arc(t1 - 2 * math.pi, t0 - 2 * math.pi, 1.0, 80))


def centroid(d_pts) -> tuple[float, float]:
    return sum(q[0] for q in d_pts) / len(d_pts), sum(q[1] for q in d_pts) / len(d_pts)


def r1(v: float) -> float:
    return round(v, 1)


def nautilus_items() -> list[dict]:
    items = []
    # the green the shell sat on, carrying on where the old oval and its lines were (fill only), and the coil's whole
    # silhouette, its outer wall, swelling out of the oval
    green = ''.join(m.FILLS[f] for f in ('f028', 'f029')) + ''.join(m.INKS[i] for i in BODY_INK)
    items.append(it(green, GREEN, 0, OVAL_C, 0.06, 0.28))
    sil = poly(arc(-2 * math.pi, 0, 1.0, 120))
    items.append(it(sil, BROWN, INK, OVAL_C, 0.0, 0.28))
    # the turns wind in from the mouth, one after another
    for j, (col, _) in enumerate(TURNS):
        o = it(band(j), col, INK * (1 if j < 2 else 0.8), NC, *SWEEP[j])
        o['sweep'] = {'from': round(MOUTH, 1), 'to': round(MOUTH + 360, 1)}
        items.append(o)
    eye = lump(*npt(-8 * math.pi, 0.2), 34, 31, 7, 0.08, 7)
    items.append(it(eye, YELLOW, INK * 0.7, npt(-8 * math.pi, 0.2), 0.66, 0.78))
    # the chambers pop in, outside in and from the mouth inward, their outlines the septa: twelve to a turn
    for j, (_, cols) in enumerate(TURNS[:3]):
        lo, hi = POPS[j]
        order = sorted(cols, reverse=True)
        for n, k in enumerate(order):
            t0 = -2 * math.pi * (j + 1) + k * math.pi / 6
            s0, s1 = lumpy_septum(t0, j, 100 * j + k), lumpy_septum(t0 + math.pi / 6, j, 100 * j + k + 1)
            P = s0[::-1] + arc(t0, t0 + math.pi / 6, outer(j), 10)[1:-1] + s1 + arc(t0 + math.pi / 6 - 2 * math.pi, t0 - 2 * math.pi, 1.0, 10)[1:-1]
            s = lo + (hi - lo - 0.1) * n / max(1, len(order) - 1)
            items.append(it(poly(P), cols[k], INK * (0.9, 0.8, 0.55)[j], centroid(P), s, s + 0.1))
    return items


def it(d, fill, edge, at, s, e) -> dict:
    return {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [r1(at[0]), r1(at[1])], 'start': round(s, 3),
            'end': round(min(1.0, e), 3), 'grow': 'scale'}


def spr_svg(items, t) -> str:
    """The app's sprites at t: each grows from `at` over its window (out-cubic), or with `sweep` is revealed by a wedge
    round `at` turning from `from` to `to` degrees (0 = right, 90 = up)."""
    out = ''
    for n, q in enumerate(items):
        v = 1 - (1 - max(0.0, min(1.0, (t - q['start']) / max(1e-6, q['end'] - q['start'])))) ** 3
        x, y = q['at']
        stroke = f' stroke="#000" stroke-width="{q["edge"]}" stroke-linejoin="round"' if q['edge'] > 0 else ''
        if 'sweep' in q:
            if v <= 0.005:
                continue
            a0 = q['sweep']['from']
            a1 = a0 + (q['sweep']['to'] - a0) * v
            pts = [(x, y)] + [(x + math.cos(math.radians(a0 + (a1 - a0) * i / 24)) * 5000,
                               y - math.sin(math.radians(a0 + (a1 - a0) * i / 24)) * 5000) for i in range(25)]
            out += (f'<clipPath id="w{n}"><path d="{poly(pts)}"/></clipPath>'
                    f'<path d="{q["d"]}" fill="{q["fill"]}"{stroke} clip-path="url(#w{n})"/>')
            continue
        if v <= 0.01:
            continue
        out += f'<path d="{q["d"]}" fill="{q["fill"]}"{stroke} transform="translate({x} {y}) scale({v:.4f}) translate({-x} {-y})"/>'
    return out


def around(sprites: str, front: list[str]) -> Image.Image:
    """The painting with the sprites above its ink, masked like the app's `around`: the front shapes, and a band as
    wide as the ink round them, stay in front."""
    im = m.compose()
    if not sprites:
        return im
    sp = m.svg(sprites)
    mk = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#fff" stroke="#fff" stroke-width="44" stroke-linejoin="round"/>'
                       for f in front)).getchannel('A')
    a = sp.getchannel('A')
    sp.putalpha(Image.composite(Image.new('L', a.size, 0), a, mk))
    im.alpha_composite(sp)
    return im


def naut_frame(t: float) -> Image.Image:
    return around(spr_svg(nautilus_items(), t) if t > 0 else '', ['f030'] + TRUNK)


def naut_main() -> None:
    out = OUT.parent / 'nautilus'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [naut_frame(t) for t in frames]
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


if __name__ == '__main__' and 'naut' in __import__('sys').argv[1:]:
    naut_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The striped shell: tap for Gear or Equal tuning; on Equal it swells and coils into a nautilus, '
                 'twelve equal chambers to every turn',
        'glide': 800,
        'effects': [{'effect': 'sprites', 'place': 'around', 'parts': [ROLE_RING], 'front': TRUNK,
                     'items': nautilus_items()}],
        'objectParts': {ROLE_RING: ['f030']},
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(nautilus_items()), 'shapes')
