# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Notes batch b11: 47 (turtle), 52 (cream drip), 55 (ballerina), 82 (chameleon), 87 (ear perks), 107 (hummingbird).

    uv run scripts/notes_b11.py            # strips and end frames
    uv run scripts/notes_b11.py 55         # one note
    uv run scripts/notes_b11.py export     # docs/objects/note-<n>/build.json
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
p, tube, bez, spiral, circle = k.p, k.tube, k.bez, k.spiral, k.circle
crescent = k.g.crescent


# ---- drawing helpers -----------------------------------------------------------------------------------------------

def closed(P) -> str:
    """A smooth closed Catmull-Rom curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def rot(x, y, cx, cy, deg):
    a = math.radians(deg)
    u, v = x - cx, y - cy
    return (cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a))


def blob(x, y, rx, ry, r=0.0, seed=0, wob=0.1, n=9) -> str:
    """A lumpy, hand-drawn ellipse round (x, y), turned r degrees."""
    rnd = random.Random(seed)
    P = []
    for i in range(n):
        a = i / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        P.append(rot(x + math.cos(a) * rx * f, y + math.sin(a) * ry * f, x, y, r))
    return closed(P)


def petal(base, ang, length, width, seed=0, lop=0.1) -> str:
    """A pointed, slightly lopsided petal, leaf or feather from base, heading ang degrees (y down)."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    bx, by = base
    Q = lambda u, v: (bx + ux * u + nx * v, by + uy * u + ny * v)
    w1, w2 = width * (1 - lop + rnd.random() * 2 * lop), width * (1 - lop + rnd.random() * 2 * lop)
    return (f'M{p(*Q(0, 0))}C{p(*Q(length * 0.25, w1))} {p(*Q(length * 0.7, w1 * 0.9))} {p(*Q(length, 0))}'
            f'C{p(*Q(length * 0.7, -w2 * 0.9))} {p(*Q(length * 0.25, -w2))} {p(*Q(0, 0))}Z')


def drop(tx, ty, cx, cy, r) -> str:
    """A drip: pointed at (tx, ty), swelling to a round bead of radius r centred on (cx, cy)."""
    a = math.atan2(cy - ty, cx - tx)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    L = math.hypot(cx - tx, cy - ty)
    Q = lambda u, v: (tx + ux * u + nx * v, ty + uy * u + ny * v)
    return (f'M{p(tx, ty)}C{p(*Q(L * 0.45, r * 0.18))} {p(*Q(L - r * 0.9, r * 1.02))} {p(*Q(L, r))}'
            f'C{p(*Q(L + r * 0.62, r))} {p(*Q(L + r * 1.05, r * 0.55))} {p(*Q(L + r * 1.02, 0))}'
            f'C{p(*Q(L + r * 1.05, -r * 0.55))} {p(*Q(L + r * 0.62, -r))} {p(*Q(L, -r))}'
            f'C{p(*Q(L - r * 0.9, -r * 1.02))} {p(*Q(L * 0.45, -r * 0.18))} {p(tx, ty)}Z')


def ruffle(cx, cy, rx, ry, n=14, depth=0.12, seed=0) -> str:
    """A lumpy ruffled ring (a tutu layer): an ellipse whose edge goes out in uneven scallops."""
    rnd = random.Random(seed)
    P = []
    for i in range(2 * n):
        a = i / (2 * n) * 2 * math.pi + (rnd.random() - 0.5) * 0.08
        f = (1 + (rnd.random() - 0.5) * 0.08) if i % 2 == 0 else (1 - depth * (0.7 + rnd.random() * 0.6))
        P.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
    return closed(P)


def tutu(cx, ty, hy, ht, hh, n=9, d=8.0, seed=0) -> str:
    """A tutu layer: narrow at the waist (y=ty), flaring flat out to a scalloped hem (y about hy), lumpy."""
    rnd = random.Random(seed)
    P = [(cx - ht, ty), (cx + ht, ty), (cx + hh, ty + (hy - ty) * 0.55)]
    m = 2 * n
    for i in range(m + 1):
        u = i / m
        x = cx + hh * 0.94 * (1 - 2 * u) + (rnd.random() - 0.5) * 4
        bow = 8 * math.sin(math.pi * u)
        y = hy + bow + (d if i % 2 == 0 else -d * 0.6) * (0.7 + rnd.random() * 0.6)
        P.append((x, y))
    P.append((cx - hh, ty + (hy - ty) * 0.55))
    return closed(P)


def crown(cx, by, w, h, n=5, seed=0) -> str:
    """A splash crown standing on the line y=by: n uneven tines with round-ish tips, a bowed foot."""
    rnd = random.Random(seed)
    x0, x1 = cx - w / 2, cx + w / 2
    d = f'M{p(x0, by)}'
    step = w / n
    for i in range(n):
        xa = x0 + i * step
        hi = h * (0.6 + 0.4 * math.sin((i + 0.5) / n * math.pi)) * (0.85 + rnd.random() * 0.3)
        tip = (xa + step * (0.5 + (rnd.random() - 0.5) * 0.3) + (i - (n - 1) / 2) * step * 0.18, by - hi)
        valley = (xa + step, by - h * 0.32)
        d += f'C{p(xa + step * 0.15, by - hi * 0.6)} {p(tip[0] - step * 0.3, tip[1])} {p(*tip)}'
        end = valley if i < n - 1 else (x1, by)
        d += f'C{p(tip[0] + step * 0.3, tip[1])} {p(end[0] - step * 0.15, end[1] - hi * 0.4)} {p(*end)}'
    d += f'C{p(x1 - w * 0.2, by + h * 0.22)} {p(x0 + w * 0.2, by + h * 0.22)} {p(x0, by)}Z'
    return d


def I(d, fill, edge, at, start, end, grow='scale', **kw) -> dict:
    it = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 3),
          'end': round(end, 3), 'grow': grow}
    for key, v in kw.items():
        it[key] = round(v, 3) if isinstance(v, float) else v
    return it


def out(it, a, b) -> dict:
    it['outStart'], it['outEnd'] = a, b
    return it


WHITE = '#ffffff'

# ---- note 47 B2: the orange disc becomes a turtle --------------------------------------------------------------------
# The disc (f079) is the base the pink figure's long neck (f075, with the ear flap f082) rises out of: it domes up into
# a shell behind the neck, plates pop on, legs push out from under it, a tail, and the front leg lifts mid-stride.


def turtle() -> list[dict]:
    E = 13
    base = (2356.0, 3292.0)
    rnd = random.Random(47)
    dome_pts = [(2222, 3294), (2226, 3240), (2246, 3192), (2284, 3154), (2334, 3132), (2388, 3128), (2432, 3144),
                (2464, 3178), (2484, 3224), (2492, 3270), (2470, 3298)]
    dome_pts = [(x + (rnd.random() - 0.5) * 8, y + (rnd.random() - 0.5) * 8) for x, y in dome_pts]
    dome = closed(dome_pts)
    items = [I(dome, '#F28C38', E, base, 0.0, 0.26, grow='y')]
    scutes = [((2358, 3172), 48, 30, 0, '#FFD24A'), ((2276, 3220), 34, 40, -24, '#FF7A59'),
              ((2440, 3212), 34, 40, 22, '#FF7A59'), ((2318, 3236), 36, 24, -6, '#FF8FCF'),
              ((2398, 3234), 36, 24, 6, '#FF8FCF')]
    for i, ((x, y), rx, ry, r, col) in enumerate(scutes):
        s = 0.2 + i * 0.075
        items.append(I(blob(x, y, rx, ry, r, seed=470 + i, wob=0.12, n=7), col, 11, (x, y), s, s + 0.11))
    SKIN = '#D9B45E'
    # back leg, front leg (standing), each a stubby lumpy limb with a foot
    for (hx, hy), (fx, fy), s, sd in [((2285, 3318), (2268, 3398), 0.5, 1), ((2462, 3318), (2482, 3396), 0.58, 2)]:
        leg = tube(bez((hx, hy), (hx - 4, hy + 30), (fx + 4, fy - 30), (fx, fy), 12), 30, 30)
        foot = blob(fx + 6, fy + 6, 42, 24, 0, seed=480 + sd, wob=0.12, n=8)
        it1 = I(leg, SKIN, E, (hx, hy), s, s + 0.12)
        it2 = I(foot, SKIN, E, (hx, hy), s, s + 0.12)
        it3 = I(leg, SKIN, 0, (hx, hy), s, s + 0.12)
        for it in (it1, it2, it3):
            out(it, 0.8, 0.88) if sd == 2 else out(it, 0.86, 0.92)
        items += [it1, it2, it3]
    # tail
    items.append(I(tube(bez((2236, 3302), (2214, 3306), (2198, 3318), (2182, 3336), 12), 18, 6), SKIN, 12, (2236, 3302), 0.68, 0.8))
    # the front leg lifted forward, mid-stride
    hx, hy, fx, fy = 2462, 3318, 2552, 3352
    leg = tube(bez((hx, hy), (hx + 30, hy + 10), (fx - 30, fy + 4), (fx, fy), 12), 30, 30)
    foot = blob(fx + 10, fy + 2, 26, 40, -25, seed=489, wob=0.12, n=8)
    items += [I(leg, SKIN, E, (hx, hy), 0.8, 0.92), I(foot, SKIN, E, (hx, hy), 0.8, 0.92), I(leg, SKIN, 0, (hx, hy), 0.8, 0.92)]
    # a shine on the shell, and motion crescents behind the lifted foot
    items.append(I(blob(2296, 3170, 26, 10, -40, seed=490, wob=0.1, n=8), WHITE, 0, (2296, 3170), 0.86, 1.0))
    # the back leg pushing off behind
    hx, hy, fx, fy = 2285, 3318, 2236, 3392
    leg = tube(bez((hx, hy), (hx - 10, hy + 30), (fx + 16, fy - 26), (fx, fy), 12), 30, 30)
    foot = blob(fx - 8, fy + 6, 40, 22, 18, seed=491, wob=0.12, n=8)
    items += [I(leg, SKIN, E, (hx, hy), 0.86, 0.96), I(foot, SKIN, E, (hx, hy), 0.86, 0.96), I(leg, SKIN, 0, (hx, hy), 0.86, 0.96)]
    return items


# ---- note 52 E3: the cream pennant drips ---------------------------------------------------------------------------
# Its point (2169.6, 3166.4) swells into a bead, stretches, necks in, lets the drop go, and it lands in a crown splash.

def cream_drip() -> list[dict]:
    tx, ty = 2169.6, 3160.0
    C, E = '#F3EEBE', 13
    items = []
    poses = [((2170, 3200), 32, 0.0, 0.08, 0.14, 0.2), ((2172, 3236), 42, 0.12, 0.3, 0.34, 0.4),
             ((2174, 3276), 52, 0.32, 0.52, 0.56, 0.6)]
    for (cx, cy), r, s, e, o1, o2 in poses:
        items.append(out(I(drop(tx, ty, cx, cy, r), C, E, (tx, ty), s, e), o1, o2))
        items.append(out(I(blob(cx - r * 0.38, cy - r * 0.2, r * 0.22, r * 0.34, 20, seed=int(cy), wob=0.1, n=7), WHITE, 0,
                           (tx, ty), s, e), o1, o2))
    # what stays on the tip once the drop lets go
    items.append(I(drop(tx, ty, 2170, 3188, 22), C, E, (tx, ty), 0.55, 0.62))
    # the falling drop, with its shine
    fd = drop(2172, 3296, 2172, 3346, 48)
    items.append(out(I(fd, C, E, (2172, 3346), 0.56, 0.64), 0.72, 0.78))
    items.append(out(I(blob(2154, 3334, 11, 17, 20, seed=523, wob=0.1, n=7), WHITE, 0, (2172, 3346), 0.56, 0.64), 0.72, 0.78))
    # the crown splash
    cx, by = 2146, 3400
    items.append(I(blob(cx, by + 6, 136, 32, 0, seed=521, wob=0.08, n=10), C, E, (cx, by + 6), 0.7, 0.8, grow='x'))
    items.append(I(crown(cx, by, 236, 132, n=5, seed=52), C, E, (cx, by + 6), 0.74, 0.9, grow='y'))
    items.append(I(blob(cx, by + 2, 100, 16, 0, seed=522, wob=0.1, n=8), '#FFFBE0', 0, (cx, by + 6), 0.76, 0.9, grow='x'))
    for i, (x, y, r) in enumerate([(1996, 3262, 24), (2060, 3206, 22), (2296, 3330, 22)]):
        items.append(I(blob(x, y, r, r * 1.1, 0, seed=524 + i, wob=0.1, n=7), C, 12, (x, y), 0.86 + i * 0.04, 0.94 + i * 0.02))
    return items


# ---- note 55 G3: the little pink horned figure dances ---------------------------------------------------------------
# Its purple skirt (f171) ruffles into a three-layer tutu, its arms go out and then up into a ring over its horns
# (behind them), a leg drops to a pointe shoe, and swirl crescents spin round it.

def ballerina() -> list[dict]:
    E = 12
    waist = (1908.0, 3326.0)
    items = [
        I(tutu(1908, 3298, 3388, 72, 172, n=5, d=9, seed=551), '#E6BCFF', E, waist, 0.0, 0.12, grow='x'),
        I(tutu(1908, 3302, 3360, 68, 148, n=4, d=8, seed=552), '#FF7FD0', E, waist, 0.12, 0.28, grow='x'),
        I(tutu(1908, 3306, 3334, 64, 120, n=4, d=7, seed=553), '#BC24FF', E, waist, 0.24, 0.4, grow='x'),
    ]
    PINK = '#FF24B4'
    # arms out to the sides (they go as the arms rise)
    for sx, sy, P in [(1852, 3226, ((1852, 3226), (1810, 3222), (1775, 3200), (1746, 3170))),
                      (1960, 3222, ((1960, 3222), (2002, 3216), (2038, 3194), (2066, 3162)))]:
        d = tube(bez(*P, 14), 14, 12)
        hx, hy = P[-1]
        hand = blob(hx + (hx - sx) * 0.06, hy - 6, 17, 15, 0, seed=int(hx), wob=0.1, n=7)
        for dd, e in [(d, E), (hand, E), (d, 0)]:
            items.append(out(I(dd, PINK, e, (sx, sy), 0.38, 0.52), 0.58, 0.66))
    # arms up in a ring over the horns
    for sx, sy, P in [(1852, 3226, ((1852, 3226), (1770, 3190), (1770, 3010), (1896, 2984))),
                      (1960, 3222, ((1960, 3222), (2048, 3180), (2040, 3002), (1922, 2982)))]:
        d = tube(bez(*P, 22), 14, 12)
        items.append(I(d, PINK, E, (sx, sy), 0.56, 0.72))
    items.append(I(blob(1909, 2984, 22, 17, 0, seed=559, wob=0.1, n=7), PINK, E, (1909, 2984), 0.64, 0.72))
    for sx, sy, P in [(1852, 3226, ((1852, 3226), (1770, 3190), (1770, 3010), (1896, 2984))),
                      (1960, 3222, ((1960, 3222), (2048, 3180), (2040, 3002), (1922, 2982)))]:
        items.append(I(tube(bez(*P, 22)[-5:], 13, 12), PINK, 0, (sx, sy), 0.56, 0.72))
    # a leg down to a pointe shoe
    leg = tube(bez((1906, 3350), (1907, 3380), (1910, 3410), (1912, 3436), 10), 15, 13)
    shoe = (f'M{p(1894, 3428)}C{p(1892, 3452)} {p(1902, 3474)} {p(1912, 3480)}C{p(1922, 3474)} {p(1932, 3452)} '
            f'{p(1930, 3428)}C{p(1922, 3420)} {p(1902, 3420)} {p(1894, 3428)}Z')
    items += [I(leg, PINK, E, (1906, 3350), 0.72, 0.84, grow='y'), I(shoe, '#E6BCFF', E, (1906, 3350), 0.74, 0.86, grow='y'),
              I(leg, PINK, 0, (1906, 3350), 0.72, 0.84, grow='y')]
    # swirl crescents spinning round it
    for i, (r, a0, a1, col) in enumerate([(185, 195, 250, WHITE), (185, 15, 70, '#7FE8FF'), (225, 280, 320, '#FFE14A')]):
        items.append(I(crescent(1908, 3200, r, a0, a1, 24), col, 11, (1908, 3200), 0.84 + i * 0.04, 0.94 + i * 0.02))
    return items


# ---- note 82 A#5: the lime hook is a chameleon's head --------------------------------------------------------------
# The hook (f078) is the head, its curl the mouth line, snout at the left: a turret eye bulges, a body arches out to the
# right over the yellow pod's tip, legs grip, a tail coils, the tongue zaps out left, candy stripes flush its body.

def chameleon() -> tuple[list[dict], list[dict]]:
    E = 11
    LIME, DEEP = '#87FF48', '#3FCF4A'
    items = []
    # tail coil (drawn first, under the body)
    P = [(2944, 3148), (2978, 3156)] + spiral(2978, 3156, math.radians(70), 40, 1.4, 0.75, 1, 44)[1:]
    items.append(I(tube(P, 17, 7), LIME, E, (2944, 3150), 0.38, 0.56))
    # legs
    for (hx, hy), (fx, fy), s in [((2830, 3160), (2818, 3212), 0.3), ((2930, 3162), (2944, 3214), 0.36)]:
        leg = tube(bez((hx, hy), (hx - 2, hy + 20), (fx + 2, fy - 18), (fx, fy), 10), 16, 15)
        items.append(I(leg, LIME, E, (hx, hy), s, s + 0.1))
        items.append(I(blob(fx, fy + 8, 25, 13, 0, seed=int(fx), wob=0.12, n=7), DEEP, E, (hx, hy), s, s + 0.1))
        items.append(I(leg, LIME, 0, (hx, hy), s, s + 0.1))
    # body: arched, lumpy, from behind the head out over the pod's tip
    body = closed([(2780, 3185), (2786, 3140), (2812, 3108), (2856, 3090), (2902, 3092), (2942, 3112), (2960, 3146),
                   (2944, 3176), (2896, 3172), (2850, 3176), (2810, 3190)])
    items.append(I(body, LIME, E, (2790, 3160), 0.14, 0.34))
    # back ridge bumps (fill + outline, then the body top laid again so they join)
    for i, (x, y) in enumerate([(2830, 3104), (2870, 3091), (2910, 3094)]):
        items.append(I(blob(x, y, 16, 12, 0, seed=820 + i, wob=0.1, n=7), DEEP, 10, (2790, 3160), 0.2 + i * 0.03, 0.36 + i * 0.03))
    items.append(I(blob(2870, 3134, 76, 34, -3, seed=829, wob=0.06, n=10), LIME, 0, (2790, 3160), 0.28, 0.4))
    # tongue zaps left out of the snout, with a sticky tip
    tongue = tube(bez((2676, 3150), (2630, 3146), (2584, 3132), (2548, 3112), 16), 12, 10)
    items.append(I(tongue, '#FF5FA8', E, (2672, 3150), 0.6, 0.72, grow='x'))
    items.append(I(blob(2538, 3106, 22, 19, 0, seed=823, wob=0.12, n=8), '#FF5FA8', E, (2672, 3150), 0.64, 0.76))
    # turret eye on the head (drawn over it), its pupil looking right, then left at the tongue
    eye = []
    eye.append(I(blob(2730, 3160, 30, 27, 0, seed=824, wob=0.08, n=8), LIME, E, (2730, 3160), 0.0, 0.07))
    eye.append(I(circle(2730, 3160, 15), '#FFE14A', 9, (2730, 3160), 0.03, 0.09))
    eye.append(out(I(circle(2736, 3160, 7), '#000', 0, (2736, 3160), 0.08, 0.15), 0.55, 0.6))
    eye.append(I(circle(2723, 3159, 7), '#000', 0, (2723, 3159), 0.57, 0.62))
    # candy stripes flush across the body
    for i, (x, col) in enumerate([(2832, '#FF5FA8'), (2876, '#FFE14A'), (2918, '#3FD8FF')]):
        d = blob(x, 3136, 15, 34, 8, seed=830 + i, wob=0.12, n=8)
        items.append(I(d, col, 9, (x, 3136), 0.8 + i * 0.06, 0.9 + i * 0.033))
    return items, eye


# ---- note 87 D#6: the peach ear perks up and listens ---------------------------------------------------------------
# The ear (f245) on the lying creature's head (f014) stands up taller, opens pink inside, a tuft springs from its tip,
# it swivels to the right, and three listening arcs come in to it.

def ear_perks() -> list[dict]:
    E = 11
    PEACH, PINK, TUFT = '#F2B48E', '#FF8FB8', '#C4664A'
    root = (2242.0, 3812.0)
    items = []
    # pose 1: standing up tall
    ear1 = closed([(2198, 3818), (2206, 3752), (2224, 3690), (2250, 3640), (2284, 3618), (2304, 3640), (2302, 3700),
                   (2292, 3760), (2286, 3818)])
    in1 = closed([(2228, 3792), (2238, 3730), (2256, 3678), (2280, 3652), (2288, 3690), (2280, 3748), (2268, 3796)])
    tuft1 = [petal((2286, 3628), a, l, 13, seed=870 + i) for i, (a, l) in enumerate([(-112, 54), (-84, 70), (-60, 52)])]
    items.append(out(I(ear1, PEACH, E, root, 0.0, 0.08, grow='y'), 0.44, 0.48))
    items.append(out(I(in1, PINK, 9, root, 0.1, 0.22, grow='y'), 0.44, 0.48))
    for i, d in enumerate(tuft1):
        items.append(out(I(d, TUFT, 9, (2286, 3628), 0.2 + i * 0.04, 0.3 + i * 0.04), 0.44, 0.48))
    # pose 2: swivelled toward the right, wider open
    # (wide enough to cover the cream under-fill f026 the painted ear leaves behind when it goes)
    ear2 = closed([(2190, 3818), (2180, 3752), (2170, 3690), (2172, 3640), (2196, 3604), (2236, 3606), (2268, 3640),
                   (2292, 3690), (2300, 3760), (2296, 3818)])
    in2 = closed([(2214, 3798), (2200, 3740), (2192, 3684), (2200, 3644), (2226, 3632), (2252, 3664), (2272, 3720),
                  (2276, 3796)])
    tuft2 = [petal((2210, 3606), a, l, 13, seed=875 + i) for i, (a, l) in enumerate([(-145, 54), (-115, 72), (-86, 54)])]
    items.append(I(ear2, PEACH, E, root, 0.4, 0.44))
    items.append(I(in2, PINK, 9, root, 0.41, 0.45))
    for i, d in enumerate(tuft2):
        items.append(I(d, TUFT, 9, (2210, 3606), 0.42 + i * 0.02, 0.46 + i * 0.02))
    # listening arcs coming in to it from the open ground on its left, outermost first
    for i, (r, col) in enumerate([(150, '#7FE8FF'), (112, '#FFE14A'), (76, '#FF8FD8')]):
        items.append(I(crescent(2192, 3650, r, 150, 222, 22), col, 10, (2192, 3650), 0.6 + i * 0.12, 0.72 + i * 0.12))
    return items


# ---- note 107 B7: the lime spike is a hummingbird's bill -----------------------------------------------------------
# The spike (f095) on the waving pink creature's snout: a head pops on at its base, a body and tail tilt down to the
# left, two wings blur up, its throat flashes pink, and motion crescents buzz round the wings.

def hummingbird() -> list[dict]:
    E = 10
    G, DG, WING = '#3BD16F', '#1E9E5A', '#C9F6FF'
    head = (1716.0, 3440.0)
    items = []
    # wings (under the body)
    w1 = petal((1690, 3452), -128, 118, 30, seed=1071)
    w2 = petal((1694, 3450), -100, 104, 26, seed=1072)
    items.append(I(w2, WING, E, (1692, 3452), 0.5, 0.64))
    items.append(I(w1, WING, E, (1692, 3452), 0.38, 0.54))
    # tail
    for i, a in enumerate([118, 136, 152]):
        items.append(I(petal((1640, 3508), a, 54, 12, seed=1073 + i), DG, E, (1640, 3508), 0.22 + i * 0.04, 0.34 + i * 0.04))
    # body
    body = blob(1668, 3482, 52, 30, 38, seed=1076, wob=0.08, n=9)
    items.append(I(body, G, E, head, 0.08, 0.24))
    items.append(I(blob(1676, 3496, 26, 12, 38, seed=1077, wob=0.1, n=8), '#E9FFE0', 0, head, 0.14, 0.26))
    # head at the bill's base, with an eye
    items.append(I(blob(1712, 3442, 30, 28, 0, seed=1078, wob=0.07, n=8), G, E, head, 0.0, 0.07))
    items.append(I(circle(1714, 3434, 7.5), '#000', 0, (1714, 3434), 0.03, 0.08))
    items.append(I(circle(1716, 3431, 2.6), WHITE, 0, (1716, 3431), 0.05, 0.09))
    # pink throat flash
    items.append(I(blob(1704, 3466, 20, 12, 20, seed=1079, wob=0.12, n=7), '#FF24B4', 9, (1708, 3460), 0.66, 0.8))
    items.append(I(blob(1700, 3464, 7, 4, 20, seed=1080, wob=0.1, n=6), WHITE, 0, (1700, 3464), 0.88, 0.98))
    # motion crescents buzzing round the wings
    for i, (r, a0, a1) in enumerate([(140, 95, 140), (140, 150, 185)]):
        items.append(I(crescent(1692, 3452, r, a0, a1, 20), WHITE, 9, (1692, 3452), 0.8 + i * 0.07, 0.9 + i * 0.05))
    return items


DESIGNS = [
    {'note': 47, 'label': 'The orange disc the pink figure rises from: hold B2 to play; it domes up into a turtle shell, '
                          'plates pop on it, legs push out, a tail flicks and the front foot lifts mid-stride',
     'crop': (1960, 2900, 760, 760),
     'effects': [{'effect': 'sprites', 'place': 'around', 'items': turtle()}]},
    {'note': 52, 'label': 'The pale cream pennant under the green bank: hold E3 to play; its point drips, stretches and '
                          'lets the drop go into a crown splash',
     'crop': (1900, 3020, 560, 560),
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': cream_drip()}]},
    {'note': 55, 'label': 'The little pink horned figure: hold G3 to play; its skirt ruffles into a tutu, its arms rise '
                          'into a ring over its horns and it spins up onto a pointe shoe',
     'crop': (1660, 2900, 600, 600),
     'effects': [{'effect': 'sprites', 'place': 'around', 'front': ['f172', 'f173'], 'items': ballerina()}]},
    {'note': 82, 'label': 'The lime hook on the yellow pod: hold A#5 to play; it is a chameleon\'s head: a turret eye '
                          'bulges, its body and coiled tail come out, its tongue zaps and it flushes candy stripes',
     'crop': (2500, 2900, 560, 560),
     'effects': [{'effect': 'sprites', 'place': 'around', 'items': chameleon()[0]},
                 {'effect': 'sprites', 'place': 'over', 'items': chameleon()[1]}]},
    {'note': 87, 'label': 'The peach ear on the lying creature\'s head: hold D#6 to play; it perks up tall, a tuft springs '
                          'from its tip, it swivels and listening arcs come in to it',
     'crop': (2020, 3460, 440, 440),
     'effects': [{'effect': 'vanish', 'span': [0, 0.06]},
                 {'effect': 'sprites', 'place': 'around', 'own': False, 'front': ['f014'], 'items': ear_perks()}]},
    {'note': 107, 'label': 'The lime spike on the pink creature\'s snout: hold B7 to play; it is a hummingbird\'s bill: a '
                           'head, body and tail pop on, its wings blur up and its throat flashes pink',
     'crop': (1520, 3260, 420, 420),
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': hummingbird()}]},
]

if __name__ == '__main__':
    k.run(DESIGNS)
