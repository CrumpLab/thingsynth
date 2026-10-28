# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (tonewheel crosstalk at its most, -20 dB) for the purple path: the pale sage band down the left of
the stream, a long tapering tail at the top left that runs down to the pink horned creature, with an arm forking off
to the right that widens into a pointed wedge against the purple plug and its blue ring.

    uv run scripts/path_endframes.py          # the five end frames and sheet
    uv run scripts/path_endframes.py snake    # the chosen two-headed snake: progression strip and end frame
    uv run scripts/path_endframes.py export   # docs/objects/tg-crosstalk/build.json
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
m.CROP = (1250, 2250, 1300, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-crosstalk/endframes'
p, outlined, circle, bez = m.p, m.outlined, g.circle, g.bez
INK = 15
SAGE, SAGE2 = '#b4d78b', '#9fc877'          # the path as it reads on the painting, and a shade of it
LAV, LAV2 = '#c9a3f0', '#a77fe0'            # the purple it is named for
PINK, PINK2, MOUTH = '#ff7fd8', '#f64c76', '#8a1f4a'
YEL, CYAN, ORANGE, WHITE = '#ffe066', '#7fe0f0', '#ff9f43', '#ffffff'
FRONT = ['f170', 'f172', 'f173', 'f080', 'f081']  # the pink horned creature and the purple plug in its blue ring


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


# ---- hand-drawn shapes ---------------------------------------------------------------------------------------------
def closed(P) -> str:
    """A smooth closed curve through the points (Catmull-Rom)."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sy=1.0) -> str:
    """A lumpy round (or, with sy, oval) shape round (x, y)."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        u, v = math.cos(a) * rr, math.sin(a) * rr * sy
        P.append((x + u * math.cos(rot) - v * math.sin(rot), y + u * math.sin(rot) + v * math.cos(rot)))
    return closed(P)


def place(P, ox, oy, deg=0.0, s=1.0, flip=False):
    """Local points (facing +x) moved to (ox, oy), turned by deg and scaled; flip mirrors them first (facing -x)."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in P:
        x, y = (-x if flip else x) * s, y * s
        out.append((ox + x * ca - y * sa, oy + x * sa + y * ca))
    return out


def jit(P, seed, amt=7):
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * 2 * amt, y + (rnd.random() - 0.5) * 2 * amt) for x, y in P]


def tube(P, w0, w1) -> str:
    """A tapered outlined limb along the centreline P, w0 to w1 either side, with a round cap at the end drawn as a
    true half circle (whichever way the limb points)."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = w0 + (w1 - w0) * i / (n - 1)
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    (ax, ay), (ex, ey) = P[-2], P[-1]
    h = math.atan2(ey - ay, ex - ax)
    cap = [(ex + math.cos(h + math.pi / 2 - k * math.pi / 8) * w1, ey + math.sin(h + math.pi / 2 - k * math.pi / 8) * w1)
           for k in range(1, 8)]
    return 'M' + 'L'.join(p(*q) for q in L + cap + R[::-1]) + 'Z'


def limb(P, w0, w1, col, ink=INK) -> str:
    """A tapered outlined limb along P growing out of a shape: like tube, but its outline left open at the root, so it
    joins whatever it grows from without a seam."""
    d = tube(P, w0, w1)
    # the fill closes across the root; the line goes up one side, round the tip, back down the other, and stops
    return outlined(d, col, ink, d[:-1])


def eye(cx, cy, r, look=(1, 0), ink=INK * 0.85) -> str:
    out = outlined(lump(cx, cy, r, int(cx), 0.05, 8), WHITE, ink)
    px, py = cx + look[0] * r * 0.35, cy + look[1] * r * 0.35
    out += f'<path d="{circle(px, py, r * 0.42)}" fill="#000"/>'
    out += f'<path d="{circle(px + r * 0.15, py - r * 0.16, r * 0.13)}" fill="#fff"/>'
    return out


# ---- 1: two-headed snake --------------------------------------------------------------------------------------------
def snake_head(ox, oy, deg, s, flip, seed) -> str:
    """A big open-mouthed serpent head facing +x from a neck at (0, 0), in local units, placed and turned."""
    P = lambda pts: closed(jit(place(pts, ox, oy, deg, s, flip), seed))
    mouth = [(20, 5), (150, -30), (250, -40), (260, 25), (230, 95), (120, 75), (30, 45)]
    upper = [(-60, -40), (10, -105), (110, -125), (210, -100), (270, -55), (255, -30), (150, -20), (60, -5), (-20, 20)]
    lower = [(-40, 30), (40, 40), (140, 70), (230, 95), (245, 120), (190, 140), (80, 125), (-20, 90)]
    tongue = place([(80, 40), (160, 35), (205, 20), (230, 0)], ox, oy, deg, s, flip)
    out = outlined(P(mouth), MOUTH, INK)
    out += outlined(P(lower), SAGE2, INK)
    out += outlined(tube(tongue, 22 * s, 14 * s), PINK2, INK * 0.8)
    out += outlined(P(upper), SAGE, INK)
    ex, ey = place([(115, -75)], ox, oy, deg, s, flip)[0]
    out += eye(ex, ey, 40 * s, (-1 if flip else 1, 0.1))
    # two nostril dots, a stripe of lavender down its crown
    nx, ny = place([(235, -60)], ox, oy, deg, s, flip)[0]
    out += f'<path d="{circle(nx, ny, 8 * s)}" fill="#000"/>'
    # two big lavender spots on its crown: the purple the path is named for
    for k, (u, v, r) in enumerate([(20, -60, 26), (175, -78, 20)]):
        sx, sy = place([(u, v)], ox, oy, deg, s, flip)[0]
        out += outlined(lump(sx, sy, r * s, seed * 5 + k, 0.12, 7), LAV, INK * 0.7)
    return out


def v1_snake() -> Image.Image:
    """Two-headed snake: the path rears up into a two-headed serpent, its two arms lifting heads that chatter at each
    other over the fork, mouths wide open."""
    out = ''
    # the necks rise out of the bands: the tail arm (f105) and the right arm (f106)
    out += limb(bez((1712, 2850), (1680, 2740), (1660, 2670), (1690, 2600), 24), 66, 60, SAGE)
    out += limb(bez((2195, 2900), (2215, 2790), (2230, 2700), (2205, 2610), 24), 66, 60, SAGE)
    out += snake_head(1700, 2600, -14, 0.85, False, 11)
    out += snake_head(2200, 2610, 14, 0.85, True, 12)
    return draw(out, FRONT)


# ---- 2: high five --------------------------------------------------------------------------------------------------
def hand(ox, oy, deg, s, flip, seed, col) -> str:
    """A big open hand reaching up (-y) from a wrist at (0, 0): four fat fingers fanned, a thumb out to the side away
    from the other hand (-x), and a lumpy palm over their roots. Local units, placed and turned."""
    Q = lambda pts: place(pts, ox, oy, deg, s, flip)
    out = ''
    for k, (a, L, bx) in enumerate([(-14, 110, -63), (-4, 135, -21), (6, 130, 21), (16, 105, 63)]):
        r = math.radians(a)
        P = [(bx, -120), (bx + math.sin(r) * L * 0.5, -150 - math.cos(r) * L * 0.5), (bx + math.sin(r) * L, -150 - math.cos(r) * L)]
        out += outlined(tube(jit(Q(P), seed + k, 3), 24 * s, 22 * s), col, INK * 0.9)
    out += outlined(tube(Q([(-60, -50), (-115, -80), (-145, -120)]), 25 * s, 23 * s), col, INK * 0.9)
    palm = [(-50, 10), (-88, -60), (-86, -140), (0, -168), (86, -142), (88, -70), (50, 10)]
    out += outlined(closed(jit(Q(palm), seed, 4)), col, INK)
    return out


def v2_high_five() -> Image.Image:
    """High five: the path's two arms lift up out of the fork as arms, big open hands slapping together palm to palm
    over it, a yellow burst where they meet."""
    out = ''
    burst = []
    for k in range(16):
        a = k / 16 * 2 * math.pi
        r = 175 if k % 2 == 0 else 95
        burst.append((1945 + math.cos(a) * r, 2470 + math.sin(a) * r))
    out += outlined(closed(jit(burst, 70, 8)), YEL, INK * 0.9)
    out += limb(bez((1712, 2850), (1690, 2760), (1720, 2720), (1770, 2695), 24), 58, 52, SAGE)
    out += limb(bez((2195, 2900), (2215, 2800), (2175, 2740), (2120, 2700), 24), 58, 52, SAGE)
    out += hand(1775, 2700, 21, 1.1, False, 71, SAGE)
    out += hand(2115, 2705, -21, 1.1, True, 72, SAGE)
    for x, y, a in [(1700, 2420, -50), (2190, 2420, 50), (1945, 2300, 0)]:
        out += outlined(tube(place([(-40, 12), (0, -8), (40, 12)], x, y, a), 16, 12), PINK, INK * 0.75)
    return draw(out, FRONT)


# ---- 3: chattering flowers -------------------------------------------------------------------------------------------
def flower(x, y, r, petals, col, seed, look) -> str:
    """A big flower head: lumpy petals round a yellow disc whose middle is an open, chattering mouth."""
    rnd = random.Random(seed)
    out = ''
    for k in range(petals):
        a = k / petals * 2 * math.pi + rnd.random() * 0.2
        px, py = x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62
        out += outlined(lump(px, py, r * 0.45, seed * 11 + k, 0.12, 7, a, 0.75), col, INK * 0.85)
    out += outlined(lump(x, y, r * 0.48, seed * 3, 0.08, 9), YEL, INK * 0.85)
    mx, my = x + look * r * 0.08, y + r * 0.06
    out += outlined(lump(mx, my, r * 0.24, seed * 5, 0.12, 7, 0, 0.8), MOUTH, INK * 0.75)
    out += f'<path d="{lump(mx, my + r * 0.09, r * 0.13, seed * 9, 0.1, 7, 0, 0.55)}" fill="{PINK2}"/>'
    for dx in (-0.2, 0.2):
        out += f'<path d="{circle(x + (dx + look * 0.08) * r, y - r * 0.24, r * 0.07)}" fill="#000"/>'
    return out


def stem(base, top, bend, w0=26, w1=18) -> str:
    (x0, y0), (x1, y1) = base, top
    P = bez((x0, y0), (x0 + bend, y0 + (y1 - y0) * 0.4), (x1 - bend * 0.3, y1 - (y1 - y0) * 0.3), (x1, y1), 20)
    out = limb(P, w0, w1, '#5fbf4a', INK * 0.85)
    mx, my = P[9]
    out += outlined(lump(mx + 50 * (1 if bend > 0 else -1), my, 60, int(x0), 0.1, 7, 0.4 if bend > 0 else -0.4, 0.45), '#7fd36b', INK * 0.8)
    return out


def v3_flowers() -> Image.Image:
    """Chattering flowers: big candy flowers spring up out of the path in two pairs, each head leaning in to its
    neighbour, their middles open mouths, talking over one another."""
    out = ''
    # (base in the band, head, radius, petals, colour, which way it looks, stem bend)
    F = [((1672, 2770), (1590, 2560), 112, 7, PINK, 1, -60),
         ((1745, 2880), (1790, 2590), 118, 8, CYAN, -1, 50),
         ((2010, 2880), (2000, 2620), 112, 6, ORANGE, 1, -50),
         ((2200, 2885), (2215, 2600), 122, 7, LAV, -1, 50)]
    for base, top, r, n, col, look, bend in F:
        out += stem(base, top, bend)
    for k, (base, top, r, n, col, look, bend) in enumerate(F):
        out += flower(top[0], top[1], r, n, col, 31 + k, look)
    return draw(out, FRONT)


# ---- 4: chattering teeth ------------------------------------------------------------------------------------------
def tooth(x, y, w, h, down, seed) -> str:
    """One big lumpy white tooth, its root at (x, y), hanging down (or standing up)."""
    s = 1 if down else -1
    P = [(x - w / 2, y - s * 12), (x + w / 2, y - s * 12), (x + w * 0.5, y + s * h * 0.6), (x + w * 0.25, y + s * h),
         (x - w * 0.25, y + s * h), (x - w * 0.5, y + s * h * 0.6)]
    return outlined(closed(jit(P, seed, 4)), WHITE, INK * 0.8)


def v4_teeth() -> Image.Image:
    """Chattering teeth: the right arm of the path becomes a big chattering jaw, its jagged underside turning into a
    row of big white teeth and a lower jaw dropping open beneath it, a pink tongue inside."""
    out = ''
    mouth = [(1880, 2880), (2030, 2925), (2175, 2935), (2250, 3010), (2265, 3110), (2180, 3150), (2040, 3080), (1930, 2980)]
    out += outlined(closed(jit(mouth, 80, 4)), MOUTH, INK)
    out += outlined(lump(2140, 3060, 80, 81, 0.1, 8, -0.5, 0.55), PINK2, INK * 0.85)
    # lower jaw: the path's sage, hinged under the fork, swung down
    jaw = [(1860, 2880), (1925, 2990), (2040, 3095), (2180, 3165), (2290, 3150), (2300, 3200), (2190, 3240),
           (2030, 3180), (1900, 3060), (1830, 2930)]
    lower_teeth = ''.join(tooth(x, y, 62, 64, False, 90 + k) for k, (x, y) in
                          enumerate([(1960, 3040), (2035, 3100), (2115, 3145), (2200, 3168)]))
    out += lower_teeth + outlined(closed(jit(jaw, 82, 4)), SAGE, INK)
    # the upper teeth hang from the band's underside, the gum a lavender strip they grow from
    gum = [(1890, 2870), (2030, 2915), (2175, 2925), (2255, 3000), (2262, 3060), (2225, 3020), (2160, 2965),
           (2030, 2955), (1900, 2905)]
    upper_teeth = ''.join(tooth(x, y, 66, 74, True, 100 + k) for k, (x, y) in
                          enumerate([(1965, 2925), (2040, 2948), (2118, 2955), (2200, 2985)]))
    out += upper_teeth + outlined(closed(jit(gum, 83, 3)), LAV, INK * 0.85)
    for x, y, a in [(2330, 3030, 70), (2345, 3120, 100), (1800, 3000, -110)]:
        out += outlined(tube(place([(-34, 10), (0, -6), (34, 10)], x, y, a), 14, 10), YEL, INK * 0.7)
    return draw(out, FRONT)


# ---- 5: party line --------------------------------------------------------------------------------------------------
def v5_party_line() -> Image.Image:
    """Party line: the right arm of the path pricks up a huge listening ear, and its other end, down by the horned
    creature, opens into big lips whispering up to it; puffs of whisper drift between, eavesdropped."""
    out = ''
    # the ear rises out of the band, its opening turned to the left, toward the lips
    ear = [(2200, 2500), (2290, 2560), (2320, 2680), (2290, 2790), (2240, 2880), (2170, 2890), (2140, 2830),
           (2150, 2760), (2110, 2690), (2090, 2600), (2120, 2530)]
    out += outlined(closed(jit(ear, 51, 5)), SAGE, INK)
    bowl = [(2185, 2565), (2255, 2610), (2270, 2710), (2235, 2785), (2190, 2800), (2180, 2740), (2150, 2670), (2145, 2600)]
    out += outlined(closed(jit(bowl, 52, 4)), PINK, INK * 0.9)
    fold = [(2195, 2615), (2235, 2650), (2232, 2725), (2205, 2700), (2190, 2650)]
    out += outlined(closed(jit(fold, 53, 3)), SAGE2, INK * 0.8)
    out += f'<path d="{lump(2185, 2752, 18, 57, 0.1, 7)}" fill="{MOUTH}"/>'
    out += f'<path d="{lump(2185, 2878, 50, 58, 0.06, 8)}" fill="{SAGE}"/>'
    # the lips at the lower end of the tail arm, open and turned up toward the ear
    lx, ly, a, sc = 1905, 2960, -28, 1.5
    upper = [(-60, -10), (-20, -55), (10, -40), (40, -60), (85, -25), (95, -5), (30, -12), (-20, -8)]
    lower = [(-60, 5), (-10, 12), (40, 14), (95, 8), (70, 52), (10, 62), (-40, 42)]
    out += f'<path d="{lump(1880, 2985, 72, 56, 0.06, 8)}" fill="{SAGE}"/>'
    out += outlined(closed(place([(-50, -2), (90, -22), (90, 18), (-40, 22)], lx, ly, a, sc)), MOUTH, INK * 0.9)
    out += outlined(closed(jit(place(lower, lx, ly, a, sc), 54, 3)), PINK2, INK * 0.9)
    out += outlined(closed(jit(place(upper, lx, ly, a, sc), 55, 3)), PINK2, INK * 0.9)
    # whisper puffs drifting from the lips to the ear, growing as they go
    for k, (x, y, r, c) in enumerate([(1995, 2810, 34, YEL), (2040, 2730, 44, CYAN), (2085, 2640, 52, LAV)]):
        out += outlined(lump(x, y, r, 60 + k, 0.15, 7), c, INK * 0.8)
    return draw(out, FRONT)


VERSIONS = [
    ('1-two-headed-snake', 'Two-headed snake', v1_snake),
    ('2-high-five', 'High five', v2_high_five),
    ('3-chattering-flowers', 'Chattering flowers', v3_flowers),
    ('4-chattering-teeth', 'Chattering teeth', v4_teeth),
    ('5-party-line', 'Party line', v5_party_line),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (crosstalk -80 dB)', m.compose())]
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


# ---- chosen: the two-headed snake ----------------------------------------------------------------------------------
# Picked under 5a: the path itself turns into a creature that could live there (rule 1), with a character doing
# something social (rule 2), a big drawn reading of crosstalk's "the notes chatter to each other" (rule 4), on its
# most characterful part: the two arm ends at the fork. Crosstalk from -80 to -20 dB (continuous): the tail arm's neck
# rises (0-0.22) and its head comes out of it, sleepy (0.14-0.34); then the right arm's neck (0.22-0.44) and head
# (0.36-0.54); the lids lift and the eyes look at each other (0.5-0.68); the jaws drop open, the second head's a beat
# after the first, so they chatter (0.6-0.9), tongues last inside; lavender spots pop on their crowns (0.84-1).
# Placed `over`: nothing of the painting stands in front of the necks or heads.
def sp(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


# (neck centreline, head origin, turn, flip, seed, neck window, head window, lid lifts, jaw window, spots window)
HEADS = [
    (((1738, 2870), (1690, 2750), (1662, 2670), (1690, 2600)), (1690, 2600), -14, False, 11,
     (0.0, 0.22), (0.14, 0.34), (0.5, 0.6), (0.6, 0.76), (0.84, 0.94)),
    (((2135, 2905), (2165, 2790), (2200, 2700), (2185, 2610)), (2185, 2610), 14, True, 12,
     (0.22, 0.44), (0.36, 0.54), (0.56, 0.66), (0.68, 0.86), (0.9, 1.0)),
]
HS = 0.85


def snake_items() -> list[dict]:
    items = []
    for neck, (ox, oy), deg, flip, seed, nw, hw, lw, jw, sw in HEADS:
        Q = lambda pts, sd=seed, a=4: jit(place(pts, ox, oy, deg, HS, flip), sd, a)
        root = neck[0]
        # the neck: a fill-only body and an open outline (no line across its root), both stretching up from the band
        body = tube(bez(*neck, 24), 66, 60)
        items.append(sp(body, SAGE, 0, root, *nw, 'y'))
        items.append(sp(body[:-1], 'none', INK, root, *nw, 'y'))
        hinge = place([(0, 20)], ox, oy, deg, HS, flip)[0]
        # closed: a lip of lower jaw tucked under the upper jaw; it gives way to the open jaw
        shut = [(-40, 15), (60, 0), (160, -12), (255, -32), (262, -5), (190, 30), (70, 48), (-25, 48)]
        items.append(sp(closed(Q(shut, seed + 1)), SAGE2, INK, (ox, oy), *hw, out=(jw[0] + 0.04, jw[0] + 0.1)))
        # open: the mouth, the tongue inside, the lower jaw dropping from the hinge
        mouth = [(20, 5), (150, -30), (250, -40), (260, 25), (230, 95), (120, 75), (30, 45)]
        lower = [(-40, 30), (40, 40), (140, 70), (230, 95), (245, 120), (190, 140), (80, 125), (-20, 90)]
        tongue = place([(70, 45), (150, 40), (205, 20), (235, 0)], ox, oy, deg, HS, flip)
        j0, j1 = jw
        items.append(sp(closed(Q(mouth, seed)), MOUTH, INK, hinge, j0, j1 - 0.04))
        items.append(sp(tube(tongue, 22 * HS, 15 * HS), PINK2, INK * 0.8, tongue[0], j0 + 0.08, j1))
        items.append(sp(closed(Q(lower, seed + 2)), SAGE2, INK, hinge, j0, j1 - 0.04))
        # the upper jaw: the head itself, lumpy, coming out of the neck's top
        upper = [(-60, -40), (10, -105), (110, -125), (210, -100), (270, -55), (255, -30), (150, -20), (60, -5), (-20, 20)]
        items.append(sp(closed(Q(upper, seed + 3, 7)), SAGE, INK, (ox, oy), *hw))
        nx, ny = place([(235, -60)], ox, oy, deg, HS, flip)[0]
        items.append(sp(circle(nx, ny, 8 * HS), '#000', 0, (nx, ny), hw[1] - 0.06, hw[1]))
        # the eye: white, a sleepy sage lid over its top half that lifts away, then the pupil looking across
        ex, ey = place([(115, -75)], ox, oy, deg, HS, flip)[0]
        r = 40 * HS
        items.append(sp(lump(ex, ey, r, int(ex), 0.05, 8), WHITE, INK * 0.85, (ex, ey), hw[0] + 0.06, hw[1]))
        lid = [(ex + math.cos(a) * r * 1.12, ey + math.sin(a) * r * 1.12) for a in [math.pi * (1 + k / 8) for k in range(9)]]
        lid += [(ex + r * 0.8, ey + r * 0.22), (ex, ey + r * 0.32), (ex - r * 0.8, ey + r * 0.22)]
        items.append(sp(closed(jit(lid, seed + 5, 2)), SAGE, INK * 0.85, (ex, ey - r), hw[0] + 0.06, hw[1], out=lw))
        lx = -1 if flip else 1
        px, py = ex + lx * r * 0.35, ey + r * 0.05
        items.append(sp(circle(px, py, r * 0.42), '#000', 0, (px, py), lw[0] + 0.04, lw[1] + 0.02))
        items.append(sp(circle(px + r * 0.15, py - r * 0.16, r * 0.13), WHITE, 0, (px + r * 0.15, py - r * 0.16), lw[1] - 0.02, lw[1] + 0.04))
        # lavender spots on its crown, last
        for k, (u, v, rr) in enumerate([(20, -60, 26), (175, -78, 20)]):
            sx, sy = place([(u, v)], ox, oy, deg, HS, flip)[0]
            a, b = sw
            items.append(sp(lump(sx, sy, rr * HS, seed * 5 + k, 0.12, 7), LAV, INK * 0.7, (sx, sy),
                            a + k * (b - a) * 0.4, a + (k * 0.4 + 0.6) * (b - a)))
    # draw order: both necks first, then each head's parts in the order listed
    necks = [it for it in items if it['grow'] == 'y']
    return necks + [it for it in items if it['grow'] != 'y']


def snake_frame(t: float) -> Image.Image:
    im = m.compose()
    if t > 0:
        im.alpha_composite(m.svg(g.sprite_svg(snake_items(), t)))
    return im


def snake_main() -> None:
    out = OUT.parent / 'two-headed-snake'
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()

    def strip(frames, name, sc):
        tiles = [snake_frame(t) for t in frames]
        w, h = tiles[0].size
        tw, th = int(w * sc), int(h * sc)
        im = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        d = ImageDraw.Draw(im)
        for i, (tt, tile) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}', fill='black', font=font)
            im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        im.save(out / name)
        return tiles
    tiles = strip([0, 0.25, 0.5, 0.75, 1.0], 'strip.png', 0.42)
    tiles[-1].save(out / 'end-frame.png')
    strip([k / 10 for k in range(11)], 'steps.png', 0.24)
    print('wrote', out)


if __name__ == '__main__' and 'snake' in __import__('sys').argv[1:]:
    snake_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The purple path: drag for Crosstalk; it rears up into a two-headed snake: two necks rise out of it, '
                 'sleepy eyes wake, and the heads chatter at each other, one mouth opening just after the other',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': snake_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']), 'shapes')
