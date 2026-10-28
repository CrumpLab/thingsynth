# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Lower 5 1/3' drawbar fully out) for the coral antler hand, bottom centre: a translucent coral
hand rising from the red ground, its tall middle finger an antler with four prongs on its right, a thumb with a
lavender nail on its left, and a pink tongue-like curl (f086) in a loop at the bottom of its palm.

    uv run scripts/coralhand_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (2560, 2300, 1250, 1300)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db2/endframes'
p, outlined, circle, tube, bez, crescent = m.p, m.outlined, g.circle, g.tube, g.bez, g.crescent
INK = 14
HAND = ['f076', 'f086']
# the painted shapes laid over the hand: the lavender thumbnail and the fan's pale pills
NEAR = ['f087', 'f088', 'f091', 'f092']
CORAL, PINK, LAV, YEL, CYAN, LIME, CREAM = '#ff6f61', '#F681A5', '#C681F6', '#ffe066', '#2DFFF4', '#d4f55a', '#fff1d6'

# where things can grow out of the hand: the antler's top, its four prong tips, the thumb tip, the left nub
TOP_L, TOP_R = (3225.0, 2700.0), (3280.0, 2705.0)
PRONGS = [(3392.0, 2690.0), (3418.0, 2790.0), (3425.0, 2890.0), (3365.0, 2975.0)]
THUMB = (3062.0, 2925.0)
NUB = (3005.0, 3345.0)
PALM_EYE = (3205.0, 3190.0)
MOUTH = (3255.0, 3368.0)


def draw(front: str = '', again: list[str] | None = None, over: str = '', hide: list[str] | None = None) -> Image.Image:
    """New shapes over the painting (`front`), the named painted shapes (and their ink) laid back on top, then `over`
    on top of everything. `hide` drops fills (and the ink round them) first, as the app's vanish would."""
    tags, inks = m.FILL_TAGS, m.INKS
    if hide:
        keep = {s for f in NEAR for s in m.own_ink(f)}
        gone = {s for f in hide for s in m.own_ink(f)} - keep
        m.FILL_TAGS = [t for t in tags if not any(f'id="{f}"' in t for f in hide)]
        m.INKS = {k: v for k, v in inks.items() if k not in gone}
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK, m.FILL_TAGS, m.INKS = [], [], tags, inks
    if over:
        im.alpha_composite(m.svg(over))
    return im


BASE = None


def col_at(x: float, y: float) -> str:
    """The hand's colour as painted at (x, y), so a part growing out of it there joins without a seam."""
    global BASE
    if BASE is None:
        BASE = m.compose()
    cx, cy, w, h = m.CROP
    s = BASE.size[0] / w
    px = []
    for dx in range(-24, 25, 6):
        for dy in range(-24, 25, 6):
            c = BASE.getpixel((int((x + dx - cx) * s), int((y + dy - cy) * s)))[:3]
            if sum(c) > 240:  # not the ink
                px.append(c)
    r, gg, b = (sorted(q[i] for q in px)[len(px) // 2] for i in range(3))
    return f'#{r:02x}{gg:02x}{b:02x}'


def smooth_closed(P) -> str:
    """A closed Catmull-Rom curve through the points."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(cx, cy, rx, ry, seed=0, lump=0.08, n=11, rot=0.0) -> str:
    """A lumpy, hand-drawn oval."""
    rnd = random.Random(seed)
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.uniform(-0.12, 0.12)
        f = 1 + rnd.uniform(-lump, lump)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return smooth_closed(P)


def ray(x, y, ang, L, bend=0.0, n=18):
    a, b = math.radians(ang), math.radians(ang + bend)
    return bez((x, y), (x + math.cos(a) * L * 0.4, y + math.sin(a) * L * 0.4),
               (x + math.cos(a) * L * 0.7 + math.cos(b) * L * 0.05, y + math.sin(a) * L * 0.7 + math.sin(b) * L * 0.05),
               (x + math.cos(b) * L, y + math.sin(b) * L), n)


# ---- 1  coral grows ------------------------------------------------------------------------------------------------
def coral_branches():
    """(centreline, w0, w1, colour, knob colour) for each branch: eight of them, one per drawbar step."""
    knobs = [PINK, CORAL, '#ff9f7a', PINK, CORAL, '#ff9f7a', PINK, CORAL]
    spec = [  # start (inside the hand), direction, length, bend, width
        (TOP_L, -112, 300, -18, 44), (TOP_R, -70, 280, 20, 42),
        (PRONGS[0], -48, 250, -20, 32), (PRONGS[1], -22, 240, -26, 32),
        (PRONGS[2], -6, 220, -30, 31), (PRONGS[3], 14, 180, -40, 30),
        (THUMB, -104, 280, -22, 42), (NUB, 196, 240, 28, 34),
    ]
    out = []
    for k, ((x, y), ang, L, bend, w) in enumerate(spec):
        a = math.radians(ang)
        sx, sy = x - math.cos(a) * 26, y - math.sin(a) * 26
        P = ray(sx, sy, ang, L, bend)
        col = col_at(sx, sy)
        out.append((P, w, w * 0.72, col, knobs[k]))
        # a side shoot from two thirds of the way along
        q = P[len(P) * 3 // 5]
        side = 1 if k % 2 else -1
        S = ray(q[0], q[1], ang + bend * 0.5 + side * 42, L * 0.45, side * 12, 12)
        out.append((S, w * 0.7, w * 0.55, col, knobs[(k + 3) % 8]))
    return out


def v1_coral() -> Image.Image:
    """Coral grows: knobbly coral branches push out of the antler's top, every prong and the thumb, each forking once
    and ending in a round candy polyp; one branch per drawbar step."""
    B = coral_branches()
    front = ''.join(outlined(tube(P, w0, w1), c, INK) for P, w0, w1, c, _ in B)
    for P, w0, w1, c, _ in B:  # the fill-only layer, reaching back into the hand, melts the joins
        (x0, y0), (x1, y1) = P[0], P[1]
        back = [(x0 - (x1 - x0), y0 - (y1 - y0))] + P
        front += f'<path d="{tube(back, w0 - INK / 2, w1 - INK / 2)}" fill="{c}"/>'
    for i, (P, w0, w1, c, kc) in enumerate(B):
        ex, ey = P[-1]
        r = min(70.0, w1 * 2.6)
        rnd = random.Random(i)
        for k in range(3):  # a lumpy polyp head: a cluster of round knobs
            a = rnd.uniform(0, 2 * math.pi)
            front += outlined(blob(ex + math.cos(a) * r * 0.45, ey + math.sin(a) * r * 0.45, r * 0.62, r * 0.58, seed=i * 7 + k), kc, INK)
        front += f'<path d="{blob(ex, ey, r * 0.6, r * 0.55, seed=i * 3)}" fill="{kc}"/>'
        front += outlined(blob(ex, ey, r * 0.2, r * 0.17, seed=i + 40), '#c2185b', INK * 0.5)
    return draw(front, [])


# ---- 2  the palm wakes ----------------------------------------------------------------------------------------------
def v2_palm_face() -> Image.Image:
    """The palm wakes: a big round eye opens in the middle of the palm, the loop under it opens into a mouth round the
    pink tongue, cheeks flush, and the thumb waves (motion crescents)."""
    ex, ey = PALM_EYE
    front = outlined(blob(ex, ey, 98, 80, seed=3, lump=0.05), '#ffffff', INK)
    front += outlined(circle(ex + 10, ey + 8, 46), LIME, INK * 0.8)
    front += f'<path d="{circle(ex + 12, ey + 10, 24)}" fill="#000"/>'
    front += f'<path d="{circle(ex + 28, ey - 8, 10)}" fill="#fff"/>'
    # a heavy upper lid line drawn as a filled crescent, not a bare stroke
    front += outlined(crescent(ex, ey + 30, 110, 25, 155, 22), col_at(ex, ey - 95), INK * 0.7)
    mx, my = MOUTH
    front += outlined(blob(mx - 5, my - 5, 90, 58, seed=8, lump=0.06), '#7a1530', INK)
    for cx, cy in ((3095.0, 3290.0), (3292.0, 3282.0)):
        front += outlined(blob(cx, cy, 36, 24, seed=int(cx)), '#ff8fb1', INK * 0.6)
    return draw(front, ['f086'] + NEAR)


# ---- 3  antler in bloom ---------------------------------------------------------------------------------------------
def flower(cx, cy, R, col, seed, petals=6) -> str:
    rnd = random.Random(seed)
    out = ''
    a0 = rnd.uniform(0, 60)
    for k in range(petals):
        a = math.radians(a0 + k * 360 / petals)
        out += outlined(blob(cx + math.cos(a) * R * 0.55, cy + math.sin(a) * R * 0.55, R * 0.52, R * 0.36, seed=seed * 10 + k,
                             lump=0.07, rot=math.degrees(a)), col, INK * 0.9)
    out += outlined(blob(cx, cy, R * 0.34, R * 0.32, seed=seed + 99), YEL, INK * 0.9)
    for k in range(5):
        a = math.radians(k * 72 + a0)
        out += f'<path d="{circle(cx + math.cos(a) * R * 0.15, cy + math.sin(a) * R * 0.15, R * 0.05)}" fill="#e0671e"/>'
    return out


def v3_bloom() -> Image.Image:
    """Antler in bloom: big candy blossoms open on the antler's top, its four prongs and the thumb, buds swelling
    beside them, petals drifting down."""
    tips = [(TOP_L, -100, 110, PINK), (PRONGS[0], -48, 100, LAV), (PRONGS[1], -22, 92, '#ffffff'),
            (PRONGS[2], -2, 88, CYAN), (PRONGS[3], 20, 78, YEL), (THUMB, -110, 100, CORAL)]
    spots = [(x + math.cos(math.radians(a)) * R * 0.75, y + math.sin(math.radians(a)) * R * 0.75, R, c) for (x, y), a, R, c in tips]
    over = ''
    for (x, y), c in [((3310, 2610), '#ffb3cf')]:
        over += outlined(blob(x, y, 40, 52, seed=x, lump=0.06), c, INK * 0.9)
        over += outlined(blob(x, y + 45, 26, 18, seed=y), col_at(TOP_L[0], TOP_L[1] + 20), INK * 0.8)
    for i, (x, y, R, c) in enumerate(spots):
        over += flower(x, y, R, c, i + 1, 6 if R > 90 else 5)
    for i, (x, y) in enumerate([(3540, 2980), (2900, 3060), (3480, 3200), (2960, 2700)]):
        over += outlined(blob(x, y, 38, 23, seed=i + 7, rot=30 * i), [PINK, LAV, '#ffffff', CORAL][i], INK * 0.7)
    return draw('', NEAR, over)


# ---- 4  conch horn --------------------------------------------------------------------------------------------------
def v4_conch() -> Image.Image:
    """Conch horn (the hollow low tone): the hand curls up into a big spiral conch, knobbly spire at the top, its
    flared pink lip opening along its right side and booming out three round, low sound rings."""
    sx, sy = 3290.0, 2690.0  # the spire's tip
    bx, by = 3080.0, 3500.0  # the siphon canal, down in the ground
    ax, ay = bx - sx, by - sy
    L = math.hypot(ax, ay)
    ux, uy = ax / L, ay / L
    nx, ny = -uy, ux  # across the shell: + is its left, - its right
    Q = lambda s, t: (sx + ux * s * L + nx * t, sy + uy * s * L + ny * t)
    body = smooth_closed([Q(0.12, 0), Q(0.2, 130), Q(0.33, 225), Q(0.5, 220), Q(0.7, 150), Q(0.88, 60), Q(1.0, 20),
                          Q(1.0, -25), Q(0.85, -60), Q(0.6, -90), Q(0.35, -110), Q(0.2, -90)])
    out = f'<defs><clipPath id="shell"><path d="{body}"/></clipPath></defs>' + f'<path d="{body}" fill="#FBC79B"/>'
    for s0 in (0.38, 0.55, 0.71):  # coral bands round the body
        band = smooth_closed([Q(s0 - 0.03, 260), Q(s0 + 0.035, 260), Q(s0 + 0.045, 0), Q(s0 + 0.03, -200), Q(s0 - 0.03, -200), Q(s0 - 0.02, 0)])
        out += f'<path d="{band}" fill="{CORAL}" clip-path="url(#shell)"/>'
    out += f'<path d="{body}" fill="none" stroke="#000" stroke-width="{INK * 1.1}" stroke-linejoin="round"/>'
    for s0, t0 in ((0.2, 135), (0.28, 200), (0.38, 228), (0.25, -105)):  # knobs on the shoulder
        out += outlined(blob(*Q(s0, t0), 36, 32, seed=int(s0 * 100) + t0), '#FBC79B', INK)
    rot = math.degrees(math.atan2(uy, ux)) + 90
    for i, (s0, r) in enumerate(((0.11, 125), (0.04, 86), (-0.02, 54), (-0.06, 28))):  # the spire's whorls
        out += outlined(blob(*Q(s0, 0), r, r * 0.58, seed=20 + i, lump=0.05, rot=rot), '#FBC79B' if i % 2 == 0 else '#ffd9b8', INK)
    # the aperture: a flared cream lip along the right side, pink inside, a dark throat
    lip = smooth_closed([Q(0.24, -120), Q(0.3, -270), Q(0.44, -330), Q(0.62, -280), Q(0.8, -170), Q(0.94, -60),
                         Q(0.82, -20), Q(0.55, -40), Q(0.34, -70)])
    pink = smooth_closed([Q(0.33, -120), Q(0.45, -255), Q(0.62, -220), Q(0.82, -100), Q(0.66, -60), Q(0.45, -70)])
    throat = smooth_closed([Q(0.42, -110), Q(0.52, -190), Q(0.66, -150), Q(0.74, -90), Q(0.58, -80)])
    out += outlined(lip, CREAM, INK * 1.1) + outlined(pink, PINK, INK) + outlined(throat, '#7a1530', INK * 0.8)
    rings = ''
    ox, oy = Q(0.45, -200)
    for r, w, c in ((200, 44, PINK), (265, 48, LAV), (330, 50, CYAN)):
        rings += outlined(crescent(ox, oy, r, -15, 62, w), c, INK)
    return draw('', [], rings + out, hide=HAND + ['f087'])


# ---- 5  octopus -----------------------------------------------------------------------------------------------------
def v5_octopus() -> Image.Image:
    """Octopus: the hand turns into a coral octopus, its head where the antler was, two big eyes opening, eight
    curling tentacles (one per drawbar step) spreading over the ground round it."""
    hx, hy = 3215.0, 2930.0
    out = ''
    tent = [(200, 360, 28), (145, 380, 30), (122, 430, 22), (102, 440, 15),
            (80, 440, -15), (60, 420, -22), (38, 380, -30), (-20, 360, -28)]
    under = ''
    for k, (ang, L, bend) in enumerate(tent):
        x0 = hx + math.cos(math.radians(ang)) * 110
        y0 = hy + 120 + math.sin(math.radians(ang)) * 60
        P = ray(x0, y0, ang, L, bend, 24)
        # curl the tip
        ex, ey = P[-1]
        a = math.atan2(ey - P[-2][1], ex - P[-2][0])
        sgn = 1 if bend > 0 else -1
        P += g.spiral(ex, ey, a, 40, 0.8, 0.7, sgn, 16)[1:]
        under += outlined(tube(P, 52, 18), CORAL if k % 2 else '#ff8a6b', INK)
    head = blob(hx, hy, 190, 215, seed=5, lump=0.09, n=13)
    out += outlined(head, CORAL, INK * 1.1)
    out += outlined(blob(hx - 70, hy - 110, 45, 30, seed=6, rot=-30), '#ff9f8f', INK * 0.6)
    for ex, sgn in ((hx - 70, -1), (hx + 70, 1)):
        out += outlined(blob(ex, hy + 40, 62, 66, seed=int(ex), lump=0.04), '#ffffff', INK)
        out += outlined(circle(ex + sgn * 6, hy + 52, 32), '#000', 1)
        out += f'<path d="{circle(ex + sgn * 6 + 12, hy + 38, 10)}" fill="#fff"/>'
    out += outlined(blob(hx, hy + 130, 40, 26, seed=12), '#7a1530', INK * 0.8)
    return draw('', [], under + out, hide=HAND + ['f087'])


VERSIONS = [
    ('1-coral-grows', 'Coral grows', v1_coral),
    ('2-palm-wakes', 'The palm wakes', v2_palm_face),
    ('3-antler-in-bloom', 'Antler in bloom', v3_bloom),
    ('4-conch-horn', 'Conch horn', v4_conch),
    ('5-octopus', 'Octopus', v5_octopus),
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


# ---- chosen: coral grows, then the palm wakes -----------------------------------------------------------------------
# Picked: coral on steps 1-6, the waking palm on 7-8. The hand is coral, so it grows the way coral does: one chunky
# branch per drawbar step out of the antler's top, its prongs, the thumb and the left nub, each crowned with a big
# lumpy candy polyp (about 150 px across). Then an eye opens in the palm (step 7) and the loop at its bottom opens into
# a mouth round the pink tongue (step 8). Branches are drawn twice (outlined, then fill-only reaching back into the
# hand) in the hand's own colour where they join, so they grow out of it without a seam.
STEP = 1 / 8
# (start inside the hand, direction, length, bend, width at the base, width at the tip, polyp radius, polyp colour)
BRANCHES = [
    (TOP_L, -112, 300, -18, 46, 46, 88, PINK),
    (PRONGS[0], -24, 240, -20, 34, 40, 80, YEL),
    (THUMB, -104, 280, -22, 46, 44, 86, LAV),
    (TOP_R, -82, 290, 10, 44, 44, 84, '#ff9f7a'),
    (PRONGS[1], -2, 230, -24, 34, 40, 78, CYAN),
    (NUB, 196, 240, 28, 38, 42, 80, '#ffb3cf'),
]
PORE = {PINK: '#c2185b', YEL: '#e0671e', LAV: '#6a3fb5', '#ff9f7a': '#c2410c', CYAN: '#117a8b', '#ffb3cf': '#c2185b'}


def item(d, fill, edge, at, start, end, grow='scale') -> dict:
    return {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
            'start': round(start, 4), 'end': round(end, 4), 'grow': grow}


def coral_items() -> list[dict]:
    lines, fills, polyps = [], [], []
    for k, ((x, y), ang, L, bend, w0, w1, R, pc) in enumerate(BRANCHES):
        s0 = k * STEP
        a = math.radians(ang)
        sx, sy = x - math.cos(a) * 26, y - math.sin(a) * 26
        col = col_at(sx, sy)
        P = ray(sx, sy, ang, L, bend)
        q = P[len(P) // 2]
        side = 1 if k % 2 else -1
        S = ray(q[0], q[1], ang + bend * 0.5 + side * 48, L * 0.36, side * 10, 10)  # a knobbly side stub
        for C, v0, v1, t0, t1 in ((P, w0, w1, s0, s0 + 0.65 * STEP), (S, w1 * 0.8, w1 * 0.72, s0 + 0.3 * STEP, s0 + 0.75 * STEP)):
            (x0, y0), (x1, y1) = C[0], C[1]
            back = [(x0 - (x1 - x0), y0 - (y1 - y0))] + C
            lines.append(item(tube(C, v0, v1), col, INK, C[0], t0, t1))
            fills.append(item(tube(back, v0 - INK / 2, v1 - INK / 2), col, 0, C[0], t0, t1))
        ex, ey = P[-1]
        dx, dy = math.cos(math.radians(ang + bend)), math.sin(math.radians(ang + bend))
        cx, cy = ex + dx * R * 0.35, ey + dy * R * 0.35
        rnd = random.Random(k + 1)
        lumps = [(cx, cy, R * 0.62)]
        a0 = rnd.uniform(0, 2 * math.pi)
        for j in range(5):
            aa = a0 + j * 2 * math.pi / 5 + rnd.uniform(-0.25, 0.25)
            lumps.append((cx + math.cos(aa) * R * 0.5, cy + math.sin(aa) * R * 0.5, R * rnd.uniform(0.44, 0.54)))
        t0, t1 = s0 + 0.45 * STEP, s0 + STEP
        for j, (lx, ly, r) in enumerate(lumps):
            polyps.append(item(blob(lx, ly, r, r * 0.94, seed=k * 10 + j, lump=0.08), pc, INK, (cx, cy), t0, t1))
        for j, (lx, ly, r) in enumerate(lumps):
            polyps.append(item(blob(lx, ly, r - INK / 2, r * 0.94 - INK / 2, seed=k * 10 + j, lump=0.08), pc, 0, (cx, cy), t0, t1))
        for j in range(3):  # pores
            aa = a0 + 0.6 + j * 2.1
            polyps.append(item(blob(cx + math.cos(aa) * R * 0.38, cy + math.sin(aa) * R * 0.38, R * 0.13, R * 0.11, seed=k * 5 + j),
                               PORE[pc], INK * 0.5, (cx, cy), t0 + 0.2 * STEP, t1))
    return lines + fills + polyps


def eye_items() -> list[dict]:
    """Step 7: the palm's eye opens (every part grows in height from the eye's middle, like a lid lifting)."""
    ex, ey = PALM_EYE
    t0, t1 = 6 * STEP, 7 * STEP
    return [item(blob(ex, ey, 98, 80, seed=3, lump=0.05), '#ffffff', INK, (ex, ey), t0, t1 - 0.2 * STEP, 'y'),
            item(circle(ex + 10, ey + 8, 46), LIME, INK * 0.8, (ex, ey), t0 + 0.25 * STEP, t1, 'y'),
            item(circle(ex + 12, ey + 10, 24), '#000', 0, (ex, ey), t0 + 0.35 * STEP, t1, 'y'),
            item(circle(ex + 28, ey - 8, 10), '#ffffff', 0, (ex, ey), t0 + 0.5 * STEP, t1, 'y')]


def mouth_items() -> list[dict]:
    """Step 8: the loop at the bottom of the palm opens into a dark mouth, the pink tongue (f086, with its own painted
    ink) laid back on top the moment it starts, and a cheek flushes."""
    mx, my = 3248.0, 3358.0
    t0 = 7 * STEP
    out = [item(blob(mx, my, 108, 72, seed=8, lump=0.06, rot=-22), '#7a1530', INK, (mx, my), t0, t0 + 0.75 * STEP)]
    out.append(item(m.FILLS['f086'], '#F681A5', 0, (mx, my), t0, t0 + 0.001))
    out += [item(m.INKS[i], '#000', 0, (mx, my), t0, t0 + 0.001) for i in m.own_ink('f086')]
    out.append(item(blob(3105, 3288, 40, 26, seed=31), '#ff8fb1', INK * 0.6, (3105, 3288), t0 + 0.4 * STEP, 1.0))
    return out


def sprite_svg(items, t) -> str:
    """ghost_endframes.sprite_svg with the app's x / y growth as well as scale (same easing)."""
    out = ''
    for it in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - it['start']) / max(1e-6, it['end'] - it['start'])))) ** 3
        if v <= 0.01:
            continue
        x, y = it['at']
        sc = f'{v:.4f} 1' if it['grow'] == 'x' else f'1 {v:.4f}' if it['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def wake_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    im = m.compose()
    im.alpha_composite(m.svg(sprite_svg(coral_items() + eye_items() + mouth_items(), t)))
    return im


def strip(frames, tiles, path, sc=0.42, label=lambda t: f'frame {t:.2f}') -> None:
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    im = Image.new('RGB', (tw * len(tiles) + 10 * (len(tiles) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), label(tt), fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    im.save(path)


def wake_main() -> None:
    out = OUT.parent / 'coral-wakes'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [wake_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    strip(frames, tiles, out / 'strip.png')
    steps = [k / 8 for k in range(9)]
    strip(steps, [wake_frame(t) for t in steps], out / 'steps.png', 0.3, lambda t: f'step {round(t * 8)}')
    print('wrote', out)


def export() -> None:
    import json
    build = {
        'label': "The coral antler hand: drag for the Lower 5 1/3' drawbar; it grows like coral, a chunky branch with a "
                 "big candy polyp out of its antler, prongs, thumb and side at every step, then an eye opens in its palm "
                 "and the loop below opens into a mouth round its pink tongue",
        'effects': [
            {'effect': 'sprites', 'place': 'over', 'items': coral_items() + eye_items() + mouth_items()},
        ],
    }
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', sum(len(e['items']) for e in build['effects']), 'shapes to', path)


if __name__ == '__main__' and 'wake' in __import__('sys').argv[1:]:
    wake_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
