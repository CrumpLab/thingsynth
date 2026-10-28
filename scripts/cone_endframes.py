# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Upper 1' drawbar fully out) for the party-hat cone: the tall, narrow lilac cone by the big eye,
right, pointing up, the lavender eye-head sitting at its base and the cyan cactus-hand's hooked arm crossing its foot.

    uv run scripts/cone_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (3480, 1640, 1140, 1520)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/upper-db9/endframes'
p, outlined, circle, ellipse, tube, bez, spiral = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.spiral
smooth = m.smooth
INK = 13

# The cone (f174): apex, the corner where its right edge meets the eye-head, its foot, its left corner. Its right edge
# carries on down behind the head to about RB.
APEX, RIGHT, FOOT, LEFT, RB = (4313.0, 2237.0), (4392.0, 2696.0), (4168.0, 3037.0), (3982.0, 2861.0), (4440.0, 2985.0)
LILAC, LILAC_D, LILAC_L = '#c9a2ec', '#a47ad8', '#ead9ff'
PINK, HOT, YELLOW, CYAN, LIME, ORANGE, CREAM = '#ff9fc4', '#f64c76', '#ffe066', '#7fe8f0', '#b8f060', '#ff9f43', '#fffbe6'
HEAD, ARM, TUBE = 'f176', 'f179', 'f180'
FACE = [HEAD, 'f177', 'f178', 'f239']  # the eye-head, its lip, pupil and eye: kept in front
EYE_AT = (4400.0, 2960.0)  # inside the big eye


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if again and HEAD in again:
        im = keep_eye(im)
    if over:
        im.alpha_composite(m.svg(over))
    return im


_EYE = None


def eye_mask() -> Image.Image:
    """The big eye is a gap in the head's fill where the wash shows through: the region enclosed by the head round
    EYE_AT, found by flood fill, grown a little to take its ink ring too."""
    global _EYE
    if _EYE is None:
        x, y, w, h = m.CROP
        ink = ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(HEAD))
        ex, ey = EYE_AT
        ring = f'<path d="M{x} {y}h{w}v{h}h{-w}Z{circle(ex, ey, 175)}" fill-rule="evenodd"/>'  # never past the eye
        head = m.svg(f'<g fill="#000"><path d="{m.FILLS[HEAD]}"/>{ink}{ring}</g>').getchannel('A').point(lambda v: 255 if v > 40 else 0)
        sc = head.size[0] / w
        seed = (round((ex - x) * sc), round((ey - y) * sc))
        ImageDraw.floodfill(head, seed, 128)
        mask = head.point(lambda v: 255 if v == 128 else 0)
        _EYE = mask.filter(ImageFilter.MaxFilter(9))
    return _EYE


def keep_eye(im: Image.Image) -> Image.Image:
    base = m.compose()
    im.paste(base, (0, 0), eye_mask())
    return im


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(pt, o, deg):
    a = math.radians(deg)
    x, y = pt[0] - o[0], pt[1] - o[1]
    return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a))


def blob(cx, cy, rx, ry, seed, n=10, j=0.09, rot_deg=0.0) -> str:
    """A lumpy, hand-drawn round shape."""
    rnd = random.Random(seed)
    a0 = math.radians(rot_deg)
    pts = []
    for k in range(n):
        a = k / n * 2 * math.pi
        r = 1 + (rnd.random() - 0.5) * 2 * j
        x, y = math.cos(a) * rx * r, math.sin(a) * ry * r
        pts.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return smooth(pts)


def star(cx, cy, r, points=5, inner=0.48, seed=0, rot_deg=-90.0) -> str:
    """A soft, slightly uneven star: points rounded off the way a brush would."""
    rnd = random.Random(seed)
    pts = []
    for k in range(points * 2):
        a = math.radians(rot_deg) + k * math.pi / points + (rnd.random() - 0.5) * 0.08
        rr = r * (1 if k % 2 == 0 else inner) * (1 + (rnd.random() - 0.5) * 0.12)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    # sharpen the tips a little by adding a near point either side of each tip
    out = []
    for k, q in enumerate(pts):
        if k % 2 == 0:
            a = math.atan2(q[1] - cy, q[0] - cx)
            out += [(cx + math.cos(a - 0.05) * r * 0.9, cy + math.sin(a - 0.05) * r * 0.9), q,
                    (cx + math.cos(a + 0.05) * r * 0.9, cy + math.sin(a + 0.05) * r * 0.9)]
        else:
            out.append(q)
    return smooth(out)


def sparkle(cx, cy, r, colour='#ffffff', w=INK * 0.8, tilt=0.0) -> str:
    return outlined(star(cx, cy, r, 4, 0.26, int(cx), -90 + tilt), colour, w)


def cone_outline(apex=APEX) -> list:
    """The cone's own outline points, with its apex possibly moved."""
    return [apex, lerp(apex, RIGHT, 0.5), RIGHT, RB, FOOT, lerp(LEFT, FOOT, 0.5), LEFT, lerp(LEFT, apex, 0.5)]


# ---- 1. crystal --------------------------------------------------------------------------------------------------
def crystal(base, ang, length, width, light, dark, seed) -> str:
    """A big quartz point the painting's way: a lumpy prism with a pointed tip, a light face and a dark face, each an
    outlined fill (no bare ridge line). `base` is the middle of its foot, `ang` the direction it points (degrees)."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    J = lambda: (rnd.random() - 0.5) * width * 0.12
    P = lambda s, t: (base[0] + ux * s + nx * t + J(), base[1] + uy * s + ny * t + J())
    bl, br = P(0, -width / 2), P(0, width / 2)
    sl, sr = P(length * 0.66, -width * 0.47), P(length * 0.7, width * 0.5)
    tip = P(length, width * 0.06)
    mb, ms = P(-width * 0.05, width * 0.08), P(length * 0.72, width * 0.1)
    left = f'M{p(*bl)}L{p(*sl)}L{p(*tip)}L{p(*ms)}L{p(*mb)}Z'
    right = f'M{p(*mb)}L{p(*ms)}L{p(*tip)}L{p(*sr)}L{p(*br)}Z'
    hi = f'M{p(*P(length * 0.12, -width * 0.32))}L{p(*P(length * 0.6, -width * 0.3))}L{p(*P(length * 0.6, -width * 0.18))}L{p(*P(length * 0.14, -width * 0.2))}Z'
    return (outlined(left, light, INK) + outlined(right, dark, INK)
            + f'<path d="{hi}" fill="#ffffff" fill-opacity="0.85"/>')


def v1_crystal() -> Image.Image:
    """Crystal: the cone morphs into a tall lilac quartz point, and a cluster of candy crystals grows out round its
    foot, one per step, glinting."""
    out = ''
    # little ones behind first, the big point last
    out += crystal((4060, 2860), -150, 300, 125, PINK, '#e477a6', 3)
    out += crystal((4070, 2760), -122, 330, 135, CYAN, '#3fc4d2', 4)
    out += crystal((4150, 2650), -104, 300, 120, YELLOW, '#f2b736', 5)
    out += crystal((4390, 2730), -58, 260, 115, PINK, '#e477a6', 6)
    out += crystal((4400, 2860), -30, 210, 105, CYAN, '#3fc4d2', 7)
    out += crystal((4215, 2985), -84, 860, 330, LILAC_L, LILAC_D, 1)
    over = sparkle(4300, 2105, 70) + sparkle(3850, 2540, 55, YELLOW) + sparkle(4590, 2520, 50)
    return draw(out, FACE, over)


# ---- 2. chirping beak --------------------------------------------------------------------------------------------
def v2_beak() -> Image.Image:
    """Chirping beak: the cone is the big eye's beak; it splits down its length and opens wide, pointing at the sky
    like a baby bird's, pink mouth and tongue, singing the highest note out in big crescents."""
    M = (4215.0, 2965.0)  # the hinge: the middle of the cone's foot, tucked behind the head
    left = [APEX, lerp(LEFT, APEX, 0.5), LEFT, lerp(LEFT, FOOT, 0.5), FOOT, M]
    right = [APEX, lerp(APEX, RIGHT, 0.5), RIGHT, RB, M]
    L2 = [rot(q, M, -19) for q in left]
    R2 = [rot(q, M, 13) for q in right]
    tl, tr = L2[0], R2[0]
    top = lerp(tl, tr, 0.5)
    # the open mouth: a deep pink wedge between the two halves, a darker throat and a tongue
    mouth = smooth([M, lerp(M, tl, 0.5), lerp(M, tl, 0.92), (top[0] - 60, top[1] - 40), (top[0] + 60, top[1] - 45), lerp(M, tr, 0.92), lerp(M, tr, 0.5)])
    out = outlined(mouth, HOT, INK)
    out += outlined(blob(4240, 2640, 100, 210, 2, rot_deg=-2), '#9e1f55', INK * 0.8)
    out += outlined(tube(bez((4225, 2950), (4215, 2780), (4180, 2650), (4235, 2520), 16), 72, 50), PINK, INK)
    out += f'<path d="{tube(bez((4224, 2900), (4214, 2780), (4190, 2690), (4215, 2600), 12), 8, 6)}" fill="#e0466a"/>'
    out += outlined(smooth(L2), LILAC, INK) + outlined(smooth(R2), LILAC_D, INK)
    over = ''
    for k, r in enumerate((110, 200, 290)):
        over += g.c.swoosh(top[0] + 10, top[1] + 60, r, -150, -30, 52 - k * 6, [YELLOW, CYAN, PINK][k])
    return draw(out, FACE, over)


# ---- 3. party popper ---------------------------------------------------------------------------------------------
def ribbon(P, w, col) -> str:
    return outlined(tube(P, w, w * 0.8), col, INK * 0.85)


def v3_popper() -> Image.Image:
    """Party popper: the party hat pops; a puff bursts at its tip and fat curly streamers and big confetti fly out,
    one streamer per step."""
    tip = (4313, 2225)
    out = ''
    rnd = random.Random(11)
    cols = [PINK, YELLOW, CYAN, LIME, '#c4a3f0', ORANGE, HOT, YELLOW]
    angs = [-165, -140, -118, -98, -78, -58, -38, -15]
    for k, (ang, col) in enumerate(zip(angs, cols)):
        a = math.radians(ang)
        L = 300 + rnd.random() * 120
        mid = (tip[0] + math.cos(a) * L * 0.55 + math.cos(a + 1.2) * 50, tip[1] + math.sin(a) * L * 0.55 + math.sin(a + 1.2) * 50)
        end = (tip[0] + math.cos(a) * L, tip[1] + math.sin(a) * L)
        P = bez(tip, mid, (end[0] - math.cos(a - 1.0) * 60, end[1] - math.sin(a - 1.0) * 60), end, 18)
        hd = math.atan2(P[-1][1] - P[-2][1], P[-1][0] - P[-2][0])
        P += spiral(end[0], end[1], hd, 70, 1.1, 0.7, 1 if k % 2 else -1, 30)[1:]
        out += ribbon(P, 22, col)
    for (x, y, r, col, s) in [(3930, 2050, 55, YELLOW, 1), (4540, 2000, 50, PINK, 2), (4080, 1880, 45, CYAN, 3)]:
        out += outlined(star(x, y, r * 1.5, 5, 0.5, s), col, INK * 0.85)
    for (x, y, r, col, s) in [(3860, 2260, 38, LIME, 4), (4470, 2200, 36, '#c4a3f0', 5), (4230, 1830, 34, HOT, 6)]:
        out += outlined(blob(x, y, r, r * 0.8, s), col, INK * 0.85)
    puff = ''.join(outlined(blob(tip[0] + dx, tip[1] + dy, rr, rr * 0.9, s), CREAM, INK) for dx, dy, rr, s in
                   [(-60, -10, 62, 1), (55, -15, 60, 2), (0, -55, 70, 3), (0, 10, 58, 4)])
    puff += f'<path d="{blob(tip[0], tip[1] - 15, 75, 50, 9)}" fill="{CREAM}"/>'
    return draw('', [], out + puff)


# ---- 4. tip-top star ---------------------------------------------------------------------------------------------
def v4_star() -> Image.Image:
    """Tip-top star: the cone stretches up to be the highest thing around, a candy-striped point growing out of its
    tip, and a big sparkling star lands on top, glints round it."""
    top = (4330.0, 1985.0)
    jl, jr = lerp(APEX, LEFT, 0.3), lerp(APEX, RIGHT, 0.3)  # where the new point joins the cone
    ext = smooth([jl, (jl[0] + 8, jl[1] - 200), (top[0] - 50, top[1] + 90), top, (top[0] + 45, top[1] + 100), (jr[0] + 12, jr[1] - 200), jr,
                  lerp(jl, jr, 0.5)])
    out = outlined(ext, LILAC, INK)
    # candy bands round the new point: outlined filled bands clipped to it, the lowest at the join
    out += f'<defs><clipPath id="ext"><path d="{ext}"/></clipPath></defs><g clip-path="url(#ext)">'
    for k in range(7):
        y0 = jl[1] + 30 - k * 95
        band = f'M{p(4050, y0 + 60)}C{p(4250, y0 + 20)} {p(4400, y0)} {p(4600, y0 - 40)}L{p(4600, y0 - 90)}C{p(4400, y0 - 50)} {p(4250, y0 - 30)} {p(4050, y0 + 10)}Z'
        out += outlined(band, [PINK, YELLOW][k % 2], INK * 0.8)
    out += '</g>' + f'<path d="{ext}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    sx, sy = top[0], top[1] - 120
    rays = ''
    for k in range(10):
        a = math.radians(-90 + k * 36 + 18)
        a1, a2 = a - 0.13, a + 0.13
        rays += outlined(f'M{p(sx + math.cos(a1) * 150, sy + math.sin(a1) * 150)}L{p(sx + math.cos(a) * 270, sy + math.sin(a) * 270)}'
                         f'L{p(sx + math.cos(a2) * 150, sy + math.sin(a2) * 150)}Z', '#fff2a8', INK * 0.8)
    out += rays
    out += outlined(star(sx, sy, 175, 5, 0.5, 7), YELLOW, INK) + outlined(star(sx + 4, sy + 8, 85, 5, 0.5, 8), ORANGE, INK * 0.8)
    out += f'<path d="{blob(sx - 55, sy - 40, 22, 14, 3, rot_deg=-30)}" fill="#fff"/>'
    out += sparkle(4040, 1980, 75) + sparkle(4580, 2130, 60) + sparkle(4110, 2250, 50, YELLOW)
    return draw(out, [])


# ---- 5. soft-serve -----------------------------------------------------------------------------------------------
def v5_softserve() -> Image.Image:
    """Soft-serve: the cone turns into a tall strawberry-and-vanilla soft-serve swirl, one lumpy roll piled on the
    last per step, a curl at the very top, a cherry and two drips."""
    out = ''
    n = 8
    base, tip = (4205.0, 2930.0), (4330.0, 2290.0)
    rolls = []
    for k in range(n):
        t = k / (n - 1)
        cx, cy = lerp(base, tip, t)
        rx = 265 * (1 - 0.62 * t)
        ry = 84 - 30 * t
        rolls.append((cx, cy, rx, ry, k))
    # drips from the lowest roll first, behind it
    for dx, L in ((-190, 120), (-95, 85)):
        x0, y0 = base[0] + dx, base[1] + 20
        out += outlined(tube([(x0, y0 - 30), (x0 + 4, y0 + L * 0.5), (x0 + 2, y0 + L)], 26, 24), CREAM, INK * 0.85)
    for cx, cy, rx, ry, k in rolls:
        col = [PINK, CREAM][k % 2]
        out += outlined(blob(cx, cy, rx, ry, 30 + k, n=12, j=0.07, rot_deg=-13 + (k % 2) * 9), col, INK)
        # the swirl's crease: a darker fill-only sliver along the roll's underside
        out += f'<path d="{blob(cx + rx * 0.2, cy + ry * 0.5, rx * 0.55, ry * 0.28, 60 + k, rot_deg=-11)}" fill="{["#f27aa8", "#f0dca8"][k % 2]}"/>'
    # the curl on top
    P = bez((tip[0] - 10, tip[1] + 20), (tip[0] + 5, tip[1] - 60), (tip[0] + 70, tip[1] - 110), (tip[0] + 20, tip[1] - 150), 16)
    out += outlined(tube(P, 52, 18), PINK, INK)
    cx, cy = tip[0] - 30, tip[1] - 175
    out += outlined(tube(bez((cx, cy - 40), (cx + 10, cy - 90), (cx + 40, cy - 120), (cx + 70, cy - 130), 10), 9, 7), '#6cc35b', INK * 0.7)
    out += outlined(blob(cx, cy, 62, 58, 5), HOT, INK) + f'<path d="{blob(cx - 22, cy - 22, 16, 11, 2, rot_deg=-30)}" fill="#fff"/>'
    return draw(out, FACE)


VERSIONS = [
    ('1-crystal', 'Crystal', v1_crystal),
    ('2-chirping-beak', 'Chirping beak', v2_beak),
    ('3-party-popper', 'Party popper', v3_popper),
    ('4-tip-top-star', 'Tip-top star', v4_star),
    ('5-soft-serve', 'Soft-serve', v5_softserve),
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


# ---- chosen: the chirping beak ----------------------------------------------------------------------------------
# Picked (Claude, under 5a): 2 Chirping beak. The cone is the big eye's beak. Upper 1' is a drawbar (0..8), so every
# step lands an arrival on k/8:
#   steps 1-4  the cone splits down its length (from its tip to its foot) and the halves open a quarter more each step,
#              a dark mouth showing between them;
#   step 5     the pink mouth lining, the throat and the tongue;
#   steps 6-8  one fat, lumpy candy crescent per step, each bigger, rising from the open beak.
# Sprites can only grow, shrink or be swept in, not turn, so each step's pose of each half is its own shape: it is
# swept in round the hinge from its inner edge outward over the step, and the pose before it drops away as the step
# lands. The dark mouth between the halves is swept open round the same hinge in step with them, so its edges are the
# halves' inner edges exactly. All of it goes `around`: above the ink, masked by the eye-head and its lip so they stay
# in front. The cone itself is not masked (an empty role `split` is named as the parts).
STEP = 1 / 8
HINGE = FOOT  # the cone's bottom corner, tucked under the eye-head's lip
OPEN_L, OPEN_R = 19.0, 13.0  # how far each half turns by step 4 (degrees)
FRONT_IDS = ['f176', 'f177', 'f178', 'f239', 'f179']  # the eye-head, its lip and eye, and the cyan arm's hook
PLUM = '#5a1a45'


def app_angle(pt) -> float:
    """The app's sweep angle of pt round the hinge: degrees, 0 = right, 90 = up."""
    return math.degrees(math.atan2(-(pt[1] - HINGE[1]), pt[0] - HINGE[0]))


SPLIT = app_angle(APEX)


def half_path(pts) -> str:
    """A beak half: a straight inner edge from the hinge to the tip, then a hand-drawn curve round its outer side
    through pts back to the hinge."""
    P = [HINGE] + pts + [HINGE]
    d = f'M{p(*HINGE)}L{p(*pts[0])}'
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def bulge(a, b, t, out):
    """A point t of the way from a to b, pushed `out` px to the left of the direction a->b (lumpy, hand-drawn)."""
    x, y = lerp(a, b, t)
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1
    return (x + dy / n * out, y - dx / n * out)


LEFT_PTS = [APEX, bulge(APEX, LEFT, 0.3, 14), bulge(APEX, LEFT, 0.62, 22), LEFT, (4080, 2955)]
RIGHT_PTS = [APEX, bulge(APEX, RIGHT, 0.35, -16), bulge(APEX, RIGHT, 0.72, -12), RIGHT, (4300, 2840)]


def along(r, ang):
    a = math.radians(ang)
    return (HINGE[0] + math.cos(a) * r, HINGE[1] - math.sin(a) * r)


def mouth_shape() -> str:
    """The open mouth at its widest: straight sides along the halves' inner edges at step 4, its top an arc round
    the hinge from tip to tip, so the pink lining reaches the beak's points and covers the painted cone's own tip."""
    al, ar = SPLIT + OPEN_L, SPLIT - OPEN_R
    R = 800.0
    tl, tr = along(R, al), along(R, ar)
    return f'M{p(*HINGE)}L{p(*tl)}A{R:.0f} {R:.0f} 0 0 1 {p(*tr)}Z'


def item(d, fill, edge, at, k0, k1=None, grow='scale', **kw) -> dict:
    """A sprite arriving over steps k0..k1 (in eighths; fractions allowed)."""
    k1 = k0 + 1 if k1 is None else k1
    it = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
          'start': round(k0 * STEP, 4), 'end': round(k1 * STEP, 4), 'grow': grow}
    it.update(kw)
    return it


def crescent(cx, cy, r, th, a0, a1, seed) -> str:
    """A fat, lumpy crescent round (cx, cy) from a0 to a1 (screen degrees), thickest in the middle, round-ended."""
    rnd = random.Random(seed)
    n = 9
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        w = th * (0.25 + 0.75 * math.sin(math.pi * u) ** 0.8) * (1 + (rnd.random() - 0.5) * 0.18)
        j = (rnd.random() - 0.5) * th * 0.12
        outer.append((cx + math.cos(a) * (r + w / 2 + j), cy + math.sin(a) * (r + w / 2 + j)))
        inner.append((cx + math.cos(a) * (r - w / 2 + j), cy + math.sin(a) * (r - w / 2 + j)))
    return smooth(outer + inner[::-1])


def beak_items() -> list[dict]:
    items = []
    mouth = mouth_shape()
    # the dark mouth, swept open between the halves' inner edges, step by step (each a little wider than the last)
    for k in range(1, 5):
        for sign, deg in ((1, OPEN_L), (-1, OPEN_R)):
            items.append(item(mouth, PLUM, INK, HINGE, k - 1 + 0.02, k, sweep={'from': round(SPLIT, 2), 'to': round(SPLIT + sign * deg * k / 4, 2)}))
    # step 5: the pink lining, the throat and the tongue
    dirn = SPLIT + (OPEN_L - OPEN_R) / 2
    cx, cy = along(470, dirn)
    items.append(item(mouth, HOT, INK, HINGE, 4, 4.7))
    throat = blob(cx, cy, 92, 180, 2, n=10, j=0.06, rot_deg=90 - dirn)
    items.append(item(throat, '#9e1f55', INK * 0.8, along(260, dirn), 4.2, 4.85))
    tongue = tube(bez(along(60, dirn), along(220, dirn + 3), along(380, dirn - 4), along(520, dirn + 1), 16), 64, 48)
    items.append(item(tongue, PINK, INK, along(60, dirn), 4.35, 5))
    groove = tube(bez(along(120, dirn), along(240, dirn + 2), along(360, dirn - 2), along(450, dirn), 12), 8, 6)
    items.append(item(groove, '#e0466a', 0, along(60, dirn), 4.5, 5))
    # steps 1-4: each pose of each half swept in round the hinge from its inner edge outward; the last pose drops away
    for k in range(1, 5):
        for pts, sign, deg, col, reach in ((LEFT_PTS, 1, OPEN_L, LILAC, 90), (RIGHT_PTS, -1, OPEN_R, LILAC_D, 75)):
            a = sign * deg * k / 4
            d = half_path([rot(q, HINGE, -a) for q in pts])
            kw = {'sweep': {'from': round(SPLIT + a, 2), 'to': round(SPLIT + a + sign * reach, 2)}}
            if k < 4:
                kw.update(outStart=round((k + 1) * STEP - 0.004, 4), outEnd=round((k + 1) * STEP, 4))
            items.append(item(d, col, INK, HINGE, k - 1 + 0.02, k, **kw))
    # steps 6-8: fat lumpy candy crescents rising out of the open beak, each bigger
    sx, sy = along(770, dirn)
    for k, (r, th, col) in enumerate(((170, 64, YELLOW), (255, 76, CYAN), (345, 88, PINK))):
        d = crescent(sx, sy, r, th, -148 + k * 5, -32 - k * 5, 40 + k)
        items.append(item(d, col, INK, (sx, sy), 5 + k, 6 + k))
    return items


def sprites_svg(items, t) -> str:
    """The app's drawSprites, frame t: easeOut3 growth, the shrink-away window, and sweeps revealed by a wedge."""
    e3 = lambda u: 1 - (1 - max(0.0, min(1.0, u))) ** 3
    out = ''
    for n, it in enumerate(items):
        v = e3((t - it['start']) / max(1e-6, it['end'] - it['start']))
        if 'outStart' in it:
            v *= 1 - e3((t - it['outStart']) / max(1e-6, it['outEnd'] - it['outStart']))
        x, y = it['at']
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        if 'sweep' in it:
            if v <= 0.005:
                continue
            a0, a1 = it['sweep']['from'], it['sweep']['to']
            a1 = a0 + (a1 - a0) * v
            pts = [f'{x:.1f} {y:.1f}'] + [f'{x + math.cos(math.radians(a0 + (a1 - a0) * i / 24)) * 5000:.1f} {y - math.sin(math.radians(a0 + (a1 - a0) * i / 24)) * 5000:.1f}' for i in range(25)]
            out += f'<clipPath id="w{n}"><path d="M{"L".join(pts)}Z"/></clipPath><path d="{it["d"]}" fill="{it["fill"]}"{stroke} clip-path="url(#w{n})"/>'
            continue
        if v <= 0.01:
            continue
        sc = f'{v:.4f} 1' if it['grow'] == 'x' else f'1 {v:.4f}' if it['grow'] == 'y' else f'{v:.4f}'
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def around(sprites: str, front: list[str]) -> Image.Image:
    """The app's `around` layer: above the ink, masked out over the front shapes and a 44 px band round them."""
    im = m.compose()
    layer = m.svg(sprites)
    cut = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in front)).getchannel('A')
    a = layer.getchannel('A')
    layer.putalpha(Image.composite(Image.new('L', a.size, 0), a, cut))
    im.alpha_composite(layer)
    return im


def beak_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    return around(sprites_svg(beak_items(), t), FRONT_IDS)


def strip(frames, out: Path, name: str) -> None:
    tiles = [beak_frame(t) for t in frames]
    w, h = tiles[0].size
    sc = 0.36
    tw, th = int(w * sc), int(h * sc)
    im = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.3f}'.rstrip('0').rstrip('.') if tt not in (0, 1) else f'frame {tt:.2f}', fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    im.save(out / name)


def beak_main() -> None:
    out = OUT.parent / 'chirping-beak'
    out.mkdir(parents=True, exist_ok=True)
    beak_frame(1.0).save(out / 'end-frame.png')
    strip([0, 0.25, 0.5, 0.75, 1.0], out, 'strip.png')
    strip([k / 8 for k in range(9)], out, 'steps.png')
    print('wrote', out)


LABEL = ("The party-hat cone: drag for the Upper 1' drawbar; it is the big eye's beak: it splits and opens wide like a "
         "baby bird's a little more each step, shows its pink mouth and tongue, then sings the highest note in big candy "
         "crescents, one more each step")


def export() -> None:
    import json
    items = beak_items()
    build = {'label': LABEL,
             'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['split'], 'front': FRONT_IDS, 'items': items}],
             'objectParts': {'split': []}}
    path = ROOT / 'docs/objects/upper-db9/build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(items), 'sprites to', path)


if __name__ == '__main__' and 'beak' in __import__('sys').argv[1:]:
    beak_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
