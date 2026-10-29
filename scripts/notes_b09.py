# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b09 of the note animations: notes 28 (E1), 35 (B1), 37 (C#2), 43 (G2), 46 (A#2), 67 (G4).

    uv run scripts/notes_b09.py            # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b09.py 35         # one note
    uv run scripts/notes_b09.py export     # build.json for each
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
crescent, rot = k.g.crescent, k.g.rot_path

PINK, YELLOW, CYAN, LIME, LILAC, ORANGE = '#FF6FB5', '#FFE94A', '#57E3F5', '#B7FF5C', '#C39BFF', '#FF9F45'
WHITE = '#FFFFFF'


# ---- drawing helpers ------------------------------------------------------------------------------------------------

def closed(pts) -> str:
    """A smooth closed outline through the points (Catmull-Rom)."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def jitter(pts, seed, amt=4.0):
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in pts]


def blob(cx, cy, rx, ry, seed=0, wob=0.08, n=11, rot_deg=0.0) -> str:
    """A lumpy hand-drawn oval."""
    rnd = random.Random(seed)
    r0 = math.radians(rot_deg)
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        f = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r0) - y * math.sin(r0), cy + x * math.sin(r0) + y * math.cos(r0)))
    return closed(pts)


def limb(P, wf, seed=0, jit=0.06, cap=True, cap0=False) -> str:
    """An outlined limb along the centreline P, half-width wf(u) along it, wobbling a little between its ends (so
    pieces laid end to end meet at the same width); round cap at the end, and open (flat) at the start so it can grow
    out of something, unless cap0."""
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
        w = wf(u)
        env = math.sin(math.pi * u)
        wl, wr = w * (1 + jit * env * math.sin(u * 11 + ph1)), w * (1 + jit * env * math.sin(u * 9 + ph2))
        L.append((x + nx * wl, y + ny * wl))
        R.append((x - nx * wr, y - ny * wr))
    rr = math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1]) / 2
    end = f'A{rr:.1f} {rr:.1f} 0 0 0 {p(*R[-1])}' if cap else f'L{p(*R[-1])}'
    r0 = math.hypot(L[0][0] - R[0][0], L[0][1] - R[0][1]) / 2
    start = f'A{r0:.1f} {r0:.1f} 0 0 0 {p(*L[0])}' if cap0 else 'Z'
    return 'M' + 'L'.join(p(*q) for q in L) + end + 'L' + 'L'.join(p(*q) for q in R[::-1]) + start + ('Z' if cap0 else '')


def taper(w0, w1):
    return lambda u: w0 + (w1 - w0) * u


def I(d, fill, edge, at, s, e, grow='scale', out=None, sweep=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 4), 'end': round(e, 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    if sweep:
        x['sweep'] = {'from': sweep[0], 'to': sweep[1]}
    return x


def layered(pieces, edge):
    """Pieces of one continuous form drawn so the joins melt: each piece's outlined layer (stroke 2x, so the fill on
    top leaves the painting's width showing) goes down before the fill-only layer of the piece before it.
    pieces: [(d, fill, at, s, e)]."""
    outl = [I(d, f, edge * 2, at, s, e) for d, f, at, s, e in pieces]
    fill = [I(d, f, 0, at, s, e) for d, f, at, s, e in pieces]
    items = [outl[0]]
    for i in range(1, len(pieces)):
        items += [outl[i], fill[i - 1]]
    return items + [fill[-1]]


def tooth(x, y, w, h, deg=0.0) -> str:
    """A chunky, slightly rounded tooth with its base centred at (x, y), pointing up (h > 0) or down (h < 0)."""
    pts = [(x - w / 2, y), (x - w * 0.28, y - h * 0.55), (x, y - h), (x + w * 0.28, y - h * 0.55), (x + w / 2, y), (x, y + h * 0.12)]
    d = closed(pts)
    return rot(d, x, y, deg) if deg else d


# ---- note-28 E1: party streamer ------------------------------------------------------------------------------------

def streamer_28():
    E = 15
    tip = (4062, 1662)
    S = [
        ((4062, 1662), (4095, 1570), (4100, 1470), (4040, 1420)),
        ((4040, 1420), (3985, 1375), (3990, 1290), (3930, 1270)),
        ((3930, 1270), (3870, 1250), (3840, 1320), (3860, 1390)),
        ((3860, 1390), (3880, 1460), (3820, 1495), (3770, 1460)),
        ((3770, 1460), (3720, 1430), (3740, 1340), (3690, 1310)),
    ]
    cols = [PINK, YELLOW, CYAN, LIME, LILAC]
    wins = [(0.0, 0.06), (0.07, 0.2), (0.2, 0.33), (0.33, 0.46), (0.46, 0.58)]
    pieces = []
    for i, (seg, c, (s, e)) in enumerate(zip(S, cols, wins)):
        P = bez(*seg, n=24)
        pieces.append((limb(P, lambda u: 31, seed=28 + i, jit=0.12, cap=True), c, P[0], s, e))
    # the end curls up into a spiral
    sp = k.spiral(3690, 1310, math.radians(200), 95, 0.72, 0.6, 1, n=30)
    pieces.append((limb(sp, taper(31, 22), seed=40, jit=0.1), ORANGE, sp[0], 0.58, 0.7))
    main = layered(pieces, E)
    # a second streamer flings out of the tip up to the right at the end
    T = [((4070, 1650), (4150, 1610), (4185, 1520), (4150, 1460)),
         ((4150, 1460), (4115, 1400), (4140, 1330), (4195, 1330))]
    tp = []
    for i, (seg, c, (s, e)) in enumerate(zip(T, [CYAN, PINK], [(0.76, 0.87), (0.87, 0.97)])):
        P = bez(*seg, n=20)
        tp.append((limb(P, lambda u: 27, seed=50 + i, jit=0.12), c, P[0], s, e))
    second = layered(tp, E)
    # chunky confetti
    conf = []
    for i, (x, y, c, r, s) in enumerate([(3820, 1575, YELLOW, 25, 0.28), (4015, 1212, PINK, -30, 0.42),
                                          (3760, 1532, CYAN, 40, 0.56), (4000, 1545, LILAC, 15, 0.7)]):
        conf.append(I(blob(x, y, 28, 18, seed=60 + i, wob=0.12, n=8, rot_deg=r), c, 11, (x, y), s, s + 0.1))
    # candy bands across the wisp itself: it is crepe paper
    bands = []
    for i, (cx, cy, c) in enumerate([(4040, 1700, PINK), (3990, 1840, CYAN), (3925, 1985, PINK)]):
        pts = jitter([(cx - 180, cy - 30), (cx, cy - 20), (cx + 180, cy - 34), (cx + 180, cy + 26), (cx, cy + 34), (cx - 180, cy + 30)], 70 + i, 5)
        bands.append(I(rot(closed(pts), cx, cy, -28), c, 12, (cx, cy), 0.64 + 0.06 * i, 0.74 + 0.06 * i, grow='x'))
    return [
        {'effect': 'sprites', 'place': 'on', 'items': bands},
        {'effect': 'sprites', 'place': 'over', 'items': main + second + conf},
    ]


# ---- note-35 B1: crocodile -----------------------------------------------------------------------------------------

def croc_35():
    E = 14
    OLIVE, DARK = '#86A94A', '#6A8C38'
    piv = (3700, 2792)
    # skin: the band turns to crocodile green with lumpy scales (clipped to the band)
    skin = [I('M3400 2640L4020 2640L4020 3020L3400 3020Z', OLIVE, 0, (3700, 2850), 0.05, 0.28, grow='x')]
    for i, (x, y, rx, ry) in enumerate([(3520, 2848, 34, 16), (3610, 2858, 30, 15), (3730, 2730, 30, 22),
                                        (3800, 2900, 40, 20), (3900, 2925, 34, 18)]):
        skin.append(I(blob(x, y, rx, ry, seed=350 + i, wob=0.15, n=9), DARK, 10, (x, y), 0.12 + 0.03 * i, 0.3 + 0.03 * i))
    # tail curls up off the right end
    tailP = bez((3950, 2968), (4010, 3000), (4085, 2985), (4095, 2925), n=20) + \
        bez((4095, 2925), (4100, 2885), (4060, 2875), (4045, 2900), n=10)[1:]
    tail = layered([(limb(tailP, taper(32, 13), seed=36, jit=0.1), OLIVE, tailP[0], 0.38, 0.54)], E)
    tail.append(I(blob(3958, 2972, 26, 20, seed=360, wob=0.05), OLIVE, 0, (3958, 2972), 0.38, 0.46))
    # upper jaw: closed lumpy shape over the band's top edge, opened in two poses round the hinge
    top = [(3705, 2748), (3630, 2752), (3550, 2768), (3475, 2782), (3428, 2796)]
    bot = [(3432, 2826), (3500, 2822), (3580, 2808), (3650, 2798), (3712, 2796)]
    jaw = closed(jitter(top + [(3410, 2812)] + bot, 37, 3))
    nost = blob(3442, 2792, 20, 14, seed=38, wob=0.1, n=8)
    j1 = [I(rot(jaw, *piv, 9), OLIVE, E, piv, 0.5, 0.62, out=(0.64, 0.7)),
          I(rot(nost, *piv, 9), OLIVE, 11, piv, 0.5, 0.62, out=(0.64, 0.7))]
    j2 = [I(rot(jaw, *piv, 25), OLIVE, E, piv, 0.63, 0.77), I(rot(nost, *piv, 25), OLIVE, 11, piv, 0.63, 0.77)]
    # the mouth: pink between the open jaw and the band's top edge
    ub = [k.g.rot_path(f'M{p(*q)}', *piv, 25) for q in bot[::-1]]
    ubp = [tuple(float(v) for v in s[1:].split()) for s in ub]
    lower = [(3440, 2832), (3470, 2818), (3546, 2833), (3588, 2800), (3640, 2798), (3690, 2800)]
    mouth = I(closed(ubp + lower), '#FF7FA8', 12, piv, 0.55, 0.77)
    throat = I(blob(3640, 2770, 40, 24, seed=39, rot_deg=-20), '#B0305E', 0, piv, 0.6, 0.77)
    lt = [I(tooth(x, y, 26, 30), WHITE, 10, (x, y), 0.76 + 0.025 * i, 0.86 + 0.025 * i)
          for i, (x, y) in enumerate([(3478, 2822), (3530, 2828), (3600, 2802), (3655, 2796)])]
    upts = [tuple(float(v) for v in k.g.rot_path(f'M{x} {y}', *piv, 25)[1:].split()) for x, y in
            [(3480, 2826), (3540, 2818), (3600, 2808), (3660, 2800)]]
    ut = [I(tooth(x, y, 26, -30, 25), WHITE, 10, (x, y), 0.78 + 0.025 * i, 0.88 + 0.025 * i) for i, (x, y) in enumerate(upts)]
    # the eye bump on the band's raised lobe: it lifts sleepy, then the lid goes up off a slit-pupilled yellow eye
    ex, ey = 3730, 2668
    eye = [I(blob(ex, ey + 4, 54, 40, seed=31, wob=0.07), OLIVE, E, (ex, ey + 30), 0.0, 0.05),
           I(blob(ex, ey + 2, 32, 24, seed=32, wob=0.05), '#FFD93A', 10, (ex, ey), 0.0, 0.05),
           I(blob(ex + 2, ey + 2, 7, 19, seed=33, wob=0.05), '#000', 0, (ex, ey), 0.02, 0.06),
           I(blob(ex, ey - 8, 38, 22, seed=34, wob=0.05), OLIVE, 10, (ex, ey - 20), 0.0, 0.05, out=(0.24, 0.38))]
    over = tail + [mouth, throat] + lt + j1 + j2 + ut + eye
    return [
        {'effect': 'sprites', 'place': 'on', 'items': skin},
        {'effect': 'sprites', 'place': 'over', 'items': over},
    ]


# ---- note-37 C#2: sea sharp ----------------------------------------------------------------------------------------

def shark_37():
    E = 13
    VIO, BELLY, DEEP, SPLASH = '#9B6FE0', '#EEDDFF', '#5A1F5A', '#BFF4FF'
    base = (4095, 2532)
    C = bez(base, (4085, 2400), (4010, 2305), (3880, 2330), n=30)

    def frame(u):
        i = min(len(C) - 2, int(u * (len(C) - 1)))
        (x0, y0), (x1, y1) = C[i], C[i + 1]
        f = u * (len(C) - 1) - i
        x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        d = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / d, (y1 - y0) / d
        return (x, y), (tx, ty), (-ty, tx)  # point, tangent (toward the nose), normal (the back, outside the arc)

    W = lambda u: 24 + 46 * math.sin(math.pi * u ** 0.75)

    def L(u, s):
        (x, y), _, (nx, ny) = frame(u)
        return (x + nx * W(u) * s, y + ny * W(u) * s)

    def ang(v):  # rotation that turns an upward tooth to point along v
        return math.degrees(math.atan2(v[0], -v[1]))

    body = limb(C, W, seed=371, jit=0.05)
    belly = closed([L(u, -0.82) for u in (0.18, 0.35, 0.55, 0.75, 0.9)] + [L(u, -0.2) for u in (0.86, 0.65, 0.45, 0.25)])
    # the first arrival: a fin pops up above the horizon line, the triangle's point tipped up
    fin0 = closed(jitter([(3995, 2512), (4040, 2405), (4068, 2418), (4100, 2512)], 372, 2))
    _, (tx, ty), (nx, ny) = frame(0.5)
    fb0, fb1 = L(0.4, 0.85), L(0.62, 0.85)
    ftip = (fb0[0] + nx * 105 - tx * 45, fb0[1] + ny * 105 - ty * 45)
    dorsal = closed([fb0, ((fb0[0] + ftip[0]) / 2 + nx * 4 + tx * 12, (fb0[1] + ftip[1]) / 2 + ny * 4 + ty * 12), ftip,
                     ((ftip[0] + fb1[0]) / 2 + tx * 6 - nx * 6, (ftip[1] + fb1[1]) / 2 + ty * 6 - ny * 6), fb1])
    _, (tx, ty), (nx, ny) = frame(0.64)
    pb0, pb1 = L(0.58, -0.8), L(0.7, -0.8)
    ptip = (pb0[0] - nx * 80 - tx * 45, pb0[1] - ny * 80 - ty * 45)
    pect = closed([pb0, ptip, ((ptip[0] + pb1[0]) / 2 - nx * 4 + tx * 10, (ptip[1] + pb1[1]) / 2 - ny * 4 + ty * 10), pb1])
    tail = closed(jitter([(4070, 2525), (4062, 2580), (4030, 2652), (4084, 2598), (4100, 2578), (4126, 2592),
                          (4165, 2612), (4134, 2552), (4120, 2525)], 373, 2))
    # the grin: an open dark mouth under the snout with chunky teeth top and bottom
    (mx, my), (tx, ty), (nx, ny) = frame(0.86)
    mx, my = mx - nx * 16, my - ny * 16
    mdeg = math.degrees(math.atan2(ty, tx))
    mouth = blob(mx, my, 44, 21, seed=374, wob=0.06, rot_deg=mdeg)
    teeth = []
    for j, kk in enumerate((-1.3, -0.1, 1.1)):
        x, y = mx + nx * 14 + tx * kk * 22, my + ny * 14 + ty * kk * 22
        teeth.append(I(tooth(x, y, 17, 19, ang((-nx, -ny))), WHITE, 8, (x, y), 0.66 + 0.03 * j, 0.76 + 0.03 * j))
    for j, kk in enumerate((-0.7, 0.5)):
        x, y = mx - nx * 14 + tx * kk * 22, my - ny * 14 + ty * kk * 22
        teeth.append(I(tooth(x, y, 17, 17, ang((nx, ny))), WHITE, 8, (x, y), 0.7 + 0.03 * j, 0.8 + 0.03 * j))
    ex, ey = L(0.8, 0.38)
    # the leap: a splash crown at the waterline round its tail, then drops flying
    sx, sy = base
    top = []
    for i in range(9):
        x = sx + 125 - i * 31
        h = (64 if i % 2 else 20) * (1 - abs(i - 4) / 7)
        top.append((x, sy - 6 - h))
    splash = closed(jitter([(sx + 128, sy + 10)] + top + [(sx - 128, sy + 10), (sx, sy + 22)], 377, 3))
    drops = [I(blob(x, y, 16, 20, seed=390 + i), SPLASH, 10, (x, y), 0.86 + 0.04 * i, 0.94 + 0.02 * i)
             for i, (x, y) in enumerate([(3955, 2445), (4235, 2440), (4195, 2370)])]
    items = [
        I(fin0, VIO, E, (4045, 2512), 0.0, 0.05, out=(0.18, 0.28)),
        I(tail, VIO, E, base, 0.4, 0.52),
        I(dorsal, VIO, E, fb0, 0.3, 0.42),
        I(pect, VIO, 11, pb0, 0.45, 0.55),
        I(body, VIO, E, base, 0.12, 0.4, sweep=(30, 215)),
        I(belly, BELLY, 0, base, 0.16, 0.44, sweep=(30, 215)),
        I(blob(ex, ey, 20, 20, seed=375), WHITE, 10, (ex, ey), 0.5, 0.6),
        I(blob(ex - 5, ey + 1, 10, 10, seed=376), '#000', 0, (ex, ey), 0.53, 0.62),
        I(mouth, DEEP, 11, (mx, my), 0.58, 0.7),
    ] + teeth + [I(splash, SPLASH, 11, base, 0.78, 0.92)] + drops
    return [{'effect': 'sprites', 'place': 'over', 'items': items}]


# ---- note-43 G2: meerkat on lookout ------------------------------------------------------------------------------

def meerkat_43():
    E = 13
    TAN, DTAN, BELLY, PATCH = '#D9A35F', '#B9824A', '#F7E2B0', '#5A3A22'
    hx, hy = 4440, 2400
    body = closed(jitter([(4402, 2745), (4392, 2660), (4404, 2570), (4418, 2490), (4446, 2448), (4478, 2488),
                          (4498, 2570), (4512, 2660), (4510, 2745), (4456, 2768)], 431, 3))
    head = closed(jitter([(hx - 50, hy - 6), (hx - 40, hy - 36), (hx, hy - 46), (hx + 40, hy - 36), (hx + 50, hy - 6),
                          (hx + 30, hy + 30), (hx, hy + 50), (hx - 30, hy + 30)], 432, 2))
    tailP = bez((4495, 2735), (4560, 2720), (4565, 2610), (4535, 2545), n=20)
    items = [
        I(limb(tailP, taper(17, 7), seed=433), DTAN, E, tailP[0], 0.55, 0.7),
        I(body, TAN, E, (4456, 2765), 0.06, 0.28, grow='y'),
        I(blob(4456, 2640, 36, 92, seed=434, wob=0.05), BELLY, 0, (4456, 2765), 0.22, 0.4, grow='y'),
        I(blob(4425, 2760, 26, 12, seed=435), DTAN, 11, (4425, 2760), 0.22, 0.32),
        I(blob(4490, 2764, 26, 12, seed=436), DTAN, 11, (4490, 2764), 0.24, 0.34),
        # the head pops at the sliver's tip first, ears and nose with it
        I(blob(hx - 42, hy - 34, 16, 14, seed=437), DTAN, 11, (hx, hy), 0.0, 0.05),
        I(blob(hx + 42, hy - 34, 16, 14, seed=438), DTAN, 11, (hx, hy), 0.0, 0.05),
        I(head, TAN, E, (hx, hy), 0.0, 0.05),
        I(blob(hx, hy + 38, 11, 8, seed=439), '#3B2416', 0, (hx, hy), 0.0, 0.05),
        # dark eye patches and bright eyes
        I(blob(hx - 20, hy + 4, 15, 19, seed=440, rot_deg=25), PATCH, 0, (hx - 20, hy + 4), 0.26, 0.36),
        I(blob(hx + 20, hy + 4, 15, 19, seed=441, rot_deg=-25), PATCH, 0, (hx + 20, hy + 4), 0.28, 0.38),
        I(blob(hx - 19, hy + 2, 8, 8, seed=442), '#000', 0, (hx - 19, hy + 2), 0.32, 0.42),
        I(blob(hx + 19, hy + 2, 8, 8, seed=443), '#000', 0, (hx + 19, hy + 2), 0.34, 0.44),
        I(blob(hx - 16, hy - 1, 3.5, 3.5, seed=444), WHITE, 0, (hx - 16, hy - 1), 0.36, 0.44),
        I(blob(hx + 22, hy - 1, 3.5, 3.5, seed=445), WHITE, 0, (hx + 22, hy - 1), 0.38, 0.46),
        # paws fold on its chest
        I(limb([(4418, 2500), (4432, 2530), (4450, 2556)], taper(15, 13), seed=446, cap0=True), TAN, 11, (4418, 2500), 0.44, 0.56),
        I(limb([(4496, 2500), (4482, 2530), (4464, 2556)], taper(15, 13), seed=447, cap0=True), TAN, 11, (4496, 2500), 0.48, 0.6, out=(0.72, 0.8)),
        # then it raises a paw to shade its eyes, looking out over the cone
        I(limb(bez((4492, 2505), (4520, 2470), (4510, 2400), (4478, 2378), n=12), taper(15, 13), seed=448, cap0=True), TAN, 11, (4492, 2505), 0.74, 0.88),
        I(blob(hx + 18, hy - 22, 34, 13, seed=449, rot_deg=-12), TAN, 11, (hx + 40, hy - 26), 0.82, 0.92),
    ]
    return [{'effect': 'sprites', 'place': 'over', 'items': items}]


# ---- note-46 A#2: frog tongue catches a fly ------------------------------------------------------------------------

def tongue_46():
    E = 13
    TONGUE = '#FF7580'
    fx, fy = 2884, 1916
    T1 = bez((3048, 2250), (3012, 2205), (2992, 2150), (2976, 2100), n=16)
    T2 = bez((2976, 2100), (2962, 2050), (2948, 2010), (2918, 1985), n=16)
    curl = k.spiral(2918, 1985, math.radians(165), 46, 0.7, 0.5, -1, n=20)
    tongue = layered([(limb(T1, taper(30, 27), seed=461), TONGUE, T1[0], 0.0, 0.05),
                      (limb(T2, taper(27, 24), seed=462), TONGUE, T2[0], 0.3, 0.46),
                      (limb(curl, taper(24, 18), seed=463), TONGUE, curl[0], 0.48, 0.64)], E)
    # a big candy fly buzzes in (drawn at 1.35x round its centre)
    Z = 1.35
    q = lambda dx, dy: (fx + dx * Z, fy + dy * Z)
    fly = [
        I(blob(*q(-22, -42), 46 * Z, 26 * Z, seed=464, rot_deg=-35), '#E9D8FF', 11, (fx, fy), 0.06, 0.2),
        I(blob(*q(26, -44), 44 * Z, 25 * Z, seed=465, rot_deg=30), '#E9D8FF', 11, (fx, fy), 0.08, 0.22),
        I(blob(fx, fy, 42 * Z, 30 * Z, seed=466), '#43C6E8', E, (fx, fy), 0.05, 0.18),
        I(blob(*q(-6, 4), 9 * Z, 26 * Z, seed=467, rot_deg=10), '#FF4FA0', 0, (fx, fy), 0.1, 0.22),
        I(blob(*q(16, 2), 8 * Z, 24 * Z, seed=468, rot_deg=10), '#FF4FA0', 0, (fx, fy), 0.12, 0.24),
        I(blob(*q(-44, -6), 24 * Z, 22 * Z, seed=469), '#2A5D8A', 11, (fx, fy), 0.06, 0.18),
        I(blob(*q(-50, -10), 9 * Z, 9 * Z, seed=470), WHITE, 0, (fx, fy), 0.14, 0.24),
    ]
    # a fill-only patch melts the tongue's root into the painted tongue
    root = [I(blob(3058, 2262, 34, 22, seed=475, wob=0.04, rot_deg=-40), TONGUE, 0, (3058, 2262), 0.0, 0.05)]
    ex, ey = 3285, 2112
    face = [
        I(blob(ex, ey, 30, 34, seed=471), WHITE, 11, (ex, ey), 0.66, 0.78),
        I(blob(ex - 10, ey - 8, 14, 15, seed=472), '#000', 0, (ex, ey), 0.7, 0.8),
        I(blob(ex - 15, ey - 14, 5, 5, seed=473), WHITE, 0, (ex, ey), 0.72, 0.82),
        I(blob(3352, 2196, 26, 16, seed=474), '#FF8FB8', 0, (3352, 2196), 0.74, 0.86),
    ]
    flap = [I(crescent(fx, fy - 20, r, a0, a1, 24), WHITE, 10, (fx, fy - 20), 0.86 + 0.05 * i, 0.96 + 0.04 * i)
            for i, (r, a0, a1) in enumerate([(125, 115, 160), (125, 25, 70)])]
    return [{'effect': 'sprites', 'place': 'over', 'items': fly + tongue + root + face + flap}]


# ---- note-67 G4: candy bunting -------------------------------------------------------------------------------------

def bunting_67():
    E = 11
    RIB = '#E8408F'
    sw1 = ((2990, 2700), (3040, 2762), (3140, 2762), (3194, 2690))
    sw2 = ((3196, 2688), (3238, 2742), (3318, 2742), (3366, 2684))

    def swag(seg, at, a0, a1, s, e, seed):
        P = bez(*seg, n=24)
        return P, I(limb(P, lambda u: 8, seed=seed, jit=0.1, cap=False), RIB, 9, at, s, e, sweep=(a0, a1))

    P1, r1 = swag(sw1, (3092, 2420), -117, -62, 0.0, 0.3, 671)
    P2, r2 = swag(sw2, (3281, 2430), -116, -60, 0.4, 0.58, 672)

    def pennant(P, u, col, s, seed):
        i = int(u * (len(P) - 1))
        a, b = P[max(0, i - 3)], P[min(len(P) - 1, i + 3)]
        (x, y) = P[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        tx, ty = dx / d, dy / d
        A, B = (x - tx * 36, y - ty * 36 + 4), (x + tx * 36, y + ty * 36 + 4)
        C = (x + 3, y + 96)
        pts = jitter([A, ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2 + 3), B, ((B[0] + C[0]) / 2 + 2, (B[1] + C[1]) / 2), C,
                      ((A[0] + C[0]) / 2 - 2, (A[1] + C[1]) / 2)], seed, 2.5)
        lerp = lambda P0, P1, f: (P0[0] + (P1[0] - P0[0]) * f, P0[1] + (P1[1] - P0[1]) * f)
        band = closed([lerp(A, C, 0.3), lerp(B, C, 0.3), lerp(B, C, 0.5), lerp(A, C, 0.5)])
        return [I(closed(pts), col, E, (x, y), s, s + 0.1), I(band, '#FFF6D0', 0, (x, y), s + 0.03, s + 0.12)]

    pens = []
    for P, u, col, s, seed in [(P1, 0.2, PINK, 0.0, 673), (P1, 0.5, YELLOW, 0.13, 674), (P1, 0.8, CYAN, 0.26, 675),
                               (P2, 0.32, LIME, 0.52, 676), (P2, 0.72, LILAC, 0.64, 677)]:
        pens += pennant(P, u, col, s, seed)
    # the first pennant must show at a tap, so its stretch of ribbon comes with it
    rx, ry = 3196, 2672
    rosette = [
        I(limb(bez((rx - 6, ry + 10), (rx - 20, ry + 50), (rx - 30, ry + 80), (rx - 22, ry + 108), n=10), taper(13, 11), seed=678, cap=False), '#FF4FA0', E, (rx, ry), 0.8, 0.9),
        I(limb(bez((rx + 6, ry + 10), (rx + 20, ry + 50), (rx + 34, ry + 76), (rx + 30, ry + 104), n=10), taper(13, 11), seed=679, cap=False), '#FF4FA0', E, (rx, ry), 0.82, 0.92),
        I(closed([(rx + math.cos(a) * (44 + 8 * math.cos(9 * a)), ry + math.sin(a) * (44 + 8 * math.cos(9 * a)))
                  for a in [i / 36 * 2 * math.pi for i in range(36)]]), '#FF4FA0', E, (rx, ry), 0.84, 0.96),
        I(blob(rx, ry, 20, 20, seed=680), YELLOW, 10, (rx, ry), 0.88, 1.0),
    ]
    return [{'effect': 'sprites', 'place': 'over', 'items': [r1, r2] + pens + rosette}]


DESIGNS = [
    {'note': 28, 'label': "The pale yellow wisp behind the acorn frog: hold E1 to play; it curls into a candy crepe "
                          "streamer that unrolls in waves over the pyramid, confetti flying, bands of colour come up on "
                          "it and a second streamer flings out",
     'effects': streamer_28(), 'crop': (3450, 1150, 1000, 1000)},
    {'note': 35, 'label': "The dusky band under the blue fish: hold B1 to play; it wakes as a crocodile, its eye "
                          "lifting and opening, its tail curling up, and its jaws gape in a toothy grin",
     'effects': croc_35(), 'crop': (3300, 2400, 850, 850)},
    {'note': 37, 'label': "The violet triangle under the fish's fin: hold C#2 to play; a sea-sharp fin pops up, then "
                          "the shark leaps out grinning with a splash",
     'effects': shark_37(), 'crop': (3700, 2150, 650, 650)},
    {'note': 43, 'label': "The slate sliver on the big-eye creature's head: hold G2 to play; it becomes a meerkat on "
                          "lookout that folds its paws, curls its tail and shades its eyes",
     'effects': meerkat_43(), 'crop': (4100, 2250, 600, 600)},
    {'note': 46, 'label': "The pink tongue under the acorn frog's blue head: hold A#2 to play; it flicks out after a "
                          "candy fly and curls round it, and the frog's eye goes wide",
     'effects': tongue_46(), 'crop': (2650, 1720, 800, 800)},
    {'note': 67, 'label': "The little aqua patch between the orange capsule and the antler: hold G4 to play; candy "
                          "bunting strings across it pennant by pennant and a rosette pops on the antler",
     'effects': bunting_67(), 'crop': (2880, 2480, 560, 560)},
]

if __name__ == '__main__':
    k.run(DESIGNS)
