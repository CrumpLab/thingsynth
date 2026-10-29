# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b08: notes 31, 61, 63, 68, 74, 102.

    uv run scripts/notes_b08.py            # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b08.py 61         # just note-61
    uv run scripts/notes_b08.py export     # docs/objects/note-<n>/build.json

note-31  G1  f162  the dark green hedge on the pool's far shore  -> hedge-hog
note-61  C#4 f133  the thin waterfall from the pink creature's snout  -> loop-the-loop
note-63  D#4 f085  the pink stub on the blue-capped cone  -> cupcake swirl with a candy topper
note-68  G#4 f080  the cyan ring with the purple plug  -> swim ring, a beach ball bounces on it
note-74  D5  f203  the dark maroon wedge under the bush  -> bat
note-102 F#7 f160  the tiny green tuft at the waterfall's spout  -> grasshopper
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
m, p, tube, bez, crescent = k.m, k.p, k.tube, k.bez, k.g.crescent
smooth = m.smooth

PINK, HOT, YEL, CYAN, LILAC, ORANGE, MINT, CREAM = ('#ff9fc4', '#FF5CED', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43',
                                                    '#a8f5c8', '#fff4d6')


# ---- helpers ---------------------------------------------------------------------------------------------------------

def r2(v):
    return [round(v[0], 1), round(v[1], 1)]


def it(d, fill, edge, at, start, end, grow='scale', out=None, sweep=None) -> dict:
    """One sprite item."""
    x = {'d': d, 'fill': fill, 'edge': edge, 'at': r2(at), 'start': round(start, 4), 'end': round(end, 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    if sweep:
        x['sweep'] = {'from': round(sweep[0], 1), 'to': round(sweep[1], 1)}
    return x


def layered(parts, fill, ink) -> list[dict]:
    """Seamless joins: every part as an outlined layer (double ink, so the fill-only layer above covers its inner
    half), then every part again fill-only on top. parts: (d, at, start, end, kwargs)."""
    outl = [it(d, fill, ink * 2, at, s, e, **kw) for d, at, s, e, kw in parts]
    fills = [it(d, fill, 0, at, s, e, **kw) for d, at, s, e, kw in parts]
    return outl + fills


def lump(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.06, n=12) -> str:
    """A lumpy hand-drawn oval, turned by rot degrees."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        f = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * f, math.sin(t) * ry * f
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def ltube(P, w0, w1, seed=0, wob=0.08) -> str:
    """A lumpy tapered outlined limb along the centreline P, round at both ends."""
    rnd = random.Random(seed)
    ph = rnd.random() * 6.28
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + wob * math.sin(u * 11 + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    # round caps: a point beyond each end
    (x0, y0), (x1, y1) = P[0], P[1]
    d0 = math.hypot(x1 - x0, y1 - y0) or 1
    cap0 = (x0 - (x1 - x0) / d0 * w0 * 0.9, y0 - (y1 - y0) / d0 * w0 * 0.9)
    (xa, ya), (xb, yb) = P[-2], P[-1]
    d1 = math.hypot(xb - xa, yb - ya) or 1
    cap1 = (xb + (xb - xa) / d1 * w1 * 0.9, yb + (yb - ya) / d1 * w1 * 0.9)
    pts = L[::2] + [L[-1], cap1, R[-1]] + R[::-1][1::2] + [R[0], cap0]
    return smooth(pts)


def rot(pts, c, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


def poly(pts) -> str:
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def eye(cx, cy, r, look=(0.2, 0.1), ink=11) -> list[dict]:
    """A round eye: white, pupil, glint (three items with the timing filled in by the caller)."""
    return [(lump(cx, cy, r, r * 1.05, 0, 7, 0.04), '#ffffff', ink),
            (lump(cx + look[0] * r, cy + look[1] * r, r * 0.55, r * 0.6, 0, 8, 0.05), '#1a1020', 0),
            (lump(cx + look[0] * r + r * 0.18, cy + look[1] * r - r * 0.22, r * 0.18, r * 0.18, 0, 9, 0.05), '#ffffff', 0)]


# ---- note-31: hedge-hog ----------------------------------------------------------------------------------------------
# The hedge f162 (x 2198-2625, top 2324-2400, foot on the shore line at y ~2470) heaves up into a hedgehog facing left
# (its right end is next to note-74's wedge): spines bristle on top at once, then three rows of fat lumpy spines fan up
# over its back, back row first, a cream snout pushes out of its left end with a pink nose, a bead eye and an ear, a
# blush, and two candy apples land speared on its back.

H_C = (2420.0, 2474.0)   # the dome's centre on the shore line
H_RX, H_RY = 205.0, 150.0


def spiky_dome(base, tip, a0, a1, n, seed, lean=0.07) -> str:
    """A dome on the shore line whose top edge is a row of fat, lumpy spines pointing out from H_C and leaning back
    (to the right, toward the tail). base/tip: radii (as fractions of the dome) of the spines' roots and tips."""
    rnd = random.Random(seed)
    cx, cy = H_C
    E = lambda a, r: (cx + H_RX * r * math.cos(a), cy - H_RY * r * math.sin(a))
    A0, A1 = math.radians(a0), math.radians(a1)
    d = ''
    pts_first = E(A1, base)
    d = f'M{p(cx + H_RX * base * math.cos(A1), cy)}L{p(*pts_first)}'
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        aa, ab = A1 + (A0 - A1) * u0, A1 + (A0 - A1) * u1
        am = (aa + ab) / 2 - lean
        t = tip * (1 + 0.1 * (rnd.random() * 2 - 1))
        q0, q1, tp = E(aa, base), E(ab, base), E(am, t)
        c0 = E(aa + 0.01, base + (t - base) * 0.55)
        c1 = E(ab - 0.03, base + (t - base) * 0.45)
        d += f'Q{p(*c0)} {p(*tp)}Q{p(*c1)} {p(*q1)}'
    last = E(A0, base)
    d += f'L{p(cx + H_RX * base * math.cos(A0), cy)}Z'
    return d


def hedgehog() -> dict:
    INK = 14
    items = []
    # 0-0.04: a first tuft of spines bristles up out of the hedge's top
    first = spiky_dome(0.7, 0.98, 0, 175, 7, 3, 0.04)
    items.append(it(first, '#4f8a3a', INK, (2420, 2474), 0.0, 0.04, 'y'))
    # the rows: back (tallest, darkest) to front (lightest), each a dome down to the shore so it covers the hedge
    rows = [(0.9, 1.55, 0, 160, 7, '#2f6a27', 0.06, 0.32),
            (0.82, 1.34, 0, 166, 7, '#47852f', 0.26, 0.52),
            (0.72, 1.1, 0, 170, 8, '#69a842', 0.48, 0.72)]
    for k_, (b, t, a0, a1, n, col, s, e) in enumerate(rows):
        items.append(it(spiky_dome(b, t, a0, a1, n, 20 + k_), col, INK, (H_C[0], H_C[1] - 2), s, e, 'y'))
    # the face: a cream snout cone out of the left end, an ear, a pink nose, a bead eye with a glint, a blush
    snout = smooth([(2305, 2332), (2262, 2338), (2228, 2362), (2196, 2378), (2160, 2408), (2120, 2432), (2110, 2452),
                    (2140, 2466), (2200, 2462), (2252, 2474), (2318, 2470), (2350, 2430), (2338, 2370)])
    ear = lump(2292, 2338, 30, 26, -20, 4, 0.08)
    items.append(it(ear, '#d9a877', INK, (2300, 2360), 0.36, 0.46))
    items.append(it(snout, '#ecc996', INK, (2330, 2440), 0.28, 0.46, 'x'))
    items.append(it(lump(2290, 2340, 15, 12, -20, 5), '#ff9fc4', 0, (2292, 2340), 0.42, 0.48))
    items.append(it(lump(2114, 2440, 26, 22, 10, 6, 0.08), HOT, INK, (2125, 2445), 0.44, 0.54))
    items.append(it(lump(2215, 2400, 17, 19, 0, 7, 0.05), '#1a1020', 0, (2215, 2400), 0.52, 0.58))
    items.append(it(lump(2209, 2393, 6, 6, 0, 8), '#ffffff', 0, (2209, 2393), 0.56, 0.6))
    items.append(it(lump(2235, 2442, 28, 15, -10, 9, 0.08), '#ff8fb0', 0, (2235, 2442), 0.62, 0.72))
    # 4 s: two candy apples land speared on its back, each with a stalk and a leaf
    for j, (cx, cy, r, col, s, e) in enumerate(((2385, 2262, 48, '#f64c76', 0.78, 0.9), (2525, 2300, 42, YEL, 0.88, 1.0))):
        apple = smooth([(cx, cy - r * 0.72), (cx + r * 0.55, cy - r * 0.95), (cx + r, cy - r * 0.2), (cx + r * 0.7, cy + r * 0.75),
                        (cx, cy + r * 0.95), (cx - r * 0.7, cy + r * 0.75), (cx - r, cy - r * 0.2), (cx - r * 0.55, cy - r * 0.95)])
        stalk = ltube([(cx, cy - r * 0.6), (cx + 4, cy - r * 1.0), (cx + 10, cy - r * 1.3)], 6, 5, j)
        leaf = lump(cx + r * 0.45, cy - r * 1.15, r * 0.38, r * 0.18, -30, j + 3, 0.05)
        items.append(it(stalk, '#8a5a2b', 10, (cx, cy), s, e))
        items.append(it(leaf, '#7fd36b', 10, (cx, cy), s, e))
        items.append(it(apple, col, INK, (cx, cy), s, e))
        items.append(it(lump(cx - r * 0.38, cy - r * 0.3, r * 0.2, r * 0.13, -30, j + 5), '#ffffff', 0, (cx, cy), s + 0.04, e))
    return {
        'note': 31,
        'label': "The dark green hedge on the pool's far shore: hold G1 to play; it bristles up into a hedgehog, rows of "
                 "spines fanning over its back, its snout and pink nose poking out, and two candy apples land on its spines",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (2000, 2000, 800, 800),
    }


# ---- note-61: loop-the-loop ------------------------------------------------------------------------------------------
# The thin waterfall f133 arcs from the pink creature's snout (1632, 2172) over and down into the pool (1912, 2600).
# A fatter sprite stream covers it at once and its foot kicks up out of the pool; then the falling water winds into a
# fat wobbly loop, a second, and a third up on the arch (each a cursive loop off the stream's line, wiped in round its
# middle), and a candy splash crown bursts where it lands.

W_LINE = [(1628, 2172), (1690, 2170), (1758, 2188), (1810, 2236), (1850, 2298), (1878, 2365), (1896, 2440),
          (1906, 2512), (1911, 2600)]
WATER = '#b6f6ee'


def polyline_at(P, s):
    """The point and unit direction at arc length s along P."""
    for a, b in zip(P, P[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if s <= L:
            u = s / L
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        s -= L
    a, b = P[-2], P[-1]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def loop_line(s0, s1, R, side, seed, n=40):
    """A cursive loop off the stream between arc lengths s0 and s1: a prolate trochoid along the stream's line,
    bulging to one side, its radius wobbling. Returns the centreline and the loop's middle."""
    rnd = random.Random(seed)
    ph = rnd.random() * 6.28
    A, dA = polyline_at(W_LINE, s0)
    B, _ = polyline_at(W_LINE, s1)
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    tx, ty = (B[0] - A[0]) / L, (B[1] - A[1]) / L
    nx, ny = -ty * side, tx * side
    P = []
    for i in range(n + 1):
        u = i / n
        r = R * (1 + 0.08 * math.sin(3 * 2 * math.pi * u + ph))
        a = L * u - 1.15 * r * math.sin(2 * math.pi * u)
        b = r * (1 - math.cos(2 * math.pi * u))
        P.append((A[0] + tx * a + nx * b, A[1] + ty * a + ny * b))
    mid = (A[0] + tx * L / 2 + nx * R, A[1] + ty * L / 2 + ny * R)
    return P, mid, math.degrees(math.atan2(-(A[1] - mid[1]), A[0] - mid[0]))


def resample(P, n):
    """n+1 points evenly along the polyline P."""
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(P, P[1:]))
    return [polyline_at(P, tot * i / n)[0] for i in range(n + 1)]


def waterfall() -> dict:
    INK = 13
    W = 22
    parts = []
    # 0-0.03: the stream itself, a little fatter, laid over the painted one
    parts.append((ltube(resample(W_LINE, 40), W + 1, W + 2, 1, 0.06), (1760, 2190), 0.0, 0.03, {}))
    # 0-0.04: its foot kicks up out of the pool in a curl
    kick = ltube(bez((1911, 2596), (1925, 2640), (1985, 2630), (1995, 2560), 16), 20, 18, 2, 0.08)
    parts.append((kick + lump(1997, 2548, 22, 26, 0, 3), (1911, 2600), 0.0, 0.045, {}))
    # three loops, each wiped in round its middle: up on the arch's bend, down the fall on the right, lower on the left.
    # The back half of each loop joins the stream seamlessly; its front half crosses over on top with its own outline.
    loops = [(70, 122, 60, -1, 0.07, 0.3), (292, 338, 54, -1, 0.32, 0.55), (430, 472, 50, 1, 0.57, 0.8)]
    fronts, patches = [], []
    for j, (s0, s1, R, side, s, e) in enumerate(loops):
        P, mid, a_start = loop_line(s0, s1, R, side, 10 + j, 48)
        sw = {'sweep': (a_start, a_start + 380 * (1 if side < 0 else -1))}
        parts.append((ltube(P[:31], W, W, 20 + j, 0.07), mid, s, e, sw))
        fronts.append(it(ltube(P[22:], W, W, 30 + j, 0.07), WATER, INK, mid, s, e, **sw))
        patches.append(it(ltube(P[18:30], W - 0.5, W - 0.5, 0, 0.0), WATER, 0, mid, s, e, **sw))
        B, _ = polyline_at(W_LINE, s1)
        seg = [polyline_at(W_LINE, s1 + d_)[0] for d_ in range(-4, 40, 4)]
        patches.append(it(ltube(seg, W, W, 0, 0.0), WATER, 0, B, e - 0.04, e))
    # 4 s: a splash crown where it lands: round-tipped lobes fanning up out of a lumpy pool of foam
    lobes = [(-110, 58, -52), (-60, 80, -24), (0, 88, 4), (58, 76, 26), (110, 56, 54)]
    crown = ''
    for j, (dx, h, tilt) in enumerate(lobes):
        bx, by = 1912 + dx * 0.6, 2626
        tip = (bx + math.sin(math.radians(tilt)) * h, by - math.cos(math.radians(tilt)) * h)
        mid_ = (bx + math.sin(math.radians(tilt)) * h * 0.5, by - math.cos(math.radians(tilt)) * h * 0.55)
        crown += ltube(bez((bx, by), mid_, mid_, tip, 10), 24, 18, 50 + j, 0.05)
    splash = [(crown, (1912, 2626), 0.82, 0.96, {'grow': 'y'}),
              (lump(1912, 2624, 125, 36, 0, 5, 0.08), (1912, 2624), 0.8, 0.9, {})]
    # the shine along the arch (with the stream), then the splash's shine and candy drops flying off it
    sh = [(x, y - 11) for x, y in resample(W_LINE[:4], 12)]
    shine = [it(ltube(sh, 4, 3, 40, 0.1), '#ffffff', 0, (1700, 2175), 0.0, 0.03)]
    items = layered(parts, WATER, INK) + shine + fronts + patches + layered(splash, WATER, INK)
    items.append(it(lump(1900, 2618, 60, 12, 0, 6), '#ffffff', 0, (1912, 2622), 0.86, 0.95))
    for j, (pair, col) in enumerate(((((1762, 2555, 26), (2040, 2510, 24)), HOT), (((2000, 2440, 22), (1800, 2620, 20)), YEL))):
        d = ''
        for x, y, r in pair:
            d += smooth([(x, y - r * 1.5), (x + r * 0.8, y - r * 0.1), (x + r * 0.6, y + r * 0.7), (x, y + r),
                         (x - r * 0.6, y + r * 0.7), (x - r * 0.8, y - r * 0.1)])
        items.append(it(d, col, 10, (1912, 2560), 0.86 + 0.05 * j, 0.96 + 0.04 * j))
    return {
        'note': 61,
        'label': "The thin waterfall from the pink creature's snout: hold C#4 to play; its foot kicks up out of the pool, "
                 "then the falling water winds into one, two, three fat wobbly loops and lands in a splash crown that flings candy drops",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (1450, 1950, 750, 750),
    }


# ---- note-63: cupcake ------------------------------------------------------------------------------------------------
# The pink stub f085 stands in the blue cap (the frosting, f084) on the peach cone (the cupcake case, f083). A pink
# dollop puffs at its foot at once; then the stub is swirled over with frosting, tier on tier, candy sprinkles pop on
# the blue, and at 4 s a tall twisted swirl peak tops it with a striped wrapped candy.

def tier(cx, cy, w, h, seed, tilt=0.0):
    """One lumpy roll of a frosting swirl, tilted, and the crease that makes it read as a swirl winding round."""
    rnd = random.Random(seed)
    j = lambda: rnd.uniform(-0.05, 0.05)
    pts = [(cx - w, cy + h * 0.2), (cx - w * (0.88 + j()), cy - h * 0.55), (cx - w * 0.4, cy - h * (0.98 + j())),
           (cx + w * 0.2, cy - h * (0.9 + j())), (cx + w * (0.8 + j()), cy - h * 0.6), (cx + w * 1.03, cy + h * 0.1),
           (cx + w * 0.75, cy + h * (0.8 + j())), (cx + w * 0.1, cy + h), (cx - w * (0.6 + j()), cy + h * 0.85)]
    body = smooth(rot(pts, (cx, cy), tilt))
    crease = [(cx - w * 0.85, cy - h * 0.05), (cx - w * 0.2, cy + h * 0.25), (cx + w * 0.55, cy + h * 0.15),
              (cx + w * 0.92, cy - h * 0.15), (cx + w * 0.7, cy + h * 0.35), (cx - w * 0.15, cy + h * 0.55),
              (cx - w * 0.7, cy + h * 0.25)]
    return body, smooth(rot(crease, (cx, cy), tilt))


def cupcake() -> dict:
    INK = 13
    items = []
    # 0-0.04: a pink dollop puffs up round the stub's foot
    items.append(it(lump(2738, 2852, 70, 34, -4, 1, 0.08), PINK, INK, (2738, 2870), 0.0, 0.04))
    # sprinkles on the blue frosting, three pops
    spr = [(2655, 2880, 30, YEL), (2700, 2925, -40, CYAN), (2790, 2940, 15, '#ffffff'), (2830, 2905, 70, HOT),
           (2675, 2905, 80, ORANGE), (2760, 2950, -20, LILAC), (2820, 2955, 40, YEL), (2645, 2858, -60, '#7fd36b'),
           (2730, 2938, 50, HOT)]
    for g in range(3):
        for x, y, a, col in spr[g::3]:
            d = ltube(rot([(x - 19, y), (x + 19, y)], (x, y), a), 8, 8, 0, 0.0)
            items.append(it(d, col, 8, (x, y), 0.22 + 0.1 * g, 0.3 + 0.1 * g))
    # the swirl: three rolls up the stub, each smaller, alternating its own pink and a paler pink
    tiers = [(2740, 2850, 114, 44, '#ffb3d6', 0.05, 0.3, -4), (2748, 2790, 90, 40, '#F681D9', 0.4, 0.58, 5),
             (2732, 2735, 68, 36, '#ffb3d6', 0.6, 0.76, -6)]
    for j, (cx, cy, w, h, col, s, e, tl) in enumerate(tiers):
        body, crease = tier(cx, cy, w, h, j, tl)
        items.append(it(body, col, INK, (cx, cy + h), s, e))
        items.append(it(crease, '#e05aae' if col != '#F681D9' else '#c9479a', 0, (cx, cy + h), s + 0.04, e))
    # 4 s: a tall twisted peak (bigger than the stub ever was) with a striped wrapped candy on its tip
    peak = smooth([(2682, 2708), (2688, 2668), (2704, 2636), (2718, 2610), (2740, 2590), (2772, 2582), (2798, 2596),
                   (2788, 2612), (2766, 2612), (2760, 2636), (2778, 2668), (2794, 2706), (2740, 2722)])
    items.append(it(peak, '#ffb3d6', INK, (2738, 2715), 0.76, 0.9, 'y'))
    items.append(it(smooth([(2702, 2690), (2740, 2668), (2775, 2655), (2770, 2668), (2735, 2684), (2706, 2700)]),
                    '#e05aae', 0, (2738, 2715), 0.8, 0.9, 'y'))
    items.append(it(smooth([(2718, 2652), (2748, 2634), (2762, 2630), (2756, 2642), (2730, 2655)]), '#e05aae', 0,
                    (2738, 2715), 0.82, 0.9, 'y'))
    c = (2782, 2556)
    wrap_l = smooth(rot([(c[0] - 34, c[1]), (c[0] - 70, c[1] - 30), (c[0] - 92, c[1] - 40), (c[0] - 84, c[1]),
                         (c[0] - 94, c[1] + 38), (c[0] - 70, c[1] + 28)], c, -12))
    wrap_r = smooth(rot([(c[0] + 34, c[1]), (c[0] + 70, c[1] - 30), (c[0] + 92, c[1] - 40), (c[0] + 84, c[1]),
                         (c[0] + 94, c[1] + 38), (c[0] + 70, c[1] + 28)], c, -12))
    items.append(it(wrap_l, YEL, 10, c, 0.9, 1.0))
    items.append(it(wrap_r, YEL, 10, c, 0.9, 1.0))
    items.append(it(lump(c[0], c[1], 44, 33, -12, 3, 0.05), HOT, INK, c, 0.88, 0.98))
    stripes = ''
    for dx in (-22, 0, 22):
        stripes += poly(rot([(c[0] + dx - 5, c[1] - 30), (c[0] + dx + 6, c[1] - 30), (c[0] + dx + 3, c[1] + 30),
                             (c[0] + dx - 8, c[1] + 30)], c, -12))
    items.append(it(stripes, '#ffffff', 0, c, 0.92, 1.0))
    return {
        'note': 63,
        'label': "The pink stub in the blue-capped cone: hold D#4 to play; it turns into a cupcake, pink frosting swirling "
                 "up it roll by roll, sprinkles popping on the blue, and a tall swirl peak topped with a wrapped candy",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (2450, 2450, 600, 600),
    }


# ---- note-68: swim ring ----------------------------------------------------------------------------------------------
# The cyan ring f080 (a tilted ring, the purple plug f081 in its hole) puffs at once into a fat inflatable ring with a
# shine, candy stripes wipe round it one after another, a valve pops on its side, then a beach ball drops in from
# above, lands squashed on the ring and bounces up again at 4 s.

RING_C = (2428.0, 2924.0)
RING_A = -55.0   # the ring's long axis, degrees


def ell(c, rx, ry, a0, a1, rot_deg, n, seed=0, amt=0.0):
    rnd = random.Random(seed)
    a = math.radians(rot_deg)
    out = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        f = 1 + amt * math.sin(5 * t + rnd.random())
        x, y = rx * f * math.cos(t), ry * f * math.sin(t)
        out.append((c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a)))
    return out


def swim_ring() -> dict:
    INK = 13
    RO, RI = (150, 98), (74, 32)
    outer = ell(RING_C, *RO, 0, 360, RING_A, 36, 1, 0.025)[:-1]
    inner = ell((RING_C[0] - 8, RING_C[1] - 4), *RI, 360, 0, RING_A, 24, 2, 0.02)[:-1]
    torus = smooth(outer) + smooth(inner)  # the hole wound the other way, so it stays open
    items = [it(torus, '#5fe3ff', INK, RING_C, 0.0, 0.035)]
    # candy stripes: broad bowed sectors of the ring, wiped round it one after another
    IC = (RING_C[0] - 8, RING_C[1] - 4)
    shd = ell(IC, RI[0] + 22, RI[1] + 16, 160, 330, RING_A, 10) + ell(IC, RI[0] + 2, RI[1] + 2, 330, 160, RING_A, 10)
    items.append(it(smooth(shd), '#2bb5dd', 0, RING_C, 0.0, 0.035))
    for j in range(4):
        a0, a1 = j * 90 + 12, j * 90 + 60
        o = ell(RING_C, RO[0] - 2, RO[1] - 2, a0, a1, RING_A, 12, 1, 0.025)
        i_ = ell(IC, RI[0] + 2, RI[1] + 2, a1, a0, RING_A, 6, 2, 0.02)
        bow = lambda q0, q1, k_: ((q0[0] + q1[0]) / 2 + k_ * (q1[1] - q0[1]) * 0.12, (q0[1] + q1[1]) / 2 - k_ * (q1[0] - q0[0]) * 0.12)
        d = (f'M{p(*o[0])}' + ''.join(f'L{p(*q)}' for q in o[1:]) + f'Q{p(*bow(o[-1], i_[0], 1))} {p(*i_[0])}'
             + ''.join(f'L{p(*q)}' for q in i_[1:]) + f'Q{p(*bow(i_[-1], o[0], 1))} {p(*o[0])}Z')
        P = o[len(o) // 2]
        ang = math.degrees(math.atan2(-(P[1] - RING_C[1]), P[0] - RING_C[0]))
        s = 0.1 + 0.11 * j
        items.append(it(d, [HOT, '#ffffff', HOT, '#ffffff'][j] if j % 2 == 0 else YEL, 10, RING_C, s, s + 0.1,
                        sweep=(ang - 45, ang + 45)))
    # puffiness: a shadow inside the hole's far rim, a big shine on the near side; then the valve
    sh = ell(RING_C, 128, 80, 190, 255, RING_A, 8)
    sh2 = ell(RING_C, 106, 62, 255, 190, RING_A, 8)
    items.append(it(smooth(sh + sh2), '#ffffff', 0, RING_C, 0.015, 0.05))
    vx, vy = ell(RING_C, 150, 98, 95, 95, RING_A, 1)[0]
    items.append(it(lump(vx + 10, vy + 8, 20, 15, 30, 4), '#ffffff', 10, (vx, vy), 0.56, 0.64))

    # the beach ball: curved candy gores from pole to pole, turned a little; falling, landed squashed, bounced up
    def ball(cx, cy, r, sq=1.0, turn=-22):
        sx, sy = 1 / sq ** 0.5, sq
        T = lambda pts: [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in rot(pts, (cx, cy), turn)]
        mer = lambda ph, back=False: [(cx + r * math.sin(th) * math.sin(math.radians(ph)), cy - r * math.cos(th))
                                      for th in ([math.pi * q / 14 for q in range(15)][::-1] if back else
                                                 [math.pi * q / 14 for q in range(15)])]
        out = [(lump(cx, cy, r * sx, r * sy, turn, 11, 0.02), '#ffffff', INK)]
        for (pa, pb), col in (((-90, -52), HOT), ((-16, 18), YEL), ((52, 90), CYAN)):
            out.append((poly(T(mer(pa) + mer(pb, True))), col, 0))
        seams = ''.join(ltube(T(mer(ph))[1:-1], 2.5, 2.5, 0, 0.0) for ph in (-52, -16, 18, 52))
        seams += lump(*T([(cx, cy - r * 0.97)])[0], r * 0.13, r * 0.1, turn, 12)
        out.append((seams, '#1a1020', 0))
        return out
    poses = [((2470, 2640, 66, 1.0), 0.62, 0.68, (0.72, 0.75)),
             ((2482, 2786, 68, 0.78), 0.72, 0.75, (0.84, 0.87)),
             ((2492, 2660, 66, 1.0), 0.84, 0.88, None)]
    for (cx, cy, r, sq), s, e, out in poses:
        for d, col, ed in ball(cx, cy, r, sq):
            items.append(it(d, col, ed, (cx, cy), s, e, out=out))
    # motion crescents under the bounced ball
    for j, (r_, a0, a1) in enumerate(((88, 225, 315), (116, 232, 308))):
        items.append(it(crescent(2492, 2660, r_, a0, a1, 18), '#ffffff', 10, (2492, 2660), 0.88 + 0.04 * j, 0.96 + 0.04 * j))
    return {
        'note': 68,
        'label': "The cyan ring with the purple plug: hold G#4 to play; it puffs up into a fat candy-striped swim ring "
                 "and a beach ball drops onto it and bounces",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (2150, 2500, 650, 650),
    }


# ---- note-74: bat ----------------------------------------------------------------------------------------------------
# The dark wedge f203 (left tip 2618,2528; top corner 2776,2386; right corner 2844,2433), a shadowy hollow under the
# bush, turns into a bat: an ear pricks up from its top corner at once, its body puffs out, a scalloped wing unfolds out
# of each side, a head, a second ear and a face come, the wings stretch wide and it squeaks with two little fangs.

BAT = '#6e3046'
WING = '#94456a'


def wing(sh, span, up, side, seed, fingers=3):
    """A bat wing from the shoulder sh: the arm runs out and up to the tip, then the trailing edge comes back to the
    body in scallops hanging between finger tips. side = -1 for the left wing, +1 for the right. Returns the wing
    and its finger ribs (thin outlined fills from the wrist)."""
    rnd = random.Random(seed)
    x0, y0 = sh
    tip = (x0 + side * span, y0 - up)
    c1 = (x0 + side * span * 0.3, y0 - up * 0.9 - 30)
    c2 = (x0 + side * span * 0.75, y0 - up * 1.08 - 12)
    wrist = (x0 + side * span * 0.62, y0 - up * 0.98 - 14)
    D = 0.62 * span + 30
    fin = [tip]
    for f in range(1, fingers + 1):
        u = f / (fingers + 1)
        fin.append((x0 + side * span * (1 - u) * 1.02 + rnd.uniform(-6, 6),
                    y0 - up * (1 - u) + D * (0.55 + 0.45 * math.sin(math.pi * u)) + rnd.uniform(-8, 8)))
    fin.append((x0 + side * 10, y0 + 30))
    d = f'M{p(*sh)}C{p(*c1)} {p(*c2)} {p(*tip)}'
    for a_, b_ in zip(fin, fin[1:]):
        mx, my = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
        d += f'Q{p(mx - side * 6, my - 48 + rnd.uniform(-5, 5))} {p(*b_)}'
    d += 'Z'
    ribs = ''
    for k_, b_ in enumerate(fin[1:-1]):
        ribs += ltube([wrist, ((wrist[0] + b_[0]) / 2 + side * 6, (wrist[1] + b_[1]) / 2), b_], 4.5, 3, seed + k_, 0.05)
    return d, ribs


def bat() -> dict:
    INK = 12
    items = []
    # ears (behind the head) - the first pricks up from the wedge's top corner at once
    ear_r = smooth([(2770, 2412), (2778, 2370), (2795, 2320), (2810, 2300), (2818, 2340), (2815, 2385), (2802, 2418)])
    ear_l = smooth([(2712, 2420), (2702, 2380), (2700, 2330), (2708, 2312), (2728, 2335), (2748, 2375), (2748, 2418)])
    # wings: half-open, then stretched wide at the end
    shL, shR = (2716, 2448), (2790, 2448)
    poses = [
        (wing(shL, 160, 80, -1, 1), shL, (275, 135), 0.08, 0.3, (0.74, 0.8)),
        (wing(shR, 150, 75, 1, 2), shR, (-95, 45), 0.28, 0.48, (0.74, 0.8)),
        (wing(shL, 190, 150, -1, 3), shL, (275, 115), 0.74, 0.88, None),
        (wing(shR, 185, 140, 1, 4), shR, (-95, 65), 0.76, 0.9, None),
    ]
    for (d, ribs), sh, sw, s, e, out in poses:
        items.append(it(d, WING, INK, sh, s, e, out=out, sweep=sw))
        items.append(it(ribs, BAT, 8, sh, s + 0.04, e, out=out, sweep=sw))
    items.append(it(lump(2753, 2470, 62, 52, 0, 1, 0.07), BAT, INK, (2753, 2500), 0.03, 0.12))  # the body
    items.append(it(ear_r, BAT, INK, (2792, 2410), 0.0, 0.04))
    items.append(it(smooth([(2790, 2400), (2798, 2350), (2806, 2328), (2808, 2380)]), PINK, 0, (2792, 2410), 0.0, 0.04))
    items.append(it(ear_l, BAT, INK, (2725, 2415), 0.44, 0.52))
    items.append(it(smooth([(2716, 2405), (2712, 2350), (2730, 2370), (2738, 2405)]), PINK, 0, (2725, 2415), 0.46, 0.52))
    head = lump(2758, 2418, 58, 48, 0, 3, 0.06)
    items.append(it(head, BAT, INK, (2758, 2440), 0.5, 0.6))
    # face: eyes, a pink snout, then the squeak
    for ex in (2735, 2782):
        for d, col, ed in eye(ex, 2404, 13, (0.0, 0.15), 9):
            items.append(it(d, col, ed, (ex, 2404), 0.58, 0.66))
    items.append(it(lump(2759, 2428, 17, 12, 0, 5), '#ff7fae', 10, (2759, 2428), 0.62, 0.7))
    mouth = smooth([(2738, 2444), (2759, 2441), (2780, 2444), (2772, 2468), (2759, 2474), (2746, 2468)])
    items.append(it(mouth, '#2a0c18', 9, (2759, 2448), 0.86, 0.94))
    for fx in (2748, 2770):
        items.append(it(poly([(fx - 6, 2446), (fx + 6, 2446), (fx, 2461)]), '#ffffff', 0, (fx, 2446), 0.9, 0.95))
    for j, (r_, a0, a1) in enumerate(((92, 112, 150), (120, 116, 146))):
        items.append(it(crescent(2759, 2455, r_, a0, a1, 15), YEL, 9, (2759, 2455), 0.9 + 0.03 * j, 0.97 + 0.03 * j))
    return {
        'note': 74,
        'label': "The dark maroon wedge under the bush: hold D5 to play; it turns into a bat, an ear pricking up, wings "
                 "unfolding one then the other and stretching wide, and it squeaks",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (2450, 2150, 600, 600),
    }


# ---- note-102: grasshopper -------------------------------------------------------------------------------------------
# The tiny serrated tuft f160 at the waterfall's spout becomes a grasshopper facing up-left: two antennae spring up at
# once, its body swells out of the tuft, its head and a round eye, a serrated leaf wing, its big hind leg folds up, its
# front legs, then it kicks the hind leg back and chirps.

GREEN, GDARK, GLIME = '#6cc04a', '#3f8a2f', '#b6f05a'


def grasshopper() -> dict:
    INK = 10
    items = []
    head = (1572, 2062)
    # 0-0.04: the antennae spring up from the tuft
    for j, P in enumerate((bez((1566, 2046), (1560, 1990), (1585, 1950), (1630, 1935), 14),
                           bez((1580, 2044), (1590, 1995), (1625, 1975), (1668, 1975), 14))):
        items.append(it(ltube(P, 8, 5, j, 0.05), GLIME, INK, (1600, 2080), 0.0, 0.04 + 0.01 * j))
    # the hind leg (folded), behind the body
    thigh = ltube(bez((1630, 2112), (1650, 2080), (1675, 2045), (1695, 2030), 12), 20, 11, 3, 0.06)
    shin = ltube(bez((1695, 2030), (1700, 2060), (1702, 2110), (1700, 2140), 10), 7, 6, 4, 0.04)
    items.append(it(shin, GDARK, INK, (1695, 2030), 0.48, 0.58, out=(0.82, 0.86)))
    items.append(it(thigh, GREEN, INK, (1630, 2112), 0.42, 0.56, out=(0.82, 0.86)))
    # kicked back at 4 s
    thigh2 = ltube(bez((1630, 2112), (1660, 2092), (1695, 2072), (1716, 2060), 12), 20, 11, 5, 0.06)
    shin2 = ltube(bez((1716, 2060), (1738, 2080), (1758, 2105), (1772, 2128), 10), 7, 6, 6, 0.04)
    items.append(it(shin2, GDARK, INK, (1716, 2060), 0.86, 0.92))
    items.append(it(thigh2, GREEN, INK, (1630, 2112), 0.84, 0.9))
    # the body swells out of the tuft, then the head
    body = smooth([(1575, 2075), (1600, 2060), (1640, 2080), (1672, 2108), (1690, 2135), (1676, 2152), (1645, 2148),
                   (1605, 2125), (1580, 2105)])
    items.append(it(body, GREEN, INK, (1630, 2125), 0.04, 0.2))
    items.append(it(lump(head[0], head[1], 30, 26, -35, 1, 0.06), GREEN, INK, (1590, 2075), 0.14, 0.28))
    # the wing: a serrated leaf along its back, the tuft's own sawtooth
    wing = smooth([(1600, 2072), (1618, 2066), (1628, 2078), (1640, 2076), (1650, 2090), (1662, 2092), (1672, 2108),
                   (1686, 2118), (1672, 2124), (1640, 2110), (1610, 2092)])
    items.append(it(wing, GLIME, INK, (1600, 2080), 0.26, 0.4, 'x'))
    # the eye
    for d, col, ed in eye(1564, 2054, 12, (-0.2, 0.05), 9):
        items.append(it(d, col, ed, (1564, 2054), 0.34, 0.44))
    # front legs
    for j, P in enumerate((bez((1598, 2100), (1590, 2120), (1580, 2135), (1570, 2148), 8),
                           bez((1620, 2112), (1618, 2130), (1612, 2148), (1606, 2160), 8))):
        items.append(it(ltube(P, 6, 5, 7 + j, 0.04), GDARK, INK, P[0], 0.56 + 0.04 * j, 0.64 + 0.04 * j))
    # 4 s: chirp arcs off its head
    for j, (r_, a0, a1) in enumerate(((54, 118, 205), (82, 122, 200), (110, 128, 192))):
        items.append(it(crescent(1572, 2062, r_, a0, a1, 17), YEL, 9, (1572, 2062), 0.86 + 0.04 * j, 0.94 + 0.03 * j))
    return {
        'note': 102,
        'label': "The tiny green tuft at the waterfall's spout: hold F#7 to play; its antennae spring up and it turns "
                 "into a grasshopper that kicks its hind leg and chirps",
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (1400, 1850, 500, 500),
    }


DESIGNS = [hedgehog(), waterfall(), cupcake(), swim_ring(), bat(), grasshopper()]

if __name__ == '__main__':
    for d in DESIGNS:
        n = sum(len(e.get('items', [])) for e in d['effects'])
        print(f"note-{d['note']}: {n} sprite items")
    k.run(DESIGNS)
