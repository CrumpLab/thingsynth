# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (upper drawbar 1 1/3', the larigot, fully out) for the tall white cloud at the right edge: a
column of scallops whose outline runs out past the painting's edge, behind the hat creature with the tan ears.

    uv run scripts/rightcloud_endframes.py
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
m.CROP = (3850, 230, 1100, 1640)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/upper-db8/endframes'
p, outlined, circle, tube, bez, smooth = m.p, m.outlined, g.circle, g.tube, g.bez, m.smooth
INK = 14
WHITE, CREAM = '#ffffff', '#fffbe6'
PINK, YELLOW, CYAN, LILAC, ORANGE, GREEN, MAGENTA, LIME = ('#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43',
                                                           '#7fd36b', '#FF1ABE', '#d4f55a')
# the hat creature in front of the cloud (body, brim, head, mouth, ears, eye) and the egg below it
CREATURE = ['f187', 'f195', 'f196', 'f197', 'f198', 'f199', 'f200', 'f188', 'f189']
# the cloud's scallops down its right edge, as (cx, cy, r)
LOBES = [(4560, 590, 75), (4585, 840, 95), (4600, 1060, 90), (4585, 1255, 90), (4570, 1430, 70)]


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


def blob(cx, cy, rx, ry, seed, wob=0.08, n=9, rot=0.0) -> str:
    """A lumpy hand-drawn oval."""
    rnd = random.Random(seed)
    a0, ca, sa = rnd.random() * 6.28, math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for k in range(n):
        a = a0 + k / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return smooth(pts)


def leaf(base, tip, w, bend=0.0, tipw=0.35) -> str:
    """A long lumpy petal or feather from base to tip, widest past the middle, with a soft round tip; `bend` curves it
    sideways (a fraction of its length)."""
    (x0, y0), (x1, y1) = base, tip
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    pt = lambda u, v: (x0 + ux * u * L + nx * (v + bend * L * math.sin(math.pi * u)), y0 + uy * u * L + ny * (v + bend * L * math.sin(math.pi * u)))
    pts = [pt(0, w * 0.45), pt(0.35, w * 0.85), pt(0.7, w), pt(0.93, w * tipw * 1.6), pt(1.0, 0), pt(0.93, -w * tipw * 1.6),
           pt(0.7, -w), pt(0.35, -w * 0.85), pt(0, -w * 0.45), pt(-0.06, 0)]
    return smooth(pts)


def fluff(cx, cy, r, seed, bumps=7) -> str:
    """A woolly scalloped clump: a ring of lumpy bumps round a centre, as one outline (drawn as bumps then a fill-only
    core so the inner outlines vanish)."""
    rnd = random.Random(seed)
    out, core = '', ''
    for k in range(bumps):
        a = k / bumps * 2 * math.pi + rnd.random() * 0.3
        rr = r * (0.42 + rnd.random() * 0.1)
        out += outlined(blob(cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62, rr, rr, seed * 31 + k, 0.1), WHITE, INK)
    core = f'<path d="{blob(cx, cy, r * 0.78, r * 0.78, seed, 0.05)}" fill="{WHITE}"/>'
    return out + core


def eye(cx, cy, r, look=(0.25, 0.1), iris=None) -> str:
    out = outlined(blob(cx, cy, r, r * 1.1, int(cx + cy), 0.04), WHITE, INK)
    if iris:
        out += outlined(circle(cx + r * look[0], cy + r * look[1], r * 0.55), iris, INK * 0.8)
    out += f'<path d="{circle(cx + r * look[0] * 1.2, cy + r * look[1] * 1.2, r * 0.3)}" fill="#000"/>'
    out += f'<path d="{circle(cx + r * look[0] * 1.2 + r * 0.12, cy + r * look[1] * 1.2 - r * 0.14, r * 0.1)}" fill="#fff"/>'
    return out


# ---- 1: flock of sheep -------------------------------------------------------------------------------------------
def sheep(cx, cy, r, seed, face=1) -> str:
    """A sheep made of a cloud lobe: woolly body, a big lilac-grey face poking out to one side with floppy ears, two
    stubby legs."""
    out = ''
    for dx in (-0.3, 0.35):
        out += outlined(tube([(cx + r * dx, cy + r * 0.5), (cx + r * dx + 8, cy + r * 1.3)], r * 0.13, r * 0.12), '#5b5470', INK * 0.85)
    out += fluff(cx, cy, r, seed)
    hx, hy = cx + face * r * 0.85, cy - r * 0.1
    out += outlined(blob(hx + face * r * 0.32, hy - r * 0.38, r * 0.3, r * 0.14, seed + 5, 0.08, rot=-25 * face), '#8e86b8', INK * 0.8)
    out += outlined(blob(hx - face * r * 0.3, hy - r * 0.4, r * 0.28, r * 0.13, seed + 6, 0.08, rot=25 * face), '#8e86b8', INK * 0.8)
    out += outlined(blob(hx, hy, r * 0.52, r * 0.66, seed + 7, 0.05, rot=-15 * face), '#8e86b8', INK)
    out += eye(hx - face * r * 0.14, hy - r * 0.12, r * 0.15, (0.3 * face, 0.1))
    out += eye(hx + face * r * 0.2, hy - r * 0.14, r * 0.14, (0.3 * face, 0.1))
    out += outlined(blob(hx + face * r * 0.08, hy + r * 0.32, r * 0.16, r * 0.1, seed + 8, 0.05), '#ff96a4', INK * 0.7)
    # a woolly forelock over the face's top
    out += outlined(blob(hx, hy - r * 0.5, r * 0.26, r * 0.16, seed + 9, 0.12), WHITE, INK * 0.8)
    return out


def v1_sheep() -> Image.Image:
    """Flock of sheep: each scallop down the cloud's right edge puffs into a woolly sheep, faces looking out of the
    painting, stubby legs dangling."""
    out = ''
    for k, (cx, cy, r) in enumerate([(4535, 590, 135), (4585, 850, 140), (4570, 1110, 135), (4600, 1360, 125)]):
        out += sheep(cx, cy, r, k + 1, face=1 if k % 2 == 0 else 1)
    return draw(out, CREATURE)


# ---- 2: the cloud whistles ---------------------------------------------------------------------------------------
def v2_whistle() -> Image.Image:
    """Whistling: the cloud wakes into a face down its visible column, two big eyes and pink puffed cheeks, its lips
    pursed out at the painting's edge, blowing a string of little cloud puffs out of the picture."""
    out = eye(4470, 900, 62, (0.4, -0.1), '#7cc4ff') + eye(4600, 880, 60, (0.45, -0.1), '#7cc4ff')
    for x, y in ((4465, 805), (4600, 785)):
        out += outlined(tube(bez((x - 55, y + 14), (x - 20, y - 14), (x + 20, y - 14), (x + 55, y + 8), 12), 12, 10), '#5b5470', INK * 0.6)
    out += outlined(blob(4470, 1040, 64, 46, 3, 0.06), '#ff9fc4', INK * 0.8)
    out += outlined(blob(4610, 1030, 60, 44, 4, 0.06), '#ff9fc4', INK * 0.8)
    # pursed lips: a pink ring with a dark hole, pushed out past the edge
    out += outlined(blob(4680, 1110, 66, 58, 5, 0.08), PINK, INK)
    out += outlined(blob(4692, 1110, 28, 25, 6, 0.08), '#5b2340', INK * 0.8)
    for k, (x, y, r) in enumerate([(4810, 1060, 70), (4880, 940, 58), (4905, 830, 46)]):
        out += fluff(x, y, r * 1.3, 40 + k, 6)
    return draw(out, CREATURE)


# ---- 3: cockatoo -------------------------------------------------------------------------------------------------
def v3_cockatoo() -> Image.Image:
    """Cockatoo: the cloud turns into a big white cockatoo; its top becomes a head with a hooked beak and a blue-ringed
    eye, a sulphur-yellow crest fans up, and the scallops down its side become the layered feathers of a wing."""
    out = ''
    # wing: big white feathers layered down the right side, rounded tops and soft points at the bottom
    for k in range(5):
        x0, y0 = 4555 + 22 * math.sin(k * 1.3), 760 + k * 130
        w_, h_ = 95 - k * 4, 260
        d = (f'M{p(x0 - w_, y0 + 40)}C{p(x0 - w_, y0 - 50)} {p(x0 + w_, y0 - 50)} {p(x0 + w_, y0 + 40)}'
             f'C{p(x0 + w_, y0 + h_ * 0.6)} {p(x0 + 30, y0 + h_ * 0.9)} {p(x0 - 10, y0 + h_)}'
             f'C{p(x0 - 40, y0 + h_ * 0.8)} {p(x0 - w_, y0 + h_ * 0.55)} {p(x0 - w_, y0 + 40)}Z')
        out += f'<g transform="rotate(-12 {x0:.0f} {y0:.0f})">' + outlined(d, WHITE if k % 2 == 0 else CREAM, INK) + '</g>'
    # crest: yellow feathers fanning up and back from the head
    hx, hy = 4490, 610
    for k, ang in enumerate((-150, -128, -106, -84, -62)):
        a = math.radians(ang)
        L = 280 + 30 * math.sin(k)
        b = (hx + math.cos(a) * 70, hy + math.sin(a) * 70)
        t = (hx + math.cos(a + 0.2) * L, hy + math.sin(a + 0.2) * L)
        out += outlined(leaf(b, t, 38, 0.08), YELLOW if k % 2 else '#ffd23f', INK)
    # head
    out += outlined(blob(hx, hy, 150, 135, 11, 0.04), WHITE, INK)
    # beak: a slate hooked upper bill over a lower one
    bx, by = hx + 125, hy + 25
    out += outlined(f'M{p(bx - 20, by + 30)}C{p(bx + 40, by + 70)} {p(bx + 90, by + 60)} {p(bx + 100, by + 20)}C{p(bx + 70, by + 40)} {p(bx + 20, by + 30)} {p(bx, by + 10)}Z', '#8e86b8', INK)
    out += outlined(f'M{p(bx - 30, by - 50)}C{p(bx + 60, by - 90)} {p(bx + 150, by - 30)} {p(bx + 120, by + 70)}C{p(bx + 100, by + 30)} {p(bx + 50, by + 10)} {p(bx - 25, by + 25)}Z', '#5b5470', INK)
    # eye with a pale blue ring
    out += outlined(blob(hx + 30, hy - 25, 52, 48, 12, 0.05), '#a8e6ff', INK * 0.8)
    out += f'<path d="{circle(hx + 38, hy - 25, 22)}" fill="#000"/><path d="{circle(hx + 44, hy - 33, 8)}" fill="#fff"/>'
    # a candy cheek
    out += outlined(blob(hx + 30, hy + 60, 38, 26, 13, 0.08), '#ff9fc4', INK * 0.6)
    return draw(out, CREATURE)


# ---- 4: fireworks ------------------------------------------------------------------------------------------------
def burst(cx, cy, R, cols, seed, n=9) -> str:
    """A firework flower: fat lumpy teardrop petals flung out round a centre, alternating candy colours, outlined,
    with round sparks off the petal tips."""
    rnd = random.Random(seed)
    out = ''
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.random() * 0.15
        L = R * (0.85 + rnd.random() * 0.2)
        b = (cx + math.cos(a) * R * 0.15, cy + math.sin(a) * R * 0.15)
        t = (cx + math.cos(a) * L * 0.82, cy + math.sin(a) * L * 0.82)
        out += outlined(leaf(b, t, R * 0.1, 0.1, 0.6), cols[k % len(cols)], INK * 0.8)
        out += outlined(blob(cx + math.cos(a + 0.08) * L * 1.02, cy + math.sin(a + 0.08) * L * 1.02, R * 0.14, R * 0.14, seed * 7 + k, 0.1),
                        cols[(k + 1) % len(cols)], INK * 0.8)
    out += outlined(blob(cx, cy, R * 0.22, R * 0.21, seed, 0.1), WHITE, INK * 0.9)
    return out


def v4_fireworks() -> Image.Image:
    """Fireworks: rockets shoot up out of the cloud's scallops trailing puffs, and burst into big candy firework
    flowers over it."""
    out = ''
    for (x0, y0), (x1, y1), r in [((4600, 1420), (4630, 1300), 40), ((4470, 1010), (4450, 860), 36)]:
        for k in range(3):
            u = k / 3
            out += outlined(blob(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, r * (0.6 + u * 0.5), r * (0.6 + u * 0.5), k + int(x0), 0.12), CREAM, INK * 0.8)
    out += burst(4500, 620, 200, [PINK, YELLOW, MAGENTA, ORANGE], 1)
    out += burst(4670, 930, 170, [CYAN, LILAC, '#7cc4ff', LIME], 2)
    out += burst(4600, 1220, 160, [ORANGE, LIME, YELLOW, PINK], 3)
    return draw(out, CREATURE)


# ---- 5: on its feet (1 1/3 foot) ---------------------------------------------------------------------------------
def stocking(P, w0, w1, cols, cid) -> str:
    d = tube(P, w0, w1)
    out = f'<defs><clipPath id="{cid}"><path d="{d}"/></clipPath></defs><path d="{d}" fill="{cols[0]}"/><g clip-path="url(#{cid})">'
    for k in range(2, len(P) - 1, 4):
        (x, y), (x2, y2) = P[k], P[k + 1]
        a = math.atan2(y2 - y, x2 - x)
        nx, ny = -math.sin(a), math.cos(a)
        out += f'<path d="{blob(x, y, 30, w0 * 1.6, k, 0.05, rot=math.degrees(a))}" fill="{cols[1]}" stroke="#000" stroke-width="{INK * 0.6}"/>'
    return out + f'</g><path d="{d}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'


def shoe(fx, fy, ang, col, s=1.15) -> str:
    g_ = f'<g transform="rotate({ang} {fx:.1f} {fy:.1f}) translate({fx:.1f} {fy:.1f}) scale({s})">'
    g_ += outlined(f'M{p(-70, -20)}C{p(-85, 60)} {p(40, 75)} {p(150, 60)}C{p(200, 55)} {p(190, -10)} {p(120, -25)}C{p(60, -40)} {p(30, -75)} {p(-70, -20)}Z', col, INK / s)
    g_ += outlined(f'M{p(-80, 30)}C{p(-20, 85)} {p(120, 85)} {p(195, 40)}L{p(190, 62)}C{p(120, 100)} {p(-30, 100)} {p(-82, 50)}Z', WHITE, INK * 0.8 / s)
    g_ += outlined(blob(30, -28, 36, 22, int(fx), 0.1), YELLOW, INK * 0.7 / s)
    return g_ + '</g>'


def v5_feet() -> Image.Image:
    """On its feet: the drawbar is a length in feet, so the cloud grows two candy-striped legs out of its bottom
    scallops and stands up on big sneakers, one stepping out of the painting."""
    out = ''
    legs = [(bez((4520, 1420), (4510, 1530), (4530, 1620), (4500, 1700), 16), PINK, 0, [CREAM, '#ff9fc4']),
            (bez((4610, 1400), (4660, 1460), (4690, 1530), (4710, 1600), 16), CYAN, -18, [CREAM, '#7cc4ff'])]
    for k, (P, col, ang, cols) in enumerate(legs):
        out += stocking(P, 50, 44, cols, f'leg{k}')
    for k, (P, col, ang, cols) in enumerate(legs):
        out += shoe(P[-1][0] - 20, P[-1][1] + 10, ang, col)
    # the cloud's bottom scallops redrawn over the tops of the legs, so they come out of it
    out += outlined(blob(4570, 1420, 110, 75, 7, 0.06), WHITE, INK)
    out += outlined(blob(4500, 1440, 60, 50, 8, 0.06), WHITE, INK)
    out += f'<path d="{blob(4555, 1400, 95, 60, 9, 0.04)}" fill="{WHITE}"/>'
    return draw('', [], out)


VERSIONS = [
    ('1-flock-of-sheep', 'Flock of sheep', v1_sheep),
    ('2-whistling', 'Whistling', v2_whistle),
    ('3-cockatoo', 'Cockatoo', v3_cockatoo),
    ('4-fireworks', 'Fireworks', v4_fireworks),
    ('5-on-its-feet', 'On its feet', v5_feet),
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


# ---- chosen: cockatoo (3), with a squawk on the last step ----------------------------------------------------------
# The upper 1 1/3' drawbar turns the cloud into a big white cockatoo, one arrival per drawbar step (k/8):
#   1-3  wing feathers come in over the cloud's scallops, two a step, top down (the lowest two pale sulphur);
#   4    a lumpy head rounds out on the cloud's top with a sleepy half-lidded eye;
#   5    the hooked beak;
#   6-8  the crest fans up feather by feather (two, two, one) and the eye wakes wide open on 6;
#   8    the beak opens in a squawk.
# Everything sits above the ink but masked by the hat creature (its body, brim, head, ears) so it stays in front;
# the cloud itself stays as the bird's body, and the new parts are kept inside the painting's right edge (x 4574).
STEP = 1 / 8
HEAD = (4430.0, 612.0)
EYE_C, EYE_R = (4463.0, 588.0), 33.0
SLATE, BILL, LID = '#5b5470', '#8e86b8', '#e4def7'
FRONT_IDS = ['f187', 'f188', 'f189', 'f195', 'f196', 'f197', 'f198', 'f200']


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 3),
         'end': round(e, 3), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 3), round(out[1], 3)
    return x


def lumpy(pts_fn, n, seed, wob) -> str:
    rnd = random.Random(seed)
    return smooth([pts_fn(k / n * 2 * math.pi, 1 + (rnd.random() - 0.5) * 2 * wob) for k in range(n)])


def wing_feather(x0, y0, w, h, rot, seed) -> str:
    """A big wing feather the painting's way: lumpy rounded top, slightly bulging sides, a soft point at the bottom."""
    rnd = random.Random(seed)
    j = lambda: (rnd.random() - 0.5) * w * 0.12
    pts = [(x0 - w * 0.95 + j(), y0 + h * 0.12), (x0 - w * 0.55 + j(), y0 - h * 0.06), (x0 + w * 0.1 + j(), y0 - h * 0.1),
           (x0 + w * 0.75 + j(), y0 - h * 0.02), (x0 + w * 1.0 + j(), y0 + h * 0.3), (x0 + w * 0.85 + j(), y0 + h * 0.66),
           (x0 + w * 0.45, y0 + h * 0.92), (x0 + w * 0.0, y0 + h), (x0 - w * 0.45, y0 + h * 0.9), (x0 - w * 0.9 + j(), y0 + h * 0.55)]
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    return smooth([(x0 + (x - x0) * ca - (y - y0) * sa, y0 + (x - x0) * sa + (y - y0) * ca) for x, y in pts])


def head_path() -> str:
    """The cockatoo's head: a lumpy round with a couple of soft feather tufts at the back of the crown and the cheek."""
    hx, hy = HEAD
    rnd = random.Random(21)
    pts = []
    n = 14
    for k in range(n):
        a = -math.pi / 2 + k / n * 2 * math.pi
        r = 1 + (rnd.random() - 0.5) * 0.12
        if k in (9, 11):  # tufts on the back of the head (upper left)
            r += 0.13
        if k in (1, 5):  # a lump on the crown's front and a fluffy cheek bump at the lower right
            r += 0.07
        pts.append((hx + math.cos(a) * 125 * r, hy + math.sin(a) * 115 * r))
    return smooth(pts)


def quill(P, w) -> str:
    """A crest feather along the centreline P: narrow at the root, widest past the middle, tapering to a round tip."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        ww = w * max(0.3, math.sin(math.pi * (0.2 + 0.72 * u)) ** 0.7)
        L.append((x + nx * ww, y + ny * ww))
        R.append((x - nx * ww, y - ny * ww))
    (ex, ey), (ax, ay) = P[-1], P[-2]
    d = math.hypot(ex - ax, ey - ay) or 1
    ux, uy = (ex - ax) / d, (ey - ay) / d
    re = math.hypot(L[-1][0] - ex, L[-1][1] - ey)
    cap = [(ex + (L[-1][0] - ex) * math.cos(t) + ux * re * math.sin(t), ey + (L[-1][1] - ey) * math.cos(t) + uy * re * math.sin(t))
           for t in (math.pi * 0.3, math.pi * 0.5, math.pi * 0.7)]
    return smooth(L[0:-1:3] + [L[-1]] + cap + [R[-1]] + R[::-1][3::3])


def crest_feathers() -> list[tuple[str, tuple, float, float, str]]:
    """(path, root, start, end, colour) for the five crest feathers: fanned back over the cloud's dome, uneven lengths,
    the tips curling forward; the tallest, middle one comes last."""
    hx, hy = HEAD
    spec = [  # root angle on the head, lean, length, width, hook, start, end, colour
        (-118, -128, 230, 30, 1.0, 0.64, 0.75, '#ffd23f'),
        (-98, -104, 200, 29, 1.15, 0.67, 0.75, YELLOW),
        (-135, -150, 185, 27, 0.9, 0.77, 0.875, YELLOW),
        (-80, -84, 160, 27, 1.2, 0.8, 0.875, '#ffd23f'),
        (-108, -117, 275, 34, 1.05, 0.89, 1.0, '#ffe98a'),
    ]
    out = []
    for ang, lean, Ln, w, hook, s, e, col in spec:
        a, b = math.radians(ang), math.radians(lean)
        root = (hx + math.cos(a) * 75, hy + math.sin(a) * 70)
        mid = (root[0] + math.cos(b) * Ln * 0.8, root[1] + math.sin(b) * Ln * 0.8)
        tip = (mid[0] + math.cos(b + hook) * Ln * 0.28, mid[1] + math.sin(b + hook) * Ln * 0.28)
        P = bez(root, (root[0] + math.cos(b) * Ln * 0.45, root[1] + math.sin(b) * Ln * 0.45),
                (mid[0] + math.cos(b) * Ln * 0.12, mid[1] + math.sin(b) * Ln * 0.12), tip, 24)
        out.append((quill(P, w), root, s, e, col))
    return out


def beak_paths() -> tuple[str, str, str, str]:
    """Upper bill, closed lower bill, open lower bill, and the open mouth's pink inside."""
    bx, by = HEAD[0] + 70, HEAD[1] + 5
    upper = (f'M{p(bx - 10, by - 42)}C{p(bx + 34, by - 66)} {p(bx + 84, by - 36)} {p(bx + 84, by + 14)}'
             f'C{p(bx + 84, by + 56)} {p(bx + 62, by + 92)} {p(bx + 40, by + 104)}C{p(bx + 46, by + 76)} {p(bx + 40, by + 48)} {p(bx + 20, by + 36)}'
             f'C{p(bx + 6, by + 30)} {p(bx - 6, by + 30)} {p(bx - 14, by + 26)}C{p(bx - 22, by + 2)} {p(bx - 22, by - 26)} {p(bx - 10, by - 42)}Z')
    lower = (f'M{p(bx - 12, by + 26)}C{p(bx + 8, by + 30)} {p(bx + 32, by + 42)} {p(bx + 46, by + 64)}'
             f'C{p(bx + 34, by + 84)} {p(bx + 4, by + 84)} {p(bx - 10, by + 68)}C{p(bx - 18, by + 56)} {p(bx - 18, by + 38)} {p(bx - 12, by + 26)}Z')
    lower_open = g.rot_path(lower, bx - 14, by + 28, 50)
    mouth = blob(bx + 16, by + 64, 36, 42, 17, 0.06)
    return upper, lower, lower_open, mouth


def bird_items() -> list[dict]:
    items = []
    # wing feathers: listed bottom first so the upper ones overlap the lower like shingles; they arrive top down
    wing = [(4478, 752, 86, 220, 14, WHITE), (4490, 852, 84, 228, 12, CREAM), (4484, 958, 82, 236, 14, WHITE),
            (4494, 1058, 78, 232, 12, CREAM), (4488, 1150, 74, 215, 14, '#fff6c2'), (4496, 1228, 64, 180, 12, '#ffef9e')]
    times = [(0.0, 0.11), (0.03, 0.125), (0.125, 0.235), (0.155, 0.25), (0.25, 0.36), (0.28, 0.375)]
    for k in range(5, -1, -1):
        x0, y0, w, h, rot, col = wing[k]
        s, e = times[k]
        items.append(it(wing_feather(x0, y0, w, h, rot, 30 + k), col, INK, (x0, y0 + h * 0.15), s, e))
    # crest, behind the head: roots hidden inside it
    for d, root, s, e, col in crest_feathers():
        items.append(it(d, col, INK, root, s, e))
    hx, hy = HEAD
    # head (step 4), grows from where it sits on the cloud
    items.append(it(head_path(), WHITE, INK, (hx, hy + 80), 0.375, 0.47))
    items.append(it(blob(hx + 10, hy + 62, 26, 18, 13, 0.1), '#ff9fc4', INK * 0.6, (hx + 10, hy + 62), 0.42, 0.5))
    # eye: a pale blue ring, the dark eye, a glint; a sleepy lid over its top half lifts away on step 6
    ex, ey = EYE_C
    items.append(it(blob(ex, ey, EYE_R, EYE_R * 0.95, 12, 0.05), '#a8e6ff', INK * 0.8, EYE_C, 0.4, 0.5))
    items.append(it(circle(ex + 6, ey + 2, EYE_R * 0.48), '#000', 0, EYE_C, 0.42, 0.5))
    items.append(it(circle(ex + 12, ey - 8, EYE_R * 0.16), '#fff', 0, EYE_C, 0.44, 0.5))
    r = EYE_R + 4
    lid = (f'M{p(ex - r, ey + 6)}C{p(ex - r, ey - r * 1.35)} {p(ex + r, ey - r * 1.35)} {p(ex + r, ey + 2)}'
           f'C{p(ex + r * 0.4, ey + 16)} {p(ex - r * 0.4, ey + 18)} {p(ex - r, ey + 6)}Z')
    items.append(it(lid, LID, INK * 0.8, (ex, ey - r), 0.4, 0.5, 'y', out=(0.64, 0.73)))
    # beak (step 5), then the squawk (step 8): the closed lower bill swaps for an open one round a pink mouth
    upper, lower, lower_open, mouth = beak_paths()
    bx, by = hx + 70, hy + 5
    items.append(it(mouth, '#e0466a', INK * 0.8, (bx - 8, by + 30), 0.9, 1.0))
    items.append(it(blob(bx + 14, by + 84, 17, 11, 7, 0.1), '#ff9fc4', INK * 0.6, (bx + 6, by + 66), 0.92, 1.0))
    items.append(it(lower_open, BILL, INK, (bx - 14, by + 28), 0.9, 1.0))
    items.append(it(lower, BILL, INK, (bx - 12, by + 26), 0.53, 0.625, out=(0.88, 0.94)))
    items.append(it(upper, SLATE, INK, (bx - 16, by), 0.5, 0.625))
    return items


def sprite_preview(items, t) -> str:
    """ghost_endframes.sprite_svg with the app's 'x' and 'y' growth too (same easing)."""
    out = ''
    for e in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - e['start']) / (e['end'] - e['start'])))) ** 3
        if 'outStart' in e:
            u = max(0.0, min(1.0, (t - e['outStart']) / (e['outEnd'] - e['outStart'])))
            v *= 1 - (1 - (1 - u) ** 3)
        if v <= 0.01:
            continue
        x, y = e['at']
        sc = f'{v:.4f} 1' if e['grow'] == 'x' else f'1 {v:.4f}' if e['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{e["edge"]}" stroke-linejoin="round"' if e['edge'] > 0 else ''
        out += f'<path d="{e["d"]}" fill="{e["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def bird_frame(t: float) -> Image.Image:
    """As the app draws it: the sprites above the ink, masked by the hat creature and the ear (with an ink-wide band)."""
    if t <= 0:
        return m.compose()
    x, y, w, h = m.CROP
    holes = ''.join(f'<path d="{m.FILLS[i]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for i in FRONT_IDS + ['f199'])
    body = (f'<defs><mask id="front" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/>{holes}</mask></defs>'
            f'<g mask="url(#front)">{sprite_preview(bird_items(), t)}</g>')
    return draw(body, [])


def bird_main() -> None:
    out = OUT.parent / 'cockatoo'
    out.mkdir(parents=True, exist_ok=True)
    bird_frame(1.0).save(out / 'end-frame.png')
    for frames, name in (([0, 0.25, 0.5, 0.75, 1.0], 'strip.png'), ([k / 8 for k in range(9)], 'steps.png')):
        tiles = [bird_frame(t) for t in frames]
        w, h = tiles[0].size
        sc = 0.42 if len(frames) == 5 else 0.3
        tw, th = int(w * sc), int(h * sc)
        strip = Image.new('RGB', (tw * len(frames) + 10 * len(frames) + 10, th + 56), 'white')
        try:
            font = ImageFont.load_default(size=24)
        except TypeError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3f}'.rstrip('0').rstrip('.') if name == 'steps.png' else f'frame {tt:.2f}', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        strip.save(out / name)
    print('wrote', out)


def build_json() -> dict:
    return {
        'label': 'The tall white cloud at the right edge: drag for the Upper 1 1/3\' drawbar; it turns into a cockatoo, wing '
                 'feathers, then a sleepy head and beak, then its crest fans up, its eye wakes and it squawks',
        'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['detail'], 'front': FRONT_IDS, 'items': bird_items()}],
    }


if __name__ == '__main__' and 'cockatoo' in __import__('sys').argv[1:]:
    bird_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    bp = ROOT / 'docs/objects/upper-db8/build.json'
    bp.write_text(_j.dumps(build_json(), indent=2) + '\n')
    print('exported', len(bird_items()), 'shapes to', bp)
