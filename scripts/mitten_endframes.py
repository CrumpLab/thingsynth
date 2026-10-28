# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1", "shapely>=2"]
# ///
"""Five end frames (Lower 1 1/3' drawbar fully out) for the mitten: the lavender-blue mitten hand, bottom left, the
raised arm of the grey lying creature (the party narwhal of key click). It comes up from behind the pink cap, the
grey body over the base of its arm, its palm pointing up and to the right with a rounded upper lobe and a bigger
thumb lobe.

    uv run scripts/mitten_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (1100, 2850, 1300, 1300)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db8/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 14
MITT = '#a9b8f0'  # the mitten as it reads over the wash: a soft lavender blue
CANDY = ['#f64c76', '#ffe066', '#ff9f43', '#7fe0c8', '#c4a3f0', '#2DFFF4', '#ff9fc4', '#a8ec6b']
PALM = (1760.0, 3850.0)
TIP = (1785.0, 3700.0)  # the upper lobe's tip
THUMB = (1925.0, 3820.0)  # the thumb lobe's far edge
WRIST = (1565.0, 4010.0)
AXIS = -58.0  # the arm's direction, degrees (up and to the right)
MITTEN = ['f241']
MITTEN_LINES = ['i0942', 'i0126', 'i0945', 'i0131', 'i0946', 'i0132', 'i0129', 'i0128']


def draw(front: str = '', again: list[str] | None = None, over: str = '', hide: bool = False) -> Image.Image:
    """`front` drawn over the painting, then the `again` shapes and their ink laid back on top, then `over`. With
    `hide`, the mitten's fill and its own outline are taken out first (what the app's vanish does)."""
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        if hide:
            im = m.compose(front=front or '<g/>', fill_colour={'f241': 'none'}, ink_over={i: 'M0 0' for i in MITTEN_LINES})
        else:
            im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def blob(cx, cy, rx, ry, rot=0.0, seed=0, wob=0.08, n=9) -> str:
    """A lumpy, hand-drawn oval: a closed smooth curve through jittered points."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for k in range(n):
        t = k / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(t) * rx * f, math.sin(t) * ry * f
        pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
    return m.smooth(pts)


def petal(cx, cy, ang, r0, r1, w, seed) -> str:
    """A lumpy petal from radius r0 to r1 along `ang`, widest two thirds out, rounded at the end."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    P = lambda u, v: (cx + ca * u - sa * v, cy + sa * u + ca * v)
    L = r1 - r0
    j = lambda: 1 + (rnd.random() - 0.5) * 0.18
    pts = [P(r0, -w * 0.25), P(r0 + L * 0.35, -w * 0.48 * j()), P(r0 + L * 0.7, -w * 0.52 * j()), P(r0 + L * 0.95, -w * 0.28 * j()),
           P(r1, 0), P(r0 + L * 0.95, w * 0.3 * j()), P(r0 + L * 0.7, w * 0.5 * j()), P(r0 + L * 0.35, w * 0.46 * j()), P(r0, w * 0.25)]
    return m.smooth(pts)


_clips = [0]


def mitten_copy(dx: float, dy: float, rot: float = 0.0, s: float = 1.0, fill: str = MITT, about=WRIST, cut: float = -40.0) -> str:
    """The painted mitten itself (its fill and its own outline), turned by `rot` degrees and scaled by `s` about its
    wrist, then moved by (dx, dy): the same lumpy shape, opaque. Everything further down the arm than `cut` (px
    along the arm from the wrist) is clipped off, so a new arm can take over there."""
    x, y = about
    a = math.radians(AXIS)
    ca, sa = math.cos(a), math.sin(a)
    Q = lambda u, v: p(x + ca * u - sa * v, y + sa * u + ca * v)
    _clips[0] += 1
    cid = f'mc{_clips[0]}'
    clip = f'<clipPath id="{cid}"><path d="M{Q(cut, -900)}L{Q(900, -900)}L{Q(900, 900)}L{Q(cut, 900)}Z"/></clipPath>'
    tf = f'translate({x + dx:.1f} {y + dy:.1f}) rotate({rot:.1f}) scale({s:.3f}) translate({-x:.1f} {-y:.1f})'
    lines = ''.join(f'<path d="{m.INKS[i]}"/>' for i in MITTEN_LINES)
    return (f'<defs>{clip}</defs><g transform="{tf}"><g clip-path="url(#{cid})"><path d="{m.FILLS["f241"]}" fill="{fill}"/>'
            f'<g fill="#000">{lines}</g></g></g>')


# ---- 1. flower ------------------------------------------------------------------------------------------------------
FLOWER_COLS = ['#ff9f43', '#f64c76', '#ffe066', MITT, MITT, '#ff9fc4', '#7fe0c8']


def v1_flower() -> Image.Image:
    """Mitten flower: the mitten opens into a big candy flower held up on its arm: seven lumpy petals open round the
    palm one per drawbar step, the two where its lobes were in its own lavender blue, leaving the arm as its
    stalk, and the palm turns into a golden centre last."""
    cx, cy = PALM
    rnd = random.Random(2)
    out = ''
    for k in range(7):
        ang = 185 + k * 48 + (rnd.random() - 0.5) * 10
        L = 300 + rnd.random() * 70
        out += outlined(petal(cx, cy, ang, 80, L, 175 + rnd.random() * 40, k), FLOWER_COLS[k], INK)
    over = outlined(blob(cx, cy, 135, 122, AXIS, 7, 0.07), '#ffd23f', INK)
    over += outlined(blob(cx + 10, cy - 5, 70, 62, AXIS, 9, 0.1), '#ffb627', INK * 0.8)
    return draw(out, ['f004', 'f014', 'f023', 'f024'], over)


# ---- 2. reaching high -----------------------------------------------------------------------------------------------
def risen_arm(dx, dy, rot, s, col, base, w, bend=(0.0, 0.0)) -> str:
    """A mitten copy moved by (dx, dy) and turned by rot, on an arm from `base` (hidden behind something) up to its
    cuff: the outlined arm, the mitten over it, then the arm's fill again over the mitten's cut-off wrist, so the
    two join without a seam."""
    a = math.radians(AXIS + rot)
    cx, cy = WRIST[0] + dx, WRIST[1] + dy
    end = (cx + math.cos(a) * 110 * s, cy + math.sin(a) * 110 * s)
    c1 = (base[0] + (cx - base[0]) * 0.3 + bend[0], base[1] + (cy - base[1]) * 0.3 + bend[1])
    c2 = (cx - math.cos(a) * 220 * s, cy - math.sin(a) * 220 * s)
    P = bez(base, c1, c2, end, 40)
    out = outlined(tube(P, w, w * 0.95), col, INK)
    out += mitten_copy(dx, dy, rot, s, col)
    out += f'<path d="{tube(P[-14:-2], w * 0.95 - INK * 0.6, w * 0.95 - INK * 0.6)}" fill="{col}"/>'
    return out


def v2_reach() -> Image.Image:
    """Reaching high: the narwhal's arm stretches up out of the crowd, bending, and its mitten waves high above the
    others, motion crescents either side of it."""
    dx, dy, rot, s = 300.0, -480.0, -30.0, 0.95
    out = risen_arm(dx, dy, rot, s, MITT, (1590, 4120), 106, (-150, -40))
    a = math.radians(AXIS + rot)
    hx, hy = WRIST[0] + dx + math.cos(a) * 210, WRIST[1] + dy + math.sin(a) * 210
    for (a0, a1, r) in [(-210, -160, 270), (-25, 25, 270), (-200, -170, 345), (-15, 15, 345)]:
        out += g.swoosh(hx, hy, r, a0, a1, 40, '#fffbe6')
    return draw(out, ['f004', 'f014', 'f023', 'f024'], '', hide=True)


# ---- 3. hands up ----------------------------------------------------------------------------------------------------
HANDS = [  # (cuff x, cuff y, rot, scale, colour, arm base): copies of the mitten peeping up behind the narwhal's back
    (1290, 3840, -40, 0.8, '#ffe066', (1170, 4160)),
    (1985, 3790, -24, 0.8, '#7fe0c8', (2000, 4060)),
    (2265, 3770, 22, 0.72, '#f64c76', (2290, 4020)),
]


def v3_hands_up() -> Image.Image:
    """Hands up: a crowd of candy mittens comes up from behind the narwhal's back round its own, as at a concert,
    one more per drawbar step."""
    out = ''.join(risen_arm(cx - WRIST[0], cy - WRIST[1], rot, s, col, base, 118 * s) for cx, cy, rot, s, col, base in HANDS)
    return draw(out, ['f004', 'f014', 'f023', 'f024', 'f241'])


# ---- 4. firework ----------------------------------------------------------------------------------------------------
def ray(cx, cy, ang, r0, r1, w, seed) -> str:
    """A flame-like ray: round at its inner end, swelling, then drawn to a point at r1."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    P = lambda u, v: (cx + ca * u - sa * v, cy + sa * u + ca * v)
    L = r1 - r0
    k = 1 + (rnd.random() - 0.5) * 0.3
    return (f'M{p(*P(r0, 0))}C{p(*P(r0, -w * 0.5))} {p(*P(r0 + L * 0.3, -w * 0.62 * k))} {p(*P(r0 + L * 0.5, -w * 0.45))}'
            f'C{p(*P(r0 + L * 0.7, -w * 0.25))} {p(*P(r0 + L * 0.9, -w * 0.12))} {p(*P(r1, 0))}'
            f'C{p(*P(r0 + L * 0.9, w * 0.1))} {p(*P(r0 + L * 0.7, w * 0.22))} {p(*P(r0 + L * 0.5, w * 0.42))}'
            f'C{p(*P(r0 + L * 0.3, w * 0.6 / k))} {p(*P(r0, w * 0.5))} {p(*P(r0, 0))}Z')


def comet(cx, cy, ang, r0, r1, w, seed) -> str:
    """A firework streak flying out from (cx, cy): a point at r0 swelling to a round head at r1."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    P = lambda u, v: (cx + ca * u - sa * v, cy + sa * u + ca * v)
    L = r1 - r0
    k = 1 + (rnd.random() - 0.5) * 0.25
    return (f'M{p(*P(r0, 0))}C{p(*P(r0 + L * 0.4, -w * 0.12))} {p(*P(r0 + L * 0.7, -w * 0.38 * k))} {p(*P(r1 - w * 0.4, -w * 0.5))}'
            f'C{p(*P(r1 + w * 0.15, -w * 0.52))} {p(*P(r1 + w * 0.15, w * 0.52))} {p(*P(r1 - w * 0.4, w * 0.5))}'
            f'C{p(*P(r0 + L * 0.7, w * 0.38 / k))} {p(*P(r0 + L * 0.4, w * 0.12))} {p(*P(r0, 0))}Z')


def v4_firework() -> Image.Image:
    """Firework: high and bright. The mitten flings up a rocket on a wavy trail, and it bursts high above into a ring
    of big candy comets flying outward from a white-hot flash."""
    tx, ty = TIP
    bx, by = 1960.0, 3200.0
    P = bez((tx, ty + 10), (tx + 90, ty - 180), (bx - 160, by + 320), (bx, by), 30)
    out = outlined(tube(P[:-3], 14, 30), '#fff6c2', INK * 0.8)
    cols = ['#ffe066', '#f64c76', '#7fe0c8', '#ff9f43', '#c4a3f0', '#ff9fc4']
    rnd = random.Random(5)
    for k in range(12):
        ang = -90 + k * 30 + (rnd.random() - 0.5) * 10
        out += outlined(comet(bx, by, ang, 110, 380 + rnd.random() * 70, 100, k), cols[k % 6], INK)
    out += outlined(blob(bx, by, 130, 120, 0, 11, 0.14, 11), '#fff6c2', INK)
    out += outlined(blob(bx + 5, by - 4, 66, 60, 30, 12, 0.12), '#ffffff', INK * 0.8)
    return draw(out, ['f241', 'f014', 'f023', 'f024'], '')


# ---- 5. coral hand --------------------------------------------------------------------------------------------------
LOBES = [  # (base inside the mitten, angle out, length, width): first buds out of its two lobes and its back
    ((1765, 3730), -100, 240, 150),
    ((1800, 3725), -55, 240, 145),
    ((1880, 3790), -20, 230, 150),
    ((1880, 3870), 15, 210, 140),
    ((1640, 3770), -125, 220, 140),
]
SUB = [  # second buds from the first ones' ends: (which, angle, length, width)
    (0, -125, 190, 120), (0, -80, 190, 120), (1, -40, 180, 115), (4, -150, 170, 110),
]


def v5_coral() -> Image.Image:
    """Coral hand: the mitten's own lobes bud new lobes, and those bud again, until the mitten is a big branching
    coral of rounded fingers in its own lavender blue (one bud per drawbar step)."""
    shapes = []
    ends = []
    for k, ((x, y), ang, L, w) in enumerate(LOBES):
        shapes.append(petal(x, y, ang, -40, L, w, k + 40))
        a = math.radians(ang)
        ends.append((x + math.cos(a) * (L - 60), y + math.sin(a) * (L - 60)))
    for k, (i, ang, L, w) in enumerate(SUB):
        x, y = ends[i]
        shapes.append(petal(x, y, ang, -40, L, w, k + 60))
    base = m.FILLS['f241']
    out = ''.join(outlined(d, MITT, INK) for d in shapes)
    out += outlined(base, MITT, INK)
    out += ''.join(f'<path d="{d}" fill="{MITT}"/>' for d in shapes)
    out += f'<path d="{base}" fill="{MITT}"/>'
    return draw(out, ['f004', 'f014', 'f023', 'f024'], '')



VERSIONS = [
    ('1-flower', 'Mitten flower', v1_flower),
    ('2-reaching-high', 'Reaching high', v2_reach),
    ('3-hands-up', 'Hands up', v3_hands_up),
    ('4-firework', 'Firework', v4_firework),
    ('5-coral-hand', 'Coral hand', v5_coral),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (drawbar in)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.45
    tw, th = int(w * s), int(h * s)
    sheet = Image.new('RGB', (tw * 3 + 40, (th + 60) * 2 + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = 10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 60)
        d.text((x, y), label, fill='black', font=font)
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
    sheet.save(OUT / 'sheet.png')
    print('wrote', OUT / 'sheet.png')


if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    main()


# ---- chosen: reaching high ------------------------------------------------------------------------------------------
# Picked: 2, reaching high, on its own (no firework: restraint, and the area is busy). The Lower 1 1/3' drawbar, 0-8 in
# integer steps: the narwhal's arm grows up out of the gap between the pink cap and its body one segment per step over
# steps 1-6 (the painted mitten fading over steps 1-2), the raised mitten pops onto the end of the arm on step 7 with a
# little overshoot, and the motion crescents flick out either side of it on step 8. Every arrival lands on k/8.
# The arm is drawn twice, an outlined layer then a fill-only layer, so its segments join into one shape; it sits above
# the ink with the narwhal's body and the pink cap masked in front ("around"), so its base tucks behind them.
#
#     uv run scripts/mitten_endframes.py reach     # progression strip, steps and end frame
#     uv run scripts/mitten_endframes.py export    # docs/objects/lower-db8/build.json
REACH_DX, REACH_DY, REACH_ROT, REACH_S = 300.0, -480.0, -30.0, 0.95
ARM_BASE, ARM_W, ARM_BEND = (1600.0, 4130.0), 106.0, (-150.0, -40.0)
COL = '#8dc9c2'  # f241's translucent blue as it reads over the wash here: a soft blue-teal
STEP = 1 / 8
FRONT_IDS = ['f014', 'f004']  # the narwhal's body and the pink cap, in front of the arm's base
# Ink the vanish takes with the mitten (it runs along f241) but which is the narwhal's: the edge where the wrist met
# its body, and the crease below it. Laid back over everything from the first step so the body keeps its outline.
KEEP_INK = ['i0941', 'i0950']
VANISH_INK = MITTEN_LINES + ['i0941', 'i0125', 'i0950', 'i0136']


def flatten(d: str, n: int = 8) -> list[list[tuple[float, float]]]:
    """The subpaths of an M/C/Z path as polygons, each cubic sampled at n points."""
    toks = re.findall(r'[MCZ]|-?\d+\.?\d*', d)
    polys, cur, i, cmd = [], [], 0, None
    while i < len(toks):
        t = toks[i]
        if t in 'MCZ':
            cmd = t
            i += 1
            if t == 'Z' and cur:
                polys.append(cur)
                cur = []
            continue
        if cmd == 'M':
            if cur:
                polys.append(cur)
            cur = [(float(toks[i]), float(toks[i + 1]))]
            i += 2
            cmd = 'L'
        elif cmd == 'L':
            cur.append((float(toks[i]), float(toks[i + 1])))
            i += 2
        elif cmd == 'C':
            q = [float(v) for v in toks[i:i + 6]]
            p0 = cur[-1]
            for k in range(1, n + 1):
                u = k / n
                b = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3]
                cur.append((b[0] * p0[0] + b[1] * q[0] + b[2] * q[2] + b[3] * q[4], b[0] * p0[1] + b[1] * q[1] + b[2] * q[3] + b[3] * q[5]))
            i += 6
    if cur:
        polys.append(cur)
    return polys


def clip_half(poly, f):
    """Sutherland-Hodgman against one half-plane: keep where f(pt) >= 0."""
    out = []
    for k in range(len(poly)):
        a, b = poly[k - 1], poly[k]
        fa, fb = f(a), f(b)
        if fb >= 0:
            if fa < 0:
                t = fa / (fa - fb)
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            out.append(b)
        elif fa >= 0:
            t = fa / (fa - fb)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def poly_d(poly, tol: float = 0.6) -> str:
    """A polygon as a path, thinned (Douglas-Peucker, `tol` px) so the build stays small."""
    from shapely.geometry import LineString
    if tol and len(poly) > 8:
        poly = list(LineString(list(poly) + [poly[0]]).simplify(tol).coords)[:-1]
    return 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in poly) + 'Z'


def reach_dir() -> tuple[float, float]:
    a = math.radians(AXIS + REACH_ROT)
    return math.cos(a), math.sin(a)


def cuff() -> tuple[float, float]:
    return WRIST[0] + REACH_DX, WRIST[1] + REACH_DY


def raised(d: str, extra: float = 1.0, cut: float = -40.0) -> list[str]:
    """A painted path (the mitten's fill or one of its ink strokes) as it sits on the raised arm: cut off below the
    wrist, turned, scaled and moved like mitten_copy, as plain polygons in canvas px."""
    x, y = WRIST
    a = math.radians(AXIS)
    ca, sa = math.cos(a), math.sin(a)
    r = math.radians(REACH_ROT)
    cr, sr = math.cos(r), math.sin(r)
    s = REACH_S * extra
    out = []
    for poly in flatten(d):
        q = clip_half(poly, lambda pt: (pt[0] - x) * ca + (pt[1] - y) * sa - cut)
        if len(q) < 3:
            continue
        moved = []
        for px, py in q:
            u, v = (px - x) * s, (py - y) * s
            moved.append((x + REACH_DX + u * cr - v * sr, y + REACH_DY + u * sr + v * cr))
        out.append(poly_d(moved))
    return out


def arm_line(n: int = 48):
    """The arm's centreline from behind the body up to inside the raised palm, and its lumpy half-widths."""
    dx, dy = reach_dir()
    cx, cy = cuff()
    s = REACH_S
    end = (cx + dx * 110 * s, cy + dy * 110 * s)
    c1 = (ARM_BASE[0] + (cx - ARM_BASE[0]) * 0.3 + ARM_BEND[0], ARM_BASE[1] + (cy - ARM_BASE[1]) * 0.3 + ARM_BEND[1])
    c2 = (cx - dx * 220 * s, cy - dy * 220 * s)
    P = bez(ARM_BASE, c1, c2, end, n - 1)
    # lumpy, and fuller where it comes out between the pink cap and the body, so it fills that gap
    W = [ARM_W * (1 - 0.05 * u) + 6 * math.sin(u * math.pi * 4.3 + 0.7) + 40 * max(0.0, 1 - u / 0.22) for u in (i / (n - 1) for i in range(n))]
    return P, W


def tube_pts(P, W) -> list[tuple[float, float]]:
    return [tuple(map(float, q.split())) for q in tube_w(P, W)[1:-1].split('L')]


def tube_w(P, W) -> str:
    """An outlined limb along P with its own half-width at every point, flat at the start, round at the end."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        ddx, ddy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(ddx, ddy) or 1
        nx, ny = -ddy / d, ddx / d
        L.append((x + nx * W[i], y + ny * W[i]))
        R.append((x - nx * W[i], y - ny * W[i]))
    ex, ey = P[-1]
    ha = math.atan2(ey - P[-2][1], ex - P[-2][0])
    la = math.atan2(L[-1][1] - ey, L[-1][0] - ex)
    side = 1 if math.sin(ha - la) > 0 else -1  # turn from the L side through the heading to the R side
    cap = [(ex + math.cos(la + side * math.pi * k / 12) * W[-1], ey + math.sin(la + side * math.pi * k / 12) * W[-1]) for k in range(1, 12)]
    return 'M' + 'L'.join(p(*q) for q in L + cap + R[::-1]) + 'Z'


def crescent(cx, cy, r, a0, a1, w) -> str:
    """A motion arc from a0 to a1 degrees round (cx, cy), thickest in the middle (as g.swoosh, as one path)."""
    n = 28
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        th = w * math.sin(math.pi * t) ** 0.9
        outer.append((cx + math.cos(a) * (r + th / 2), cy + math.sin(a) * (r + th / 2)))
        inner.append((cx + math.cos(a) * (r - th / 2), cy + math.sin(a) * (r - th / 2)))
    return 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'


def rnd_pt(q) -> list[float]:
    return [round(q[0], 1), round(q[1], 1)]


def reach_items() -> list[dict]:
    """The arm, the raised mitten and the motion crescents ('around': the body and pink cap stay in front)."""
    P, W = arm_line()
    n = len(P)
    bounds = [round(u * (n - 1)) for u in (0, 0.24, 0.4, 0.55, 0.7, 0.85, 1)]  # the first reaches out past the body
    segs = []
    for k in range(6):
        i0, i1 = max(0, bounds[k] - 2), bounds[k + 1]
        segs.append((P[i0:i1 + 1], W[i0:i1 + 1], k * STEP, (k + 1) * STEP))
    items = []
    for Q, V, s0, s1 in segs:  # the outlined layer, one segment per step
        items.append({'d': tube_w(Q, V), 'fill': COL, 'edge': INK, 'at': rnd_pt(Q[0]), 'start': round(s0, 4), 'end': round(s1, 4), 'grow': 'scale'})
    for Q, V, s0, s1 in segs:  # the fill-only layer that melts the joins
        items.append({'d': tube_w(Q, [w - INK / 2 for w in V]), 'fill': COL, 'edge': 0, 'at': rnd_pt(Q[0]), 'start': round(s0, 4), 'end': round(s1, 4), 'grow': 'scale'})
    c = rnd_pt(cuff())
    h0, h1 = 6 * STEP, 7 * STEP
    # step 7: the mitten pops out of the arm's end, swelling a little past its size first (a bigger copy that grows
    # in and sinks away under it)
    for d in raised(m.FILLS['f241'], 1.12):
        items.append({'d': d, 'fill': COL, 'edge': INK, 'at': c, 'start': round(h0, 4), 'end': round(h0 + 0.06, 4), 'grow': 'scale',
                      'outStart': round(h0 + 0.06, 4), 'outEnd': round(h1 - 0.005, 4)})
    for d in raised(m.FILLS['f241']):
        items.append({'d': d, 'fill': COL, 'edge': 0, 'at': c, 'start': round(h0 + 0.01, 4), 'end': round(h1, 4), 'grow': 'scale'})
    for i in MITTEN_LINES[::2]:  # each stroke is in the ink twice; once is enough
        for d in raised(m.INKS[i], cut=-5.0):
            items.append({'d': d, 'fill': '#000', 'edge': 0, 'at': c, 'start': round(h0 + 0.01, 4), 'end': round(h1, 4), 'grow': 'scale'})
    # the arm's fill again over the mitten's cut-off wrist, so arm and mitten are one shape
    items.append({'d': tube_w(P[-14:-2], [w * 0.95 - INK * 0.6 for w in W[-14:-2]]), 'fill': COL, 'edge': 0, 'at': c,
                  'start': round(h0 + 0.01, 4), 'end': round(h1, 4), 'grow': 'scale'})
    # step 8: motion crescents flick out either side of the hand, the inner pair first
    dx, dy = reach_dir()
    hx, hy = cuff()[0] + dx * 210, cuff()[1] + dy * 210
    for k, (a0, a1, r) in enumerate([(-218, -152, 290), (-33, 33, 290), (-208, -162, 370), (-23, 23, 370)]):
        am = math.radians((a0 + a1) / 2)
        at = (hx + math.cos(am) * (r - 70), hy + math.sin(am) * (r - 70))
        s0 = 7 * STEP + (0.0 if k < 2 else 0.03)
        items.append({'d': crescent(hx, hy, r, a0, a1, 30), 'fill': '#fffbe6', 'edge': 11, 'at': rnd_pt(at),
                      'start': round(s0, 4), 'end': round(min(1.0, s0 + 0.09), 4), 'grow': 'scale'})
    return items


def base_items() -> list[dict]:
    """Where the arm comes out between the pink cap and the body, the 'around' mask keeps a band 22 px wide round
    them clear of the arm, and the wash would show there as a strip. These fill that band (and only that band, outside
    the front shapes' own outlines) with the arm's outline and fill, so the arm runs right up to them."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    P, W = arm_line()
    k = round(0.24 * (len(P) - 1))
    arm = Polygon(tube_pts(P[:k + 1], W[:k + 1])).buffer(0)
    front = unary_union([Polygon(flatten(m.FILLS[f])[0]).buffer(0) for f in FRONT_IDS])
    band = front.buffer(24, join_style=1).difference(front.buffer(6, join_style=1))
    out = []
    for geom, col in ((arm.buffer(INK / 2).intersection(band), '#000'), (arm.buffer(-INK / 2).intersection(band), COL)):
        for poly in getattr(geom, 'geoms', [geom]):
            if poly.is_empty or poly.geom_type != 'Polygon' or poly.area < 20:
                continue
            out.append({'d': poly_d(list(poly.exterior.coords)[:-1]), 'fill': col, 'edge': 0, 'at': rnd_pt(ARM_BASE),
                        'start': 0.0, 'end': round(STEP, 4), 'grow': 'scale'})
    return out


def keep_items() -> list[dict]:
    """The narwhal's own ink that the mitten's vanish would take, laid back over everything from the first step."""
    return [{'d': m.INKS[i], 'fill': '#000', 'edge': 0, 'at': [round(v, 1) for v in m.IP[i]['bbox'][:2]], 'start': 0.0, 'end': 0.001, 'grow': 'scale'}
            for i in KEEP_INK]


def reach_effects() -> list[dict]:
    return [
        {'effect': 'vanish', 'parts': ['body'], 'span': [0.0, round(2 * STEP, 4)]},
        # parts [] keeps the mitten's own shape out of the mask: it has faded, and the arm draws where it was
        {'effect': 'sprites', 'place': 'around', 'parts': [], 'front': FRONT_IDS, 'items': reach_items()},
        {'effect': 'sprites', 'place': 'over', 'items': base_items() + keep_items()},
    ]


_painted: dict[str, Image.Image] = {}


def reach_frame(t: float) -> Image.Image:
    """The app's stack, previewed: the mitten fading, the sprites above the ink with the front shapes masked out (a 44
    px band round them, as topGroup does), then the kept ink."""
    if not _painted:
        _painted['a'] = m.compose()
        _painted['b'] = m.compose(fill_colour={'f241': 'none'}, ink_over={i: 'M0 0' for i in VANISH_INK})
        fr = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in FRONT_IDS)
        _painted['mask'] = m.svg(fr).getchannel('A')
    vf = max(0.0, min(1.0, t / (2 * STEP)))
    im = Image.blend(_painted['a'], _painted['b'], vf)
    spr = m.svg(g.sprite_svg(reach_items(), t))
    keep = Image.new('L', spr.size, 255)
    keep.paste(0, mask=_painted['mask'])
    alpha = spr.getchannel('A')
    spr.putalpha(Image.composite(alpha, Image.new('L', spr.size, 0), keep))
    im.alpha_composite(spr)
    if t > 0:
        im.alpha_composite(m.svg(g.sprite_svg(base_items() + keep_items(), t)))
    return im


def strip(frames, labels, path, sc=0.42):
    tiles = [reach_frame(t) for t in frames]
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    cols = min(len(tiles), 5)
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 46) * rows + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (lab, tile) in enumerate(zip(labels, tiles)):
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 46)
        d.text((x, y), lab, fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
    im.save(path)
    return tiles


def reach_main() -> None:
    out = OUT.parent / 'reaching-high'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = strip(frames, [f'frame {t:.2f}' for t in frames], out / 'strip.png')
    tiles[-1].save(out / 'end-frame.png')
    strip([k / 8 for k in range(9)] + [0.81], [f'step {k}' for k in range(9)] + ['mid-step 7 (overshoot)'], out / 'steps.png', 0.3)
    print('wrote', out)


if __name__ == '__main__' and 'reach' in __import__('sys').argv[1:]:
    reach_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The mitten hand: drag for the Lower 1 1/3' drawbar; the narwhal's arm stretches up a segment per step "
                 "and its mitten pops up waving high above the crowd",
        'effects': reach_effects(),
    }
    dest = ROOT / 'docs/objects/lower-db8/build.json'
    dest.write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', dest, len(build['effects'][1]['items']), 'shapes')
