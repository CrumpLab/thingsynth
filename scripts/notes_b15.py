# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Note animations, batch b15: D1, F#1, A2, C#3 and F4, all on and round the bunny slab, bottom right.

    uv run scripts/notes_b15.py            # strips and end frames
    uv run scripts/notes_b15.py 26         # one note
    uv run scripts/notes_b15.py export     # build.json for each

note-26 D1  f059 the tall pale leaf on the slab's low tier: it opens into a Venus flytrap
note-30 F#1 f051 the orange front band of the bunny's pot: it puffs into an iced, sprinkled donut
note-45 A2  f060 the pale hollow in the big salmon swoop's hooked loop: a hermit crab comes out of it
note-49 C#3 f058 the pale almond at the foot of the bunny's spiny lobe: a bud that opens into a waxy cactus bloom
note-65 F4  f057 the white of the bunny's sleepy eye: it turns into a beating heart
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
m, g, p = k.m, k.g, k.p
smooth, tube, bez = m.smooth, k.tube, k.bez


# ---- helpers -------------------------------------------------------------------------------------------------------

def item(d, fill, edge, at, start, end, grow='scale', out=None, sweep=None) -> dict:
    it = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 4),
          'end': round(end, 4), 'grow': grow}
    if out:
        it['outStart'], it['outEnd'] = round(out[0], 4), round(out[1], 4)
    if sweep:
        it['sweep'] = {'from': round(sweep[0], 1), 'to': round(sweep[1], 1)}
    return it


def rot(pt, c, deg):
    """Turn pt round c by deg, clockwise on screen."""
    a = math.radians(deg)
    dx, dy = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def jitter(pts, seed, amt):
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in pts]


def lump(cx, cy, rx, ry, rot_deg=0.0, seed=0, amt=0.06, n=14) -> str:
    rnd = random.Random(seed)
    a = math.radians(rot_deg)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        kk = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * kk, math.sin(t) * ry * kk
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def ltube(P, w0, w1, seed, cap=True) -> str:
    """A lumpy tapered limb along P, rounded at the end."""
    rnd = random.Random(seed)
    ph, n = rnd.random() * 6.28, len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + 0.08 * math.sin(u * 9 + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    tip = []
    if cap:
        ex, ey = P[-1]
        a, b = P[-2], P[-1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        tip = [(ex + dx / d * w1 * 0.9, ey + dy / d * w1 * 0.9)]
    pts = L + tip + R[::-1]
    return smooth(pts[::2] if len(pts) > 44 else pts)


def poly_pts(fid):
    nums = [float(t) for t in re.findall(r'-?\d+\.?\d*', m.FILLS[fid])]
    return list(zip(nums[0::2], nums[1::2]))


def heart(cx, cy, size, tilt=0.0, seed=0, amt=0.03) -> str:
    """A lumpy hand-drawn heart, size = its width."""
    rnd = random.Random(seed)
    pts = []
    for i in range(22):
        t = i / 22 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        kk = 1 + amt * rnd.uniform(-1, 1)
        pts.append(rot((cx + x * size / 34 * kk, cy + y * size / 34 * kk), (cx, cy), tilt))
    return smooth(pts)


PINK, HOT, MINT, LIME, YELLOW, CREAM, WHITE = '#FF8CC6', '#FF4F9A', '#9EEB8C', '#B6EC5A', '#FFE24A', '#FFF4D6', '#FFFFFF'


# ---- note-26 D1: the tall pale leaf opens into a Venus flytrap -----------------------------------------------------

def flytrap() -> dict:
    INK = 14
    H = (3496.0, 4338.0)
    LAV, LINING, DROP = '#C9B6F4', '#FF5C9E', '#FFC93C'

    def frame_pts(side, theta, L, W, f_lin):
        phi = -10 + side * theta  # the lobe's axis, degrees clockwise from straight up
        def to_canvas(v, u):  # v across (toward the body), u up the axis
            return rot((H[0] + side * v, H[1] - u), H, phi)
        N = 14
        outer = []
        for i in range(N + 1):
            s = i / N
            v = W * math.sin(math.pi * s) ** 0.7 * (0.72 + 0.45 * s)
            outer.append(to_canvas(v, L * s))
        lin = []
        for i in range(2, N - 1):
            s = i / N
            lin.append(to_canvas(-2, L * s))
        for i in range(N - 2, 1, -1):
            s = i / N
            v = W * f_lin * math.sin(math.pi * (s - 0.1) / 0.85) ** 0.8 * (0.72 + 0.45 * s)
            lin.append(to_canvas(v, L * s))
        return outer, lin, to_canvas

    def lobe(side, theta, L, W, lash, f_lin, seed):
        outer, lin, tc = frame_pts(side, theta, L, W, f_lin)
        rnd = random.Random(seed)
        shell = smooth(jitter(outer, seed, 4) + [tc(-4, L * 0.5)])
        lashes = ''
        for j, s in enumerate((0.4, 0.57, 0.73, 0.88)):
            ln = lash * (0.8 + 0.35 * math.sin(math.pi * s)) * rnd.uniform(0.9, 1.1)
            a = math.radians(32 + 14 * (s - 0.5))
            dv, du = -math.cos(a), math.sin(a)
            b0, b1 = tc(6, L * s - 24), tc(6, L * s + 24)
            q = lambda f, off: tc(dv * ln * f + du * off, L * s + du * ln * f - dv * off)
            lashes += smooth([b0, q(0.45, -17), q(0.85, -9), q(1.0, 0), q(0.85, 9), q(0.45, 17), b1]).replace('Z', 'Z ')
        return lashes.strip(), shell, smooth(jitter(lin, seed + 7, 3))

    poses = [  # theta, L, W, lash length, lining share, window
        (6, 322, 120, 40, 0.18, (0.0, 0.05)),
        (15, 334, 128, 62, 0.32, (0.09, 0.27)),
        (25, 346, 138, 84, 0.45, (0.33, 0.52)),
        (34, 360, 148, 104, 0.56, (0.58, 0.78)),
    ]
    # the throat: a deep pink cup behind the lobes, filling where the leaf stood as they part
    # the throat: a deep pink cup where the leaf stood, behind the lobes, showing as they part
    throat = smooth(jitter([(3496, 4336), (3440, 4302), (3404, 4222), (3396, 4150), (3408, 4078), (3432, 4026),
                            (3478, 4030), (3530, 4088), (3572, 4160), (3596, 4230), (3576, 4300), (3536, 4334)], 12, 3))
    items = [item(throat, '#C42A86', INK, H, 0.03, 0.2, 'y')]
    for k_, (th, L, W, lash, fl, (a, b)) in enumerate(poses):
        nxt = poses[k_ + 1][5] if k_ + 1 < len(poses) else None
        out = (nxt[1], nxt[1] + 0.04) if nxt else None
        prev = poses[k_ - 1][0] if k_ else 0
        for side in (-1, 1):
            lashes, shell, lining = lobe(side, th, L, W, lash, fl, 10 * k_ + (side > 0))
            rim0 = 90 - (-10 + side * prev)  # math angle of the previous rim
            body = 90 - (-10 + side * th) - side * 75
            sw = None if k_ == 0 else (rim0 + side * 4, body)
            grow = 'scale'
            items.append(item(lashes, MINT, INK * 0.85, H, a, b, grow, out, sw))
            items.append(item(shell, LAV, INK, H, a, b, grow, out, sw))
            items.append(item(lining, LINING, INK * 0.75, H, a, b, grow, out, sw))
    # 3-4 s: a glistening nectar drop swells at its heart, then shines
    items.append(item(lump(3497, 4232, 34, 42, -8, 3, 0.05), DROP, INK * 0.8, (3497, 4270), 0.8, 0.92))
    items.append(item(lump(3486, 4218, 9, 15, -20, 4, 0.08), WHITE, 0, (3486, 4218), 0.9, 1.0))
    return {
        'note': 26,
        'label': 'The tall pale leaf on the slab: hold D1 to play; it splits along its midrib and opens wide into a '
                 'Venus flytrap with pink linings and soft mint lashes, a nectar drop shining at its heart',
        'effects': [{'effect': 'vanish', 'span': [0.02, 0.06]},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (3020, 3700, 900, 900),
    }


# ---- note-30 F#1: the pot's orange band puffs into a donut ---------------------------------------------------------

def donut() -> dict:
    INK = 14
    DOUGH, ICING, SHINE = '#E8963A', '#FF7EB9', '#FFE3F0'
    pts = poly_pts('f051')
    i0 = min(range(len(pts)), key=lambda i: pts[i][0])
    i1 = max(range(len(pts)), key=lambda i: pts[i][0])
    ring = pts[i0:] + pts[:i0]
    j1 = ring.index(pts[i1])
    arc_a, arc_b = ring[:j1 + 1], ring[j1:] + [ring[0]]
    top, bot = (arc_a, arc_b) if sum(y for _, y in arc_a) / len(arc_a) < sum(y for _, y in arc_b) / len(arc_b) else (arc_b, arc_a)

    def y_at(arc, x):
        best = min(arc, key=lambda q: abs(q[0] - x))
        return best[1]

    # the dough: the band pushed out round its edge, lumpy
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    rnd = random.Random(5)
    sub = pts[::8]
    dough = []
    for i, (x, y) in enumerate(sub):
        a, b = sub[i - 1], sub[(i + 1) % len(sub)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = dy / d, -dx / d
        if (x + nx - cx) ** 2 + (y + ny - cy) ** 2 < (x - cx) ** 2 + (y - cy) ** 2:
            nx, ny = -nx, -ny
        push = 16 + 7 * math.sin(i * 1.7) + rnd.uniform(-3, 3)
        dough.append((x + nx * push, min(4558.0, y + ny * push)))
    dough_d = smooth(dough)
    xs = [3990 + 470 * i / 24 for i in range(25)]
    # the icing over its top, with a wavy hem
    hem = []
    for x in xs:
        yt, yb = y_at(top, x), y_at(bot, x)
        hem.append((x, yt + (yb - yt) * (0.52 + 0.1 * math.sin(x / 37) + 0.05 * math.sin(x / 13))))
    lip = [(x, y_at(top, x) - 12) for x in xs[::-1]]
    icing_d = smooth([(3972, 4262)] + hem + [(4470, 4318)] + lip)
    drips = []
    for n_, (x, ln, w) in enumerate(((4052, 34, 15), (4150, 62, 18), (4228, 30, 14), (4352, 52, 17), (4420, 26, 13))):
        yh = dict(hem)[min(dict(hem), key=lambda q: abs(q - x))]
        P = [(x, yh - 22), (x + 3, yh + ln * 0.45), (x - 2, yh + ln)]
        drips.append((ltube(P, w * 0.8, w * 1.35, 40 + n_), (x, yh - 22)))
    long_P = [(4290, 4440), (4293, 4490), (4288, 4522)]
    long_d = ltube(long_P, 15, 23, 61)
    items = [
        item(dough_d, DOUGH, INK * 2, (cx, cy), 0.0, 0.05),
        item(dough_d, DOUGH, 0, (cx, cy), 0.0, 0.05),
    ]
    sweep = (182, 358)
    outl = [item(icing_d, ICING, INK * 2, (4218, 4250), 0.08, 0.36, sweep=sweep)]
    fills = [item(icing_d, ICING, 0, (4218, 4250), 0.08, 0.36, sweep=sweep)]
    for n_, (d, at) in enumerate(drips):
        s = (0.2, 0.3, 0.26, 0.36, 0.4)[n_]
        outl.append(item(d, ICING, INK * 2, at, s, s + 0.14, 'y'))
        fills.append(item(d, ICING, 0, at, s, s + 0.14, 'y'))
    outl.append(item(long_d, ICING, INK * 2, (4290, 4430), 0.78, 0.94, 'y'))
    fills.append(item(long_d, ICING, 0, (4290, 4430), 0.78, 0.94, 'y'))
    items += outl + fills
    # sprinkles pop on, one after another
    cols = ['#FFFFFF', '#3FD0FF', '#FFE14A', '#7CF06A', '#B46BFF', '#FF6A3D', '#FFFFFF', '#3FD0FF', '#FFE14A']
    spots = [(4010, 4285, 30), (4075, 4330, -20), (4140, 4362, 60), (4200, 4385, -40), (4262, 4398, 15),
             (4330, 4400, -65), (4385, 4383, 35), (4435, 4350, -10), (4105, 4372, 80)]
    for n_, ((x, y, a), col) in enumerate(zip(spots, cols)):
        yt = y_at(top, x)
        y = max(y, yt + 26)
        P = [rot((x - 19, y), (x, y), a), rot((x + 19, y), (x, y), a)]
        s = 0.44 + 0.04 * n_
        items.append(item(ltube(P, 8.5, 8.5, 70 + n_), col, INK * 0.75, (x, y), s, s + 0.06))
    # the shine lands, and a drop falls off the long drip
    items.append(item(lump(4150, 4352, 46, 11, 24, 8, 0.1), SHINE, 0, (4150, 4352), 0.84, 0.94, 'x'))
    items.append(item(lump(4290, 4552, 17, 14, 0, 9, 0.05), ICING, INK * 0.8, (4290, 4530), 0.93, 1.0))
    return {
        'note': 30,
        'label': "The orange band of the bunny's pot: hold F#1 to play; it puffs up into a donut, pink icing pours "
                 'over it and drips, candy sprinkles pop on, and a drip runs off the bottom',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (3800, 3900, 800, 800),
    }


# ---- note-45 A2: a hermit crab comes out of the hollow -------------------------------------------------------------

def claw(cx, cy, ang, s, opn, seed) -> str:
    """A crab's pincer at (cx, cy) pointing along ang (degrees clockwise from right), size s, opened by opn."""
    o = opn
    loc = [(-0.5, -0.36), (0.0, -0.5), (0.45, -0.56 - o * 0.3), (0.9, -0.52 - o * 0.55), (1.22, -0.32 - o * 0.6),
           (1.36, -0.08 - o * 0.5), (1.3, -0.04 - o * 0.45), (1.08, -0.16 - o * 0.45), (0.78, -0.18 - o * 0.3),
           (0.46, -0.02), (0.74, 0.14 + o * 0.15), (0.98, 0.14 + o * 0.25), (1.16, 0.04 + o * 0.3),
           (1.21, 0.1 + o * 0.3), (1.08, 0.32 + o * 0.25), (0.7, 0.46), (0.2, 0.5), (-0.3, 0.42), (-0.56, 0.06)]
    pts = [rot((cx + x * s, cy + y * s), (cx, cy), ang) for x, y in loc]
    return smooth(jitter(pts, seed, s * 0.03))


def hermit_crab() -> dict:
    INK = 12
    CRAB, CLAW = '#FF8457', '#FF6A45'
    on, over = [], []
    # the crab's face fills the shell's mouth (drawn on the hollow, under its ink)
    on.append(item(lump(3500, 3802, 102, 128, 12, 21, 0.05), CRAB, 0, (3500, 3810), 0.06, 0.2))
    on.append(item(lump(3482, 3878, 26, 12, 8, 22, 0.1), '#7A1D3A', INK * 0.6, (3482, 3878), 0.18, 0.28))
    # 0-0.05: eye-stalks pop up out of the hollow with eyes
    stalks = [((3462, 3780), (3448, 3720), (3425, 3672), (3420, 3626), 1), ((3515, 3772), (3525, 3712), (3548, 3664), (3557, 3618), 2)]
    for a, b, c, e, sd in stalks:
        over.append(item(ltube(bez(a, b, c, e, 12), 13, 11, 30 + sd), CRAB, INK, a, 0.0, 0.05))
    for (_, _, _, e, sd) in stalks:
        over.append(item(lump(e[0], e[1] - 14, 31, 35, 0, 33 + sd, 0.05), WHITE, INK, (e[0], e[1] + 10), 0.0, 0.05))
        over.append(item(lump(e[0] + 4, e[1] - 6, 14, 16, 0, 35 + sd, 0.06), '#1A1030', 0, (e[0], e[1] + 10), 0.0, 0.05))
    # 0.6-0.75: three legs hook over the hollow's bottom lip, one after another
    for n_, (a, b, c, e) in enumerate((((3448, 3880), (3428, 3910), (3410, 3935), (3398, 3968)),
                                       ((3496, 3900), (3498, 3930), (3492, 3950), (3478, 3980)),
                                       ((3545, 3884), (3568, 3905), (3588, 3925), (3600, 3958)))):
        s = 0.58 + 0.06 * n_
        over.append(item(ltube(bez(a, b, c, e, 12), 18, 9, 50 + n_), CRAB, INK, a, s, s + 0.08))
    # claws: out to the sides (1-2 s), then up and open, snapping hello (3-4 s)
    def arm(root, ctrl, hand, ang, size, opn, seed, start, end, out=None):
        d_arm = ltube(bez(root, ctrl[0], ctrl[1], hand, 12), 19, 15, seed, cap=False)
        a = math.radians(ang)
        cxy = (hand[0] + math.cos(a) * size * 0.45, hand[1] + math.sin(a) * size * 0.45)
        return [item(d_arm, CRAB, INK, root, start, end, out=out),
                item(claw(cxy[0], cxy[1], ang, size, opn, seed + 1), CLAW, INK, root, start, end, out=out)]
    over += arm((3560, 3860), ((3600, 3880), (3640, 3880)), (3672, 3862), -8, 112, 0.25, 60, 0.24, 0.4, (0.8, 0.86))
    over += arm((3432, 3862), ((3395, 3880), (3360, 3878)), (3330, 3862), 188, 92, 0.25, 64, 0.4, 0.56, (0.84, 0.9))
    over += arm((3560, 3850), ((3615, 3850), (3650, 3810)), (3665, 3755), -62, 118, 0.7, 70, 0.76, 0.86)
    over += arm((3432, 3852), ((3380, 3850), (3350, 3810)), (3338, 3760), 238, 98, 0.7, 74, 0.8, 0.9)
    # snapping: a motion crescent beside each raised claw
    for n_, (cx, cy, r, a0, a1) in enumerate(((3690, 3708, 170, 8, 58), (3315, 3723, 150, 122, 172))):
        over.append(item(g.crescent(cx, cy, r, a0, a1, 26), WHITE, INK * 0.8, (cx, cy), 0.9 + 0.03 * n_, 0.97 + 0.03 * n_))
    return {
        'note': 45,
        'label': "The pale hollow in the salmon swoop's hooked loop: hold A2 to play; a hermit crab's eyes pop up out "
                 'of it, its face fills the shell, its claws reach out and its legs hook over the lip, then it waves '
                 'both claws up, snapping hello',
        'effects': [{'effect': 'sprites', 'place': 'on', 'items': on},
                    {'effect': 'sprites', 'place': 'over', 'items': over}],
        'crop': (3080, 3440, 820, 820),
    }


# ---- note-49 C#3: the almond is a bud that opens into a cactus bloom -----------------------------------------------

def petal(c, ang, r0, ln, w, seed) -> str:
    """A broad, rounded, waxy petal from r0 out to r0 + ln along ang (degrees clockwise from right): spoon-shaped,
    widest two-thirds out, with a soft point."""
    rnd = random.Random(seed)
    L, R = [], []
    N = 10
    for i in range(N + 1):
        s = i / N
        hw = w * (0.22 + 0.78 * s ** 0.75) * max(0.0, 1 - s ** 2.4) ** 0.6
        hw *= 1 + 0.07 * rnd.uniform(-1, 1)
        L.append((r0 + ln * s * 0.97, -hw))
        R.append((r0 + ln * s * 0.97, hw))
    pts = L[:-1] + [(r0 + ln, rnd.uniform(-3, 3))] + R[::-1][1:]
    pts = [rot((c[0] + x, c[1] + y), c, ang) for x, y in pts]
    return smooth(pts)


def cactus_bloom() -> dict:
    INK = 12
    OUT, MID, INN = '#FF4F9A', '#FF8CC4', '#FFC8E2'
    C = (3808.0, 4062.0)
    TIP = (3772.0, 4092.0)
    items = []
    # 0-0.05: the bud's tip parts and three petal tips poke out
    for n_, a in enumerate((112, 146, 180)):
        items.append(item(petal(TIP, a, -24, 92, 30, 90 + n_), OUT, INK, TIP, 0.0, 0.05))
    # then three rings of broad waxy petals open out, one petal after another: outer, middle, inner
    rings = [  # count, start angle, r0, length, width, colour, window start, step
        (9, 8, 16, 150, 50, OUT, 0.06, 0.028),
        (8, 30, 12, 112, 40, MID, 0.32, 0.03),
        (6, 0, 8, 74, 38, INN, 0.57, 0.034),
    ]
    shines = []
    for ri, (cnt, a0, r0, ln, w, col, ws, st) in enumerate(rings):
        cc = (C[0] - 6 * ri, C[1] + 5 * ri)  # inner rings sit a little toward the tip: a cup tilted at us
        rnd = random.Random(ri)
        order = sorted(range(cnt), key=lambda j: math.cos(math.radians(a0 + 360 * j / cnt - 145)), reverse=True)
        for n_, j in enumerate(order):
            ang = a0 + 360 * j / cnt + rnd.uniform(-9, 9)
            sq = 0.8 if math.cos(math.radians(ang + 40)) > 0.4 else 1.0  # petals toward the lobe sit back, shorter
            s = ws + st * n_
            items.append(item(petal(cc, ang, r0, ln * sq * rnd.uniform(0.92, 1.08), w * rnd.uniform(0.9, 1.1),
                                    100 + ri * 10 + j), col, INK, cc, s, s + 0.1))
            if ri == 0 and j in (4, 7):
                sx, sy = rot((cc[0] + r0 + ln * sq * 0.8, cc[1] - w * 0.12), cc, ang)
                shines.append(item(lump(sx, sy, 18, 7, ang + 6, 120 + j, 0.1), WHITE, 0, (sx, sy), 0.9, 0.97))
    # a fuzzy mass of stamens, then the lime stigma at its heart, then the waxy shines
    S = (C[0] - 14, C[1] + 11)
    bumps = []
    rnd = random.Random(7)
    for i in range(30):
        a = i / 30 * 2 * math.pi
        r = 50 + (9 if i % 2 else 0) + rnd.uniform(-4, 4)
        bumps.append((S[0] + math.cos(a) * r, S[1] + math.sin(a) * r))
    items.append(item(smooth(bumps), YELLOW, INK, S, 0.78, 0.88))
    star = []
    for i in range(12):
        a = -math.pi / 2 + i / 12 * 2 * math.pi
        r = 30 if i % 2 == 0 else 12
        star.append((S[0] + math.cos(a) * r, S[1] + math.sin(a) * r))
    items.append(item(smooth(star), LIME, INK * 0.8, S, 0.86, 0.95))
    items += shines
    return {
        'note': 49,
        'label': "The pale almond at the foot of the bunny's spiny lobe: hold C#3 to play; it is a bud: its tip parts "
                 'and a waxy cactus bloom opens, ring after ring of broad pink petals, with a fuzzy yellow heart and '
                 'a lime stigma',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (3550, 3800, 560, 560),
    }


# ---- note-65 F4: the bunny's eye turns into a beating heart --------------------------------------------------------

def heart_eye() -> dict:
    INK = 11
    RED, PINKH, GLINT = '#FF3D7F', '#FFA0C8', '#FFFFFF'
    E = (4306.0, 3895.0)
    items = [
        item(heart(E[0], E[1] - 4, 136, -4, 1), RED, INK, E, 0.0, 0.05, out=(0.16, 0.22)),
        item(heart(E[0], E[1] - 16, 178, -6, 2), RED, INK, E, 0.15, 0.27, out=(0.66, 0.7)),
        # the first beat: it swells past itself and sinks back
        item(heart(E[0], E[1] - 22, 222, -6, 3), RED, INK, E, 0.4, 0.48, out=(0.5, 0.6)),
        # the second beat stays: biggest
        item(heart(E[0], E[1] - 26, 238, -7, 4), RED, INK, E, 0.64, 0.74),
        item(heart(E[0] - 8, E[1] - 30, 122, -7, 5), PINKH, 0, (E[0] - 8, E[1] - 30), 0.72, 0.82),
        item(lump(E[0] - 52, E[1] - 72, 20, 12, -35, 6, 0.08), GLINT, 0, (E[0] - 52, E[1] - 72), 0.8, 0.86),
        # two small hearts pop off it, up and to the right
        item(heart(4462, 3738, 74, 14, 7), RED, INK, (4400, 3800), 0.86, 0.94),
        item(heart(4512, 3640, 56, 22, 8), PINKH, INK * 0.9, (4440, 3720), 0.92, 1.0),
    ]
    return {
        'note': 65,
        'label': "The white of the bunny's sleepy eye: hold F4 to play; it turns into a pink heart that swells past "
                 'its lid and beats bigger twice, then two little hearts pop off it',
        'effects': [{'effect': 'vanish', 'span': [0.02, 0.05]},
                    {'effect': 'sprites', 'place': 'over', 'items': items}],
        'crop': (4100, 3550, 474, 474),
    }


DESIGNS = [flytrap(), donut(), hermit_crab(), cactus_bloom(), heart_eye()]

if __name__ == '__main__':
    k.run(DESIGNS)
