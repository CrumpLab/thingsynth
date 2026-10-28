# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (split point at C5) for the purple ledge: the long dusty-mauve shelf of land right of the stream,
with a frilly, torn hem hanging over the lime ground below it.

    uv run scripts/ledge_endframes.py          # the five end frames and sheet
    uv run scripts/ledge_endframes.py clam     # the chosen giant clam: progression strip, steps and end frame
    uv run scripts/ledge_endframes.py export   # docs/objects/voice-split/build.json
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
m.CROP = (2480, 1990, 1360, 1080)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/voice-split/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 16
LEDGE = 'f165'
LILAC, DEEP, PALE, PLUM = '#c98ad9', '#a35cc4', '#ead0f2', '#5b2a63'
MAUVE = '#d3a0c4'  # the ledge's own dusty mauve, a touch pinker and opaque
PINK, LEMON, MINT, CYAN, ORANGE, MAGENTA = '#ff9fc4', '#ffe066', '#7fe0c8', '#2DFFF4', '#ff9f43', '#f64c76'
# painted shapes that sit in front of the ledge: the orange capsule, the cyan bits under it, the fish, the grey shade
IN_FRONT = ['f167', 'f168', 'f169', 'f179', 'f182']
HINGE = (3690.0, 2520.0)  # the ledge's right end, tucked behind the fish's fin
# the ledge's top edge, left to right
TOP = [(2700, 2540), (2780, 2500), (2860, 2475), (2930, 2463), (3000, 2480), (3120, 2500), (3200, 2512), (3286, 2522),
       (3470, 2532), (3667, 2534), (3722, 2532)]


def draw(front: str = '', again: list[str] | None = None, over: str = '', colour: str | None = None) -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>', fill_colour={LEDGE: colour} if colour else None)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def closed(P) -> str:
    """A smooth closed curve (Catmull-Rom) through the points P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sy=1.0) -> str:
    """A lumpy, hand-drawn round shape: n bumps round (x, y)."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr, y + math.sin(a) * rr * sy))
    return closed(P)


def wobble(P, amt, seed) -> list:
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * amt, y + (rnd.random() - 0.5) * amt) for x, y in P]


def top_y(x: float) -> float:
    for (x0, y0), (x1, y1) in zip(TOP, TOP[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return TOP[0][1] if x < TOP[0][0] else TOP[-1][1]


# ---- 1. giant clam: the ledge is the lower shell and its frilly hem the mantle; the upper shell lifts open --------
def clam_lid(open_deg: float = 24.0, A: float = 500.0, B: float = 270.0, nrib: int = 9):
    """The upper shell: a half-ellipse hinged at HINGE, its lip running up-left at open_deg, a scalloped outer edge,
    pale rib bands fanning from the hinge (stopping short of it so the ink doesn't crowd), and a lumpy umbo."""
    hx, hy = HINGE
    a = math.radians(180 + open_deg)
    ux, uy = math.cos(a), math.sin(a)          # along the lip, away from the hinge
    vx, vy = math.sin(a) * -1, math.cos(a)     # perpendicular, toward the dome
    if vy > 0:
        vx, vy = -vx, -vy
    P = lambda u, v: (hx + ux * u + vx * v, hy + uy * u + vy * v)
    ell = lambda t, bump=0.0: P(A * (1 + math.cos(t)) + bump * math.cos(t), (B + bump) * math.sin(t))
    T0, T1 = 0.0, 0.86 * math.pi
    edge = []
    for i in range(nrib * 6 + 1):
        t = T0 + (T1 - T0) * i / (nrib * 6)
        bump = 30 * abs(math.sin(math.pi * i / 6))
        edge.append(ell(t, bump))
    tail = [ell(t) for t in (0.92 * math.pi, 0.98 * math.pi)]
    lip = [P(A * 2 * k / 6, (6 if k % 2 else -6)) for k in range(1, 6)]  # hinge to the far end, a little uneven
    outline = closed(wobble([P(-6, 4)] + lip + edge + tail, 6, 12))
    out = outlined(outline, LILAC, INK)
    for k in range(0, nrib, 2):  # pale bands, every other rib
        ts = [T0 + (T1 - T0) * (k * 6 + j) / (nrib * 6) for j in range(7)]
        outer = [ell(t, 30 * abs(math.sin(math.pi * j / 6))) for j, t in enumerate(ts)]
        q0, q1 = outer[0], outer[-1]
        inner = [(hx + (q1[0] - hx) * 0.38, hy + (q1[1] - hy) * 0.38), (hx + (q0[0] - hx) * 0.38, hy + (q0[1] - hy) * 0.38)]
        out += outlined(closed(wobble(outer + inner, 5, 30 + k)), PALE, INK * 0.7)
    ux0, uy0 = P(70, 60)
    out += outlined(lump(ux0, uy0, 72, 13, 0.12, 7), DEEP, INK)
    return out, P(A * 2, 0)


def v1_clam() -> Image.Image:
    """Giant clam: a fluted lilac upper shell lifts open from a hinge behind the fish, a frilly candy mantle lines the
    gap and a big pearl sits inside: the ledge splits into upper and lower."""
    hx, hy = HINGE
    lid, lip_end = clam_lid()
    # the dark inside, between the ledge's top and the lid's lip
    inside = [(hx - 20, hy - 4)] + [(x, top_y(x) - 6) for x in range(3640, 2700, -80)] + [(2700, 2520), (lip_end[0] + 10, lip_end[1] + 30)]
    out = outlined(closed(wobble(inside, 10, 1)), PLUM, INK)
    # the mantle along the lower lip: a frilly candy band lying on the ledge's top edge
    frill = []
    for k, x in enumerate(range(2740, 3680, 38)):
        h = (62 if k % 2 else 30) * min(1.0, (x - 2700) / 250, (3700 - x) / 250)
        frill.append((x, top_y(x) - h))
    frill += [(x, top_y(x) + 8) for x in range(3680, 2730, -120)]
    out += outlined(closed(wobble(frill, 8, 2)), MINT, INK * 0.8)
    # the pearl
    out += outlined(lump(3000, 2385, 104, 5, 0.04, 13), '#fff4f8', INK)
    out += f'<path d="{lump(2960, 2345, 28, 6, 0.15, 6)}" fill="#ffffff"/>'
    out += f'<path d="{lump(3030, 2418, 32, 7, 0.15, 6)}" fill="#f3d3ee"/>'
    # the upper mantle hanging under the lid's lip
    lx, ly = lip_end
    lip = []
    for k in range(15):
        u = k / 14
        x, y = hx + (lx - hx) * u, hy + (ly - hy) * u
        lip.append((x, y + (52 if k % 2 else 22) * min(1, u * 4, (1 - u) * 6 + 0.2)))
    lip += [(lx + 10, ly - 14), (hx - 30, hy - 16)]
    out += outlined(closed(wobble(lip, 8, 3)), PINK, INK * 0.8)
    out += lid
    return draw(out, IN_FRONT)


# ---- 2. axolotl: the ledge is its long body; its left end rears into a head with frilly gills --------------------
def v2_axolotl() -> Image.Image:
    """Axolotl: the ledge becomes a lilac axolotl lying by the stream; its left end lifts into a broad smiling head,
    three frilly candy gills fan out each side, a sleepy eye wakes, a fin runs along its back and a foot steps out."""
    out = ''
    # the dorsal fin along its back, pale and frilly
    fin = [(x, top_y(x) - (55 + 50 * abs(math.sin((x - 2960) / 120 * math.pi))) * min(1, (x - 2950) / 160) * min(1, (3700 - x) / 160))
           for x in range(2960, 3700, 30)]
    fin += [(3690, top_y(3690) + 10), (2960, top_y(2960) + 10)]
    out += outlined(closed(wobble(fin, 10, 4)), PALE, INK * 0.85)
    # gills: three feathery candy fronds behind the head, fanning back and up
    hx, hy = 2770, 2440
    for k, (ang, L) in enumerate(((-152, 220), (-118, 250), (-84, 225))):
        a = math.radians(ang)
        base = (hx + 70 + math.cos(a) * 60, hy - 40 + math.sin(a) * 60)
        tip = (base[0] + math.cos(a) * L, base[1] + math.sin(a) * L)
        C = bez(base, (base[0] + math.cos(a) * L * 0.4, base[1] + math.sin(a) * L * 0.4),
                (tip[0] - math.cos(a + 0.35) * L * 0.3, tip[1] - math.sin(a + 0.35) * L * 0.3), tip, 12)
        left, right = [], []
        for i, (x, y) in enumerate(C):
            q0, q1 = C[max(0, i - 1)], C[min(len(C) - 1, i + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            dd = math.hypot(dx, dy) or 1
            nx, ny = -dy / dd, dx / dd
            w = (50 - 22 * i / len(C)) * (1 + 0.28 * abs(math.sin(i * math.pi / 2.2))) * min(1, 0.6 + i / 6)
            left.append((x + nx * w, y + ny * w))
            wr = (50 - 22 * i / len(C)) * (1 + 0.28 * abs(math.sin(i * math.pi / 2.2 + 1.2))) * min(1, 0.6 + i / 6)
            right.append((x - nx * wr, y - ny * wr))
        out += outlined(closed(wobble(left + [(tip[0] + math.cos(a) * 30, tip[1] + math.sin(a) * 30)] + right[::-1], 2, 20 + k)),
                        PINK, INK * 0.8)
        out += outlined(tube(C[3:-3], 12, 7), MAGENTA, INK * 0.55)
    # the head: broad, flat, lumpy, over the ledge's left end
    head = [(2600, 2470), (2610, 2390), (2680, 2345), (2790, 2330), (2890, 2360), (2960, 2420), (2990, 2490),
            (2960, 2555), (2860, 2590), (2720, 2590), (2630, 2550)]
    out += outlined(closed(wobble(head, 12, 5)), MAUVE, INK)
    # the smile: a thin outlined crescent
    out += outlined(f'M{p(2618, 2500)}C{p(2680, 2560)} {p(2800, 2565)} {p(2880, 2520)}C{p(2800, 2548)} {p(2690, 2545)} {p(2618, 2500)}Z',
                    PLUM, INK * 0.7)
    # a blush of pink on its cheek
    out += f'<path d="{lump(2860, 2470, 42, 9, 0.15, 7, sy=0.7)}" fill="{PINK}"/>'
    # the eye, round and awake
    out += outlined(lump(2735, 2420, 46, 8, 0.06, 8), '#ffffff', INK)
    out += f'<path d="{circle(2722, 2425, 26)}" fill="#000"/><path d="{circle(2712, 2414, 9)}" fill="#fff"/>'
    # a front foot stepping out of the hem toward the stream
    leg = bez((2830, 2590), (2828, 2640), (2818, 2680), (2808, 2705), 10)
    out += outlined(tube(leg, 40, 34), MAUVE, INK * 0.9)
    out += outlined(lump(2808, 2722, 54, 11, 0.18, 7, sy=0.65), MAUVE, INK * 0.9)
    return draw(out, ['f169', 'f179', 'f182'])


# ---- 3. keyboard: an octave of big keys, C4 to C5, rises out of the ledge's top ---------------------------------
def v3_keys() -> Image.Image:
    """Split keyboard: the ledge's top edge rises into an octave of big lumpy keys, C4 to C5, one per semitone; the
    lower manual's keys candy, a plum black key between each pair, the frilly hem the keyboard's skirt."""
    out = ''
    x0, x1 = 2760, 3660
    nW = 8
    w = (x1 - x0) / nW
    keys_h = 230
    cols = [PINK, LEMON, MINT, '#c4a3f0', ORANGE, CYAN, MAGENTA, PALE]
    for k in range(nW):
        a, b = x0 + k * w, x0 + (k + 1) * w
        yb = max(top_y(a), top_y(b)) + 12
        yt = top_y((a + b) / 2) - keys_h
        P = [(a + 6, yb), (a + 2, yt + 30), (a + 18, yt + 4), (b - 18, yt), (b - 4, yt + 26), (b - 6, yb)]
        out += outlined(closed(wobble(P, 9, 20 + k)), cols[k], INK)
    for k in (0, 1, 3, 4, 5):  # black keys between C-D, D-E, F-G, G-A, A-B
        cx = x0 + (k + 1) * w
        yt = top_y(cx) - keys_h - 16
        P = [(cx - 34, yt + 150), (cx - 38, yt + 20), (cx - 20, yt), (cx + 22, yt + 2), (cx + 38, yt + 22), (cx + 34, yt + 152),
             (cx, yt + 162)]
        out += outlined(closed(wobble(P, 6, 40 + k)), PLUM, INK)
        out += f'<path d="{lump(cx - 12, yt + 40, 10, 41 + k, 0.2, 5, sy=2.2)}" fill="#8a4d94"/>'
    return draw(out, IN_FRONT)


# ---- 4. banana split: scoops, cream, sauce and cherries pile up along its top -----------------------------------
def v4_banana_split() -> Image.Image:
    """Banana split: a long banana half lies along the ledge's top, three big scoops sit on it, whipped cream, chocolate
    sauce running down and cherries on top: a party on the shelf."""
    out = ''
    # the banana half, a long curved yellow shape along the top edge
    ban_top = [(x, top_y(x) - 70 - 30 * math.sin((x - 2740) / 960 * math.pi)) for x in range(2740, 3700, 80)]
    ban_bot = [(x, top_y(x) + 14) for x in range(3700, 2730, -80)]
    out += outlined(closed(wobble([(2700, 2530)] + ban_top + [(3730, 2500)] + ban_bot, 8, 50)), '#ffe58a', INK)
    # three scoops
    for k, (x, col, r) in enumerate(((2990, PINK, 140), (3270, MINT, 150), (3540, '#8a5a3c', 135))):
        y = top_y(x) - 90 - r * 0.75
        out += outlined(lump(x, y, r, 60 + k, 0.1, 10, sy=0.85), col, INK)
        # the drippy rim where it melts on the banana
        rim = [(x - r * 1.02 + i * r * 0.2, y + r * 0.62 + (38 if i % 2 else 8)) for i in range(11)]
        rim += [(x + r * 0.9, y + r * 0.35), (x - r * 0.9, y + r * 0.35)]
        out += outlined(closed(wobble(rim, 6, 70 + k)), col, INK * 0.85)
    # whipped cream on the middle scoop, and sauce running down the chocolate and strawberry
    out += outlined(lump(3265, 2165, 85, 80, 0.2, 7), '#fffbe6', INK * 0.9)
    out += outlined(lump(3250, 2110, 55, 81, 0.2, 6), '#fffbe6', INK * 0.9)
    sauce = [(2900, 2225), (2960, 2195), (3060, 2205), (3100, 2240), (3080, 2290), (3060, 2330), (3040, 2290), (3010, 2270),
             (2980, 2340), (2955, 2300), (2925, 2280)]
    out += outlined(closed(wobble(sauce, 5, 82)), '#6b3a24', INK * 0.8)
    # cherries with stems
    for k, (cx, cy) in enumerate(((3275, 2040), (3000, 2160), (3560, 2200))):
        stem = bez((cx, cy - 40), (cx + 5, cy - 90), (cx + 30, cy - 120), (cx + 55, cy - 140), 10)
        out += outlined(tube(stem, 9, 7), '#7fd36b', INK * 0.6)
        out += outlined(lump(cx, cy, 52, 90 + k, 0.08, 8), '#ff2a4a', INK)
        out += f'<path d="{lump(cx - 16, cy - 18, 13, 95 + k, 0.2, 5)}" fill="#fff"/>'
    return draw(out, IN_FRONT)


# ---- 5. grapes: bunches of grapes swell from the frilly hem, under vine leaves -------------------------------------
def leaf(cx, cy, r, seed) -> str:
    """A lumpy three-lobed vine leaf, lobes up and out: outlined lobes, then their fill laid over the middle so the
    inner joins melt away."""
    lobes = [(cx + math.cos(math.radians(a)) * r * 0.5, cy + math.sin(math.radians(a)) * r * 0.5, r * s, a)
             for a, s in ((195, 0.52), (268, 0.6), (345, 0.52))]
    out = ''.join(outlined(lump(x, y, rr, seed * 7 + k, 0.16, 8, math.radians(a)), '#7fd36b', INK * 0.9)
                  for k, (x, y, rr, a) in enumerate(lobes))
    out += ''.join(f'<path d="{lump(x + (cx - x) * 0.35, y + (cy - y) * 0.35, rr * 0.7, seed * 7 + k, 0.1, 8)}" fill="#7fd36b"/>'
                   for k, (x, y, rr, a) in enumerate(lobes))
    return out


def bunch(x, y, r, seed) -> str:
    """A hanging bunch of big grapes, rows 4-3-3-2-1 from (x, y) down."""
    rnd = random.Random(seed)
    out = ''
    rows = (3, 3, 2, 2, 1)
    for i, n in enumerate(rows):
        for j in range(n):
            gx = x + (j - (n - 1) / 2) * r * 1.6 + (rnd.random() - 0.5) * 10
            gy = y + i * r * 1.35 + (rnd.random() - 0.5) * 10
            col = '#8e4fc9' if (i + j) % 2 else '#a96ad9'
            out += outlined(lump(gx, gy, r, seed * 13 + i * 5 + j, 0.07, 8), col, INK * 0.85)
            out += f'<path d="{lump(gx - r * 0.35, gy - r * 0.35, r * 0.22, seed + i + j, 0.2, 5)}" fill="#e4c8f6"/>'
    return out


def v5_grapes() -> Image.Image:
    """Grapes: the frilly hem is a vine; big bunches of purple grapes swell and hang from it, each under a green leaf,
    a curly tendril between them."""
    out = ''
    for k, (x, y, la) in enumerate(((2810, 2700, -170), (3110, 2745, -190), (3540, 2835, -175))):
        out += leaf(x + (40 if k != 1 else -40), y - 40, 130, 100 + k)
        out += bunch(x, y, 50, k + 1)
    # tendrils as tapered outlined curls
    for k, (x, y, s) in enumerate(((2960, 2660, 1), (3420, 2700, -1))):
        P = g.spiral(x, y, math.radians(90), 52, 1.5, 0.65, s, 40)
        out += outlined(tube(P, 12, 7), '#5cbf4a', INK * 0.6)
    return draw(out, ['f169', 'f179'])


VERSIONS = [
    ('1-giant-clam', 'Giant clam', v1_clam),
    ('2-axolotl', 'Axolotl', v2_axolotl),
    ('3-split-keyboard', 'Split keyboard', v3_keys),
    ('4-banana-split', 'Banana split', v4_banana_split),
    ('5-grapes', 'Grapes', v5_grapes),
]


def main(only: str = '') -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (split at C4)', m.compose())]
    for slug, title, fn in VERSIONS:
        if only and not slug.startswith(only):
            continue
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    if only:
        return
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


# ---- chosen: giant clam ---------------------------------------------------------------------------------------------
# Picked under 5a: the ledge turns into a giant clam that could live by the stream, its frilly hem already a mantle, and
# one shell splitting into an upper and a lower half reads the split point (one keyboard dividing into lower and upper
# manuals). Adjusted on pick: the lid a lumpy, scalloped clam shell with a few broad wavy flutes (not a fan of straight
# rays: the big eye already has a peacock fan), the mantles lumpy and hand-drawn. The split point runs C4 to C5 in 12
# semitone steps, so every arrival lands on k/12:
#   steps 1-6   the upper shell rises from behind the fish's fin and lifts open, one pose per step (2 to 24 degrees),
#               the dark mouth and a pink lip showing under it as it opens
#   step 7      the lower mantle frills out along the ledge's top, a row of lumpy mint frills, left to right
#   step 8      the upper mantle frills out under the lid's lip, lumpy pink frills, from the hinge out
#   steps 9-11  a pearl swells in the mouth, one size a step
#   step 12     its shine: a white highlight and a glint of colour
STEP = 1 / 12
POSES = [2.0, 7.0, 12.0, 16.0, 20.0, 24.0]
LID_A, LID_B, NFL = 500.0, 228.0, 5
CLAM_FRONT = ['f179', 'f169']  # the fish's fin over the hinge, the orange capsule under the hem
PEARL = (3000.0, 2386.0)
PEARL_SIZES = [(62, 9), (84, 10), (104, 11)]  # radius, step


def it(d, fill, edge, at, s, e, out=None, grow='scale') -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 4), 'end': round(min(1.0, e), 4), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 4), round(min(1.0, out[1]), 4)
    return o


def lid_local():
    """The upper shell in its own frame: u runs along the lip from the hinge, v up into the dome. Returns the outline,
    the pale flutes and the umbo as point lists (the same every pose, so the shell only turns)."""
    rnd = random.Random(7)
    T1 = 0.9 * math.pi
    dt = T1 / NFL
    swell = [1 + (rnd.random() - 0.5) * 0.4 for _ in range(NFL)]

    def edge(t, inset=0.0):
        """The rim: one broad scallop per flute, dipping between them."""
        k = min(NFL - 1, int(t / dt))
        frac = (t - k * dt) / dt
        bump = 64 * swell[k] * max(0.0, math.sin(math.pi * frac)) ** 0.55 - inset
        ct, st = math.cos(t), math.sin(t)
        return (LID_A * (1 + ct) + bump * ct, (LID_B + bump) * st)

    lip = [(LID_A * 2 * k / 6, (7 if k % 2 else -5)) for k in range(0, 6)]
    rim = [edge(T1 * i / (NFL * 8)) for i in range(NFL * 8 + 1)]
    tail = [(LID_A * (1 + math.cos(t)), LID_B * math.sin(t)) for t in (0.94 * math.pi, 0.985 * math.pi)]
    outline = wobble(lip + rim + tail, 7, 12)
    flutes = []
    for k in (1, 3):
        ta, tb = k * dt + 0.12 * dt, (k + 1) * dt - 0.12 * dt
        tm = (ta + tb) / 2
        arc = [edge(ta + (tb - ta) * i / 10, 10) for i in range(11)]
        mx, my = edge(tm)
        inner = (mx * 0.3, my * 0.3)

        def side(rim_pt, sway):
            ix, iy = inner
            dx, dy = rim_pt[0] - ix, rim_pt[1] - iy
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            return [(ix + dx * j / 7 + nx * sway * math.sin(math.pi * j / 7), iy + dy * j / 7 + ny * sway * math.sin(math.pi * j / 7))
                    for j in range(1, 7)]
        sway = 30 if k == 1 else -26
        flutes.append(wobble([inner] + side(arc[0], sway) + arc + side(arc[-1], sway)[::-1], 5, 40 + k))
    umbo = []
    rr = random.Random(13)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        r = 74 * (1 + (rr.random() - 0.5) * 0.25)
        umbo.append((78 + math.cos(a) * r, 64 + math.sin(a) * r * 0.85))
    return outline, flutes, umbo


LID = lid_local()


def to_canvas(deg: float):
    hx, hy = HINGE
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    U, V = (-c, -s_), (s_, -c)
    return lambda u, v: (hx + U[0] * u + V[0] * v, hy + U[1] * u + V[1] * v)


def lip_band(P, n=14, depth=26, seed=3):
    """A thin lumpy pink lip under the lid's edge (pose drawing; the frilly mantle comes later)."""
    rnd = random.Random(seed)
    top = [P(LID_A * 2 * k / n, 4) for k in range(1, n)]
    bot = [P(LID_A * 2 * k / n, -depth * (0.7 + rnd.random() * 0.6) * min(1, k / 3)) for k in range(n - 1, 0, -1)]
    return closed(top + bot)


def mouth(P) -> list:
    """The dark inside of the clam, from the ledge's top up to the lid's lip."""
    hx, hy = HINGE
    lx, ly = P(LID_A * 2, 0)
    low = [(x, top_y(x) - 4) for x in range(3640, 2700, -70)]
    pts = [(hx - 30, hy - 6)] + low + [(2702, 2524), (lx + 14, ly + 26)]
    pts += [P(LID_A * 2 * k / 5, -10) for k in range(4, 0, -1)]
    return wobble(pts, 8, 1)


def pose_items(deg: float, s: float, e: float, out) -> list[dict]:
    P = to_canvas(deg)
    outline, flutes, umbo = LID
    items = []
    if deg >= 5:
        items.append(it(closed(mouth(P)), PLUM, INK, HINGE, s, e, out))
        items.append(it(lip_band(P), PINK, INK * 0.8, HINGE, s, e, out))
    items.append(it(closed([P(*q) for q in outline]), LILAC, INK, HINGE, s, e, out))
    for fl in flutes:
        items.append(it(closed([P(*q) for q in fl]), PALE, INK * 0.75, HINGE, s, e, out))
    items.append(it(closed([P(*q) for q in umbo]), DEEP, INK, HINGE, s, e, out))
    return items


def frill_items(base, normal, depth, colour, s, e, seed, nseg=4) -> list[dict]:
    """A lumpy, hand-drawn ruffle along the curve base(q), q 0..1, its free edge pushed out along normal(q) in uneven
    rounded lobes. Built as nseg overlapping pieces that frill out one after another over [s, e], then their middles
    laid again fill-only so the joins between the pieces melt away."""
    rnd = random.Random(seed)
    # uneven lobes along the whole band
    cuts = [0.0]
    while cuts[-1] < 1:
        cuts.append(cuts[-1] + 0.085 + rnd.random() * 0.07)
    cuts[-1] = 1.0
    deep = [depth * (0.5 + rnd.random() * 0.4) for _ in cuts]

    def free(q):
        k = max(0, min(len(cuts) - 2, next(i for i in range(len(cuts) - 1) if q <= cuts[i + 1])))
        frac = (q - cuts[k]) / (cuts[k + 1] - cuts[k])
        return depth * 0.42 + deep[k] * max(0.0, math.sin(math.pi * frac)) ** 0.5

    def at(q, d):
        (x, y), (nx, ny) = base(q), normal(q)
        return (x + nx * d, y + ny * d)

    outl, fills = [], []
    for k in range(nseg):
        q0, q1 = max(0.0, (k - 0.25) / nseg), min(1.0, (k + 1.25) / nseg)
        qs = [q0 + (q1 - q0) * i / 48 for i in range(49)]
        taper = lambda q: min(1.0, q / 0.06 + 0.15, (1 - q) / 0.06 + 0.15)
        P = [at(q, free(q) * taper(q)) for q in qs] + [at(q, 0) for q in qs[::-1]]
        u0 = s + (e - s) * 0.55 * k / max(1, nseg - 1)
        root = at((q0 + q1) / 2, 0)
        outl.append(it(closed(wobble(P, 2, seed * 7 + k)), colour, INK * 0.8, root, u0, u0 + (e - s) * 0.45))
        C = [at(q, max(10.0, free(q) * taper(q) - 10)) for q in qs] + [at(q, 5) for q in qs[::-1]]
        fills.append(it(closed(C), colour, 0, root, u0, u0 + (e - s) * 0.45))
    return outl + fills


def clam_items() -> list[dict]:
    items = []
    for k, deg in enumerate(POSES):
        s, e = (k + 1) * STEP - 0.03, (k + 1) * STEP  # a quick swing at the end of each step, so a glide shows one shell
        out = ((k + 2) * STEP - 0.006, (k + 2) * STEP) if k < len(POSES) - 1 else None
        items += pose_items(deg, s, e, out)
    # step 7: the lower mantle along the ledge's top, mint, left to right
    low_base = lambda q: (2730 + q * 880, top_y(2730 + q * 880) + 4)
    items += frill_items(low_base, lambda q: (0.0, -1.0), 78, MINT, 6 * STEP + 0.01, 7 * STEP, 21)
    # step 8: the upper mantle under the lid's lip, pink, hanging, from the hinge out
    P = to_canvas(POSES[-1])
    hx, hy = HINGE
    V = (P(0, 1)[0] - hx, P(0, 1)[1] - hy)
    up_base = lambda q: P(LID_A * 2 * (0.08 + 0.88 * q), 2)
    items += frill_items(up_base, lambda q: (-V[0], -V[1]), 66, PINK, 7 * STEP + 0.01, 8 * STEP, 23)
    # steps 9-11: the pearl swells, sitting on the lower mantle
    px, py = PEARL
    base = (px, py + 100)
    for r, k in PEARL_SIZES:
        s, e = (k - 1) * STEP + 0.01, k * STEP
        cy = base[1] - r
        items.append(it(lump(px, cy, r, 5 + k, 0.02, 16), '#fff4f8', INK, base, s, e))
        items.append(it(lump(px + r * 0.3, cy + r * 0.34, r * 0.36, 7 + k, 0.15, 7), '#f3d3ee', 0, base, s + 0.004, e))
    # step 12: its shine, a white highlight and a glint of colour round its rim
    r = PEARL_SIZES[-1][0]
    cy = base[1] - r
    s, e = 11 * STEP + 0.01, 12 * STEP
    items.append(it(lump(px - r * 0.62, cy + r * 0.2, r * 0.2, 31, 0.2, 6, sy=1.6), '#bff6ff', 0, (px - r * 0.62, cy + r * 0.2), s, e))
    items.append(it(lump(px - r * 0.32, cy - r * 0.38, r * 0.3, 32, 0.15, 7, sy=0.8), '#ffffff', 0, (px - r * 0.32, cy - r * 0.38), s + 0.01, e))
    items.append(it(lump(px - r * 0.02, cy - r * 0.6, r * 0.11, 33, 0.15, 6), '#ffffff', 0, (px - r * 0.02, cy - r * 0.6), s + 0.03, e))
    return items


def clam_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    return draw(g.sprite_svg(clam_items(), t), CLAM_FRONT)


def strip(times, out: Path, name: str, sc=0.42, per_row=5) -> None:
    tiles = [clam_frame(t) for t in times]
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    rows = math.ceil(len(tiles) / per_row)
    im = Image.new('RGB', (tw * per_row + 10 * (per_row + 1), (th + 50) * rows + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(times, tiles)):
        x, y = 10 + (i % per_row) * (tw + 10), 10 + (i // per_row) * (th + 50)
        semis = round(tt * 12)
        d.text((x, y), f'frame {tt:.2f}' + (f'  (split +{semis})' if abs(tt * 12 - semis) < 1e-6 else ''), fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
    im.save(out / name)


def clam_main() -> None:
    m.CROP = (2480, 1930, 1360, 1080)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = OUT.parent / 'giant-clam'
    out.mkdir(parents=True, exist_ok=True)
    clam_frame(1.0).save(out / 'end-frame.png')
    strip([0, 0.25, 0.5, 0.75, 1.0], out, 'strip.png')
    strip([k / 12 for k in range(13)], out, 'steps.png', sc=0.3)
    print('wrote', out)


LABEL = ("The purple ledge: shows the split point (display only); it is a giant clam: as the split rises from C4 its "
         "fluted upper shell lifts open a step at a time, its mantles frill out, and a pearl swells inside and shines")


def export() -> None:
    import json
    items = clam_items()
    build = {'label': LABEL,
             'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['open'], 'front': CLAM_FRONT, 'items': items}],
             'objectParts': {'open': []}}
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(items), 'sprites to', path)


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if not args:
        main()
    elif args[0] == 'one':
        main(args[1])
    elif args[0] == 'clam':
        clam_main()
    elif args[0] == 'export':
        export()
