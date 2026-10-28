# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower drawbar 7, the tierce, all the way out) for the rocket hill: the white cloud lobe behind the
little mint rocket at the top of the pyramid, with the rocket's pink striped fin (f311) lying over it and a white wedge
running down the pyramid's right slope behind the lavender straw creature.

    uv run scripts/rockethill_endframes.py
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
m.CROP = (3250, 330, 1300, 1150)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db7/endframes'
p, outlined, smooth, circle, ellipse, tube, bez = m.p, m.outlined, m.smooth, g.circle, g.ellipse, g.tube, g.bez
INK = 14
WHITE, PINK, CREAM, MINT = '#fffdf8', '#FFB4A5', '#FFE5A5', '#A5FFD1'
CANDY = ['#ff9fc4', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b', '#f64c76']
ROCKET, FIN_L, FIN_R = 'f309', 'f310', 'f311'
STRAW = ['f195', 'f196', 'f197', 'f198', 'f199', 'f200']  # the straw creature's hat brim, head, tongue, ears, eye
TOP = 380  # the painting's top edge on the canvas: nothing new goes above it


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


def blob(cx, cy, rx, ry, seed, n=11, j=0.1, rot=0.0) -> str:
    """A lumpy hand-drawn oval."""
    rnd = random.Random(seed)
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for k in range(n):
        a = k / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * j
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return smooth(pts)


def puff(cx, cy, r, seed, col=WHITE, lumps=7) -> str:
    """A cloud puff: a ring of outlined lumps, then the same lumps fill-only on top so they merge without seams."""
    rnd = random.Random(seed)
    L = []
    for k in range(lumps):
        a = k / lumps * 2 * math.pi + rnd.random() * 0.5
        L.append((cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.42, r * (0.48 + rnd.random() * 0.14)))
    out = ''.join(outlined(circle(x, y, rr), col, INK) for x, y, rr in L)
    out += ''.join(f'<path d="{circle(x, y, rr - INK / 2)}" fill="{col}"/>' for x, y, rr in L)
    out += f'<path d="{blob(cx, cy, r * 0.62, r * 0.5, seed)}" fill="{col}"/>'
    return out


def lumpy_rect(x0, y0, x1, y1, r, seed, j=6) -> list[tuple[float, float]]:
    rnd = random.Random(seed)
    pts = []
    for (cx, cy), a0 in (((x1 - r, y0 + r), -90), ((x1 - r, y1 - r), 0), ((x0 + r, y1 - r), 90), ((x0 + r, y0 + r), 180)):
        for k in range(3):
            a = math.radians(a0 + k * 45)
            pts.append((cx + math.cos(a) * r + (rnd.random() - 0.5) * j, cy + math.sin(a) * r + (rnd.random() - 0.5) * j))
    return pts


# ---- 1 Blast-off -------------------------------------------------------------------------------------------------
def v1_blastoff() -> Image.Image:
    """Blast-off: big candy flames roar out under the rocket's foot and the white hill billows into a rolling exhaust
    cloud, puff after puff out of its wedge and down both slopes."""
    rnd = random.Random(3)
    fl = ''
    for (bx, by), h, w, ang, outer, core in [((3530, 955), 280, 150, 218, '#f64c76', '#ffb4a5'),
                                              ((3640, 955), 280, 150, 142, '#ff9f43', '#fff3a0'),
                                              ((3585, 955), 440, 200, 180, '#ff8a3d', '#ffe066')]:
        fl += m.flame((bx, by), h, w, ang, rnd, outer, core, INK)
    pf = ''
    for k, (x, y, r) in enumerate([(3920, 1010, 150), (4060, 1150, 130), (3400, 1130, 150), (3780, 1180, 160),
                                   (3300, 990, 120), (3620, 1330, 150)]):
        pf += puff(x, y, r, 10 + k, [WHITE, '#fff0f4', WHITE, '#fff7e0', '#fff0f4', WHITE][k])
    return draw(pf + fl, [ROCKET, FIN_L, FIN_R], '')


# ---- 2 Feathered wing --------------------------------------------------------------------------------------------
def feather(root, ang, L, W, col, seed) -> str:
    """One lumpy outlined feather from `root` along angle `ang`, with two of the fin's black stripes near its root."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (root[0] + ca * u - sa * v, root[1] + sa * u + ca * v)
    rnd = random.Random(seed)
    pts = [R(-30, 0), R(L * 0.2, -W * 0.45), R(L * 0.55, -W * 0.55), R(L * 0.88, -W * 0.35), R(L, 0),
           R(L * 0.86, W * 0.38), R(L * 0.5, W * 0.5), R(L * 0.15, W * 0.4)]
    pts = [(x + (rnd.random() - 0.5) * 10, y + (rnd.random() - 0.5) * 10) for x, y in pts]
    out = outlined(smooth(pts), col, INK)
    for u, v in ((0.3, -0.1), (0.46, 0.08)):
        P = [R(L * u, W * v), R(L * (u + 0.12), W * (v - 0.22))]
        out += f'<path d="{tube(P, 6, 3)}" fill="#000"/>'
    return out


def v2_wing() -> Image.Image:
    """Wing: the pink fin opens into a big feathered wing, pink and white feathers trailing from its edge and sweeping
    out over the hill and down the slope."""
    out = ''
    spec = [((3730, 740), 82, 300, PINK), ((3755, 700), 68, 380, WHITE), ((3780, 650), 54, 440, PINK),
            ((3800, 590), 40, 460, WHITE), ((3808, 530), 26, 440, PINK), ((3800, 480), 12, 380, WHITE),
            ((3785, 455), -2, 290, PINK)]
    for k, (root, ang, L, col) in enumerate(spec):
        out += feather(root, ang, L, 125, col, k)
    return draw(out, [ROCKET, FIN_L, FIN_R] + STRAW)


# ---- 3 Waving fin -------------------------------------------------------------------------------------------------
NO_FIN = {'fill_over': {'f311': 'M0 0Z'}, 'ink_over': {i: 'M0 0Z' for i in ('i1382', 'i1381', 'i1380', 'i1375', 'i0533',
                                                                            'i0532', 'i0531', 'i0526')}}


def v3_wave() -> Image.Image:
    """Hello! The rocket's pink fin lifts away from it like an arm, its stripes opening into the fingers of a big pink
    mitten that waves over the hill, motion crescents flicking out."""
    P = bez((3700, 760), (3730, 710), (3780, 670), (3830, 645), 20)
    arm = outlined(tube(P, 46, 40), PINK, INK)
    hx, hy = 3865, 625
    hand = ''
    rot = 25
    for k, (dx, ln, a) in enumerate([(-58, 90, -22), (-20, 108, -7), (20, 106, 8), (56, 88, 22)]):
        hand += (f'<g transform="translate({p(hx, hy)}) rotate({rot}) translate({dx} -40) rotate({a})">'
                 + outlined(blob(0, -ln / 2, 24, ln / 2, k, j=0.05), PINK, INK) + '</g>')
    hand += (f'<g transform="translate({p(hx, hy)}) rotate({rot - 70}) translate(-95 0) rotate(-20)">'
             + outlined(blob(0, 0, 50, 24, 9, j=0.05), PINK, INK) + '</g>')
    palm = blob(hx, hy, 86, 72, 5, j=0.06, rot=rot)
    hand += outlined(palm, PINK, INK)
    sw = c_swoosh(hx, hy, 150, -75, -35, 24) + c_swoosh(hx, hy, 195, -72, -42, 20) + \
        c_swoosh(hx, hy, 150, -150, -112, 24)
    return draw2(arm + hand, [ROCKET], sw, **NO_FIN)


def draw2(front, again, over, fill_over=None, ink_over=None) -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>', fill_over=fill_over, ink_over=ink_over)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def c_swoosh(cx, cy, r, a0, a1, w) -> str:
    return g.c.swoosh(cx, cy, r, a0, a1, w)


# ---- 4 Fireworks -------------------------------------------------------------------------------------------------
def burst(cx, cy, r, cols, seed, n=8) -> str:
    """A chrysanthemum burst: fat lumpy petals round a lumpy heart, each petal tipped with a round spark."""
    rnd = random.Random(seed)
    out = ''
    for k in range(n):
        a = k / n * 360 + rnd.random() * 14
        L = r * (0.82 + rnd.random() * 0.18)
        out += (f'<g transform="translate({p(cx, cy)}) rotate({a:.1f})">'
                + outlined(blob(L * 0.55, 0, L * 0.42, r * 0.17, seed * 10 + k, j=0.08), cols[k % len(cols)], INK) + '</g>')
        ar = math.radians(a)
        out += outlined(blob(cx + math.cos(ar) * (L + r * 0.12), cy + math.sin(ar) * (L + r * 0.12), r * 0.1, r * 0.1, k), cols[(k + 1) % len(cols)], INK * 0.8)
    out += outlined(blob(cx, cy, r * 0.34, r * 0.32, seed, j=0.12), '#fffbe6', INK)
    out += outlined(blob(cx, cy, r * 0.16, r * 0.15, seed + 1), cols[0], INK * 0.8)
    return out


def v4_fireworks() -> Image.Image:
    """Fireworks: the hill shoots candy rockets up on puffy white trails and they burst into big petal flowers over
    it and over the clouds either side."""
    trails, bursts = '', ''
    for k, ((bx, by), r, cols, P) in enumerate([
            ((3840, 570), 175, ['#ff9fc4', '#ffe066', '#f64c76'], [(3900, 960), (3880, 870), (3865, 790), (3855, 720)]),
            ((4460, 650), 125, ['#2DFFF4', '#c4a3f0', '#7fd36b'], [(4200, 1200), (4280, 1080), (4350, 960), (4410, 840), (4440, 760)]),
            ((3380, 480), 120, ['#ffe066', '#ff9f43', '#2DFFF4'], [(3470, 960), (3440, 850), (3415, 740), (3398, 640)])]):
        trails += ''.join(puff(x, y, 80 - 11 * i, 40 + k * 5 + i) for i, (x, y) in enumerate(P))
        bursts += burst(bx, by, r, cols, 30 + k)
    return draw(trails, [ROCKET, FIN_L] + STRAW, bursts)


# ---- 5 Tiered cake -----------------------------------------------------------------------------------------------
def tier(x0, y0, x1, y1, seed, body, icing) -> str:
    """One lumpy cake tier with drippy icing over its top."""
    out = outlined(smooth(lumpy_rect(x0, y0, x1, y1, 30, seed, j=16)), body, INK)
    rnd = random.Random(seed)
    # icing: across the top, then a drippy lower edge
    d = f'M{p(x0 - 8, y0 + 40)}'
    d += f'C{p(x0 - 10, y0 - 10)} {p(x0 + 20, y0 - 14)} {p(x0 + 50, y0 - 14)}L{p(x1 - 50, y0 - 14)}'
    d += f'C{p(x1 - 20, y0 - 14)} {p(x1 + 10, y0 - 10)} {p(x1 + 8, y0 + 40)}'
    n = max(3, int((x1 - x0) / 70))
    xs = [x1 - (x1 - x0) * (k + 0.5) / n for k in range(n)]
    for x in xs:
        dl = 40 + rnd.random() * 45
        d += f'C{p(x + 40, y0 + 40)} {p(x + 22, y0 + 40 + dl)} {p(x, y0 + 40 + dl)}C{p(x - 22, y0 + 40 + dl)} {p(x - 30, y0 + 40)} {p(x - 35, y0 + 40)}'
    d += f'L{p(x0 - 8, y0 + 40)}Z'
    out += outlined(d, icing, INK * 0.85)
    return out


def v5_cake() -> Image.Image:
    """Tiers (the tierce): the hill stacks up into a big three-tier celebration cake, pink and white like the fin,
    standing on the slope, with candy candles burning on top."""
    out = tier(3640, 810, 4010, 1010, 1, WHITE, PINK)
    out += tier(3690, 660, 3960, 820, 2, PINK, WHITE)
    out += tier(3745, 540, 3905, 670, 3, WHITE, '#ff9fc4')
    for k, x in enumerate((3785, 3828, 3870)):
        out += outlined(blob(x, 505, 17, 42, k, j=0.06), CANDY[k + 1], INK * 0.8)
        out += m.flame((x, 468), 60, 36, (k - 1) * 8, random.Random(k), '#ff8a3d', '#ffe066', INK * 0.7)
    return draw(out, [ROCKET, FIN_L] + STRAW)


VERSIONS = [
    ('1-blastoff', 'Blast-off', v1_blastoff),
    ('2-wing', 'Feathered wing', v2_wing),
    ('3-waving-fin', 'Waving fin', v3_wave),
    ('4-fireworks', 'Fireworks', v4_fireworks),
    ('5-tiered-cake', 'Tiered cake', v5_cake),
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


# ---- chosen: blast-off ---------------------------------------------------------------------------------------------
# Picked (Claude, under 5a): 1 Blast-off on its own. The hill is a cloud lobe, and it does what a cloud under a rocket
# would do: it billows up into exhaust. On the drawbar it builds up step by step: puffs swell out of the hill's lobe
# and wedge, one or two a step over steps 1-4 (the rumble); the flames ignite under the rocket's foot on steps 5-6 and
# grow; the big central flame roars out on step 7 and the last puffs roll down the slopes on step 8.
SLUG = 'blast-off'
FRONT_IDS = [ROCKET, FIN_L, 'f187', 'f188', 'f189'] + STRAW  # the rocket and the straw creature stay in front
FOOT = (3585.0, 955.0)  # inside the rocket's foot: the flames start here, hidden by the rocket
S = 1 / 8  # one drawbar step


def scallop(cx, cy, rx, ry, seed, bump=88) -> tuple[str, list]:
    """A cloud puff the painting's way: an uneven, flat-bottomed blob whose edge is a run of lumps of different sizes.
    Returns the path and the junctions between lumps (where the painting puts its little ink ticks)."""
    rnd = random.Random(seed)
    tilt = (rnd.random() - 0.5) * 0.5
    per = math.pi * (rx + ry)
    n = max(6, round(per / bump))
    gaps = [0.35 + rnd.random() * 1.4 for _ in range(n)]
    tot = sum(gaps)
    a, pts = rnd.random() * 0.6, []
    for gp in gaps:
        f = 1 + (rnd.random() - 0.5) * 0.3
        sy = ry * (0.82 if math.sin(a) > 0.35 else 1.0)  # clouds sit on a flatter bottom
        x, y = math.cos(a) * rx * f, math.sin(a) * sy * f
        pts.append((cx + x * math.cos(tilt) - y * math.sin(tilt) * 0.3, cy + y + x * tilt * 0.2))
        a += gp / tot * 2 * math.pi
    d = f'M{p(*pts[0])}'
    for i in range(n):
        q0, q1 = pts[i], pts[(i + 1) % n]
        ch = math.dist(q0, q1)
        r = ch / 2 * (1.0 + rnd.random() * 0.6)
        d += f'A{r:.1f} {r:.1f} 0 0 1 {p(*q1)}'
    return d + 'Z', pts


def ticks(pts, cx, cy, seed, k=2) -> list[str]:
    """A few short tapered ink ticks pointing in from lump junctions, like the painting's cloud hooks."""
    rnd = random.Random(seed)
    out = []
    for q in rnd.sample(pts, min(k, len(pts))):
        dx, dy = cx - q[0], cy - q[1]
        L = math.hypot(dx, dy) or 1
        ln = 38 + rnd.random() * 18
        bend = (rnd.random() - 0.5) * 0.6
        P = [(q[0] + dx / L * 4, q[1] + dy / L * 4),
             (q[0] + (dx / L + bend * dy / L) * ln * 0.6, q[1] + (dy / L - bend * dx / L) * ln * 0.6),
             (q[0] + (dx / L + bend * 1.6 * dy / L) * ln, q[1] + (dy / L - bend * 1.6 * dx / L) * ln)]
        out.append(tube(P, 7, 2.5))
    return out


def flame_paths(base, h, w, angle, seed) -> tuple[str, str]:
    """m.flame's tongue and core as plain canvas-space paths (no transforms), for sprite items."""
    rnd = random.Random(seed)
    lean, wob = (rnd.random() - 0.5) * 0.5, rnd.random() * 0.15
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    T = lambda x, y: p(base[0] + x * ca - y * sa, base[1] + x * sa + y * ca)

    def shape(W, H):
        return (f'M{T(-W / 2, 0)}C{T(-W * (0.75 + wob), -H * 0.32)} {T(-W * 0.05, -H * 0.62)} {T(W * lean, -H)}'
                f'C{T(W * (0.32 + wob), -H * 0.6)} {T(W * 0.85, -H * 0.34)} {T(W / 2, 0)}Z')
    return shape(w, h), shape(w * 0.5, h * 0.56)


# (centre, rx, ry, colour, grows-from, start, end): steps 1-4 out of the hill, step 8 down the slopes
PUFFS = [
    # step 8: the last puffs roll down both slopes (listed first so the earlier puffs lie over them)
    ((3330, 1190), 150, 112, WHITE, (3470, 1060), 7 * S, 8 * S),
    ((3600, 1400), 165, 118, '#fff0f4', (3600, 1250), 7 * S + 0.02, 8 * S),
    ((4110, 1270), 130, 100, '#fff7e0', (3990, 1150), 7 * S + 0.01, 8 * S),
    # step 4: out beside the rocket's foot, either side
    ((3420, 1010), 135, 100, '#fff7e0', (3520, 960), 3 * S, 4 * S),
    ((3790, 1050), 150, 108, WHITE, (3760, 930), 3 * S + 0.02, 4 * S),
    # step 3: down the wedge, and off the lobe's right edge
    ((4040, 1090), 120, 92, '#fff0f4', (3960, 990), 2 * S, 3 * S),
    ((3925, 690), 105, 82, WHITE, (3880, 690), 2 * S + 0.02, 3 * S),
    # step 2: out of the wedge's top, and a small one at the lobe's foot by the rocket
    ((3935, 930), 135, 100, WHITE, (3880, 880), S, 2 * S),
    ((3710, 880), 95, 75, '#fff7e0', (3720, 820), S + 0.02, 2 * S),
    # step 1: the first puff swells out of the bottom of the lobe
    ((3815, 800), 125, 95, '#fff0f4', (3790, 760), 0.0, S),
]

# (base, height, width, angle, outer, core, start, end, core start): steps 5-6 the side flames, 7-8 the big one
FLAMES = [
    ((3530, 955), 300, 150, 218, '#f64c76', '#ffb4a5', 4 * S, 6 * S, 5 * S),
    ((3640, 955), 300, 150, 142, '#ff9f43', '#fff3a0', 4 * S + 0.02, 6 * S, 5 * S),
    (FOOT, 450, 205, 180, '#ff8a3d', '#ffe066', 6 * S, 7 * S, 7 * S),
]


def blast_items() -> list[dict]:
    items = []
    for k, ((cx, cy), rx, ry, col, at, s, e) in enumerate(PUFFS):
        d, pts = scallop(cx, cy, rx, ry, 100 + k)
        base = {'at': [float(at[0]), float(at[1])], 'start': round(s, 3), 'end': round(e, 3), 'grow': 'scale'}
        items.append({'d': d, 'fill': col, 'edge': INK, **base})
        for t in ticks(pts, cx, cy, 200 + k):
            items.append({'d': t, 'fill': '#000', 'edge': 0, **base})
    for k, (b, h, w, ang, outer, core, s, e, cs) in enumerate(FLAMES):
        od, cd = flame_paths(b, h, w, ang, 7 + k)
        at = [float(b[0]), float(b[1])]
        items.append({'d': od, 'fill': outer, 'edge': INK, 'at': at, 'start': round(s, 3), 'end': round(e, 3), 'grow': 'scale'})
        items.append({'d': cd, 'fill': core, 'edge': round(INK * 0.75, 1), 'at': at, 'start': round(cs, 3), 'end': round(min(1.0, cs + S), 3), 'grow': 'scale'})
    return items


def around(body: str) -> str:
    """The app's place: "around": drawn above the ink, masked so the fin, the rocket and the straw creature (and a
    band as wide as their ink) stay in front."""
    W = 4950
    holes = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>'
                    for f in [FIN_R] + FRONT_IDS)
    return (f'<defs><mask id="mk" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{W}">'
            f'<rect width="{W}" height="{W}" fill="#fff"/>{holes}</mask></defs><g mask="url(#mk)">{body}</g>')


def blast_frame(t: float) -> Image.Image:
    im = m.compose()
    if t > 0:
        im.alpha_composite(m.svg(around(g.sprite_svg(blast_items(), t))))
    return im


def strip(frames, path, sc=0.42) -> None:
    tiles = [blast_frame(t) for t in frames]
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    cols = 5
    rows = math.ceil(len(frames) / cols)
    im = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 50) * rows + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(frames, tiles)):
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 50)
        label = f'frame {tt:.2f}' + (f'  (step {round(tt * 8)})' if len(frames) > 5 else '')
        d.text((x, y), label, fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 36))
    im.save(path)


def blast_main() -> None:
    out = OUT.parent / SLUG
    out.mkdir(parents=True, exist_ok=True)
    blast_frame(1.0).save(out / 'end-frame.png')
    strip([0, 0.25, 0.5, 0.75, 1.0], out / 'strip.png')
    strip([k / 8 for k in range(9)], out / 'steps.png', sc=0.3)
    print('wrote', out)


LABEL = ("The cloud hill under the rocket: drag for the Lower 1 3/5' drawbar; it billows into exhaust puff by puff, "
         "then the rocket's flames ignite and roar")


def export() -> None:
    import json
    build = {'label': LABEL,
             'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['detail'], 'front': FRONT_IDS,
                          'items': blast_items()}]}
    path = ROOT / 'docs/objects/lower-db7/build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']), 'shapes to', path)


if __name__ == '__main__' and 'blast' in __import__('sys').argv[1:]:
    blast_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
