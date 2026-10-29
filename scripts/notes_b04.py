# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note batch b04: notes 54, 70, 79, 85, 94, 95 (picks made centrally, see docs/objects/note-<n>/choice.md).

    uv run scripts/notes_b04.py           # strips and end frames
    uv run scripts/notes_b04.py 70        # one note
    uv run scripts/notes_b04.py export    # build.json for each
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
m, g, p, tube, bez, spiral = k.m, k.g, k.p, k.tube, k.bez, k.spiral


# ---- drawing helpers ------------------------------------------------------------------------------------------------

def smooth(P) -> str:
    """A closed Catmull-Rom curve through the points P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sy=1.0) -> str:
    """A lumpy, hand-drawn round shape (squashed by sy)."""
    rnd = random.Random(seed)
    P = []
    for i in range(n):
        a = rot + i / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr, y + math.sin(a) * rr * sy))
    return smooth(P)


def leaf(x, y, ang, L, W, seed=0, wob=0.06, base=0.25) -> str:
    """A lumpy elongated petal/wing from (x, y) toward angle ang (degrees, screen up = +90), length L, width W."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    n = 7
    side1, side2 = [], []
    for i in range(1, n):
        u = i / n
        w = W / 2 * (math.sin(math.pi * u) ** 0.8 * (1 - base) + base * (1 - u)) * (1 + (rnd.random() - 0.5) * 2 * wob)
        cx, cy = x + ux * L * u, y + uy * L * u
        side1.append((cx + nx * w, cy + ny * w))
        side2.append((cx - nx * w, cy - ny * w))
    tip = (x + ux * L, y + uy * L)
    root1, root2 = (x + nx * W * base / 2, y + ny * W * base / 2), (x - nx * W * base / 2, y - ny * W * base / 2)
    return smooth([root1] + side1 + [tip] + side2[::-1] + [root2])


def star(x, y, R, seed=0, pts=5, inner=0.5, rot=-90.0) -> str:
    """A fat, rounded, slightly lopsided candy star."""
    rnd = random.Random(seed)
    P = []
    for i in range(pts * 2):
        a = math.radians(rot + i * 180 / pts) + (rnd.random() - 0.5) * 0.12
        r = R * (1 if i % 2 == 0 else inner) * (1 + (rnd.random() - 0.5) * 0.12)
        P.append((x + math.cos(a) * r, y + math.sin(a) * r))
    return smooth(P)


def band(P, i0, i1, w0, w1) -> str:
    """A filled band along the centreline P between indices i0 and i1, half-width w0..w1 (linear over all of P)."""
    n = len(P)
    L, R = [], []
    for i in range(i0, i1 + 1):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dd = math.hypot(dx, dy) or 1
        nx, ny = -dy / dd, dx / dd
        w = w0 + (w1 - w0) * i / (n - 1)
        L.append((P[i][0] + nx * w, P[i][1] + ny * w))
        R.append((P[i][0] - nx * w, P[i][1] - ny * w))
    return 'M' + 'L'.join(p(*q) for q in L + R[::-1]) + 'Z'


def strip(P, i0, i1, w0, w1, f0, f1) -> str:
    """A band on one side of a tube along P (half-width w0..w1): from f0 to f1 of the local half-width (negative is the
    left of the direction of travel), pointed at both ends."""
    n = len(P)
    A, Bs = [], []
    for i in range(i0, i1 + 1):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dd = math.hypot(dx, dy) or 1
        nx, ny = -dy / dd, dx / dd
        w = (w0 + (w1 - w0) * i / (n - 1)) * math.sin(math.pi * (i - i0) / max(1, i1 - i0)) ** 0.5
        A.append((P[i][0] + nx * w * f0, P[i][1] + ny * w * f0))
        Bs.append((P[i][0] + nx * w * f1, P[i][1] + ny * w * f1))
    return 'M' + 'L'.join(p(*q) for q in A + Bs[::-1]) + 'Z'


def resample(P, n):
    """P resampled to n+1 points evenly spaced along its length."""
    seg = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]
    tot = sum(seg)
    out, j, acc = [], 0, 0.0
    for i in range(n + 1):
        s = tot * i / n
        while j < len(seg) - 1 and acc + seg[j] < s:
            acc += seg[j]
            j += 1
        u = (s - acc) / (seg[j] or 1)
        out.append((P[j][0] + (P[j + 1][0] - P[j][0]) * u, P[j][1] + (P[j + 1][1] - P[j][1]) * u))
    return out


def it(d, fill, edge, at, s, e, grow='scale', out=None, sweep=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    if sweep:
        o['sweep'] = {'from': sweep[0], 'to': sweep[1]}
    return o


# ---- note-54 F#3: the mask's neck ring fans out into a ruff ---------------------------------------------------------

def ruff_tier(cx, cy, rxl, rxr, ryt, ryb, n, depth, seed):
    """A ruffled ring edge: n scallops round an egg-shaped outline that is narrower on the left (the painting's edge)."""
    rnd = random.Random(seed)
    P = []
    for i in range(2 * n):
        a = i / (2 * n) * 2 * math.pi + (rnd.random() - 0.5) * 0.08
        c, s = math.cos(a), math.sin(a)
        rx = rxr if c > 0 else rxl
        ry = ryb if s > 0 else ryt
        f = (1 if i % 2 == 0 else 1 - depth) * (1 + (rnd.random() - 0.5) * 0.08)
        P.append((cx + c * rx * f, cy + s * ry * f))
    return smooth(P)


def note54():
    cx, cy = 572, 1392
    at = (552, 1385)
    tiers = [  # outermost first so the inner ones lie on top; each arrives later the further out it is
        (180, 370, 330, 300, 8, 0.26, '#FF2EB8', 0.72, 0.92),
        (176, 280, 175, 228, 16, 0.10, '#7FF0C8', 0.5, 0.72),
        (172, 232, 148, 186, 15, 0.10, '#B99CFF', 0.28, 0.5),
        (164, 190, 122, 148, 14, 0.11, '#FF8AD8', 0.08, 0.3),
        (146, 150, 100, 110, 12, 0.13, '#FFE66B', 0.0, 0.06),
    ]
    items = []
    for i, (rxl, rxr, ryt, ryb, n, dep, col, s, e) in enumerate(tiers):
        items.append(it(ruff_tier(cx, cy, rxl, rxr, ryt, ryb, n, dep, 54 + i), col, 14 if i < 2 else 13, at, s, e))
        if i == 0:  # the frill's ribs: deep magenta wedges between its lobes, after it opens
            for j in range(8):
                a = j / 8 * 2 * math.pi
                c, sn = math.cos(a), math.sin(a)
                rx, ry = (370 if c > 0 else 180), (300 if sn > 0 else 330)
                x0, y0 = cx + c * rx * 0.72, cy + sn * ry * 0.72
                x1, y1 = cx + c * rx * 0.97, cy + sn * ry * 0.97
                L = math.hypot(x1 - x0, y1 - y0)
                ang = math.degrees(math.atan2(-(y1 - y0), x1 - x0))
                items.append(it(leaf(x0, y0, ang, L, 30, 540 + j, base=0.6), '#B80F86', 0, (x0, y0), 0.84 + j * 0.015, 0.95 + j * 0.005))
    return {
        'note': 54,
        'label': 'The pink ring round the horned mask\'s neck: hold F#3 to play; it fans out into a big ruff, tier '
                 'after tier, butter, pink, lilac and mint, and last a magenta frilled-lizard collar',
        'effects': [{'effect': 'sprites', 'place': 'around', 'front': ['f289', 'f290', 'f298', 'f299', 'f300'], 'items': items}],
        'crop': (330, 960, 800, 800),
        'again': ['f289', 'f290', 'f298', 'f299', 'f300'],
    }


# ---- note-70 A#4: the tube's yellow end blooms into a calla lily ---------------------------------------------------

def note70():
    O = (1107.0, 1267.0)
    u = (0.68, -0.73)   # the painted oval's long axis
    w = (0.73, 0.68)    # into the tube (down-right)
    A = (-0.22, -0.975)  # the way the lily opens: up, a little left
    B = (0.975, -0.22)
    S = 0.9
    P = lambda s, t: (O[0] + (s * A[0] + t * B[0]) * S, O[1] + (s * A[1] + t * B[1]) * S)
    # the funnel's foot runs along the oval's lower-right edge, so it sits on the tube's end
    foot = [(O[0] + 92 * math.cos(f) * u[0] + 46 * math.sin(f) * w[0], O[1] + 92 * math.cos(f) * u[1] + 46 * math.sin(f) * w[1])
            for f in [k_ * math.pi / 6 for k_ in range(7)]]
    spathe = smooth(foot[::-1] + [P(60, -64), P(112, -92), P(146, -142), P(196, -152), P(252, -122), P(292, -56),
                                       P(318, 14), P(350, 78), P(398, 124), P(352, 124), P(300, 116), P(258, 138),
                                       P(222, 146), P(168, 128), P(112, 84), P(60, 62)][::-1])
    C = (185, 0)
    rim = lambda rs, rt, ds=0.0: [P(C[0] + ds + rs * math.sin(f) + 0.28 * rt * math.cos(f), C[1] + rt * math.cos(f))
                                  for f in [i * math.pi / 10 for i in range(20)]]
    throat = smooth(rim(24, 128))
    blush = smooth(foot[::-1] + [P(40, -64), P(90, -60), P(104, 0), P(90, 60), P(40, 64)][::-1])
    # the near lip rolling back: a band hugging the opening's near (lower) rim
    near = lambda rs, rt, ds: [P(C[0] + ds - rs * math.sin(f) + 0.28 * rt * math.cos(f), C[1] + rt * math.cos(f))
                               for f in [i * math.pi / 12 for i in range(13)]]
    lip = smooth(near(50, 166, -8) + near(20, 126, 0)[::-1])
    sp = bez(P(150, 4), P(210, 0), P(262, -8), P(315, -24), 16)
    spadix = tube(sp, 22 * S, 16 * S)
    tx, ty = sp[-1]
    items = [
        it(spathe, '#FFF7FB', 14, O, 0.0, 0.22),
        it(blush, '#FFB3DE', 0, O, 0.14, 0.32),
        it(throat, '#D9EE7E', 12, P(*C), 0.22, 0.42),
        it(spadix, '#FFD94A', 12, sp[0], 0.48, 0.72),
        it(lip, '#FF9AD5', 12, P(C[0] - 40, C[1]), 0.34, 0.54),
    ]
    for i, (dx, dy, r, col) in enumerate([(-8, -34, 24, '#FFE66B'), (30, -8, 21, '#FFB347'), (-34, 6, 19, '#FFF3A0'), (10, 30, 16, '#FFB347')]):
        items.append(it(lump(tx + dx, ty + dy, r, 700 + i, 0.18, 7), col, 11, (tx, ty), 0.76 + i * 0.06, 0.9 + i * 0.03))
    return {
        'note': 70,
        'label': 'The yellow end of the pink tube by the lilac bell: hold A#4 to play; it blooms into a calla lily, '
                 'its pink lip rolls back, a yellow spadix rises and puffs of pollen pop off its tip',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (760, 820, 700, 700),
    }


# ---- note-79 G5: the pink spike becomes a dragonfly ------------------------------------------------------------------

def note79():
    tip = (1198.0, 1737.0)
    d = (0.915, -0.408)
    nu = (-0.408, -0.915)  # up-left of the bar
    T = (tip[0] - 72 * d[0], tip[1] - 72 * d[1])  # thorax
    bar_ang = math.degrees(math.atan2(0.408, 0.915))  # 24
    wings = [  # (angle, length, width, colour, start, end, sweep from)
        (62, 190, 76, 'rgba(120,235,255,0.62)', 0.1, 0.26, bar_ang),
        (88, 175, 70, 'rgba(255,140,225,0.6)', 0.26, 0.42, bar_ang),
        (118, 182, 74, 'rgba(190,160,255,0.62)', 0.4, 0.56, bar_ang + 180),
        (146, 165, 66, 'rgba(150,255,195,0.6)', 0.54, 0.68, bar_ang + 180),
    ]
    back = []
    for i, (ang, L, W, col, s, e, a0) in enumerate(wings):
        base = (T[0] + d[0] * (14 if ang < 90 else -14), T[1] + d[1] * (14 if ang < 90 else -14))
        back.append(it(leaf(base[0], base[1], ang, L, W, 790 + i, base=0.3), col, 10, base, s, e,
                       sweep=(round(a0, 1), round(ang + (16 if ang < 90 else -16), 1))))
    over = []
    # abdomen bands down the bar, root to thorax
    root = (948.0, 1852.0)
    for i, f in enumerate((0.2, 0.4, 0.6, 0.8)):
        cxb, cyb = root[0] + (T[0] - root[0]) * f, root[1] + (T[1] - root[1]) * f
        hw = 26 - 4 * f
        q = [(cxb + nu[0] * hw - d[0] * 7, cyb + nu[1] * hw - d[1] * 7), (cxb + nu[0] * hw + d[0] * 7, cyb + nu[1] * hw + d[1] * 7),
             (cxb - nu[0] * hw + d[0] * 7, cyb - nu[1] * hw + d[1] * 7), (cxb - nu[0] * hw - d[0] * 7, cyb - nu[1] * hw - d[1] * 7)]
        over.append(it(smooth(q), '#A8126F', 0, (cxb, cyb), 0.66 + i * 0.03, 0.76 + i * 0.03))
    # two big compound eyes on the tip, the lower one behind
    for j, (off, col) in enumerate(((-20, '#38D9F5'), (20, '#5CF2C0'))):
        ex, ey = tip[0] + nu[0] * off + d[0] * 4, tip[1] + nu[1] * off + d[1] * 4
        over.append(it(lump(ex, ey, 34, 7900 + j, 0.08, 8), col, 11, tip, 0.0, 0.06))
    for j, off in enumerate((-20, 20)):
        ex, ey = tip[0] + nu[0] * off + d[0] * 14, tip[1] + nu[1] * off + d[1] * 14
        over.append(it(lump(ex, ey, 13, 7910 + j, 0.1, 7), '#1a1a1a', 0, (ex, ey), 0.03, 0.12))
        over.append(it(lump(ex + 3, ey - 6, 5, 7920 + j, 0.1, 6), '#ffffff', 0, (ex, ey), 0.08, 0.16))
    # the wings buzz: motion crescents above them
    for j, (a0, a1, r) in enumerate(((56, 90, 205), (116, 148, 198))):
        over.append(it(g.crescent(T[0], T[1], r, a0, a1, 20), '#ffffff', 10, T, 0.84 + j * 0.06, 0.96 + j * 0.04))
    return {
        'note': 79,
        'label': 'The long pink spike on the blue ring creature: hold G5 to play; it becomes a dragonfly, two big '
                 'eyes pop on its tip, four see-through candy wings unfold one by one and buzz',
        'effects': [{'effect': 'sprites', 'place': 'around', 'items': back},
                    {'effect': 'sprites', 'place': 'over', 'items': over}],
        'crop': (820, 1420, 560, 560),
    }


# ---- note-85 C#6: the red curl is a party blower and unrolls ---------------------------------------------------------

def note85():
    root = (1206.0, 1893.0)
    RED, YEL = '#FF2E24', '#FFE14D'

    def pose(straight, r0, turns, n=60):
        a0 = math.radians(-8)
        end = (root[0] + math.cos(a0) * straight, root[1] + math.sin(a0) * straight)
        line = [(root[0] + (end[0] - root[0]) * i / 20, root[1] + (end[1] - root[1]) * i / 20) for i in range(21)]
        if turns > 0:
            curl = spiral(end[0], end[1], a0, r0, turns, 0.45, 1, 30)[1:]
            line += curl
        return resample(line, n)

    items = []
    poses = [  # (straight length, curl radius, curl turns, in, out)
        (95, 34, 1.0, 0.0, 0.04, (0.3, 0.31)),
        (170, 26, 0.75, 0.3, 0.31, (0.5, 0.51)),
        (250, 0, 0, 0.5, 0.51, None),
    ]
    for j, (L, r0, tu, s, e, out) in enumerate(poses):
        P = pose(L, r0, tu)
        items.append(it(tube(P, 18, 14), RED, 11, root, s, e, out=out))
        for q in range(4, 60, 10):
            items.append(it(band(P, q, min(59, q + 4), 13, 9.5), YEL, 0, root, s, e, out=out))
    # the mouthpiece
    mp = [(root[0] - 54, root[1] - 10), (root[0] - 50, root[1] - 26), (root[0] + 4, root[1] - 22), (root[0] + 8, root[1] + 12),
          (root[0] - 48, root[1] + 16), (root[0] - 56, root[1] + 4)]
    items.append(it(smooth(mp), '#FF8AD8', 11, root, 0.1, 0.2))
    items.append(it(lump(root[0] - 54, root[1] - 4, 13, 851, 0.1, 6, sy=1.3), '#FFF3F9', 10, root, 0.14, 0.22))
    # the feather tassel at the tip, then two toot puffs
    tx, ty = root[0] + math.cos(math.radians(-8)) * 250, root[1] + math.sin(math.radians(-8)) * 250
    for i, (ang, col) in enumerate(((40, '#FF8AD8'), (-2, '#7FE8FF'), (-42, '#FFE66B'))):
        items.append(it(leaf(tx - 6, ty, ang, 78, 34, 860 + i, base=0.3), col, 10, (tx, ty), 0.68 + i * 0.03, 0.8 + i * 0.03))
    for i, (dx, dy, r) in enumerate(((70, -52, 30), (92, 18, 34))):
        items.append(it(lump(tx + dx, ty + dy, r, 870 + i, 0.2, 8), '#FFFFFF', 10, (tx + 20, ty), 0.84 + i * 0.07, 0.94 + i * 0.06))
    return {
        'note': 85,
        'label': 'The little red curl on the blue ring creature: hold C#6 to play; it is a party blower: it unrolls '
                 'straight, candy-striped, gets a mouthpiece and a feather tassel, and toots',
        'effects': [{'effect': 'vanish', 'span': [0, 0.05]},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (1080, 1650, 560, 560),
    }


# ---- note-94 A#6: the sleepy eye opens starstruck ---------------------------------------------------------------------

def note94():
    cx, cy = 723.0, 1683.0
    lid = (723.0, 1692.0)
    items = [
        it(lump(cx, cy, 61, 941, 0.03, 10), '#FFFFF4', 13, lid, 0.0, 0.05, grow='y'),
        it(lump(cx + 2, cy - 4, 74, 942, 0.04, 10), '#FFFFF4', 13, (cx, cy), 0.14, 0.3),
        it(lump(cx + 6, cy - 2, 34, 943, 0.05, 8), '#FF4FC8', 11, (cx + 6, cy), 0.28, 0.42, out=(0.56, 0.64)),
        it(lump(cx + 8, cy - 2, 16, 944, 0.05, 7), '#1a1a1a', 0, (cx + 8, cy), 0.32, 0.44, out=(0.54, 0.62)),
        it(star(cx + 6, cy - 2, 50, 945), '#FFD12E', 12, (cx + 6, cy - 2), 0.5, 0.68),
        it(star(cx + 6, cy - 2, 24, 946, inner=0.55), '#FF4FC8', 0, (cx + 6, cy - 2), 0.58, 0.72),
        it(lump(cx + 30, cy - 34, 10, 947, 0.1, 6), '#ffffff', 0, (cx + 30, cy - 34), 0.66, 0.76),
    ]
    for i, (x, y, r, col) in enumerate(((618, 1600, 34, '#5CE1FF'), (830, 1612, 40, '#FF7AD0'), (845, 1752, 30, '#B4F04A'))):
        items.append(it(star(x, y, r, 950 + i), col, 10, (x, y), 0.76 + i * 0.06, 0.86 + i * 0.05))
    return {
        'note': 94,
        'label': 'The white of the green blob\'s sleepy eye: hold A#6 to play; the eye snaps open, swells, its pink '
                 'pupil turns into a fat yellow star and little candy stars pop round it',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (500, 1450, 460, 460),
    }


# ---- note-95 B6: the red sliver is a hot chili ------------------------------------------------------------------------

def note95():
    C = bez((434, 1924), (448, 1972), (560, 1924), (668, 1872), 24)
    cap = (672.0, 1868.0)
    items = [
        it(tube(bez((452, 1949), (500, 1937), (585, 1905), (668, 1872), 20), 15, 30), '#FF2E24', 11, (640, 1880), 0.0, 0.05),
        it(tube(C, 10, 44), '#F2121A', 13, (650, 1880), 0.12, 0.36),
        it(strip(C, 5, 20, 10, 44, -0.35, -0.75), '#FF9A8F', 0, (600, 1890), 0.42, 0.56),
        it(lump(cap[0] + 6, cap[1] - 2, 30, 951, 0.2, 7), '#4CC23A', 12, cap, 0.3, 0.46),
        it(tube(bez((cap[0] + 8, cap[1] - 20), (cap[0] + 18, cap[1] - 50), (cap[0] + 4, cap[1] - 74), (cap[0] - 22, cap[1] - 84), 12), 11, 8),
           '#3FA82E', 11, (cap[0] + 8, cap[1] - 20), 0.34, 0.5),
    ]
    for i, (x, y, r) in enumerate(((548, 1846, 30), (594, 1786, 38))):  # steam: three-lobed puffs, inner joins melted
        lobes = [(x - r * 0.55, y + r * 0.1, r * 0.6), (x + r * 0.35, y - r * 0.25, r * 0.7), (x + r * 0.15, y + r * 0.4, r * 0.55)]
        for j, (lx, ly, lr) in enumerate(lobes):
            items.append(it(lump(lx, ly, lr, 960 + 7 * i + j, 0.14, 7), '#FFFFFF', 10, (x, y + r), 0.56 + i * 0.1, 0.72 + i * 0.1))
        for j, (lx, ly, lr) in enumerate(lobes):
            items.append(it(lump(lx, ly, lr * 0.78, 960 + 7 * i + j, 0.14, 7), '#FFFFFF', 0, (x, y + r), 0.56 + i * 0.1, 0.72 + i * 0.1))
    fx, fy = 434.0, 1918.0
    ang = math.radians(112)  # the flame bursts up and a little left off the hooked tip
    ax, ay = math.cos(ang), -math.sin(ang)
    R = lambda q: (fx + 1.3 * (q[1] * ax - q[0] * ay), fy + 1.3 * (q[1] * ay + q[0] * ax))  # q = (across, along the flame)
    flame = smooth([R(q) for q in [(-18, 0), (-30, 30), (-22, 60), (-38, 94), (-12, 80), (-8, 122), (8, 88), (28, 106), (22, 64), (34, 34), (18, 0)]])
    core = smooth([R(q) for q in [(-10, 4), (-16, 30), (-6, 60), (4, 44), (12, 66), (14, 30), (10, 4)]])
    items.append(it(flame, '#FF8A1F', 11, (fx, fy), 0.82, 0.95))
    items.append(it(core, '#FFE14D', 0, (fx, fy), 0.88, 1.0))
    return {
        'note': 95,
        'label': 'The red sliver poking out of the gold ring: hold B6 to play; it plumps up into a fat glossy chili with '
                 'a green cap, steam puffs rise off it and a puff of flame bursts from its tip',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (330, 1660, 480, 480),
    }


DESIGNS = [note54(), note70(), note79(), note85(), note94(), note95()]

if __name__ == '__main__':
    k.run(DESIGNS)
