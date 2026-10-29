# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b07: notes 22, 25, 41, 51, 84, 100.

    uv run scripts/notes_b07.py           # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b07.py 41        # just note-41
    uv run scripts/notes_b07.py export    # docs/objects/note-<n>/build.json
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks); ks.loader.exec_module(k)
p, tube, bez = k.p, k.tube, k.bez


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


def L(c, ang, u, v):
    """A point u along direction ang (degrees, screen: y down) from c and v across it."""
    a = math.radians(ang)
    return (c[0] + math.cos(a) * u - math.sin(a) * v, c[1] + math.sin(a) * u + math.cos(a) * v)


def blob(x, y, rx, ry, rot=0.0, seed=0, wob=0.1, n=9) -> str:
    """A lumpy, hand-drawn ellipse round (x, y), turned rot degrees."""
    rnd = random.Random(seed)
    P = []
    for j in range(n):
        a = j / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        P.append(L((x, y), rot, math.cos(a) * rx * f, math.sin(a) * ry * f))
    return closed(P)


def petal(c, ang, length, width, seed=0, base=8.0) -> str:
    """A lumpy petal or leaf from near c out along ang."""
    rnd = random.Random(seed)
    j = lambda s: 1 + (rnd.random() - 0.5) * 2 * s
    pts = [(base, -width * 0.16), (length * 0.32, -width * 0.5 * j(0.12)), (length * 0.72, -width * 0.42 * j(0.15)),
           (length * j(0.05), width * 0.04), (length * 0.74, width * 0.44 * j(0.15)), (length * 0.34, width * 0.5 * j(0.12)),
           (base, width * 0.16)]
    return closed([L(c, ang, u, v) for u, v in pts])


def crescent(c, r, a0, a1, w, seed=0, wob=0.04) -> str:
    """A fat, lumpy band along an arc (angles in screen degrees), pointed at both ends."""
    rnd = random.Random(seed)
    n = 14
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        rr = r * (1 + (rnd.random() - 0.5) * wob)
        t = max(2.0, math.sin(u * math.pi) * w / 2)
        outer.append((c[0] + math.cos(a) * (rr + t), c[1] + math.sin(a) * (rr + t)))
        inner.append((c[0] + math.cos(a) * (rr - t), c[1] + math.sin(a) * (rr - t)))
    return closed(outer + inner[::-1])


def star(c, r, seed=0, points=4, rot=-90.0) -> str:
    """A lumpy, soft-pointed glint."""
    rnd = random.Random(seed)
    P = []
    for j in range(points * 2):
        rr = r * (1.0 if j % 2 == 0 else 0.3) * (1 + (rnd.random() - 0.5) * 0.15)
        a = math.radians(rot + j * 180 / points)
        P.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    return closed(P)


def stripe(P, w) -> str:
    """A band along P, tapering to points at both ends (a fill, never a bare line)."""
    n = len(P)
    A, B = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * (0.3 + 0.7 * math.sin(math.pi * i / (n - 1)) ** 0.5)
        A.append((x + nx * ww, y + ny * ww))
        B.append((x - nx * ww, y - ny * ww))
    return closed(A + B[::-1])


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(max(0.0, s), 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


GREEN, GREEN2, STEM = '#6fd65a', '#3fae4a', '#8a5a2b'


# ---- note-22 A#0: the yellow plume out of the orange horn becomes a horn of plenty --------------------------------

def horn_of_plenty() -> dict:
    E = 15
    M = (742.0, 1985.0)  # the horn's mouth: every fruit tumbles out of it
    items = []
    # plum (tap): pops right out of the mouth
    pc = (636.0, 2008.0)
    items.append(it(blob(*pc, 66, 58, -25, 221, 0.07), '#b54be0', E, M, 0.0, 0.07))
    items.append(it(petal((662, 1958), -50, 74, 40, 222), GREEN, E * 0.8, (662, 1958), 0.05, 0.12))
    items.append(it(blob(612, 1990, 20, 10, -30, 223), '#e2b5ff', 0, (612, 1990), 0.06, 0.12))
    # pear (1 s): its neck up and right, back toward the mouth
    pr, pa = 70.0, -52.0
    pcen = (520.0, 2120.0)
    prof = []
    for deg in range(60, 301, 40):
        a = math.radians(deg)
        prof.append((math.cos(a) * pr, math.sin(a) * pr))
    for deg in (-110, -55, 0, 55, 110):
        a = math.radians(deg)
        prof.append((pr * 1.3 + math.cos(a) * pr * 0.56, math.sin(a) * pr * 0.56))
    prof = sorted(prof, key=lambda q: math.atan2(q[1], q[0] - pr * 0.45))
    rnd = random.Random(224)
    pear = closed([L(pcen, pa, u * (1 + (rnd.random() - 0.5) * 0.08), v * (1 + (rnd.random() - 0.5) * 0.08)) for u, v in prof])
    items.append(it(pear, '#cdee4c', E, M, 0.12, 0.3))
    items.append(it(blob(pcen[0] - 18, pcen[1] + 16, 30, 22, pa, 225, 0.12), '#ffa36b', 0, (pcen[0] - 18, pcen[1] + 16), 0.24, 0.33))
    tip = L(pcen, pa, pr * 1.84, 0)
    items.append(it(tube([L(pcen, pa, pr * 1.7, 0), L(pcen, pa, pr * 2.05, -6), L(pcen, pa, pr * 2.3, 4)], 9, 8), STEM, E * 0.7, tip, 0.27, 0.34))
    # grapes (2 s): one after another out of the mouth, hanging in a bunch
    grapes = [(470, 2196), (512, 2188), (550, 2206), (452, 2240), (494, 2236), (534, 2250), (474, 2284), (514, 2288), (494, 2328)]
    for j, (x, y) in enumerate(grapes):
        s = 0.31 + 0.022 * j
        items.append(it(blob(x, y, 34, 32, 0, 230 + j, 0.06, 8), '#9a5cff' if j % 2 else '#b583ff', E * 0.85, M, s, s + 0.1))
    items.append(it(petal((548, 2176), -35, 96, 64, 240), GREEN, E * 0.85, (548, 2176), 0.5, 0.56))
    # apple (3 s): rolls out further down
    ac = (568.0, 2338.0)
    items.append(it(blob(*ac, 80, 74, 0, 241, 0.06, 10), '#ff4d5e', E, M, 0.53, 0.7))
    items.append(it(tube([(566, 2270), (572, 2246), (582, 2228)], 9, 7), STEM, E * 0.7, (566, 2270), 0.66, 0.72))
    items.append(it(petal((582, 2236), -20, 66, 36, 242), GREEN, E * 0.8, (582, 2236), 0.68, 0.74))
    items.append(it(blob(540, 2306, 24, 12, -35, 243), '#ffd0d6', 0, (540, 2306), 0.68, 0.74))
    # melon (4 s): the heaviest last, landing at the plume's tip on the bush
    mc, mr = (650.0, 2466.0), -24.0
    items.append(it(blob(*mc, 138, 100, mr, 244, 0.05, 11), '#86e27a', E, M, 0.72, 0.88))
    for j, v in enumerate((-0.58, -0.2, 0.2, 0.58)):
        P = [L(mc, mr, u * 118, v * 86 * math.sqrt(max(0.0, 1 - u * u)) + 4 * math.sin(u * 7 + j)) for u in [x / 10 for x in range(-9, 10)]]
        items.append(it(stripe(P, 13), GREEN2, 0, mc, 0.84 + 0.025 * j, 0.93 + 0.025 * j))
    items.append(it(blob(*L(mc, mr, -40, -58), 40, 13, mr, 245), '#d4ffcc', 0, L(mc, mr, -40, -58), 0.92, 1.0))
    end = L(mc, mr, 136, -10)
    curl = k.spiral(end[0], end[1], math.radians(mr - 30), 26, 0.9, 0.5, -1, 18)
    items.append(it(tube(curl, 9, 6), GREEN2, E * 0.7, end, 0.92, 1.0))
    return {
        'note': 22,
        'label': 'The yellow plume pouring from the orange horn: hold A#0 to play; it becomes a horn of plenty, and big '
                 'candy fruit tumble out of the horn down it, a plum, a pear, a bunch of grapes, an apple and last a heavy '
                 'striped melon',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-25 C#1: the yellow pour under the blue bell turns into a baritone sax ------------------------------------

def bari_sax() -> dict:
    E = 15
    BRASS, BRASS2 = '#f2b33a', '#ffe08a'
    bell, ba = (1090.0, 2440.0), 35.0  # the ragged hem, its diagonal mouth facing down and left
    coat = [it('M955 2080L1275 2080L1275 2530L955 2530Z', BRASS, 0, (1200, 2082), 0.06, 0.42, 'y'),
            it(tube([(1236, 2128), (1244, 2210), (1238, 2300), (1220, 2400), (1204, 2480)], 13, 9), BRASS2, 0, (1236, 2128), 0.3, 0.46, 'y'),
            it(tube([(1150, 2272), (1100, 2318), (1036, 2362)], 11, 7), BRASS2, 0, (1150, 2272), 0.36, 0.48)]
    items = []
    # the tap: the hem flares into a brass bell rim, dark inside
    items.append(it(blob(*bell, 146, 54, ba, 251, 0.05, 11), BRASS, E, bell, 0.0, 0.06))
    items.append(it(blob(bell[0] + 4, bell[1] - 2, 114, 30, ba, 252, 0.06, 10), '#4a2a14', E * 0.6, bell, 0.02, 0.08))
    # the key rod and the candy keys popping on, one at a time, down the body
    keys = [((1236, 2188), 27, '#ff6fb5'), ((1230, 2256), 29, '#5fe0ff'), ((1210, 2322), 30, '#8ff0c0'),
            ((1182, 2378), 28, '#c39bff'), ((1112, 2318), 26, '#ffa04a'), ((1058, 2352), 24, '#ff6fb5')]
    for j, (c, r, col) in enumerate(keys):
        s = 0.4 + 0.065 * j
        items.append(it(blob(*c, r, r * 0.92, 0, 260 + j, 0.07, 8), col, E * 0.65, c, s, s + 0.08))
        items.append(it(blob(c[0] - r * 0.3, c[1] - r * 0.32, r * 0.3, r * 0.18, -30, 270 + j), '#ffffff', 0, c, s + 0.03, s + 0.09))
    # the honk: fat lumpy crescents burst out of the bell, left and down
    for j, (r, w, col) in enumerate(((150, 44, '#fff27a'), (215, 50, '#ff8fd0'), (280, 56, '#9ff0ff'))):
        s = 0.8 + 0.06 * j
        items.append(it(crescent(bell, r, 122, 200, w, 280 + j, 0.015), col, E * 0.8, bell, s, s + 0.08))
    return {
        'note': 25,
        'label': 'The yellow pour under the blue bell: hold C#1 to play; it turns into a brass baritone sax, its bell '
                 'flaring, the brass running down it and candy keys popping on one by one, and then it honks',
        'effects': [{'effect': 'sprites', 'place': 'on', 'items': coat},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-41 F2: the tall magenta petal becomes an ice lolly -------------------------------------------------------

def ice_lolly() -> dict:
    E = 12
    PINK = '#FF47C7'
    stick = [it('M1374 2296L1374 2448C1374 2476 1414 2476 1414 2448L1414 2296Z', '#f1cf8f', E, (1394, 2300), 0.0, 0.05, 'y')]
    coat = closed([(1314, 2168), (1316, 2118), (1324, 2080), (1346, 2048), (1380, 2034), (1408, 2042), (1420, 2074),
                   (1412, 2112), (1408, 2160), (1402, 2214), (1390, 2178), (1374, 2166), (1362, 2238), (1348, 2176),
                   (1334, 2172), (1326, 2200)])
    items = [it(tube([(1342, 2190), (1340, 2250), (1352, 2316)], 9, 7), '#ffaee6', 0, (1342, 2190), 0.0, 0.06, 'y')]
    items.append(it(coat, '#fff1d6', E, (1380, 2036), 0.08, 0.32, 'y'))
    items.append(it(tube([(1338, 2072), (1332, 2110), (1334, 2140)], 8, 6), '#ffffff', 0, (1338, 2072), 0.26, 0.34, 'y'))
    sprinkles = [((1356, 2088), 30, '#ffe34a'), ((1392, 2066), -40, '#5fe0ff'), ((1396, 2112), 70, '#7ee36a'),
                 ((1344, 2132), -12, '#ff8a3d'), ((1376, 2142), 48, '#b07bff'), ((1366, 2104), -70, '#ff5f8f')]
    for j, (c, a, col) in enumerate(sprinkles):
        s = 0.34 + 0.04 * j
        items.append(it(tube([L(c, a, -16, 0), L(c, a, 16, 0)], 8, 8), col, 6, c, s, s + 0.06))
    # melting: a cream drip runs past its left edge, a pink drip runs down the stick
    items.append(it(tube([(1322, 2160), (1318, 2212), (1322, 2258)], 12, 11), '#fff1d6', E * 0.85, (1322, 2160), 0.6, 0.76, 'y'))
    items.append(it(tube([(1396, 2338), (1395, 2370), (1397, 2398)], 10, 8), PINK, E * 0.85, (1394, 2340), 0.64, 0.8, 'y'))
    # a fat drop lets go and splats
    drop = closed([(1394, 2470), (1408, 2500), (1410, 2520), (1394, 2534), (1378, 2520), (1380, 2500)])
    items.append(it(drop, PINK, E * 0.85, (1394, 2440), 0.8, 0.88, 'scale', (0.9, 0.94)))
    items.append(it(blob(1398, 2568, 76, 21, -4, 291, 0.16, 11), PINK, E * 0.85, (1396, 2568), 0.88, 0.97))
    items.append(it(petal((1452, 2556), -40, 40, 20, 292, 0), PINK, E * 0.7, (1440, 2560), 0.91, 1.0))
    return {
        'note': 41,
        'label': 'The tall magenta petal on the pink flower creature: hold F2 to play; it becomes an ice lolly, a stick '
                 'pokes out, a cream dip pours over its top and sprinkles pop on, then it melts and a fat drop splats',
        'effects': [{'effect': 'sprites', 'place': 'around', 'items': stick},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-51 D#3: the pale blue lip of the blue bell freezes -------------------------------------------------------

def icicle(x0, y0, length, width, seed) -> str:
    rnd = random.Random(seed)
    j = lambda: (rnd.random() - 0.5) * width * 0.18
    w = width / 2
    return closed([(x0 - w, y0 - 12), (x0 - w * 0.86 + j(), y0 + length * 0.22), (x0 - w * 0.5 + j(), y0 + length * 0.5),
                   (x0 - w * 0.22, y0 + length * 0.82), (x0 + 2, y0 + length), (x0 + w * 0.26, y0 + length * 0.8),
                   (x0 + w * 0.56 + j(), y0 + length * 0.46), (x0 + w * 0.9 + j(), y0 + length * 0.2), (x0 + w, y0 - 12),
                   (x0, y0 - 20)])


def icicles() -> dict:
    E = 12
    ICE, ICE2 = '#a6d2ff', '#eef8ff'
    under = []
    for x0, y0, ln, wd, s, e, seed in ((1034, 2154, 140, 78, 0.0, 0.06, 301), (1130, 2118, 150, 74, 0.15, 0.35, 302),
                                        (1002, 2120, 104, 60, 0.33, 0.53, 304), (1080, 2156, 252, 94, 0.52, 0.78, 303)):
        under.append(it(icicle(x0, y0, ln, wd, seed), ICE, E, (x0, y0 - 12), s, e, 'y'))
        under.append(it(tube([(x0 - wd * 0.22, y0 + 6), (x0 - wd * 0.16, y0 + ln * 0.4), (x0 - wd * 0.04, y0 + ln * 0.72)], wd * 0.09, wd * 0.05),
                        ICE2, 0, (x0, y0 - 12), s + (e - s) * 0.4, e + 0.03, 'y'))
    rime = [it(stripe(bez((1000, 2104), (1030, 2146), (1110, 2140), (1160, 2062), 20), 16), '#f4fbff', 0, (1080, 2140), 0.08, 0.3),
            it(stripe(bez((1050, 2066), (1080, 2050), (1110, 2048), (1140, 2056), 10), 8), '#f4fbff', 0, (1095, 2052), 0.2, 0.36)]
    over = []
    tip = (1082.0, 2408.0)
    over.append(it(closed([(1082, 2392), (1100, 2418), (1100, 2440), (1082, 2454), (1064, 2440), (1064, 2418)]), ICE2, E * 0.8, tip, 0.78, 0.9))
    over.append(it(star((1126, 2410), 54, 320), '#ffffff', E * 0.8, (1126, 2410), 0.88, 1.0))
    return {
        'note': 51,
        'label': 'The pale blue lip of the blue bell: hold D#3 to play; it freezes, icicles growing from it one after '
                 'another, a crust of frost along it, and a drop that glints on the longest one',
        'effects': [{'effect': 'sprites', 'place': 'on', 'items': rime},
                    {'effect': 'sprites', 'place': 'around', 'items': under},
                    {'effect': 'sprites', 'place': 'over', 'items': over}],
    }


# ---- note-84 C6: the yellow in the eye tree's eye turns to eye candy -----------------------------------------------

def eye_candy() -> dict:
    E = 11
    PINK, YEL, WRAP = '#ff4fa3', '#ffe066', '#c2f0ff'
    t0 = (850.0, 2612.0)
    on = [it(stripe([(c - 70, 2612 - 70), (c, 2612), (c + 70, 2612 + 70)], 13), PINK, 0, t0, 0.0, 0.05) for c in (800, 850, 900)]
    on.append(it(blob(826, 2584, 9, 20, 30, 401), '#ffffff', 0, t0, 0.0, 0.05))
    cc, R = (760.0, 2656.0), 92.0
    over = []
    # the wrapper twists behind it: left, then right, each pinched at a knot by the sweet
    lk, rk = (664.0, 2668.0), (854.0, 2640.0)
    over.append(it(closed([(670, 2648), (620, 2600), (566, 2588), (544, 2640), (552, 2716), (604, 2730), (668, 2690)]), WRAP, E, lk, 0.3, 0.46))
    over.append(it(closed([(588, 2618), (566, 2652), (574, 2700), (612, 2690), (600, 2650)]), '#e8faff', 0, lk, 0.36, 0.48))
    over.append(it(closed([(848, 2620), (894, 2566), (950, 2550), (978, 2600), (970, 2674), (920, 2694), (850, 2662)]), WRAP, E, rk, 0.45, 0.62))
    over.append(it(closed([(930, 2580), (952, 2600), (948, 2656), (920, 2668), (934, 2622)]), '#e8faff', 0, rk, 0.5, 0.64))
    over.append(it(blob(*lk, 16, 26, 10, 402), '#9be0ff', E * 0.8, lk, 0.3, 0.42))
    over.append(it(blob(*rk, 16, 26, -20, 403), '#9be0ff', E * 0.8, rk, 0.45, 0.56))
    # the sweet pops out of the eye, then its pink swirl spins in arm by arm
    over.append(it(blob(*cc, R, R * 0.9, -15, 404, 0.05, 10), YEL, E, t0, 0.08, 0.3))
    for j in range(5):
        a0 = math.radians(-90 + j * 72)
        P = [(cc[0] + math.cos(a0 + u * 1.7) * R * u * 0.86, cc[1] + math.sin(a0 + u * 1.7) * R * u * 0.8) for u in [0.12 + 0.76 * q / 10 for q in range(11)]]
        over.append(it(stripe(P, 13), PINK, 0, cc, 0.62 + 0.045 * j, 0.7 + 0.045 * j))
    over.append(it(blob(cc[0] - 40, cc[1] - 46, 24, 11, -35, 405), '#ffffff', 0, (cc[0] - 40, cc[1] - 46), 0.8, 0.88))
    over.append(it(star((850, 2560), 54, 406), '#ffffff', E * 0.85, (850, 2560), 0.88, 1.0))
    return {
        'note': 84,
        'label': "The yellow in the eye tree's eye: hold C6 to play; it turns into eye candy, a striped sweet that pops "
                 'out of its eye, twists its wrapper out either side, and sparkles',
        'effects': [{'effect': 'sprites', 'place': 'on', 'items': on},
                    {'effect': 'sprites', 'place': 'over', 'items': over}],
    }


# ---- note-100 E7: the little yellow bud on the eye bush blossoms ---------------------------------------------------

def blossom() -> dict:
    E = 10
    C = (1448.0, 2652.0)
    items = []
    for j, (a, col) in enumerate(((-25, '#ff8fd0'), (45, '#8fe8ff'), (115, '#c9a2ff'), (185, '#ffb06a'), (255, '#ff8fd0'))):
        s = 0.66 + 0.055 * j
        items.append(it(petal(C, a, 124, 72, 500 + j, 16), col, E, C, s, s + 0.12))
    for j, (a, s, e) in enumerate(((-60, 0.0, 0.06), (220, 0.0, 0.06), (10, 0.15, 0.28), (150, 0.33, 0.46), (80, 0.5, 0.63))):
        items.append(it(petal(C, a, 90, 64, 510 + j, 8), '#fff27a' if j % 2 else '#ffe94d', E, C, s, e))
    items.append(it(blob(*C, 28, 26, 0, 520, 0.1, 8), '#ff9a3c', E, C, 0.0, 0.05))
    items.append(it(blob(C[0] - 7, C[1] - 8, 9, 7, 0, 521), '#ffd27a', 0, C, 0.03, 0.08))
    return {
        'note': 100,
        'label': 'The little yellow bud on the eye bush: hold E7 to play; it blossoms, a yellow petal at a time round an '
                 'orange middle, then a ring of candy petals opens behind',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


DESIGNS = [horn_of_plenty(), bari_sax(), ice_lolly(), icicles(), eye_candy(), blossom()]

if __name__ == '__main__':
    k.run(DESIGNS)
