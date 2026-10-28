# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (pedal split at C3, its highest) for the grey ground, bottom centre (f074): a big translucent
stretch of ground between the pink horned figure, the waving pink creature, the mitten and the lying creature's head.
Its one characterful part is a little dark green dish-shaped hole near its middle, a brown oval inside it, with a
brown wisp curling down into it from under the orange disc of the pink figure.

    uv run scripts/ground_endframes.py          # the five end frames and sheet
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
m.CROP = (1500, 2950, 1300, 1150)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/voice-pedal-split/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 15
C = (2112.0, 3600.0)       # the dish's middle
HOLE = (2128.0, 3562.0)    # the brown oval inside it
A = math.radians(-22.0)    # the dish's long axis, rising to the right
DISH_GREEN, DISH_BROWN = '#4d7a5a', '#7a5a3e'
PINK, PINK2, CREAM, MINT, LILAC = '#ff9fc4', '#ffd0e4', '#fff3cf', '#7fe0c8', '#d9a6ff'
YELLOW, RED, CHOC, CYAN, CYAN2, LEAF = '#ffe066', '#f64c76', '#7a3f22', '#8fe3f7', '#4fb7e6', '#7fd36b'


def R(u, v, c=C, a=A):
    """A point u along the dish's axis and v across it (v negative is up-left)."""
    ca, sa = math.cos(a), math.sin(a)
    return (c[0] + ca * u - sa * v, c[1] + sa * u + ca * v)


def closed(P) -> str:
    """A smooth closed Catmull-Rom curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(x, y, rx, ry, rot=0.0, seed=0, wob=0.1, n=9) -> str:
    """A lumpy, hand-drawn ellipse round (x, y), turned rot degrees."""
    rnd = random.Random(seed)
    a0 = math.radians(rot)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * math.cos(a0) - v * math.sin(a0), y + u * math.sin(a0) + v * math.cos(a0)))
    return closed(P)


def petal(base, ang, length, width, seed=0) -> str:
    """A pointed, slightly lopsided petal or leaf from base, heading ang degrees."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    bx, by = base
    Q = lambda u, v: (bx + ux * u + nx * v, by + uy * u + ny * v)
    w1, w2 = width * (0.9 + rnd.random() * 0.2), width * (0.9 + rnd.random() * 0.2)
    return (f'M{p(*Q(0, 0))}C{p(*Q(length * 0.25, w1))} {p(*Q(length * 0.7, w1 * 0.9))} {p(*Q(length, 0))}'
            f'C{p(*Q(length * 0.7, -w2 * 0.9))} {p(*Q(length * 0.25, -w2))} {p(*Q(0, 0))}Z')


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


def front_rim(colour=DISH_GREEN) -> str:
    """The near lip of the dish, redrawn over whatever comes up out of it."""
    P = [R(u, 62 * math.sqrt(max(0.0, 1 - (u / 132) ** 2)) - 6) for u in [-132 + 264 * k / 20 for k in range(21)]]
    Q = [R(u, 18 * math.sqrt(max(0.0, 1 - (u / 120) ** 2)) - 2) for u in [120 - 240 * k / 16 for k in range(17)]]
    d = 'M' + 'L'.join(p(*q) for q in P) + 'L' + 'L'.join(p(*q) for q in Q) + 'Z'
    return outlined(d, colour, INK)


# ---- 1  banana split ------------------------------------------------------------------------------------------------
def scoop(x, y, r, colour, seed) -> str:
    out = outlined(blob(x, y, r, r * 0.92, 0, seed, 0.1, 10), colour, INK)
    # chocolate sauce over its top, running down in two drips
    rnd = random.Random(seed)
    sauce = blob(x, y - r * 0.5, r * 0.82, r * 0.42, rnd.uniform(-8, 8), seed + 1, 0.14, 8)
    drips = ''
    for k, du in enumerate((-0.45, 0.3)):
        dx = x + du * r
        drips += outlined(tube([(dx, y - r * 0.3), (dx + 3, y + r * (0.05 + 0.2 * k))], r * 0.13, r * 0.11), CHOC, INK * 0.8)
    out += drips + outlined(sauce, CHOC, INK * 0.85) + f'<path d="{blob(x, y - r * 0.47, r * 0.7, r * 0.3, 0, seed + 1, 0.1, 8)}" fill="{CHOC}"/>'
    out += f'<path d="{blob(x - r * 0.3, y - r * 0.6, r * 0.18, r * 0.08, -20, seed + 2)}" fill="#b0714a"/>'
    return out


def crescent(P, w, colour, edge=INK) -> str:
    """A banana-like shape along P, fattest in the middle and tapering to both ends."""
    n = len(P)
    L, Rr = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * (0.25 + 0.75 * math.sin(math.pi * i / (n - 1)) ** 0.6)
        L.append((x + nx * ww, y + ny * ww))
        Rr.append((x - nx * ww, y - ny * ww))
    return outlined(closed(L + Rr[::-1]), colour, edge)


def banana(P, seed, w=38) -> str:
    out = crescent(P, w, YELLOW)
    out += f'<path d="{closed([((P[i][0] + P[i + 1][0]) / 2, (P[i][1] + P[i + 1][1]) / 2 - 12) for i in range(4, len(P) - 5, 3)] + [(P[i][0], P[i][1] - 4) for i in range(len(P) - 6, 4, -3)])}" fill="#fff3a8"/>'
    out += outlined(blob(*P[0], 16, 12, 0, seed, 0.1, 7), '#6b4a2a', INK * 0.7)
    out += outlined(blob(*P[-1], 14, 11, 0, seed + 1, 0.1, 7), '#6b4a2a', INK * 0.7)
    return out


BOAT = (2105.0, 3585.0)
BA = math.radians(-14.0)


def v1_banana_split() -> Image.Image:
    """Banana split: the dish becomes a long glass sundae boat, two banana halves along it, three scoops piled in it,
    the brown wisp pours on as chocolate sauce, whipped cream and a cherry on top."""
    GLASS, GLASS2 = '#e4d8ff', '#cdb9ff'
    Q = lambda u, v: R(u, v, BOAT, BA)
    out = outlined(blob(*Q(0, -4), 250, 52, -14, 3, 0.04, 12), GLASS2, INK)  # the far rim
    # the back banana half, its ends curling up out of the boat behind the scoops
    out += banana(bez(Q(-340, -190), Q(-300, -20), Q(300, -30), Q(345, -200), 26), 5, 30)
    scoops = [(Q(-135, -88), 86, PINK), (Q(138, -92), 84, MINT), (Q(0, -112), 98, CREAM)]
    for k, ((x, y), r, col) in enumerate(scoops):
        out += scoop(x, y, r, col, 10 + k)
    # the boat's body over the scoops' bottoms
    bowl = closed([Q(-268, -16), Q(-190, 80), Q(0, 118), Q(190, 82), Q(268, -20), Q(130, -8), Q(0, -4), Q(-130, -6)])
    out += outlined(bowl, GLASS, INK)
    out += f'<path d="{blob(*Q(-120, 84), 70, 11, -10, 4, 0.08)}" fill="#ffffff" fill-opacity="0.8"/>'
    # the front banana half lying along its lip, the tips poking out of both ends
    out += banana(bez(Q(-320, -30), Q(-190, 46), Q(190, 44), Q(318, -40), 26), 7, 24)
    # the wisp thickened into a stream of sauce pouring from under the orange disc onto the mint scoop
    (mx, my), mr = scoops[1][0], scoops[1][1]
    P = bez((2246, 3330), (2266, 3372), (mx + 30, my - mr - 30), (mx + 14, my - mr * 0.7), 20)
    out += outlined(tube(P, 18, 26), CHOC, INK * 0.85)
    # whipped cream and a cherry on the big middle scoop
    (x, y), r = scoops[2][0], 98
    top = y - r * 0.85
    for k, (dy, rr) in enumerate(((10, 66), (-36, 50), (-72, 34))):
        out += outlined(blob(x + k * 4, top + dy, rr, rr * 0.62, 0, 20 + k, 0.12, 9), '#ffffff', INK * 0.9)
    out += outlined(tube(bez((x + 16, top - 108), (x + 22, top - 150), (x + 52, top - 170), (x + 74, top - 176), 10), 8, 7), '#5aa84a', INK * 0.6)
    out += outlined(blob(x + 12, top - 84, 46, 44, 0, 23, 0.06, 8), RED, INK * 0.9)
    out += f'<path d="{blob(x - 4, top - 100, 12, 8, -30, 24)}" fill="#ffffff"/>'
    return draw('', [], out)


# ---- 2  the splits --------------------------------------------------------------------------------------------------
def striped_leg(P, w0, w1, bands, cols) -> str:
    """An outlined leg along P with candy stocking stripes: fill, stripes (fill only), then the outline on top."""
    n = len(P)
    L, Rr = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = w0 + (w1 - w0) * i / (n - 1)
        L.append((x + nx * w, y + ny * w))
        Rr.append((x - nx * w, y - ny * w))
    shape = tube(P, w0, w1)
    out = f'<path d="{shape}" fill="{cols[0]}"/>'
    step = (n - 1) / bands
    for k in range(1, bands, 2):
        i0, i1 = round(k * step), round((k + 1) * step)
        q = L[i0:i1 + 1] + Rr[i0:i1 + 1][::-1]
        out += f'<path d="M{"L".join(p(*z) for z in q)}Z" fill="{cols[1]}"/>'
    out += f'<path d="{shape}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    return out


def shoe(x, y, ang, seed) -> str:
    """A big round-toed party shoe pointing ang degrees, a pompom on its toe."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    out = outlined(blob(x - ux * 10, y - uy * 10 + 18, 96, 30, ang, seed + 2, 0.06, 9), '#6b3fa0', INK)  # the sole
    out += outlined(blob(x, y, 98, 54, ang, seed, 0.07, 10), RED, INK)
    out += outlined(blob(x + ux * 58, y + uy * 58 - 30, 34, 30, 0, seed + 1, 0.14, 8), YELLOW, INK * 0.85)
    return out


def v2_splits() -> Image.Image:
    """The splits: a pink tutu frills up round the hole and two long candy-striped legs shoot out of it upside down,
    kicking apart into the splits, big party shoes on their feet (pedals: feet)."""
    hx, hy = HOLE
    out = ''
    legs = [
        (bez((hx - 20, hy - 60), (hx - 110, hy - 160), (hx - 210, hy - 200), (hx - 280, hy - 200), 22), (hx - 338, hy - 212), 192),
        (bez((hx + 20, hy - 70), (hx + 120, hy - 190), (hx + 250, hy - 240), (hx + 330, hy - 250), 22), (hx + 392, hy - 262), -8),
    ]
    for k, (P, foot, ang) in enumerate(legs):
        out += striped_leg(P, 48, 36, 9, ['#ffffff', '#a46cff' if k == 0 else RED])
        out += shoe(*foot, ang, 40 + k)
    # the tutu: two frilly layers round the hole, the legs coming up out of its middle
    out += outlined(blob(hx - 4, hy - 20, 190, 84, -20, 31, 0.16, 18), PINK, INK)
    out += outlined(blob(hx, hy - 38, 135, 56, -20, 32, 0.16, 15), PINK2, INK * 0.9)
    return draw('', [], out)


# ---- 3  the burrower ------------------------------------------------------------------------------------------------
def paws(x, y, ang, seed, col) -> str:
    out = outlined(blob(x, y, 48, 34, ang, seed, 0.1, 8), col, INK * 0.9)
    a = math.radians(ang)
    for k in (-1, 0, 1):
        fx, fy = x + math.cos(a) * k * 26 + math.sin(a) * 26, y + math.sin(a) * k * 26 - math.cos(a) * 26
        fx, fy = x + k * 28, y + 24
        out += outlined(blob(fx, fy, 17, 15, 0, seed + k + 5, 0.1, 7), col, INK * 0.7)
    return out


def tall_eye(x, y, rx, ry, look=(0, -0.3), lid=0.0) -> str:
    """The painting's eye: a tall white oval with a heavy outline, a dark pupil looking somewhere."""
    out = outlined(blob(x, y, rx, ry, 0, int(x), 0.05, 9), '#ffffff', INK)
    out += f'<path d="{blob(x + look[0] * rx * 0.45, y + look[1] * ry * 0.45, rx * 0.46, ry * 0.4, 0, int(y), 0.05, 8)}" fill="#1b1b3a"/>'
    out += f'<path d="{circle(x + look[0] * rx * 0.45 + rx * 0.15, y + look[1] * ry * 0.45 - ry * 0.12, rx * 0.12)}" fill="#fff"/>'
    if lid:
        out += outlined(f'M{p(x - rx - 4, y - ry * 0.2)}C{p(x - rx, y - ry - lid)} {p(x + rx, y - ry - lid)} {p(x + rx + 4, y - ry * 0.2)}'
                        f'C{p(x + rx * 0.5, y - ry * 0.45)} {p(x - rx * 0.5, y - ry * 0.45)} {p(x - rx - 4, y - ry * 0.2)}Z', LILAC, INK * 0.8)
    return out


def v3_burrower() -> Image.Image:
    """The burrower: a round lilac creature pops up out of the hole, paws on the rim, a long pink snout, wide eyes, and
    waves a big paw."""
    hx, hy = HOLE
    col = LILAC
    out = ''
    # the waving arm, behind the head, raised up and out to the left
    P = bez((hx + 60, hy - 200), (hx + 140, hy - 250), (hx + 150, hy - 330), (hx + 160, hy - 380), 18)
    out += outlined(tube(P, 40, 34), col, INK)
    hand = (hx + 168, hy - 420)
    for k, ang in enumerate((-170, -130, -95, -60)):
        a = math.radians(ang)
        out += outlined(blob(hand[0] + math.cos(a) * 64, hand[1] + math.sin(a) * 64, 32, 25, ang, 50 + k, 0.1, 7), col, INK * 0.85)
    out += outlined(blob(*hand, 74, 64, 20, 55, 0.1, 9), col, INK)
    # the head and body, coming up out of the hole
    out += outlined(blob(hx + 5, hy - 150, 132, 180, 8, 60, 0.08, 11), col, INK)
    out += f'<path d="{blob(hx - 40, hy - 240, 40, 22, -20, 61)}" fill="#f2d6ff"/>'
    out += tall_eye(hx - 40, hy - 220, 34, 58, (-0.5, -0.3))
    out += tall_eye(hx + 52, hy - 214, 32, 54, (-0.5, -0.3))
    # a long lumpy pink snout poking out to the left, a dark nose on its tip
    out += outlined(blob(hx - 70, hy - 132, 105, 42, 12, 64, 0.08, 10), PINK, INK)
    out += outlined(blob(hx - 168, hy - 150, 30, 30, 0, 63, 0.1, 7), '#c02a6a', INK * 0.9)
    out += front_rim()
    out += paws(*R(-80, -14), 0, 70, col) + paws(*R(100, -24), 0, 80, col)
    return draw('', [], out)


# ---- 4  sprout ------------------------------------------------------------------------------------------------------
def v4_sprout() -> Image.Image:
    """Sprout: the wisp turns green and grows into a thick stalk out of the hole, two big leaves unfurl and a candy
    flower opens at its top."""
    hx, hy = HOLE
    P = bez((hx, hy), (hx + 60, hy - 140), (hx - 40, hy - 260), (hx + 10, hy - 400), 26)
    out = outlined(tube(P, 34, 22), LEAF, INK)
    out += outlined(petal((hx + 22, hy - 120), 200, 230, 70, 1), '#5cc35a', INK)
    out += outlined(petal((hx - 6, hy - 250), -25, 220, 64, 2), '#8fe36b', INK)
    fx, fy = P[-1][0], P[-1][1] - 30
    cols = [PINK, YELLOW, '#ff9f43', PINK, '#c4a3f0', YELLOW, '#ff9f43']
    for k in range(7):
        out += outlined(petal((fx, fy), k * 360 / 7 - 80, 140, 52, 10 + k), cols[k], INK)
    out += outlined(blob(fx, fy, 58, 54, 0, 20, 0.08, 9), '#ffcf3a', INK)
    out += f'<path d="{blob(fx - 15, fy - 15, 18, 12, -30, 21)}" fill="#fff3b0"/>'
    out += front_rim()
    return draw('', [], out)


# ---- 5  pond --------------------------------------------------------------------------------------------------------
def pad(x, y, rx, ry, rot, seed, col='#5cc35a') -> str:
    a = math.radians(rot)
    d = blob(x, y, rx, ry, rot, seed, 0.06, 10)
    notch = f'M{p(x, y)}L{p(x + math.cos(a + 0.25) * rx * 1.2, y + math.sin(a + 0.25) * ry * 1.2)}L{p(x + math.cos(a - 0.25) * rx * 1.2, y + math.sin(a - 0.25) * ry * 1.2)}Z'
    return (f'<mask id="n{seed}"><rect x="0" y="0" width="5000" height="5000" fill="#fff"/><path d="{notch}" fill="#000"/></mask>'
            f'<g mask="url(#n{seed})">{outlined(d, col, INK * 0.9)}</g>')


def v5_pond() -> Image.Image:
    """Pond: the hole wells up and spreads into a cyan lily pond across the ground, lily pads float out and a big pink
    lotus opens on one of them."""
    out = outlined(blob(*R(-20, -24), 330, 125, -18, 70, 0.06, 12), CYAN, INK)
    out += f'<path d="{blob(*R(10, -30), 220, 74, -18, 71, 0.07, 10)}" fill="{CYAN2}"/>'
    out += f'<path d="{blob(*R(-120, 50), 90, 16, -18, 72, 0.1, 8)}" fill="#e6fbff"/>'
    out += pad(*R(-175, 20), 120, 60, -12, 73)
    out += pad(*R(170, 34), 92, 46, 170, 74, '#7fd36b')
    out += pad(*R(60, -60), 58, 30, 30, 75, '#8fe36b')
    lx, ly = R(-165, 0)
    for k, (ang, L) in enumerate(((-165, 150), (-15, 150), (-132, 175), (-48, 175), (-90, 190))):
        out += outlined(petal((lx, ly), ang, L, 60, 80 + k), PINK if k < 4 else PINK2, INK)
    out += outlined(blob(lx, ly - 22, 40, 28, 0, 85, 0.12, 8), YELLOW, INK * 0.85)
    return draw('', ['f014'], out)


VERSIONS = [
    ('1-banana-split', 'Banana split', v1_banana_split),
    ('2-the-splits', 'The splits', v2_splits),
    ('3-burrower', 'Burrower', v3_burrower),
    ('4-sprout', 'Sprout', v4_sprout),
    ('5-lily-pond', 'Lily pond', v5_pond),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (split Off)', m.compose())]
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


# ---- chosen: banana split -------------------------------------------------------------------------------------------
# Picked under 5a: a big drawn pun on "split" (rule 4), party food for the celebration (rule 3), and the ground's own
# dish morphing into something else (rule 1); the painted wisp already reads as sauce pouring into a dish. Built as
# arrivals across the 16 values of the pedal split (frame = value / 15), each landing on k/15: the painted dish turns to
# glass (C1), the boat swells up out of it on a stem (D1), the two banana halves (E1, F1), three scoops one after
# another, pink, mint, then the big cream one (G1, A1, B1), a sauce cap and drips on each (C2, D2, E2), the wisp
# thickens into a pour of sauce off the orange disc onto the cream scoop (F2) and runs down it (G2), whipped cream in two
# goes (A2, B2) and the cherry (C3). The sundae sits up and left of the painted dish, so it clears the narwhal's fountain
# splash (x 2020-2440 below y 3510); it is placed `around` with the pink horned figure standing in front of it.
#
#     uv run scripts/ground_endframes.py split    # progression strip, step sheet and end frame
#     uv run scripts/ground_endframes.py export   # docs/objects/voice-pedal-split/build.json
SPLIT = (1990.0, 3470.0)   # the boat's middle, up and left of the painted dish
SA = math.radians(-18.0)   # rising to the right, near the painted dish's own axis
# The pink horned figure standing on the ground stays in front of the sundae.
FRONT = ['f170', 'f171', 'f172', 'f173']
GLASS, GLASS2, GLASS3 = '#e4d8ff', '#cdb9ff', '#f6f1ff'
K = lambda k: k / 15       # value k (C1 = 1 ... C3 = 15) as a frame


def S(u, v):
    return R(u, v, SPLIT, SA)


def crescent_d(P, w) -> str:
    n = len(P)
    L, Rr = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * (0.25 + 0.75 * math.sin(math.pi * i / (n - 1)) ** 0.6)
        L.append((x + nx * ww, y + ny * ww))
        Rr.append((x - nx * ww, y - ny * ww))
    return closed(L + Rr[::-1])


def it(d, fill, edge, at, s, e) -> dict:
    return {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
            'start': round(s, 4), 'end': round(min(1.0, e), 4), 'grow': 'scale'}


def banana_items(P, w, seed, s, e) -> list[dict]:
    mid = P[len(P) // 2]
    hi = closed([((P[i][0] + P[i + 1][0]) / 2, (P[i][1] + P[i + 1][1]) / 2 - w * 0.3) for i in range(4, len(P) - 5, 3)]
                + [(P[i][0], P[i][1] - w * 0.1) for i in range(len(P) - 6, 4, -3)])
    return [it(crescent_d(P, w), YELLOW, INK, mid, s, e),
            it(hi, '#fff3a8', 0, mid, s + (e - s) * 0.3, e),
            it(blob(*P[0], 16, 12, 0, seed, 0.1, 7), '#6b4a2a', INK * 0.7, P[0], s + (e - s) * 0.5, e),
            it(blob(*P[-1], 14, 11, 0, seed + 1, 0.1, 7), '#6b4a2a', INK * 0.7, P[-1], s + (e - s) * 0.5, e)]


# (centre, radius, colour, value it lands on, value its sauce lands on, drip offsets)
SCOOPS = [
    ((1838.0, 3452.0), 76, PINK, 5, 8, (-0.5, 0.25)),
    ((1962.0, 3428.0), 72, MINT, 6, 9, (-0.25, 0.35)),
    ((2088.0, 3364.0), 92, CREAM, 7, 10, (-0.45, 0.3)),
]


def scoop_items(c, r, col, k, ks, drips, seed) -> list[dict]:
    x, y = c
    base = (x, y + r * 0.8)
    out = [it(blob(x, y, r, r * 0.92, 0, seed, 0.11, 10), col, INK, base, K(k - 1), K(k))]
    # the sauce: drips run down first, then the cap spreads over its top and joins them
    s0, s1 = K(ks - 1), K(ks)
    for j, du in enumerate(drips):
        dx = x + du * r
        P = [(dx, y - r * 0.3), (dx + 2, y + r * (0.05 + 0.18 * j)), (dx + 4, y + r * (0.12 + 0.2 * j))]
        out.append(it(tube(P, r * 0.13, r * 0.11), CHOC, INK * 0.8, (dx, y - r * 0.3), s0 + (s1 - s0) * 0.35, s1))
    cap = blob(x, y - r * 0.5, r * 0.84, r * 0.44, (seed * 7) % 13 - 6, seed + 1, 0.15, 8)
    out.append(it(cap, CHOC, INK * 0.85, (x, y - r * 0.6), s0, s0 + (s1 - s0) * 0.7))
    out.append(it(blob(x, y - r * 0.47, r * 0.7, r * 0.3, 0, seed + 1, 0.1, 8), CHOC, 0, (x, y - r * 0.5), s0 + (s1 - s0) * 0.3, s0 + (s1 - s0) * 0.8))
    out.append(it(blob(x - r * 0.3, y - r * 0.62, r * 0.18, r * 0.08, -20, seed + 2), '#b0714a', 0, (x - r * 0.3, y - r * 0.62), s0 + (s1 - s0) * 0.6, s1))
    return out


def split_items() -> list[dict]:
    dish = (2108.0, 3604.0)  # the painted dish's middle: everything for the boat grows out of it
    items = []
    # C1: the painted dish turns to glass, the boat's foot
    items.append(it(blob(2108, 3603, 142, 70, -22, 90, 0.05, 10), GLASS2, INK, dish, 0, K(1)))
    items.append(it(blob(2126, 3566, 84, 40, -16, 91, 0.06, 9), GLASS, INK * 0.8, (2126, 3566), K(0.4), K(1)))
    # D1: a short glass stem lifts the boat up out of it
    items.append(it(blob(2068, 3560, 58, 34, -30, 92, 0.08, 8), GLASS2, INK, dish, K(1), K(1.6)))
    # D1: the boat swells up out of it: its far rim (its body comes later in the list, over the scoops)
    items.append(it(blob(*S(0, -4), 252, 52, -18, 3, 0.05, 12), GLASS2, INK, dish, K(1), K(2)))
    # E1: the back banana half, its ends curling up out of the boat behind the scoops
    items += banana_items(bez(S(-268, -130), S(-236, -36), S(246, -46), S(286, -136), 26), 28, 5, K(2), K(3))
    for j, (c, r, col, k, ks, drips) in enumerate(SCOOPS):
        items += scoop_items(c, r, col, k, ks, drips, 10 + j)
    # the boat's body over the scoops' bottoms (D1, with the rim)
    bowl = closed([S(-262, -16), S(-190, 70), S(-10, 104), S(170, 72), S(262, -20), S(130, 18), S(0, 24), S(-130, 20)])
    items.append(it(bowl, GLASS, INK, dish, K(1), K(2)))
    items.append(it(blob(*S(-110, 52), 70, 11, -18, 4, 0.08), GLASS3, 0, S(-110, 52), K(1.5), K(2)))
    # F1: the front banana half along its lip, the tips poking out of both ends
    items += banana_items(bez(S(-274, 6), S(-176, 86), S(176, 82), S(270, -4), 26), 20, 7, K(3), K(4))
    # F2-G2: the wisp thickens into a pour of sauce from under the orange disc onto the mint scoop
    P = bez((2240, 3322), (2222, 3352), (2196, 3352), (2170, 3336), 18)
    items.append(it(tube(P, 15, 24), CHOC, INK * 0.85, P[0], K(10), K(11)))
    items.append(it(tube([(2172, 3330), (2176, 3380), (2180, 3420)], 22, 17), CHOC, INK * 0.8, (2172, 3330), K(11), K(12)))
    items.append(it(blob(2168, 3332, 30, 22, 0, 95, 0.12, 8), CHOC, 0, (2170, 3336), K(11), K(12)))
    # A2-B2: whipped cream on the big middle scoop in two goes
    (x, y), r = SCOOPS[2][0], SCOOPS[2][1]
    top = y - r * 0.85
    for j, (dy, rr, k) in enumerate(((10, 64, 13), (-34, 48, 14), (-68, 32, 14))):
        s0 = K(k - 1) + (K(1) * 0.35 if j == 2 else 0)
        items.append(it(blob(x + j * 5, top + dy, rr, rr * 0.62, 0, 20 + j, 0.13, 9), '#ffffff', INK * 0.9, (x + j * 5, top + dy + rr * 0.5), s0, K(k)))
    # C3: the cherry
    items.append(it(tube(bez((x + 16, top - 104), (x + 22, top - 146), (x + 52, top - 166), (x + 74, top - 172), 10), 8, 7), '#5aa84a', INK * 0.6,
                    (x + 16, top - 104), K(14.3), K(15)))
    items.append(it(blob(x + 12, top - 80, 46, 44, 0, 23, 0.06, 8), RED, INK * 0.9, (x + 12, top - 40), K(14), K(15)))
    items.append(it(blob(x - 4, top - 96, 12, 8, -30, 24), '#ffffff', 0, (x - 4, top - 96), K(14.5), K(15)))
    return items


def split_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    return draw(g.sprite_svg(split_items(), t), FRONT)


NOTES = ['Off', 'C1', 'D1', 'E1', 'F1', 'G1', 'A1', 'B1', 'C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'C3']


def strip(frames, labels, path, sc) -> None:
    tiles = [split_frame(t) for t in frames]
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    cols = min(len(tiles), 5 if len(tiles) == 5 else 4)
    rows = math.ceil(len(tiles) / cols)
    out = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 46) * rows + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(out)
    for i, (lab, im) in enumerate(zip(labels, tiles)):
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 46)
        d.text((x, y), lab, fill='black', font=font)
        out.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 34))
    out.save(path)
    return tiles


def split_main() -> None:
    out = OUT.parent / 'banana-split'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = strip(frames, [f'frame {t:.2f}' for t in frames], out / 'strip.png', 0.42)
    tiles[-1].save(out / 'end-frame.png')
    strip([k / 15 for k in range(16)], [f'{NOTES[k]} ({k}/15)' for k in range(16)], out / 'steps.png', 0.3)
    print('wrote', out)


if __name__ == '__main__' and 'split' in __import__('sys').argv[1:]:
    split_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The grey ground: shows the pedal split (display only); its little dish turns into a banana split, one more '
                 'part for each note higher, boat, bananas, scoops, sauce, cream, up to the cherry at C3',
        'effects': [{'effect': 'sprites', 'place': 'around', 'parts': [], 'front': FRONT, 'items': split_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(split_items()), 'shapes')
