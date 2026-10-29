# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b13: notes 59, 66, 73, 92, 93 (the striped stack and the waving pink creature, lower left).

    uv run scripts/notes_b13.py            # strips and end frames
    uv run scripts/notes_b13.py 73         # one note
    uv run scripts/notes_b13.py export     # build.json for each

- note-59 B3 (f244): the almond lobe on the waving creature's chest is a pouch, and a joey climbs out and waves.
- note-66 F#4 (f013): the red drop under the striped stack turns into a strawberry and flowers.
- note-73 C#5 (f017): the pale wedge on the pink cap is an egg, and a chick hatches and chirps.
- note-92 G#6 (f008): the green creature's lip purses and whistles candy puffs.
- note-93 A6 (f018): the tiny pale triangle becomes a gold percussion triangle that is struck and rings.
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
m, g, p, tube, bez = k.m, k.g, k.p, k.tube, k.bez
smooth = m.smooth

INK_DARK = '#3A1F2E'


# ---- helpers -------------------------------------------------------------------------------------------------------

def rot(pts, ox, oy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(ox + (x - ox) * ca - (y - oy) * sa, oy + (x - ox) * sa + (y - oy) * ca) for x, y in pts]


def lump_pts(cx, cy, rx, ry, rot_deg=0.0, seed=0, amt=0.06, n=12):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        q = 1 + amt * (rnd.random() * 2 - 1)
        pts.append((cx + math.cos(t) * rx * q, cy + math.sin(t) * ry * q))
    return rot(pts, cx, cy, rot_deg) if rot_deg else pts


def lump(cx, cy, rx, ry, rot_deg=0.0, seed=0, amt=0.06, n=12) -> str:
    """A lumpy hand-drawn oval."""
    return smooth(lump_pts(cx, cy, rx, ry, rot_deg, seed, amt, n))


def shift(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def ltube(P, w0, w1, seed=0) -> str:
    """A lumpy tapered limb along P with round ends."""
    rnd = random.Random(seed)
    ph, n = rnd.random() * 6.28, len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + 0.06 * math.sin(u * 8 + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    (x0, y0), (x1, y1) = P[0], P[-1]
    a0 = math.atan2(P[1][1] - y0, P[1][0] - x0)
    a1 = math.atan2(y1 - P[-2][1], x1 - P[-2][0])
    cap_end = [(x1 + math.cos(a1) * w1 * 0.9, y1 + math.sin(a1) * w1 * 0.9)]
    cap_start = [(x0 - math.cos(a0) * w0 * 0.9, y0 - math.sin(a0) * w0 * 0.9)]
    pts = L + cap_end + R[::-1] + cap_start
    return smooth(pts[::2] if len(pts) > 44 else pts)


def leaf(bx, by, ang, ln, wd, seed=0) -> str:
    """A pointed leaf (or sepal) from its base at (bx, by) pointing at angle ang (degrees, screen)."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    j = lambda: 1 + 0.08 * (rnd.random() * 2 - 1)
    P = lambda s, t: (bx + ux * ln * s + nx * wd * t, by + uy * ln * s + ny * wd * t)
    return smooth([P(0, -0.35), P(0.3, -0.5 * j()), P(0.65, -0.38 * j()), P(1.0, 0), P(0.65, 0.38 * j()), P(0.3, 0.5 * j()),
                   P(0, 0.35)])


def item(d, fill, edge, at, start, end, out=None, grow='scale'):
    it = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 3),
          'end': round(end, 3), 'grow': grow}
    if out:
        it['outStart'], it['outEnd'] = round(out[0], 3), round(out[1], 3)
    return it


def crescent(cx, cy, r, a0, a1, w):
    return g.crescent(cx, cy, r, a0, a1, w)


def closed_eye(cx, cy, r, w):
    """A sleepy closed eye: a thin dark crescent sagging down (a filled shape, not a line)."""
    return crescent(cx, cy - r * 0.55, r, 200, 340, w)


def star(cx, cy, r, inner=0.38, pts=4, seed=0) -> str:
    rnd = random.Random(seed)
    P = []
    for i in range(pts * 2):
        a = math.pi / 2 + i * math.pi / pts
        rr = r * (1 if i % 2 == 0 else inner) * (1 + 0.06 * (rnd.random() * 2 - 1))
        P.append((cx + math.cos(a) * rr, cy - math.sin(a) * rr))
    return smooth(P)


# ---- note-59 B3: joey in the pouch ---------------------------------------------------------------------------------

def joey() -> list[dict]:
    E = 13
    FUR, EAR_IN, MUZZLE, LIP, HOLE = '#EFA66C', '#F78FB3', '#FCE6C6', '#EAA294', '#4A2340'
    pouch = (1545.0, 3712.0)
    it = []
    # 0-0.05: the pouch's mouth opens (the dark slit and its lip, the lip laid last so it stays in front)
    it.append(item(lump(1541, 3700, 46, 17, -8, 1, 0.05), HOLE, 10, (1541, 3700), 0.0, 0.05))
    # the ears poke up out of it (1 s)
    for cx, rd, sd in ((1508, -13, 2), (1584, 13, 3)):
        it.append(item(lump(cx, 3588, 29, 120, rd, sd, 0.05), FUR, E, pouch, 0.06, 0.24))
        it.append(item(lump(cx + (rd / 13) * 1.5, 3560, 13, 78, rd, sd + 10, 0.06), EAR_IN, 0, pouch, 0.1, 0.26))
    # the paw comes up later; its arm is drawn here so the head stays in front of its root
    hand = (1452.0, 3598.0)
    arm = bez((1518, 3712), (1495, 3675), (1470, 3640), hand, 14)
    it.append(item(ltube(arm, 19, 17, 5), FUR, E, (1518, 3712), 0.78, 0.9))
    it.append(item(lump(hand[0], hand[1] - 10, 33, 37, -20, 6, 0.09), FUR, E, (1518, 3712), 0.8, 0.92))
    it.append(item(lump(hand[0] - 2, hand[1] - 4, 14, 16, -20, 7), EAR_IN, 0, (1518, 3712), 0.84, 0.94))
    # 2 s: the head rises out of the pouch, eyes shut
    it.append(item(lump(1546, 3632, 74, 63, 0, 4, 0.05, 14), FUR, E, pouch, 0.26, 0.46))
    it.append(item(lump(1546, 3657, 38, 26, 0, 8, 0.05), MUZZLE, 9, pouch, 0.3, 0.48))
    it.append(item(lump(1546, 3644, 13, 9, 0, 9, 0.05), INK_DARK, 6, pouch, 0.32, 0.48))
    lids = [(1516, 3610), (1576, 3610)]
    for x, y in lids:
        it.append(item(closed_eye(x, y, 15, 9), '#000', 0, pouch, 0.3, 0.46, out=(0.5, 0.55)))
    # 2.5 s: the eyes open
    for j, (x, y) in enumerate(lids):
        tilt = 10 if j == 0 else -10
        it.append(item(lump(x, y - 3, 19, 14, tilt, 20 + j, 0.05, 10), '#ffffff', 9, (x, y), 0.5, 0.6))
        it.append(item(lump(x + 1, y - 3, 9, 10, 0, 30 + j, 0.04), '#A000FF', 0, (x, y), 0.53, 0.62))
        it.append(item(lump(x + 1, y - 3, 4.5, 5, 0, 35 + j, 0.04), '#000', 0, (x, y), 0.54, 0.62))
        it.append(item(lump(x + 4, y - 7, 2.6, 2.6, 0, 40 + j, 0.02), '#ffffff', 0, (x, y), 0.56, 0.64))
    # 3 s: a smile and pink cheeks
    it.append(item(crescent(1546, 3652, 18, 205, 335, 13), '#7A2140', 6, (1546, 3666), 0.64, 0.74))
    for x in (1497, 1595):
        it.append(item(lump(x, 3647, 15, 9, 0, int(x), 0.06), '#FF9FBF', 0, (x, 3647), 0.66, 0.76))
    # 3.2-4 s: the paw waves, motion crescents last
    for j, (r, a0, a1) in enumerate(((70, 100, 172), (102, 108, 164))):
        it.append(item(crescent(hand[0], hand[1] - 8, r, a0, a1, 18), '#ffffff', 9, hand, 0.88 + 0.04 * j, 0.96 + 0.04 * j))
    # the pouch's front lip, in front of the ears', head's and arm's roots
    lip = smooth([(1492, 3696), (1520, 3712), (1546, 3716), (1572, 3710), (1592, 3698), (1590, 3716), (1570, 3734),
                  (1543, 3743), (1514, 3736), (1495, 3718)])
    it.append(item(lip, LIP, 12, (1541, 3718), 0.0, 0.05))
    return it


# ---- note-66 F#4: strawberry ---------------------------------------------------------------------------------------

def strawberry() -> list[dict]:
    E = 13
    RED, SEED, GREEN, PETAL, MID = '#F2384F', '#FFE45C', '#45C24A', '#FFFFFF', '#FFD23F'
    c = (1410.0, 4430.0)
    body = [(1282, 4448), (1318, 4424), (1370, 4400), (1424, 4371), (1468, 4340), (1506, 4310), (1522, 4342), (1517, 4394),
            (1497, 4444), (1465, 4486), (1430, 4512), (1394, 4506), (1350, 4489), (1308, 4472)]
    rnd = random.Random(66)
    body = [(x + rnd.uniform(-3, 3), y + rnd.uniform(-3, 3)) for x, y in body]
    it = [item(smooth(body), RED, E, c, 0.0, 0.045)]

    def seed(x, y, s, e, j):
        return item(lump(x, y, 8, 12, -30, 100 + j, 0.08, 8), SEED, 6, (x, y), s, e)

    first = [(1388, 4432), (1458, 4416), (1418, 4478)]
    second = [(1335, 4452), (1437, 4398), (1484, 4370), (1465, 4458)]
    third = [(1362, 4478), (1410, 4452), (1490, 4412), (1392, 4495), (1445, 4490)]
    it += [seed(x, y, 0.0, 0.05, j) for j, (x, y) in enumerate(first)]
    it += [seed(x, y, 0.08 + 0.03 * j, 0.2 + 0.03 * j, 10 + j) for j, (x, y) in enumerate(second)]
    # 1-2 s: the leafy crown fans out along its top edge, sepal by sepal
    cx, cy = 1408.0, 4384.0
    for j, (ang, ln) in enumerate(((-175, 88), (-140, 96), (-110, 92), (-78, 84), (-38, 80))):
        it.append(item(leaf(cx, cy, ang, ln, 34, 200 + j), GREEN, 11, (cx, cy), 0.22 + 0.05 * j, 0.34 + 0.05 * j))
    it.append(item(lump(cx, cy - 6, 22, 16, -30, 210, 0.06), GREEN, 0, (cx, cy), 0.3, 0.4))
    # 2-3 s: it ripens: more seeds and a shine
    it += [seed(x, y, 0.5 + 0.03 * j, 0.62 + 0.03 * j, 20 + j) for j, (x, y) in enumerate(third)]
    # 3-4 s: a stalk curls up to the right and a white strawberry blossom opens on it
    bx, by = 1572.0, 4268.0
    stalk = bez((1452, 4364), (1480, 4300), (1530, 4268), (bx - 30, by + 6), 16)
    it.append(item(ltube(stalk, 10, 9, 230), GREEN, 10, (1452, 4364), 0.62, 0.72))
    it.append(item(leaf(1500, 4292, -150, 70, 34, 231), GREEN, 10, (1500, 4292), 0.68, 0.78))
    for j in range(5):
        a = math.radians(90 + j * 72 + 8)
        px, py = bx + math.cos(a) * 34, by - math.sin(a) * 34
        it.append(item(lump(px, py, 31, 25, -math.degrees(a), 240 + j, 0.07), PETAL, 10, (bx, by), 0.74 + 0.04 * j, 0.84 + 0.04 * j))
    it.append(item(lump(bx, by, 21, 20, 0, 250, 0.08), MID, 9, (bx, by), 0.92, 1.0))
    return it


# ---- note-73 C#5: hatching chick -----------------------------------------------------------------------------------

def egg_outline(cx, cy, rx, ry, n=48):
    return [(cx + rx * math.sin(t) * (1 - 0.16 * math.cos(t)), cy - ry * math.cos(t)) for t in (i / n * 2 * math.pi for i in range(n))]


def chick() -> list[dict]:
    E = 12
    SHELL, YEL, BEAK, MOUTH = '#FFF5D2', '#FFD93B', '#FF8A1F', '#FF6FA0'
    ex, ey, rx, ry = 1392.0, 3918.0, 74.0, 95.0
    rnd = random.Random(73)
    out = [(x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.5, 1.5)) for x, y in egg_outline(ex, ey, rx, ry)]
    zy = 3880.0
    # half-width of the egg at the crack's height
    hw = max(abs(x - ex) for x, y in out if abs(y - zy) < 9)
    zig = []
    teeth = 7
    for i in range(teeth + 1):
        u = i / teeth
        zig.append((ex - hw + 2 * hw * u, zy + (13 if i % 2 else -13) * (0 < i < teeth)))
    lower = [q for q in out if q[1] > zy + 1]  # right side, round the bottom, up the left side
    lower_d = 'M' + 'L'.join(p(*q) for q in zig + lower) + 'Z'
    up = [i for i, q in enumerate(out) if q[1] < zy - 1]
    a = max(i for i in up if i < len(out) // 2)
    b = min(i for i in up if i > len(out) // 2)
    cap_pts = out[b:] + out[:a + 1] + zig[::-1]  # left side over the top to the right side, then back along the crack
    capc = (ex, 3852.0)
    hx, hy, hr = 1392.0, 3842.0, 62.0
    it = []
    # 1-2 s: the chick's head pushes up inside the shell, eyes shut, beak shut
    grow_at = (ex, 3905.0)
    it.append(item(lump(hx, hy, hr, hr * 0.95, 0, 73, 0.06, 14), YEL, E, grow_at, 0.2, 0.4))
    for j, (x, y, r) in enumerate(((1372, 3782, 15), (1392, 3776, 17), (1411, 3783, 14))):
        it.append(item(lump(x, y, r * 0.8, r, (j - 1) * 25, 80 + j, 0.1), YEL, 9, grow_at, 0.24, 0.42))
    it.append(item(lump(hx, hy - 30, 46, 22, 0, 85, 0.04), YEL, 0, grow_at, 0.24, 0.42))
    eyes = [(1366, 3834), (1418, 3834)]
    for x, y in eyes:
        it.append(item(closed_eye(x, y, 12, 7), '#000', 0, grow_at, 0.26, 0.42, out=(0.5, 0.55)))
    it.append(item(lump(hx, 3862, 16, 11, 0, 86, 0.06), BEAK, 9, grow_at, 0.26, 0.42, out=(0.78, 0.83)))
    # 2.5 s: the eyes open
    for j, (x, y) in enumerate(eyes):
        it.append(item(lump(x, y - 3, 14, 16, 0, 88 + j, 0.05, 10), '#ffffff', 8, (x, y), 0.5, 0.6))
        it.append(item(lump(x + 1, y - 2, 8, 10, 0, 90 + j, 0.05), '#000', 0, (x, y), 0.52, 0.61))
        it.append(item(lump(x + 4, y - 6, 3, 3, 0, 92 + j, 0.02), '#ffffff', 0, (x, y), 0.54, 0.62))
    # the egg: lower shell in front of the head; the top of the shell pops off and lands on its head as a hat
    it.append(item(lower_d, SHELL, E, (ex, ey + 40), 0.0, 0.045))
    it.append(item(smooth_poly(cap_pts), SHELL, E, capc, 0.0, 0.045, out=(0.12, 0.2)))
    lifted = shift(rot(cap_pts, *capc, -22), -10, -46)
    it.append(item(smooth_poly(lifted), SHELL, E, (capc[0] - 10, capc[1] - 46), 0.1, 0.2, out=(0.4, 0.48)))
    on_head = shift(rot(cap_pts, *capc, 12), 4, -94)
    it.append(item(smooth_poly(on_head), SHELL, E, (capc[0] + 4, capc[1] - 94), 0.4, 0.5))
    # 3 s: stubby wings pop out over the shell's rim
    for j, (x, y, r) in enumerate(((1322, 3902, -35), (1462, 3902, 35))):
        it.append(item(lump(x, y, 31, 18, r, 95 + j, 0.08), YEL, 10, (ex, 3905), 0.6 + 0.05 * j, 0.72 + 0.05 * j))
    # 4 s: its beak opens wide and it chirps
    it.append(item(lump(hx, 3872, 17, 14, 0, 97, 0.05), MOUTH, 8, (hx, 3866), 0.8, 0.9))
    it.append(item(lump(hx, 3855, 20, 10, 0, 98, 0.06), BEAK, 9, (hx, 3866), 0.8, 0.9))
    it.append(item(lump(hx, 3888, 16, 8, 0, 99, 0.06), BEAK, 9, (hx, 3866), 0.82, 0.92))
    for j, (r, a0, a1) in enumerate(((95, 125, 165), (128, 130, 160))):
        it.append(item(crescent(hx, 3860, r, a0, a1, 18), '#ffffff', 9, (hx, 3860), 0.88 + 0.05 * j, 0.95 + 0.05 * j))
    return it


def smooth_poly(pts) -> str:
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def puff(cx, cy, r, seed) -> str:
    """A little scalloped cloud puff."""
    rnd = random.Random(seed)
    ph = rnd.random() * 6.28
    P = []
    for i in range(30):
        t = i / 30 * 2 * math.pi
        rr = r * (0.88 + 0.13 * abs(math.sin(3.5 * t + ph))) * (1 + 0.03 * (rnd.random() * 2 - 1))
        P.append((cx + math.cos(t) * rr, cy + math.sin(t) * rr * 0.9))
    return smooth(P)


# ---- note-92 G#6: whistle ------------------------------------------------------------------------------------------

def whistle() -> list[dict]:
    E = 11
    LIPC, HOLE, CHEEK = '#F64C76', '#4A1030', '#AEEB9B'
    mx, my = 850.0, 4392.0
    it = []
    # 3 s: a cheek puffs out under the mouth (drawn first, so the lips stay in front)
    it.append(item(lump(925, 4418, 54, 44, 0, 920, 0.06), CHEEK, E, (905, 4400), 0.7, 0.84))
    # 0-0.05: the lips purse into a round O
    it.append(item(lump(mx, my, 58, 46, -8, 921, 0.07), LIPC, E, (mx, my), 0.0, 0.045))
    it.append(item(lump(mx - 5, my, 23, 18, -8, 922, 0.06), HOLE, 8, (mx, my), 0.0, 0.05))
    it.append(item(lump(mx + 20, my - 25, 13, 6, -15, 923, 0.05), '#FFB3C9', 0, (mx, my), 0.02, 0.06))
    # 1-4 s: candy puffs pop out one a second, each bigger and further up and to the left
    puffs = [((748, 4350), 36, '#FFE45C', 0.1, 0.24), ((664, 4286), 46, '#7FF3F3', 0.34, 0.48),
             ((568, 4212), 56, '#FF8AD8', 0.58, 0.72), ((456, 4126), 70, '#C59CFF', 0.84, 0.98)]
    for j, ((x, y), r, col, s, e) in enumerate(puffs):
        it.append(item(puff(x, y, r, 930 + j), col, 10, (x + r * 0.6, y + r * 0.5), s, e))
        it.append(item(lump(x - r * 0.35, y - r * 0.38, r * 0.28, r * 0.16, -30, 940 + j, 0.05), '#ffffff', 0, (x, y), s + 0.04, e))
    return it


# ---- note-93 A6: the triangle --------------------------------------------------------------------------------------

def rounded_line(corners, r=16, n=6):
    """A centreline through the corners, each inner corner rounded by a little quadratic arc."""
    P = [corners[0]]
    for i in range(1, len(corners) - 1):
        a, b, c = corners[i - 1], corners[i], corners[i + 1]
        da, dc = math.hypot(b[0] - a[0], b[1] - a[1]), math.hypot(c[0] - b[0], c[1] - b[1])
        p0 = (b[0] + (a[0] - b[0]) * r / da, b[1] + (a[1] - b[1]) * r / da)
        p2 = (b[0] + (c[0] - b[0]) * r / dc, b[1] + (c[1] - b[1]) * r / dc)
        for j in range(n + 1):
            u = j / n
            P.append(((1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * b[0] + u * u * p2[0],
                      (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * b[1] + u * u * p2[1]))
    P.append(corners[-1])
    dense = []
    for a, b in zip(P, P[1:]):
        steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 14))
        dense += [(a[0] + (b[0] - a[0]) * s / steps, a[1] + (b[1] - a[1]) * s / steps) for s in range(steps)]
    return dense + [P[-1]]


def beater(tip, handle, s, e, out=None):
    rod = bez(handle, (handle[0] * 0.7 + tip[0] * 0.3, handle[1] * 0.7 + tip[1] * 0.3 - 4),
              (handle[0] * 0.3 + tip[0] * 0.7, handle[1] * 0.3 + tip[1] * 0.7 - 4), tip, 12)
    return [item(tube(rod, 8, 7), '#EEF0F6', 8, handle, s, e, out),
            item(lump(tip[0], tip[1], 14, 14, 0, int(tip[0]), 0.06), '#FF5FA2', 8, handle, s, e, out)]


def triangle() -> list[dict]:
    GOLD = '#FFD84D'
    apex, br, bl = (1590.0, 4042.0), (1692.0, 4208.0), (1494.0, 4208.0)
    centre = (1592.0, 4150.0)
    # the bar starts just right of the bottom-left corner, runs round the right side and over the apex, and stops short
    # of the bottom-left corner (the open corner a real triangle has)
    line = rounded_line([(bl[0] + 24, bl[1]), br, apex, (bl[0] + 9, bl[1] - 22)], r=20)
    inner = smooth([(apex[0], apex[1] + 30), (br[0] - 30, br[1] - 13), (bl[0] + 28, bl[1] - 13)])
    it = [item(inner, '#F1E7B8', 0, centre, 0.0, 0.045), item(ltube(line, 13, 13, 931), GOLD, 10, centre, 0.0, 0.045)]
    it.append(item(ltube(rounded_line([(1598, 4072), (1628, 4122)]), 3.5, 3, 932), '#FFF6C0', 0, centre, 0.02, 0.06))
    # the beater strikes the right side, twice
    hit = (1658.0, 4132.0)
    handle = (1790.0, 4262.0)
    up = (1712.0, 4072.0)
    it += beater(up, (1800.0, 4214.0), 0.06, 0.14, out=(0.16, 0.2))
    it += beater(hit, handle, 0.16, 0.22, out=(0.42, 0.46))
    it += beater(up, (1800.0, 4214.0), 0.43, 0.49, out=(0.64, 0.68))
    it += beater(hit, handle, 0.65, 0.71)
    # rings go out from where it is struck, one a second, the last two after the second strike
    for j, (r, s, e) in enumerate(((56, 0.2, 0.32), (86, 0.28, 0.44), (116, 0.7, 0.82), (146, 0.78, 0.92))):
        it.append(item(crescent(hit[0], hit[1], r, 14, 76, 15 + 2 * j), '#ffffff', 9, hit, s, e))
    # 4 s: a star glint pops at its top corner
    it.append(item(star(apex[0] + 2, apex[1] - 6, 42, 0.36, 4, 933), '#ffffff', 8, apex, 0.88, 1.0))
    return it


DESIGNS = [
    {'note': 59, 'label': 'The almond lobe on the waving pink creature\'s chest: hold B3 to play; it opens as a pouch and '
                          'a joey climbs out ears first, wakes, smiles and waves',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': joey()}], 'crop': (1250, 3400, 600, 600)},
    {'note': 66, 'label': 'The red drop under the striped stack: hold F#4 to play; it ripens into a strawberry, seeds, '
                          'leafy crown and all, and a white blossom opens on its stalk',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': strawberry()}], 'crop': (1170, 4060, 520, 520)},
    {'note': 73, 'label': 'The pale wedge on top of the pink cap: hold C#5 to play; it is an egg that cracks, and a chick '
                          'hatches with the shell on its head and chirps',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': chick()}], 'crop': (1150, 3600, 500, 500)},
    {'note': 92, 'label': 'The green creature\'s pink lip: hold G#6 to play; it purses into an O and whistles candy puffs, '
                          'one a second, cheek puffed out',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': whistle()}], 'crop': (360, 3990, 620, 620)},
    {'note': 93, 'label': 'The tiny pale triangle at the pink cap\'s tip: hold A6 to play; it becomes a gold triangle '
                          'that is struck and rings out',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': triangle()}], 'crop': (1430, 3930, 440, 440)},
]

if __name__ == '__main__':
    k.run(DESIGNS)
