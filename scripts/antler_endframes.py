# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower 16' drawbar fully out) for the antler trunk: the pale lime column, centre, rising from the
red ground to the horizon line behind the coral antler hand, with the orange capsule poking up at its top.

    uv run scripts/antler_endframes.py
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
m.CROP = (2330, 2080, 1250, 1450)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db1/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
TRUNK = m.FILLS['f072']
LIME, PALE, CREAM = '#e4f59a', '#f4f7b8', '#fffbe6'
PINK, CYAN, YELLOW, VIOLET, ORANGE, MINT = '#ff8fc0', '#5fe3e0', '#ffe066', '#c4a3f0', '#ff9f43', '#8fe3a8'
# shapes that stay in front of anything drawn on or out of the trunk: the antler hand and its nails, the yellow
# tongue, the orange capsule at its top, the acorn creature to its left (not its little cyan wedge f167, which the
# risen trunk covers)
FRONT = ['f076', 'f086', 'f087', 'f092', 'f077', 'f078', 'f169', 'f083', 'f084']
TOP = (2905.0, 2880.0)  # the middle of the trunk's top, on the horizon line
PAINTED = m.compose()


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    """New shapes drawn over the painting, then the named painted shapes (fills and their own ink) put back on top
    exactly as painted. The fills here are translucent, so they are restored from the untouched painting through
    their mask rather than drawn a second time (which would darken them)."""
    im = m.compose(front=front or '<g/>')
    if again:
        ink = sorted({s for f in again for s in m.own_ink(f)})
        mask = m.svg('<g fill="#000">' + ''.join(f'<path d="{m.FILLS[f]}"/>' for f in again)
                     + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink) + '</g>').getchannel('A')
        im = Image.composite(PAINTED, im, mask)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def closed(pts) -> str:
    """A smooth closed path through pts (Catmull-Rom as cubic beziers)."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(cx, cy, rx, ry, seed, wob=0.08, n=11, rot=0.0) -> str:
    """A lumpy hand-drawn oval."""
    rnd = random.Random(seed)
    r0 = math.radians(rot)
    pts = []
    for k in range(n):
        a = k / n * 2 * math.pi
        f = 1 + wob * (rnd.random() * 2 - 1)
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r0) - y * math.sin(r0), cy + x * math.sin(r0) + y * math.cos(r0)))
    return closed(pts)


def puff(cx, cy, r, seed, bumps=7) -> str:
    """A scalloped cloud-like puff: bumps round the edge."""
    rnd = random.Random(seed)
    pts = []
    n = bumps * 4
    ph = rnd.random() * 6
    for k in range(n):
        a = k / n * 2 * math.pi
        f = 1 + 0.11 * math.cos(bumps * a + ph) + 0.04 * (rnd.random() - 0.5)
        pts.append((cx + math.cos(a) * r * f, cy + math.sin(a) * r * f * 0.88))
    return closed(pts)


def column(x0, x1, y_bot, y_top, seed, lean=0.0, top_round=True) -> str:
    """A lumpy upright column (trunk, neck, pipe) from y_bot up to y_top; open at the bottom (it starts inside the
    trunk), round or flat at the top."""
    rnd = random.Random(seed)
    n = 8
    L, R = [], []
    for i in range(n + 1):
        u = i / n
        y = y_bot + (y_top - y_bot) * u
        dx = lean * u * u
        L.append((x0 + dx + (rnd.random() - 0.5) * 10, y))
        R.append((x1 + dx + (rnd.random() - 0.5) * 10, y))
    w = (x1 - x0) / 2
    tx, ty = (L[-1][0] + R[-1][0]) / 2, y_top
    d = f'M{p(*L[0])}' + ''.join(f'L{p(*q)}' for q in L[1:])
    if top_round:
        d += f'C{p(L[-1][0], ty - w * 0.9)} {p(R[-1][0], ty - w * 0.9)} {p(*R[-1])}'
    else:
        d += f'L{p(*R[-1])}'
    d += ''.join(f'L{p(*q)}' for q in R[-2::-1])
    return d + 'Z'


def edged(d, colour, width=INK) -> str:
    """Outlined fill whose outline leaves the bottom open (it joins the trunk): fill the whole shape, then stroke
    only the sides and top (the path without its closing segment)."""
    return f'<path d="{d}" fill="{colour}"/><path d="{d[:-1]}" fill="none" stroke="#000" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def clip(cid: str, d: str, body: str) -> str:
    return f'<defs><clipPath id="{cid}"><path d="{d}"/></clipPath></defs><g clip-path="url(#{cid})">{body}</g>'


def trunk_recolour(colour: str, extra: str = '') -> str:
    """The trunk's own shape filled in a new colour (plus clipped extras), outlined again."""
    return f'<path d="{TRUNK}" fill="{colour}"/>' + (clip('trk', TRUNK, extra) if extra else '') + \
        f'<path d="{TRUNK}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'


# ---- 1. the trunk grows into a candy tree -------------------------------------------------------------------------
def v1_tree() -> Image.Image:
    """Candy tree: the trunk grows up through the horizon, forks into two boughs, and a big lumpy crown of candy
    foliage puffs comes out over them, with pink blossoms."""
    out = edged(column(2815, 2995, 2960, 2600, 1, lean=10, top_round=False), PALE)
    out += outlined(tube(bez((2850, 2650), (2800, 2580), (2740, 2540), (2700, 2470), 16), 48, 30), PALE, INK)
    out += outlined(tube(bez((2960, 2650), (3010, 2580), (3080, 2540), (3130, 2470), 16), 48, 30), PALE, INK)
    out += f'<path d="{blob(2905, 2640, 100, 60, 3)}" fill="{PALE}"/>'
    crown = [(2700, 2430, 150, MINT), (2905, 2330, 175, '#8fe36b'), (3120, 2420, 150, '#5cd6b8'), (2790, 2250, 130, '#c8f56b'),
             (3030, 2240, 135, MINT), (2600, 2330, 110, '#5cd6b8'), (3230, 2310, 110, '#8fe36b'), (2905, 2500, 120, '#c8f56b')]
    for k, (x, y, r, c) in enumerate(crown):
        out += outlined(puff(x, y, r, 10 + k), c, INK)
    for k, (x, y) in enumerate([(2760, 2330), (3000, 2400), (3160, 2290), (2880, 2190), (2640, 2420)]):
        out += outlined(puff(x, y, 48, 30 + k, 5), PINK, INK * 0.8) + outlined(circle(x, y, 17), YELLOW, INK * 0.6)
    return draw(out, FRONT)


# ---- 2. the trunk wakes and sings a deep note ---------------------------------------------------------------------
def wave_band(x0, y0, ang, length, amp, w, colour, seed) -> str:
    """A long slow wave of sound: an outlined ribbon along a sine, thick in the middle, thin at the ends."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    n = 40
    P = []
    for i in range(n + 1):
        u = i / n
        v = amp * math.sin(u * 2 * math.pi * 1.25)
        P.append((x0 + ca * u * length - sa * v, y0 + sa * u * length + ca * v))
    L, R = [], []
    for i, (x, y) in enumerate(P):
        q0, q1 = P[max(0, i - 1)], P[min(n, i + 1)]
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        t = w * (0.25 + 0.75 * math.sin(math.pi * i / n))
        L.append((x + nx * t, y + ny * t))
        R.append((x - nx * t, y - ny * t))
    return outlined('M' + 'L'.join(p(*q) for q in L + R[::-1]) + 'Z', colour, INK * 0.85)


def v2_singing() -> Image.Image:
    """Basso: the trunk swells up over the horizon into a big round head, opens two big eyes and a deep round mouth,
    and long slow waves of a low note roll out to both sides."""
    head = (f'M{p(2815, 2960)}C{p(2800, 2760)} {p(2760, 2620)} {p(2765, 2520)}C{p(2770, 2380)} {p(2840, 2330)} {p(2905, 2330)}'
            f'C{p(2975, 2330)} {p(3045, 2380)} {p(3045, 2520)}C{p(3045, 2620)} {p(3005, 2760)} {p(2995, 2960)}Z')
    out = wave_band(2720, 2540, 195, 330, 24, 30, YELLOW, 1) + wave_band(2715, 2650, 165, 300, 22, 26, PINK, 2)
    out += wave_band(3090, 2480, -15, 320, 24, 30, CYAN, 3)
    out += edged(head, PALE)
    for x, y in ((2850, 2450), (2965, 2445)):
        out += outlined(blob(x, y, 52, 60, int(x)), '#ffffff', INK)
        out += outlined(circle(x + 4, y + 14, 27), '#3a9fd8', INK * 0.7) + f'<path d="{circle(x + 4, y + 14, 13)}" fill="#000"/>'
        out += f'<path d="{circle(x + 13, y + 4, 7)}" fill="#fff"/>'
    out += outlined(blob(2905, 2575, 50, 62, 7, 0.06), '#7a1033', INK)
    out += f'<path d="{blob(2908, 2612, 32, 18, 8)}" fill="{PINK}"/>'
    return draw(out, FRONT)


# ---- 3. the trunk becomes the 16' organ pipe ----------------------------------------------------------------------
GOLD, GOLD_LT, GOLD_DK = '#ffcf3a', '#fff0a0', '#d99a1e'


def cloud(cx, cy, r, seed, colour=CREAM) -> str:
    """A lumpy puff of breath: round lobes round a middle, one outline, the middle filled over the joins."""
    rnd = random.Random(seed)
    out = ''
    for k in range(7):
        a = k / 7 * 2 * math.pi + rnd.random() * 0.3
        out += outlined(circle(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.45, r * (0.42 + rnd.random() * 0.1)), colour, INK)
    return out + f'<path d="{blob(cx, cy, r * 0.7, r * 0.55, seed)}" fill="{colour}"/>'


def v3_organ_pipe() -> Image.Image:
    """Sixteen-foot pipe: the trunk turns gold and rises far over the horizon as a giant organ pipe (the 16' is the
    longest, lowest pipe), its mouth opening above the horizon and a deep puff of breath rolling out."""
    shine = f'<path d="{blob(2850, 3150, 24, 330, 2, 0.04)}" fill="{GOLD_LT}"/>'
    out = trunk_recolour(GOLD, shine)
    body = column(2815, 2995, 2960, 2290, 4, top_round=False)
    out += edged(body, GOLD)
    out += f'<path d="{blob(2848, 2620, 20, 250, 5, 0.04)}" fill="{GOLD_LT}"/>'
    out += outlined(f'M{p(2808, 2340)}L{p(3002, 2340)}L{p(3000, 2385)}L{p(2810, 2385)}Z', PINK, INK)
    out += outlined(ellipse(2905, 2292, 98, 30), GOLD_DK, INK) + f'<path d="{ellipse(2905, 2296, 74, 18)}" fill="#3a2a10"/>'
    # the mouth: an arched upper lip over a dark slot, above the capsule
    out += outlined(f'M{p(2838, 2565)}C{p(2842, 2495)} {p(2880, 2460)} {p(2905, 2455)}C{p(2930, 2460)} {p(2968, 2495)} {p(2972, 2565)}Z', GOLD_DK, INK)
    out += outlined(blob(2905, 2580, 74, 22, 9, 0.05), '#2a1a08', INK)
    out += outlined(f'M{p(2832, 2598)}C{p(2870, 2610)} {p(2940, 2610)} {p(2978, 2598)}L{p(2972, 2640)}C{p(2940, 2650)} {p(2870, 2650)} {p(2838, 2640)}Z', GOLD, INK * 0.8)
    # breath rolling out of the mouth to the left
    out += cloud(2700, 2540, 120, 21) + cloud(2520, 2470, 85, 22)
    return draw(out, FRONT)


# ---- 4. the trunk turns out to be a giraffe's neck ----------------------------------------------------------------
def v4_giraffe() -> Image.Image:
    """Giraffe: orange patches come up on the trunk, it stretches up over the horizon as a long neck with a candy
    mane, and a friendly giraffe head with ossicones and a wide eye looks out over the hand."""
    spots = ''.join(outlined(blob(x, y, rx, ry, k, 0.18, 9), ORANGE, INK * 0.8)
                    for k, (x, y, rx, ry) in enumerate([(2860, 2990, 42, 50), (2965, 3080, 40, 46), (2950, 3260, 36, 48),
                                                        (2850, 3060, 30, 34), (2960, 3420, 38, 40)]))
    out = trunk_recolour(PALE, spots)
    neck = column(2815, 2995, 2960, 2470, 11, lean=60, top_round=False)
    # mane along the back of the neck
    for k in range(6):
        y = 2860 - k * 75
        out += outlined(blob(2790 + 60 * ((2905 - y) / 435) ** 2, y, 50, 44, 40 + k), PINK if k % 2 else VIOLET, INK * 0.85)
    out += edged(neck, PALE)
    for k, (x, y, rx, ry) in enumerate([(2900, 2800, 44, 50), (2955, 2680, 38, 44), (2880, 2610, 34, 40), (2990, 2540, 30, 36)]):
        out += outlined(blob(x, y, rx, ry, 60 + k, 0.18, 9), ORANGE, INK * 0.8)
    # head
    for x in (2925, 3010):
        out += outlined(tube([(x, 2380), (x - 12, 2250)], 18, 15), PALE, INK * 0.85) + outlined(circle(x - 12, 2238, 30), PINK, INK * 0.85)
    out += outlined(blob(2830, 2370, 70, 34, 70, 0.06, 9, rot=-25), PALE, INK)
    out += outlined(blob(3000, 2420, 170, 100, 71, 0.05, 12, rot=12), PALE, INK)
    out += outlined(blob(3135, 2470, 75, 65, 72, 0.05), '#ffc9a0', INK)
    out += f'<path d="{ellipse(3160, 2460, 10, 14)}" fill="#000"/>'
    out += outlined(blob(2965, 2385, 42, 46, 73), '#ffffff', INK * 0.9) + outlined(circle(2978, 2395, 22), '#6b3a1f', INK * 0.6)
    out += f'<path d="{circle(2986, 2386, 7)}" fill="#fff"/>'
    out += outlined(f'M{p(3080, 2520)}C{p(3110, 2545)} {p(3150, 2545)} {p(3175, 2515)}C{p(3150, 2530)} {p(3110, 2530)} {p(3080, 2520)}Z', '#7a1033', INK * 0.6)
    return draw(out, FRONT)


# ---- 5. the trunk dressed as a maypole ----------------------------------------------------------------------------
def v5_maypole() -> Image.Image:
    """Maypole: candy ribbons wind up the trunk, it rises over the horizon to a big flower, and broad ribbons fly
    out from under the flower, curling down both sides."""
    stripes = ''
    cols = [PINK, CYAN, YELLOW, VIOLET]
    for k in range(-6, 12):
        y = 2860 + k * 80
        stripes += outlined(f'M{p(2760, y)}L{p(3250, y - 170)}L{p(3250, y - 125)}L{p(2760, y + 45)}Z', cols[k % 4], INK * 0.8)
    out = trunk_recolour(CREAM, stripes)
    pole = column(2850, 2960, 2960, 2470, 12, top_round=False)
    out += edged(pole, CREAM) + clip('pole', pole, stripes) + f'<path d="{pole[:-1]}" fill="none" stroke="#000" stroke-width="{INK}"/>'
    rib = ''
    for k, (c1, c2, end, col) in enumerate([((2780, 2480), (2630, 2560), (2580, 2760), PINK), ((2760, 2520), (2700, 2650), (2720, 2800), YELLOW),
                                            ((3040, 2480), (3200, 2540), (3260, 2700), CYAN), ((3060, 2520), (3120, 2640), (3090, 2760), VIOLET)]):
        P = bez((2905, 2470), c1, c2, end, 24)
        rib += outlined(tube(P, 26, 34), col, INK * 0.85)
    out += rib
    for k in range(8):
        a = k / 8 * 2 * math.pi
        out += outlined(blob(2905 + math.cos(a) * 95, 2390 + math.sin(a) * 95, 70, 52, 80 + k, 0.08, 9, rot=math.degrees(a)), PINK if k % 2 else '#ff5ea8', INK)
    out += outlined(blob(2905, 2390, 72, 70, 90), YELLOW, INK)
    return draw(out, FRONT)


VERSIONS = [
    ('1-candy-tree', 'Candy tree', v1_tree),
    ('2-basso', 'Basso (sings low)', v2_singing),
    ('3-organ-pipe', "16' organ pipe", v3_organ_pipe),
    ('4-giraffe', 'Giraffe', v4_giraffe),
    ('5-maypole', 'Maypole', v5_maypole),
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


# ---- chosen: giraffe (4) ------------------------------------------------------------------------------------------
# The Lower 16' drawbar turns the trunk into a giraffe, one arrival per drawbar step (k/8):
#   1 the trunk pales and uneven orange patches swell on it; 2 the lower neck rises out of its top over the horizon;
#   3 the upper neck rises on it, leaning toward the hand; 4 patches come up on the neck; 5 a candy mane pops out
#   along its back; 6 the head swells at the top, sleepy-eyed; 7 two ossicones sprout; 8 the eye opens wide.
# Two sprite effects: patches and the pale hide go "on" the trunk (clipped to it, under the ink, the shapes painted
# after it in front); the neck and head go "around" (over the ink, so they cover the trunk's top edge where they rise
# out of it, masked so the capsule f169 and the hand, tongue and acorn creature stay in front). The around effect is
# restricted to the role "capsule" (f169, the orange capsule at the trunk's top) so the trunk itself does not mask
# the neck rising out of it.
STEP = 1 / 8
LID = '#FFE47F'
NECK_FRONT = ['f076', 'f086', 'f087', 'f092', 'f077', 'f078', 'f083', 'f084']
CAPSULE = 'f169'
N0, N1, N2, N3 = (2905.0, 2955.0), (2900.0, 2740.0), (2925.0, 2600.0), (2972.0, 2470.0)  # the neck's centreline


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 4), 'end': round(e, 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    return x


def lumpy_tube(P, w0, w1, seed, jit=0.06, cap=True) -> str:
    """A tapered outlined limb along P whose width wobbles a little, like the painting's hand-drawn forms."""
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
        L.append((x + nx * w * (1 + jit * math.sin(u * 9 + ph1)), y + ny * w * (1 + jit * math.sin(u * 9 + ph1))))
        R.append((x - nx * w * (1 + jit * math.sin(u * 7 + ph2)), y - ny * w * (1 + jit * math.sin(u * 7 + ph2))))
    rr = (math.hypot(L[-1][0] - R[-1][0], L[-1][1] - R[-1][1])) / 2
    end = f'A{rr:.1f} {rr * 1.1:.1f} 0 0 1 {p(*R[-1])}' if cap else f'L{p(*R[-1])}'
    return 'M' + 'L'.join(p(*q) for q in L) + end + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def patch(x, y, r, seed) -> str:
    """An uneven giraffe patch: a lumpy, lopsided blob with a few flat-ish sides."""
    rnd = random.Random(seed)
    n = 7
    pts = []
    for k in range(n):
        a = (k + rnd.random() * 0.5) / n * 2 * math.pi
        f = 0.7 + rnd.random() * 0.5
        pts.append((x + math.cos(a) * r * f * 1.1, y + math.sin(a) * r * f * 0.9))
    return closed(pts)


def neck_line(u0, u1, n=16):
    P = bez(N0, N1, N2, N3, 60)
    return P[round(u0 * 60):round(u1 * 60) + 1][:: max(1, round((u1 - u0) * 60 / n))]


def neck_width(u):
    return 98 - 36 * u


def on_items() -> list[dict]:
    """Step 1, on the trunk: its pale hide rises from the bottom, then uneven patches swell on it."""
    items = [it(TRUNK, PALE, 0, (2905, 3515), 0.0, 0.09, 'y')]
    spots = [(2852, 3030, 44), (2958, 3085, 46), (2950, 3255, 44), (2962, 3425, 46), (2862, 3112, 30)]
    for k, (x, y, r) in enumerate(spots):
        s = 0.03 + 0.012 * k
        items.append(it(patch(x, y, r, 100 + k), ORANGE, INK * 0.8, (x, y), s, min(STEP, s + 0.06)))
    return items


def neck_items() -> list[dict]:
    items = []
    # step 5 (drawn first so the neck covers its roots): the mane pops out along the back of the neck
    P = bez(N0, N1, N2, N3, 60)
    for k, u in enumerate((0.44, 0.54, 0.64, 0.74, 0.84, 0.94)):
        x, y = P[round(u * 60)]
        w = neck_width(u)
        mx, my = x - w * 1.18, y + 4
        s = 4 * STEP + 0.016 * k
        items.append(it(blob(mx, my, 58 - 14 * u, 50 - 10 * u, 200 + k, 0.12, 8), PINK if k % 2 else VIOLET, INK * 0.85, (x - w * 0.5, y), s, min(5 * STEP, s + 0.05)))
    # steps 2 and 3: the neck rises in two sections, outlined layers first, then fill-only layers that melt the join
    lo, hi = neck_line(0.0, 0.58), neck_line(0.5, 1.0)
    lo_w, hi_w = (neck_width(0), neck_width(0.58)), (neck_width(0.5), neck_width(1.0))
    low_ext = [(N0[0], N0[1] + 22)] + lo  # the fill-only layer reaches further down, over the outline's open end
    items.append(it(lumpy_tube(lo, *lo_w, 301), PALE, INK, N0, STEP, 2 * STEP, 'y'))
    items.append(it(lumpy_tube(hi, *hi_w, 302), PALE, INK, hi[0], 2 * STEP, 3 * STEP, 'y'))
    items.append(it(lumpy_tube(low_ext, lo_w[0] - INK / 2, lo_w[1] - INK / 2, 301), PALE, 0, N0, STEP, 2 * STEP, 'y'))
    items.append(it(lumpy_tube(hi, hi_w[0] - INK / 2, hi_w[1] - INK / 2, 302, cap=False), PALE, 0, hi[0], 2 * STEP, 3 * STEP, 'y'))
    # step 4: patches on the neck, bottom to top
    for k, (u, side, r) in enumerate([(0.12, -0.45, 40), (0.36, 0.2, 46), (0.55, -0.35, 40), (0.68, 0.4, 36), (0.82, -0.2, 38), (0.95, 0.35, 28)]):
        x, y = P[round(u * 60)]
        x += side * neck_width(u)
        s = 3 * STEP + 0.014 * k
        items.append(it(patch(x, y, r, 400 + k), ORANGE, INK * 0.8, (x, y), s, min(4 * STEP, s + 0.05)))
    return items


HEAD_AT = (2985.0, 2440.0)
EYE = (2990.0, 2370.0, 40.0, 54.0)  # cx, cy, rx, ry: a tall oval, like the painting's eyes


def head_items() -> list[dict]:
    s6, e6 = 5 * STEP, 6 * STEP
    items = []
    # step 7, drawn first so the head covers their roots: two ossicones sprout from the crown
    for k, (bx, by, tx, ty) in enumerate([(2925, 2300, 2900, 2200), (3000, 2290, 2995, 2185)]):
        s = 6 * STEP + 0.02 * k
        e = min(7 * STEP, s + 0.08)
        items.append(it(lumpy_tube(bez((bx, by + 30), (bx, by - 20), (tx + 4, ty + 30), (tx, ty), 10), 24, 18, 500 + k), PALE, INK * 0.9, (bx, by + 30), s, e))
        items.append(it(blob(tx, ty - 8, 34, 30, 510 + k, 0.1, 8), PINK, INK * 0.9, (bx, by + 30), s, e))
    # step 6: the ear, then the head with its muzzle, nostril and smile
    ear = closed([(2880, 2345), (2830, 2300), (2760, 2268), (2745, 2300), (2790, 2350), (2860, 2385)])
    items.append(it(ear, PALE, INK, HEAD_AT, s6, s6 + 0.09))
    items.append(it(closed([(2865, 2335), (2815, 2305), (2785, 2300), (2805, 2330), (2850, 2362)]), PINK, INK * 0.6, HEAD_AT, s6, s6 + 0.09))
    head = closed([(2862, 2400), (2872, 2328), (2930, 2282), (3010, 2275), (3080, 2318), (3150, 2372), (3205, 2420), (3200, 2488),
                   (3138, 2522), (3050, 2510), (2985, 2502), (2920, 2486), (2872, 2452)])
    items.append(it(head, PALE, INK * 1.05, HEAD_AT, s6, s6 + 0.09))
    muzzle = closed([(3110, 2365), (3165, 2385), (3208, 2425), (3203, 2488), (3140, 2520), (3092, 2500), (3080, 2440)])
    items.append(it(muzzle, '#ffc9a0', INK * 0.9, HEAD_AT, s6 + 0.01, s6 + 0.1))
    items.append(it(blob(3168, 2432, 13, 18, 520, 0.12, 7), '#3a1a10', 0, HEAD_AT, s6 + 0.01, s6 + 0.1))
    items.append(it(f'M{p(3092, 2478)}C{p(3120, 2500)} {p(3160, 2502)} {p(3185, 2478)}C{p(3160, 2492)} {p(3120, 2492)} {p(3092, 2478)}Z', '#000', 6, HEAD_AT, s6 + 0.01, s6 + 0.1))
    for k, (x, y, r) in enumerate([(2918, 2440, 34), (3062, 2462, 30)]):
        items.append(it(patch(x, y, r, 530 + k), ORANGE, INK * 0.7, HEAD_AT, s6 + 0.02, s6 + 0.1))
    # the eye: arrives sleepy at the end of step 6, opens at step 8
    ex, ey, rx, ry = EYE
    es, ee = s6 + 0.055, e6
    items.append(it(blob(ex, ey, rx, ry, 540, 0.05, 10), '#fffbe6', INK * 1.15, (ex, ey), es, ee))
    items.append(it(blob(ex + 8, ey + 16, 22, 30, 541, 0.05, 9), '#3fb8e8', INK * 0.8, (ex, ey), es, ee))
    items.append(it(ellipse(ex + 10, ey + 18, 10, 15), '#000', 0, (ex, ey), es, ee))
    items.append(it(circle(ex + 2, ey + 4, 7), '#fff', 0, (ex + 2, ey + 4), 7 * STEP + 0.04, 1.0))
    top = (ex, ey - ry - 12)
    lid = (f'M{p(ex - rx - 8, ey + 8)}C{p(ex - rx - 8, ey - ry * 1.45)} {p(ex + rx + 8, ey - ry * 1.45)} {p(ex + rx + 8, ey + 8)}'
           f'C{p(ex + rx * 0.4, ey + 22)} {p(ex - rx * 0.4, ey + 22)} {p(ex - rx - 8, ey + 8)}Z')
    opens = (7 * STEP, 1.0)
    items.append(it(lid, LID, INK * 1.15, top, es, ee, 'y', opens))
    # the lid line runs on past the eye in a long tapered flick, the painting's way
    flick = (f'M{p(ex - rx - 4, ey + 2)}C{p(ex - rx - 30, ey - 2)} {p(ex - rx - 55, ey - 14)} {p(ex - rx - 72, ey - 30)}'
             f'C{p(ex - rx - 52, ey - 4)} {p(ex - rx - 28, ey + 12)} {p(ex - rx - 2, ey + 14)}Z')
    items.append(it(flick, '#000', 0, top, es, ee, 'y', opens))
    return items


def around_items() -> list[dict]:
    return neck_items() + head_items()


def svg_items(items, t) -> str:
    """The app's drawSprites: each item eased (cubic out) through its window, shrinking away through its out window,
    grown by scale, x or y about `at`."""
    ease = lambda u: 1 - (1 - max(0.0, min(1.0, u))) ** 3
    out = ''
    for x in items:
        v = ease((t - x['start']) / max(1e-6, x['end'] - x['start']))
        if 'outStart' in x:
            v *= 1 - ease((t - x['outStart']) / max(1e-6, x['outEnd'] - x['outStart']))
        if v <= 0.01:
            continue
        ax, ay = x['at']
        sc = f'{v:.4f} 1' if x['grow'] == 'x' else f'1 {v:.4f}' if x['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{x["edge"]}" stroke-linejoin="round"' if x['edge'] > 0 else ''
        out += f'<path d="{x["d"]}" fill="{x["fill"]}"{stroke} transform="translate({ax} {ay}) scale({sc}) translate({-ax} {-ay})"/>'
    return out


def giraffe_frame(t: float) -> Image.Image:
    """As the app draws it: the on-layer right after the trunk in the fills (clipped to it), the around-layer over the
    ink, with the capsule and the front shapes (and a 44 px band round them, for their outlines) left as they were."""
    on = svg_items(on_items(), t)
    tags = m.FILL_TAGS
    if on:
        layer = f'<defs><clipPath id="onTrunk"><path d="{TRUNK}"/></clipPath></defs><g clip-path="url(#onTrunk)">{on}</g>'
        m.FILL_TAGS = [tg + layer if 'id="f072"' in tg else tg for tg in tags]
    try:
        base = m.compose()
    finally:
        m.FILL_TAGS = tags
    ar = svg_items(around_items(), t)
    if not ar:
        return base
    im = base.copy()
    im.alpha_composite(m.svg(ar))
    keep = ''.join(f'<path d="{m.FILLS[f]}" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in [CAPSULE] + NECK_FRONT)
    mask = m.svg(f'<g fill="#000">{keep}</g>').getchannel('A')
    return Image.composite(base, im, mask)


def giraffe_main() -> None:
    out = OUT.parent / 'giraffe'
    out.mkdir(parents=True, exist_ok=True)
    giraffe_frame(1.0).save(out / 'end-frame.png')
    for frames, name, sc in [([0, 0.25, 0.5, 0.75, 1.0], 'strip.png', 0.42), ([k / 8 for k in range(9)], 'steps.png', 0.3)]:
        tiles = [giraffe_frame(t) for t in frames]
        w, h = tiles[0].size
        tw, th = int(w * sc), int(h * sc)
        strip = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        try:
            font = ImageFont.load_default(size=24)
        except TypeError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}' if name == 'steps.png' else f'frame {tt:.2f}', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        strip.save(out / name)
    print('wrote', out)


if __name__ == '__main__' and 'giraffe' in __import__('sys').argv[1:]:
    giraffe_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The pink trunk with antlers: drag for the Lower 16' drawbar; it turns into a giraffe, its neck rising "
                 'over the horizon step by step until a sleepy head looks out and opens its eye',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'parts': ['body'], 'items': on_items()},
            {'effect': 'sprites', 'place': 'around', 'parts': ['capsule'], 'front': NECK_FRONT, 'items': around_items()},
        ],
        'objectParts': {'capsule': [CAPSULE]},
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(on_items()) + len(around_items()), 'shapes')
