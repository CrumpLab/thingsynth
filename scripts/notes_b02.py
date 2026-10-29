# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b02 of the note animations: notes 24, 71, 72, 86, 105, 106, all in the stalk forest at the top centre,
round the big grey-green cap with the sleepy pink eye.

    uv run scripts/notes_b02.py            # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b02.py 24         # just note-24
    uv run scripts/notes_b02.py export     # build.json for each

note-24  C1  f306 the tall cream gap between the stalks -> a bear wakes: head, body, hugs the stalks, eyes open,
                                                            stretches its arms up and yawns
note-71  B4  f283 the slate patch under the cap         -> a honey hive swells band by band, a door, honey drips,
                                                            two candy bees zip out
note-72  C5  f284 the mauve pod under the cap           -> seed pod: a seam splits, peel curls back, three seeds pop
                                                            out on stalks and sing
note-86  D6  f277 the pink lid of the cap's eye         -> ladybug: spots, a head peeks out, its wing cases lift, it
                                                            flies up off the eye, which is left wide open
note-105 A7  f270 the green thorn-leaf on the stem      -> fiddlehead: it curls into a coil that unrolls into a frond
note-106 A#7 f273 the green half-moon leaf on the stalk -> lily-of-the-valley: a stem arches out, three candy bells
                                                            open and ring
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks); ks.loader.exec_module(k)
p, tube, bez, spiral, crescent, rot_path = k.p, k.tube, k.bez, k.spiral, k.g.crescent, k.g.rot_path
FILLS = k.m.FILLS

DARK = '#3A1F3D'
PLUM = '#5B2346'
PINK = '#FF8FB8'


# ---- drawing helpers --------------------------------------------------------------------------------------------

def closed(pts) -> str:
    """A smooth closed Catmull-Rom outline through the points."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(cx, cy, rx, ry, seed=0, wob=0.07, n=11, rot=0.0) -> str:
    """A lumpy hand-drawn oval, turned by rot degrees."""
    rnd = random.Random(seed)
    r0 = math.radians(rot)
    pts = []
    for j in range(n):
        a = j / n * 2 * math.pi
        f = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r0) - y * math.sin(r0), cy + x * math.sin(r0) + y * math.cos(r0)))
    return closed(pts)


def ltube(P, w0, w1, seed=0, jit=0.07) -> str:
    """A lumpy tapered limb along P (half-widths w0 -> w1), round-capped at the end."""
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
        wl = w * (1 + jit * math.sin(u * 9 + ph1))
        wr = w * (1 + jit * math.sin(u * 7 + ph2))
        L.append((x + nx * wl, y + ny * wl))
        R.append((x - nx * wr, y - ny * wr))
    rr = max(1.0, math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1]) / 2)
    return 'M' + 'L'.join(p(*q) for q in L) + f'A{rr:.1f} {rr:.1f} 0 0 1 {p(*R[-1])}' + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def _move(d: str, dx: float, dy: float) -> str:
    """Translate an M/L/C/A/Z path."""
    import re
    out = []
    for cmd, args in re.findall(r'([MLCAZ])([^MLCAZ]*)', d):
        v = [float(t) for t in re.findall(r'-?\d+\.?\d*', args)]
        if cmd == 'A':
            rx, ry, xr, la, sw, x, y = v
            out.append(f'A{rx:.1f} {ry:.1f} {xr:.1f} {int(la)} {int(sw)} {p(x + dx, y + dy)}')
        elif cmd == 'Z':
            out.append('Z')
        else:
            out.append(cmd + ' '.join(p(v[i] + dx, v[i + 1] + dy) for i in range(0, len(v), 2)))
    return ''.join(out)


def _scale(d: str, ox: float, oy: float, k: float) -> str:
    """Scale an M/L/C/Z path about (ox, oy)."""
    import re
    out = []
    for cmd, args in re.findall(r'([MLCZ])([^MLCZ]*)', d):
        v = [float(t) for t in re.findall(r'-?\d+\.?\d*', args)]
        out.append('Z' if cmd == 'Z' else cmd + ' '.join(p(ox + (v[i] - ox) * k, oy + (v[i + 1] - oy) * k) for i in range(0, len(v), 2)))
    return ''.join(out)


def it(d, fill, edge, at, s, e, out=None, grow='scale') -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


def pair(d, fill, ink, at, s, e, out=None, grow='scale'):
    """A seamless part: an outlined layer (twice the ink: the fill layer covers its inner half) and a fill-only one."""
    return it(d, fill, ink * 2, at, s, e, out, grow), it(d, fill, 0, at, s, e, out, grow)


def sprites(items, place='over') -> dict:
    return {'effect': 'sprites', 'place': place, 'items': items}


# ---- note-24 C1: the bear wakes -----------------------------------------------------------------------------------

def bear() -> dict:
    E = 15
    FUR, LIGHT, MUZ = '#F9DDAA', '#FFF4DC', '#FFE9C9'
    base = (1462.0, 1292.0)
    hb = (1462.0, 1050.0)  # the head grows from its chin
    body = blob(1462, 1172, 104, 124, seed=3, wob=0.08, n=10, rot=3)
    arms = [  # (centreline, paw centre, window, out window, shoulder)
        (bez((1430, 1105), (1395, 1112), (1360, 1092), (1340, 1066), 16), (1336, 1058), (0.25, 0.4), (0.74, 0.8), (1405, 1095)),
        (bez((1494, 1105), (1530, 1112), (1565, 1092), (1588, 1066), 16), (1592, 1058), (0.33, 0.48), (0.74, 0.8), (1520, 1095)),
        (bez((1425, 1100), (1360, 1070), (1330, 1000), (1318, 920), 18), (1314, 900), (0.76, 0.9), None, (1405, 1090)),
        (bez((1499, 1100), (1565, 1070), (1590, 1000), (1600, 920), 18), (1604, 900), (0.79, 0.93), None, (1520, 1090)),
    ]
    outl, fills, paws = [], [], []
    bo, bf = pair(body, FUR, E, base, 0.06, 0.24, grow='y')
    outl.append(bo)
    for j, (P, paw, (s, e), out, sh) in enumerate(arms):
        ao, af = pair(ltube(P, 30, 26, seed=40 + j), FUR, E, sh, s, e, out)
        outl.append(ao)
        fills.append(af)
        paws.append(it(blob(paw[0], paw[1], 36, 33, seed=50 + j, wob=0.08), FUR, E, sh, s, e, out))
    belly = it(blob(1462, 1196, 62, 80, seed=7, wob=0.1, n=9), LIGHT, 12, base, 0.1, 0.26, grow='y')
    ears = it(blob(1386, 912, 40, 32, seed=11, wob=0.12, n=9, rot=-30) + blob(1540, 906, 34, 36, seed=12, wob=0.12, n=9, rot=20),
              FUR, E, hb, 0.0, 0.06)
    inner = it(blob(1390, 916, 19, 14, seed=13, wob=0.15, n=8, rot=-30) + blob(1536, 912, 15, 17, seed=14, wob=0.15, n=8),
               PINK, 10, hb, 0.0, 0.06)
    head = it(blob(1462, 978, 104, 80, seed=5, wob=0.09, n=10, rot=-4), FUR, E, hb, 0.0, 0.06)
    muzzle = it(blob(1464, 1016, 50, 33, seed=8, wob=0.12, n=9, rot=6), MUZ, 12, hb, 0.0, 0.06)
    nose = it(closed([(1446, 990), (1464, 984), (1482, 991), (1466, 1006)]), DARK, 8, hb, 0.0, 0.06)

    def almond(ex, ey, w, h, tilt):
        return closed([(ex - w, ey + tilt), (ex - w * 0.4, ey - h * 0.9), (ex + w * 0.3, ey - h), (ex + w, ey - tilt),
                       (ex + w * 0.3, ey + h * 0.9), (ex - w * 0.4, ey + h * 0.85)])

    def lid(ex, ey, w, h, tilt):  # the upper part of the almond, down past its middle: the eye half-shut
        return closed([(ex - w, ey + tilt), (ex - w * 0.4, ey - h * 0.9), (ex + w * 0.3, ey - h), (ex + w, ey - tilt),
                       (ex + w * 0.3, ey + h * 0.45), (ex - w * 0.4, ey + h * 0.45)])

    EYES = ((1417, 958, 30, 20, 4), (1509, 958, 30, 20, -4))
    sleepy = it(''.join(almond(*q) for q in EYES), '#C9A0D8', 11, hb, 0.0, 0.06, (0.5, 0.56))
    lids = it(''.join(lid(*q) for q in EYES), '#FF9AAE', 11, hb, 0.0, 0.06, (0.5, 0.56))
    whites = it(''.join(almond(*q) for q in EYES), '#FFFFFF', 12, (1462, 958), 0.5, 0.6, grow='y')
    irises = it(blob(1420, 956, 15, 15, seed=23) + blob(1506, 956, 15, 15, seed=24), '#39D5FF', 8, (1462, 956), 0.56, 0.64)
    pupils = it(blob(1421, 952, 8, 8, seed=25) + blob(1507, 952, 8, 8, seed=26), DARK, 0, (1462, 953), 0.6, 0.68)
    mouth = it(blob(1464, 1046, 36, 44, seed=31, wob=0.1, n=9), PLUM, 12, (1462, 1008), 0.78, 1.0)
    tongue = it(blob(1462, 1068, 23, 14, seed=32), PINK, 9, (1462, 1008), 0.86, 1.0)
    bfill = it(body, FUR, 0, base, 0.06, 0.24, grow='y')
    items = outl + [bfill] + fills + [belly] + paws + [ears, inner, head, muzzle, nose, sleepy, lids, whites, irises, pupils, mouth, tongue]
    return {
        'note': 24,
        'label': 'The tall cream gap between the stalks under the big cap: hold C1 to play; it wakes as a big cream bear '
                 'that hugs the stalks, opens its eyes, then stretches its arms up and yawns',
        'effects': [sprites(items)],
    }


# ---- note-71 B4: honey hive ---------------------------------------------------------------------------------------

def hive() -> dict:
    E = 14
    GOLD, AMBER, HONEY = '#FFC93C', '#F5A524', '#FFB938'
    hang = (1456.0, 694.0)
    bands = [  # bottom first, so each band above laps over the one below; (cx, cy, rx, ry, colour, window)
        (1458, 818, 70, 29, AMBER, (0.27, 0.4)),
        (1458, 781, 90, 31, GOLD, (0.15, 0.29)),
        (1456, 743, 82, 30, AMBER, (0.05, 0.18)),
        (1455, 708, 60, 27, GOLD, (0.0, 0.06)),
    ]
    items = []
    drips_o, drips_f = [], []
    for x0, y0, x1, y1, r, s in ((1530, 790, 1538, 872, 16, 0.47),):
        d = ltube(bez((x0, y0), (x0 + 4, y0 + 24), (x1, y1 - 34), (x1, y1 - r), 10), 9, 5, seed=int(x0)) + blob(x1, y1, r, r * 1.1, seed=int(y0), wob=0.06)
        o, f = pair(d, HONEY, 11, (x0, y0), s, s + 0.15, grow='y')
        drips_o.append(o)
        drips_f.append(f)
    items += drips_o + drips_f
    for j, (cx, cy, rx, ry, col, (s, e)) in enumerate(bands):
        items.append(it(blob(cx, cy, rx, ry, seed=60 + j, wob=0.08, n=10), col, E, hang, s, e))
    door = (1460.0, 800.0)
    items.append(it(blob(door[0], door[1], 23, 18, seed=66, wob=0.1), DARK, 11, door, 0.4, 0.5))

    def bee(cx, cy, rot, s, seed, face=-1):
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        R = lambda x, y: (cx - face * x * ca - y * sa, cy - face * x * sa + y * ca)
        wings = (blob(*R(-6, -50), 20, 34, seed=seed, wob=0.1, rot=rot - 25) +
                 blob(*R(24, -46), 17, 30, seed=seed + 1, wob=0.1, rot=rot + 30))
        body_ = blob(cx, cy, 54, 36, seed=seed + 2, wob=0.08, rot=rot)
        stripes = blob(*R(2, 0), 9, 33, seed=seed + 3, rot=rot) + blob(*R(28, 0), 8, 27, seed=seed + 4, rot=rot)
        head_ = blob(*R(-48, 2), 22, 21, seed=seed + 5, wob=0.08, rot=rot)
        return [it(wings, '#DDFBFF', 10, door, s, s + 0.14), it(body_, '#FFE14D', 12, door, s, s + 0.14),
                it(stripes, '#FF4FA3', 0, door, s, s + 0.14), it(head_, DARK, 10, door, s, s + 0.14)]

    items += bee(1290, 870, -18, 0.63, 70)          # zips out down to the left, over the left stalk
    items += bee(1600, 782, 12, 0.78, 80, face=1)   # and out to the right, over the middle stalk
    items.insert(0, it(crescent(1290, 870, 96, 20, 75, 26), '#FFFFFF', 10, (1290, 870), 0.78, 0.9))
    items.insert(0, it(crescent(1600, 782, 92, 150, 205, 26), '#FFFFFF', 10, (1600, 782), 0.9, 1.0))
    return {
        'note': 71,
        'label': 'The slate patch under the big cap, between the stalks: hold B4 to play; it swells into a honey hive band '
                 'by band, honey drips from it and two candy bees zip out',
        'effects': [sprites(items)],
    }


# ---- note-72 C5: seed pod -----------------------------------------------------------------------------------------

def pod() -> dict:
    E = 13
    B = (1690.0, 818.0)
    STALK = '#8EDC63'
    seeds = [  # (centre, r, colour, window, seed)
        ((1636, 928), 44, '#FF7FB8', (0.24, 0.36), 1),
        ((1720, 975), 48, '#FFE14D', (0.42, 0.54), 2),
        ((1786, 908), 40, '#6FE6FF', (0.6, 0.72), 3),
    ]
    items = []
    for (cx, cy), r, col, (s, e), sd in seeds:
        P = bez(B, (B[0] + (cx - B[0]) * 0.2, B[1] + 40), (cx, cy - r - 30), (cx, cy - r + 6), 14)
        items.append(it(ltube(P, 10, 8, seed=sd), STALK, 11, B, s - 0.02, e - 0.04))
    items.append(it(blob(1690, 814, 44, 17, seed=90), PLUM, 11, B, 0.04, 0.14))
    items.append(it(ltube(bez((1668, 800), (1636, 856), (1584, 878), (1566, 846), 18), 34, 12, seed=91), '#9A55B4', E, (1668, 800), 0.05, 0.2))
    items.append(it(ltube(bez((1714, 798), (1748, 852), (1800, 868), (1816, 836), 18), 34, 12, seed=92), '#B06CC8', E, (1714, 798), 0.1, 0.25))
    # the tap: the pod swells a little (its own outline, scaled from its top) and a fat bright seam splits it, glinting
    seam = closed([(1698, 722), (1720, 756), (1716, 800), (1692, 826), (1668, 800), (1672, 756)])
    glint = closed([(1734, 742), (1741, 762), (1760, 768), (1741, 774), (1734, 794), (1727, 774), (1708, 768), (1727, 762)])
    items[:0] = [it(_scale(FILLS['f284'], 1690, 722, 1.12), '#A45CC0', E, (1690, 722), 0.0, 0.04)]
    items.append(it(seam, '#FFF27A', 11, (1694, 774), 0.0, 0.045))
    items.append(it(glint, '#FFFFFF', 8, (1734, 768), 0.0, 0.05))
    for (cx, cy), r, col, (s, e), sd in seeds:
        items.append(it(blob(cx, cy, r, r * 0.95, seed=sd + 10, wob=0.07), col, 12, B, s, e))
    for (cx, cy), r, col, (s, e), sd in seeds:
        eyes = crescent(cx - r * 0.38, cy - r * 0.05, r * 0.22, 20, 160, 7) + crescent(cx + r * 0.38, cy - r * 0.05, r * 0.22, 20, 160, 7)
        items.append(it(eyes, DARK, 0, B, s, e))
    for j, ((cx, cy), r, col, _, sd) in enumerate(seeds):
        s = 0.78 + 0.06 * j
        items.append(it(blob(cx, cy + r * 0.42, r * 0.3, r * 0.36, seed=sd + 20, wob=0.1), PLUM, 8, (cx, cy + r * 0.25), s, s + 0.1))
    items.append(it(crescent(1636, 928, 76, 150, 210, 20), '#FFFFFF', 10, (1636, 928), 0.9, 1.0))
    items.append(it(crescent(1786, 908, 72, -30, 30, 20), '#FFFFFF', 10, (1786, 908), 0.94, 1.0))
    return {
        'note': 72,
        'label': 'The mauve pod under the big cap, right of the stalk: hold C5 to play; it splits open, its peel curls '
                 'back and three candy seeds pop out on stalks and sing',
        'effects': [sprites(items)],
    }


# ---- note-86 D6: ladybug lid --------------------------------------------------------------------------------------

def ladybug() -> dict:
    E = 12
    SHELL = '#FF5C7A'
    C = (1832.0, 566.0)  # the lid's middle: the bug sits there, flies from there
    lid = FILLS['f277']
    halfL = closed([(1758, 590), (1768, 556), (1796, 536), (1832, 530), (1834, 560), (1832, 591), (1795, 593)])
    halfR = closed([(1832, 530), (1868, 534), (1896, 556), (1908, 588), (1870, 594), (1832, 591), (1834, 560)])
    spotsL = [(1790, 564, 11), (1812, 545, 9), (1806, 580, 8)]
    spotsR = [(1856, 548, 9), (1878, 568, 11), (1852, 580, 8)]

    def spot_d(dx=0.0, dy=0.0, rot=0.0, which='LR'):
        d = ''
        for side, S in (('L', spotsL), ('R', spotsR)):
            if side in which:
                for j, (x, y, r) in enumerate(S):
                    d += blob(x + dx, y + dy, r, r, seed=j + (0 if side == 'L' else 9), wob=0.12, n=7)
        return d

    def bug(dx, dy, deg, s, e, out=None, spread=0.0):
        """The bug with its cases open by deg, moved by (dx, dy); grows from (or shrinks to) the lid's middle.
        spread opens the filmy wings out wider (flying)."""
        hinge = (1832 + dx, 532 + dy)
        wx, wy, wr = 40 + 34 * spread, 17 + 4 * spread, 54 + 22 * spread
        wings = (blob(1832 - wx + dx, 532 - wy + dy, wr, 22 + 4 * spread, seed=101, rot=-28 - deg * 0.3) +
                 blob(1832 + wx + dx, 532 - wy + dy, wr, 22 + 4 * spread, seed=102, rot=28 + deg * 0.3))
        body_ = _move(lid, dx, dy)
        cL = rot_path(_move(halfL, dx, dy), *hinge, deg)
        cR = rot_path(_move(halfR, dx, dy), *hinge, -deg)
        sp = rot_path(spot_d(dx, dy, which='L'), *hinge, deg) + rot_path(spot_d(dx, dy, which='R'), *hinge, -deg)
        return [it(wings, '#E6FBFF', 10, C, s, e, out), it(body_, DARK, E, C, s, e, out),
                it(cL, SHELL, E, C, s, e, out), it(cR, SHELL, E, C, s, e, out), it(sp, DARK, 0, C, s, e, out)]

    def head(dx, dy, s, e, out=None):
        hx, hy = 1740 + dx, 574 + dy
        feel = (ltube(bez((hx - 8, hy - 12), (hx - 26, hy - 26), (hx - 40, hy - 28), (hx - 52, hy - 22), 10), 4, 4, seed=111) +
                ltube(bez((hx - 12, hy + 2), (hx - 30, hy + 2), (hx - 44, hy + 8), (hx - 54, hy + 18), 10), 4, 4, seed=112))
        knobs = blob(hx - 54, hy - 22, 8, 8, seed=113) + blob(hx - 56, hy + 20, 8, 8, seed=114)
        return [it(feel + knobs, DARK, 0, (hx, hy), s, e, out), it(blob(hx, hy, 24, 21, seed=115, wob=0.08), DARK, 10, (hx, hy), s, e, out),
                it(blob(hx - 9, hy - 5, 6, 6, seed=116) + blob(hx + 4, hy - 7, 6, 6, seed=117), '#FFFFFF', 0, (hx, hy), s, e, out)]

    leave = (0.55, 0.64)
    items = []
    # 0-0.2 s: spots pop on the lid and a seam splits it down the middle
    items.append(it(spot_d(), DARK, 0, C, 0.0, 0.05, (0.26, 0.3)))
    seam = closed([(1832, 532), (1837, 560), (1835, 592), (1829, 592), (1828, 560)])
    items.append(it(seam, DARK, 0, (1832, 532), 0.0, 0.05, (0.26, 0.3), grow='y'))
    # 0.2-1 s: its head and feelers peek out at the left end
    items += head(0, 0, 0.05, 0.2, leave)
    # 1-2 s: its wing cases lift and filmy wings flick out
    items += bug(0, 0, 28, 0.27, 0.42, leave)
    # 2-3 s: it lifts off the eye, which is left wide open below; the flying bug with its head
    eye = [it(lid, '#FFFFFF', E, (1832, 594), 0.55, 0.66, grow='y'),
           it(blob(1833, 584, 25, 24, seed=120), '#39D5FF', 10, (1833, 584), 0.6, 0.7),
           it(blob(1833, 586, 12, 12, seed=121), DARK, 0, (1833, 586), 0.64, 0.72, (0.74, 0.78)),
           it(blob(1842, 574, 12, 12, seed=122), DARK, 0, (1842, 574), 0.75, 0.83),
           it(blob(1850, 568, 5, 5, seed=123), '#FFFFFF', 0, (1850, 568), 0.8, 0.86)]
    items += eye
    FX, FY = 176, -90
    fly = (1836 + FX, 548 + FY)
    items.insert(0, it(crescent(*fly, 104, -30, 25, 22), '#FFFFFF', 9, fly, 0.86, 0.95))
    items.insert(0, it(crescent(*fly, 136, -25, 20, 18), '#FFFFFF', 9, fly, 0.9, 1.0))
    items += bug(FX, FY, 50, 0.56, 0.74, spread=1.0)
    items += head(FX, FY, 0.56, 0.74)
    return {
        'note': 86,
        'label': "The pink lid of the big cap's sleepy eye: hold D6 to play; it is a ladybug: spots pop, its head peeks "
                 'out, its wing cases lift and it flies up off the eye, which is left wide open looking up at it',
        'effects': [sprites(items)],
    }


# ---- note-105 A7: fiddlehead --------------------------------------------------------------------------------------

FROND = bez((1846, 944), (1792, 905), (1716, 896), (1664, 932), 40)


def frond_line(f, r0, turns):
    """The frond's rachis out to fraction f of its arch, then a coil curling under at its tip."""
    n = max(2, round(f * (len(FROND) - 1)))
    P = FROND[:n + 1]
    (ax, ay), (bx, by) = P[-2], P[-1]
    h = math.atan2(by - ay, bx - ax)
    S = spiral(bx, by, h, r0, turns, 0.6, -1, 36)
    return P + S[1:]


def blade(f, maxw, lobes, seed) -> str:
    """The frond's leafy blade along the arch out to fraction f: widest a third of the way, scalloped into lobes
    that alternate side to side, like a fern's leaflets."""
    n = max(4, round(f * (len(FROND) - 1)))
    P = FROND[:n + 1]
    rnd = random.Random(seed)
    up, dn = [], []
    for i in range(0, n + 1):
        (ax, ay), (bx, by) = P[max(0, i - 1)], P[min(n, i + 1)]
        d = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / d, (bx - ax) / d
        u = i / n
        w = maxw * max(0.15, math.sin(math.pi * (0.12 + 0.8 * u))) ** 0.8
        k = rnd.uniform(0.95, 1.05)
        wu = w * k * (0.42 + 0.58 * abs(math.sin(u * lobes * math.pi)) ** 0.7)
        wd = w * k * (0.42 + 0.58 * abs(math.sin(u * lobes * math.pi + 0.5)) ** 0.7)
        x, y = P[i]
        up.append((x + nx * wu, y + ny * wu))
        dn.append((x - nx * wd, y - ny * wd))
    return closed(up[::2] + [P[-1]] + dn[::-2])


def fiddlehead() -> dict:
    E = 11
    GREEN, LEAF = '#5FD957', '#A6F28F'
    base = (1846.0, 944.0)
    poses = [  # (fraction of the arch, coil radius, turns, leaflet pairs, window, out window)
        (0.05, 26, 1.7, 0, (0.0, 0.05), (0.24, 0.3)),
        (0.36, 24, 1.5, 1.5, (0.22, 0.32), (0.5, 0.56)),
        (0.68, 21, 1.3, 2.5, (0.5, 0.6), (0.78, 0.84)),
        (1.0, 18, 1.1, 3.5, (0.8, 0.94), None),
    ]
    leaflets, outl, fills = [], [], []
    for j, (f, r0, tn, npairs, (s, e), out) in enumerate(poses):
        o, fl = pair(ltube(frond_line(f, r0, tn), 12, 6, seed=130 + j, jit=0.05), GREEN, E, base, s, e, out)
        outl.append(o)
        fills.append(fl)
        if npairs:
            ls = s + 0.05 if j < 3 else 0.86
            leaflets.append(it(blade(f * 0.97, 50 + 22 * f, npairs, 140 + j), LEAF, E, base, ls, min(1.0, ls + 0.12), out))
    lo, lf = pair(FILLS['f270'], GREEN, E, base, 0.0, 0.04)
    items = leaflets + [lo] + outl + [lf] + fills
    return {
        'note': 105,
        'label': 'The little green thorn-leaf on the mushroom stem: hold A7 to play; it curls into a fiddlehead that '
                 'unrolls into an arching fern frond, two leaflets at a time',
        'effects': [sprites(items)],
    }


# ---- note-106 A#7: lily-of-the-valley -----------------------------------------------------------------------------

def bell_d(cx, top, w, h, seed) -> str:
    rnd = random.Random(seed)
    j = lambda: rnd.uniform(-0.04, 0.04) * w
    pts = [(cx - w * 0.36 + j(), top + h * 0.62), (cx - w * 0.3, top + h * 0.18), (cx, top - h * 0.02),
           (cx + w * 0.3, top + h * 0.18), (cx + w * 0.36 + j(), top + h * 0.62),
           (cx + w * 0.52, top + h * 0.98), (cx + w * 0.3, top + h * 0.86), (cx + w * 0.17, top + h * 1.02),
           (cx, top + h * 0.88), (cx - w * 0.17, top + h * 1.02), (cx - w * 0.3, top + h * 0.86), (cx - w * 0.52, top + h * 0.98)]
    return closed(pts)


def lily() -> dict:
    E = 11
    GREEN = '#5ED05A'
    base = (1672.0, 1206.0)
    S = bez(base, (1686, 1080), (1840, 1046), (1912, 1140), 30)
    bells = [  # (index on the stem, width, colour, window, swing)
        (9, 80, '#FFFFFF', (0.14, 0.3), -14),
        (18, 88, '#FF9ACB', (0.38, 0.54), 12),
        (27, 96, '#C9A2FF', (0.6, 0.76), -12),
    ]
    lo, lf = pair(FILLS['f273'], GREEN, E, base, 0.0, 0.04)
    so, sf = pair(ltube(S, 10, 6, seed=150), GREEN, E, base, 0.0, 0.12)
    items = [lo, so, lf, sf]
    stills, swung, clap = [], [], ''
    for q, (i, w, col, (s, e), sw) in enumerate(bells):
        x, y = S[i]
        top = y + 22
        ped = ltube([(x, y), (x + 2, y + 12), (x, top + 6)], 6, 5, seed=160 + q)
        items.append(it(ped, GREEN, 9, (x, y), s - 0.03, s + 0.04))
        b = bell_d(x, top, w, w * 0.85, 170 + q)
        stills.append(it(b, col, E, (x, top), s, e, (0.84, 0.88)))
        swung.append(it(rot_path(b, x, top, sw), col, E, (x, top), 0.85, 0.92))
        cl = blob(x, top + w * 0.92, 12, 12, seed=180 + q)
        clap += rot_path(cl, x, top, sw)
    items += stills + [it(clap, '#FFD23F', 8, S[18], 0.86, 0.94)] + swung
    for q, (b, a0, a1, rk) in enumerate(((0, 160, 215, 0.8), (2, -35, 20, 0.8), (2, -30, 15, 1.1))):
        i, w = bells[b][0], bells[b][1]
        x, y = S[i]
        cy = y + 22 + w * 0.5
        items.append(it(crescent(x, cy, w * rk, a0, a1, 20), '#FFFFFF', 10, (x, cy), 0.9 + 0.03 * q, 0.97 + 0.01 * q))
    return {
        'note': 106,
        'label': 'The little green half-moon leaf on the stalk, above the grey tube: hold A#7 to play; a stem arches out '
                 'of it and three candy lily-of-the-valley bells open one by one and ring',
        'effects': [sprites(items)],
    }


DESIGNS = [bear(), hive(), pod(), ladybug(), fiddlehead(), lily()]

if __name__ == '__main__':
    k.run(DESIGNS)
