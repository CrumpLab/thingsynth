# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (manual mode at Upper) for the bunny slab: the stepped pink-and-peach slab at the bottom right,
three tiers rising to the right, a yellow hole in the low step, an orange hole in the middle step, and on the top
step an orange pot out of which the magenta bunny rises (tall ears, a sleepy half-lidded eye, a second lobe like an
arm leaning left).

    uv run scripts/slab_endframes.py          # the five end frames and sheet
    uv run scripts/slab_endframes.py hippo    # the chosen hippo jaw: progression strip, Split and end frames
    uv run scripts/slab_endframes.py export   # docs/objects/voice-manuals/build.json
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
m.CROP = (3150, 3330, 1500, 1320)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/voice-manuals/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 17      # the slab's and the bunny's own outlines
FINE = 12     # small features
# the painting's own colours here
PEACH, SALMON, ROSE = '#f0bc88', '#f08c81', '#d97aa8'
MAGENTA, VIOLET = '#ff19c8', '#a612f8'
EAR, EAR_IN, EYE, LID = '#DFA0A9', '#f6c9d0', '#D6FFFE', '#F04F65'
YELLOW, ORANGE, ORANGE2 = '#FFF832', '#FFB632', '#F08E4F'
CANDY = ['#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b']
DEFS = (f'<defs>'
        f'<linearGradient id="bun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{MAGENTA}"/>'
        f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
        f'<linearGradient id="slab" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SALMON}"/>'
        f'<stop offset="1" stop-color="{ROSE}"/></linearGradient>'
        f'</defs>')
HOLE_Y, HOLE_O = (3441.0, 4471.0), (3780.0, 4336.0)   # the yellow hole (f049) and the orange hole (f050)
POT = ['f051', 'f052']
BUNNY_EYE = ['f054', 'f057']
EARS = ['f055', 'f056']


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=DEFS + (front or '<g/>'))
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(DEFS + over))
    return im


def blob(P) -> str:
    """A closed Catmull-Rom curve through the points P: lumpy, hand-drawn."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def openline(P, move=True) -> str:
    """An open Catmull-Rom curve through P (for an outline left open where a part joins)."""
    n = len(P)
    d = f'M{p(*P[0])}' if move else f'L{p(*P[0])}'
    for i in range(n - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d


def lump(x, y, rx, ry, seed, wob=0.08, n=10, rot=0.0) -> str:
    rnd = random.Random(seed)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * c - v * s, y + u * s + v * c))
    return blob(P)


def egg(x, y, rx, ry, seed, rot=0.0) -> str:
    """An egg, narrower at the top, slightly lumpy."""
    rnd = random.Random(seed)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    P = []
    n = 14
    for k in range(n):
        a = k / n * 2 * math.pi
        u, v = math.cos(a), math.sin(a)
        w = rx * (1 - 0.18 * (-v if v < 0 else 0)) * (1 + (rnd.random() - 0.5) * 0.05)
        u, v = u * w, v * ry * (1 + (rnd.random() - 0.5) * 0.05)
        P.append((x + u * c - v * s, y + u * s + v * c))
    return blob(P)


def rot(pt, c, deg):
    a = math.radians(deg)
    x, y = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def sleepy_eye(x, y, rx, ry, deg=0.0, lid=0.45, ink=FINE) -> str:
    """The bunny's own eye: a pale cyan almond under a red lid that covers its top."""
    e = lump(x, y, rx, ry, int(x + y), 0.04, 12, deg)
    cid = f'e{int(x)}{int(y)}'
    top = y - ry * 1.3
    lid_d = (f'M{p(*rot((x - rx * 1.5, top), (x, y), deg))}L{p(*rot((x + rx * 1.5, top), (x, y), deg))}'
             f'L{p(*rot((x + rx * 1.5, y - ry + 2 * ry * lid), (x, y), deg))}'
             f'Q{p(*rot((x, y - ry + 2 * ry * lid + ry * 0.12), (x, y), deg))} {p(*rot((x - rx * 1.5, y - ry + 2 * ry * lid), (x, y), deg))}Z')
    return (f'<clipPath id="{cid}"><path d="{e}"/></clipPath>' + f'<path d="{e}" fill="{EYE}"/>'
            + f'<g clip-path="url(#{cid})">' + outlined(lid_d, LID, ink) + '</g>'
            + f'<path d="{e}" fill="none" stroke="#000" stroke-width="{ink * 1.15}" stroke-linejoin="round"/>')


def open_eye(x, y, rx, ry, deg=0.0, look=(0.0, -0.25), ink=FINE) -> str:
    """A wide-awake eye: pale white with a big dark pupil and a glint."""
    e = lump(x, y, rx, ry, int(x * 3 + y), 0.04, 12, deg)
    px, py = x + look[0] * rx, y + look[1] * ry
    r = min(rx, ry) * 0.55
    return (outlined(e, '#fbfff4', ink * 1.15) + f'<path d="{circle(px, py, r)}" fill="#1b0b2a"/>'
            + f'<path d="{circle(px - r * 0.35, py - r * 0.4, r * 0.28)}" fill="#fff"/>')


def ear(base, length, width, deg, seed) -> str:
    """A long lumpy bunny ear like the big bunny's own, rising from base (tucked behind the head: draw the head
    after it), with a paler inner ear."""
    bx, by = base
    a = math.radians(deg)
    cx, cy = bx + math.cos(a) * length * 0.5, by + math.sin(a) * length * 0.5
    outer = lump(cx, cy, length * 0.55, width * 0.5, seed, 0.05, 12, deg)
    ix, iy = bx + math.cos(a) * length * 0.55, by + math.sin(a) * length * 0.55
    inner = lump(ix, iy, length * 0.36, width * 0.17, seed + 9, 0.08, 10, deg + 2)
    return outlined(outer, EAR, INK) + outlined(inner, EAR_IN, FINE * 0.8)


# ---- 1. hippo: the slab is a lying beast, its upper jaw lifts ---------------------------------------------------------
HINGE = (3690.0, 4470.0)
JAW = 38.0


def v1_hippo() -> Image.Image:
    """The slab wakes up as a lying beast: the low step is its snout, the orange hole its eye. At Split its mouth
    splits open; at Upper the upper jaw lifts wide, showing a candy tongue and tusks, and the eye opens."""
    R = lambda q: rot(q, HINGE, JAW)
    out = ''
    # the mouth: a wedge between the jaws, back to the hinge
    mouth = blob([HINGE, R((3560, 4528)), R((3420, 4530)), R((3300, 4522)), (3325, 4395), (3292, 4515),
                  (3450, 4520), (3600, 4505)])
    out += outlined(mouth, '#b0105e', INK)
    # the lower jaw along the bottom, its underside on the slab's own bottom line
    low = blob([(3720, 4490), (3560, 4510), (3400, 4512), (3305, 4518), (3274, 4560), (3290, 4605), (3400, 4614),
                (3720, 4612)])
    out += outlined(low, 'url(#slab)', INK)
    out += outlined(lump(3450, 4500, 150, 48, 5, 0.06, 10, -3), '#f64c76', FINE)          # tongue
    out += outlined(lump(3470, 4486, 55, 15, 6, 0.1, 8, -6), '#ff8fb0', FINE * 0.7)       # its shine
    # two tusks standing up from the lower jaw's tip
    out += outlined(egg(3330, 4455, 34, 72, 1, -8), '#fff7da', FINE * 1.1)
    out += outlined(egg(3600, 4470, 28, 52, 2, 6), '#fff7da', FINE * 1.1)
    # the upper jaw: the old snout lobe, lifted round the hinge, two teeth hanging from it
    snout = [(3740, 4350), (3560, 4352), (3420, 4346), (3320, 4356), (3272, 4410), (3282, 4490), (3335, 4528),
             (3480, 4532), (3620, 4524), (3740, 4500)]
    for q, h in (((3340, 4560), 62), ((3540, 4560), 48)):
        c = R(q)
        out += outlined(egg(c[0], c[1], 30, h, int(q[0]), JAW + 180), '#fff7da', FINE * 1.1)
    out += outlined(blob([R(q) for q in snout]), 'url(#slab)', INK)
    nost = m.FILLS['f049']   # the yellow nostril rides up with it
    out += (f'<g transform="rotate({JAW} {HINGE[0]} {HINGE[1]}) translate(-100 -28)"><path d="{nost}" fill="{YELLOW}" '
            f'stroke="#000" stroke-width="{FINE}" stroke-linejoin="round"/></g>')
    # a round jowl over the hinge, melting the seam
    out += outlined(lump(3720, 4470, 110, 100, 11, 0.07, 10), 'url(#slab)', INK)
    # the eye: a brow bump swells on the middle step, the orange hole opening into a wide eye looking up
    out += outlined(lump(3800, 4255, 170, 135, 12, 0.07, 11), 'url(#slab)', INK)
    out += open_eye(3800, 4255, 108, 84, -6, (0.18, -0.2))
    lid = f'M{p(3682, 4222)}C{p(3712, 4135)} {p(3890, 4125)} {p(3920, 4205)}C{p(3860, 4180)} {p(3740, 4183)} {p(3682, 4222)}Z'
    out += outlined(lid, ORANGE, FINE)
    return draw(out, [])


# ---- 2. bunny family: two more bunnies pop out of the holes -------------------------------------------------------
def ring(x, y, rx, ry, outer, inner, seed) -> tuple[str, str]:
    """A pot rim like the bunny's own: returns (back of the rim and its hole, front lip to lay over a body)."""
    o = lump(x, y, rx, ry, seed, 0.05, 12)
    i = lump(x, y - ry * 0.12, rx * 0.74, ry * 0.58, seed + 1, 0.05, 12)
    back = outlined(o, outer, INK) + outlined(i, inner, FINE * 1.1)
    # the front lip: the lower half of the rim, between the inner hole's bottom and the rim's bottom
    lip = (f'M{p(x - rx * 0.99, y + 2)}C{p(x - rx * 0.95, y + ry * 1.35)} {p(x + rx * 0.95, y + ry * 1.35)} {p(x + rx * 0.99, y + 2)}'
           f'C{p(x + rx * 0.72, y + ry * 0.62)} {p(x - rx * 0.72, y + ry * 0.62)} {p(x - rx * 0.99, y + 2)}Z')
    return back, outlined(lip, outer, INK)


def little_bunny(x, y, h, w, seed, lean=0.0, awake=False) -> str:
    """A small copy of the bunny rising from (x, y): a magenta-to-violet tube head, two ears, a sleepy eye."""
    rnd = random.Random(seed)
    top = y - h
    P = [(x - w * 0.5, y + 20), (x - w * 0.52, y - h * 0.4), (x - w * 0.42 + lean * 0.5, top + w * 0.35),
         (x - w * 0.1 + lean, top + 4), (x + w * 0.25 + lean, top + 10), (x + w * 0.48 + lean * 0.5, top + w * 0.4),
         (x + w * 0.5, y - h * 0.45), (x + w * 0.48, y + 20)]
    P = [(a + (rnd.random() - 0.5) * 8, b + (rnd.random() - 0.5) * 8) for a, b in P]
    head = blob(P)
    out = ear((x - w * 0.2 + lean, top + 60), h * 0.8, w * 0.5, -104 - rnd.random() * 6, seed)
    out += ear((x + w * 0.22 + lean, top + 60), h * 0.88, w * 0.46, -76 + rnd.random() * 6, seed + 1)
    out += outlined(head, 'url(#bun)', INK)
    ex, ey = x + w * 0.06 + lean * 0.6, top + h * 0.42
    out += open_eye(ex, ey, w * 0.2, h * 0.17, 0, (0.1, -0.2)) if awake else sleepy_eye(ex, ey, w * 0.25, h * 0.25, 0, 0.45)
    return out


def v2_family() -> Image.Image:
    """Bunny family: the holes turn into pots like the big bunny's own, and a bunny pops out of each, the middle one
    at Split, the low one at Upper, ears up, sleepy-eyed like their parent."""
    out = ''
    for (x, y), (outer, inner), h, w, lean, seed in (
            (HOLE_O, (ORANGE, '#c8642a'), 380, 200, -14, 21),
            (HOLE_Y, (YELLOW, '#d9a520'), 330, 185, 12, 31)):
        back, front = ring(x, y, 172, 76, outer, inner, seed)
        out += back + little_bunny(x, y - 4, h, w, seed, lean) + front
    return draw(out, [])


# ---- 3. easter eggs: the holes swell into big candy eggs, and the pot fills with them -----------------------------
def candy_egg(x, y, rx, ry, base, bands, seed, rot_=0.0) -> str:
    e = egg(x, y, rx, ry, seed, rot_)
    cid = f'g{seed}'
    out = f'<clipPath id="{cid}"><path d="{e}"/></clipPath><path d="{e}" fill="{base}"/><g clip-path="url(#{cid})" transform="rotate({rot_} {x} {y})">'
    rnd = random.Random(seed)
    for k, (col, kind) in enumerate(bands):
        cy = y - ry * 0.55 + k * ry * 0.62
        hgt = ry * 0.24
        if kind == 'zig':
            n = 7
            top = ''.join(f'L{p(x - rx * 1.2 + i * rx * 2.4 / n, cy - hgt * (0.5 if i % 2 else -0.1))}' for i in range(n + 1))
            bot = ''.join(f'L{p(x + rx * 1.2 - i * rx * 2.4 / n, cy + hgt * (0.9 if i % 2 else 0.4))}' for i in range(n + 1))
            d = f'M{p(x - rx * 1.2, cy)}{top}{bot}Z'
        else:
            pts = [(x - rx * 1.3 + i * rx * 0.4, cy + (hgt * 0.35 if i % 2 else -hgt * 0.35)) for i in range(8)]
            pts2 = [(a, b + hgt) for a, b in pts[::-1]]
            d = openline(pts) + openline(pts2, False) + 'Z'
        out += outlined(d, col, FINE * 0.9)
    for k, (u, v) in enumerate(((-0.45, -0.05), (0.42, 0.62), (0.35, -0.72))):
        out += outlined(lump(x + u * rx, y + v * ry, rx * 0.17, rx * 0.15, seed + k, 0.1, 8),
                        CANDY[(seed + k) % 6], FINE * 0.8)
    out += '</g>'
    return out + f'<path d="{e}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'


def v3_eggs() -> Image.Image:
    """Easter eggs: the yellow and orange holes swell up into big candy-banded eggs (orange at Split, yellow at
    Upper), and the bunny's pot becomes a basket heaped with eggs round it."""
    out = ''
    # eggs in the basket, behind the pot's front (re-laid) and beside the bunny
    basket = candy_egg(4060, 4170, 92, 118, '#2DFFF4', [('#f64c76', 'wave'), ('#ffe066', 'zig')], 51, -24)
    basket += candy_egg(4400, 4170, 88, 112, '#7fd36b', [('#ffe066', 'zig'), ('#c4a3f0', 'wave')], 52, 20)
    out += candy_egg(3780, 4205, 118, 152, ORANGE, [('#c4a3f0', 'wave'), ('#f64c76', 'zig')], 53)
    out += candy_egg(3441, 4345, 128, 165, YELLOW, [('#f64c76', 'zig'), ('#2DFFF4', 'wave')], 54, -5)
    return draw(basket, ['f051'], out)


# ---- 4. two manuals: the steps turn into two stacked keyboards ----------------------------------------------------
def keyboard(x0, x1, y_top, depth, n, seed, sharps=(1, 2, 4, 5)) -> str:
    """A row of n big lumpy white keys from x0 to x1, their front faces from y_top down by depth, with candy
    black keys sitting between some of them, and a slab-coloured key bed behind."""
    rnd = random.Random(seed)
    w = (x1 - x0) / n
    bed = blob([(x0 - 40, y_top - 70), (x1 + 40, y_top - 82), (x1 + 52, y_top + depth * 0.5), (x1 + 40, y_top + depth + 20),
                (x0 - 40, y_top + depth + 26), (x0 - 54, y_top + depth * 0.5)])
    out = outlined(bed, 'url(#slab)', INK)
    for k in range(n):
        a, b = x0 + k * w + 6, x0 + (k + 1) * w - 6
        j = lambda: (rnd.random() - 0.5) * 8
        key = blob([(a + j(), y_top - 40 + j()), ((a + b) / 2, y_top - 46 + j()), (b + j(), y_top - 40 + j()),
                    (b + 2 + j(), y_top + depth * 0.5), (b + j(), y_top + depth + j()), ((a + b) / 2, y_top + depth + 6),
                    (a + j(), y_top + depth + j()), (a - 2 + j(), y_top + depth * 0.5)])
        out += outlined(key, '#fffaf0', INK * 0.85)
    for k in sharps:
        if k >= n:
            continue
        cx = x0 + k * w
        sk = blob([(cx - w * 0.3, y_top - 52), (cx + w * 0.3, y_top - 54), (cx + w * 0.32, y_top + depth * 0.3), (cx + w * 0.22, y_top + depth * 0.5), (cx - w * 0.24, y_top + depth * 0.5), (cx - w * 0.33, y_top + depth * 0.3)])
        out += outlined(sk, '#c20fa0' if k % 2 else VIOLET, INK * 0.8)
    return out


def v4_manuals() -> Image.Image:
    """Two manuals: the slab's steps turn into an organ console, a lower keyboard along the low step and an upper
    keyboard rising behind it on the middle step (the lower one at Split, the upper at Upper)."""
    out = keyboard(3410, 3990, 4205, 150, 6, 7)       # upper manual, set back and higher
    out += keyboard(3300, 3900, 4440, 165, 6, 3, (1, 2, 4))      # lower manual, in front
    return draw(out, ['f051', 'f052'])


# ---- 5. twins: the bunny splits into two ------------------------------------------------------------------------
def v5_twins() -> Image.Image:
    """Split in two: the bunny's leaning lobe becomes a second head of its own, ears sprouting, and both wake and
    look at each other (it divides at Split, both wake at Upper)."""
    out = ''
    out += ear((3935, 3745), 300, 110, -118, 61)
    out += ear((3990, 3735), 320, 100, -88, 62)
    # a cap over the lobe's top so the ears grow out of it seamlessly
    cap = blob([(3884, 3800), (3880, 3740), (3915, 3700), (3970, 3690), (4020, 3712), (4040, 3760), (4030, 3800),
                (3960, 3820)])
    out += f'<path d="{cap}" fill="{MAGENTA}" opacity="0.92"/>'
    out += f'<path d="{openline([(3884, 3812), (3880, 3740), (3915, 3700), (3970, 3690), (4020, 3712), (4040, 3762)])}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
    out += open_eye(3945, 3860, 52, 80, -18, (0.35, -0.1))
    # the big bunny wakes too, looking back at its twin
    big = open_eye(4316, 3842, 70, 172, 2, (-0.4, -0.15))
    return draw(out, [], big)


VERSIONS = [
    ('1-hippo', 'Hippo jaw', v1_hippo),
    ('2-bunny-family', 'Bunny family', v2_family),
    ('3-easter-eggs', 'Easter eggs', v3_eggs),
    ('4-two-manuals', 'Two manuals', v4_manuals),
    ('5-twins', 'Split in two', v5_twins),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Channels)', m.compose())]
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


# ---- chosen: hippo jaw, with the bunny waking ----------------------------------------------------------------------
# Picked under 5a: the slab itself becomes a creature (its low step the snout, the orange hole an eye), the switch read
# literally: at Split its mouth splits open, at Upper the upper jaw lifts. Two arrivals on an 800 ms glide. A sprite
# cannot rotate, so the jaw comes as poses: closed (covering the painted snout), cracked (Split), wide (Upper), each
# shrinking out as the next grows in from the hinge.
#   0-0.15   the closed snout and lower jaw cover the painted lobe (its yellow hole fading under them), the jowl and
#            a brow bump swell over the middle step (the orange hole fading under it)
#   0.12-0.4 the eye opens: white, then the orange lid, then the pupil looking up at the bunny
#   0.28-0.46 the jaw cracks open: the cracked pose grows from the hinge over the closed one, a dark wedge inside
#   0.6-0.8  the upper jaw swings up wide; the mouth, tongue, then chunky tusks and teeth come in (0.7-0.92)
#   0.82-1   the bunny on its back wakes: a tall wide-open eye over its sleepy one, the pupil looking down at the hippo
SLAB_C, JAW_C, MOUTH_C, TONGUE_C, TOOTH_C = '#ec8f96', '#df7f9c', '#b0105e', '#f64c76', '#fff7da'
WHITE_C, PUPIL_C = '#fbfff4', '#1b0b2a'
HIP = (3700.0, 4470.0)   # the jaw's hinge
SNOUT = [(3770, 4330), (3650, 4312), (3530, 4326), (3410, 4310), (3305, 4330), (3240, 4382), (3228, 4452),
         (3256, 4512), (3330, 4538), (3470, 4542), (3612, 4532), (3770, 4506)]
LOWER = [(3770, 4498), (3610, 4515), (3450, 4522), (3300, 4526), (3238, 4556), (3256, 4606), (3400, 4617),
         (3580, 4613), (3770, 4612)]
NOSTRIL = (3318, 4392)
POSES = [(0.0, (0.0, 0.1), (0.32, 0.46)), (13.0, (0.28, 0.46), (0.62, 0.76)), (40.0, (0.6, 0.8), None)]


def jaw_shapes(a: float) -> tuple[str, str, str]:
    """The upper jaw lifted a degrees round the hinge: (jaw, nostril, the mouth wedge behind it)."""
    R = lambda q: rot(q, HIP, a)
    jaw = blob([R(q) for q in SNOUT])
    nx, ny = R(NOSTRIL)
    nost = lump(nx, ny, 78, 46, 49, 0.06, 10, a - 8)
    tip_up, tip_lo = R((3262, 4512)), (3256, 4524)
    mid = ((tip_up[0] + tip_lo[0]) / 2 + 22, (tip_up[1] + tip_lo[1]) / 2)
    wedge = blob([(HIP[0], HIP[1] - 30), R((3612, 4532)), R((3470, 4542)), R((3330, 4538)), tip_up, mid, tip_lo,
                  (3330, 4524), (3470, 4520), (3620, 4508)])
    return jaw, nost, wedge


def hippo_items() -> list[dict]:
    it = lambda d, fill, edge, at, s, e, out=None: (lambda o: o)(
        {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': s, 'end': e,
         'grow': 'scale', **({'outStart': out[0], 'outEnd': out[1]} if out else {})})
    items = [it(blob(LOWER), JAW_C, INK, (3500, 4560), 0.0, 0.1)]
    for k, (a, (s, e), out) in enumerate(POSES):
        jaw, nost, wedge = jaw_shapes(a)
        at = (3500, 4430) if a == 0 else HIP
        if a:
            items.append(it(wedge, MOUTH_C, INK, HIP, s - 0.02, e - 0.04, out))
        if a == 40.0:
            items.append(it(lump(3455, 4500, 165, 52, 5, 0.07, 10, -3), TONGUE_C, FINE, (3620, 4505), 0.7, 0.84))
            items.append(it(lump(3480, 4486, 62, 17, 6, 0.1, 8, -6), '#ff8fb0', 0, (3620, 4505), 0.74, 0.86))
            for (x, base, h, d) in ((3322, 4528, 140, -8), (3575, 4516, 108, 6)):   # chunky tusks from the lower jaw
                items.append(it(egg(x, base - h * 0.42, 46, h * 0.52, int(x), d), TOOTH_C, FINE * 1.1, (x, base), 0.74, 0.88))
            for (q, h) in (((3345, 4538), 92), ((3540, 4542), 78)):                 # chunky teeth hanging from the upper jaw
                r0 = rot(q, HIP, a)
                c = rot((q[0], q[1] + h * 0.42), HIP, a)
                items.append(it(egg(c[0], c[1], 42, h * 0.52, int(q[0]), a + 180), TOOTH_C, FINE * 1.1, r0, 0.76, 0.9))
        items.append(it(jaw, SLAB_C, INK, at, s, e, out))
        items.append(it(nost, YELLOW, FINE, at, s, e, out))
    items.append(it(lump(3735, 4462, 132, 118, 11, 0.09, 10), SLAB_C, INK, (3735, 4520), 0.03, 0.15))      # jowl
    items.append(it(lump(3785, 4265, 182, 152, 12, 0.09, 11), SLAB_C, INK, (3785, 4380), 0.0, 0.15))      # brow
    eye = lump(3790, 4265, 122, 96, 13, 0.05, 12, -6)
    items.append(it(eye, WHITE_C, FINE * 1.2, (3790, 4265), 0.12, 0.28))
    items.append(it(circle(3818, 4240, 52), PUPIL_C, 0, (3818, 4240), 0.24, 0.38))
    items.append(it(circle(3800, 4218, 16), '#ffffff', 0, (3800, 4218), 0.3, 0.4))
    lid = (f'M{p(3652, 4236)}C{p(3680, 4132)} {p(3890, 4116)} {p(3928, 4208)}C{p(3858, 4176)} {p(3720, 4184)} '
           f'{p(3652, 4236)}Z')
    items.append(it(lid, ORANGE, FINE, (3788, 4172), 0.18, 0.34))
    # the bunny wakes: a tall wide-open eye over its sleepy one, looking down at the hippo
    beye = lump(4318, 3842, 66, 172, 14, 0.04, 12, 2)
    items.append(it(beye, WHITE_C, INK, (4318, 3842), 0.82, 0.94))
    items.append(it(circle(4290, 3868, 44), PUPIL_C, 0, (4290, 3868), 0.88, 0.98))
    items.append(it(circle(4276, 3852, 13), '#ffffff', 0, (4276, 3852), 0.92, 1.0))
    for o in items:
        o['start'], o['end'] = round(max(0.0, o['start']), 3), round(min(1.0, o['end']), 3)
    return items


HIPPO_VANISH = [('snout', 'f049', (0.04, 0.1)), ('eye', 'f050', (0.05, 0.13))]


def hippo_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    gone = [f for _, f, (a, b) in HIPPO_VANISH if t >= (a + b) / 2]
    im = m.compose(fill_over={f: 'M0 0Z' for f in gone}, ink_over={i: 'M0 0Z' for f in gone for i in m.own_ink(f)})
    im.alpha_composite(m.svg(g.sprite_svg(hippo_items(), t)))
    return im


def hippo_main() -> None:
    out = OUT.parent / 'hippo-jaw'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [hippo_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    tiles[2].save(out / 'split-frame.png')
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * 5 + 60, th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    names = {0: ' (Channels)', 0.5: ' (Split)', 1.0: ' (Upper)'}
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.2f}{names.get(tt, "")}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    print('wrote', out)


if __name__ == '__main__' and 'hippo' in __import__('sys').argv[1:]:
    hippo_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': ("The bunny slab shows the manual mode (display only: it changes which keys play which manual); it wakes as a hippo, its eye opening and its mouth "
                  "splitting open at Split, its upper jaw lifting wide at Upper as the bunny on its back wakes"),
        'glide': 800,
        'effects': [{'effect': 'vanish', 'parts': [role], 'span': list(span)} for role, _, span in HIPPO_VANISH]
                   + [{'effect': 'sprites', 'place': 'over', 'items': hippo_items()}],
        'objectParts': {role: [f] for role, f, _ in HIPPO_VANISH},
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(hippo_items()), 'shapes')
