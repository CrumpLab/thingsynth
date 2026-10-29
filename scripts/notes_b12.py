# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b12 of the note animations: notes 27, 33, 36, 69, 81, 103.

    uv run scripts/notes_b12.py           # strips and end frames
    uv run scripts/notes_b12.py 69        # one note
    uv run scripts/notes_b12.py export    # build.json for each
"""
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


# ---- drawing helpers -----------------------------------------------------------------------------------------------

def lump(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.06, n=14) -> str:
    """A lumpy hand-drawn ellipse, rotated by rot degrees."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        q = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * q, math.sin(t) * ry * q
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def puff(cx, cy, r, seed=0, bumps=7) -> str:
    """A scalloped cloud puff, like the painting's clouds: bumps round a lumpy core."""
    rnd = random.Random(seed)
    pts = []
    n = bumps * 4
    for i in range(n):
        t = i / n * 2 * math.pi + rnd.random() * 0.05
        ph = (i % 4) / 4
        rr = r * (0.86 + 0.16 * math.sin(ph * math.pi)) * (1 + 0.05 * (rnd.random() * 2 - 1))
        pts.append((cx + math.cos(t) * rr, cy + math.sin(t) * rr * 0.86))
    return smooth(pts)


def leaf(P, wmax, w0=0.0, seed=0) -> str:
    """A pointed, lumpy leaf (or limb) along the centreline P: width w0 at the root, wmax in the middle, a point at
    the tip."""
    rnd = random.Random(seed)
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = max(w0 * (1 - u), wmax * math.sin(math.pi * min(1.0, 0.15 + 0.85 * u)) ** 0.8) * (1 + 0.05 * rnd.uniform(-1, 1))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    pts = L + R[::-1][1:]
    return smooth(pts[::2] if len(pts) > 30 else pts)


def multi(*ds) -> str:
    return ''.join(ds)


def rnd2(v):
    return [round(v[0], 1), round(v[1], 1)]


def it(d, fill, edge, at, start, end, grow='scale', out=None, sweep=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': edge, 'at': rnd2(at), 'start': round(start, 4), 'end': round(end, 4), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 4), round(out[1], 4)
    if sweep:
        o['sweep'] = sweep
    return o


def merged(parts, ink) -> list[dict]:
    """Parts that should read as one shape: every outlined layer (double-width ink) first, then every fill-only layer
    over them, so only the outer half of each outline shows and the joins vanish."""
    return [{**q, 'edge': ink * 2} for q in parts] + [{**q, 'edge': 0} for q in parts]


# ---- note-27 D#1: the peach band becomes a dachshund ---------------------------------------------------------------

def dachshund() -> list[dict]:
    INK = 14
    PEACH, FAR, EAR, NOSE = '#FBC79B', '#E9A57A', '#D98A5C', '#4A2A1E'
    legs = []
    # stubby legs from behind the band's lower edge: front pair (0-0.08), back pair (0.12-0.26)
    for x, top, col, s, e, sd in [(3482, 3490, FAR, 0.0, 0.07, 1), (3432, 3492, PEACH, 0.0, 0.08, 2),
                                  (3652, 3470, FAR, 0.12, 0.22, 3), (3708, 3490, PEACH, 0.14, 0.26, 4)]:
        bot = top + 112
        leg = tube(bez((x, top), (x + 2, top + 40), (x - 4, top + 70), (x - 6, bot - 14), 10), 27, 25)
        paw = lump(x - 16, bot - 4, 36, 20, 0, sd)
        legs += [it(leg, col, INK, (x, top), s, e, 'y'), it(paw, col, INK, (x, top), s, e, 'y')]
    # the head rears up out of the band's left end on a neck (0.26-0.5)
    root = (3405, 3470)
    neck = tube(bez(root, (3370, 3436), (3326, 3404), (3284, 3372), 12), 52, 50)
    head = lump(3248, 3350, 100, 72, -14, 5, 0.05)
    snout = lump(3146, 3390, 88, 47, 12, 6, 0.05)
    hd = merged([it(neck, PEACH, 0, root, 0.26, 0.48), it(head, PEACH, 0, root, 0.28, 0.5),
                 it(snout, PEACH, 0, root, 0.3, 0.5)], INK)
    nose = it(lump(3066, 3406, 27, 22, 10, 7), NOSE, 12, (3066, 3406), 0.42, 0.52)
    # a long floppy ear drops from the back of its head (0.46-0.6)
    ear = it(leaf(bez((3292, 3296), (3336, 3332), (3340, 3420), (3318, 3486), 14), 42, 30, 8), EAR, INK,
             (3292, 3296), 0.46, 0.6)
    # a sleepy eye (0.52-0.64) whose lid lifts (0.66-0.8)
    ex, ey = 3208, 3322
    eye_w = it(lump(ex, ey, 29, 25, -10, 9, 0.04), '#FFFFFF', 11, (ex, ey), 0.52, 0.62)
    iris = it(lump(ex - 5, ey + 2, 16, 17, 0, 10, 0.04), '#5B3216', 0, (ex, ey), 0.52, 0.62)
    glint = it(lump(ex - 8, ey - 4, 4.5, 4.5, 0, 11, 0.02), '#FFFFFF', 0, (ex, ey), 0.6, 0.66)
    lid = it(f'M{p(ex - 34, ey + 2)}C{p(ex - 32, ey - 36)} {p(ex + 32, ey - 36)} {p(ex + 34, ey + 2)}'
             f'C{p(ex + 12, ey + 9)} {p(ex - 14, ey + 9)} {p(ex - 34, ey + 2)}Z', PEACH, 11, (ex, ey - 22), 0.52, 0.62,
             out=(0.66, 0.8))
    # its mouth opens, panting, a pink tongue lolling out (0.78-0.94)
    mouth = it(lump(3140, 3428, 48, 17, 14, 12, 0.05), '#6E1F2C', 11, (3160, 3420), 0.78, 0.88)
    tongue = it(leaf(bez((3146, 3430), (3142, 3462), (3132, 3494), (3124, 3520), 10), 25, 21, 13), '#FF6F9A', 11,
                (3146, 3430), 0.82, 0.94)
    # its tail (the orange arch in its ring) wags: two motion crescents round the arch's top (0.88-1)
    wag = [it(g.crescent(3935, 3300, r, a0, a1, 44), '#FFFFFF', 12, (3935, 3300), s, e)
           for r, a0, a1, s, e in [(140, 96, 160, 0.88, 0.96), (146, 22, 84, 0.92, 1.0)]]
    return legs + hd + [nose, ear, eye_w, iris, glint, lid, mouth, tongue] + wag


# ---- note-33 A1: the big-eye creature's pink snout sneezes ---------------------------------------------------------

def sneeze() -> list[dict]:
    INK = 14
    PINK, DEEP = '#FFA6DA', '#EE72B6'
    N = (4020, 3104)  # the nostrils at its tip
    # it wrinkles: crease crescents pop on top of the snout (0-0.06, a third at 0.4)
    creases = [it(g.crescent(cx, cy, r, a0, a1, 24), DEEP, 11, (cx, cy - r), s, e)
               for cx, cy, r, a0, a1, s, e in [(4186, 3170, 74, 60, 120, 0.0, 0.055), (4262, 3186, 66, 62, 118, 0.02, 0.09),
                                               (4126, 3164, 62, 64, 116, 0.36, 0.46)]]
    # the tip swells up into a bulb, tilting up (0.1-0.5); a pink patch inside the snout hides the bulb's back edge
    bulb = merged([it(lump(4084, 3098, 88, 70, -20, 21, 0.05), PINK, 0, (4120, 3112), 0.1, 0.5)], INK)
    bulb.append(it(lump(4156, 3106, 44, 36, -10, 22, 0.03), PINK, 0, (4156, 3106), 0.1, 0.3))
    # nostrils open (0.26-0.4), then flare wide (0.52-0.64)
    nos = it(multi(lump(4026, 3078, 11, 17, 20, 23), lump(4040, 3124, 11, 17, 30, 24)), '#7A1E4E', 9, N, 0.26, 0.38,
             out=(0.52, 0.58))
    flare = it(multi(lump(4024, 3076, 19, 26, 20, 25), lump(4038, 3128, 19, 26, 30, 26)), '#7A1E4E', 10, N, 0.52, 0.64)
    # ACHOO: scalloped puffs blast out of the nostrils to the left, the biggest last (0.66-1)
    puffs = []
    for cx, cy, r, col, s, e, sd in [(3930, 3100, 70, '#FFFFFF', 0.66, 0.74, 31), (3846, 3018, 80, '#FFD6EC', 0.69, 0.78, 32),
                                     (3850, 3196, 76, '#C9F5E3', 0.71, 0.8, 33), (3730, 3104, 116, '#FFFFFF', 0.74, 0.86, 34),
                                     (3712, 2940, 86, '#FFFFFF', 0.78, 0.9, 35), (3712, 3268, 80, '#FFF3B0', 0.8, 0.92, 36),
                                     (3578, 3060, 122, '#FFFFFF', 0.84, 1.0, 37), (3590, 2888, 76, '#CFEFFF', 0.88, 1.0, 38),
                                     (3584, 3236, 82, '#FFD6EC', 0.9, 1.0, 39)]:
        puffs.append(it(puff(cx, cy, r, sd, 6 if r >= 90 else 5), col, INK - 2, N, s, e))
    # blast streaks out of the nostrils and flecks of spray (0.68-1)
    flecks = [it(multi(*[lump(x, y, 15, 12, 0, 50 + i) for i, (x, y) in enumerate(pts)]), col, 9, N, s, e)
              for pts, col, s, e in [([(3880, 2900), (3800, 3330), (3440, 3000)], '#FF7FC4', 0.8, 0.95),
                                     ([(3960, 2960), (3640, 2780), (3450, 3170)], '#5FE0F0', 0.84, 0.98),
                                     ([(3960, 3250), (3500, 3330), (3470, 2860)], '#FFE14D', 0.88, 1.0)]]
    return creases + bulb + [nos, flare] + puffs + flecks


# ---- note-36 C2: a mouse comes out of the arched hole ------------------------------------------------------------

def mouse() -> list[dict]:
    INK = 13
    FUR, PALE, PINKIN, NOSE = '#B9AFD2', '#DCD5EA', '#F7A6C8', '#FF6FAE'
    cx = 2877
    # ears pop up in the hole (0-0.07)
    ears = []
    for ex, s, e, sd in [(2828, 0.0, 0.06, 61), (2928, 0.01, 0.075, 62)]:
        ears.append(it(lump(ex, 3680, 40, 38, 0, sd, 0.05), FUR, INK, (ex, 3710), s, e))
        ears.append(it(lump(ex, 3684, 24, 23, 0, sd + 10, 0.05), PINKIN, 0, (ex, 3710), s, e))
    # its body (0.5-0.64) and head (0.1-0.3) push out under the band; the snout pokes forward (0.2-0.36)
    body = it(lump(cx, 3826, 74, 52, 0, 63, 0.05), FUR, INK, (cx, 3760), 0.5, 0.64)
    head = it(lump(cx, 3726, 80, 60, 0, 64, 0.04), FUR, INK, (cx, 3690), 0.1, 0.3)
    snout = it(lump(cx, 3768, 42, 30, 0, 65, 0.05), PALE, INK - 2, (cx, 3740), 0.2, 0.36)
    nose = it(lump(cx, 3788, 16, 13, 0, 66), NOSE, 10, (cx, 3788), 0.3, 0.4)
    # whiskers: thin outlined tapers fanning out from the snout (0.36-0.48)
    wh = []
    for sgn in (-1, 1):
        for dy, dx2, dy2 in [(-6, 78, -22), (4, 84, 2), (14, 74, 26)]:
            x0 = cx + sgn * 28
            wh.append(leaf(bez((x0, 3772 + dy), (x0 + sgn * dx2 * 0.4, 3772 + dy + dy2 * 0.3),
                               (x0 + sgn * dx2 * 0.8, 3772 + dy + dy2 * 0.8), (x0 + sgn * dx2, 3772 + dy + dy2), 8), 4.5, 4))
    whisk = it(multi(*wh), '#FFFFFF', 7, (cx, 3772), 0.36, 0.48)
    # eyes pop open (0.44-0.56)
    eyes = it(multi(lump(cx - 30, 3722, 13, 15, 0, 67, 0.03), lump(cx + 30, 3722, 13, 15, 0, 68, 0.03)), '#1E1A2C', 8,
              (cx, 3722), 0.44, 0.56)
    glints = it(multi(lump(cx - 34, 3716, 4.5, 4.5, 0, 69, 0.02), lump(cx + 26, 3716, 4.5, 4.5, 0, 70, 0.02)), '#FFFFFF', 0,
                (cx, 3722), 0.52, 0.58)
    # a fat wedge of cheese comes up in its paws (0.66-0.84), holes (0.84-0.96), paws on it (0.62-0.74)
    wedge = smooth([(2784, 3880), (2790, 3842), (2840, 3812), (2930, 3784), (2978, 3790), (2982, 3842), (2978, 3884),
                    (2880, 3888)])
    cheese = it(wedge, '#FFD84A', INK, (cx, 3880), 0.66, 0.84)
    rind = it(smooth([(2790, 3842), (2840, 3812), (2930, 3784), (2978, 3790), (2970, 3806), (2900, 3820), (2840, 3836),
                      (2800, 3852)]), '#FFEFA0', 0, (cx, 3880), 0.7, 0.86)
    holes = it(multi(lump(2840, 3858, 17, 13, 0, 71), lump(2915, 3846, 13, 11, 0, 72), lump(2950, 3868, 10, 9, 0, 73)),
               '#E4A422', 8, (cx, 3850), 0.84, 0.96)
    paws = it(multi(lump(2818, 3822, 22, 17, -20, 74), lump(2944, 3796, 22, 17, 20, 75)), PINKIN, 10, (cx, 3810), 0.62, 0.74)
    # its pink tail curls up out from behind it on the right (0.86-1)
    tail = it(tube(bez((2930, 3842), (3010, 3846), (3070, 3790), (3036, 3738), 18), 10, 6), PINKIN, 10, (2930, 3842),
              0.86, 1.0)
    return [tail] + ears + [body, head, snout, nose, whisk, eyes, glints, cheese, rind, holes, paws]


# ---- note-69 A4: the bunny's ear becomes an ear of corn ------------------------------------------------------------

def corn() -> list[dict]:
    INK = 12
    B, T = (4444.0, 3645.0), (4462.0, 3318.0)
    ln = math.hypot(T[0] - B[0], T[1] - B[1])
    ux, uy = (T[0] - B[0]) / ln, (T[1] - B[1]) / ln
    nx, ny = -uy, ux  # to the right
    ang = math.degrees(math.atan2(ny, nx))
    L = lambda s, w: (B[0] + ux * s + nx * w, B[1] + uy * s + ny * w)
    top = 372.0
    hw = lambda s: 70 * math.sin(math.pi * min(1.0, 0.5 + 0.5 * s / top)) ** 0.6 + 6 if s > 0 else 70
    rnd = random.Random(80)
    side = [L(s, hw(s) * (1 + 0.04 * rnd.uniform(-1, 1))) for s in range(-14, int(top), 34)]
    other = [L(s, -hw(s) * (1 + 0.04 * rnd.uniform(-1, 1))) for s in range(-14, int(top), 34)]
    cob = smooth(side + [L(top + 10, 0)] + other[::-1])
    items = [it(cob, '#E7A52B', INK, B, 0.0, 0.42, 'y')]
    # kernels pop up row by row from the base (0-0.4), three across, two near the tip
    for r, s in enumerate(range(22, int(top) - 20, 46)):
        w = hw(s)
        cols = (-0.63, 0.0, 0.63) if s < top - 60 else (-0.38, 0.38)
        ker = multi(*[lump(*L(s, f * w), w * (0.32 if len(cols) == 3 else 0.38), 24, ang, 90 + r * 5 + j, 0.08)
                      for j, f in enumerate(cols)])
        st = 0.045 * r
        items.append(it(ker, '#FFE04A', 10, L(s, 0), st, st + 0.07))
    # glints on the kernels (0.4-0.5)
    gl = multi(*[lump(*L(s + 6, -0.63 * hw(s) - 6), 7, 5, ang, 120 + s) for s in range(68, int(top) - 60, 92)])
    items.append(it(gl, '#FFFFFF', 0, L(200, 0), 0.4, 0.5))
    # husks: two leaves hug its sides with a green cup at its foot (0.42-0.62), then peel back and flare open
    # (0.64-0.9)
    G, DG, LITE = '#78C94A', '#5DB43F', '#B6EA6A'
    hug = [bez(L(-6, -34), L(80, -90), L(170, -80), L(262, -26), 16), bez(L(-6, 34), L(80, 88), L(160, 80), L(244, 28), 16)]
    for k2, P in enumerate(hug):
        st = 0.42 + 0.06 * k2
        items.append(it(leaf(P, 46, 12, 130 + k2), G, INK, L(-10, 0), st, st + 0.14, out=(0.66, 0.74)))
        items.append(it(leaf(P, 16, 4, 140 + k2), LITE, 0, L(-10, 0), st + 0.03, st + 0.15, out=(0.66, 0.74)))
    peel = [(bez(L(-4, -28), L(80, -130), L(60, -230), L(-30, -262), 16), 50, DG, 0.64),
            (bez(L(-4, 28), L(70, 92), L(50, 118), L(-34, 112), 16), 42, G, 0.7),
            (bez(L(-4, -10), L(110, -96), L(220, -132), L(320, -106), 16), 44, G, 0.76)]
    for k2, (P, wmax, col, st) in enumerate(peel):
        items.append(it(leaf(P, wmax, 12, 150 + k2), col, INK, L(-10, 0), st, st + 0.14))
        items.append(it(leaf(P, wmax * 0.34, 4, 160 + k2), LITE, 0, L(-10, 0), st + 0.03, st + 0.15))
    items.append(it(lump(*L(-16, 0), 62, 36, ang, 165, 0.06), DG, INK, L(-16, 0), 0.42, 0.56))
    # a silk tassel bursts from its tip (0.84-1)
    tip = L(top - 10, 0)
    strands_c, strands_p = [], []
    for j, (dw, ds, cw) in enumerate([(-96, 80, -40), (-44, 130, -20), (6, 150, 22), (52, 124, 36), (92, 76, 40)]):
        P = bez(tip, L(top + ds * 0.4, dw * 0.15), L(top + ds * 0.8, dw * 0.6 + cw * 0.3), L(top + ds, dw), 14)
        (strands_c if j % 2 == 0 else strands_p).append(leaf(P, 15, 13, 170 + j))
    items.append(it(multi(*strands_p), '#F59AB8', 10, tip, 0.84, 0.96))
    items.append(it(multi(*strands_c), '#FFE6C2', 10, tip, 0.88, 1.0))
    return items


# ---- note-81 A5: a sprout pops out of the cream cap and flowers ----------------------------------------------------

def sprout() -> list[dict]:
    INK = 11
    G, LITE, BUD, PET = '#68C04A', '#B2EC70', '#FF6FAE', '#FF9ECF'
    R = (3994.0, 3548.0)
    shoot = it(lump(R[0] + 2, R[1] - 16, 22, 28, 8, 201, 0.07), G, INK, R, 0.0, 0.05)
    P = bez(R, (3998, 3486), (4048, 3462), (4062, 3390), 18)
    stem = merged([it(tube(P, 16, 13), G, 0, R, 0.04, 0.3)], INK)
    l1 = bez((4004, 3484), (3980, 3460), (3950, 3448), (3906, 3450), 12)
    l2 = bez((4040, 3460), (4068, 3450), (4100, 3440), (4144, 3420), 12)
    leaves = [it(leaf(l1, 29, 6, 202), G, INK, (4004, 3482), 0.24, 0.42),
              it(leaf(l1, 10, 2, 203), LITE, 0, (4004, 3482), 0.28, 0.44),
              it(leaf(l2, 30, 6, 204), G, INK, (4040, 3460), 0.4, 0.58),
              it(leaf(l2, 10, 2, 205), LITE, 0, (4040, 3460), 0.44, 0.6)]
    C = (4062.0, 3352.0)
    bud = [it(lump(C[0], C[1] + 2, 26, 38, 0, 206, 0.07), BUD, INK, (C[0], C[1] + 26), 0.58, 0.74, out=(0.84, 0.92)),
           it(multi(leaf(bez((C[0], C[1] + 28), (C[0] - 14, C[1] + 16), (C[0] - 22, C[1] + 2), (C[0] - 24, C[1] - 12), 8), 9, 7, 207),
                    leaf(bez((C[0], C[1] + 28), (C[0] + 14, C[1] + 16), (C[0] + 22, C[1] + 2), (C[0] + 24, C[1] - 12), 8), 9, 7, 208)),
              G, 9, (C[0], C[1] + 28), 0.64, 0.76)]
    petals = []
    for j in range(5):
        a = math.radians(-90 + j * 72)
        rr = (42, 38, 44, 37, 41)[j]
        px, py = C[0] + math.cos(a) * rr, C[1] + math.sin(a) * rr
        st = 0.8 + 0.03 * j
        petals.append(it(lump(px, py, rr * 0.98, rr * 0.74, math.degrees(a), 210 + j, 0.12), PET if j % 2 else '#FFB3DA', INK,
                         C, st, st + 0.08))
    centre = it(lump(C[0], C[1], 22, 20, 0, 220, 0.08), '#FFE04A', INK - 1, C, 0.93, 1.0)
    return [shoot] + stem + leaves + bud[1:] + bud[:1] + petals + [centre]


# ---- note-103 G7: the thumbnail becomes a jewel beetle ------------------------------------------------------------

def beetle() -> list[dict]:
    INK = 10
    LAV, DEEP, DARK, WING = '#C681F6', '#8B4ED0', '#3E2466', '#E2F6FF'
    C = (3066.0, 3030.0)
    tilt = 13.0
    a = math.radians(tilt)
    ux, uy = math.sin(a), -math.cos(a)  # up the beetle
    nx, ny = math.cos(a), math.sin(a)  # to its right
    L = lambda s, w: (C[0] + ux * s + nx * w, C[1] + uy * s + ny * w)
    H = L(78, 0)
    # head and feelers pop out at the nail's tip (0-0.05)
    head = it(lump(*H, 29, 23, tilt, 301, 0.05), DARK, INK, L(52, 0), 0.0, 0.05)
    feel = it(multi(tube(bez(L(94, -10), L(124, -22), L(142, -50), L(132, -74), 10), 6, 5),
                    tube(bez(L(94, 10), L(124, 22), L(142, 50), L(132, 74), 10), 6, 5),
                    lump(*L(130, -78), 10, 10, 0, 304), lump(*L(130, 78), 10, 10, 0, 305)), DARK, 8, L(80, 0), 0.0, 0.06)
    # stubby legs (0.06-0.18)
    legs = []
    for sgn in (-1, 1):
        ds = [leaf(bez(L(s0, sgn * 40), L(s0 + 8, sgn * 62), L(s0 - 4, sgn * 78), L(s0 - 16, sgn * 86), 8), 7, 7, 310 + s0)
              for s0 in (30, 0, -34)]
        legs.append(it(multi(*ds), DARK, 8, L(0, 0), 0.06 + (0.03 if sgn > 0 else 0), 0.18 + (0.03 if sgn > 0 else 0),
                       out=(0.58, 0.66)))
    # the nail swells into its shell (0.12-0.3), the thorax behind the head (0.14-0.28)
    shell = it(lump(*L(-6, 0), 58, 70, tilt, 320, 0.04), LAV, INK + 1, C, 0.12, 0.3, out=(0.6, 0.68))
    thorax = it(lump(*L(56, 0), 38, 18, tilt, 321, 0.05), DEEP, INK, L(40, 0), 0.14, 0.28)
    # a seam splits it (0.3-0.42), spots come up (0.4-0.54), a shine (0.5-0.6)
    seam = it(leaf(bez(L(52, 0), L(20, 1), L(-30, -1), L(-72, 0), 12), 4, 4, 322), DARK, 6, L(52, 0), 0.3, 0.42,
              out=(0.6, 0.68))
    spots = it(multi(lump(*L(24, -28), 11, 9, tilt, 323), lump(*L(-24, -24), 13, 11, tilt, 324),
                     lump(*L(20, 28), 10, 9, tilt, 325), lump(*L(-30, 26), 12, 11, tilt, 326),
                     lump(*L(-56, -10), 8, 7, tilt, 327)), DEEP, 7, C, 0.4, 0.54, out=(0.6, 0.68))
    shine = it(lump(*L(28, -40), 7, 18, tilt + 20, 328), '#FFFFFF', 0, C, 0.5, 0.6, out=(0.6, 0.68))
    # the wing cases lift apart (0.6-0.76) over a dark body; gauzy wings flutter out (0.7-0.86), then beat wide (0.88-1)
    hinge = L(44, 0)
    abdomen = it(lump(*L(-14, 0), 34, 56, tilt, 330), '#6A3AA8', INK, hinge, 0.58, 0.68)
    wings1 = [it(leaf(bez(L(36, sgn * 10), L(10, sgn * 70), L(-40, sgn * 120), L(-90, sgn * 140), 14), 32, 14, 331 + sgn),
                 WING, 9, hinge, 0.7, 0.86, out=(0.88, 0.93)) for sgn in (-1, 1)]
    wings2 = [it(leaf(bez(L(36, sgn * 10), L(60, sgn * 70), L(70, sgn * 130), L(52, sgn * 176), 14), 38, 14, 335 + sgn),
                 WING, 9, hinge, 0.88, 0.98) for sgn in (-1, 1)]
    veins = [it(leaf(bez(L(36, sgn * 14), L(56, sgn * 70), L(62, sgn * 120), L(52, sgn * 156), 14), 10, 4, 337 + sgn),
                '#BCE3F5', 0, hinge, 0.9, 1.0) for sgn in (-1, 1)]
    cases, cspots = [], []
    for sgn in (-1, 1):
        cc = L(20, sgn * 58)
        cases.append(it(lump(*cc, 32, 66, tilt + sgn * 42, 340 + sgn, 0.04), LAV, INK, hinge, 0.6, 0.76))
        cspots.append(it(multi(lump(*L(34, sgn * 50), 10, 9, 0, 344 + sgn), lump(*L(2, sgn * 78), 12, 10, 0, 346 + sgn)),
                         DEEP, 7, hinge, 0.66, 0.78))
    flut = [it(g.crescent(*L(56, sgn * 150), 58, a0, a1, 20), '#FFFFFF', 9, L(56, sgn * 150), 0.92, 1.0)
            for sgn, a0, a1 in [(-1, 130, 215), (1, -35, 50)]]
    return ([abdomen] + wings1 + wings2 + veins + legs + [head, feel, thorax, shell, seam, spots, shine]
            + cases + cspots + flut)


DESIGNS = [
    {'note': 27,
     'label': 'The long peach band under the big-eye creature: hold D#1 to play; it turns into a dachshund: stubby legs '
              'drop under it, a floppy-eared head rears out of its left end, wakes and pants, and its orange tail wags',
     'effects': [{'effect': 'sprites', 'place': 'around', 'items': dachshund()}]},
    {'note': 33,
     'label': "The big-eye creature's pink snout, right edge: hold A1 to play; it wrinkles, swells and flares its "
              'nostrils, then sneezes a big ACHOO of candy puffs',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': sneeze()}], 'crop': (3400, 2600, 1200, 1200)},
    {'note': 36,
     'label': 'The pale blue band with the arched hole on the orange disc: hold C2 to play; a mouse peeks out of its '
              'hole, ears first, then its nose, whiskers and eyes, and comes out holding a fat wedge of cheese',
     'effects': [{'effect': 'sprites', 'place': 'around', 'items': mouse()}]},
    {'note': 69,
     'label': "The bunny's thin pink right ear: hold A4 to play; it turns into an ear of corn, kernels popping up row by "
              'row, green husks unfurling and a silk tassel bursting from its tip',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': corn()}], 'crop': (3760, 2980, 880, 880)},
    {'note': 81,
     'label': 'The cream cap on the pale pill under the peach band: hold A5 to play; a green shoot pokes out of it, '
              'unfurls two leaves and a bud that pops open into a pink flower',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': sprout()}]},
    {'note': 103,
     'label': "The coral hand's lavender thumbnail: hold G7 to play; it turns into a jewel beetle: its head and feelers "
              'pop out, its shell splits open and gauzy wings flutter out',
     'effects': [{'effect': 'sprites', 'place': 'over', 'items': beetle()}]},
]

if __name__ == '__main__':
    for d in DESIGNS:
        n = sum(len(e.get('items', [])) for e in d['effects'])
        print(f"note-{d['note']}: {n} sprite items")
    k.run(DESIGNS)
