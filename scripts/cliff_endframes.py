# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (master tuning at 450 Hz, its sharpest) for the grey cliff, left (f104).

The cliff is the big translucent grey mass behind everything on the left. Most of it is hidden behind the horn blob,
the yellow streamers, the eye tree and the eye bush; what shows is its open face in the middle (between the yellow
streamer, the pink heart creature and the eye bush) and the long slope running down to the stream at its right edge,
with the little crag ticks drawn on it. Every idea lives on that face and slope.

    uv run scripts/cliff_endframes.py          # the five end frames and sheet
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (850, 1950, 1250, 1400)
m.PX = 1000
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-master/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 16
ROCK, ROCK_L, ROCK_D = '#a49fa6', '#cdc8cf', '#87828c'
CLIFF, CLIFF_A = '#818181', 0.68  # the cliff's own fill
CYAN, PINK, LAV, YEL, MINT, ORANGE, MAGENTA = '#7FFFF6', '#FF89FC', '#c4a3f0', '#FFE47F', '#89FF8C', '#ff9f43', '#FF47C7'
# painted shapes that stay in front of anything new: the eye bush, its eye and fruits, the pink heart creature
FRONT_IDS = ['f118', 'f121', 'f122', 'f123', 'f124', 'f125', 'f126', 'f128', 'f129', 'f130', 'f131', 'f132']


def front_mask() -> Image.Image:
    body = ''.join(f'<path d="{m.FILLS[f]}" fill="#000"/>' for f in FRONT_IDS)
    body += ''.join(f'<path d="{m.INKS[i]}" fill="#000"/>' for f in FRONT_IDS for i in m.own_ink(f))
    return m.svg(body).getchannel('A')


def draw(layer: str, over: str = '') -> Image.Image:
    """The painting, then the new shapes masked off where the front shapes are (as the app's `around` does), then
    `over` on top of everything."""
    im = m.compose()
    lay = m.svg(layer)
    a = ImageChops.multiply(lay.getchannel('A'), ImageChops.invert(front_mask()))
    lay.putalpha(a)
    im.alpha_composite(lay)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def closed(pts) -> str:
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def opened(pts) -> str:
    """An open Catmull-Rom curve through the points."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d


def blob(cx, cy, rx, ry, seed=0, wob=0.08, n=11, rot=0.0) -> str:
    """A lumpy hand-drawn oval, rotated by rot degrees."""
    rnd = random.Random(seed)
    r0 = math.radians(rot)
    pts = []
    for k in range(n):
        a = k / n * 2 * math.pi
        f = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r0) - y * math.sin(r0), cy + x * math.sin(r0) + y * math.cos(r0)))
    return closed(pts)


def edged(d_closed: str, d_open: str, colour: str, width=INK) -> str:
    """A filled shape whose outline is only the open part (it leaves its join with the cliff unlined)."""
    return (f'<path d="{d_closed}" fill="{colour}"/><path d="{d_open}" fill="none" stroke="#000" stroke-width="{width}" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def rock(d: str, width=INK) -> str:
    """Broken rock in the cliff's own translucent grey (over a little paper, as the cliff lies over the wash)."""
    return (f'<path d="{d}" fill="#ffffff" fill-opacity="0.5"/><path d="{d}" fill="{CLIFF}" fill-opacity="0.8"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="{width}" stroke-linejoin="round"/>')


def taper(d_fill: str) -> str:
    return f'<path d="{d_fill}" fill="#000"/>'


def lumpy_tube(P, w0, w1, seed, jit=0.07) -> str:
    rnd = random.Random(seed)
    ph1, ph2 = rnd.random() * 6, rnd.random() * 6
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = w0 + (w1 - w0) * u
        L.append((x + nx * w * (1 + jit * math.sin(u * 9 + ph1)), y + ny * w * (1 + jit * math.sin(u * 9 + ph1))))
        R.append((x - nx * w * (1 + jit * math.sin(u * 7 + ph2)), y - ny * w * (1 + jit * math.sin(u * 7 + ph2))))
    rr = math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1]) / 2
    return 'M' + 'L'.join(p(*q) for q in L) + f'A{rr:.1f} {rr * 1.1:.1f} 0 0 1 {p(*R[-1])}' + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def crescent(cx, cy, r, a0, a1, w, colour) -> str:
    """An outlined sound crescent: an arc round (cx, cy) from a0 to a1 degrees, thickest in its middle."""
    n = 24
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        t = w * math.sin(math.pi * u) + 3
        outer.append((cx + math.cos(a) * (r + t / 2), cy + math.sin(a) * (r + t / 2)))
        inner.append((cx + math.cos(a) * (r - t / 2), cy + math.sin(a) * (r - t / 2)))
    d = 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'
    return outlined(d, colour, INK * 0.8)


def eye(cx, cy, rx, ry, rot=0.0, iris=CYAN, look=(0.25, 0.0), lid=None) -> str:
    """The painting's eye: a lumpy white almond with a heavy outline, a big iris and pupil, and a lid whose line runs
    on past the eye in a tapered flick."""
    out = outlined(blob(cx, cy, rx, ry, 7, 0.05, 12, rot), '#ffffff', INK * 1.1)
    ix, iy = cx + look[0] * rx, cy + look[1] * ry
    out += outlined(blob(ix, iy, rx * 0.5, ry * 0.62, 3, 0.05, 10), iris, INK * 0.7)
    out += f'<path d="{blob(ix + rx * 0.06, iy, rx * 0.24, ry * 0.32, 4, 0.05, 9)}" fill="#111"/>'
    out += f'<path d="{circle(ix + rx * 0.16, iy - ry * 0.18, rx * 0.08)}" fill="#fff"/>'
    if lid:
        out += outlined(lid, ROCK_L, INK * 1.1)
    # the flick: a tapered black wedge off the back corner of the eye
    r0 = math.radians(rot)
    bx, by = cx - math.cos(r0) * rx * 0.95, cy - math.sin(r0) * rx * 0.95
    fl = bez((bx, by), (bx - 40, by - 4), (bx - 70, by - 18), (bx - 92, by - 42), 12)
    out += taper(tube(fl, 9, 2))
    return out


# ---- 1. crystals ---------------------------------------------------------------------------------------------------
def crystal(bx, by, ang, L, W, colour, seed) -> str:
    """A big candy quartz point standing out of the rock at (bx, by), pointing at ang degrees: a hand-drawn prism
    with an uneven faceted tip and one lighter face, its foot hidden in the rock collar."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    J = lambda k=0.1: (rnd.random() - 0.5) * W * k
    P = lambda s, t: (bx + ux * s + vx * t, by + uy * s + vy * t)
    sh_l, sh_r = L * (0.66 + rnd.random() * 0.08), L * (0.7 + rnd.random() * 0.08)
    tip = (L, W * (rnd.random() - 0.5) * 0.25)
    mid = 0.12 + (rnd.random() - 0.5) * 0.1
    body = [P(-40, -W / 2), P(L * 0.35, -W / 2 - W * 0.04 + J()), P(sh_l, -W / 2 + J()), P(*tip), P(sh_r, W / 2 + J()),
            P(L * 0.4, W / 2 + W * 0.05 + J()), P(-40, W / 2)]
    d = 'M' + 'L'.join(p(*q) for q in body) + 'Z'
    face = [P(-40, -W * 0.1), P(sh_l * 0.98, W * (mid - 0.18)), P(*tip), P(sh_r * 0.98, W * (mid + 0.22)), P(-40, W * 0.2)]
    fd = 'M' + 'L'.join(p(*q) for q in face) + 'Z'
    ridge = f'M{p(*P(sh_l * 0.98, W * (mid - 0.18)))}L{p(*P(sh_r * 0.98, W * (mid + 0.22)))}'
    k = INK * 0.7
    return (f'<path d="{d}" fill="{colour}"/><path d="{fd}" fill="#ffffff" fill-opacity="0.5"/>'
            f'<path d="{fd}" fill="none" stroke="#000" stroke-width="{k}" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{ridge}" fill="none" stroke="#000" stroke-width="{k}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round" stroke-linecap="round"/>')


CLUSTERS = [
    # base of the cluster, its rock collar (rx, ry, tilt), then (angle, length, width, colour)
    ((1265, 2585), (175, 70, -4), [(-158, 250, 105, LAV), (-128, 390, 130, CYAN), (-98, 470, 150, PINK), (-70, 360, 125, YEL)]),
    ((1490, 2480), (85, 60, -30), [(-40, 300, 110, MINT), (-5, 230, 95, PINK)]),
    ((1650, 2935), (130, 60, -20), [(-115, 260, 100, YEL), (-80, 360, 125, CYAN), (-45, 290, 108, LAV)]),
]


def v1_crystals() -> Image.Image:
    """Crystals: big candy quartz points burst out of the cliff's open face and its slope in clusters, each out of a
    collar of broken rock: the cliff itself gone sharp and bright (and quartz is what keeps tuning)."""
    out = ''
    for k, ((bx, by), (rx, ry, tilt), cr) in enumerate(CLUSTERS):
        for j, (ang, L, W, col) in enumerate(cr):
            out += crystal(bx, by, ang, L, W, col, k * 10 + j)
        out += rock(blob(bx, by + 18, rx, ry, k + 40, 0.15, 11, tilt))
        out += outlined(blob(bx - rx * 0.4, by + 8, rx * 0.36, ry * 0.5, k + 50, 0.16, 9, tilt), ROCK_L, INK * 0.8)
    return draw(out)


# ---- 2. singing cliff face -----------------------------------------------------------------------------------------
def crag(x, y, ang, L, w=14) -> str:
    """One of the painting's crag ticks: a tapered black wedge (a filled shape, not a stroke)."""
    a = math.radians(ang)
    P = bez((x, y), (x + math.cos(a) * L * 0.35, y + math.sin(a) * L * 0.35), (x + math.cos(a + 0.2) * L * 0.7, y + math.sin(a + 0.2) * L * 0.7),
            (x + math.cos(a + 0.3) * L, y + math.sin(a + 0.3) * L), 12)
    return taper(tube(P, w / 2, 1.5))


def v2_face() -> Image.Image:
    """Cliff face: the cliff's right edge, where it drops to the stream, juts out into a big craggy profile looking
    right (a heavy brow, a long nose, a jaw); its eye opens under the brow and its mouth opens wide, singing high."""
    edge = [(1440, 2365), (1560, 2372), (1655, 2400), (1672, 2450), (1610, 2478), (1560, 2480), (1600, 2530), (1680, 2590),
            (1765, 2650), (1748, 2690), (1680, 2700), (1640, 2712), (1700, 2760), (1750, 2840), (1700, 2880), (1660, 2930),
            (1730, 2990), (1760, 3060)]
    back = [(1700, 3080), (1560, 2900), (1470, 2700), (1400, 2500)]
    face = closed(edge + back)
    out = f'<path d="{face}" fill="#ffffff" fill-opacity="0.5"/>'  # the paper under it, as under the cliff
    out += f'<path d="{face}" fill="{CLIFF}" fill-opacity="0.8"/>'
    out += f'<path d="{opened(edge)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round" stroke-linecap="round"/>'
    # the open mouth: a dark cave between the lips, with a pink tongue
    mouth = 'M' + 'L'.join(p(*q) for q in [(1650, 2712), (1730, 2712), (1770, 2760), (1760, 2830), (1700, 2836), (1650, 2770)])
    out += outlined(closed([(1640, 2712), (1735, 2706), (1790, 2760), (1770, 2836), (1700, 2846), (1650, 2780)]), '#3b2140', INK)
    out += f'<path d="{blob(1720, 2808, 44, 22, 12, 0.08, 9, -15)}" fill="#ff7fb0"/>'
    # lips over the mouth's corners, so it reads as opened
    out += outlined(blob(1712, 2702, 70, 24, 21, 0.08, 9, 8), ROCK_L, INK)
    out += outlined(blob(1722, 2852, 62, 26, 22, 0.08, 9, -12), ROCK_L, INK)
    # brow ledge, cheekbone, chin: lighter rock lumps that make it carved stone
    out += outlined(blob(1575, 2410, 95, 34, 14, 0.1, 10, 8), ROCK_L, INK)
    out += outlined(blob(1560, 2650, 58, 42, 15, 0.12, 9, 30), ROCK_L, INK * 0.85)
    out += crag(1470, 2560, 70, 90) + crag(1520, 2770, 60, 100) + crag(1600, 2960, 55, 90) + crag(1650, 2500, 110, 60)
    # the eye under the brow, looking right and up, with a heavy lid
    out += eye(1535, 2515, 86, 54, 4, CYAN, (0.35, -0.05))
    over = crescent(1790, 2770, 120, -55, 40, 26, PINK) + crescent(1790, 2770, 205, -48, 34, 30, YEL)
    return draw(out, over)


# ---- 3. organ pipes ------------------------------------------------------------------------------------------------
PIPES = [  # x centre, foot, top, width, stone, cap colour
    (1230, 2650, 2190, 128, '#b8acc6', CYAN),
    (1360, 2665, 2080, 140, '#a9a4ae', PINK),
    (1480, 2705, 2190, 130, '#c9b3c3', YEL),
    (1595, 2830, 2360, 124, '#b0a7bd', LAV),
    (1700, 2955, 2540, 116, '#a9a4ae', MINT),
    (1800, 3090, 2720, 108, '#c9b3c3', ORANGE),
]


def pipe(x, foot, top, w, stone, cap, seed) -> str:
    rnd = random.Random(seed)
    n = 6
    lean = (rnd.random() - 0.5) * 30
    L = [(x - w / 2 + lean * i / n + (rnd.random() - 0.5) * 16, foot + (top - foot) * i / n) for i in range(n + 1)]
    R = [(x + w / 2 + lean * i / n + (rnd.random() - 0.5) * 16, foot + (top - foot) * i / n) for i in range(n + 1)]
    tx = (L[-1][0] + R[-1][0]) / 2
    body_d = 'M' + opened(L)[1:] + 'L' + opened(R[::-1])[1:] + 'Z'
    out = f'<path d="{body_d}" fill="{stone}"/>'
    fx = [(q[0] + w * 0.28, q[1]) for q in L]  # a lighter facet down its left side
    out += f'<path d="M{opened(L)[1:]}L{opened(fx[::-1])[1:]}Z" fill="#ffffff" fill-opacity="0.35"/>'
    for side in (L, R):
        out += f'<path d="{opened(side)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
    # the top: a lumpy hexagonal cap in a candy colour, its rim lit
    out += outlined(blob(tx, top, w * 0.58, w * 0.21, seed + 3, 0.07, 6, lean * 0.1), cap, INK)
    out += f'<path d="{blob(tx - w * 0.1, top - 3, w * 0.3, w * 0.07, seed + 4, 0.08, 6)}" fill="#ffffff" fill-opacity="0.65"/>'
    # the organ-pipe mouth a third of the way up: a dark slot under a pointed upper lip
    my = foot + (top - foot) * 0.3
    mx = x + lean * 0.3
    mw, mh = w * 0.3, 34
    slot = closed([(mx - mw, my), (mx, my - mh * 1.4), (mx + mw, my), (mx + mw * 0.9, my + mh * 0.5), (mx - mw * 0.9, my + mh * 0.5)])
    out += outlined(slot, '#2f2338', INK * 0.8)
    return out


def v3_pipes() -> Image.Image:
    """Organ pipes: the cliff's face cracks into a row of basalt columns (the rock formation called organ pipes),
    stepping down the slope to the stream, each with a pipe mouth and a candy cap."""
    out = ''
    for k, (x, foot, top, w, stone, cap) in enumerate(PIPES):
        out += pipe(x, foot, top, w, stone, cap, k * 7 + 1)
        out += rock(blob(x + 10, foot + 6, w * 0.78, 42, k + 70, 0.16, 9))
    return draw(out)


# ---- 4. tuning fork ------------------------------------------------------------------------------------------------
def v4_fork() -> Image.Image:
    """Tuning fork: a giant steel tuning fork stands struck deep into the cliff like a sword in a stone, ringing,
    candy sound crescents pulsing off its prongs."""
    fx, fy = 1300.0, 2620.0  # where it goes into the rock
    ang = -10.0
    a = math.radians(ang)

    def T(u, v):  # u up the fork, v across it, leaning by ang
        return (fx + v * math.cos(a) + u * math.sin(a), fy - u * math.cos(a) + v * math.sin(a))
    STEEL, STEEL_L = '#d9dde8', '#f7f9ff'
    stem = closed([T(u, v) for u, v in [(-30, -30), (90, -33), (200, -30), (200, 30), (90, 33), (-30, 30)]])
    # the yoke and prongs as one lumpy U
    U = [(180, -34), (215, -95), (300, -122), (420, -120), (560, -118), (618, -110), (622, -46), (560, -44), (420, -42),
         (330, -40), (300, 0), (330, 40), (420, 42), (560, 44), (622, 46), (618, 110), (560, 118), (420, 120), (300, 122),
         (215, 95), (180, 34)]
    out = outlined(stem, STEEL, INK) + outlined(closed([T(u, v) for u, v in U]), STEEL, INK)
    for v in (-82, 82):  # a shine down each prong
        out += f'<path d="{closed([T(u, w) for u, w in [(330, v - 20), (590, v - 22), (592, v - 6), (330, v - 4)]])}" fill="{STEEL_L}"/>'
    # the ball on its foot and the broken rock round where it's struck in
    out += rock(blob(fx + 5, fy + 22, 160, 56, 81, 0.16, 11, -4))
    out += outlined(blob(fx - 105, fy + 10, 58, 34, 82, 0.15, 9), ROCK_L, INK * 0.85)
    out += rock(blob(fx + 110, fy + 14, 52, 30, 83, 0.15, 9), INK * 0.85)
    over = ''
    for s, base in ((-1, 180), (1, 0)):
        tx, ty = T(560, s * 82)
        for k, (r, col) in enumerate([(110, PINK), (190, YEL), (270, CYAN)]):
            over += crescent(tx, ty, r, base - 38 + ang, base + 38 + ang, 20 + k * 5, col)
    return draw(out, over)


# ---- 5. mountain goat ----------------------------------------------------------------------------------------------
def v5_goat() -> Image.Image:
    """Mountain goat: a big shaggy cream goat has climbed onto the cliff's open face and stands on its ledge, head up
    and bleating a high note, with big curled candy horns (the cliff's own creature arriving)."""
    CREAM, CREAM2, HORN, HORN2 = '#f7f1e3', '#e9dfc9', '#ffcf5a', '#ff9f43'
    out = ''
    legs = [((1270, 2570), (1250, 2690)), ((1330, 2585), (1330, 2700)), ((1450, 2580), (1470, 2690)), ((1500, 2560), (1545, 2665))]
    for k, (a, b) in enumerate(legs):
        P = bez(a, (a[0], a[1] + 40), (b[0], b[1] - 40), b, 12)
        out += outlined(lumpy_tube(P, 30, 22, k + 90), CREAM if k % 2 else CREAM2, INK * 0.9)
        out += outlined(blob(b[0] + 4, b[1] + 8, 28, 17, k + 95, 0.08, 8), '#4a3b4f', INK * 0.8)
    out += outlined(blob(1200, 2480, 34, 24, 99, 0.12, 8, -30), CREAM, INK * 0.85)  # tail tuft
    body = blob(1380, 2520, 185, 95, 91, 0.07, 13, -8)
    out += outlined(body, CREAM, INK)
    for k, (x, y) in enumerate([(1290, 2560), (1385, 2575), (1470, 2540)]):  # shaggy flank lumps
        out += outlined(blob(x, y, 52, 26, 100 + k, 0.15, 8, -8), CREAM2, INK * 0.75)
    neck = lumpy_tube(bez((1500, 2500), (1540, 2470), (1590, 2445), (1630, 2420), 12), 74, 58, 92)
    out += outlined(neck, CREAM, INK)
    out += '<g transform="translate(40 20)">'  # the head, shifted clear of the heart creature
    # a big ibex horn sweeping back over its neck, ridged
    hp = bez((1640, 2350), (1615, 2250), (1520, 2245), (1470, 2330), 24)
    out += outlined(lumpy_tube(hp, 46, 13, 94, 0.04), HORN, INK)
    for u in (0.2, 0.36, 0.52, 0.68):
        i = int(u * (len(hp) - 1))
        (x0, y0), (x1, y1) = hp[i - 1], hp[i + 1]
        aa = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
        w = (46 - 33 * u) * 0.9
        rid = [(hp[i][0] + math.cos(aa) * w, hp[i][1] + math.sin(aa) * w), (hp[i][0] - math.cos(aa) * w * 0.2, hp[i][1] - math.sin(aa) * w * 0.2)]
        out += taper(tube(rid, 5, 1.5))
    beard = closed([(1640, 2430), (1690, 2445), (1680, 2540), (1660, 2560), (1650, 2470)])
    out += outlined(beard, CREAM2, INK * 0.85)
    head = blob(1650, 2390, 98, 60, 93, 0.06, 12, 30)
    out += outlined(head, CREAM, INK)
    out += outlined(blob(1592, 2350, 52, 22, 96, 0.1, 8, -20), '#ffb3d9', INK * 0.8)  # ear
    # bleating mouth at the snout tip, and an eye
    out += outlined(blob(1722, 2448, 26, 17, 97, 0.1, 8, 30), '#3b2140', INK * 0.8)
    out += eye(1650, 2372, 28, 19, 22, YEL, (0.3, 0.1))
    out += '</g>'
    over = crescent(1775, 2470, 100, -60, 15, 22, PINK) + crescent(1775, 2470, 175, -55, 12, 26, CYAN)
    return draw(out, over)


VERSIONS = [
    ('1-crystals', 'Crystals', v1_crystals),
    ('2-singing-face', 'Singing cliff face', v2_face),
    ('3-organ-pipes', 'Organ pipes', v3_pipes),
    ('4-tuning-fork', 'Tuning fork', v4_fork),
    ('5-mountain-goat', 'Mountain goat', v5_goat),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (440 Hz)', m.compose())]
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


# ---- chosen: crystals ----------------------------------------------------------------------------------------------
# Picked under 5a: the cliff itself changes in its own nature (it grows crystals), a literal reading of tuned sharper
# and brighter (and quartz is what keeps tuning), and a celebratory candy display. Presets sit at 440 Hz (frame 0), so
# it shows only when tuned sharp. Master tuning from 0 to 1 breaks three clusters out of the cliff one point after
# another, each out of a collar of broken rock that cracks out first: the face (0-0.35), the slope down to the stream
# (0.3-0.65), the right edge over the bank (0.6-0.9); glints pop on the tips last (0.88-1). Each point is a chunky
# hand-drawn prism (body, a shaded right face, a lit middle face and a highlight) that pushes out from its foot.
#
#     uv run scripts/cliff_endframes.py crystals   # progression strip and end frame
#     uv run scripts/cliff_endframes.py export     # docs/objects/tg-master/build.json
CANDY = {  # base, lit, shade
    'pink': ('#FF89FC', '#FFCFFD', '#E25ED9'),
    'cyan': ('#7FFFF6', '#D6FFFC', '#3CD3CA'),
    'yellow': ('#FFE47F', '#FFF6CC', '#F2BC3A'),
    'lav': ('#C4A3F0', '#E9DDFB', '#9A74D8'),
    'mint': ('#89FF8C', '#D4FFD5', '#4FD255'),
}
COLLAR, COLLAR_L = '#a89c84', '#d2c8b2'
EDGE, THIN = 16, 10
# cluster: foot, collar (rx, ry, tilt), window, points (angle, length, width, colour); later points draw on top
CRYSTAL_CLUSTERS = [
    ((1265, 2590), (190, 74, -4), (0.0, 0.35), [(-140, 330, 150, 'lav'), (-48, 320, 150, 'yellow'), (-102, 470, 190, 'pink')]),
    ((1655, 2940), (150, 64, -18), (0.3, 0.65), [(-8, 270, 135, 'yellow'), (-42, 310, 145, 'lav'), (-84, 400, 170, 'cyan')]),
    ((1500, 2490), (100, 62, -30), (0.6, 0.9), [(-2, 260, 130, 'pink'), (-42, 330, 150, 'mint')]),
]
GLINT = '#fffbe0'


def it(d, fill, edge, at, s, e) -> dict:
    return {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
            'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': 'scale'}


def wobbly(pts, seed, amp, closed_=True) -> str:
    """A hand-drawn polygon: each edge subdivided, nudged a little sideways and drawn as a smooth curve, so the
    corners stay corners but the sides are lumpy, like the painting's outlines."""
    rnd = random.Random(seed)
    d = ''
    ring = pts + ([pts[0]] if closed_ else [])
    for i in range(len(ring) - 1):
        (x0, y0), (x1, y1) = ring[i], ring[i + 1]
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        k = max(2, int(L // 90))
        seg = [(x0, y0)]
        for j in range(1, k):
            u = j / k
            o = (rnd.random() - 0.5) * 2 * amp
            seg.append((x0 + (x1 - x0) * u + nx * o, y0 + (y1 - y0) * u + ny * o))
        seg.append((x1, y1))
        c = opened(seg)
        d += c if i == 0 else 'L' + c[1:].split('C', 1)[0] + ('C' + c[1:].split('C', 1)[1] if 'C' in c else '')
    return d + ('Z' if closed_ else '')


def crystal_items(bx, by, ang, L, W, colour, seed, s, e) -> tuple[list[dict], tuple[float, float]]:
    """One chunky candy crystal pushing out of the rock at (bx, by) over [s, e]; returns its items and its tip."""
    rnd = random.Random(seed)
    base, lit, shade = CANDY[colour]
    a = math.radians(ang)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    P = lambda q: (bx + ux * q[0] + vx * q[1], by + uy * q[0] + vy * q[1])
    shl, shr = L * (0.62 + rnd.random() * 0.06), L * (0.68 + rnd.random() * 0.06)
    tip = (L, W * (rnd.random() - 0.5) * 0.2)
    m1, m2 = -W * 0.12, W * 0.24  # the middle face between these
    foot = -60
    body = [(foot, -W / 2), (shl, -W * 0.5), tip, (shr, W * 0.5), (foot, W / 2)]
    right = [(foot, m2), (shr * 0.97 + (shl - shr) * 0.3, m2), tip, (shr, W * 0.5), (foot, W / 2)]
    mid = [(foot, m1), (shl * 1.02, m1), tip, (shr * 0.97 + (shl - shr) * 0.3, m2), (foot, m2)]
    shine = [(L * 0.12, m1 + W * 0.07), (L * 0.55, m1 + W * 0.06), (L * 0.55, m1 + W * 0.13), (L * 0.12, m1 + W * 0.16)]
    amp = W * 0.045
    items = [it(wobbly([P(q) for q in body], seed, amp), base, EDGE, (bx, by), s, e),
             it(wobbly([P(q) for q in right], seed + 1, amp * 0.7), shade, THIN, (bx, by), s, e),
             it(wobbly([P(q) for q in mid], seed + 2, amp * 0.7), lit, THIN, (bx, by), s, e),
             it(closed([P(q) for q in shine]), '#ffffff', 0, (bx, by), s + (e - s) * 0.3, e)]
    return items, P(tip)


def glint(x, y, r, rot) -> str:
    """A four-pointed candy glint with soft concave sides, outlined."""
    pts = []
    for k in range(8):
        a = math.radians(rot + k * 45)
        rr = r if k % 2 == 0 else r * 0.3
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    return closed(pts)


def crystal_items_all() -> list[dict]:
    items, tips = [], []
    for c, ((bx, by), (rx, ry, tilt), (s0, s1), pts) in enumerate(CRYSTAL_CLUSTERS):
        span = s1 - s0
        # the collar cracks out first; each point then pushes out of it in turn, overlapping a little
        n = len(pts)
        dur = span * 0.42
        for k, (ang, L, W, col) in enumerate(pts):
            s = s0 + span * 0.12 + (span * 0.88 - dur) * k / max(1, n - 1)
            its, tip = crystal_items(bx, by, ang, L, W, col, c * 10 + k + 1, s, s + dur)
            items += its
            tips.append((tip, L))
        collar = [it(blob(bx, by + 20, rx, ry, c + 40, 0.15, 11, tilt), COLLAR, EDGE, (bx, by + 20), s0, s0 + span * 0.2),
                  it(blob(bx - rx * 0.42, by + 12, rx * 0.36, ry * 0.5, c + 50, 0.16, 9, tilt), COLLAR_L, THIN, (bx - rx * 0.42, by + 12),
                     s0 + span * 0.06, s0 + span * 0.26),
                  it(blob(bx + rx * 0.5, by + 26, rx * 0.26, ry * 0.42, c + 60, 0.16, 9, tilt), COLLAR_L, THIN, (bx + rx * 0.5, by + 26),
                     s0 + span * 0.1, s0 + span * 0.3)]
        items += collar
    # glints on the tallest tips, last
    order = sorted(tips, key=lambda q: -q[1])[:5]
    for k, ((x, y), L) in enumerate(order):
        s = 0.88 + 0.025 * k
        items.append(it(glint(x, y, 58 + L * 0.06, 8 + k * 11), GLINT, THIN, (x, y), s, s + 0.06))
    return items


def front_mask_app() -> Image.Image:
    """The app's `around` mask: the front fills plus a band as wide as the ink round them."""
    body = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in FRONT_IDS)
    return m.svg(body).getchannel('A')


def crystal_frame(t: float) -> Image.Image:
    im = m.compose()
    if t <= 0:
        return im
    lay = m.svg(g.sprite_svg(crystal_items_all(), t))
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), ImageChops.invert(front_mask_app())))
    im.alpha_composite(lay)
    return im


def strip(frames, tiles, path, sc=0.42) -> None:
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    out = Image.new('RGB', (tw * len(tiles) + 10 * (len(tiles) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {t:.2f}  ({440 + 10 * t:.1f} Hz)', fill='black', font=font)
        out.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    out.save(path)


def crystals_main() -> None:
    out = OUT.parent / 'crystals'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [crystal_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    strip(frames, tiles, out / 'strip.png')
    fine = [0.08, 0.18, 0.32, 0.45, 0.62, 0.8, 0.93]
    strip(fine, [crystal_frame(t) for t in fine], out / 'strip-fine.png', 0.32)
    print('wrote', out)


LABEL = ("The grey cliff: shows Master Tuning (set by a preset or MIDI); tuned sharp above 440 Hz, big candy crystals "
         "break out of its face and slope cluster by cluster, and glint")


def export() -> None:
    import json
    build = {'label': LABEL,
             'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['none'], 'front': FRONT_IDS,
                          'items': crystal_items_all()}],
             'objectParts': {'none': []}}
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']), 'sprites to', path)


if __name__ == '__main__' and 'crystals' in __import__('sys').argv[1:]:
    crystals_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
