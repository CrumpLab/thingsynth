# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b01 of the note animations: notes 23, 44, 50, 77, 83, 89, all round the horned mask at the top left.

    uv run scripts/notes_b01.py            # strips and end frames in docs/objects/note-<n>/
    uv run scripts/notes_b01.py 23         # just note-23
    uv run scripts/notes_b01.py export     # build.json for each

note-23 B0  f279 the coral hood          -> anglerfish: a lure rises from its cap and lights, its zigzag leaf gapes
note-44 G#2 f291 the mask's left horn    -> seahorse: a head and snout push out of its bend, ridges, fins, a tail
note-50 D3  f265 the purple segment      -> pinata: fringe, a crack, it bursts and candies tumble out
note-77 F5  f300 the pale wave in the panel -> the mask's other eye opens, lid lifts, lashes, a glint
note-83 B5  f293 the left horn's tip     -> crescent moon with a sleepy face and stars popping round it
note-89 F6  f294 the right horn's tip    -> a crab pincer that opens wide and snaps shut with click crescents
"""
import importlib.util
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks); ks.loader.exec_module(k)
p, tube, bez, spiral, crescent = k.p, k.tube, k.bez, k.spiral, k.g.crescent


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


def poly(pts) -> str:
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def blob(cx, cy, rx, ry, seed=0, wob=0.08, n=11, rot=0.0) -> str:
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


def ltube(P, w0, w1, seed=0, jit=0.07, inner_bumps=0, bump=0.0) -> str:
    """A lumpy tapered limb along P (half-widths w0 -> w1), round-capped; inner_bumps knobs on its right side."""
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
        if inner_bumps:
            wr += bump * max(0.0, math.sin(u * inner_bumps * math.pi)) ** 2 * (1 - u * 0.5)
        L.append((x + nx * wl, y + ny * wl))
        R.append((x - nx * wr, y - ny * wr))
    rr = max(1.0, math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1]) / 2)
    return 'M' + 'L'.join(p(*q) for q in L) + f'A{rr:.1f} {rr:.1f} 0 0 1 {p(*R[-1])}' + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def star(cx, cy, R, r, seed=0, rot=-90.0, pts=5) -> str:
    """A plump, slightly lopsided star."""
    rnd = random.Random(seed)
    out = []
    for j in range(pts * 2):
        a = math.radians(rot + j * 180 / pts + rnd.uniform(-5, 5))
        rad = (R if j % 2 == 0 else r) * (1 + rnd.uniform(-0.08, 0.08))
        out.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    return closed(out)


def sparkle(cx, cy, R, r) -> str:
    """A four-pointed glint."""
    out = []
    for j in range(8):
        a = math.radians(-90 + j * 45)
        rad = R if j % 2 == 0 else r
        out.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    return closed(out)


def it(d, fill, edge, at, start, end, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 4),
         'end': round(end, 4), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 4), round(out[1], 4)
    return o


def frame_map(A, ang_deg):
    """(u, v) in a frame at A with u along ang_deg (screen degrees) and v to its right-hand (screen) side."""
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    return lambda u, v: (A[0] + u * ux + v * vx, A[1] + u * uy + v * vy)


# palette
CREAM, WHITE, BLACK, PLUM = '#fff4d6', '#ffffff', '#000000', '#3a1030'
PINK, YELLOW, CYAN, MINT, LILAC, ORANGE = '#ff86c8', '#ffe14d', '#57e0ff', '#8ff0b0', '#c9a6ff', '#ff9a3c'


# ---- note-23 B0: the coral hood becomes an anglerfish ------------------------------------------------------------

def anglerfish() -> dict:
    E = 14
    lure, face, fin, mouthparts = [], [], [], []
    # the lure stalk rises out of the lavender cap's tip (the cap stays in front), arches right over the mushroom cap
    base = (1124, 505)
    P = bez(base, (1140, 385), (1290, 370), (1322, 462), 34)
    lure.append(it(ltube(P[:22], 22, 17, 3), '#c99be0', E, base, 0.0, 0.05))
    lure.append(it(ltube(P, 22, 13, 3), '#c99be0', E, base, 0.04, 0.26))
    bx, by = 1324, 506
    # glow round the bulb, then the bulb, then its core lights
    lure.append(it(blob(bx, by, 92, 88, 7, 0.1, 13), '#fff8b0', 11, (bx, by), 0.46, 0.62))
    lure.append(it(blob(bx, by, 50, 48, 5, 0.09), '#f4e2ff', E, (bx, by - 30), 0.2, 0.36))
    lure.append(it(blob(bx + 4, by + 3, 31, 29, 8, 0.12), '#ffd72e', 0, (bx, by), 0.44, 0.58))
    # rays blaze out at the end (none straight up, the painting's top edge is close)
    rays = ''
    for j, ang in enumerate((-10, 30, 70, 110, 150, 190, 225, 315)):
        a = math.radians(ang)
        r0, r1 = 104, 150 if j % 2 == 0 else 132
        ca, sa = math.cos(a), math.sin(a)
        mid = (r0 + r1) / 2
        w = 15
        pts = [(bx + ca * r0 - sa * 6, by + sa * r0 + ca * 6), (bx + ca * mid - sa * w, by + sa * mid + ca * w),
               (bx + ca * r1, by + sa * r1), (bx + ca * mid + sa * w, by + sa * mid - ca * w),
               (bx + ca * r0 + sa * 6, by + sa * r0 - ca * 6)]
        rays += closed(pts)
    lure.append(it(rays, '#ffd23a', 11, (bx, by), 0.8, 0.97))
    lure.append(it(blob(bx - 16, by - 18, 12, 9, 2), WHITE, 0, (bx, by), 0.88, 1.0))

    # the jaw: the cyan leaf hanging off the hood is its upper jaw; from behind its lower edge a dark mouth drops
    # open round a hinge at the back, a crack first and then wide, with crooked candy teeth hanging from the leaf
    # and standing on a big lumpy cyan lower jaw (drawn behind the leaf, so its edge stays the upper lip)
    Hn = (1000, 884)
    TOPLIP = [(992, 868), (1030, 892), (1064, 910), (1100, 924), (1128, 916), (1150, 888), (1172, 856)]

    def mouth(G, seed):
        rnd = random.Random(seed)
        f = lambda u: G * math.sin(math.pi * min(1.0, u * 0.62 + 0.08)) ** 0.9   # how far the lip drops at u (0-1)
        n = len(TOPLIP) - 1
        low = [(x + 6 * u * G / 120, y + f(u) + 8) for (x, y), u in ((q, j / n) for j, q in enumerate(TOPLIP))]
        low[-1] = (low[-1][0] + 18 * G / 120, low[-1][1])
        hole = closed([(x, y - 18) for x, y in TOPLIP] + [(TOPLIP[-1][0] + 14, TOPLIP[-1][1] + 6)] + low[::-1])
        th = 40 + 18 * G / 120
        out = [(x - 4, y + th * (0.7 + 0.5 * math.sin(math.pi * j / n)) + rnd.uniform(-6, 6)) for j, (x, y) in enumerate(low)]
        jaw = closed(low + [(low[-1][0] + 16, low[-1][1] + th * 0.45)] + out[::-1] + [(out[0][0] - 12, (out[0][1] + low[0][1]) / 2)])
        tt, tb = '', ''
        for j in (1, 2, 3, 4):
            (x0, y0), (x1, y1) = TOPLIP[j], TOPLIP[j + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ln = (0.42 * f(j / n + 0.08) + 6) * rnd.uniform(0.85, 1.15)
            w = 9 + 5 * G / 120
            tt += closed([(mx - w, my - 14), (mx + rnd.uniform(-3, 4), my + ln), (mx + w, my - 14)])
        for j in (1, 2, 3, 4):
            (x0, y0), (x1, y1) = low[j], low[j + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ln = (0.34 * f(j / n + 0.08) + 5) * rnd.uniform(0.85, 1.15)
            w = 8 + 5 * G / 120
            tb += closed([(mx - w, my + 6), (mx + rnd.uniform(-4, 4), my - ln), (mx + w, my + 6)])
        return hole, jaw, tt, tb

    for (G, s0, s1, outw, seed) in ((26, 0.3, 0.44, (0.55, 0.62), 1), (120, 0.55, 0.76, None, 2)):
        hole, jaw, tt, tb = mouth(G, seed)
        mouthparts.append(it(hole, PLUM, E, Hn, s0, s1, out=outw))
        if G > 60:
            mouthparts.append(it(blob(1092, 990, 40, 20, 4, 0.1, 9, -8), '#ff6fa8', 10, Hn, 0.7, 0.84))
        mouthparts.append(it(jaw, '#3ce6d6', E, Hn, s0, s1, out=outw))
        mouthparts.append(it(tb, CREAM, 10, Hn, s0 + 0.03, s1, out=outw))
        mouthparts.append(it(tt, CREAM, 10, Hn, s0 + 0.03, s1, out=outw))
    # a round eye on the hood under the cap, looking up at its lure
    ex, ey = 1050, 688
    face.append(it(blob(ex, ey, 27, 26, 9, 0.05), WHITE, 12, (ex, ey), 0.5, 0.6))
    face.append(it(blob(ex + 7, ey - 6, 15, 15, 1, 0.04), '#ffd23a', 9, (ex, ey), 0.56, 0.66))
    face.append(it(blob(ex + 9, ey - 8, 8, 8, 2, 0.04), BLACK, 0, (ex, ey), 0.6, 0.68))
    # a spiny coral fin out of the hood's back (the hood in front of its root)
    fin.append(it(closed([(820, 774), (772, 750), (800, 800), (740, 824), (798, 852), (752, 906), (810, 914)]),
                  '#ff8a7a', E, (858, 840), 0.6, 0.76))
    return {
        'note': 23,
        'label': 'The coral hood under the lavender cap: hold B0 to play; it turns into a deep-sea anglerfish, a lure '
                 'rising from its cap and lighting up as its zigzag leaf gapes into a toothy jaw',
        'effects': [
            {'effect': 'sprites', 'place': 'under', 'items': fin},
            {'effect': 'sprites', 'place': 'around', 'front': ['f282'], 'items': lure},
            {'effect': 'sprites', 'place': 'around', 'front': ['f280', 'f281'], 'items': mouthparts},
            {'effect': 'sprites', 'place': 'over', 'items': face},
        ],
        'again': ['f282', 'f280', 'f281'],
    }


# ---- note-44 G#2: the mask's left horn becomes a seahorse ---------------------------------------------------------

def seahorse() -> dict:
    E = 14
    HORN = '#72b0c0'
    back, on = [], []
    hx, hy = 506, 662          # its head, on the horn's upper bend, under the tip
    head = blob(hx + 22, hy, 42, 40, 11, 0.07)
    P = bez((hx + 28, hy - 2), (hx + 60, hy - 16), (hx + 88, hy - 18), (hx + 116, hy - 14), 16)
    snout = ltube(P, 20, 15, 5, 0.05)
    flare = blob(hx + 122, hy - 14, 15, 24, 6, 0.06)
    # outlined layer (double width) then fill-only layer, so head, snout and flare merge into one shape
    parts = ((head, 0.0, 0.05), (snout, 0.02, 0.16), (flare, 0.12, 0.22))
    for d, s0, s1 in parts:
        back.append(it(d, HORN, E * 2, (hx, hy), s0, s1))
    for d, s0, s1 in parts:
        back.append(it(d, HORN, 0, (hx, hy), s0, s1))
    back.append(it(blob(hx + 126, hy - 14, 5, 11, 2, 0.05), '#1d3e47', 0, (hx, hy), 0.18, 0.26))
    # pectoral fin, then a frilly dorsal fin on its back, both from behind the horn
    back.append(it(closed([(478, 712), (538, 692), (560, 712), (556, 738), (574, 756), (526, 774), (480, 764)]),
                   '#ff9ccc', 12, (484, 734), 0.58, 0.74))
    back.append(it(closed([(426, 698), (384, 706), (402, 730), (378, 752), (398, 774), (380, 800), (426, 814)]),
                   '#ffe066', 12, (424, 756), 0.7, 0.86))
    # a curled tail out of its root, over the mask's forehead
    T = spiral(522, 872, 0.15, 46, 1.05, 0.55, -1, 40)
    back.append(it(ltube(T, 14, 7, 9, 0.05), HORN, E, (522, 872), 0.8, 0.98))
    # the eye, on the head beside the horn
    ex, ey = hx + 34, hy - 10
    eye = [it(blob(ex, ey, 19, 18, 3, 0.05), WHITE, 11, (ex, ey), 0.24, 0.36),
           it(blob(ex + 5, ey - 1, 9, 9, 4, 0.05), BLACK, 0, (ex, ey), 0.3, 0.4),
           it(blob(ex + 8, ey - 5, 3.5, 3.5, 4, 0.05), WHITE, 0, (ex, ey), 0.36, 0.42)]
    # ridges band its belly, top to bottom, drawn on the horn
    for j, (y, tilt) in enumerate(((710, -8), (762, -2), (814, 10), (864, 22))):
        band = blob(470, y, 110, 11, 20 + j, 0.05, 12, tilt)
        on.append(it(band, '#3f7f93', 10, (470, y), 0.36 + 0.07 * j, 0.46 + 0.07 * j, grow='x'))
    return {
        'note': 44,
        'label': "The mask's blue-grey left horn: hold G#2 to play; it turns into a seahorse, a head and long snout "
                 'pushing out of its bend, ridges banding its belly, fins fanning and its tail curling last',
        'effects': [
            {'effect': 'sprites', 'place': 'around', 'front': ['f293'], 'items': back},
            {'effect': 'sprites', 'place': 'on', 'items': on},
            {'effect': 'sprites', 'place': 'over', 'items': eye},
        ],
        'crop': (320, 400, 560, 560),
        'again': ['f293'],
    }


# ---- note-50 D3: the purple segment is a pinata ------------------------------------------------------------------

def wrapped(x, y, rot, seed, size=1.0):
    """A wrapped sweet: two twisted ends and a lumpy body."""
    s = size
    tw = (closed([(x - 34 * s, y), (x - 74 * s, y - 28 * s), (x - 64 * s, y), (x - 74 * s, y + 28 * s)]) +
          closed([(x + 34 * s, y), (x + 74 * s, y - 28 * s), (x + 64 * s, y), (x + 74 * s, y + 28 * s)]))
    return k.g.rot_path(tw, x, y, rot), blob(x, y, 42 * s, 30 * s, seed, 0.06, 11, rot)


def pinata() -> dict:
    E = 12
    on, over = [], []
    # three bands of crepe-paper fringe, each a row of hanging tabs
    for j, (y, col, s0) in enumerate(((1070, PINK, 0.0), (1124, YELLOW, 0.1), (1178, CYAN, 0.2))):
        rnd = random.Random(40 + j)
        top = [(800, y - 26 + rnd.uniform(-3, 3)), (955, y - 28 + rnd.uniform(-3, 3))]
        bot = []
        n = 6
        for s in range(n):
            x0, x1 = 955 - s * 155 / n, 955 - (s + 1) * 155 / n
            dep = rnd.uniform(18, 26)
            bot += [(x0 - 2, y + 2), (x0 - 4, y + dep), ((x0 + x1) / 2 + 2, y + dep + 4), (x1 + 6, y + dep - 2), (x1 + 4, y + 2)]
        on.append(it(poly(top + bot), col, 10, (876, y), s0, s0 + (0.06 if j == 0 else 0.13), grow='x'))
    c = (876, 1122)
    # the crack, wider, then it bursts open
    zz = [(812, 1128), (838, 1110), (852, 1132), (874, 1104), (892, 1130), (912, 1106), (940, 1120)]
    crack1 = poly([(x, y - 6) for x, y in zz] + [(x + 2, y + 7) for x, y in zz[::-1]])
    over.append(it(crack1, PLUM, 0, c, 0.32, 0.4, out=(0.46, 0.52)))
    crack2 = poly([(x, y - 15 - 5 * (j % 2)) for j, (x, y) in enumerate(zz)] +
                  [(x + 2, y + 16 + 5 * (j % 2)) for j, (x, y) in list(enumerate(zz))[::-1]])
    over.append(it(crack2, PLUM, 8, c, 0.44, 0.52, out=(0.56, 0.62)))
    rnd = random.Random(7)
    hole = [(c[0] + math.cos(a) * r * 1.0, c[1] + math.sin(a) * r * 1.05)
            for a, r in ((math.radians(j * 30), 58 + (10 if j % 2 else -4) + rnd.uniform(-4, 4)) for j in range(12))]
    over.append(it(poly(hole), PLUM, E, c, 0.54, 0.64))
    # candy packed inside, peeking out of the hole
    over.append(it(blob(858, 1108, 24, 21, 11, 0.1) + blob(898, 1146, 20, 18, 12, 0.1), PINK, 10, c, 0.58, 0.66))
    over.append(it(blob(896, 1104, 19, 18, 13, 0.1) + blob(856, 1146, 18, 16, 14, 0.1), YELLOW, 10, c, 0.6, 0.68))
    # paper shards fly off, frilled like the bands
    over.append(it(poly([(742, 1030), (796, 1016), (806, 1056), (790, 1064), (782, 1080), (764, 1068), (750, 1082)]),
                   PINK, 10, c, 0.56, 0.68))
    over.append(it(poly([(966, 1046), (1022, 1040), (1030, 1084), (1012, 1090), (1004, 1104), (986, 1094), (972, 1100)]),
                   YELLOW, 10, c, 0.58, 0.7))
    # candies tumble out of the hole (each scales out from it, so it flies out), biggest first
    t1, b1 = wrapped(972, 1268, -15, 1, 1.0)
    over += [it(t1, PINK, 11, c, 0.62, 0.74), it(b1, PINK, 11, c, 0.62, 0.74),
             it(blob(964, 1262, 26, 9, 3, 0.1, 9, -15), WHITE, 0, c, 0.65, 0.76)]
    over.append(it(closed([(752, 1300), (758, 1250), (790, 1228), (824, 1248), (832, 1300)]), MINT, 11, c, 0.66, 0.78))
    sx, sy = 1012, 1160          # a lollipop
    over.append(it(tube(bez((sx, sy), (1026, 1200), (1040, 1236), (1052, 1272), 12), 8, 8), WHITE, 10, c, 0.7, 0.82))
    over.append(it(blob(sx, sy, 50, 48, 4, 0.05), YELLOW, 11, c, 0.7, 0.82))
    over.append(it(crescent(sx, sy, 26, 30, 250, 17), ORANGE, 0, c, 0.72, 0.84))
    over.append(it(blob(872, 1318, 40, 38, 5, 0.06), LILAC, 11, c, 0.74, 0.86))
    t2, b2 = wrapped(740, 1176, 20, 6, 0.9)
    over += [it(t2, CYAN, 11, c, 0.78, 0.9), it(b2, CYAN, 11, c, 0.78, 0.9)]
    over.append(it(closed([(930, 1372), (936, 1326), (966, 1306), (998, 1326), (1004, 1372)]), ORANGE, 11, c, 0.82, 0.94))
    # confetti bursts out last
    for j, (col, ang0) in enumerate(((PINK, 0), (CYAN, 24), (YELLOW, 48))):
        rnd = random.Random(60 + j)
        d = ''
        for q in range(5):
            a = math.radians(ang0 + q * 72 + rnd.uniform(-10, 10))
            r = rnd.uniform(160, 210)
            d += blob(c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.9, 18, 11, 70 + q, 0.15, 7, rnd.uniform(0, 180))
        over.append(it(d, col, 9, c, 0.86 + 0.03 * j, 0.96 + 0.02 * j))
    return {
        'note': 50,
        'label': 'The purple segment under the coral hood: hold D3 to play; it is a pinata, frilled in candy paper, it '
                 'cracks, bursts open and candies tumble out over the lavender cone',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': on},
            {'effect': 'sprites', 'place': 'over', 'items': over},
        ],
    }


# ---- note-77 F5: the pale wave in the mask's panel opens as its other eye -----------------------------------------

def other_eye() -> dict:
    E = 12
    LID = '#ff3fd0'
    cx, cy = 666, 1028
    almond = [(672, 954), (702, 974), (716, 1020), (710, 1066), (686, 1098), (660, 1104), (632, 1084), (620, 1040),
              (626, 994), (646, 964)]
    items = [it(closed(almond), WHITE, E, (cx, cy), 0.0, 0.05)]
    items.append(it(blob(652, 1044, 29, 32, 3, 0.05), '#18c8f0', 10, (cx, cy), 0.2, 0.34))
    items.append(it(blob(648, 1048, 14, 16, 4, 0.05), BLACK, 0, (cx, cy), 0.26, 0.38))
    # the lid: shut over the whole eye at a tap, it lifts to sleepy half way, then wide open into a fold
    shut = closed(almond[:1] + [(704, 972), (720, 1020), (712, 1068), (688, 1102), (660, 1108), (630, 1088),
                                (616, 1040), (622, 992), (644, 960)])
    items.append(it(shut, LID, E, (cx, cy), 0.0, 0.05, out=(0.1, 0.2)))
    items.append(it(tube(bez((626, 1060), (650, 1090), (690, 1088), (712, 1052), 14), 6, 3), BLACK, 0, (cx, cy), 0.0, 0.05,
                    out=(0.1, 0.2)))
    half = closed([(672, 950), (706, 970), (722, 1018), (702, 1040), (668, 1046), (634, 1040), (614, 1000), (640, 960)])
    items.append(it(half, LID, E, (cx, 950), 0.1, 0.22, grow='y', out=(0.5, 0.64)))
    items.append(it(crescent(666, 1032, 86, 52, 128, 26), LID, 10, (666, 946), 0.54, 0.66))
    # lashes flick up off the lid, one after another
    for j, ((x0, y0), (cx1, cy1), (x1, y1)) in enumerate((((640, 962), (622, 936), (606, 906)),
                                                       ((672, 948), (674, 918), (686, 888)),
                                                       ((702, 966), (724, 944), (748, 930)))):
        P = bez((x0, y0 + 10), (cx1, cy1), (cx1, cy1), (x1, y1), 12)
        items.append(it(tube(P, 10, 3.5), BLACK, 0, (x0, y0), 0.68 + 0.05 * j, 0.76 + 0.05 * j))
    items.append(it(blob(660, 1034, 7, 7, 1, 0.05), WHITE, 0, (cx, cy), 0.84, 0.92))
    items.append(it(sparkle(742, 1010, 40, 11), '#e8fdff', 9, (742, 1010), 0.86, 1.0))
    return {
        'note': 77,
        'label': "The pale wave in the horned mask's striped panel: hold F5 to play; it opens as the mask's other eye, "
                 'sleepy at first, then its lid lifts, lashes flick up and it glints',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-83 B5: the left horn's tip becomes a crescent moon -----------------------------------------------------

def crescent_moon(C1, R, C2, r, nose=16, seed=3) -> str:
    """Outer disc (C1, R) minus inner disc (C2, r), the inner edge carrying a nose bump at its middle."""
    rnd = random.Random(seed)
    dx, dy = C2[0] - C1[0], C2[1] - C1[1]
    d = math.hypot(dx, dy)
    a = (R * R - r * r + d * d) / (2 * d)
    h = math.sqrt(max(0.0, R * R - a * a))
    mx, my = C1[0] + a * dx / d, C1[1] + a * dy / d
    P1 = (mx - h * dy / d, my + h * dx / d)
    P2 = (mx + h * dy / d, my - h * dx / d)
    ang = lambda c, q: math.atan2(q[1] - c[1], q[0] - c[0])
    beta = math.atan2(dy, dx)                    # toward the hollow
    a1, a2 = ang(C1, P1), ang(C1, P2)
    # outer arc from P1 to P2 the long way round (away from beta)
    span = (a2 - a1) % (2 * math.pi)
    if abs(((a1 + span / 2) - beta + math.pi) % (2 * math.pi) - math.pi) < math.pi / 2:
        span -= 2 * math.pi
    outer = [(C1[0] + R * math.cos(a1 + span * j / 24), C1[1] + R * math.sin(a1 + span * j / 24)) for j in range(25)]
    # inner arc from P2 back to P1, the way that passes toward C1
    b2, b1 = ang(C2, P2), ang(C2, P1)
    sp = (b1 - b2) % (2 * math.pi)
    if abs(((b2 + sp / 2) - (beta + math.pi) + math.pi) % (2 * math.pi) - math.pi) > math.pi / 2:
        sp -= 2 * math.pi
    inner = []
    for j in range(1, 24):
        u = j / 24
        t = b2 + sp * u
        rr = r - nose * math.exp(-((u - 0.47) / 0.07) ** 2) + 2 * math.sin(j * 1.7)
        inner.append((C2[0] + rr * math.cos(t), C2[1] + rr * math.sin(t)))
    pts = [(x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.5, 1.5)) for x, y in outer[::2] + inner[::2]]
    return closed(pts)


def moon() -> dict:
    E = 11
    MOON = '#ffe95a'
    C1, R = (468, 512), 98
    C2, r = (430, 548), 84
    items = [it(k.m.FILLS['f293'], MOON, E, (456, 545), 0.0, 0.05, out=(0.12, 0.22)),
             it(star(600, 468, 44, 19, 1, -80), PINK, E, (600, 468), 0.0, 0.07),
             it(crescent_moon(C1, R, C2, r), MOON, E, (470, 520), 0.08, 0.28)]
    # the painting is bare under the tip: as the tip fades, a patch of the sky's own cream fills the moon's hollow
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', k.m.FILLS['f293'])]
    tp = list(zip(nums[0::2], nums[1::2]))
    mx, my = sum(q[0] for q in tp) / len(tp), sum(q[1] for q in tp) / len(tp)
    patch = poly([(mx + (x - mx) * 1.15, my + (y - my) * 1.15) for x, y in tp])
    items.insert(0, it(patch, '#f1fbdb', 0, (mx, my), 0.1, 0.18))
    # its sleepy face: a closed lid, then a blush, then a smile; stars pop between
    items.append(it(crescent(512, 452, 15, 200, 340, 9), BLACK, 0, (512, 452), 0.3, 0.4))
    items.append(it(star(580, 562, 36, 15, 2, -100), CYAN, E, (580, 562), 0.38, 0.5))
    items.append(it(blob(528, 486, 15, 11, 6, 0.1), '#ff9cc0', 0, (528, 486), 0.5, 0.6))
    items.append(it(star(548, 404, 28, 12, 3, -70), '#c9f06a', E, (548, 404), 0.6, 0.72))
    smile = closed([(512, 506), (528, 518), (542, 512), (532, 532), (514, 528)])
    items.append(it(smile, PLUM, 9, (526, 518), 0.72, 0.84))
    for j, (x, y, s) in enumerate(((600, 468, 24), (580, 562, 20), (548, 404, 17))):
        items.append(it(sparkle(x + s * 1.4, y - s * 1.3, s, s * 0.3), WHITE, 8, (x + s, y - s), 0.84 + 0.04 * j,
                        0.92 + 0.03 * j))
    return {
        'note': 83,
        'label': "The ochre tip of the mask's left horn: hold B5 to play; it fattens into a crescent moon with a sleepy "
                 'face that blushes and smiles, as candy stars pop out round it one by one',
        'effects': [{'effect': 'vanish', 'span': [0.08, 0.2]},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (330, 360, 520, 520),
    }


# ---- note-89 F6: the right horn's tip becomes a snapping pincer ---------------------------------------------------

def pincer() -> dict:
    E = 11
    CRAB = '#ff5a46'
    H = (764, 562)                # the movable finger's hinge, at the palm's lower left
    palm = blob(800, 556, 62, 48, 4, 0.08, 11, -30)

    def finger(ang, seed, bumps=0):
        F = frame_map(H, ang)
        P = [F(140 * j / 16, -28 * (j / 16) ** 2) for j in range(17)]   # bends toward the hook
        return ltube(P, 28, 5, seed, 0.06, bumps, 13)

    poses = [(-140, 0.0, 0.06, (0.18, 0.26), 2), (-163, 0.16, 0.3, (0.44, 0.52), 3), (-188, 0.42, 0.56, (0.78, 0.82), 3),
             (-124, 0.78, 0.84, None, 0)]
    # the hook itself turns crab red at a tap, and is the claw's fixed finger
    items = [it(k.m.FILLS['f294'], CRAB, E, (760, 500), 0.0, 0.05)]
    # outlined layers, then fill-only layers, so palm and finger are one shape
    items.append(it(palm, CRAB, E * 2, (800, 560), 0.0, 0.06))
    fingers = [(finger(a, 10 + j, b), s0, s1, out) for j, (a, s0, s1, out, b) in enumerate(poses)]
    for d, s0, s1, out in fingers:
        items.append(it(d, CRAB, E * 2, H, s0, s1, out=out))
    items.append(it(palm, CRAB, 0, (800, 560), 0.0, 0.06))
    for d, s0, s1, out in fingers:
        items.append(it(d, CRAB, 0, H, s0, s1, out=out))
    # cream knobbly teeth along the hook's inner edge, then a shine on the palm
    items.append(it(blob(734, 518, 16, 12, 1, 0.1, 9, 30) + blob(716, 486, 14, 11, 2, 0.1, 9, 30) +
                    blob(700, 458, 11, 9, 3, 0.1, 9, 30), CREAM, 10, (740, 520), 0.28, 0.4, out=(0.78, 0.82)))
    items.append(it(blob(818, 536, 20, 11, 5, 0.1, 9, -30), '#ffd0c4', 0, (810, 548), 0.6, 0.72))
    tip = (700, 446)
    items.append(it(crescent(tip[0] + 8, tip[1] + 6, 60, 70, 150, 24), WHITE, 10, tip, 0.84, 0.93))
    items.append(it(crescent(tip[0] + 8, tip[1] + 6, 96, 80, 140, 28), WHITE, 10, tip, 0.88, 0.97))
    items.append(it(sparkle(tip[0] - 6, tip[1] - 4, 30, 9), YELLOW, 9, tip, 0.86, 0.96))
    return {
        'note': 89,
        'label': "The ochre tip of the mask's right horn: hold F6 to play; it turns into a red crab's pincer that opens "
                 'wider and wider, shows its knobbly teeth and snaps shut with a click',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (500, 330, 480, 480),
    }


DESIGNS = [anglerfish(), seahorse(), pinata(), other_eye(), moon(), pincer()]

if __name__ == '__main__':
    k.run(DESIGNS)
