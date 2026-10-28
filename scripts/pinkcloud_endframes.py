# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Leslie horn/drum balance at +12 dB, all horn) for the pink cloud: the scalloped pink cloud left
of the pyramid, its lumps hooked with little curls, its lower half hidden behind the magenta and yellow spikes.

    uv run scripts/pinkcloud_endframes.py           # the five end frames and sheet
    uv run scripts/pinkcloud_endframes.py elephant  # the chosen pink elephant: progression strip, steps and end frame
    uv run scripts/pinkcloud_endframes.py export    # docs/objects/leslie-balance/build.json
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
m.CROP = (1700, 520, 1350, 1230)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/leslie-balance/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 14
CLOUD, CLOUD_D, CLOUD_L = '#fcc4ea', '#f59ee0', '#ffe3f6'
MAGENTA, PINK, BUTTER, ORANGE, CYAN, LILAC, LIME = '#FF5CED', '#f64c76', '#ffe066', '#ff9f43', '#2DFFF4', '#c4a3f0', '#7fd36b'
SPIKES = ['f226', 'f227', 'f228', 'f229', 'f230']  # the magenta and yellow spikes in front of the cloud


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


def closed(P) -> str:
    """A closed Catmull-Rom curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, r, seed, wob=0.12, n=9, rot=0.0, ry=None) -> str:
    """A lumpy, hand-drawn round (or oval, with ry) shape round (x, y)."""
    rnd = random.Random(seed)
    ry = ry or r
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * r * f, math.sin(a) * ry * f
        P.append((x + u * math.cos(rot) - v * math.sin(rot), y + u * math.sin(rot) + v * math.cos(rot)))
    return closed(P)


def oval(x, y, rx, ry, deg=0.0, n=40) -> str:
    a = math.radians(deg)
    P = [(x + math.cos(t) * rx * math.cos(a) - math.sin(t) * ry * math.sin(a),
          y + math.cos(t) * rx * math.sin(a) + math.sin(t) * ry * math.cos(a)) for t in (k / n * 2 * math.pi for k in range(n))]
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


def scallop(x, y, r, n, seed, bump=0.22, rot=0.0, ry=None) -> str:
    """A cloud-like scalloped round: n round bumps on its rim, the way the painting draws clouds."""
    rnd = random.Random(seed)
    ry = ry or r
    P = []
    for k in range(n * 4):
        a = rot + k / (n * 4) * 2 * math.pi
        ph = (k % 4) / 4
        f = 1 + bump * (math.sin(ph * math.pi) - 0.4) + (rnd.random() - 0.5) * 0.05
        P.append((x + math.cos(a) * r * f, y + math.sin(a) * ry * f))
    return closed(P)


def round_eye(x, y, r, look=(0.0, 0.0)) -> str:
    out = outlined(circle(x, y, r), '#ffffff', INK * 0.85)
    out += f'<path d="{circle(x + look[0] * r * 0.35, y + look[1] * r * 0.35, r * 0.48)}" fill="#111"/>'
    out += f'<path d="{circle(x + look[0] * r * 0.35 - r * 0.16, y + look[1] * r * 0.35 - r * 0.18, r * 0.15)}" fill="#fff"/>'
    return out


def poly(P) -> str:
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


# ---- 1 pink elephant ------------------------------------------------------------------------------------------------
def bell(tip, toward, base_w, rim_r, length, colour=BUTTER) -> str:
    """A flared horn bell out of a tube's end at tip, pointing along toward (degrees): outlined, open mouth."""
    a = math.radians(toward)
    ux, uy = math.cos(a), math.sin(a)  # along
    nx, ny = -uy, ux                   # across
    L = lambda s, t: (tip[0] + ux * s + nx * t, tip[1] + uy * s + ny * t)
    side = [(-10, base_w), (length * 0.45, base_w * 1.25), (length * 0.8, rim_r * 0.7), (length, rim_r)]
    P = [L(s, t) for s, t in side] + [L(s, -t) for s, t in side[::-1]]
    out = outlined(closed(P[:4] + [L(length + 12, 0)] + P[4:]), colour, INK)
    mx, my = L(length, 0)
    deg = math.degrees(a) + 90
    out += outlined(oval(mx, my, rim_r, rim_r * 0.3, deg), ORANGE, INK * 0.8)
    out += f'<path d="{oval(mx - ux * 4, my - uy * 4, rim_r * 0.62, rim_r * 0.15, deg)}" fill="{PINK}"/>'
    return out


def v1_elephant() -> Image.Image:
    """Pink elephant: the cloud is a pink elephant: its top lump becomes a head with a big scalloped ear and a waking
    eye, and its trunk swings up out of the cloud and trumpets through a flared golden bell."""
    out = ''
    out += outlined(scallop(2545, 1150, 150, 6, 3, 0.18, 0.3, 175), CLOUD_D, INK)  # the ear, behind the head
    out += f'<path d="{lump(2560, 1160, 85, 4, 0.1, 8, 0, 105)}" fill="#ffb3d9"/>'
    P = bez((2300, 1150), (2160, 1240), (2030, 1110), (2070, 900), 26)  # the trunk, up and to the left
    out += outlined(tube(P, 76, 46), CLOUD, INK)
    for u in (0.42, 0.58):  # two soft wrinkle bands, fill only
        i = int(u * (len(P) - 1))
        (ax, ay), (bx, by) = P[i - 1], P[i + 1]
        w = 76 + (46 - 76) * u
        out += f'<path d="{oval(P[i][0], P[i][1], 12, w * 0.8, math.degrees(math.atan2(by - ay, bx - ax)))}" fill="{CLOUD_D}"/>'
    (ax, ay), (bx, by) = P[-3], P[-1]
    out += bell(P[-1], math.degrees(math.atan2(by - ay, bx - ax)) - 8, 44, 140, 170)
    out += outlined(scallop(2370, 1085, 152, 5, 7, 0.14, -0.4, 135), CLOUD, INK)  # the head over the top lump
    out += f'<path d="{lump(2330, 1150, 45, 8, 0.1, 7, 0, 28)}" fill="#ffa0cf"/>'
    out += outlined(closed([(2265, 1185), (2205, 1250), (2140, 1268), (2185, 1222), (2235, 1170)]), '#fff6d6', INK * 0.8)
    out += round_eye(2390, 1058, 40, (-0.6, -0.3))
    return draw(out, SPIKES)


# ---- 2 coiled horn --------------------------------------------------------------------------------------------------
def v2_coil() -> Image.Image:
    """Coiled horn: the cloud rolls up round its middle into one big spiral, like its own curled hooks, a fat pink
    tube winding outward, and the outer end flares open into a horn's bell, up and to the left."""
    cx, cy = 2440, 1135
    th_max = 2 * math.pi * 1.4
    phi_end = math.pi + 0.3
    P = []
    for k in range(70):
        th = th_max * k / 69
        r = 30 + 190 * th / th_max
        phi = phi_end - th_max + th
        P.append((cx + math.cos(phi) * r, cy + math.sin(phi) * r * 0.92))
    out = outlined(tube(P, 18, 58), CLOUD, INK)
    out += outlined(lump(*P[0], 30, 141, 0.1, 7), CLOUD_D, INK * 0.8)
    (ax, ay), (bx, by) = P[-4], P[-1]
    out += bell((bx, by), math.degrees(math.atan2(by - ay, bx - ax)) - 6, 58, 175, 210, CLOUD_L)
    return draw(out, SPIKES)


# ---- 3 horn and drum -------------------------------------------------------------------------------------------------
def horn_and_drum(hs: float, ds: float) -> str:
    """The horn grown to hs and the drum to ds (0..1)."""
    out = ''
    if ds > 0:  # the drum: the cloud's left lump made into a fat bass drum
        x, y, rx, ry, h = 2140, 1120, 150, 52, 145
        body = f'M{p(x - rx, y)}L{p(x - rx, y + h)}A{rx} {ry} 0 0 0 {p(x + rx, y + h)}L{p(x + rx, y)}Z'
        d = outlined(body, MAGENTA, INK)
        for k in range(5):  # candy zigzag ties as filled triangles
            x0 = x - rx + 22 + k * (2 * rx - 44) / 5
            d += outlined(poly([(x0, y + 14), (x0 + (2 * rx - 44) / 10, y + h - 8), (x0 + (2 * rx - 44) / 5, y + 14)]), BUTTER, INK * 0.6)
        d += outlined(f'M{p(x - rx, y + h - 24)}L{p(x - rx, y + h)}A{rx} {ry} 0 0 0 {p(x + rx, y + h)}L{p(x + rx, y + h - 24)}'
                      f'A{rx} {ry} 0 0 1 {p(x - rx, y + h - 24)}Z', BUTTER, INK * 0.8)
        d += outlined(oval(x, y, rx, ry), '#fff6fb', INK)
        out += f'<g transform="translate({x} {y + h * 0.6}) scale({ds}) translate({-x} {-y - h * 0.6})">{d}</g>'
    if hs > 0:  # the horn: the top lump stretches up into a pink horn with a wide golden bell
        x, y = 2420, 1110
        P = bez((2430, 1130), (2440, 960), (2400, 860), (2300, 790), 20)
        d = outlined(tube(P, 92, 50), CLOUD, INK)
        (ax, ay), (bx, by) = P[-3], P[-1]
        d += bell(P[-1], math.degrees(math.atan2(by - ay, bx - ax)) - 15, 50, 200, 230)
        d += outlined(scallop(2425, 1110, 150, 5, 9, 0.14, 0.2, 115), CLOUD, INK)
        out += f'<g transform="translate({x} {y}) scale({hs}) translate({-x} {-y})">{d}</g>'
    return out


def v3_horn_and_drum() -> Image.Image:
    """Horn and drum (two-sided): the cloud's left lump rounds into a fat bass drum and its top lump stretches up into
    a big horn. Up to the middle the drum comes first; toward +12 (shown) the horn opens wide and the drum shrinks."""
    return draw(horn_and_drum(1.0, 0.72), SPIKES)


def v3_mid() -> Image.Image:
    return draw(horn_and_drum(0.6, 1.0), SPIKES)


# ---- 4 blowing -------------------------------------------------------------------------------------------------------
def gust(start, heading, run, r0, sign, n=40) -> list:
    """A gust's centreline: out from start along heading (degrees), bending gently for run px, then winding into a
    curl of radius r0 (sign 1 curls clockwise on screen, -1 counter-clockwise)."""
    x, y = start
    a = math.radians(heading)
    P = [(x, y)]
    for k in range(16):
        a += sign * 0.012
        x, y = x + math.cos(a) * run / 16, y + math.sin(a) * run / 16
        P.append((x, y))
    cx, cy = x - math.sin(a) * r0 * sign, y + math.cos(a) * r0 * sign
    phi0 = math.atan2(y - cy, x - cx)
    for k in range(1, n):
        v = k / (n - 1)
        r = r0 * (1 - 0.55 * v)
        phi = phi0 + sign * v * 2 * math.pi * 1.05
        P.append((cx + math.cos(phi) * r, cy + math.sin(phi) * r))
    return P


def v4_blowing() -> Image.Image:
    """Blowing: the cloud wakes up with two round eyes, puffs its left side out into a big cheek and blows two
    curling gusts of wind out to the left, across the stalks and spikes."""
    out = outlined(scallop(2215, 1195, 150, 5, 11, 0.12, 0.5, 125), CLOUD, INK)  # the puffed cheek
    out += f'<path d="{lump(2225, 1225, 60, 12, 0.1, 7, 0, 38)}" fill="#ff9fc4"/>'
    out += round_eye(2360, 1060, 44, (-0.7, 0.1)) + round_eye(2458, 1048, 44, (-0.7, 0.1))
    over = outlined(tube(gust((2040, 1165), 198, 250, 80, 1), 58, 16), '#ffffff', INK)
    over += outlined(tube(gust((2040, 1220), 160, 210, 66, -1), 48, 14), '#c9f6ff', INK)
    over += outlined(lump(2066, 1170, 42, 60, 0.1, 8, 0, 26), PINK, INK * 0.9)  # the pursed lips
    over += outlined(lump(2066, 1214, 44, 61, 0.1, 8, 0, 28), PINK, INK * 0.9)
    over += outlined(oval(2056, 1192, 22, 16), '#5a0f2a', INK * 0.7)
    return draw(out, SPIKES, over)


# ---- 5 cotton candy --------------------------------------------------------------------------------------------------
def v5_cotton_candy() -> Image.Image:
    """Cotton candy: the cloud billows up into a heap of candy floss in pinks, lilac and pale blue, on a striped
    paper cone poking out in front of the spikes."""
    out = ''
    # the cone, in front of the spikes
    cone = poly([(2230, 1330), (2530, 1330), (2385, 1720)])
    out += outlined(cone, '#fff6d6', INK)
    for k in range(4):  # candy stripes across it, as filled bands
        y0 = 1350 + k * 90
        w0 = 150 * (1 - (y0 - 1330) / 390)
        w1 = 150 * (1 - (y0 + 40 - 1330) / 390)
        out += f'<path d="{poly([(2380 - w0, y0), (2380 + w0, y0 + 10), (2380 + w1, y0 + 50), (2380 - w1, y0 + 40)])}" fill="{PINK}"/>'
    out += f'<path d="{cone}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    puffs = [(2250, 1280, 120, CLOUD), (2510, 1290, 115, LILAC), (2130, 1170, 105, '#bfeaff'), (2390, 1200, 150, CLOUD_D),
             (2620, 1150, 110, '#bfeaff'), (2240, 1020, 130, LILAC), (2500, 1000, 140, CLOUD), (2370, 860, 120, '#bfeaff'),
             (2620, 880, 90, CLOUD_D), (2140, 900, 85, CLOUD)]
    for k, (x, y, r, c) in enumerate(puffs):
        out += outlined(scallop(x, y, r, 5, 70 + k, 0.2, k * 0.7), c, INK)
        out += f'<path d="{lump(x - r * 0.25, y - r * 0.25, r * 0.32, 90 + k, 0.15, 7)}" fill="#ffffff" fill-opacity="0.7"/>'
    return draw('', [], out)


VERSIONS = [
    ('1-pink-elephant', 'Pink elephant', v1_elephant),
    ('2-coiled-horn', 'Coiled horn', v2_coil),
    ('3-horn-and-drum', 'Horn and drum', v3_horn_and_drum),
    ('4-blowing', 'Blowing', v4_blowing),
    ('5-cotton-candy', 'Cotton candy', v5_cotton_candy),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (-12 dB)', m.compose())]
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
    v3_mid().save(OUT / '3-horn-and-drum-at-0dB.png')
    print('wrote', OUT / 'sheet.png')


if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    main()


# ---- chosen: pink elephant ---------------------------------------------------------------------------------------------
# Picked under 5a: the cloud becomes something that could live there (a pink elephant), with an eye that wakes, and it
# trumpets: a playful literal reading of the horn side of the balance. The default is 0 dB (frame 0.5) and the painting
# must look as drawn there, so frames 0 to 0.5 are exactly as painted (nothing on the drum side) and the whole elephant
# arrives from 0.5 to +12 dB: ear and head form over the top lump (0.5-0.7), its eye opens sleepy and wakes (0.65-0.8),
# the trunk rises up and to the left (0.75-0.92), and the golden bell flares open, trumpeting, last (0.88-1). Head and
# ear are cloud-scalloped, with the painting's little black hooks at their joins, so it reads as the cloud turning into
# an elephant. Everything goes over the painting; none of it reaches the spikes, so they stay in front.
HEAD = (2370, 1085)
EYE = (2390, 1056, 40)
TRUNK = bez((2300, 1150), (2160, 1235), (2035, 1110), (2075, 900), 26)


def hook(x, y, deg, r=34, sign=1) -> str:
    """One of the painting's little cloud hooks: a short black curl tapering to a point (a filled shape, no line)."""
    P = []
    a0 = math.radians(deg)
    for k in range(14):
        u = k / 13
        a = a0 + sign * u * 2.4
        rr = r * (1 - 0.35 * u)
        P.append((x + math.cos(a) * rr - math.cos(a0) * r, y + math.sin(a) * rr - math.sin(a0) * r))
    return tube(P, 11, 3)


def bell_parts(tip, toward, base_w, rim_r, length):
    a = math.radians(toward)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    L = lambda s, t: (tip[0] + ux * s + nx * t, tip[1] + uy * s + ny * t)
    side = [(-10, base_w), (length * 0.45, base_w * 1.25), (length * 0.8, rim_r * 0.7), (length, rim_r)]
    P = [L(s, t) for s, t in side] + [L(s, -t) for s, t in side[::-1]]
    mx, my = L(length, 0)
    deg = math.degrees(a) + 90
    return [(closed(P[:4] + [L(length + 12, 0)] + P[4:]), BUTTER, INK),
            (oval(mx, my, rim_r, rim_r * 0.3, deg), ORANGE, INK * 0.8),
            (oval(mx - ux * 4, my - uy * 4, rim_r * 0.62, rim_r * 0.15, deg), PINK, 0)]


def cloudy(x, y, r, ry, n, seed, rot=0.0) -> str:
    """A cloud's outline, the painting's way: n round lumps of uneven size and height round (x, y)."""
    rnd = random.Random(seed)
    widths = [0.6 + rnd.random() * 0.8 for _ in range(n)]
    tot = sum(widths)
    P, a = [], rot
    for w in widths:
        span = w / tot * 2 * math.pi
        h = 0.1 + rnd.random() * 0.16
        for j in range(6):
            u = j / 6
            f = 1 + h * math.sin(u * math.pi) - 0.04
            aa = a + span * u
            P.append((x + math.cos(aa) * r * f, y + math.sin(aa) * ry * f))
        a += span
    return closed(P)


def it(d, fill, edge, at, s, e, out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': 'scale'}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


def elephant_items() -> list[dict]:
    items = []
    # the ear: a big scalloped lump behind the head, its inside a softer pink, two hooks at its joins
    ear_at = (2470, 1130)
    items.append(it(cloudy(2548, 1152, 148, 172, 6, 3, 0.3), CLOUD_D, INK, ear_at, 0.5, 0.64))
    items.append(it(lump(2565, 1165, 82, 4, 0.14, 9, 0, 108), '#ffb3d9', 0, ear_at, 0.53, 0.66))
    items.append(it(hook(2668, 1030, -40, 40, 1), '#000', 0, ear_at, 0.56, 0.66))
    items.append(it(hook(2700, 1250, 20, 40, 1), '#000', 0, ear_at, 0.58, 0.68))
    # the trunk, rising out of the head's front up and to the left; two soft wrinkle bands ride on it
    base = TRUNK[0]
    items.append(it(tube(TRUNK, 76, 46), CLOUD, INK, base, 0.75, 0.92))
    for u in (0.42, 0.58):
        i = int(u * (len(TRUNK) - 1))
        (ax, ay), (bx, by) = TRUNK[i - 1], TRUNK[i + 1]
        w = 76 + (46 - 76) * u
        items.append(it(oval(TRUNK[i][0], TRUNK[i][1], 12, w * 0.8, math.degrees(math.atan2(by - ay, bx - ax))), CLOUD_D, 0,
                        base, 0.75, 0.92))
    # the golden bell flaring open at the trunk's tip, last
    (ax, ay), (bx, by) = TRUNK[-3], TRUNK[-1]
    for d, fill, edge in bell_parts(TRUNK[-1], math.degrees(math.atan2(by - ay, bx - ax)) - 8, 44, 140, 170):
        items.append(it(d, fill, edge, TRUNK[-1], 0.88, 1.0))
    # the head over the top lump, cloud-scalloped, with a hook at a join and a cheek
    hx, hy = HEAD
    items.append(it(cloudy(hx, hy, 148, 128, 6, 21, -0.4), CLOUD, INK, (hx, hy + 25), 0.55, 0.7))
    items.append(it(hook(2280, 975, -150, 38, -1), '#000', 0, (hx, hy + 25), 0.6, 0.7))
    items.append(it(lump(2330, 1150, 45, 8, 0.1, 7, 0, 28), '#ffa0cf', 0, (2330, 1150), 0.62, 0.7))
    # a little cream tusk under the trunk, as the trunk lifts
    items.append(it(closed([(2265, 1185), (2205, 1250), (2140, 1268), (2185, 1222), (2235, 1170)]), '#fff6d6', INK * 0.8,
                    (2250, 1180), 0.8, 0.9))
    # the eye: opens sleepy under a heavy lid (0.65-0.7), the lid lifts away and the pupil looks up at the trunk
    ex, ey, r = EYE
    items.append(it(circle(ex, ey, r), '#ffffff', INK * 0.85, (ex, ey), 0.65, 0.7))
    items.append(it(circle(ex - 0.6 * r * 0.35, ey - 0.3 * r * 0.35, r * 0.48), '#111', 0, (ex - 8, ey - 4), 0.7, 0.8))
    items.append(it(circle(ex - 0.6 * r * 0.35 - r * 0.16, ey - 0.3 * r * 0.35 - r * 0.18, r * 0.15), '#ffffff', 0,
                    (ex - 14, ey - 11), 0.74, 0.8))
    lid = f'M{p(ex - r - 3, ey + r * 0.15)}A{r + 3:.1f} {r + 3:.1f} 0 0 1 {p(ex + r + 3, ey + r * 0.15)}Z'
    items.append(it(lid, CLOUD, INK * 0.85, (ex, ey - r), 0.65, 0.7, (0.7, 0.8)))
    return items


def elephant_frame(t: float) -> Image.Image:
    im = m.compose()
    if t > 0:
        im.alpha_composite(m.svg(g.sprite_svg(elephant_items(), t)))  # place 'over': above everything, ink included
    return im


def strip_of(frames, path, sc=0.42) -> list:
    tiles = [elephant_frame(t) for t in frames]
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
        d.text((x, 12), f'frame {tt:.2f}  ({-12 + 24 * tt:+.0f} dB)', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(path)
    return tiles


def elephant_main() -> None:
    out = OUT.parent / 'pink-elephant'
    out.mkdir(parents=True, exist_ok=True)
    tiles = strip_of([0, 0.25, 0.5, 0.75, 1.0], out / 'strip.png')
    tiles[-1].save(out / 'end-frame.png')
    strip_of([0.6, 0.7, 0.78, 0.86, 0.94], out / 'steps.png')
    print('wrote', out)


if __name__ == '__main__' and 'elephant' in __import__('sys').argv[1:]:
    elephant_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The pink cloud: drag across for the horn/drum balance; toward the horn it turns into a pink elephant: '
                 'its ear and head billow up, its sleepy eye wakes, its trunk rises and it trumpets through a golden bell',
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': elephant_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(elephant_items()), 'shapes')
