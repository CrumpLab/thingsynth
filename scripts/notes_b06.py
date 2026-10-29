# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b06: notes 57, 60, 62, 75, 78, 80.

    uv run scripts/notes_b06.py           # strips and end frames
    uv run scripts/notes_b06.py 62        # just note-62
    uv run scripts/notes_b06.py export    # docs/objects/note-<n>/build.json
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks)
ks.loader.exec_module(k)
p, tube, bez = k.p, k.tube, k.bez


# ---- drawing helpers -----------------------------------------------------------------------------------------------

def smooth_closed(P) -> str:
    """A closed Catmull-Rom curve through the points, as cubic beziers."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(cx, cy, rx, ry, rot=0.0, seed=0, wob=0.07, n=12) -> str:
    """A lumpy hand-drawn oval, turned `rot` degrees (clockwise on screen)."""
    rnd = random.Random(seed)
    a0 = math.radians(rot)
    P = []
    for i in range(n):
        t = i / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        x, y = math.cos(t) * rx * f, math.sin(t) * ry * f
        P.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return smooth_closed(P)


def ring(cx, cy, ro, ri, seed=0, wob=0.04) -> str:
    """A lumpy ring: an outer lumpy circle and a reversed inner one (a hole)."""
    rnd = random.Random(seed)
    n = 14

    def pts(r, rev):
        P = []
        for i in range(n):
            t = i / n * 2 * math.pi * (-1 if rev else 1)
            f = 1 + (rnd.random() - 0.5) * 2 * wob
            P.append((cx + math.cos(t) * r * f, cy + math.sin(t) * r * f))
        return P
    return smooth_closed(pts(ro, False)) + smooth_closed(pts(ri, True))


def burst(cx, cy, r, points=9, depth=0.22, seed=0) -> str:
    """A lumpy glow burst: a round shape with soft rounded rays."""
    rnd = random.Random(seed)
    P = []
    for i in range(points * 2):
        t = i / (points * 2) * 2 * math.pi
        rr = r * (1.0 if i % 2 == 0 else 1 - depth) * (1 + (rnd.random() - 0.5) * 0.1)
        P.append((cx + math.cos(t) * rr, cy + math.sin(t) * rr))
    return smooth_closed(P)


def petal(base, ang, L, W, seed=0, wob=0.06) -> str:
    """A lumpy petal or lip from `base` pointing `ang` degrees (screen, y down), length L, widest W near its end."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    side = []
    for u in (0.0, 0.25, 0.5, 0.72, 0.88):
        w = W * (0.38 + 0.62 * math.sin(math.pi * 0.5 * min(1.0, u / 0.75))) * 0.5
        side.append((u, w))
    P = []
    for u, w in side:
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        P.append((base[0] + ux * L * u + nx * w * f, base[1] + uy * L * u + ny * w * f))
    # a rounded, slightly notched end
    for t, r in ((0.55, 0.92), (0.0, 1.0), (-0.55, 0.92)):
        tt = t * math.pi / 2
        cx, cy = base[0] + ux * L * 0.88, base[1] + uy * L * 0.88
        P.append((cx + (ux * math.cos(tt) + nx * math.sin(tt)) * W * 0.5 * r * 0.55 + ux * L * 0.06,
                  cy + (uy * math.cos(tt) + ny * math.sin(tt)) * W * 0.5 * r * 0.55 + uy * L * 0.06))
    for u, w in reversed(side):
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        P.append((base[0] + ux * L * u - nx * w * f, base[1] + uy * L * u - ny * w * f))
    return smooth_closed(P)


def flame(bx, by, h, w, lean=0.0, seed=0) -> str:
    """A teardrop flame standing on (bx, by), its tip leaning `lean` px sideways."""
    rnd = random.Random(seed)
    j = lambda v: v * (1 + (rnd.random() - 0.5) * 0.12)
    P = [(bx, by + j(w * 0.18)), (bx + j(w * 0.5), by - h * 0.22), (bx + lean * 0.4 + j(w * 0.36), by - h * 0.55),
         (bx + lean * 0.75 + w * 0.12, by - h * 0.82), (bx + lean, by - h), (bx + lean * 0.75 - w * 0.1, by - h * 0.8),
         (bx + lean * 0.3 - j(w * 0.38), by - h * 0.5), (bx - j(w * 0.5), by - h * 0.2)]
    return smooth_closed(P)


def spark(cx, cy, r) -> str:
    k2 = r * 0.22
    P = [(cx, cy - r), (cx + k2, cy - k2), (cx + r, cy), (cx + k2, cy + k2), (cx, cy + r), (cx - k2, cy + k2), (cx - r, cy),
         (cx - k2, cy - k2)]
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


def crescent(cx, cy, r, a0, a1, w) -> str:
    """An outlined band along an arc, pointed at both ends (angles in degrees, y up)."""
    n = 16
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        t = math.sin(u * math.pi) * w / 2
        outer.append((cx + math.cos(a) * (r + t), cy - math.sin(a) * (r + t)))
        inner.append((cx + math.cos(a) * (r - t), cy - math.sin(a) * (r - t)))
    return 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'


def wedge(cx, cy, r, a0, a1) -> str:
    """A pie slice of a circle (angles in degrees, y up)."""
    n = 10
    P = [(cx, cy)] + [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r,
                       cy - math.sin(math.radians(a0 + (a1 - a0) * i / n)) * r) for i in range(n + 1)]
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


def S(d, fill, edge, at, start, end, grow='scale', **kw) -> dict:
    it = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 3),
          'end': round(end, 3), 'grow': grow}
    it.update(kw)
    return it


# ---- note-57 A3: the pink petal becomes a seal balancing a beach ball ----------------------------------------------

def fat_tube(P, wfun, seed=0, wob=0.04) -> str:
    """A lumpy limb or body along the centreline P, half-width wfun(u) at u in 0..1, rounded at the far end."""
    rnd = random.Random(seed)
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = wfun(i / (n - 1))
        f1, f2 = 1 + (rnd.random() - 0.5) * 2 * wob, 1 + (rnd.random() - 0.5) * 2 * wob
        L.append((x + nx * w * f1, y + ny * w * f1))
        R.append((x - nx * w * f2, y - ny * w * f2))
    ex, ey = P[-1]
    dx, dy = ex - P[-2][0], ey - P[-2][1]
    d = math.hypot(dx, dy) or 1
    w = wfun(1.0)
    cap = [(ex + dx / d * w * 0.9, ey + dy / d * w * 0.9)]
    return smooth_closed(L + cap + R[::-1])


def seal() -> list[dict]:
    INK = 13
    PINK, BELLY, DARK = '#E475A3', '#F7B9D2', '#3B1F35'
    base = (3735.0, 1885.0)
    spine = bez(base, (3760, 1770), (3850, 1690), (3852, 1570), 10)
    neck = spine[-1]
    head = (3874.0, 1512.0)
    bw = lambda dr: (lambda u: 66 - 20 * u + 14 * math.sin(math.pi * u) - dr)
    body = lambda dr: fat_tube(spine, bw(dr), seed=2)
    hd = lambda dr: blob(head[0], head[1], 66 - dr, 56 - dr, rot=-32, seed=3, wob=0.05)
    nose_at = (3956.0, 1452.0)
    R = 56
    ball = (nose_at[0] - 2, nose_at[1] - 12 - R)
    fl = lambda sh, ang, sd: petal(sh, ang, 92, 50, seed=sd)
    items = [
        S(body(0), PINK, INK, base, 0.0, 0.1),
        S(hd(0), PINK, INK, neck, 0.03, 0.14),
        # flippers: out and down at 2 s; at 4 s both swing up and clap
        S(fl((3858, 1652), 28, 21), PINK, INK, (3858, 1652), 0.3, 0.45, outStart=0.84, outEnd=0.9),
        S(fl((3872, 1652), -32, 22), PINK, INK, (3872, 1652), 0.84, 0.95),
        S(fl((3808, 1662), -146, 23), PINK, INK, (3808, 1662), 0.84, 0.95),
        S(body(INK / 2), PINK, 0, base, 0.0, 0.1),
        S(hd(INK / 2), PINK, 0, neck, 0.03, 0.14),
        S(blob(3828, 1700, 30, 100, rot=24, seed=5, wob=0.05), BELLY, 0, base, 0.06, 0.16),
        S(blob(3925, 1476, 44, 31, rot=-38, seed=7), BELLY, INK, head, 0.1, 0.2),
        S(blob(nose_at[0], nose_at[1], 17, 13, rot=-38, seed=9), DARK, INK * 0.7, (3930, 1475), 0.14, 0.22),
        S(blob(3866, 1496, 15, 17, seed=11, wob=0.04), DARK, INK * 0.6, (3866, 1496), 0.2, 0.3),
        S(k.circle(3871, 1490, 5.5), '#FFFFFF', 0, (3866, 1496), 0.24, 0.32),
        # the ball drops onto its nose, then its stripes sweep in
        S(blob(ball[0], ball[1], R, R, seed=13, wob=0.03, n=14), '#FFE15A', INK, (ball[0], ball[1] - 110), 0.45, 0.62),
        S(wedge(ball[0], ball[1], R - 2, 60, 120), '#3FD0E6', INK * 0.75, ball, 0.62, 0.72,
          sweep={'from': 60, 'to': 120}),
        S(wedge(ball[0], ball[1], R - 2, 180, 240), '#FF5FA8', INK * 0.75, ball, 0.68, 0.78,
          sweep={'from': 180, 'to': 240}),
        S(wedge(ball[0], ball[1], R - 2, 300, 360), '#9B6BFF', INK * 0.75, ball, 0.74, 0.84,
          sweep={'from': 300, 'to': 360}),
        S(k.circle(ball[0], ball[1], 14), '#FFFFFF', INK * 0.7, ball, 0.8, 0.86),
        S(crescent(ball[0], ball[1], R - 18, 120, 165, 10), '#FFFFFF', 0, ball, 0.88, 0.96),
        # clap: motion crescents round the raised flippers
        S(crescent(3842, 1645, 160, 8, 34, 20), '#FFFFFF', INK * 0.7, (3842, 1645), 0.92, 1.0),
        S(crescent(3842, 1645, 160, 150, 176, 20), '#FFFFFF', INK * 0.7, (3842, 1645), 0.92, 1.0),
    ]
    return items


# ---- note-60 C4: the magenta petal opens into a singing snapdragon -------------------------------------------------

def turned(P, o, deg):
    """Points turned `deg` degrees about o (clockwise on screen)."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(o[0] + (x - o[0]) * ca - (y - o[1]) * sa, o[1] + (x - o[0]) * sa + (y - o[1]) * ca) for x, y in P]


def snapdragon() -> tuple[list[dict], list[dict]]:
    INK = 13
    MAG, MOUTH, THROAT, TONGUE = '#E475D4', '#4A1240', '#FFE14D', '#FF9EC4'
    M = (3972.0, 1840.0)
    TURN = -22.0
    rel = lambda P, extra=0.0: turned([(M[0] + x * 1.25, M[1] + y * 1.25) for x, y in P], M, TURN + extra)
    UPPER = [(0, -4), (28, -58), (70, -112), (104, -88), (150, -104), (178, -52), (142, -8), (64, -2)]
    LOWER = [(0, 6), (70, 4), (150, 8), (188, 42), (160, 72), (128, 124), (90, 96), (46, 118), (12, 64)]
    up = lambda o: smooth_closed(rel(UPPER, -o))
    lo = lambda o: smooth_closed(rel(LOWER, o))
    pal = lambda o: smooth_closed(rel([(40, 10), (78, 8), (112, 18), (96, 40), (56, 40)], o))
    at = lambda x, y: rel([(x, y)])[0]
    tip = (3944.0, 1822.0)
    tube_d = fat_tube(bez((3740, 1975), (3820, 1915), (3910, 1866), M, 10), lambda u: 66 + 10 * u, seed=3)
    out = {'outStart': 0.45, 'outEnd': 0.52}
    crack = [
        # the tip parts: a dark crack opens in it, then the tube swells over it
        S(blob(tip[0] - 34, tip[1] + 18, 64, 17, rot=-34, seed=1), MOUTH, INK, (tip[0] - 60, tip[1] + 34), 0.0, 0.07,
          outStart=0.1, outEnd=0.16),
    ]
    items = [
        # the petal swells into the flower's tube, closed lips at its end
        S(tube_d, MAG, INK, (3760, 1960), 0.04, 0.16),
        S(blob(*at(84, 2), 92, 9, rot=TURN, seed=4), MOUTH, INK, M, 0.12, 0.26, **out),
        S(up(0), MAG, INK, M, 0.12, 0.28, **out),
        S(lo(0), MAG, INK, M, 0.18, 0.34, **out),
        S(pal(0), THROAT, INK * 0.8, M, 0.3, 0.4, **out),
        # it opens wide and sings
        S(blob(*at(84, 6), 96, 64, rot=TURN, seed=8), MOUTH, INK, M, 0.45, 0.58),
        S(blob(*at(70, 20), 54, 24, rot=TURN + 10, seed=9), TONGUE, INK * 0.8, M, 0.62, 0.74),
        S(up(30), MAG, INK, M, 0.45, 0.6),
        S(lo(30), MAG, INK, M, 0.47, 0.62),
        S(pal(30), THROAT, INK * 0.8, M, 0.6, 0.7),
        # song arcs
        S(crescent(*at(100, 6), 150, -42, 62, 28), '#FFFFFF', INK * 0.8, at(100, 6), 0.8, 0.9),
        S(crescent(*at(100, 6), 205, -34, 54, 28), THROAT, INK * 0.8, at(100, 6), 0.88, 1.0),
    ]
    return crack, items


# ---- note-62 D4: the ghost's mouth blows a bubblegum bubble --------------------------------------------------------

def bubblegum() -> list[dict]:
    INK = 13
    GUM, GUM2, PALE = '#FF8FCB', '#FF5FAE', '#BEDAF0'
    mo = (2772.0, 1556.0)
    bub = lambda r: (mo[0] - r + 4, mo[1] - r * 0.06)
    b3c, R3 = bub(122), 122
    items = [
        S(blob(mo[0] - 22, mo[1], 40, 33, seed=1), GUM, INK, mo, 0.0, 0.07),
        # the cheek puffs out
        S(blob(2758, 1468, 40, 52, seed=2, wob=0.05), PALE, INK, (2780, 1468), 0.1, 0.22),
        S(blob(2786, 1468, 34, 50, seed=2, wob=0.03), PALE, 0, (2780, 1468), 0.1, 0.22),
        # bubbles, each bigger, nested at the mouth
        S(blob(*bub(70), 70, 68, seed=3, wob=0.03, n=14), GUM, INK, mo, 0.15, 0.3),
        S(blob(*bub(98), 98, 95, seed=4, wob=0.03, n=14), GUM, INK, mo, 0.34, 0.5),
        S(blob(*b3c, R3, R3 * 0.97, seed=5, wob=0.025, n=16), GUM, INK, mo, 0.56, 0.85),
        # gloss
        S(crescent(b3c[0], b3c[1], R3 * 0.78, 100, 172, 22), '#FFFFFF', INK * 0.6, b3c, 0.86, 0.96),
        S(crescent(b3c[0], b3c[1], R3 * 0.78, 282, 318, 16), '#FFD3EA', 0, b3c, 0.9, 1.0),
        # the lip of gum at the mouth stays on top
        S(blob(mo[0] - 10, mo[1], 26, 24, seed=7), GUM2, INK, mo, 0.0, 0.07),
    ]
    return items


# ---- note-75 D#5: the pale blue pill lights up into a firefly ------------------------------------------------------

def firefly() -> tuple[list[dict], list[dict], list[dict]]:
    INK = 11
    YEL, CORE, NAVY, ELY, HIND, GLOW = '#FFE84A', '#FFFBD0', '#2E3A5C', '#C9B6FF', '#C4F4FF', '#FFF59A'
    lc = (2752.0, 1830.0)
    on = [
        S(blob(lc[0], lc[1] + 4, 74, 76, seed=1, wob=0.05), YEL, INK, (2752, 1866), 0.0, 0.07),
        S(blob(lc[0] + 2, lc[1] + 22, 34, 30, seed=2, wob=0.05), CORE, 0, (2752, 1866), 0.86, 0.98),
    ]
    under = [
        S(burst(2700, 1792, 140, 16, 0.12, seed=4), '#FFF8C4', 9, (2730, 1800), 0.8, 0.94),
        S(burst(2712, 1796, 104, 13, 0.13, seed=3), GLOW, 9, (2730, 1800), 0.48, 0.6),
    ]
    sh = (2712.0, 1712.0)
    over = [
        S(petal((2700, 1720), -172, 128, 62, seed=5), HIND, INK, (2700, 1720), 0.6, 0.74),
        S(petal((2726, 1716), -8, 120, 60, seed=6), HIND, INK, (2726, 1716), 0.64, 0.78),
        S(petal((2702, 1712), -142, 112, 58, seed=7), ELY, INK, (2702, 1712), 0.28, 0.42),
        S(petal((2722, 1708), -38, 108, 56, seed=8), ELY, INK, (2722, 1708), 0.34, 0.48),
        S(tube(bez((2692, 1655), (2675, 1630), (2655, 1618), (2640, 1612), 12), 6, 5), NAVY, INK * 0.6, (2692, 1655), 0.2, 0.32),
        S(tube(bez((2708, 1652), (2706, 1628), (2696, 1610), (2684, 1598), 12), 6, 5), NAVY, INK * 0.6, (2708, 1652), 0.22, 0.34),
        S(blob(2702, 1676, 38, 34, seed=9), NAVY, INK, (2706, 1696), 0.05, 0.18),
        S(k.circle(2688, 1660, 7), '#FFFFFF', 0, (2700, 1668), 0.88, 0.96),
    ]
    return on, under, over


# ---- note-78 F#5: the egg becomes a jewelled Faberge egg with a crown ---------------------------------------------

def faberge() -> list[dict]:
    INK = 11
    GOLD, CYAN, VIOLET, LIME, PINK = '#F5C542', '#3FD9E8', '#B86BFF', '#A8F04A', '#FF5FA8'
    rnd = random.Random(4)
    jt = lambda v: v + (rnd.random() - 0.5) * 6
    crown = [(4222, 1304), (jt(4210), jt(1224)), (4250, 1262), (jt(4283), jt(1194)), (4316, 1262), (jt(4356), jt(1224)),
             (4346, 1304)]
    crown_d = 'M' + 'L'.join(p(*q) for q in crown) + f'Q{p(4284, 1322)} {p(*crown[0])}Z'
    items = [
        S(tube(bez((4204, 1344), (4250, 1376), (4300, 1398), (4360, 1410), 16), 13, 13), GOLD, INK, (4282, 1384), 0.0, 0.07),
        S(blob(4282, 1334, 25, 22, seed=1), CYAN, INK, (4282, 1334), 0.12, 0.22),
        S(blob(4238, 1340, 17, 15, seed=2), VIOLET, INK, (4238, 1340), 0.2, 0.3),
        S(blob(4324, 1362, 17, 15, seed=3), LIME, INK, (4324, 1362), 0.28, 0.38),
        S(k.circle(4275, 1327, 6), '#FFFFFF', 0, (4282, 1334), 0.34, 0.4),
        S(ring(4254, 1440, 19, 9, seed=4), GOLD, INK * 0.8, (4254, 1440), 0.42, 0.5),
        S(ring(4290, 1456, 19, 9, seed=5), GOLD, INK * 0.8, (4290, 1456), 0.48, 0.56),
        S(ring(4324, 1462, 17, 8, seed=6), GOLD, INK * 0.8, (4324, 1462), 0.54, 0.62),
        S(crown_d, GOLD, INK, (4284, 1306), 0.62, 0.78),
        S(blob(4284, 1294, 58, 12, seed=7, wob=0.04), PINK, INK * 0.8, (4284, 1306), 0.7, 0.8),
        S(k.circle(crown[1][0], crown[1][1], 13), PINK, INK * 0.8, crown[1], 0.8, 0.88),
        S(k.circle(crown[5][0], crown[5][1], 13), CYAN, INK * 0.8, crown[5], 0.84, 0.92),
        S(k.circle(crown[3][0], crown[3][1] - 8, 19), '#FFF6EE', INK * 0.8, crown[3], 0.88, 0.96),
        S(k.circle(crown[3][0] - 6, crown[3][1] - 14, 5), '#FFFFFF', 0, crown[3], 0.92, 0.98),
        S(spark(crown[3][0] + 34, crown[3][1] - 34, 22), '#FFFFFF', INK * 0.7, (crown[3][0] + 34, crown[3][1] - 34), 0.94, 1.0),
    ]
    return items


# ---- note-80 G#5: the coral nub lights as a birthday candle --------------------------------------------------------

def candle() -> tuple[list[dict], list[dict]]:
    INK = 11
    YEL, ORANGE, WHITE, BLUE, WAX, STRIPE = '#FFE14D', '#FF8A2A', '#FFFBEA', '#6FB8FF', '#FFF3D6', '#FFF0F5'
    bx, by = 3590.0, 1664.0
    on = []
    for i, y0 in enumerate((1702, 1742, 1782)):
        band = f'M{p(3540, y0 + 34)}L{p(3660, y0 - 6)}L{p(3660, y0 + 16)}L{p(3540, y0 + 56)}Z'
        on.append(S(band, STRIPE, 9, (3540, y0 + 45), 0.1 + i * 0.08, 0.22 + i * 0.08, grow='x'))
    over = [
        S(flame(bx, by, 92, 50, lean=6, seed=1), YEL, INK, (bx, by), 0.0, 0.07, outStart=0.26, outEnd=0.36),
        S(flame(bx - 24, by - 6, 150, 62, lean=-84, seed=2), ORANGE, INK, (bx - 20, by), 0.72, 0.84),
        S(flame(bx, by, 232, 112, lean=16, seed=3), ORANGE, INK, (bx, by), 0.26, 0.46),
        S(flame(bx + 2, by - 4, 170, 74, lean=12, seed=4), YEL, INK * 0.8, (bx, by), 0.32, 0.5),
        S(flame(bx + 3, by - 8, 84, 34, lean=6, seed=5), WHITE, INK * 0.7, (bx, by), 0.5, 0.6),
        S(blob(bx, by + 2, 26, 13, seed=6), BLUE, INK * 0.7, (bx, by), 0.52, 0.62),
        S(tube(bez((3566, 1672), (3562, 1692), (3560, 1712), (3561, 1738), 12), 11, 13), WAX, INK * 0.8, (3566, 1668), 0.6, 0.72,
          grow='y'),
        S(spark(3522, 1500, 28), YEL, INK * 0.7, (3522, 1500), 0.86, 0.93),
        S(spark(3668, 1478, 26), '#FF7AC0', INK * 0.7, (3668, 1478), 0.9, 0.97),
        S(spark(3622, 1388, 32), '#7FE7FF', INK * 0.7, (3622, 1388), 0.93, 1.0),
    ]
    return on, over


ff_on, ff_under, ff_over = firefly()
cd_on, cd_over = candle()
sd_crack, sd_items = snapdragon()

DESIGNS = [
    {'note': 57, 'label': "The pink petal on the acorn frog's back: hold A3 to play; it rears up into a pink seal that "
                          'balances a beach ball on its nose and claps',
     'effects': [{'effect': 'vanish', 'span': [0, 0.08]},
                 {'effect': 'sprites', 'place': 'around', 'own': False, 'front': ['f209'], 'items': seal()}],
     'crop': (3430, 1260, 760, 760)},
    {'note': 60, 'label': "The magenta petal on the acorn frog's back: hold C4 to play; it opens into a snapdragon "
                          'that sings',
     'effects': [{'effect': 'vanish', 'span': [0.04, 0.14]},
                 {'effect': 'sprites', 'place': 'around', 'own': False, 'front': ['f209'], 'items': sd_items},
                 {'effect': 'sprites', 'place': 'over', 'items': sd_crack}],
     'crop': (3600, 1560, 800, 800)},
    {'note': 62, 'label': "The magenta mouth at the horned ghost's foot: hold D4 to play; it blows a bubblegum bubble, "
                          'bigger and bigger',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': bubblegum()}],
     'crop': (2440, 1240, 640, 640)},
    {'note': 75, 'label': 'The pale blue pill held up by the green cat-eared creature: hold D#5 to play; it lights up '
                          'into a firefly that opens its wings and glows',
     'effects': [{'effect': 'sprites', 'place': 'around', 'front': ['f204'], 'items': ff_under},
                 {'effect': 'sprites', 'place': 'on', 'items': ff_on},
                 {'effect': 'sprites', 'place': 'over', 'items': ff_over}],
     'crop': (2480, 1460, 560, 560)},
    {'note': 78, 'label': "The pink top of the egg in the straw creature's neck: hold F#5 to play; it turns into a "
                          'jewelled Faberge egg and a crown lands on top',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': faberge()}],
     'crop': (4060, 1110, 440, 440)},
    {'note': 80, 'label': "The coral nub on the acorn frog's back: hold G#5 to play; it lights up as a birthday candle, "
                          'its flame leaping and sparks popping',
     'effects': [{'effect': 'sprites', 'place': 'on', 'items': cd_on},
                 {'effect': 'sprites', 'place': 'over', 'items': cd_over}],
     'crop': (3290, 1290, 600, 600)},
]

if __name__ == '__main__':
    k.run(DESIGNS)
