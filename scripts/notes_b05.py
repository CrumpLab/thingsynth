# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b05 of the note animations: notes 29, 38, 42, 53, 58, 91.

    uv run scripts/notes_b05.py            # strips and end frames for all six
    uv run scripts/notes_b05.py 42         # just note-42
    uv run scripts/notes_b05.py export     # docs/objects/note-<n>/build.json

Four of the six sit round the cream snout creature's straw, so each is kept to its own patch: the flamingo on the
straw itself (body on the arch, head at the water end), the paper lantern in the nook under the arch, the genie
between the snout's chin and the straw's down-leg, the pea pod between the down-leg and the yellow spike; the
daffodil opens at that spike's tip above, the party hat on the orange sprite's head to the right.
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks)
ks.loader.exec_module(k)
p, bez = k.p, k.bez


# ---- drawing helpers ------------------------------------------------------------------------------------------------

def smooth(P) -> str:
    """A closed Catmull-Rom curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.06, n=14) -> str:
    """A lumpy hand-drawn ellipse, rotated by rot degrees."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        f = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * f, math.sin(t) * ry * f
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def scallop(cx, cy, r, n, depth, seed=0, rot=0.0) -> str:
    """A scalloped puff: n round bumps on a circle."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n * 2):
        a = math.radians(rot) + i / (n * 2) * 2 * math.pi
        rr = r * (1 + (depth if i % 2 == 0 else -depth * 0.4) * (0.8 + 0.4 * rnd.random()))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return smooth(pts)


def spline(P, n=24):
    """Points along an open Catmull-Rom spline through P."""
    out = []
    m = len(P)
    for i in range(m - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(m - 1, i + 2)]
        for j in range(n):
            u = j / n
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * u + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * u * u
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * u ** 3) for c in (0, 1)))
    out.append(P[-1])
    return out


def ltube(P, w0, w1, seed=0, wob=0.06) -> str:
    """A lumpy tapered limb along the centreline P, closed with rounded ends."""
    rnd = random.Random(seed)
    ph, n = rnd.random() * 6.28, len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + wob * math.sin(u * 9 + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    step = max(1, n // 12)
    pts = L[::step] + [L[-1]] + R[::-1][::step] + [R[0]]
    return smooth(pts)


def petal(cx, cy, length, width, ang, seed=0, base=0.0) -> str:
    """A lumpy pointed petal from (cx, cy) out along ang degrees."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    prof = [(base, 0.0), (0.18, 0.75), (0.45, 1.0), (0.72, 0.85), (0.92, 0.42), (1.0, 0.0)]
    pts = []
    for s in (1, -1):
        seq = prof if s == 1 else prof[::-1]
        for t, w in seq:
            if (s == -1 and t in (base, 1.0)):
                continue
            ww = w * width / 2 * (1 + 0.08 * (rnd.random() * 2 - 1)) * s
            L = t * length * (1 + 0.03 * (rnd.random() * 2 - 1))
            pts.append((cx + ux * L + vx * ww, cy + uy * L + vy * ww))
    return smooth(pts)


def lens(x0, y0, x1, y1, w) -> str:
    """A lens (pointed both ends) from (x0, y0) to (x1, y1), w wide in the middle."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    nx, ny = -dy / d * w / 2 * 1.33, dx / d * w / 2 * 1.33
    return (f'M{p(x0, y0)}C{p(mx - dx * 0.3 + nx, my - dy * 0.3 + ny)} {p(mx + dx * 0.3 + nx, my + dy * 0.3 + ny)} {p(x1, y1)}'
            f'C{p(mx + dx * 0.3 - nx, my + dy * 0.3 - ny)} {p(mx - dx * 0.3 - nx, my - dy * 0.3 - ny)} {p(x0, y0)}Z')


def it(d, fill, edge, at, start, end, grow='scale', out=None, sweep=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 3),
         'end': round(end, 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(out[1], 3)
    if sweep:
        o['sweep'] = {'from': sweep[0], 'to': sweep[1]}
    return o


def seamless(shapes, fill, ink) -> list[dict]:
    """Outlined layer (double-width stroke) under a fill-only layer, so overlapping parts merge without seams.
    shapes: list of (d, at, start, end)."""
    outl = [it(d, fill, ink * 2, at, s, e) for d, at, s, e in shapes]
    fills = [it(d, fill, 0, at, s, e) for d, at, s, e in shapes]
    return outl + fills


def eye(cx, cy, r, iris, ink, start, lid=None, lid_out=None) -> list[dict]:
    """A round eye (white, iris, pupil, glint); with lid, a sleepy lid of that colour sits over its top half and
    shrinks away over lid_out."""
    at = (cx, cy)
    out = [it(lump(cx, cy, r, r * 1.05, 0, int(cx), 0.05, 10), '#ffffff', ink, at, start, start + 0.08),
           it(lump(cx + r * 0.12, cy + r * 0.1, r * 0.55, r * 0.6, 0, int(cy), 0.05, 10), iris, ink * 0.7, at, start + 0.02, start + 0.1),
           it(k.circle(cx + r * 0.14, cy + r * 0.14, r * 0.27), '#111111', 0, at, start + 0.03, start + 0.1),
           it(k.circle(cx + r * 0.32, cy - r * 0.08, r * 0.12), '#ffffff', 0, at, start + 0.05, start + 0.11)]
    if lid:
        d = (f'M{p(cx - r * 1.12, cy + r * 0.12)}C{p(cx - r * 1.1, cy - r * 1.45)} {p(cx + r * 1.1, cy - r * 1.45)} '
             f'{p(cx + r * 1.12, cy + r * 0.12)}C{p(cx + r * 0.4, cy - r * 0.05)} {p(cx - r * 0.4, cy - r * 0.05)} {p(cx - r * 1.12, cy + r * 0.12)}Z')
        out.append(it(d, lid, ink, (cx, cy - r), start, start + 0.08, out=lid_out))
    return out


# ---- note-29 F1: the straw becomes a flamingo ------------------------------------------------------------------------
# The straw (f249) runs from the snout's nostril over an arch and down to the waterfall. Its down-leg is the neck,
# drinking; pink climbs it band by band from the water end (drawn on the straw, under its own ink); the head lifts
# at the water end with a black-tipped beak, its eye wakes; the body puffs up on the arch top with tail plumes, and
# a big wing fluffs open upward, black flight feathers last.

def flamingo() -> dict:
    INK = 14
    PINK, DEEP, BEAK, BLACK = '#FF8FC0', '#FF4F9C', '#FFE6D2', '#232323'
    C = [(1866, 2130), (1871, 2084), (1835, 1924), (1808, 1764), (1780, 1604), (1752, 1484), (1723, 1404), (1700, 1350),
         (1640, 1306), (1560, 1298), (1482, 1322), (1410, 1364), (1360, 1404), (1312, 1444), (1262, 1488), (1235, 1515)]
    cuts = [(0, 4, 0.0, 0.05), (3, 6, 0.05, 0.18), (5, 9, 0.15, 0.3), (8, 12, 0.26, 0.38), (11, 16, 0.34, 0.46)]
    bands = []
    for a, b, s, e in cuts:
        P = spline(C[a:b], 10)
        bands.append(it(ltube(P, 75, 75, a, 0.0), PINK, 0, P[0], s, e))
    # head at the water end: a short neck curl out of the straw's end, the head lifted to the right
    # head and beak drawn 1.8x about the straw's end and lifted 60 px, so the head is the clear focus by 1 s
    F, AX, AY, UP = 1.8, 1866, 2080, -60
    S = lambda x, y: (AX + F * (x - AX), AY + F * (y - AY) + UP)
    neck = spline([(1862, 2040), S(1874, 2128), S(1912, 2138), S(1950, 2100)], 10)
    head_c = S(1968, 2042)
    head = lump(head_c[0], head_c[1], 80 * F, 68 * F, -10, 29, 0.06, 16)
    beakP = bez(S(2025, 2022), S(2098, 2008), S(2130, 2052), S(2114, 2152), 16)
    beak = ltube(beakP, 36 * F, 11 * F, 3, 0.03)
    tipP = beakP[9:]
    tip = ltube(tipP, 21 * F, 9 * F, 4, 0.02)
    head_items = seamless([(ltube(neck, 16, 60, 5), (1862, 2040), 0.02, 0.16), (head, S(1900, 2100), 0.03, 0.2)], PINK, INK)
    beak_items = [it(beak, BEAK, INK, beakP[0], 0.0, 0.05), it(tip, BLACK, INK, beakP[0], 0.0, 0.05)]
    face = eye(*S(1978, 2018), 23 * F, '#FFD21F', INK, 0.44, lid=PINK, lid_out=(0.6, 0.72))
    # body on the arch top, tail plumes to its left, then the wing fluffing open upward
    body_c = (1560, 1240)
    body = lump(body_c[0], body_c[1], 158, 92, -6, 7, 0.07, 16)
    tail = [petal(1440, 1250, 120, 52, 200, 11), petal(1440, 1235, 105, 46, 222, 12)]
    # a big full wing: 1.5x about its root, with a fuller scalloped trailing edge
    W = lambda x, y: (1560 + 1.38 * (x - 1560) + 0.25 * (1250 - y), 1250 + 1.32 * (y - 1250))
    wing_pts = [W(*q) for q in [(1500, 1250), (1505, 1170), (1545, 1090), (1615, 1015), (1700, 975), (1752, 985),
                                (1745, 1030), (1772, 1062), (1738, 1100), (1760, 1135), (1712, 1165), (1725, 1200),
                                (1672, 1218), (1660, 1258), (1610, 1262)]]
    wing = smooth(wing_pts)
    tips = [lump(*W(1728, 1000), 62, 30, -25, 21, 0.08), lump(*W(1742, 1075), 56, 28, -8, 22, 0.08)]
    body_items = ([it(t, DEEP, INK, (1500, 1250), 0.58, 0.72) for t in tail]
                  + [it(wing, DEEP, INK, (1560, 1250), 0.72, 0.92, sweep=(180, 0))]
                  + [it(body, PINK, INK, (1560, 1305), 0.5, 0.66)]
                  + [it(t, BLACK, INK, (1580, 1230), 0.86, 1.0) for t in tips])
    return {'note': 29,
            'label': "The snout creature's long straw: hold F1 to play; it turns into a flamingo, pink climbing it from "
                     "the water end, its head lifting with a black-tipped beak, its eye waking, then its body puffing "
                     "up on the arch and a big wing fluffing open",
            'crop': (1150, 760, 1350, 1500),
            'effects': [{'effect': 'sprites', 'place': 'on', 'items': bands},
                        {'effect': 'sprites', 'place': 'over', 'items': body_items + head_items + beak_items + face}]}


# ---- note-38 D2: the mint sliver becomes a pea pod -----------------------------------------------------------------

def pea_pod() -> dict:
    INK = 13
    POD, OPEN, PEA, PEA2 = '#A8E07E', '#3F7A2A', '#7BD94A', '#5DBB33'
    peas = [(1905, 1515, 40), (1888, 1615, 50), (1906, 1727, 46), (1914, 1828, 37)]
    left = [(1903, 1420), (1868, 1475), (1838, 1560), (1828, 1640), (1846, 1740), (1866, 1830), (1898, 1900)]
    right = [(1985, 1830), (2000, 1730), (1995, 1625), (1972, 1530), (1936, 1460)]
    shell = smooth(left + [(1915, 1925), (1950, 1890)] + right)
    slit = smooth([(1904, 1458), (1866, 1530), (1848, 1615), (1858, 1725), (1878, 1830), (1912, 1880),
                   (1950, 1830), (1960, 1725), (1952, 1615), (1934, 1520)])
    items = [it(shell, POD, INK, (1910, 1660), 0.05, 0.27, grow='y'),
             it(slit, OPEN, INK * 0.85, (1905, 1660), 0.25, 0.42, grow='y')]
    order = [(0, 0.42, 0.56), (2, 0.56, 0.7), (3, 0.7, 0.82), (1, 0.0, 0.05)]
    for i, s, e in order:
        x, y, r = peas[i]
        items.append(it(lump(x, y, r, r * 0.95, 0, 40 + i, 0.06, 12), PEA, INK, (x, y), s, e))
        items.append(it(lump(x + r * 0.2, y + r * 0.25, r * 0.55, r * 0.35, 20, 50 + i, 0.08, 10), PEA2, 0, (x, y), s, e))
    for i, (x, y, r) in enumerate(peas):
        items.append(it(lump(x - r * 0.35, y - r * 0.38, r * 0.24, r * 0.15, -30, 60 + i, 0.1, 8), '#ffffff', 0,
                        (x, y), 0.84 + 0.03 * i, 0.94 + 0.02 * i))
    curl = k.spiral(1912, 1432, math.radians(-70), 46, 1.25, 0.75, 1, 40)
    items.append(it(ltube(curl, 13, 6, 9, 0.04), POD, INK * 0.8, (1912, 1440), 0.8, 1.0))
    return {'note': 38,
            'label': "The pale mint sliver beside the yellow spike: hold D2 to play; its round bud swells into a pea, "
                     "the sliver fattens into a pod, splits open and three more peas pop in, and a tendril curls from "
                     "its tip",
            'items': items,
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-42 F#2: the pour from the spout becomes a genie ------------------------------------------------------------

def genie() -> dict:
    INK = 13
    BLUE, DEEP, GOLD = '#A6E8FF', '#4FB6E8', '#FFCF33'
    puff = scallop(1688, 1712, 40, 7, 0.13, 3, 20)
    tailP = spline([(1702, 1790), (1716, 1742), (1694, 1700), (1650, 1690), (1622, 1652), (1630, 1596)], 10)
    tail = ltube(tailP, 12, 50, 4, 0.12)
    body = smooth([(1572, 1500), (1600, 1486), (1640, 1484), (1680, 1490), (1696, 1512), (1680, 1560), (1662, 1600),
                   (1630, 1612), (1600, 1600), (1582, 1560)])
    head = lump(1636, 1440, 50, 48, 0, 6, 0.05)
    parts = seamless([(tail, (1700, 1772), 0.05, 0.3), (body, (1630, 1600), 0.24, 0.42), (head, (1636, 1490), 0.38, 0.52)],
                     BLUE, INK)
    sash = lump(1630, 1588, 60, 17, 4, 8, 0.08)
    knot = (f'M{p(1611, 1430)}C{p(1600, 1395)} {p(1622, 1370)} {p(1650, 1352)}C{p(1662, 1378)} {p(1668, 1408)} '
            f'{p(1660, 1430)}Z')
    band = lump(1638, 1424, 26, 9, -4, 9, 0.08)
    items = [it(puff, BLUE, INK, (1690, 1745), 0.0, 0.05)] + parts
    items += [it(sash, DEEP, INK * 0.85, (1630, 1588), 0.3, 0.44, grow='x'),
              it(knot, DEEP, INK, (1636, 1428), 0.46, 0.56), it(band, GOLD, INK * 0.8, (1638, 1424), 0.5, 0.58)]
    items += eye(1615, 1440, 15, '#2B2B8F', INK * 0.6, 0.52, lid=BLUE, lid_out=(0.62, 0.72))
    items += eye(1658, 1440, 15, '#2B2B8F', INK * 0.6, 0.53, lid=BLUE, lid_out=(0.63, 0.73))
    mouth = (f'M{p(1617, 1466)}C{p(1625, 1490)} {p(1650, 1490)} {p(1658, 1464)}C{p(1645, 1472)} {p(1630, 1472)} '
             f'{p(1617, 1466)}Z')
    items.append(it(mouth, '#D3245E', INK * 0.6, (1637, 1470), 0.68, 0.78))
    # ta-da: both arms swing up and out, gold cuffs on the wrists last
    for side, sh, ctrl, hand, seed in ((-1, (1588, 1520), ((1555, 1500), (1545, 1450)), (1568, 1398), 11),
                                       (1, (1672, 1520), ((1710, 1500), (1726, 1452)), (1714, 1396), 12)):
        P = bez(sh, ctrl[0], ctrl[1], hand, 14)
        items += seamless([(ltube(P, 17, 14, seed), sh, 0.74, 0.88), (lump(hand[0], hand[1], 22, 20, 0, seed, 0.1), sh, 0.76, 0.9)],
                          BLUE, INK)
        cx, cy = P[-4]
        ang = math.degrees(math.atan2(P[-3][1] - P[-5][1], P[-3][0] - P[-5][0]))
        items.append(it(lump(cx, cy, 9, 19, ang, seed, 0.08), GOLD, INK * 0.7, (cx, cy), 0.88, 1.0))
    return {'note': 42,
            'label': "The pale blue pour from the snout's little spout: hold F#2 to play; it lifts as a curl of smoke "
                     "and a genie swirls up out of it, its eyes open, it smiles and throws both arms up, ta-da",
            'crop': (1300, 1250, 650, 800),
            'effects': [{'effect': 'sprites', 'place': 'around', 'items': items}]}


# ---- note-53 F3: the pink cap grows into a party hat -----------------------------------------------------------------

def party_hat() -> dict:
    INK = 12
    HAT, YEL, CYAN, POM = '#F65FE2', '#FFE24D', '#5FE6F5', '#FFF6C8'
    BL, BR = (2392, 1706), (2612, 1750)
    base_mid = (2500, 1738)

    def cone(apex, wob_seed):
        rnd = random.Random(wob_seed)
        L = [(BL[0] + (apex[0] - BL[0]) * u + rnd.uniform(-5, 5), BL[1] + (apex[1] - BL[1]) * u) for u in (0.25, 0.5, 0.75)]
        R = [(apex[0] + (BR[0] - apex[0]) * u + rnd.uniform(-5, 5), apex[1] + (BR[1] - apex[1]) * u) for u in (0.25, 0.5, 0.75)]
        return smooth([BL] + L + [apex, (apex[0] + 6, apex[1] + 4)] + R + [BR, base_mid])

    A1, A2 = (2418, 1468), (2462, 1318)
    items = [it(cone(A1, 1), HAT, INK, base_mid, 0.0, 0.05, out=(0.3, 0.32)),
             it(cone(A2, 2), HAT, INK, base_mid, 0.08, 0.3)]

    def edge(P0, P1, u):
        return (P0[0] + (P1[0] - P0[0]) * u, P0[1] + (P1[1] - P0[1]) * u)
    for j, (u0, u1, col, s) in enumerate(((0.1, 0.24, CYAN, 0.3), (0.36, 0.5, YEL, 0.44), (0.62, 0.74, '#B8F24A', 0.58))):
        sk = 0.13
        q = [edge(BL, A2, u0), edge(BL, A2, u1), edge(BR, A2, min(0.97, u1 + sk)), edge(BR, A2, min(0.97, u0 + sk))]
        mid_top = ((q[1][0] + q[2][0]) / 2 + 4, (q[1][1] + q[2][1]) / 2 - 6)
        mid_bot = ((q[0][0] + q[3][0]) / 2 + 4, (q[0][1] + q[3][1]) / 2 - 6)
        band = f'M{p(*q[0])}L{p(*q[1])}Q{p(*mid_top)} {p(*q[2])}L{p(*q[3])}Q{p(*mid_bot)} {p(*q[0])}Z'
        items.append(it(band, col, INK * 0.85, ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2), s, s + 0.14, grow='x'))
    for j, (ctrl, end, col, w, a0, sg) in enumerate(((((2410, 1270), (2340, 1270)), (2320, 1210), '#B8F24A', 17, -90, 1),
                                                     (((2480, 1240), (2430, 1200)), (2455, 1150), CYAN, 16, -20, 1),
                                                     (((2530, 1300), (2590, 1290)), (2600, 1225), YEL, 16, -90, -1))):
        P = bez((A2[0], A2[1] - 12), ctrl[0], ctrl[1], end, 14)
        P += k.spiral(end[0], end[1], math.radians(a0), 26, 0.9, 0.6, sg, 14)[1:]
        items.append(it(ltube(P, w, w * 0.7, 30 + j, 0.18), col, INK * 0.85, P[0], 0.84 + 0.03 * j, 0.94 + 0.03 * j))
    items.append(it(lump(A2[0], A2[1] - 12, 42, 40, 0, 5, 0.13, 9), POM, INK, A2, 0.72, 0.84))
    return {'note': 53,
            'label': "The pink cap on the orange sprite's yellow head: hold F3 to play; it stretches up into a tall "
                     "party hat, candy stripes wind round it, a pom-pom pops on top and streamers burst out",
            'crop': (2150, 1100, 650, 750),
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-58 A#3: the spike's yellow face opens into a daffodil ------------------------------------------------------

def daffodil() -> dict:
    INK = 13
    PET, PET2, TRUMP, RIM, INNER = '#FFE83D', '#FFF59A', '#FF9A1F', '#FFB52E', '#D9560D'
    C = (1852, 1282)
    angs = [(-138, 0.0, 0.06), (-78, 0.1, 0.22), (-18, 0.22, 0.34), (42, 0.34, 0.46), (102, 0.46, 0.58), (162, 0.58, 0.7)]
    items = []
    for j, (a, s, e) in enumerate(angs):
        items.append(it(petal(C[0], C[1], 152, 94, a, 70 + j, 0.0), PET, INK, C, s, e))
        items.append(it(petal(C[0] + 14 * math.cos(math.radians(a)), C[1] + 14 * math.sin(math.radians(a)), 70, 18, a,
                              80 + j, 0.0), PET2, 0, C, s, e))
    items.append(it(scallop(C[0], C[1], 68, 12, 0.08, 9), RIM, INK, C, 0.68, 0.82))
    items.append(it(lump(C[0] + 3, C[1] + 3, 52, 50, 0, 10, 0.07), TRUMP, INK, C, 0.74, 0.88))
    items.append(it(lump(C[0] + 6, C[1] + 7, 28, 26, 0, 11, 0.1), INNER, INK * 0.8, C, 0.86, 0.96))
    for j, (dx, dy) in enumerate(((-6, -2), (10, 4), (2, 14))):
        items.append(it(k.circle(C[0] + 5 + dx, C[1] + 6 + dy, 6), '#FFF04D', INK * 0.5, C, 0.92 + 0.02 * j, 0.97 + 0.01 * j))
    return {'note': 58,
            'label': "The yellow face of the leaning spike: hold A#3 to play; its tip splits like a bud and yellow "
                     "petals open one by one into a big daffodil, then its orange trumpet pushes out",
            'crop': (1600, 1050, 600, 600),
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-91 G6: a paper lantern pops open in the nook under the straw -----------------------------------------------

def lantern() -> dict:
    INK = 10
    BODY, ORANGE, YEL, CAP, HALO, CORE = '#FF5A82', '#FFA03A', '#FFE24D', '#8A55D0', '#FFF6A6', '#FFFDE2'
    X, TOP = 1474, 1360
    cy = 1428
    halo = scallop(X, cy, 72, 13, 0.07, 2)
    cord = ltube([(X, TOP - 4), (X + 1, TOP + 22)], 4, 4, 1, 0.0)
    cap_t = lump(X, 1384, 22, 8, 0, 3, 0.08)
    body = lump(X, cy, 56, 44, 0, 4, 0.04)
    cap_b = lump(X, 1472, 18, 7, 0, 5, 0.08)
    goreA = lens(X, 1386, X, 1470, 62)
    goreB = lens(X, 1386, X, 1470, 26)
    tassel = (f'M{p(X - 7, 1476)}C{p(X - 16, 1500)} {p(X - 18, 1525)} {p(X - 6, 1540)}L{p(X + 6, 1540)}'
              f'C{p(X + 18, 1525)} {p(X + 16, 1500)} {p(X + 7, 1476)}Z')
    items = [it(halo, HALO, INK, (X, cy), 0.72, 0.88),
             it(cord, CAP, INK * 0.6, (X, TOP), 0.0, 0.04, grow='y'),
             it(body, BODY, INK, (X, TOP), 0.0, 0.05, grow='y'),
             it(goreA, ORANGE, INK * 0.8, (X, cy), 0.18, 0.34, grow='x'),
             it(goreB, YEL, INK * 0.8, (X, cy), 0.36, 0.52, grow='x'),
             it(cap_t, CAP, INK, (X, TOP), 0.0, 0.05, grow='y'),
             it(cap_b, CAP, INK, (X, TOP), 0.0, 0.05, grow='y'),
             it(tassel, BODY, INK, (X, 1476), 0.54, 0.7, grow='y'),
             it(lump(X, cy + 2, 20, 26, 0, 6, 0.1), CORE, 0, (X, cy), 0.84, 1.0)]
    return {'note': 91,
            'label': "The little cream nook under the straw's arch: hold G6 to play; a paper lantern pops open hanging "
                     "from the straw, its panels fill with colour, a tassel drops and it lights up glowing",
            'crop': (1300, 1250, 350, 350),
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


def _strip_items(d):
    d.pop('items', None)
    return d


DESIGNS = [_strip_items(f()) for f in (flamingo, pea_pod, genie, party_hat, daffodil, lantern)]
DESIGNS[1]['crop'] = (1650, 1300, 500, 700)

if __name__ == '__main__':
    k.run(DESIGNS)
