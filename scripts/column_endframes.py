# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Upper 4' drawbar fully out) for the pink column: the tall gap of pale cream sky (f305) between
the middle green stalk and the right one, under the big mushroom cap, its wash showing peach and orange bands, the
yellow spike poking up into it from below.

    uv run scripts/column_endframes.py

New shapes live in the gap: they are drawn, then masked out wherever the stalks, cap, buds, spike and arch are (and
those shapes' ink laid back on top), so they sit behind the painted things round the column. Anything that should come
out in front goes in `over`.
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (1180, 430, 1160, 1260)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/upper-db4/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 13
CX = 1760.0  # the column's middle
# The painted shapes round the column that stay in front of anything living in it: the middle stalk and its cap
# (f262), the right stalk (f263, f264), the green cap top (f268), the little buds on the stalks, the purple blob under
# the cap (f284, f286), the yellow spike (f229, f230), the pale arch (f249) and the pink haze at lower right (f228).
FRONT = ['f262', 'f263', 'f264', 'f268', 'f269', 'f270', 'f271', 'f273', 'f274', 'f284', 'f286', 'f229', 'f230',
         'f249', 'f228']
PINK, PINK2, PALE_PINK, MAGENTA = '#ff9fc4', '#f64c76', '#ffd0e4', '#ff5ced'
GOO, GOO_HI = '#ff6fc8', '#ffc4ec'
MINT, LEMON, LAV, CREAM, ORANGE = '#7fe0c8', '#ffe066', '#c4a3f0', '#fffbe6', '#ff9f43'


def draw(behind: str = '', over: str = '') -> Image.Image:
    im = m.compose()
    if behind:
        art = m.svg(behind)
        mask = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#000"/>' for f in FRONT)).getchannel('A')
        art.putalpha(ImageChops.multiply(art.getchannel('A'), ImageChops.invert(mask)))
        im.alpha_composite(art)
        ink = sorted({s for f in FRONT for s in m.own_ink(f)})
        im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink) + '</g>'))
    if over:
        im.alpha_composite(m.svg(over))
    return im


# ---- hand-drawn shapes ----------------------------------------------------------------------------------------------
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


def lump(x, y, rx, ry=None, seed=0, wob=0.07, n=10, rot=0.0) -> str:
    """A lumpy, hand-drawn round shape."""
    ry = ry or rx
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * math.cos(rot) - v * math.sin(rot), y + u * math.sin(rot) + v * math.cos(rot)))
    return smooth(P)


def wobbly(P, amt, seed) -> list:
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * 2 * amt, y + (rnd.random() - 0.5) * 2 * amt) for x, y in P]


def box(x0, y0, x1, y1, r, seed, amt=5, n=6) -> list:
    """Points round a rounded rectangle, a little wobbly, for smooth()."""
    P = []
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    for cx, cy, a0 in corners:
        for k in range(n):
            a = math.radians(a0 + 90 * k / (n - 1))
            P.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return wobbly(P, amt, seed)


def eye(x, y, r, look=(0.0, 0.15), lid=None) -> str:
    out = outlined(lump(x, y, r, seed=int(x + y), wob=0.05), '#ffffff', INK)
    px, py = x + look[0] * r, y + look[1] * r
    out += f'<path d="{circle(px, py, r * 0.46)}" fill="#000"/>'
    out += f'<path d="{circle(px + r * 0.16, py - r * 0.18, r * 0.14)}" fill="#fff"/>'
    return out


def smile(x, y, w, h, fill='#7a1838') -> str:
    d = f'M{p(x - w, y)}C{p(x - w * 0.6, y + h * 0.2)} {p(x + w * 0.6, y + h * 0.2)} {p(x + w, y)}C{p(x + w * 0.7, y + h * 1.3)} {p(x - w * 0.7, y + h * 1.3)} {p(x - w, y)}Z'
    return outlined(d, fill, INK)


# ---- the five ------------------------------------------------------------------------------------------------------
def v1_caterpillar() -> Image.Image:
    """Caterpillar: the column fills with a tall pink caterpillar standing up between the stalks, one fat segment on
    another from the bottom up, its round head under the cap with big eyes and two antennae curling out over the
    stalks."""
    out = ''
    segs = [(1772, 1250, 128), (1756, 1140, 122), (1772, 1032, 116), (1758, 928, 110)]
    for k, (x, y, r) in enumerate(segs):
        out += outlined(lump(x, y, r, r * 0.62, seed=k + 3, wob=0.06, n=11), [PINK, PALE_PINK][k % 2], INK)
        out += outlined(lump(x - r * 0.42, y - r * 0.12, r * 0.2, r * 0.13, seed=k + 20), [MAGENTA, PINK][k % 2], INK * 0.8)
        out += outlined(lump(x + r * 0.45, y + r * 0.05, r * 0.16, r * 0.11, seed=k + 30), [MAGENTA, PINK][k % 2], INK * 0.8)
    hx, hy = 1768.0, 812.0
    over = ''
    for side in (-1, 1):  # antennae: outlined tubes curling out sideways, candy balls on the ends
        P = bez((hx + side * 40, hy - 60), (hx + side * 80, hy - 150), (hx + side * 170, hy - 170), (hx + side * 210, hy - 110), 18)
        over += outlined(tube(P, 15, 11), PINK, INK * 0.9)
        over += outlined(lump(P[-1][0], P[-1][1] + 10, 38, seed=side + 50), LEMON, INK * 0.9)
    over += outlined(lump(hx, hy, 118, 98, seed=7, wob=0.05, n=11), PINK, INK)
    over += eye(hx - 46, hy - 18, 40, (0.1, 0.2)) + eye(hx + 46, hy - 18, 40, (-0.1, 0.2))
    over += smile(hx, hy + 38, 42, 34)
    over += outlined(lump(hx - 86, hy + 28, 20, 13, seed=61), MAGENTA, 0.1) + outlined(lump(hx + 86, hy + 28, 20, 13, seed=62), MAGENTA, 0.1)
    return draw(out, over)


def v2_organ_pipe() -> Image.Image:
    """Singing organ pipe: the column turns into a big pink 4-foot organ pipe standing between the stalks; its pipe
    mouth opens as a real singing mouth, two happy eyes above it, and fat sound rings puff out of it either side."""
    body = smooth(box(1648, 690, 1884, 1210, 34, 2, 8, 7))
    foot = smooth(wobbly([(1660, 1170), (1872, 1170), (1812, 1340), (1720, 1340)], 6, 5))
    out = outlined(foot, PINK, INK) + outlined(body, PINK, INK)
    out += f'<path d="{smooth(box(1660, 1150, 1872, 1220, 20, 3, 3))}" fill="{PINK}"/>'  # melts the foot's join
    out += f'<path d="{lump(1700, 960, 24, 230, seed=12, wob=0.05)}" fill="{PALE_PINK}"/>'  # shine down one side
    out += outlined(smooth(box(1640, 840, 1892, 892, 20, 7, 5)), LEMON, INK)  # a band near the top
    mx, my = 1768.0, 1085.0
    out += outlined(lump(mx, my + 4, 62, 72, seed=8, wob=0.04, n=9), '#7a1838', INK)  # a round singing mouth
    out += outlined(lump(mx + 2, my + 40, 38, 24, seed=9), '#ff6f91', INK * 0.8)
    out += outlined(lump(mx, my + 74, 82, 22, seed=11, wob=0.04, n=12), PALE_PINK, INK)  # the pipe's lower lip
    for side in (-1, 1):  # happy singing eyes: closed, curved up
        x, y = mx + side * 52, 955.0
        d = f'M{p(x - 36, y + 10)}C{p(x - 20, y - 28)} {p(x + 20, y - 28)} {p(x + 36, y + 10)}C{p(x + 18, y - 6)} {p(x - 18, y - 6)} {p(x - 36, y + 10)}Z'
        out += outlined(d, '#000', INK * 0.6)
        out += f'<path d="{lump(x + side * 6, y + 44, 22, 13, seed=int(x))}" fill="{MAGENTA}"/>'
    over = ''
    for side in (-1, 1):  # fat sound rings puffing out either side of the mouth, in front of the stalks
        for k, r in enumerate((180, 270)):
            a0, a1 = (-0.62, 0.62) if side > 0 else (math.pi - 0.62, math.pi + 0.62)
            P = []
            for i in range(19):
                a = a0 + (a1 - a0) * i / 18
                rr = r * (1 + 0.04 * (i / 18 - 0.5) * side)
                P.append((mx + math.cos(a) * rr, my - 20 + math.sin(a) * rr * 1.15))
            over += outlined(tube(P, 24 - k * 4, 18 - k * 4), [LEMON, MINT][k], INK)
    return draw(out, over)


def v3_spider() -> Image.Image:
    """Spider: a round fuzzy lavender spider lowers itself from under the cap on a fat silk rope, big eyes and a grin,
    four bent legs a side gripping the stalks, one leg up and waving."""
    bx, by, r = 1764.0, 1050.0, 125.0
    behind = outlined(tube([(bx, 690), (bx + 4, 820), (bx, by - r + 20)], 16, 16), CREAM, INK)
    over = ''
    legs = []
    for side in (-1, 1):
        for k, (a, L) in enumerate([(-35, 200), (-8, 215), (20, 210), (48, 190)]):
            ang = math.radians(a) if side > 0 else math.radians(180 - a)
            sx, sy = bx + math.cos(ang) * r * 0.7, by + math.sin(ang) * r * 0.7
            kx, ky = bx + math.cos(ang) * (r + L * 0.55), by + math.sin(ang) * (r + L * 0.55) - 70
            ex, ey = bx + math.cos(ang) * (r + L), by + math.sin(ang) * (r + L) + 40
            if side > 0 and k == 0:  # the waving leg, raised high
                kx, ky, ex, ey = bx + 190, by - 150, bx + 230, by - 290
            legs.append(bez((sx, sy), (kx - side * 40, ky), (kx + side * 10, ky - 10), (ex, ey), 16))
    for k, P in enumerate(legs):
        over += outlined(tube(P, 27, 22), '#9d72d6', INK)
        over += outlined(lump(P[-1][0], P[-1][1], 32, 30, seed=k + 100), '#9d72d6', INK)  # a round foot
    over += outlined(lump(bx, by, r, r * 0.95, seed=4, wob=0.04, n=13), LAV, INK)
    over += outlined(lump(bx - 40, by - 54, 30, 18, seed=5), '#e3d4fb', 0.1)
    over += eye(bx - 46, by - 18, 40, (0.15, 0.25)) + eye(bx + 46, by - 18, 40, (-0.05, 0.25))
    over += smile(bx, by + 46, 46, 34)
    ex, ey = legs[4][-1]
    for k in range(3):  # motion crescents round the waving foot
        a = math.radians(-175 + k * 55)
        P = [(ex + math.cos(a + 0.6 * i / 10) * 105, ey + math.sin(a + 0.6 * i / 10) * 105) for i in range(11)]
        over += outlined(tube(P, 19, 15), CREAM, INK)
    return draw(behind, over)


def v4_cake() -> Image.Image:
    """Party cake: tier on tier of candy birthday cake stacks up the column, standing out in front of the stalks, each
    tier with dripping frosting and cherries, and three candles burning on top just under the cap."""
    out = ''
    tiers = [(1200, 1335, 178, PINK), (1075, 1200, 150, MINT), (965, 1075, 122, LAV), (870, 965, 96, LEMON)]
    for k, (y0, y1, hw, col) in enumerate(tiers):
        out += outlined(smooth(box(CX - hw, y0, CX + hw, y1, 22, k + 1, 6)), col, INK)
        # frosting: a cream band along the top with round drips hanging off it
        P = [(CX - hw - 8, y0 - 10), (CX + hw + 8, y0 - 10)]
        n = 4 if k < 2 else 3
        for j in range(n, -1, -1):
            x = CX - hw + (2 * hw) * j / n
            L = [40, 64, 34, 56, 46][(j + k) % 5]
            P += [(x + 13, y0 + 26), (x, y0 + 26 + L), (x - 13, y0 + 26)]
        out += outlined(smooth(wobbly(P, 3, k + 9)), CREAM, INK)
        for j in range(2 if k < 3 else 1):  # cherries on each tier's face
            x = CX + (hw * 0.5 * (2 * j - 1) if k < 3 else 0)
            out += outlined(lump(x, y1 - 30, 24, seed=k * 3 + j), PINK2, INK)
    for j, x in enumerate((CX - 56, CX, CX + 56)):
        y0 = 875 - [120, 155, 120][j]
        out += outlined(smooth(box(x - 19, y0, x + 19, 885, 10, j + 40, 3, 4)), ['#ffffff', PALE_PINK, '#ffffff'][j], INK)
        out += f'<path d="{smooth(wobbly([(x - 19, y0 + 40), (x + 19, y0 + 20), (x + 19, y0 + 46), (x - 19, y0 + 66)], 2, j))}" fill="{[PINK2, MINT, PINK2][j]}"/>'
        fy = y0 - 8
        flame = f'M{p(x, fy - 100)}C{p(x + 14, fy - 64)} {p(x + 40, fy - 38)} {p(x + 35, fy - 12)}C{p(x + 30, fy + 16)} {p(x - 30, fy + 16)} {p(x - 35, fy - 12)}C{p(x - 38, fy - 42)} {p(x - 12, fy - 64)} {p(x, fy - 100)}Z'
        out += outlined(flame, ORANGE, INK)
        out += f'<path d="{lump(x, fy - 20, 14, 24, seed=j)}" fill="{LEMON}"/>'
    return draw('', out)


DRIPS = [(1600, 230, 42, 0.5), (1712, 400, 50, -0.6), (1826, 540, 56, 0.8), (1930, 190, 38, -0.4)]  # x, length, half-width, bend


def cap_edge(x: float) -> float:
    """The y of the mushroom cap's lower rim at x (the cap is roughly an ellipse round (1676, 568))."""
    return 568 + 139 * math.sqrt(max(0.0, 1 - ((x - 1676) / 393) ** 2))


def drip_line(x, L, w, bend) -> list:
    y = cap_edge(x) - 10
    return bez((x, y), (x + bend * 40, y + L * 0.35), (x - bend * 50, y + L * 0.7), (x + bend * 15, y + L), 18)


def v5_drips() -> Image.Image:
    """Dripping cap: thick pink goo oozes over the rim of the mushroom cap and runs down in front of the column in
    four fat drips of different lengths, bulbs at their ends, a big drop falling free below the longest."""
    top, bot = [], []
    for i in range(31):  # a wavy band of goo hugging the cap's lower rim
        x = 1540 + 460 * i / 30
        top.append((x, cap_edge(x) - 34 + 5 * math.sin(i * 1.7)))
        bot.append((x, cap_edge(x) + 22 + 10 * math.sin(i * 1.1 + 1)))
    rim = smooth(top + bot[::-1])
    shapes = [rim]
    for k, (x, L, w, bend) in enumerate(DRIPS):
        P = drip_line(x, L, w, bend)
        shapes.append(tube(P, w, w * 0.62))
        shapes.append(lump(P[-1][0], P[-1][1] + w * 0.45, w * 1.2, w * 1.32, seed=k + 70, wob=0.04))
    out = ''.join(outlined(d, GOO, INK) for d in shapes)  # outlined layer
    out += f'<path d="{rim}" fill="{GOO}"/>'
    for k, (x, L, w, bend) in enumerate(DRIPS):  # fill-only layer: melts the drips into the rim and their bulbs
        P = drip_line(x, L, w, bend)
        out += f'<path d="{tube(P, w - INK / 2, w * 0.62 - INK / 2)}" fill="{GOO}"/>'
        bx, by = P[-1]
        out += f'<path d="{lump(bx - w * 0.42, by + w * 0.25, w * 0.28, w * 0.45, seed=k + 80)}" fill="{GOO_HI}"/>'
    out += outlined(lump(1836, 1395, 48, 58, seed=90, wob=0.04), GOO, INK)
    out += f'<path d="{lump(1820, 1378, 14, 22, seed=91)}" fill="{GOO_HI}"/>'
    out += f'<path d="{lump(1640, cap_edge(1640) - 12, 64, 10, seed=92)}" fill="{GOO_HI}"/>'
    return draw('', out)


VERSIONS = [
    ('1-caterpillar', 'Caterpillar', v1_caterpillar),
    ('2-singing-pipe', 'Singing organ pipe', v2_organ_pipe),
    ('3-spider', 'Waving spider', v3_spider),
    ('4-party-cake', 'Party cake', v4_cake),
    ('5-dripping-cap', 'Dripping cap', v5_drips),
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


# ---- chosen: the caterpillar ----------------------------------------------------------------------------------------
# Picked: 1 on its own, drawn more the painting's way (lumpier segments of uneven size, irregular blob spots, heavy-lined
# almond eyes, a plain small mouth). One thing per drawbar step, each landing on k/8: five fat segments climb the gap
# from the bottom up (steps 1-5), the head arrives with sleepy half-lidded eyes (6), the lids lift and the eyes open
# wide (7), the antennae curl out over the stalks (8). The body is drawn "on" the column (clipped to f305, under the
# painting's ink) so the stalks, cap, buds and spike stay in front; the head and antennae go "over" everything.
CORAL_PINK, SPOT1, SPOT2, MOUTH = '#ff86b0', '#c86bd8', '#ff5ced', '#7a1838'
SEGS = [  # x, y, rx, ry, tilt (rad), fill
    (1770, 1262, 138, 80, 0.06, PINK),
    (1750, 1152, 116, 64, -0.08, PALE_PINK),
    (1776, 1054, 130, 68, 0.05, CORAL_PINK),
    (1752, 958, 108, 56, -0.1, PALE_PINK),
    (1770, 880, 100, 52, 0.08, PINK),
]
HEAD = (1766.0, 766.0, 128.0, 100.0)
EYES = [(1710.0, 750.0, -0.14), (1824.0, 744.0, 0.12)]  # x, y, tilt


def step(k: int, a: float = 0.08, b: float = 1.0) -> tuple[float, float]:
    """The window of drawbar step k (1..8), from fraction a to b of it: arrivals land on k/8."""
    return ((k - 1 + a) / 8, (k - 1 + b) / 8)


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 4),
         'end': round(min(1.0, e), 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    return x


def almond(cx, cy, w, h, tilt, upper=1.0, lower=0.75, n=24) -> list:
    """Points round an almond-shaped eye white: pointed corners, fuller on top."""
    top = [(-w * math.cos(math.pi * i / n), -h * upper * math.sin(math.pi * i / n) ** 0.85) for i in range(n + 1)]
    bot = [(w * math.cos(math.pi * i / n), h * lower * math.sin(math.pi * i / n) ** 0.85) for i in range(1, n)]
    c, s = math.cos(tilt), math.sin(tilt)
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in top + bot]


def lid_path(cx, cy, w, h, tilt, n=24) -> str:
    """The sleepy lid: the eye's upper part down to a slightly sagging line just below the middle."""
    top = [(-w * math.cos(math.pi * i / n), -h * math.sin(math.pi * i / n) ** 0.85) for i in range(n + 1)]
    line = [(w * math.cos(math.pi * i / n), h * 0.18 * math.sin(math.pi * i / n)) for i in range(1, n)]
    c, s = math.cos(tilt), math.sin(tilt)
    pts = [(cx + u * c - v * s, cy + u * s + v * c) for u, v in top + line]
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def body_items() -> list[dict]:
    """Steps 1-5: the segments and their spots, bottom first (each grows up out of the one below)."""
    items = []
    spots = [[(-0.42, -0.12, 0.22, 0.24), (0.34, 0.14, 0.17, 0.2)], [(0.36, -0.12, 0.2, 0.26)],
             [(-0.4, 0.0, 0.19, 0.27), (0.3, -0.16, 0.14, 0.2)], [(-0.28, -0.1, 0.2, 0.26)], [(0.36, 0.0, 0.19, 0.25)]]
    for k, (x, y, rx, ry, tilt, col) in enumerate(SEGS):
        s, e = step(k + 1, 0.06)
        at = (x, y + ry * 0.9)
        items.append(it(lump(x, y, rx, ry, seed=k * 7 + 1, wob=0.08, n=9, rot=tilt), col, INK, at, s, e))
        for j, (u, v, a, b) in enumerate(spots[k]):
            sx, sy = x + u * rx, y + v * ry * 1.6
            items.append(it(lump(sx, sy, a * rx * 1.3, b * ry * 1.7, seed=k * 11 + j, wob=0.22, n=7, rot=tilt + j),
                            [SPOT1, SPOT2][(k + j) % 2], INK * 0.8, (sx, sy), s + 0.04, e))
    return items


def antenna(side: int) -> list:
    hx, hy, rx, ry = HEAD
    x0, y0 = hx + side * 38, hy - ry * 0.7
    P = bez((x0, y0), (x0 + side * 15, y0 - 100), (x0 + side * 95, y0 - 170), (x0 + side * 175, y0 - 150), 16)
    a = math.atan2(P[-1][1] - P[-2][1], P[-1][0] - P[-2][0])
    curl = g.spiral(P[-1][0], P[-1][1], a, 48, 0.85, 0.55, 1 if side > 0 else -1, 20)
    return P + curl[1:]


def head_items() -> list[dict]:
    """Steps 6-8, over everything: antennae (drawn first so their roots tuck under the head), the head, its eyes with
    sleepy lids that lift away on step 7, and a small plain mouth."""
    hx, hy, rx, ry = HEAD
    items = []
    s8, e8 = step(8, 0.1)
    for side in (-1, 1):
        P = antenna(side)
        items.append(it(tube(P, 16, 11), PINK, INK, P[0], s8, e8))
    s6, e6 = step(6, 0.06)
    items.append(it(lump(hx, hy, rx, ry, seed=5, wob=0.07, n=10, rot=-0.05), PINK, INK, (hx, hy + ry), s6, e6))
    for k, (x, y, tilt) in enumerate(EYES):
        w, h = 50, 42
        items.append(it('M' + 'L'.join(p(*q) for q in almond(x, y, w, h, tilt)) + 'Z', '#ffffff', INK * 1.15, (x, y), s6 + 0.025, e6))
        px, py = x + (8 if k == 0 else -6), y + 3
        items.append(it(circle(px, py, 23), '#2DFFF4', INK * 0.8, (px, py), s6 + 0.03, e6))  # cyan iris
        items.append(it(circle(px, py, 11), '#000', 0, (px, py), s6 + 0.035, e6))
        # the sleepy lid: there with the eye on step 6, lifting away (shrinking up into the brow) on step 7, the
        # left one a little before the right
        o7 = step(7, 0.08 + 0.2 * k, 0.75 + 0.25 * k)
        items.append(it(lid_path(x, y, w + 1, h + 1, tilt), PINK, INK * 1.15, (x, y - h), s6 + 0.025, e6, 'y', o7))
    mx, my = hx + 4, hy + 58
    mouth = f'M{p(mx - 26, my - 4)}C{p(mx - 10, my + 4)} {p(mx + 12, my + 2)} {p(mx + 28, my - 8)}C{p(mx + 22, my + 16)} {p(mx - 18, my + 18)} {p(mx - 26, my - 4)}Z'
    items.append(it(mouth, MOUTH, INK * 0.8, (mx, my), s6 + 0.05, e6))
    return items


def preview(items, t) -> str:
    """Like ghost_endframes.sprite_svg (the app's easing), but with the app's 'x' and 'y' growth too."""
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


def cat_frame(t: float) -> Image.Image:
    im = m.compose()
    if t <= 0:
        return im
    on = preview(body_items(), t)
    if on:  # "on": clipped to the column, under the painting's ink
        im.alpha_composite(m.svg(f'<clipPath id="col"><path d="{m.FILLS["f305"]}"/></clipPath><g clip-path="url(#col)">{on}</g>'))
        im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{d}"/>' for d in m.INKS.values()) + '</g>'))
    over = preview(head_items(), t)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def cat_main() -> None:
    out = OUT.parent / 'caterpillar'
    out.mkdir(parents=True, exist_ok=True)
    cat_frame(1.0).save(out / 'end-frame.png')
    for frames, name in [([0, 0.25, 0.5, 0.75, 1.0], 'strip.png'), ([k / 8 for k in range(9)], 'steps.png')]:
        tiles = [cat_frame(t) for t in frames]
        w, h = tiles[0].size
        sc = 0.42 if len(frames) == 5 else 0.26
        tw, th = int(w * sc), int(h * sc)
        strip = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        try:
            font = ImageFont.load_default(size=24)
        except TypeError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}' if len(frames) == 5 else f'step {round(tt * 8)}', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        strip.save(out / name)
    print('wrote', out)


def build() -> dict:
    return {
        'label': "The pink column between the stalks: drag up and down for the Upper 4' drawbar; a pink caterpillar "
                 'climbs into the gap one fat segment a step, then lifts its head, opens its sleepy eyes and curls out '
                 'its antennae',
        'effects': [
            {'effect': 'sprites', 'place': 'on', 'items': body_items()},
            {'effect': 'sprites', 'place': 'over', 'items': head_items()},
        ],
    }


if __name__ == '__main__' and 'caterpillar' in __import__('sys').argv[1:]:
    cat_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    b = build()
    (OUT.parent / 'build.json').write_text(_j.dumps(b, indent=2) + '\n')
    print('exported', sum(len(e['items']) for e in b['effects']), 'shapes to', OUT.parent / 'build.json')
