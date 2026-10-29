# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b14 of the note animations: notes 56, 88, 97, 98, 99, 101.

    uv run scripts/notes_b14.py            # strips and end frames
    uv run scripts/notes_b14.py 97         # one note
    uv run scripts/notes_b14.py export     # build.json for each
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
m, g, p = k.m, k.g, k.p


# ---- drawing helpers -----------------------------------------------------------------------------------------------

def smooth(P) -> str:
    """A closed Catmull-Rom curve through P: hand-drawn roundness."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(cx, cy, rx, ry=None, rot=0.0, seed=0, wob=0.08, n=12) -> str:
    """A lumpy hand-drawn oval, turned by rot degrees."""
    ry = ry or rx
    rnd = random.Random(seed)
    a = math.radians(rot)
    P = []
    for i in range(n):
        t = i / n * 2 * math.pi
        q = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * q, math.sin(t) * ry * q
        P.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(P)


def ltube(P, w0, w1, seed=0, wob=0.06, rings=0.0, nring=5) -> str:
    """A lumpy tapered limb along P (half-widths w0 to w1), open-ended at the start, a round cap at the end.
    `rings` bulges it into segments, like a worm."""
    rnd = random.Random(seed)
    ph, n = rnd.random() * 6.28, len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        dd = math.hypot(dx, dy) or 1
        nx, ny = -dy / dd, dx / dd
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + wob * math.sin(u * 9 + ph)) * (1 + rings * abs(math.sin(u * math.pi * nring)))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    ex, ey = P[-1]
    a, b = P[-2], P[-1]
    hd = math.atan2(b[1] - a[1], b[0] - a[0])
    cap = [(ex + math.cos(hd + s) * w1, ey + math.sin(hd + s) * w1) for s in (math.pi / 2 - 0.6, 0.0, -math.pi / 2 + 0.6)]
    return smooth(L[::2] + [L[-1]] + cap + [R[-1]] + R[::-2])


def xf(d: str, fn) -> str:
    """Map every point of an M/C/L/Z path through fn."""
    import re
    out, pend = [], None
    for t in re.findall(r'[MCLZ]|-?\d+\.?\d*', d):
        if t in 'MCLZ':
            out.append(t)
            continue
        if pend is None:
            pend = float(t)
            continue
        out.append(p(*fn(pend, float(t))))
        pend = None
    return ' '.join(out).replace('M ', 'M').replace(' C ', 'C').replace(' L ', 'L').replace(' Z', 'Z')


def rot(d, ox, oy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return xf(d, lambda x, y: (ox + (x - ox) * ca - (y - oy) * sa, oy + (x - ox) * sa + (y - oy) * ca))


def star(cx, cy, ro, ri, n, rot0=0.0, sy=1.0, seed=0) -> str:
    """A lumpy candy star: n rounded points, squashed vertically by sy."""
    rnd = random.Random(seed)
    P = []
    for i in range(2 * n):
        a = math.radians(rot0) + i * math.pi / n
        r = (ro if i % 2 == 0 else ri) * (1 + 0.12 * (rnd.random() * 2 - 1))
        P.append((cx + math.cos(a) * r, cy - math.sin(a) * r * sy))
    return smooth(P)


def drop(cx, cy, r, ang, seed=0) -> str:
    """A flying teardrop, pointed toward ang (degrees, y down)."""
    rnd = random.Random(seed)
    a0 = math.radians(ang)
    P = []
    for i in range(14):
        t = i / 14 * 2 * math.pi
        q = r * (1 + 0.9 * max(0.0, math.cos(t - a0)) ** 8) * (1 + 0.05 * (rnd.random() * 2 - 1))
        P.append((cx + math.cos(t) * q, cy + math.sin(t) * q))
    return smooth(P)


def it(d, fill, edge, at, start, end, grow='scale', out=None):
    q = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 4),
         'end': round(end, 4), 'grow': grow}
    if out:
        q['outStart'], q['outEnd'] = round(out[0], 4), round(out[1], 4)
    return q


def pair(d, fill, at, start, end, edge, out=None):
    """An outlined layer (double-width stroke) and a fill-only layer: laid outlines-first, fills-second, shapes that
    overlap merge without seams."""
    return it(d, fill, edge * 2, at, start, end, out=out), it(d, fill, 0, at, start, end, out=out)


def ink_copy(ids, at):
    """The painting's own ink strokes laid back over the new drawing, from the first frame on."""
    seen, out = set(), []
    for i in ids:
        b = tuple(round(v) for v in m.IP[i]['bbox']) if hasattr(m, 'IP') else i
        if b in seen:
            continue
        seen.add(b)
        out.append(it(m.INKS[i], '#000', 0, at, 0.0, 0.002))
    return out


def eye(cx, cy, r, look, start, end, seed=0, edge=10):
    """A round friendly eye: white, a black pupil looking toward `look` (dx, dy), a glint."""
    px, py = cx + look[0] * r * 0.38, cy + look[1] * r * 0.38
    return [it(lump(cx, cy, r, r * 1.05, 0, seed, 0.05), '#ffffff', edge, (cx, cy), start, end),
            it(lump(px, py, r * 0.48, r * 0.52, 0, seed + 1, 0.05), '#111111', 0, (cx, cy), start, end),
            it(lump(px + r * 0.16, py - r * 0.18, r * 0.14, r * 0.14, 0, seed + 2, 0.02), '#ffffff', 0, (cx, cy), start, end)]


# ---- note-56 G#3: the brown panel under the cap: Pinocchio ----------------------------------------------------------

def pinocchio():
    BROWN, DARK, INK = '#A77360', '#7A4E3A', 13
    # the nose: from inside the panel out of its left side, rising a little to the left, in three sections
    C = g.bez((2772, 3812), (2660, 3806), (2540, 3780), (2392, 3738), 60)
    secs = [(0, 26, 0.0, 0.25, 26, 23), (22, 44, 0.24, 0.5, 23, 19), (40, 60, 0.48, 0.72, 19, 15)]
    outl, fills = [], []
    for k0, (a, b, s, e, w0, w1) in enumerate(secs):
        P = C[a:b + 1]
        d = ltube(P, w0, w1, seed=5 + k0)
        o, f = pair(d, BROWN, P[0], s, e, INK)
        if k0 == 0:
            # the outlined layer starts at the panel's left edge, the fill-only layer reaches into the panel
            o['d'] = ltube(C[11:b + 1], w0, w1, seed=5)
        outl.append(o)
        fills.append(f)
    tip = C[-1]
    knot = [it(lump(2590, 3790, 15, 11, -10, 3), DARK, 9, (2590, 3790), 0.3, 0.4),
            it(lump(2470, 3758, 22, 6, -14, 4, 0.1), DARK, 8, (2470, 3758), 0.56, 0.66)]
    # the eye near the top of the panel: half-lidded at once, the lid lifts, a brow goes up in surprise
    ex, ey, er = 2758, 3764, 25
    lid = (f'M{p(ex - er - 6, ey + 2)}C{p(ex - er, ey - er * 1.5)} {p(ex + er, ey - er * 1.5)} {p(ex + er + 6, ey + 2)}'
           f'C{p(ex + 10, ey + 8)} {p(ex - 10, ey + 8)} {p(ex - er - 6, ey + 2)}Z')
    eyes = eye(ex, ey, er, (-0.8, 0.3), 0.0, 0.05, seed=56, edge=11)
    lid_it = it(lid, BROWN, 11, (ex, ey - er - 4), 0.0, 0.05, grow='y', out=(0.42, 0.56))
    brow = it(ltube(g.bez((ex - 30, ey - 36), (ex - 14, ey - 52), (ex + 12, ey - 54), (ex + 30, ey - 44), 14), 6, 5, 7),
              DARK, 9, (ex - 30, ey - 36), 0.55, 0.66)
    # the payoff: a green twig with two leaves sprouts from the nose's tip
    TW = g.bez((tip[0] + 8, tip[1] + 4), (tip[0] - 6, tip[1] - 30), (tip[0] - 2, tip[1] - 60), (tip[0] + 14, tip[1] - 84), 16)
    twig = list(pair(ltube(TW, 9, 7, 9), '#6BBF3A', TW[0], 0.72, 0.84, 9))
    tx, ty = TW[-1]
    leaves = [it(lump(tx - 34, ty - 20, 40, 19, 25, 11), '#7EE05A', 10, (tx, ty), 0.8, 0.92),
              it(lump(tx + 30, ty - 30, 46, 21, -40, 12), '#B5F06A', 10, (tx, ty), 0.88, 1.0)]
    items = outl + fills + knot + eyes + [lid_it, brow] + [twig[0], twig[1]] + leaves
    return {'note': 56, 'crop': (2280, 3540, 640, 640),
            'label': 'The brown panel under the orange cap: hold G#3 to play; it opens a sleepy eye, its wooden nose '
                     'grows out like Pinocchio\'s and a leafy twig sprouts from the tip',
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-88 E6: the raspberry patch on the striped head: blowing a raspberry --------------------------------------

def raspberry():
    INK = 11
    LIP, MOUTH, TONGUE = '#EC3F6E', '#4A1530', '#FF8DB6'
    lip = it(lump(2750, 4076, 66, 52, -40, 88, 0.06), LIP, INK, (2752, 4074), 0.0, 0.05)
    gloss = it(lump(2772, 4046, 18, 8, -40, 87), '#FFB3C9', 0, (2752, 4074), 0.0, 0.05)
    mouth = it(lump(2728, 4098, 38, 29, -30, 89, 0.08), MOUTH, 9, (2730, 4096), 0.06, 0.18)
    TA = g.bez((2732, 4098), (2700, 4114), (2668, 4124), (2632, 4128), 18)
    TB = g.bez((2732, 4098), (2676, 4140), (2600, 4094), (2536, 4130), 26)
    tA = it(ltube(TA, 15, 22, 1), TONGUE, INK, TA[0], 0.16, 0.4, out=(0.42, 0.48))
    tB = it(ltube(TB, 16, 25, 2, wob=0.1), TONGUE, INK, TB[0], 0.42, 0.62)
    shine = it(lump(2584, 4100, 16, 7, -20, 3), '#FFD3E4', 0, TB[0], 0.58, 0.68)
    tip = TB[-1]
    spit = [it(drop(2482, 4080, 25, 20, 1), '#C6F2FF', 9, tip, 0.66, 0.78),
            it(drop(2466, 4146, 21, -5, 2), '#C6F2FF', 9, tip, 0.72, 0.84),
            it(drop(2494, 4204, 18, -30, 3), '#C6F2FF', 9, tip, 0.78, 0.9)]
    puffs = [(2424, 4130, 38), (2402, 4088, 30), (2398, 4174, 28)]
    po = [pair(lump(x, y, r, r * 0.9, 0, 30 + i), '#FFFFFF', (2470, 4130), 0.84 + 0.04 * i, 0.94 + 0.02 * i, 9)
          for i, (x, y, r) in enumerate(puffs)]
    items = [lip, gloss, mouth, tA, tB, shine] + spit + [q[0] for q in po] + [q[1] for q in po]
    return {'note': 88, 'crop': (2360, 3880, 560, 560),
            'label': 'The raspberry patch on the purple creature\'s striped head: hold E6 to play; its lip pouts, it '
                     'sticks its tongue out and blows a raspberry, spit flying and a puff',
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-97 C#7: the pink nub on the pale creature's back: a peeking worm ------------------------------------------

def worm():
    PINK, INK = '#F7A19E', 11
    B = (3120, 3996)
    poses = [  # (centreline, eye look, window, out)
        (g.bez(B, (3120, 3960), (3121, 3910), (3122, 3872), 20), (0.0, -0.6), (0.0, 0.06), (0.17, 0.24)),
        (g.bez(B, (3121, 3920), (3124, 3850), (3126, 3800), 24), (0.5, -0.7), (0.17, 0.3), (0.42, 0.48)),
        (g.bez(B, (3120, 3890), (3092, 3820), (3044, 3790), 26), (-0.9, -0.2), (0.42, 0.56), (0.66, 0.72)),
        (g.bez(B, (3122, 3880), (3160, 3800), (3208, 3762), 28), (0.8, -0.4), (0.66, 0.8), None),
    ]
    items = []
    for i, (P, look, (s, e), out) in enumerate(poses):
        d = ltube(P, 21, 29, seed=97 + i, rings=0.1, nring=4 + i)
        items += list(pair(d, PINK, B, s, e, INK, out))
        hx, hy = P[-1]
        a = math.atan2(P[-1][1] - P[-3][1], P[-1][0] - P[-3][0])
        cx, cy = hx + math.cos(a) * 2, hy + math.sin(a) * 2
        for q in eye(cx, cy, 19, look, s, e, seed=200 + 3 * i, edge=9):
            q['at'] = [B[0], B[1]]
            if out:
                q['outStart'], q['outEnd'] = out
            items.append(q)
    # the chirp: a round open mouth on the right of its head, and a yellow tuft springing up
    hx, hy = poses[-1][0][-1]
    items.append(it(lump(hx + 24, hy + 16, 15, 12, 20, 5), '#5A1A34', 9, (hx + 14, hy + 8), 0.8, 0.9))
    for j, (ang, ln) in enumerate(((118, 60), (86, 72), (54, 58))):
        a = math.radians(ang)
        bx, by = hx - 8, hy - 22
        P = g.bez((bx, by), (bx + math.cos(a) * ln * 0.4, by - math.sin(a) * ln * 0.4),
                  (bx + math.cos(a) * ln * 0.75, by - math.sin(a) * ln * 0.8), (bx + math.cos(a) * ln, by - math.sin(a) * ln), 10)
        items.append(it(ltube(P, 6, 12, 40 + j), '#FFE14A' if j != 1 else '#FFB84A', 8, (bx, by), 0.86 + 0.03 * j, 0.95 + 0.025 * j))
    # the pale creature's back line laid over the worm's foot, so it comes up out of the back
    items += ink_copy(['i0176'], B)
    return {'note': 97, 'crop': (2900, 3620, 460, 460),
            'label': 'The little pink nub on the pale creature\'s back: hold C#7 to play; it is a worm peeking out: it '
                     'bobs up and opens an eye, stretches up looking left and right, and chirps with a yellow tuft',
            'effects': [{'effect': 'vanish', 'span': [0, 0.04]},
                        {'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-98 D7: the pale blue sliver: a feather -------------------------------------------------------------------

def feather():
    INK = 10
    B, T = (3083.0, 4336.0), (3166.0, 4150.0)
    L = math.dist(B, T)
    ux, uy = (T[0] - B[0]) / L, (T[1] - B[1]) / L
    nx, ny = -uy, ux  # to the right of the shaft (x grows)

    def at(s, w):
        return (B[0] + ux * L * s + nx * w, B[1] + uy * L * s + ny * w)

    def wv(s, side):
        """the vane's width along the shaft: narrow at the base, widest a little above the middle, tapering to the
        tip; the right side a little wider"""
        prof = [(0.0, 24), (0.25, 56), (0.6, 66), (0.9, 46), (1.2, 10)]
        for (s0, w0), (s1, w1) in zip(prof, prof[1:]):
            if s <= s1:
                w = w0 + (w1 - w0) * (s - s0) / (s1 - s0)
                break
        else:
            w = prof[-1][1]
        return w * (1.0 if side > 0 else 0.86)

    SW = 0.2  # barbs sweep toward the tip

    def vane(s0, s1, side, seed):
        """one piece of vane between two splits: inner edge on the shaft from s0 to s1, swept outward toward the tip,
        its outer edge following the feather's outline, a little ragged"""
        rnd = random.Random(seed)
        j = lambda: 1 + 0.06 * (rnd.random() * 2 - 1)
        P = [at(s0, side * 3), at(s0 + SW * 0.5, side * wv(s0 + SW * 0.5, side) * 0.55),
             at(s0 + SW, side * wv(s0 + SW, side) * j())]
        for q in (0.33, 0.66):
            u = s0 + SW + (s1 - s0) * q
            P.append(at(u, side * wv(u, side) * j()))
        P += [at(s1 + SW, side * wv(s1 + SW, side) * 0.96), at(s1 + SW * 0.5, side * wv(s1 + SW * 0.5, side) * 0.5),
              at(s1, side * 3)]
        return smooth(P)

    PALE, LILAC, CYAN, PINK = '#D2F0F5', '#D7BDF7', '#9FE8F5', '#FFB7DA'
    cuts = [0.06, 0.3, 0.55, 0.78, 0.98]
    cols = {-1: [PINK, LILAC, CYAN, PALE], 1: [CYAN, PINK, LILAC, PALE]}
    wins = {-1: [(0.56, 0.7), (0.32, 0.48), (0.08, 0.24), (0.0, 0.05)],
            1: [(0.64, 0.78), (0.44, 0.6), (0.18, 0.34), (0.0, 0.05)]}
    items = []
    for side in (-1, 1):
        for i in range(4):
            s0, s1 = cuts[i], cuts[i + 1]
            s, e = wins[side][i]
            items.append(it(vane(s0, s1, side, 980 + i + 10 * side), cols[side][i], INK, at((s0 + s1) / 2, side * 3), s, e))
    # the tip curls over to the right
    TC = g.bez(at(0.94, 0), at(1.14, 0), at(1.24, 26), at(1.15, 52), 14)
    items.append(it(ltube(TC, 8, 6, 3), PALE, INK, TC[0], 0.74, 0.88))
    # the shaft, the painted sliver, laid back over the vanes with its ink
    items.append(it(m.FILLS['f041'], PALE, 0, B, 0.0, 0.002))
    items += ink_copy([s for s in m.own_ink('f041')], B)
    # a fluffy down tuft at its base
    down = [pair(lump(B[0] + dx, B[1] + dy, r, r * 0.85, 0, 70 + j, 0.1, 14), '#FFFFFF', B, 0.84 + 0.04 * j, 0.94 + 0.02 * j, INK - 1)
            for j, (dx, dy, r) in enumerate(((-26, 4, 24), (18, 10, 22), (-6, 28, 22), (-32, 28, 17)))]
    items += [q[0] for q in down] + [q[1] for q in down]
    return {'note': 98, 'crop': (2900, 3990, 460, 460),
            'label': 'The pale blue sliver across the pink creature\'s legs: hold D7 to play; it is a quill: candy vanes '
                     'unfurl down both sides, its tip curls over and a fluffy down tuft puffs out at its base',
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-99 D#7: the bean in the narwhal's mouth: it sprouts -------------------------------------------------------

def sprout():
    INK = 10
    STEM, LEAF, LEAF2, LEAF3, ROOT = '#5FCB45', '#7FE06A', '#B6F28A', '#4DBA3C', '#F6ECCB'
    R = g.bez((2108, 4140), (2104, 4172), (2098, 4196), (2076, 4212), 12)
    root = it(ltube(R, 13, 8, 1), ROOT, INK, R[0], 0.0, 0.05)
    base = (2138, 4092)
    H = g.bez(base, (2160, 4040), (2205, 4010), (2222, 4046), 18)          # the crook: a seedling's bent neck
    S = g.bez(base, (2165, 4045), (2215, 4010), (2246, 3962), 20)          # straightened up
    hook = it(ltube(H, 13, 11, 2), STEM, INK, base, 0.03, 0.25, out=(0.36, 0.42))
    stem = it(ltube(S, 14, 11, 3), STEM, INK, base, 0.36, 0.5)
    tx, ty = S[-1]
    leaves = [it(lump(tx - 40, ty - 18, 42, 22, 20, 4), LEAF, INK, (tx, ty), 0.48, 0.6),
              it(lump(tx + 40, ty - 14, 44, 23, -22, 5), LEAF2, INK, (tx, ty), 0.56, 0.68)]
    SP = [(tx + 4, ty - 4)] + g.spiral(tx + 30, ty - 30, math.radians(-30), 30, 1.4, 0.7, -1, 30)
    tendril = it(ltube(SP, 8, 6, 6), STEM, 9, (tx, ty), 0.68, 0.84)
    LF = [(tx - 4, ty - 8), (tx - 34, ty - 50), (tx - 30, ty - 102), (tx - 4, ty - 128), (tx + 16, ty - 92), (tx + 14, ty - 44)]
    big = it(smooth(LF), LEAF3, INK, (tx, ty), 0.8, 1.0)
    vein = it(ltube(g.bez((tx - 4, ty - 20), (tx - 10, ty - 60), (tx - 10, ty - 90), (tx - 8, ty - 110), 10), 4, 2, 7),
              '#A8EE7A', 0, (tx, ty), 0.86, 1.0)
    items = [root, hook, stem, tendril, big, vein] + leaves
    items += ink_copy(m.own_ink('f246'), base)
    return {'note': 99, 'crop': (1900, 3780, 460, 460),
            'label': 'The olive bean in the narwhal\'s mouth: hold D#7 to play; it sprouts: a root pokes out, a shoot '
                     'loops up and straightens, two seed leaves open, then a curly tendril and a big leaf',
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


# ---- note-101 F7: the pink foot at the end of the green leg: tap dance ---------------------------------------------

def tap_dance():
    INK, PINK = 12, '#F7A19E'
    ank = (3066.0, 4452.0)  # where the foot meets the round end of the green leg

    def foot(ang, ln, w1, seed):
        """the foot as a lumpy limb from the ankle, turned ang degrees from hanging straight down (negative: the toe
        swings out to the right), its toe curling up a little"""
        a = math.radians(ang)
        dx, dy = -math.sin(a), math.cos(a)
        nx, ny = -dy, dx
        P = g.bez(ank, (ank[0] + dx * ln * 0.4, ank[1] + dy * ln * 0.4),
                  (ank[0] + dx * ln * 0.8 - nx * 6, ank[1] + dy * ln * 0.8 - ny * 6),
                  (ank[0] + dx * ln - nx * 12, ank[1] + dy * ln - ny * 12), 16)
        return ltube(P, 17, w1, seed)

    def pose(d, s, e, out=None):
        return it(d, PINK, INK, ank, s, e, out=out)

    # the painted foot and its outline are hidden under a patch of the lime wash it stands on
    patch = it(lump(3062, 4482, 52, 52, 0, 7, 0.04), '#7BED59', 0, (3062, 4482), 0.0, 0.002)
    gx, gy = 3064.0, 4518.0
    stars = [
        it(star(gx, gy, 82, 50, 6, 90, 0.74, 1), '#FFE14A', 10, (gx, gy), 0.21, 0.27, out=(0.45, 0.5)),
        it(star(gx, gy, 96, 58, 7, 90, 0.7, 2), '#FF7FC8', 11, (gx, gy), 0.62, 0.72, out=(0.84, 0.88)),
        it(star(gx, gy, 60, 36, 6, 60, 0.7, 3), '#FFE14A', 10, (gx, gy), 0.64, 0.74, out=(0.84, 0.88)),
        it(star(gx, gy - 4, 124, 74, 8, 90, 0.6, 4), '#7FE8F5', 12, (gx, gy), 0.84, 0.96),
        it(star(gx, gy - 4, 92, 56, 7, 64, 0.62, 5), '#FF7FC8', 11, (gx, gy), 0.86, 0.98),
        it(star(gx, gy - 6, 56, 34, 6, 90, 0.66, 6), '#FFE14A', 10, (gx, gy), 0.88, 1.0),
    ]
    feet = [
        pose(foot(-55, 62, 28, 1), 0.0, 0.05, (0.2, 0.24)),       # flick up
        pose(foot(0, 54, 32, 2), 0.21, 0.26, (0.43, 0.47)),        # tap
        pose(foot(-88, 66, 29, 3), 0.43, 0.49, (0.6, 0.64)),       # kick higher
        pose(foot(4, 56, 34, 4), 0.61, 0.66, (0.76, 0.8)),         # tap
        pose(foot(-70, 64, 29, 5), 0.76, 0.8, (0.84, 0.87)),       # flick
        pose(foot(0, 58, 36, 6), 0.84, 0.88),                       # stomp
    ]
    flick = [it(g.crescent(ank[0] + 40, ank[1], 96, 10, 60, 18), '#FFFFFF', 9, ank, 0.46, 0.52, out=(0.6, 0.64))]
    cres = [it(g.crescent(ank[0], ank[1] + 20, r, a0, a1, 18), '#FFFFFF', 9, (ank[0], ank[1] + 20), s, s + 0.1)
            for r, a0, a1, s in ((122, 145, 192, 0.88), (122, -12, 35, 0.9))]
    items = [patch] + stars + flick + feet + cres + ink_copy(['i0173'], ank)
    return {'note': 101, 'crop': (2840, 4140, 440, 440),
            'label': 'The pink foot at the end of the purple creature\'s green leg: hold F7 to play; it tap dances: '
                     'it flicks up and taps down, kicks higher and taps again, each tap a bigger candy burst',
            'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}]}


DESIGNS = [pinocchio(), raspberry(), worm(), feather(), sprout(), tap_dance()]

if __name__ == '__main__':
    k.run(DESIGNS)
