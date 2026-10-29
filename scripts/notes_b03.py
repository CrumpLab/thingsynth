# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b03: notes 21, 32, 39, 40, 96, 108.

    uv run scripts/notes_b03.py            # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b03.py 21         # just note-21
    uv run scripts/notes_b03.py export     # docs/objects/note-<n>/build.json
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks)
ks.loader.exec_module(k)
m, p, circle, ellipse, bez, tube = k.m, k.p, k.circle, k.ellipse, k.bez, k.tube


# ---- drawing helpers -----------------------------------------------------------------------------------------------

def closed(pts) -> str:
    """A smooth closed outline through the points (Catmull-Rom as cubics)."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def poly(pts) -> str:
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def blob(cx, cy, rx, ry, seed, wob=0.08, n=11, rot=0.0) -> str:
    """A lumpy hand-drawn oval, rotated rot degrees."""
    rnd = random.Random(seed)
    r0 = math.radians(rot)
    pts = []
    for j in range(n):
        a = j / n * 2 * math.pi
        f = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r0) - y * math.sin(r0), cy + x * math.sin(r0) + y * math.cos(r0)))
    return closed(pts)


def lumpy_tube(P, w0, w1, seed, jit=0.06, cap=True) -> str:
    """A tapered outlined limb along P whose width wobbles a little."""
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
        fl, fr = 1 + jit * math.sin(u * 9 + ph1), 1 + jit * math.sin(u * 7 + ph2)
        L.append((x + nx * w * fl, y + ny * w * fl))
        R.append((x - nx * w * fr, y - ny * w * fr))
    rr = max(1.0, math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1]) / 2)
    end = f'A{rr:.1f} {rr:.1f} 0 0 1 {p(*R[-1])}' if cap else f'L{p(*R[-1])}'
    return 'M' + 'L'.join(p(*q) for q in L) + end + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def star(cx, cy, r, points=4, inner=0.38, seed=0, rot=0.0) -> str:
    """A fat, slightly lopsided sparkle star with rounded-off points."""
    rnd = random.Random(seed)
    pts = []
    for j in range(points * 2):
        a = math.radians(rot) + j * math.pi / points
        rr = r * (1 if j % 2 == 0 else inner) * (1 + 0.08 * (rnd.random() * 2 - 1))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return closed(pts)


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 4), 'end': round(e, 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    return x


def outer_contour(fid: str, per=5):
    """The first subpath of a painted fill, flattened to points (its outer edge)."""
    d = m.FILLS[fid]
    first = d.split('Z')[0]
    nums = [float(t) for t in re.findall(r'-?\d+\.?\d*', first)]
    pts = list(zip(nums[0::2], nums[1::2]))
    out = [pts[0]]
    for i in range(1, len(pts) - 2, 3):
        a, b, c, e = out[-1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(1, per + 1):
            u = s / per
            w = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3]
            out.append((sum(q * v[0] for q, v in zip(w, (a, b, c, e))), sum(q * v[1] for q, v in zip(w, (a, b, c, e)))))
    # drop near-duplicates
    clean = [out[0]]
    for q in out[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 3:
            clean.append(q)
    return clean


def clip_half(pts, A, nrm):
    """Sutherland-Hodgman: keep the part of the polygon on the side of the line through A that nrm points to."""
    side = lambda q: (q[0] - A[0]) * nrm[0] + (q[1] - A[1]) * nrm[1]
    out = []
    for i in range(len(pts)):
        P, Q = pts[i - 1], pts[i]
        sp, sq = side(P), side(Q)
        if sq >= 0:
            if sp < 0:
                t = sp / (sp - sq)
                out.append((P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t))
            out.append(Q)
        elif sp >= 0:
            t = sp / (sp - sq)
            out.append((P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t))
    return out


def reflect(pts, A, B):
    ux, uy = B[0] - A[0], B[1] - A[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    out = []
    for x, y in pts:
        t = (x - A[0]) * ux + (y - A[1]) * uy
        fx, fy = A[0] + t * ux, A[1] + t * uy
        out.append((2 * fx - x, 2 * fy - y))
    return out


# ---- note-21 A0: the ghost's pale half plays peekaboo --------------------------------------------------------------

def note21() -> dict:
    INK = 14
    DARK, UNDER = '#2E2350', '#9CBDE2'
    xl, xr = 2735.0, 2950.0
    # the hem rises in tugs, the left corner first and highest; each pose is a scalloped hem line with the dark
    # inside below it (clipped to the pale half), and the corner of the sheet turned up at its left end
    poses = [((1428, 1575), (0.0, 0.1)),
             ((1384, 1482), (0.14, 0.27)),
             ((1334, 1426), (0.3, 0.44)),
             ((1286, 1372), (0.5, 0.64)),
             ((1238, 1322), (0.78, 0.9))]
    on, over = [], []
    for j, ((yl, yr), (s, e)) in enumerate(poses):
        rnd = random.Random(60 + j)
        n = 5
        hem = []
        for q in range(n * 6 + 1):
            u = q / (n * 6)
            x = xl + (xr - xl) * u
            y = yl + (yr - yl) * u + 13 * abs(math.sin(math.pi * u * n + 0.4)) + rnd.uniform(-1.5, 1.5)
            hem.append((x, y))
        dark = 'M' + 'L'.join(p(*q) for q in hem) + f'L{p(xr, 1660)}L{p(xl, 1660)}Z'
        nxt = poses[j + 1][1][0] if j + 1 < len(poses) else None
        on.append(it(dark, DARK, INK, (2840, 1660), s, e, grow='y'))
        # the lifted hem, bunched up into a soft roll of sheet, its left corner curling up highest
        x1 = [2850, 2905, 2928, 2928, 2928][j]
        y_at = lambda x: yl + (yr - yl) * (x - xl) / (xr - xl)
        N = 16
        upper, lower = [], []
        for q in range(N + 1):
            u = q / N
            x = 2748 + (x1 - 2748) * u
            curl = 34 * (1 - u) ** 3
            upper.append((x, y_at(x) - 50 - curl + 5 * math.sin(u * 11 + j) + rnd.uniform(-3, 3)))
            lower.append((x, y_at(x) + 6 + 12 * abs(math.sin(math.pi * u * 3.2 + 0.3)) - curl * 0.6))
        capL = [(2718, y_at(2748) - 20), (2706, y_at(2748) - 62), (2730, y_at(2748) - 96)]
        capR = [(x1 + 16, y_at(x1) - 14)]
        roll = closed(capL[::-1][:1] + upper + capR + lower[::-1] + capL[:2])
        over.append(it(roll, UNDER, INK, (2760, y_at(2760)), s, e, out=(nxt, nxt + 0.04) if nxt is not None else None))
    # two big eyes peek out of the dark under the lifted sheet
    eyes = [(2804, 1366), (2868, 1372)]
    for q, (x, y) in enumerate(eyes):
        on.append(it(blob(x, y, 30, 38, 210 + q, wob=0.05), '#FFFFFF', 11, (x, y + 30), 0.4 + 0.04 * q, 0.52 + 0.04 * q, grow='y'))
    for q, (x, y) in enumerate(eyes):
        on.append(it(circle(x - 4, y + 8, 15), '#111111', 0, (x - 4, y + 8), 0.56 + 0.03 * q, 0.64 + 0.03 * q))
        on.append(it(circle(x + 2, y + 1, 5), '#FFFFFF', 0, (x + 2, y + 1), 0.62 + 0.03 * q, 0.68 + 0.03 * q))
    # a wide grin under them, last
    gr = 'M2778 1414C2802 1446 2858 1448 2886 1410C2876 1466 2796 1468 2778 1414Z'
    on.append(it(gr, '#FFFFFF', 9, (2830, 1450), 0.86, 0.98, grow='x'))
    return {
        'note': 21,
        'label': 'The pale half of the horned blue ghost: hold A0 to play; it lifts its sheet a tug at a time and two '
                 'big eyes and a grin peek out from the dark underneath',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': on},
            {'effect': 'sprites', 'place': 'over', 'items': over},
        ],
        'crop': (2450, 800, 750, 900),
    }


# ---- note-32 G#1: the rocket grows a bunch of rocket salad ---------------------------------------------------------

def leaf(root, ang, L, W, seed):
    """An arugula leaf from root at angle ang (degrees, counter-clockwise from +x): a thin stalk, two or three
    rounded side lobes each side, a big round end lobe."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    dx, dy = math.cos(a), -math.sin(a)
    nx, ny = -dy, dx
    lobes_t = [(0.34 + 0.03 * rnd.random(), 0.5), (0.52 + 0.03 * rnd.random(), 0.62), (0.68, 0.72)]
    lobes_b = [(0.29 + 0.03 * rnd.random(), 0.45), (0.46 + 0.03 * rnd.random(), 0.6), (0.63, 0.7)]

    def half(u, lobes):
        w = 0.12 + 0.12 * u
        for c, amp in lobes:
            w = max(w, amp * math.exp(-((u - c) / 0.055) ** 2))
        q = max(0.0, 1 - ((u - 0.86) / 0.145) ** 2)
        w = max(w, 1.0 * math.sqrt(q))
        return w

    N = 48
    top, bot = [], []
    for i in range(N + 1):
        u = 0.02 + 0.985 * i / N
        wt = W * half(u, lobes_t) * (1 + 0.05 * math.sin(u * 23 + seed))
        wb = W * half(u, lobes_b) * (1 + 0.05 * math.sin(u * 19 + seed * 2))
        cx, cy = root[0] + dx * L * u, root[1] + dy * L * u
        top.append((cx + nx * wt, cy + ny * wt))
        bot.append((cx - nx * wb, cy - ny * wb))
    tip = (root[0] + dx * L * 1.005, root[1] + dy * L * 1.005)
    outline = 'M' + 'L'.join(p(*q) for q in top) + f'L{p(*tip)}L' + 'L'.join(p(*q) for q in bot[::-1]) + 'Z'
    rib = tube([(root[0] + dx * L * u, root[1] + dy * L * u) for u in (0.42, 0.6, 0.76, 0.92)], 7, 2)
    return outline, rib


def rocket_flower(cx, cy, r, seed):
    """A rocket (arugula) flower: four cream petals with violet veins, a green-gold eye."""
    rnd = random.Random(seed)
    petals, veins = '', ''
    for j in range(4):
        a = math.radians(45 + 90 * j + rnd.uniform(-8, 8))
        px, py = cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55
        petals += blob(px, py, r * 0.5, r * 0.36, seed * 10 + j, wob=0.06, rot=math.degrees(a))
        vx0, vy0 = cx + math.cos(a) * r * 0.25, cy + math.sin(a) * r * 0.25
        vx1, vy1 = cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85
        veins += tube([(vx0, vy0), (vx1, vy1)], 3.2, 1.2)
    return petals, veins, blob(cx, cy, r * 0.22, r * 0.22, seed + 5, wob=0.08)


def note32() -> dict:
    INK = 13
    root = (3582, 770)
    greens = ['#4FBF55', '#6DD24E', '#3FA95A', '#7FDB5A', '#55C46B', '#45B04E']
    plan = [  # angle, length, half-width, window
        (200, 380, 70, (0.0, 0.1)),
        (338, 380, 70, (0.14, 0.27)),
        (160, 410, 74, (0.28, 0.42)),
        (22, 400, 74, (0.42, 0.56)),
        (126, 400, 72, (0.56, 0.7)),
        (56, 400, 72, (0.68, 0.82)),
    ]
    items = []
    for j, (ang, L, W, (s, e)) in enumerate(plan):
        o, rib = leaf(root, ang, L, W, 30 + j)
        items.append(it(o, greens[j], INK, root, s, e))
        items.append(it(rib, '#D9F7A6', 0, root, s + 0.02, e + 0.02))
    flowers = [((3290, 610), 58, (0.82, 0.92)), ((3860, 600), 58, (0.86, 0.96)), ((3420, 470), 50, (0.9, 1.0))]
    over = []
    for j, ((x, y), r, (s, e)) in enumerate(flowers):
        pet, vein, eye = rocket_flower(x, y, r, 70 + j)
        over.append(it(pet, '#FFF4D6', 11, (x, y), s, e))
        over.append(it(vein, '#9B5BC8', 0, (x, y), s + 0.01, e))
        over.append(it(eye, '#C9D94A', 9, (x, y), s + 0.02, e))
    return {
        'note': 32,
        'label': 'The little mint rocket on the pyramid: hold G#1 to play; it turns out to be rocket salad, big lobed '
                 'arugula leaves unfurling from behind it one by one until cream rocket flowers pop open on top',
        'effects': [
            {'effect': 'sprites', 'place': 'around', 'front': [], 'items': items},
            {'effect': 'sprites', 'place': 'over', 'items': over},
        ],
        'crop': (3130, 330, 900, 900),
    }


# ---- note-39 D#2: the right horn becomes a shrimp -----------------------------------------------------------------

def note39() -> dict:
    INK = 12
    SAL, CORAL, DEEP = '#FFA782', '#FF8466', '#F2795A'
    on, around, over = [], [], []
    # segment plates across the horn, tip to root: crescents bowed toward the tail
    axis = [(3048, 905), (3042, 968), (3030, 1032), (3012, 1098)]
    for j, (x, y) in enumerate(axis):
        tilt = -14 + 4 * j
        a = math.radians(tilt)
        ux, uy = math.cos(a), math.sin(a)
        half = 80
        P0 = (x - ux * half, y - uy * half)
        P1 = (x + ux * half, y + uy * half)
        bow = 34
        d = (f'M{p(*P0)}C{p(P0[0] + ux * 40, P0[1] + uy * 40 - bow)} {p(P1[0] - ux * 40, P1[1] - uy * 40 - bow)} {p(*P1)}'
             f'L{p(P1[0], P1[1] + 18)}C{p(P1[0] - ux * 40, P1[1] - uy * 40 + 18 - bow)} {p(P0[0] + ux * 40, P0[1] + uy * 40 + 18 - bow)} {p(P0[0], P0[1] + 18)}Z')
        s = 0.13 + 0.075 * j
        on.append(it(d, DEEP, 8, (x, y), s, s + 0.09, grow='x'))
    # tail fan at the tip
    root = (3050, 878)
    fan1 = [(124, 104, 30, CORAL), (60, 116, 34, CORAL), (93, 132, 31, SAL)]
    for j, (ang, L, W, col) in enumerate(fan1):
        a = math.radians(ang)
        cx, cy = root[0] + math.cos(a) * L * 0.55, root[1] - math.sin(a) * L * 0.55
        around.append(it(blob(cx, cy, L * 0.55, W, 300 + j, wob=0.1, rot=-ang), col, INK, root, 0.0 + 0.02 * j, 0.09 + 0.02 * j,
                         out=(0.84, 0.88)))
    fan2 = [(156, 132, 34, CORAL), (30, 146, 36, CORAL), (124, 152, 38, SAL), (60, 160, 40, SAL), (94, 176, 34, '#FFB89A')]
    for j, (ang, L, W, col) in enumerate(fan2):
        a = math.radians(ang)
        cx, cy = root[0] + math.cos(a) * L * 0.55, root[1] - math.sin(a) * L * 0.55
        around.append(it(blob(cx, cy, L * 0.55, W, 320 + j, wob=0.1, rot=-ang), col, INK, root, 0.84 + 0.02 * j, 0.94 + 0.015 * j))
    # a beady eye on a stalk at its root, then two long antennae sweeping out right
    over.append(it(blob(3086, 1076, 30, 17, 77, wob=0.08, rot=-30), SAL, 10, (3060, 1090), 0.42, 0.5))
    over.append(it(circle(3114, 1056, 26), '#141414', 0, (3114, 1056), 0.46, 0.53))
    over.append(it(circle(3121, 1048, 7.5), '#FFFFFF', 0, (3121, 1048), 0.5, 0.56))
    ant1 = bez((3070, 1112), (3170, 1080), (3260, 980), (3330, 930), 24)
    ant2 = bez((3062, 1128), (3170, 1150), (3270, 1120), (3350, 1060), 24)
    over.append(it(lumpy_tube(ant1, 13, 4, 7, jit=0.05), CORAL, 9, ant1[0], 0.56, 0.72))
    over.append(it(lumpy_tube(ant2, 13, 4, 8, jit=0.05), CORAL, 9, ant2[0], 0.64, 0.8))
    return {
        'note': 39,
        'label': "The ghost's salmon right horn: hold D#2 to play; it turns into a shrimp: a tail fan flicks out at its tip, "
                 'shell plates crease along it, a beady eye pops out, long feelers sweep out, and its tail flips wide',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': on},
            {'effect': 'sprites', 'place': 'around', 'front': [], 'items': around},
            {'effect': 'sprites', 'place': 'over', 'items': over},
        ],
        'crop': (2780, 650, 720, 720),
    }


# ---- note-40 E2: the left horn is a carrot -------------------------------------------------------------------------

def note40() -> dict:
    INK = 12
    on, around = [], []
    # ridges across the carrot, root end to tip: short curved pale creases
    ridges = [(2702, 1060, 40), (2668, 998, 36), (2644, 936, 30), (2628, 878, 24)]
    for j, (x, y, L) in enumerate(ridges):
        a = math.atan2(-0.45, 0.9)  # across the horn
        ux, uy = math.cos(a), math.sin(a)
        P = bez((x - ux * L, y - uy * L), (x - ux * L * 0.3, y - uy * L * 0.3 + 10), (x + ux * L * 0.3, y + uy * L * 0.3 + 10),
                (x + ux * L, y + uy * L), 12)
        s = 0.12 + 0.2 * j
        on.append(it(tube(P, 5, 2), '#FFB07A', 6, (x, y), s, s + 0.08, grow='x'))
    root = (2748, 1100)
    STEM = '#3E9E4A'
    leaves = ['#5CC85A', '#7ED757', '#4DB85F', '#8BE05E', '#57C24F']
    fronds = [  # control points, window
        (((2748, 1098), (2750, 980), (2760, 860), (2770, 740)), (0.0, 0.1)),
        (((2746, 1100), (2734, 990), (2706, 870), (2672, 772)), (0.18, 0.3)),
        (((2756, 1090), (2810, 960), (2880, 860), (2918, 776)), (0.38, 0.5)),
        (((2744, 1100), (2716, 980), (2668, 860), (2616, 720)), (0.58, 0.7)),
        (((2752, 1096), (2790, 960), (2836, 820), (2852, 690)), (0.76, 0.88)),
    ]
    for j, (cp, (s, e)) in enumerate(fronds):
        P = bez(*cp, n=20)
        around.append(it(lumpy_tube(P, 13, 7, 40 + j), STEM, INK, root, s, e))
        for q, u in enumerate((0.5, 0.74, 1.0)):
            i = min(len(P) - 1, int(u * (len(P) - 1)))
            x, y = P[i]
            a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            side = -1 if q % 2 == 0 else 1
            off = 30 if u < 1 else 0
            nx, ny = -math.sin(math.radians(ang)) * off * side, math.cos(math.radians(ang)) * off * side
            r = 46 if u < 1 else 54
            ls, le = (s + 0.01 * q, e + 0.01 * q) if j == 0 else (s + 0.03 + 0.03 * q, e + 0.02 + 0.03 * q)
            around.append(it(blob(x + nx, y + ny, r, r * 0.66, 400 + 10 * j + q, wob=0.2, n=9, rot=ang + side * 35),
                             leaves[(j + q) % len(leaves)], INK, (x, y), ls, le))
    return {
        'note': 40,
        'label': "The ghost's red-orange left horn: hold E2 to play; it turns out to be a carrot, its ridges creasing in "
                 'as feathery green fronds shoot up from its root one after another into a bushy top',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': on},
            {'effect': 'sprites', 'place': 'around', 'front': ['f231', 'f232', 'f233'], 'items': around},
        ],
        'crop': (2400, 560, 760, 760),
    }


# ---- note-96 C7: the straw creature's eye winks -------------------------------------------------------------------

def note96() -> dict:
    TAN = '#FFD196'
    cx, cy = 4196.0, 577.0
    items = []
    # a pupil pops in, then looks up
    items.append(it(circle(4199, 591, 17), '#161616', 0, (4199, 591), 0.0, 0.07, out=(0.18, 0.22)))
    items.append(it(circle(4205, 584, 5.5), '#FFFFFF', 0, (4205, 584), 0.02, 0.08, out=(0.18, 0.22)))
    items.append(it(circle(4201, 555, 17), '#161616', 0, (4201, 555), 0.18, 0.27))
    items.append(it(circle(4207, 548, 5.5), '#FFFFFF', 0, (4207, 548), 0.2, 0.28))
    # a heavy lid drops halfway, sly
    half = (f'M{p(cx - 36, cy + 4)}C{p(cx - 38, cy - 70)} {p(cx + 38, cy - 70)} {p(cx + 36, cy + 4)}'
            f'C{p(cx + 20, cy + 16)} {p(cx - 20, cy + 16)} {p(cx - 36, cy + 4)}Z')
    items.append(it(half, TAN, 10, (cx, cy - 52), 0.42, 0.52, grow='y'))
    # then all the way: a wink
    full = blob(cx, cy + 2, 37, 52, 96, wob=0.04, n=10)
    items.append(it(full, TAN, 10, (cx, cy - 52), 0.6, 0.68, grow='y'))
    crease = (f'M{p(cx - 30, cy + 2)}C{p(cx - 14, cy + 26)} {p(cx + 14, cy + 26)} {p(cx + 30, cy + 2)}'
              f'C{p(cx + 14, cy + 14)} {p(cx - 14, cy + 14)} {p(cx - 30, cy + 2)}Z')
    items.append(it(crease, '#161616', 4, (cx, cy + 10), 0.64, 0.72, grow='x'))
    # three thick lashes flick out at the outer corner
    for j, (a, L) in enumerate([(28, 52), (2, 58), (-24, 50)]):
        r = math.radians(a)
        x0, y0 = cx + 26, cy + 6
        P = bez((x0, y0), (x0 + math.cos(r) * L * 0.4, y0 - math.sin(r) * L * 0.4 + 4),
                (x0 + math.cos(r) * L * 0.8, y0 - math.sin(r) * L * 0.8 - 2), (x0 + math.cos(r) * L, y0 - math.sin(r) * L - 8), 10)
        items.append(it(tube(P, 7, 2.5), '#161616', 4, (x0, y0), 0.72 + 0.03 * j, 0.8 + 0.03 * j))
    # a candy sparkle at the corner, and a little one
    items.append(it(star(4282, 488, 54, seed=3, rot=8), '#FFE34D', 9, (4282, 488), 0.84, 0.95))
    items.append(it(star(4128, 500, 28, seed=4, rot=-6), '#FF8CC6', 8, (4128, 500), 0.9, 1.0))
    return {
        'note': 96,
        'label': "The straw creature's olive eye: hold C7 to play; a pupil pops in and looks up, then a heavy lid drops "
                 'in a slow wink, lashes flick out and a candy sparkle twinkles',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (3990, 380, 420, 420),
    }


# ---- note-108 C8: the sleepy eye's sleep bubble swells and pops --------------------------------------------------

def note108() -> dict:
    root = (2226.0, 606.0)
    a = math.radians(62)
    dx, dy = math.cos(a), math.sin(a)
    radii = [30, 46, 60, 74, 88]
    wins = [(0.0, 0.08), (0.14, 0.22), (0.36, 0.46), (0.54, 0.62), (0.66, 0.74)]
    POP = (0.86, 0.89)
    items = []
    cs = []
    for j, (r, (s, e)) in enumerate(zip(radii, wins)):
        c = (root[0] + dx * r * 0.82, root[1] + dy * r * 0.82)
        cs.append(c)
        items.append(it(blob(c[0], c[1], r, r * 0.96, 500 + j, wob=0.035, n=12), '#FFB3CD', 9, root, s, e, out=POP))
    c, r = cs[-1], radii[-1]
    shine = (f'M{p(c[0] - r * 0.62, c[1] - r * 0.1)}C{p(c[0] - r * 0.62, c[1] - r * 0.55)} {p(c[0] - r * 0.25, c[1] - r * 0.72)} '
             f'{p(c[0] + r * 0.08, c[1] - r * 0.7)}C{p(c[0] - r * 0.22, c[1] - r * 0.5)} {p(c[0] - r * 0.45, c[1] - r * 0.35)} '
             f'{p(c[0] - r * 0.62, c[1] - r * 0.1)}Z')
    items.append(it(shine, '#FFFFFF', 0, (c[0] - r * 0.3, c[1] - r * 0.5), 0.72, 0.8, out=POP))
    # pop! a burst where it was, and droplets flung out
    items.append(it(star(c[0], c[1], 74, points=8, inner=0.5, seed=8, rot=10), '#FF8DB6', 9, c, 0.87, 0.93))
    items.append(it(star(c[0], c[1], 36, points=6, inner=0.5, seed=9, rot=-12), '#FFF2A8', 7, c, 0.89, 0.95))
    for j, (ang, dist, rr) in enumerate([(-30, 108, 12), (40, 112, 10), (120, 104, 11), (195, 100, 9)]):
        q = math.radians(ang)
        x, y = c[0] + math.cos(q) * dist, c[1] + math.sin(q) * dist
        items.append(it(blob(x, y, rr, rr, 520 + j, wob=0.1, n=7), '#FF8DB6', 7, (x, y), 0.9 + 0.015 * j, 0.96 + 0.01 * j))
    # the eye jolts wide open
    ex, ey = 2195.0, 612.0
    white = (f'M{p(ex - 46, ey + 2)}C{p(ex - 30, ey - 40)} {p(ex + 30, ey - 40)} {p(ex + 46, ey + 2)}'
             f'C{p(ex + 30, ey + 36)} {p(ex - 30, ey + 36)} {p(ex - 46, ey + 2)}Z')
    items.append(it(white, '#FFFFFF', 10, (ex, ey), 0.88, 0.95, grow='y'))
    items.append(it(circle(ex + 3, ey + 2, 10), '#161616', 0, (ex + 3, ey + 2), 0.92, 0.97))
    items.append(it(circle(ex + 6, ey - 2, 3.5), '#FFFFFF', 0, (ex + 6, ey - 2), 0.94, 0.99))
    lid = (f'M{p(ex - 50, ey - 8)}C{p(ex - 34, ey - 58)} {p(ex + 34, ey - 58)} {p(ex + 50, ey - 8)}'
           f'C{p(ex + 30, ey - 40)} {p(ex - 30, ey - 40)} {p(ex - 50, ey - 8)}Z')
    items.append(it(lid, '#F27FA0', 9, (ex, ey - 30), 0.9, 0.98, grow='y'))
    return {
        'note': 108,
        'label': 'The pink lid of the sleepy eye on the green cap: hold C8 to play; a sleep bubble swells out of its corner '
                 'with every breath, then pops, and the eye jolts wide open',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (2010, 430, 420, 420),
    }


DESIGNS = [note21(), note32(), note39(), note40(), note96(), note108()]

if __name__ == '__main__':
    k.run(DESIGNS)
