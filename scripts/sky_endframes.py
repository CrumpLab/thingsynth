# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (output Volume at its loudest) for the sky: the translucent cream wash (f303) behind everything
across the top of the painting, the pastel bands of the wash showing through it. It is mostly covered; it shows as a
thin strip along the top edge and in a few gaps: between the big stalk cap and the cyan link, between the cap and
the link's cyan leaf, and the biggest, right of the stalk forest round the blue teardrop and above the pink cloud.

    uv run scripts/sky_endframes.py          # the five end frames and sheet
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
m.CROP = (1700, 375, 1250, 1000)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/out-level/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 13
SKY = 'f303'
PINK, YEL, CYAN, LAV, ORA, GRN, MAG, CREAM = '#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b', '#FF1ABE', '#FFFCCA'
CORAL, DARK, ICE = '#ff7a8a', '#4a1638', '#bdf3ff'


def crop_ink() -> list[str]:
    x, y, w, h = m.CROP
    out = []
    for i, s in m.IP.items():
        bx, by, bw, bh = s['bbox']
        if bx < x + w and bx + bw > x and by < y + h and by + bh > y:
            out.append(i)
    return out


def draw(on: str = '', over: str = '') -> Image.Image:
    """`on`: drawn on the sky, clipped to it, under every outline in the crop, so it sits behind everything round the
    gaps (the app's "on" placement). `over`: on top of everything."""
    im = m.compose()
    if on:
        ink = ''.join(f'<path d="{m.INKS[i]}"/>' for i in crop_ink())
        im.alpha_composite(m.svg(f'<clipPath id="sky"><path d="{m.FILLS[SKY]}"/></clipPath>'
                                 f'<g clip-path="url(#sky)">{on}</g><g fill="#000">{ink}</g>'))
    if over:
        im.alpha_composite(m.svg(over))
    return im


def smooth(P) -> str:
    """A closed Catmull-Rom curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, rx, ry, seed, wob=0.1, n=10, rot=0.0) -> str:
    """A lumpy, hand-drawn oval."""
    rnd = random.Random(seed)
    P = []
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * ca - v * sa, y + u * sa + v * ca))
    return smooth(P)


def wobble(P, amt, seed):
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * amt, y + (rnd.random() - 0.5) * amt) for x, y in P]


# ---- 1. shouting sky ------------------------------------------------------------------------------------------------
def v1_shout() -> Image.Image:
    """Shouting sky: the sky itself wakes up and shouts: a big round eye opens in the gap under the stalk cap, the
    teardrop becomes its nose, and a huge open mouth yells in the gap above the pink cloud."""
    on = ''
    # brow, eye
    ex, ey = 2285, 750
    on += outlined(lump(ex, ey, 100, 84, 5, 0.06, 11, -10), '#ffffff', INK * 1.3)
    on += outlined(lump(ex - 14, ey + 8, 52, 54, 6, 0.06, 9), CYAN, INK)
    on += f'<path d="{circle(ex - 16, ey + 10, 25)}" fill="#000"/><path d="{circle(ex - 4, ey - 6, 10)}" fill="#fff"/>'
    # mouth: lumpy coral lips round a dark open O with a pink tongue, yelling up-left
    mx, my = 2165, 1075
    on += outlined(lump(mx, my, 150, 104, 7, 0.08, 12, -18), CORAL, INK * 1.2)
    on += outlined(lump(mx + 4, my + 4, 102, 64, 8, 0.07, 11, -18), DARK, INK)
    on += outlined(lump(mx + 30, my + 40, 60, 30, 9, 0.08, 9, -18), PINK, INK * 0.8)
    on += outlined(lump(mx - 40, my - 34, 50, 18, 10, 0.1, 8, -18), '#ffffff', INK * 0.7)
    return draw(on)


# ---- 2. sky dragon --------------------------------------------------------------------------------------------------
def v2_dragon() -> Image.Image:
    """Sky dragon: a long candy festival dragon swims through the sky behind everything, its body looping through
    every gap, along the top strip and down past the cap, and its head roars out of the big gap above the pink
    cloud."""
    path = bez((2960, 420), (2700, 360), (2500, 400), (2420, 520), 20)
    path += bez((2420, 520), (2340, 640), (2320, 680), (2300, 800), 14)[1:]
    path += bez((2300, 800), (2290, 900), (2280, 960), (2230, 1030), 12)[1:]
    on = ''
    seg = 5
    cols = [PINK, ORA]
    # spines: lumpy candy fins along its back, then the body in bands, then a yellow belly stripe
    for k in range(2, len(path) - 4, 4):
        (x, y), (x2, y2) = path[k], path[k + 1]
        d = math.hypot(x2 - x, y2 - y) or 1
        nx, ny = (y2 - y) / d, -(x2 - x) / d
        on += outlined(lump(x + nx * 62, y + ny * 62, 34, 22, 40 + k, 0.12, 8, math.degrees(math.atan2(ny, nx))), CYAN, INK * 0.9)
    for k in range(0, len(path) - seg, seg):
        on += outlined(tube(path[k:k + seg + 1], 66, 66), cols[(k // seg) % 2], INK)
    for k in range(0, len(path) - seg, seg):
        P = path[k:k + seg + 1]
        sh = []
        for i, (x, y) in enumerate(P):
            a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
            dd = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            sh.append((x - (b[1] - a[1]) / dd * -26, y + (b[0] - a[0]) / dd * -26))
        on += outlined(tube(sh, 18, 18), YEL, INK * 0.7)
    # head: a big pink head in profile, roaring open-jawed to the left, drawn over the gap
    hx, hy = 2120, 1085
    head = ''
    for k, (dx, col) in enumerate(((60, CYAN), (110, YEL))):  # two candy horns sweeping back
        P = bez((hx + dx, hy - 90), (hx + dx + 30, hy - 160), (hx + dx + 90, hy - 190), (hx + dx + 140, hy - 170), 16)
        head += outlined(tube(P, 26, 8), col, INK)
    head += outlined(lump(hx - 30, hy + 10, 95, 48, 61, 0.08, 10, 14), DARK, INK)  # inside of the mouth
    head += outlined(lump(hx - 55, hy + 30, 52, 20, 62, 0.12, 8, 20), CORAL, INK * 0.8)  # tongue
    head += outlined(lump(hx - 40, hy + 58, 108, 30, 63, 0.08, 10, 24), ORA, INK)  # lower jaw, dropped open
    for fx, fy, s in ((hx - 105, hy + 26, 1), (hx + 10, hy + 70, -1)):  # two fangs
        head += outlined(f'M{p(fx - 15, fy)}Q{p(fx, fy - 6 * s)} {p(fx + 15, fy)}L{p(fx + 2, fy - 38 * s)}Z', '#ffffff', INK * 0.7)
    skull = lump(hx + 50, hy - 40, 105, 72, 64, 0.07, 11, -8)
    snout = lump(hx - 70, hy - 30, 100, 44, 65, 0.08, 10, 6)
    head += outlined(skull, PINK, INK) + outlined(snout, PINK, INK)
    head += f'<path d="{lump(hx + 50, hy - 40, 92, 60, 64, 0.07, 11, -8)}" fill="{PINK}"/><path d="{lump(hx - 70, hy - 30, 88, 33, 65, 0.08, 10, 6)}" fill="{PINK}"/>'
    head += outlined(lump(hx - 150, hy - 50, 14, 10, 66, 0.1, 7), DARK, INK * 0.6)  # nostril
    head += outlined(lump(hx + 60, hy - 64, 38, 30, 67, 0.06, 9, -8), '#ffffff', INK * 1.2)  # eye
    head += f'<path d="{circle(hx + 50, hy - 62, 15)}" fill="#000"/><path d="{circle(hx + 56, hy - 70, 5)}" fill="#fff"/>'
    head += outlined(lump(hx + 64, hy - 98, 46, 14, 68, 0.1, 8, -12), YEL, INK)  # brow
    head += outlined(tube(bez((hx - 160, hy - 40), (hx - 220, hy - 80), (hx - 250, hy - 10), (hx - 300, hy - 40), 16), 14, 5), YEL, INK * 0.8)  # whisker
    head += outlined(lump(hx + 130, hy - 10, 40, 34, 69, 0.15, 8), CYAN, INK)  # cheek frill
    return draw(on, f'<g transform="translate({hx} {hy}) scale(1.3) translate({-hx} {-hy})">{head}</g>')


# ---- 3. trumpet vine ------------------------------------------------------------------------------------------------
def trumpet(x, y, ang, L, R, col, seed) -> str:
    """A morning glory (a living loudspeaker): a flared bell of R across opening at (x, y), its throat running back L
    along ang (degrees), outlined; a pale star in the throat."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    bx, by = x - ux * L, y - uy * L
    throat = (f'M{p(bx + vx * 14, by + vy * 14)}C{p(bx + ux * L * 0.6 + vx * 18, by + uy * L * 0.6 + vy * 18)} '
              f'{p(x - ux * 30 + vx * R * 0.6, y - uy * 30 + vy * R * 0.6)} {p(x + vx * R * 0.95, y + vy * R * 0.95)}'
              f'L{p(x - vx * R * 0.95, y - vy * R * 0.95)}C{p(x - ux * 30 - vx * R * 0.6, y - uy * 30 - vy * R * 0.6)} '
              f'{p(bx + ux * L * 0.6 - vx * 18, by + uy * L * 0.6 - vy * 18)} {p(bx - vx * 14, by - vy * 14)}Z')
    out = outlined(throat, col, INK)
    rnd = random.Random(seed)
    rim, star = [], []
    for k in range(10):  # five petal points round a foreshortened rim, and a white star in the throat
        t = k / 10 * 2 * math.pi + seed
        f = (1.0 if k % 2 == 0 else 0.9) * (1 + (rnd.random() - 0.5) * 0.08)
        u, v = math.cos(t) * R * 0.38 * f, math.sin(t) * R * f
        rim.append((x + ux * u + vx * v, y + uy * u + vy * v))
        f2 = 0.7 if k % 2 == 0 else 0.2
        star.append((x + ux * (math.cos(t) * R * 0.38 * f2 + 6) + vx * math.sin(t) * R * f2, y + uy * (math.cos(t) * R * 0.38 * f2 + 6) + vy * math.sin(t) * R * f2))
    out += outlined(smooth(rim), col, INK)
    out += outlined(smooth(star), '#ffffff', INK * 0.6)
    out += f'<path d="{lump(x + ux * 8, y + uy * 8, R * 0.07, R * 0.17, seed + 2, 0.1, 8, ang)}" fill="{YEL}"/>'
    # sepal cup where the throat meets the vine
    out += outlined(lump(bx + ux * 10, by + uy * 10, 26, 22, seed + 3, 0.15, 7, ang), GRN, INK * 0.8)
    return out


def leaf(x, y, ang, s, seed) -> str:
    a = math.radians(ang)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    P = [(x, y), (x + ux * s * 0.4 + vx * s * 0.45, y + uy * s * 0.4 + vy * s * 0.45), (x + ux * s, y + uy * s),
         (x + ux * s * 0.4 - vx * s * 0.45, y + uy * s * 0.4 - vy * s * 0.45)]
    return outlined(smooth(wobble(P, s * 0.08, seed)), GRN, INK * 0.8)


def v3_trumpets() -> Image.Image:
    """Trumpet vine: a vine climbs up through the sky's gaps from behind the pink cloud and opens big candy morning
    glories, living loudspeakers, in each gap, blaring out."""
    vine = bez((2100, 1300), (2230, 1150), (2340, 1000), (2300, 880), 16)
    vine += bez((2300, 880), (2260, 780), (2300, 700), (2380, 600), 12)[1:]
    vine += bez((2380, 600), (2440, 520), (2440, 470), (2400, 420), 10)[1:]
    on = outlined(tube(vine, 18, 12), GRN, INK * 0.9)
    on += leaf(2250, 1110, 200, 110, 1) + leaf(2290, 800, -10, 100, 2) + leaf(2420, 540, 10, 90, 3)
    over = trumpet(2120, 1075, 200, 160, 135, MAG, 10)
    over += trumpet(2300, 720, -160, 120, 110, LAV, 20)
    over += trumpet(2470, 500, -40, 120, 105, YEL, 30)
    return draw(on, over)


# ---- 4. hot-air balloon ---------------------------------------------------------------------------------------------
def v4_balloon() -> Image.Image:
    """Hot-air balloon: volume as size: a candy balloon swells up out of the gap between the cap and the link,
    striped, with a basket underneath, as if the sky inflated it."""
    cx, cy, rx, ry = 2445, 600, 150, 175
    out = ''
    # basket and its skirt first, under the envelope
    out += outlined(f'M{p(cx - 60, cy + ry - 30)}L{p(cx + 60, cy + ry - 30)}L{p(cx + 36, cy + ry + 70)}L{p(cx - 36, cy + ry + 70)}Z', ORA, INK)
    for sx in (-30, 30):
        out += outlined(tube([(cx + sx * 1.6, cy + ry + 60), (cx + sx, cy + ry + 130)], 6, 6), '#a4763e', INK * 0.6)
    out += outlined(lump(cx, cy + ry + 160, 52, 40, 3, 0.08, 9), '#c98b4a', INK)
    out += outlined(lump(cx, cy + ry + 128, 58, 14, 4, 0.08, 9), '#a4763e', INK * 0.8)
    # envelope: a lumpy pear, with candy gores as outlined lens shapes
    env = smooth(wobble([(cx, cy - ry), (cx + rx * 0.8, cy - ry * 0.7), (cx + rx, cy - ry * 0.05), (cx + rx * 0.62, cy + ry * 0.62),
                         (cx + rx * 0.3, cy + ry * 0.95), (cx - rx * 0.3, cy + ry * 0.95), (cx - rx * 0.62, cy + ry * 0.62),
                         (cx - rx, cy - ry * 0.05), (cx - rx * 0.8, cy - ry * 0.7)], 26, 7))
    out += outlined(env, PINK, INK * 1.2)
    for k, (w, col) in enumerate([(0.62, YEL), (0.22, CYAN)]):
        d = (f'M{p(cx, cy - ry + 6)}C{p(cx - rx * w * 1.25, cy - ry * 0.5)} {p(cx - rx * w * 1.15, cy + ry * 0.5)} {p(cx, cy + ry * 0.94)}'
             f'C{p(cx + rx * w * 1.15, cy + ry * 0.5)} {p(cx + rx * w * 1.25, cy - ry * 0.5)} {p(cx, cy - ry + 6)}Z')
        out += outlined(d, col, INK)
    out += outlined(lump(cx - 55, cy - 95, 26, 44, 9, 0.12, 8, 20), '#ffffff', INK * 0.6)
    return draw('', out)


# ---- 5. bunting -----------------------------------------------------------------------------------------------------
def v5_bunting() -> Image.Image:
    """Bunting: a party garland strung along the top of the sky, swag after swag, its candy pennants hanging down over
    the tops of things (one pennant more for each step of loudness, right across the painting)."""
    x0, x1 = 1700, 2950
    anchors = [x0 + (x1 - x0) * k / 3 for k in range(4)]
    out = ''
    cols = [PINK, YEL, CYAN, LAV, ORA, GRN]
    k = 0
    for a, b in zip(anchors, anchors[1:]):
        rope = bez((a, 392), (a + (b - a) * 0.3, 470), (a + (b - a) * 0.7, 470), (b, 392), 24)
        flags = ''
        for i in range(1, 5):
            u = i / 5
            x, y = rope[round(u * 24)]
            (xa, ya), (xb, yb) = rope[round(u * 24) - 1], rope[round(u * 24) + 1]
            t = math.atan2(yb - ya, xb - xa)
            w, h = 62, 150
            ca, sa = math.cos(t), math.sin(t)
            P = [(x - ca * w, y - sa * w), (x + ca * w, y + sa * w), (x - sa * -h + ca * 6, y + ca * h + sa * 6)]
            P = [P[0], ((P[0][0] + P[1][0]) / 2, (P[0][1] + P[1][1]) / 2 - 4), P[1],
                 ((P[1][0] + P[2][0]) / 2 + 6, (P[1][1] + P[2][1]) / 2), P[2], ((P[0][0] + P[2][0]) / 2 - 6, (P[0][1] + P[2][1]) / 2)]
            flags += outlined(smooth(wobble(P, 20, 100 + k)), cols[k % 6], INK)
            k += 1
        out += flags + outlined(tube(rope, 9, 9), '#ffffff', INK * 0.7)
    return draw('', out)


VERSIONS = [
    ('1-shouting-sky', 'Shouting sky', v1_shout),
    ('2-sky-dragon', 'Sky dragon', v2_dragon),
    ('3-trumpet-vine', 'Trumpet vine', v3_trumpets),
    ('4-hot-air-balloon', 'Hot-air balloon', v4_balloon),
    ('5-bunting', 'Bunting', v5_bunting),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (-8 dB)', m.compose())]
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


# ---- chosen: the sky dragon -----------------------------------------------------------------------------------------
# Picked: 2 on its own. Changed for the build: the gap above the pink cloud now holds the pink elephant's head, trunk
# and bell (leslie-balance), so the head comes out of the upper gap instead, between the stalk cap and the cyan link,
# roaring up and to the right, and the body loops along the sky's top strip to the right of it. Drawn lumpier and
# looser than a festival-dragon graphic: the body is a chain of uneven lumpy segments, the head is lumpy pieces.
# Volume runs -8..12 dB; presets sit near -6 dB (frame 0.1), so nothing happens before 0.15. The body loops appear
# gap by gap along the top strip from the tail in (0.15-0.55), the head rises into its gap (0.5-0.7), the sleepy eye
# opens (0.65-0.8), horns and whisker sprout (0.75-0.88), and the jaw drops wide at the loudest (0.85-1). The body is
# "on" the sky (clipped to f303, under every outline, so everything stays in front of it); the head is "over".
DCROP = (1950, 375, 1550, 900)
PINK2, ORA2, SPINE, BELLY = '#ff5e8a', '#ff9f43', '#2DFFF4', '#ffe066'
A = math.radians(-32)  # the head's snout points up and to the right
HEAD = (2372.0, 642.0)  # the middle of its skull (before HEAD_K)
NECK = (2322.0, 700.0)  # the bottom of its dive into the gap, where the neck turns and rises
HEAD_K = 1.4  # the head is drawn small in head_raw and scaled up about NECK
# the body's centreline from the tail tip (in the deep pocket over the link's right ring) along the top strip:
# humps arch up out of the painting's top edge, the loops' bottoms dip into the strip's pockets, then it dives into
# the gap behind the cap
BODY = (bez((3225, 545), (3190, 470), (3140, 330), (3060, 330), 10)
        + bez((3060, 330), (2980, 330), (2950, 472), (2880, 472), 10)[1:]
        + bez((2880, 472), (2810, 472), (2790, 318), (2720, 318), 10)[1:]
        + bez((2720, 318), (2650, 318), (2630, 462), (2560, 462), 10)[1:]
        + bez((2560, 462), (2490, 462), (2470, 360), (2420, 380), 8)[1:]
        + bez((2420, 380), (2370, 400), (2330, 560), (2322, 700), 10)[1:])
# when each stretch of it arrives (x ranges, tail first): the tail and first loop, the second loop, the third, the dive
WINDOWS = [(3000, 0.15, 0.27), (2800, 0.25, 0.37), (2500, 0.35, 0.47), (0, 0.45, 0.56)]


def R(u, v):
    """Head-local coordinates: u along the snout (up-right), v across it (positive = the throat side)."""
    x, y = HEAD
    return (x + u * math.cos(A) - v * math.sin(A), y + u * math.sin(A) + v * math.cos(A))


def rot(extra=0.0) -> float:
    return math.degrees(A) + extra


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 4),
         'end': round(min(1.0, e), 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(min(1.0, out[1]), 4)
    return x


def resample(P, step):
    out, acc = [P[0]], 0.0
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        t = step - acc
        while t <= L:
            out.append((x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L))
            t += step
        acc = (acc + L) % step
    return out


def wtube(P, w0, w1, seed, amt=0.12) -> str:
    """A tapered outlined limb whose width wobbles a little, hand-drawn."""
    rnd = random.Random(seed)
    n = len(P)
    Lf, Rt = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = (w0 + (w1 - w0) * i / (n - 1)) * (1 + (rnd.random() - 0.5) * amt)
        Lf.append((x + nx * w, y + ny * w))
        Rt.append((x - nx * w, y - ny * w))
    pts = Lf + Rt[::-1]
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def body_items() -> list[dict]:
    """The body, "on" the sky: lumpy segments of uneven size along the centreline, tail first, each stretch in its
    window; a belly scute on the underside of each, a lumpy tail tuft at the tip."""
    items = []
    S = resample(BODY, 46)
    n = len(S)
    rnd = random.Random(7)
    # the tail tuft first, under the first segments
    tx, ty = S[0]
    for k, (dx, dy, r, col) in enumerate([(22, 60, 46, SPINE), (-26, 52, 38, BELLY), (6, 96, 34, SPINE)]):
        items.append(it(lump(tx + dx, ty + dy, r, r * 1.3, 300 + k, 0.18, 8, rnd.random() * 40 - 20), col, INK,
                        (tx, ty), 0.15 + 0.02 * k, 0.24 + 0.02 * k))
    for i, (x, y) in enumerate(S):
        a, b = S[max(0, i - 1)], S[min(n - 1, i + 1)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        x0, s0, e0 = next(w for w in WINDOWS if x >= w[0])
        # stagger within the stretch, tail end first
        xs = [q[0] for q in S if next(w for w in WINDOWS if q[0] >= w[0])[0] == x0]
        span = (max(xs) - min(xs)) or 1
        u = (max(xs) - x) / span if x0 > 0 else (i - (n - len(xs))) / max(1, len(xs) - 1)
        s = s0 + u * (e0 - s0 - 0.06)
        e = s + 0.06
        w = 58 * (0.55 + 0.45 * min(1.0, i / 7))  # thinner towards the tail
        col = [PINK, PINK2, ORA2][(i // 2) % 3]
        items.append(it(lump(x, y, w * 1.12, w, 400 + i, 0.1, 9, ang), col, INK, (x, y), s, e))
        # a belly scute on the underside (towards +y in screen terms where the loop dips)
        nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        if ny < 0:
            nx, ny = -nx, -ny
        bx, by = x + nx * w * 0.62, y + ny * w * 0.62
        items.append(it(lump(bx, by, w * 0.5, w * 0.3, 500 + i, 0.15, 7, ang), BELLY, INK * 0.8, (bx, by), s + 0.02, e + 0.01))
    return items


def head_raw() -> list[dict]:
    """The head, "over" everything, rising out of the gap: neck, closed jaw, skull and snout with a sleepy eye
    (0.5-0.7); the lid lifts (0.65-0.8); horns, crest and whisker (0.75-0.88); the jaw drops wide (0.85-1)."""
    items = []
    hs, he = 0.52, 0.65
    at = NECK
    # horns and whisker first so their roots tuck under the skull; they grow from their roots
    for k, (u0, v0, du, dv, w, col) in enumerate([(-58, -48, -95, -40, 24, SPINE), (-24, -62, -40, -110, 22, BELLY)]):
        P = bez(R(u0, v0), R(u0 + du * 0.3, v0 + dv * 0.5), R(u0 + du * 0.7, v0 + dv * 0.95), R(u0 + du, v0 + dv * 0.8), 14)
        items.append(it(wtube(P, w, 7, 60 + k, 0.2), col, INK, P[0], 0.75 + 0.03 * k, 0.86 + 0.02 * k))
    for k, (u, v, r) in enumerate([(-95, -20, 34), (-110, 22, 30)]):  # a lumpy cyan frill behind the cheek
        q = R(u, v)
        items.append(it(lump(*q, r * 1.3, r, 70 + k, 0.18, 8, rot(30)), [LAV, BELLY][k], INK, R(-60, 0), 0.76 + 0.02 * k, 0.86))
    # the mouth: a small dark gap and a jaw nearly closed, which give way to the wide one at the loudest
    shut = (0.85, 0.93)
    items.append(it(lump(*R(78, 26), 72, 18, 81, 0.08, 9, rot(6)), DARK, INK, NECK, hs, he, out=shut))
    items.append(it(lump(*R(70, 44), 86, 32, 82, 0.1, 10, rot(9)), ORA2, INK, NECK, hs, he, out=shut))
    hinge = R(-10, 30)
    items.append(it(lump(*R(64, 56), 92, 52, 83, 0.08, 10, rot(24)), DARK, INK, hinge, 0.85, 0.97))
    items.append(it(lump(*R(52, 70), 52, 20, 84, 0.12, 8, rot(30)), CORAL, INK * 0.8, hinge, 0.87, 0.98))
    items.append(it(lump(*R(48, 102), 92, 34, 85, 0.1, 10, rot(38)), ORA2, INK, hinge, 0.85, 1.0))
    fang = lambda u, v, s, dirv: (f'M{p(*R(u - 13, v))}Q{p(*R(u, v - 6 * dirv))} {p(*R(u + 13, v))}'
                                  f'L{p(*R(u + 2, v + 34 * dirv))}Z')
    items.append(it(fang(60, 86, 1, -1), '#ffffff', INK * 0.7, hinge, 0.9, 1.0))  # a lower fang
    # skull and snout, outlined, then fill-only copies so they merge with no seam
    skull, snout = (R(-18, -4), 98, 74, 86), (R(88, -10), 98, 44, 87)
    for (q, rx, ry, sd) in (skull, snout):
        items.append(it(lump(*q, rx, ry, sd, 0.08, 11, rot(-4)), PINK, INK, at, hs, he))
    for (q, rx, ry, sd) in (skull, snout):
        items.append(it(lump(*q, rx - 12, ry - 12, sd, 0.08, 11, rot(-4)), PINK, 0, at, hs, he))
    items.append(it(fang(118, 28, 1, 1), '#ffffff', INK * 0.7, at, hs + 0.05, he))  # upper fangs
    items.append(it(fang(64, 34, 1, 1), '#ffffff', INK * 0.7, at, hs + 0.05, he))
    items.append(it(lump(*R(166, -22), 15, 10, 88, 0.15, 7, rot()), DARK, INK * 0.6, at, hs + 0.05, he))  # nostril
    # the eye: an almond white with a heavy outline, cyan iris; a pink sleepy lid over it that lifts away
    ex, ey = R(-4, -32)
    items.append(it(lump(ex, ey, 40, 30, 89, 0.06, 10, rot(-8)), '#ffffff', INK * 1.25, at, hs + 0.03, he))
    ix, iy = R(4, -30)
    items.append(it(circle(ix, iy, 19), SPINE, INK * 0.8, at, hs + 0.03, he))
    items.append(it(circle(ix + 2, iy + 1, 9), '#000', 0, at, hs + 0.03, he))
    lid_top = R(-4, -64)
    lid = smooth([R(-46, -30), R(-36, -56), R(-4, -66), R(30, -56), R(42, -30), R(18, -24), R(-10, -22), R(-34, -24)])
    items.append(it(lid, PINK, INK * 1.25, lid_top, hs + 0.03, he, 'scale', (0.66, 0.8)))  # shrinks up into the brow
    items.append(it(lump(*R(-2, -74), 46, 15, 90, 0.12, 8, rot(-6)), BELLY, INK, R(-2, -74), 0.62, 0.74))  # brow
    # the whisker curling forward and down off the snout
    P = bez(R(172, 8), R(205, 60), R(215, 120), R(180, 160), 16)
    items.append(it(wtube(P, 13, 5, 91, 0.25), BELLY, INK * 0.8, P[0], 0.78, 0.88))
    return items


def scale_path(d: str, c, k: float) -> str:
    """The path d scaled by k about c (M, L, Q, C, A and Z commands, absolute)."""
    import re
    toks = re.findall(r'[A-Za-z]|-?\d+\.?\d*(?:e-?\d+)?', d)
    out, i, cmd = [], 0, None
    P = lambda x, y: f'{c[0] + (float(x) - c[0]) * k:.1f} {c[1] + (float(y) - c[1]) * k:.1f}'
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            out.append(t)
            i += 1
            continue
        if cmd == 'A':
            rx, ry, r, la, sw, x, y = toks[i:i + 7]
            out.append(f'{float(rx) * k:.1f} {float(ry) * k:.1f} {r} {la} {sw} {P(x, y)}')
            i += 7
        else:
            out.append(P(toks[i], toks[i + 1]))
            i += 2
    return ' '.join(out)


def scaled(items, c, k):
    for q in items:
        q['d'] = scale_path(q['d'], c, k)
        q['at'] = [round(c[0] + (q['at'][0] - c[0]) * k, 1), round(c[1] + (q['at'][1] - c[1]) * k, 1)]
    return items


def head_items() -> list[dict]:
    """The head drawn at the size of the painting's big shapes: head_raw scaled up about the neck."""
    c, k = NECK, HEAD_K
    bx, by = R(-62, 6)
    back = (c[0] + (bx - c[0]) * k, c[1] + (by - c[1]) * k)
    # the neck: the body's lumpy segments carried on up out of the dive, bottom first
    P = resample(bez(NECK, (NECK[0] + 8, NECK[1] - 40), (back[0] - 20, back[1] + 40), back, 20), 40)
    neck = []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        s = 0.5 + 0.05 * i / max(1, len(P) - 1)
        neck.append(it(lump(x, y, 62, 58, 600 + i, 0.1, 9, ang), [PINK, PINK2, ORA2][(i // 2) % 3], INK, (x, y), s, s + 0.06))
        nx, ny = math.cos(math.radians(ang + 90)), math.sin(math.radians(ang + 90))
        if nx < 0:
            nx, ny = -nx, -ny
        neck.append(it(lump(x + nx * 36, y + ny * 36, 29, 17, 650 + i, 0.15, 7, ang), BELLY, INK * 0.8, (x, y), s + 0.02, s + 0.07))
    return neck + scaled(head_raw(), c, k)


def preview(items, t) -> str:
    """Like ghost_endframes.sprite_svg (the app's easing), with the app's 'x' and 'y' growth too."""
    out = ''
    for q in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - q['start']) / (q['end'] - q['start'])))) ** 3
        if 'outStart' in q:
            u = max(0.0, min(1.0, (t - q['outStart']) / (q['outEnd'] - q['outStart'])))
            v *= 1 - (1 - (1 - u) ** 3)
        if v <= 0.01:
            continue
        x, y = q['at']
        sc = {'x': f'{v:.4f} 1', 'y': f'1 {v:.4f}'}.get(q['grow'], f'{v:.4f}')
        stroke = f' stroke="#000" stroke-width="{q["edge"]}" stroke-linejoin="round"' if q['edge'] > 0 else ''
        out += f'<path d="{q["d"]}" fill="{q["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def dragon_frame(t: float) -> Image.Image:
    im = m.compose()
    on = preview(body_items(), t)
    if on:  # "on": clipped to the sky, under the painting's ink
        im.alpha_composite(m.svg(f'<clipPath id="sky"><path d="{m.FILLS[SKY]}"/></clipPath><g clip-path="url(#sky)">{on}</g>'))
        im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in crop_ink()) + '</g>'))
    over = preview(head_items(), t)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def dragon_main() -> None:
    m.CROP, m.PX = DCROP, 1100
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = OUT.parent / 'sky-dragon'
    out.mkdir(parents=True, exist_ok=True)
    dragon_frame(1.0).save(out / 'end-frame.png')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    for frames, name, sc in [([0, 0.25, 0.5, 0.75, 1.0], 'strip.png', 0.4),
                             ([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 'steps.png', 0.26)]:
        tiles = [dragon_frame(t) for t in frames]
        w, h = tiles[0].size
        tw, th = int(w * sc), int(h * sc)
        cols = 5
        rows = (len(frames) + cols - 1) // cols
        strip = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 46) * rows + 10), 'white')
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 46)
            d.text((x, y), f'frame {tt:.2f}  ({-8 + 20 * tt:.0f} dB)', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
        strip.save(out / name)
    print('wrote', out)


def build() -> dict:
    return {
        'label': 'The sky round the top: it follows the output Volume (set by presets and MIDI); as it gets louder a '
                 'candy dragon loops along the top of the sky gap by gap, rears its head out between the stalk cap '
                 'and the cyan link, wakes, and roars wide at the loudest',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': body_items()},
            {'effect': 'sprites', 'place': 'over', 'items': head_items()},
        ],
    }


if __name__ == '__main__' and 'dragon' in __import__('sys').argv[1:]:
    dragon_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    b = build()
    (OUT.parent / 'build.json').write_text(_j.dumps(b, indent=2) + '\n')
    print('exported', sum(len(e['items']) for e in b['effects']), 'shapes to', OUT.parent / 'build.json')
