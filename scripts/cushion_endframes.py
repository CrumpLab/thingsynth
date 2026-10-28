# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Pedal 8' drawbar fully out) for the left cushion: the big soft two-lobed mound, lower left,
between the pink figure and the orange caps, with the eye tree's stalks planted in the dip of its top edge.

    uv run scripts/cushion_endframes.py          # the five end frames and sheet
    uv run scripts/cushion_endframes.py octo     # the chosen octopus: progression strip and end frame
    uv run scripts/cushion_endframes.py export   # docs/objects/pedal-db8/build.json
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (376, 2780, 1364, 1170)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/pedal-db8/endframes'
p, outlined, circle, tube, bez, spiral = m.p, m.outlined, g.circle, g.tube, g.bez, g.spiral
INK = 15
BODY = 'f137'
MAG, MAG2, MAGD = '#ff4fcf', '#ff8fe0', '#c21a9a'
BUTTER, MINT, CYAN, LILAC, ORANGE = '#ffe066', '#7fe0c8', '#2DFFF4', '#c4a3f0', '#ff9f43'
# painted shapes in front of the cushion (opaque ones only: re-laying a see-through fill would darken it)
PINK_FIG, YELLOW, CAP, LOWER_CAP, CYAN_CREATURE = 'f099', 'f102', 'f012', 'f011', 'f001'
STALKS = ['f114', 'f115']


def draw(front: str = '', again: list[str] | None = None, over: str = '', recolour: str = '') -> Image.Image:
    """New shapes drawn, then the named painted shapes (and their ink) laid back on top; `over` goes on top of all.
    With `recolour`, the cushion's see-through fill is painted solid in that colour (its ink stays)."""
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    pyr = m.PYR
    try:
        if recolour:
            m.PYR = [BODY]
            im = m.compose(front=front or '<g/>', fill_colour={BODY: recolour}, pyr_opaque=True)
        else:
            im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK, m.PYR = [], [], pyr
    if over:
        im.alpha_composite(m.svg(over))
    return im


def closed(P) -> str:
    """A smooth closed curve through the points P (Catmull-Rom)."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, rx, ry=None, seed=0, wob=0.1, n=10, rot=0.0) -> str:
    """A lumpy hand-drawn oval round (x, y), radii rx, ry, turned by rot degrees."""
    ry = ry or rx
    rnd = random.Random(seed)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * c - v * s, y + u * s + v * c))
    return closed(P)


def eye(cx, cy, r, look=(0.15, 0.2), iris=LILAC) -> str:
    """A big round waking eye: white, coloured iris, black pupil, a glint."""
    ix, iy = cx + look[0] * r, cy + look[1] * r
    out = outlined(lump(cx, cy, r, r * 1.05, int(cx), 0.05, 9), '#ffffff', INK)
    out += outlined(circle(ix, iy, r * 0.52), iris, INK * 0.8)
    out += f'<path d="{circle(ix, iy, r * 0.26)}" fill="#000"/><path d="{circle(ix + r * 0.14, iy - r * 0.14, r * 0.1)}" fill="#fff"/>'
    return out


def tentacle(P, w0, w1, colour, sucker, seed) -> str:
    """A fat tentacle along P, tapering faster toward its tip, with a few big pale suckers along its underside."""
    n = len(P)
    W = [w1 + (w0 - w1) * (1 - i / (n - 1)) ** 1.4 for i in range(n)]
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
        L.append((x + nx * W[i], y + ny * W[i]))
        R.append((x - nx * W[i], y - ny * W[i]))
    d = closed_open(L) + f'A{W[-1]:.1f} {W[-1]:.1f} 0 0 1 {p(*R[-1])}' + closed_open(R[::-1], move=False) + 'Z'
    out = outlined(d, colour, INK)
    rnd = random.Random(seed)
    for k in (0.22, 0.4, 0.56):
        i = int(k * (n - 1))
        a, b = P[i - 1], P[i + 1]
        dd = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / dd, (b[0] - a[0]) / dd
        x, y = P[i][0] - nx * W[i] * 0.42, P[i][1] - ny * W[i] * 0.42
        out += outlined(lump(x, y, W[i] * 0.36, W[i] * 0.3, seed * 7 + i, 0.08, 8, rnd.random() * 90), sucker, INK * 0.6)
    return out


def closed_open(P, move=True) -> str:
    """A smooth open curve through P (Catmull-Rom), starting with M (or continuing with L)."""
    d = (f'M{p(*P[0])}' if move else f'L{p(*P[0])}')
    for i in range(len(P) - 1):
        p0, p1, p2 = P[max(0, i - 1)], P[i], P[i + 1]
        p3 = P[min(len(P) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d


def curl_arm(root, mid, end, r0, sign, turns=0.85) -> list:
    """A centreline: a curve out from the root that rolls into a curl at its end."""
    P = bez(root, mid, mid, end, 14)
    a = math.atan2(end[1] - mid[1], end[0] - mid[0])
    return P + spiral(end[0], end[1], a, r0, turns, 0.55, sign, 16)[1:]


# ---- 1: octopus ----------------------------------------------------------------------------------------------------
def v1_octopus() -> Image.Image:
    """Octopus: an octave up = octo: the cushion turns into a magenta octopus, eight fat tentacles curling out from
    behind its edges and two big eyes waking on its front lobe."""
    arms = [
        ((750, 3340), (650, 3400), (570, 3380), 55, 1),     # left, over the orange cap
        ((850, 3250), (820, 3120), (870, 3010), 55, 1),     # up beside the stalks
        ((1360, 3330), (1430, 3220), (1520, 3150), 60, -1),  # up and right
        ((1270, 3580), (1420, 3610), (1540, 3540), 60, -1),  # right
        ((1280, 3700), (1400, 3790), (1500, 3840), 55, -1),  # down right
        ((1170, 3650), (1190, 3790), (1120, 3870), 55, 1),   # down
        ((1020, 3620), (960, 3760), (860, 3820), 55, 1),     # down left, over the cyan creature
        ((975, 3560), (860, 3650), (720, 3660), 55, 1),      # left, low, over the orange cap
    ]
    arms_svg = ''
    for k, (root, mid, end, r0, sign) in enumerate(arms):
        arms_svg += tentacle(curl_arm(root, mid, end, r0, sign), 56, 13, MAG, MAG2, k + 1)
    face = eye(1135, 3480, 72, (0.1, 0.15)) + eye(1250, 3425, 66, (0.1, 0.2))
    return draw(arms_svg + body_over(MAG), [], face, recolour=MAG)


# the cushion's own outline strokes: the back lobe's top edge and the front lobe's (the crease)
OUTLINE = ['i1129', 'i0289', 'i1124', 'i0283']


def body_over(colour: str) -> str:
    """The cushion's fill again, solid, over the roots of whatever grows out of it, and its own outline back on top,
    so new parts come out from behind its edges with no seam."""
    return f'<path d="{m.FILLS[BODY]}" fill="{colour}"/><g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in OUTLINE) + '</g>'


# ---- 2: singing ----------------------------------------------------------------------------------------------------
def v2_singing() -> Image.Image:
    """Singing: the cushion wakes up and sings the bass: two round eyes open on its front lobe under raised brows,
    and a big round mouth opens below them, tongue and all, its cheeks flushing."""
    out = ''
    out += outlined(lump(1085, 3575, 46, 32, 5, 0.08, 8), '#ff8fb8', INK * 0.8)
    out += outlined(lump(1285, 3540, 40, 30, 6, 0.08, 8), '#ff8fb8', INK * 0.8)
    out += eye(1125, 3455, 68, (0.0, -0.25)) + eye(1245, 3405, 62, (0.0, -0.25))
    # raised brows: fat outlined crescents
    for cx, cy, r in ((1120, 3362, 78), (1248, 3312, 70)):
        P = [(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r * 0.55) for a in range(200, 341, 10)]
        out += outlined(tube(P, 14, 9), MAGD, INK * 0.7)
    mouth = lump(1195, 3585, 90, 74, 11, 0.07, 9, -12)
    out += outlined(mouth, '#6a0f3a', INK)
    out += outlined(lump(1203, 3625, 54, 30, 12, 0.1, 8, -10), '#ff6f91', INK * 0.7)
    return draw('', [], out)


# ---- 3: bouncy castle ----------------------------------------------------------------------------------------------
def turret(x, base, w, h, colour, trim, flag, seed) -> str:
    """A puffy inflatable tower standing on (x, base): a fat lumpy column, a ring of round bumps for battlements, a
    rounded cone roof and a pennant."""
    rnd = random.Random(seed)
    top = base - h
    col = closed([(x - w * 0.5, base), (x - w * 0.6, base - h * 0.5), (x - w * 0.46, top + 6), (x, top - 12),
                  (x + w * 0.46, top + 6), (x + w * 0.6, base - h * 0.5), (x + w * 0.5, base), (x, base + 20)])
    out = outlined(col, colour, INK)
    out += outlined(lump(x, base - h * 0.5, w * 0.2, w * 0.22, seed, 0.06, 8), '#5a2a8a', INK * 0.8)  # a round window
    roof = closed([(x - w * 0.42, top - 18), (x - w * 0.12, top - h * 0.48), (x, top - h * 0.62), (x + w * 0.12, top - h * 0.48),
                   (x + w * 0.42, top - 18), (x, top + 4)])
    out += outlined(roof, colour if colour != trim else MAG, INK)
    for k in range(4):
        bx = x - w * 0.5 + w * (k + 0.5) / 4
        out += outlined(lump(bx, top - 2, w * 0.17, w * 0.15, seed + k, 0.08, 8), trim, INK * 0.85)
    fx, fy = x, top - h * 0.6
    out += outlined(g.tube([(fx, fy + 20), (fx + 2, fy - 90)], 8, 7), '#ffffff', INK * 0.6)
    out += outlined(closed([(fx + 6, fy - 94), (fx + 70, fy - 86), (fx + 120, fy - 62), (fx + 66, fy - 46), (fx + 6, fy - 40)]), flag, INK * 0.7)
    return out


def v3_bouncy_castle() -> Image.Image:
    """Bouncy castle: the cushion blows up into a candy bouncy castle: striped puffy turrets with pennants stand up on
    both lobes, a puffy arched doorway opens in its front."""
    body = m.FILLS[BODY]
    stripes = ''
    for k, x in enumerate(range(700, 1520, 120)):
        P = [(x, 3150), (x + 60, 3150), (x + 30, 3800), (x - 30, 3800)]
        stripes += outlined(closed([P[0], P[1], ((P[1][0] + P[2][0]) / 2 + 8, 3475), P[2], P[3], ((P[3][0] + P[0][0]) / 2 + 8, 3475)]), BUTTER, INK * 0.8)
    clip = f'<clipPath id="cush"><path d="{body}"/></clipPath>'
    towers = turret(810, 3300, 220, 260, CYAN, BUTTER, MAG, 3) + turret(1400, 3350, 180, 190, BUTTER, MAG, CYAN, 9)
    door = (f'M{p(1110, 3640)}C{p(1100, 3500)} {p(1140, 3440)} {p(1190, 3440)}C{p(1240, 3440)} {p(1270, 3500)} {p(1262, 3650)}Z')
    door_trim = (f'M{p(1080, 3650)}C{p(1066, 3480)} {p(1130, 3405)} {p(1190, 3405)}C{p(1250, 3405)} {p(1300, 3480)} {p(1292, 3660)}Z')
    front = f'{clip}<g clip-path="url(#cush)">{stripes}</g>' + towers + outlined(door_trim, BUTTER, INK) + outlined(door, '#5a2a8a', INK)
    return draw(front, [PINK_FIG, YELLOW, CAP, LOWER_CAP] + STALKS, '', recolour=MAG2)


# ---- 4: whoopee cushion --------------------------------------------------------------------------------------------
def v4_whoopee() -> Image.Image:
    """Whoopee: the pedal note as a rude low one: the cushion puffs up into a fat magenta whoopee cushion, swelling out
    over the caps in front of it, its neck pokes out at the lower right and a big lumpy puff blows out."""
    rim = closed([(700, 3240), (850, 3170), (1080, 3170), (1300, 3200), (1460, 3270), (1530, 3440), (1490, 3640),
                  (1370, 3770), (1180, 3810), (980, 3760), (800, 3660), (690, 3460)])
    bladder = closed([(740, 3270), (870, 3210), (1080, 3212), (1290, 3240), (1425, 3305), (1485, 3445), (1450, 3610),
                      (1345, 3725), (1180, 3762), (1000, 3715), (835, 3625), (735, 3455)])
    shine = lump(880, 3300, 85, 36, 4, 0.08, 8, -10)
    neck = tube(bez((1450, 3470), (1510, 3440), (1540, 3400), (1570, 3350), 14), 56, 42)
    lip = lump(1576, 3340, 30, 56, 7, 0.08, 8, -55)
    puff = ''
    for x, y, r, s_ in ((1630, 3230, 64, 1), (1660, 3320, 52, 2), (1570, 3170, 48, 3), (1680, 3190, 44, 6)):
        puff += outlined(lump(x, y, r, r * 0.9, s_, 0.14, 9), '#fff6fb', INK * 0.9)
    puff += f'<path d="{lump(1630, 3245, 40, 48, 5, 0.1, 8)}" fill="#fff6fb"/>'
    front = outlined(neck, MAG2, INK) + outlined(lip, MAGD, INK * 0.9)
    front += outlined(rim, MAG2, INK * 1.1) + outlined(bladder, MAG, INK * 0.8) + outlined(shine, '#ffd0f2', INK * 0.6)
    return draw(front + puff, [PINK_FIG], '')


def scallop(x, y, rx, ry, n, seed) -> str:
    """A cloud-like wad: n round bumps bulging out round an oval, of uneven sizes (arcs between points on the oval)."""
    rnd = random.Random(seed)
    A = sorted(k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.4 for k in range(n))
    P = [(x + math.cos(a) * rx, y + math.sin(a) * ry) for a in A]
    d = f'M{p(*P[0])}'
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        r = math.hypot(b[0] - a[0], b[1] - a[1]) * (0.55 + rnd.random() * 0.15)
        d += f'A{r:.1f} {r:.1f} 0 0 1 {p(*b)}'
    return d + 'Z'


# ---- 5: overstuffed ------------------------------------------------------------------------------------------------
def v5_overstuffed() -> Image.Image:
    """Overstuffed: the cushion swells past bursting: its crease splits open and big fluffy clouds of stuffing puff
    out of its seams, each a lumpy cream cloud the size of the painting's shapes."""
    STUFF, STUFF2 = '#fffaf0', '#ffe9f6'
    clouds = [  # (centre, radius, seed): billowing out of the split crease, the top seam, the right edge
        ((1050, 3500), 150, 1), ((1180, 3380), 110, 3), ((800, 3190), 120, 4), ((1420, 3260), 105, 6), ((1290, 3660), 105, 7),
    ]
    tears = [closed([(1030, 3585), (1060, 3470), (1120, 3400), (1165, 3372), (1110, 3450), (1075, 3530)]),
             closed([(720, 3226), (800, 3205), (880, 3236), (800, 3250)]),
             closed([(1290, 3560), (1300, 3640), (1320, 3720), (1280, 3650)])]
    out = ''.join(outlined(t, '#7a1060', INK * 0.9) for t in tears)
    for (x, y), r, sd in clouds:
        out += outlined(scallop(x, y, r, r * 0.85, 9, sd), STUFF, INK * 0.9)
        out += f'<path d="{scallop(x + r * 0.12, y + r * 0.12, r * 0.55, r * 0.45, 7, sd + 50)}" fill="{STUFF2}"/>'
    return draw('', [], out, recolour=MAG2)


VERSIONS = [
    ('1-octopus', 'Octopus', v1_octopus),
    ('2-singing', 'Singing', v2_singing),
    ('3-bouncy-castle', 'Bouncy castle', v3_bouncy_castle),
    ('4-whoopee', 'Whoopee cushion', v4_whoopee),
    ('5-overstuffed', 'Overstuffed', v5_overstuffed),
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


# ---- chosen: octopus, singing last -----------------------------------------------------------------------------------
# Picked under 5a: the cushion turns into an octopus (a morph into something that could live there, and a pun: an
# octave up is octo, eight), and it wakes and sings on the last step (the character action). Built as one arrival per
# drawbar step: steps 1-7 each bring a tentacle out from behind the cushion's edges while its see-through fill deepens
# to magenta; step 8 lifts the sleepy lids off two almond eyes and opens a singing mouth. The tentacles are uneven in
# length and thickness, lumpy, a couple tucking behind the neighbours (the pink figure, a stalk, the orange cap), with
# one or two irregular pale suckers each; they sit `around` (behind the cushion, the stalks and the figures).
#
#     uv run scripts/cushion_endframes.py octo     # progression strip and end frame
#     uv run scripts/cushion_endframes.py export   # docs/objects/pedal-db8/build.json
DEEP = '#ee4fcf'  # the magenta the cushion deepens to, and the tentacles' colour
TENT = ['#ee4fcf', '#f45ad8', '#e646c6']
SUCK = ['#ffc2ef', '#ffb3e6']
# in front of the tentacles: the pink figure (body and eye), the bush's magenta stalk and the eye tree's stalks (the
# tentacles drape over the orange caps, clear of the cyan creature's face)
AROUND_FRONT = ['f099', 'f100', 'f113', 'f114', 'f115']
STEP = 1 / 8


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def to_oklch(hx):
    n = int(hx[1:], 16)
    r, g_, b = (_lin(((n >> s) & 255) / 255) for s in (16, 8, 0))
    l = (0.4122214708 * r + 0.5363325363 * g_ + 0.0514459929 * b) ** (1 / 3)
    mm = (0.2119034982 * r + 0.6806995451 * g_ + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g_ + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.793617785 * mm - 0.0040720468 * s
    A = 1.9779984951 * l - 2.428592205 * mm + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * mm - 0.808675766 * s
    return L, math.hypot(A, B), (math.degrees(math.atan2(B, A)) + 360) % 360


def _lin_of(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_, m_, s_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, (L - 0.0894841775 * a - 1.291485548 * b) ** 3
    return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
            -0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_)


def from_oklch(L, C, H):
    ok = lambda rgb: all(-1e-4 <= v <= 1 + 1e-4 for v in rgb)
    if not ok(_lin_of(L, C, H)):
        lo, hi = 0.0, C
        for _ in range(18):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(_lin_of(L, mid, H)) else (lo, mid)
        C = lo
    return '#' + ''.join(f'{round(_gam(v) * 255):02x}' for v in _lin_of(L, C, H))


def tint(hx, to, u):
    """The app's tint: the colour moves to `to` in OKLCH (hue the short way round)."""
    a, b = to_oklch(hx), to_oklch(to)
    dh = (((b[2] - a[2]) % 360) + 540) % 360 - 180
    return from_oklch(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, (a[2] + dh * u + 360) % 360)


def smooth_pts(P, n=8):
    """Points along a Catmull-Rom curve through P, n per span (a hand-drawn centreline)."""
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(P[-1])
    return out


def lumpy_limb(P, w0, w1, seed, bumps=3.0, wob=0.13) -> tuple[str, list, list]:
    """A lumpy tapered limb round the centreline P: its half-width falls from w0 to w1 unevenly, swelling and pinching
    in a few places, with a rounded, slightly blobby tip. Returns the path, the centreline and the half-widths."""
    rnd = random.Random(seed)
    C = smooth_pts(P, 7)
    n = len(C)
    ph, ph2 = rnd.random() * 6.3, rnd.random() * 6.3
    W = []
    for i in range(n):
        t = i / (n - 1)
        base = w1 + (w0 - w1) * (1 - t) ** 0.75
        W.append(base * (1 + wob * math.sin(t * bumps * 2 * math.pi + ph) + wob * 0.5 * math.sin(t * bumps * 4.7 + ph2)))
    L, R = [], []
    for i, (x, y) in enumerate(C):
        a, b = C[max(0, i - 1)], C[min(n - 1, i + 1)]
        d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
        L.append((x + nx * W[i], y + ny * W[i]))
        R.append((x - nx * W[i], y - ny * W[i]))
    # the tip: a few points round the end, a little lopsided
    ex, ey = C[-1]
    a = math.atan2(C[-1][1] - C[-3][1], C[-1][0] - C[-3][0])
    tip = [(ex + math.cos(a + s) * W[-1] * (1.05 + 0.1 * rnd.random()), ey + math.sin(a + s) * W[-1] * (1.05 + 0.1 * rnd.random()))
           for s in (0.9, 0.0, -0.9)]
    side_l = L[:-1:2] + [L[-1]]
    ring = side_l + tip + [R[-1]] + R[-3::-2] + ([R[0]] if (len(R) - 1) % 2 else [])
    return closed(ring), C, W


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 4), 'end': round(min(1.0, e), 4), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 4), round(min(1.0, out[1]), 4)
    return o


# (step, centreline from a root hidden inside the cushion out to the tip, root half-width, tip half-width, suckers at)
TENTACLES = [
    # 1: the biggest, straight up between the bush's stalk and the eye tree's stalk, its tip curling left behind the
    #    magenta stalk
    (1, [(880, 3380), (875, 3250), (868, 3140), (852, 3040), (858, 2960), (840, 2900), (790, 2885), (752, 2920)], 72, 22, (0.42, 0.66)),
    # 2: long, out to the right under the hand's thumb, drooping down at its end
    (2, [(1235, 3585), (1330, 3595), (1420, 3585), (1510, 3555), (1590, 3552), (1642, 3592), (1652, 3655)], 60, 20, (0.38, 0.62)),
    # 3: out to the left behind the pink figure, its tip coming out past it and lifting over the bush
    (3, [(800, 3320), (700, 3315), (600, 3305), (500, 3290), (440, 3245), (425, 3175), (455, 3130)], 50, 18, (0.82,)),
    # 4: stubby and thick, up out of the front lobe's top, bending right, a blunt tip
    (4, [(1280, 3400), (1295, 3300), (1325, 3220), (1385, 3165), (1450, 3148), (1498, 3165)], 58, 32, (0.5,)),
    # 5: out over the yellow and draped left across the orange cap, under the pink figure, its tip turning up
    (5, [(1000, 3510), (910, 3530), (820, 3560), (730, 3580), (650, 3560), (600, 3505), (612, 3455)], 52, 18, (0.4, 0.66)),
    # 6: low on the right, out and down, bending under
    (6, [(1270, 3700), (1345, 3730), (1410, 3780), (1455, 3840), (1458, 3900), (1425, 3935)], 54, 18, (0.35, 0.62)),
    # 7: short, lolling out over the lower orange cap under the mouth, clear of the cyan creature's eye
    (7, [(1140, 3620), (1160, 3710), (1210, 3765), (1270, 3778), (1305, 3748)], 46, 20, (0.5,)),
]


def tentacle_items() -> list[dict]:
    items = []
    for k, (step, P, w0, w1, sucks) in enumerate(TENTACLES):
        s0, s1 = (step - 1) * STEP, step * STEP
        d, C, W = lumpy_limb(P, w0, w1, 40 + k, 2.2 + 0.4 * (k % 3), 0.12 + 0.03 * (k % 2))
        root = P[0]
        items.append(it(d, TENT[k % 3], INK, root, s0 + 0.004, s1 - 0.012))
        rnd = random.Random(90 + k)
        for j, u in enumerate(sucks):
            i = int(u * (len(C) - 1))
            a, b = C[i - 1], C[i + 1]
            dd = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            nx, ny = -(b[1] - a[1]) / dd, (b[0] - a[0]) / dd
            side = -1 if k % 2 == 0 else 1
            x, y = C[i][0] + side * nx * W[i] * 0.38, C[i][1] + side * ny * W[i] * 0.38
            r = W[i] * (0.4 + 0.12 * rnd.random())
            items.append(it(lump(x, y, r, r * (0.7 + 0.2 * rnd.random()), 7 * k + j, 0.2, 7, rnd.random() * 180),
                            SUCK[j % 2], INK * 0.65, (x, y), s0 + STEP * 0.55, s1 - 0.004))
    return items


# step 8: the face, on the front lobe
EYES = [((1135, 3478), 74, 50, -8), ((1252, 3424), 68, 46, -14)]  # centre, half-width, half-height, tilt (degrees)
EYE_IRIS = '#6fe8f0'


def almond(cx, cy, rx, ry, rot, seed, frac=1.0) -> tuple[str, list]:
    """A hand-drawn almond (pointed at both ends), turned by rot. With frac < 1, only its top down to a lid line at
    that fraction of its height (the lid's lower edge curves down a little)."""
    rnd = random.Random(seed)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    T = lambda u, v: (cx + u * c - v * s, cy + u * s + v * c)
    top = [T(-rx, 2), T(-rx * 0.55, -ry * 0.92), T(0, -ry * (1.02 + 0.04 * rnd.random())), T(rx * 0.55, -ry * 0.9), T(rx, -2)]
    if frac >= 1:
        bot = [T(rx * 0.5, ry * 0.86), T(0, ry * (0.98 + 0.04 * rnd.random())), T(-rx * 0.5, ry * 0.88)]
        P = top + bot
    else:
        yl = -ry + 2 * ry * frac
        P = top + [T(rx * 0.9, yl * 0.6 - 4), T(rx * 0.45, yl + 6), T(0, yl + 12), T(-rx * 0.45, yl + 6), T(-rx * 0.9, yl * 0.6 - 4)]
    return closed(P), [T(0, -ry)]


def face_items() -> list[dict]:
    s = 7 * STEP  # 0.875
    items = []
    for k, ((cx, cy), rx, ry, rot) in enumerate(EYES):
        white, _ = almond(cx, cy, rx, ry, rot, 5 + k)
        items.append(it(white, '#ffffff', INK * 1.15, (cx, cy), s + 0.002, s + 0.035))
        ix, iy = cx + rx * 0.08, cy + ry * 0.12
        items.append(it(lump(ix, iy, ry * 0.68, ry * 0.7, 21 + k, 0.05, 9), EYE_IRIS, INK * 0.8, (ix, iy), s + 0.01, s + 0.04))
        items.append(it(lump(ix + 2, iy + 2, ry * 0.32, ry * 0.34, 31 + k, 0.06, 8), '#000000', 0, (ix, iy), s + 0.015, s + 0.042))
        items.append(it(circle(ix + ry * 0.2, iy - ry * 0.22, ry * 0.12), '#ffffff', 0, (ix, iy), s + 0.02, s + 0.045))
        # the sleepy lid: drawn over the eye, then lifting up into the top of it
        lid, (top,) = almond(cx, cy, rx, ry, rot, 5 + k, 0.55)
        items.append(it(lid, DEEP, INK * 1.15, top, s + 0.002, s + 0.03, 'y', (s + 0.05, s + 0.095)))
    # the singing mouth opening downward from its top lip, then its tongue
    mx, my = 1192, 3560
    mouth = closed([(mx - 70, my + 4), (mx - 30, my - 6), (mx + 30, my - 10), (mx + 72, my - 2), (mx + 66, my + 52),
                    (mx + 30, my + 100), (mx - 18, my + 108), (mx - 60, my + 70)])
    items.append(it(mouth, '#6a0f3a', INK * 1.1, (mx, my - 6), s + 0.06, s + 0.11, 'y'))
    tongue = lump(mx + 4, my + 78, 46, 24, 12, 0.1, 8, -6)
    items.append(it(tongue, '#ff6f91', INK * 0.75, (mx + 4, my + 88), s + 0.085, 1.0))
    return items


def octo_effects() -> list[dict]:
    return [
        {'effect': 'tint', 'color': DEEP, 'span': [0, round(7 * STEP, 3)]},
        {'effect': 'sprites', 'place': 'around', 'front': AROUND_FRONT, 'items': tentacle_items()},
        {'effect': 'sprites', 'place': 'over', 'items': face_items()},
    ]


def sprites_svg(items, t) -> str:
    """The app's sprites at timeline t: ease-out growth over [start, end], shrinking over [outStart, outEnd], scaled
    from `at` both ways or along one axis."""
    ease = lambda u: 1 - (1 - max(0.0, min(1.0, u))) ** 3
    out = ''
    for q in items:
        v = ease((t - q['start']) / max(1e-6, q['end'] - q['start']))
        if 'outStart' in q:
            v *= 1 - ease((t - q['outStart']) / max(1e-6, q['outEnd'] - q['outStart']))
        if v <= 0.01:
            continue
        x, y = q['at']
        sc = f'{v:.4f} 1' if q['grow'] == 'x' else f'1 {v:.4f}' if q['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{q["edge"]}" stroke-linejoin="round"' if q['edge'] > 0 else ''
        out += f'<path d="{q["d"]}" fill="{q["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def octo_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    u = min(1.0, t / (7 * STEP))
    tags = m.FILL_TAGS
    m.FILL_TAGS = [tg if f'id="{BODY}"' not in tg else
                   re.sub(r'fill-opacity="[^"]*"', f'fill-opacity="{0.2 + 0.8 * u:.3f}"', re.sub(r'fill="#[0-9A-Fa-f]+"', f'fill="{tint(m.FP[BODY]["fill"], DEEP, u)}"', tg))
                   for tg in tags]
    try:
        im = m.compose()
    finally:
        m.FILL_TAGS = tags
    # around: above the ink, masked out over the cushion and the front shapes (with an ink-wide band round them)
    cut = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in [BODY] + AROUND_FRONT)
    x, y, w, h = m.CROP
    mask = f'<mask id="mk" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950"><rect width="4950" height="4950" fill="#fff"/>{cut}</mask>'
    im.alpha_composite(m.svg(f'<defs>{mask}</defs><g mask="url(#mk)">{sprites_svg(tentacle_items(), t)}</g>'))
    im.alpha_composite(m.svg(sprites_svg(face_items(), t)))
    return im


def octo_main() -> None:
    out = OUT.parent / 'octopus'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [octo_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * 5 + 60, th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.2f} (step {round(tt * 8)})', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    if 'steps' in __import__('sys').argv[1:]:  # every step and the middle of step 8, for checking
        for k in range(9):
            octo_frame(k / 8).save(out / f'step-{k}.png')
        octo_frame(7 / 8 + 0.04).save(out / 'step-7.5.png')
    print('wrote', out)


if __name__ == '__main__' and 'octo' in __import__('sys').argv[1:]:
    octo_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The magenta cushion: drag for the Pedal 8' drawbar; it turns into an octopus, one tentacle per step, and wakes and sings on the eighth",
        'effects': octo_effects(),
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(tentacle_items()) + len(face_items()), 'shapes')
