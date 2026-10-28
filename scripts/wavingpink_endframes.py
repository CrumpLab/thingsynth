# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower 8' drawbar fully out) for the waving pink creature, lower left: a pale see-through creature
(the wash glows rose and orange through it) standing upright, its head facing right with a long horn sweeping up-left,
a pointed ear on top, a round snout tipped by a green spike, a mitten hand raised beside its face, and a long body
running down behind the lavender mitten.

    uv run scripts/wavingpink_endframes.py
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
m.CROP = (840, 2690, 1340, 1560)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db3/endframes'
p, outlined, circle, tube, bez, crescent = m.p, m.outlined, g.circle, g.tube, g.bez, g.crescent
INK = 14
BODY = ['f240']
MITTEN = ['f241']  # the lavender mitten of the lying creature, in front of the creature's lower body
PINK, ROSE, DEEP, PALE = '#ff8fb8', '#f6a6c0', '#e84f7c', '#ffd0de'
CANDY = ['#f64c76', '#ffe066', '#7fe0c8', '#c4a3f0', '#ff9f43', '#2DFFF4', '#ff9fc4', '#a8ec6b']

# landmarks on the painted creature (canvas px)
HORN_TIP, HORN_BASE = (1385.0, 3195.0), (1540.0, 3330.0)
DOME = (1600.0, 3255.0)
SNOUT = (1640.0, 3415.0)
HAND = (1405.0, 3415.0)  # the mitten raised beside its face
NECK_TOP, NECK_BOT = (1535.0, 3485.0), (1470.0, 3650.0)
LOWER = (1370.0, 3780.0)  # the big lower body, its left half visible beside the mitten


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


def lumpy(cx, cy, rx, ry, rot=0.0, seed=0, n=9, wob=0.07) -> str:
    """A hand-drawn closed blob round (cx, cy): an ellipse with slightly irregular radius, smoothed."""
    rnd = random.Random(seed)
    a0, r = rnd.random() * 6.28, math.radians(rot)
    pts = []
    for k in range(n):
        a = a0 + k / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        x, y = math.cos(a) * rx * f, math.sin(a) * ry * f
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return m.smooth(pts)


def rel(x, y, ang, u, v):
    a = math.radians(ang)
    return x + math.cos(a) * u - math.sin(a) * v, y + math.sin(a) * u + math.cos(a) * v


def sausage(P, r0, r1=None, seed=0) -> str:
    """A closed sausage along the centreline P, rounded at both ends, its width wobbling a little (a balloon, a leg)."""
    r1 = r0 if r1 is None else r1
    rnd = random.Random(seed)
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (r0 + (r1 - r0) * u) * (1 + (rnd.random() - 0.5) * 0.06)
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    def cap(c, q0, ang0, r, sgn):
        return [(c[0] + math.cos(ang0 + sgn * k / 8 * math.pi) * r, c[1] + math.sin(ang0 + sgn * k / 8 * math.pi) * r) for k in range(1, 8)]
    (x1, y1), (x0, y0) = P[-1], P[-2]
    ae = math.atan2(L[-1][1] - y1, L[-1][0] - x1)
    end = cap(P[-1], L[-1], ae, r1, -1 if ((x1 - x0) * (L[-1][1] - y1) - (y1 - y0) * (L[-1][0] - x1)) > 0 else 1)
    (xs, ys), (xs1, ys1) = P[0], P[1]
    a_s = math.atan2(R[0][1] - ys, R[0][0] - xs)
    start = cap(P[0], R[0], a_s, r0, -1 if ((xs - xs1) * (R[0][1] - ys) - (ys - ys1) * (R[0][0] - xs)) > 0 else 1)
    pts = L + end + R[::-1] + start
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def shine(cx, cy, rx, ry, rot) -> str:
    return outlined(lumpy(cx, cy, rx, ry, rot, seed=int(cx), n=7, wob=0.05), '#ffffff', INK * 0.6)


def mitten(cx, cy, s, rot, col, seed=0) -> tuple[str, str]:
    """A big mitten hand the painting's way: a rounded palm with a thumb lobe. Returns (fill, outline) paths in one
    closed shape, rotated by rot (0 = fingers up)."""
    pts = []
    rnd = random.Random(seed)
    # palm outline, thumb on the left, going round clockwise from the wrist
    raw = [(-0.55, 0.9), (-0.6, 0.35), (-0.95, 0.05), (-1.15, -0.3), (-1.0, -0.5), (-0.75, -0.35), (-0.55, -0.15),
           (-0.62, -0.75), (-0.35, -1.12), (0.05, -1.22), (0.45, -1.05), (0.65, -0.65), (0.66, 0.0), (0.55, 0.9)]
    for u, v in raw:
        u *= 1 + (rnd.random() - 0.5) * 0.06
        pts.append(rel(cx, cy, rot, u * s, v * s))
    return m.smooth(pts), ''


# ---- 1: balloon animal (morph) ------------------------------------------------------------------------------------
def v1_balloon() -> Image.Image:
    """Balloon animal: the creature twists into a glossy pink balloon animal, horn, head, snout, waving hand, neck
    and body each a puffed balloon, pinched at the joins, the tied knot at its snout."""
    parts = [
        (bez(HORN_TIP, (1430, 3225), (1490, 3280), HORN_BASE, 12), 42, '#ff8fb8'),
        (bez((1340, 3370), (1380, 3400), (1440, 3440), (1500, 3460), 12), 70, '#ff7eb6'),
        (bez(NECK_TOP, (1520, 3540), (1495, 3600), NECK_BOT, 12), 52, '#ff9fc4'),
        (bez((1430, 3650), (1370, 3720), (1345, 3830), (1365, 3960), 12), 92, '#ff8fb8'),
    ]
    out = ''
    for k, (P, r, col) in enumerate(parts):
        out += outlined(sausage(P, r, r, k), col, INK)
    out += outlined(lumpy(*DOME, 82, 92, 10, seed=3), '#ff7eb6', INK)
    out += outlined(lumpy(1625, 3410, 100, 70, 4, seed=4), '#f9a3c4', INK)
    out += outlined(lumpy(1555, 3335, 34, 26, 30, seed=5), DEEP, INK * 0.8)  # twist at the neck of the head
    out += outlined(lumpy(1505, 3475, 30, 22, 60, seed=6), DEEP, INK * 0.8)
    out += outlined(lumpy(1455, 3640, 32, 22, 20, seed=7), DEEP, INK * 0.8)
    # the knot and nozzle at the snout tip
    out += outlined(f'M{p(1722, 3405)}L{p(1770, 3380)}C{p(1790, 3400)} {p(1790, 3440)} {p(1770, 3455)}L{p(1722, 3430)}Z', DEEP, INK * 0.8)
    for x, y, rx, ry, rot in [(1420, 3215, 40, 13, 40), (1580, 3215, 38, 16, -30), (1375, 3385, 42, 15, 25),
                              (1610, 3385, 46, 15, -5), (1515, 3530, 30, 12, 100), (1320, 3720, 22, 60, 15)]:
        out += shine(x, y, rx, ry, rot)
    return draw(out, MITTEN)


# ---- 2: big hello (character action) ------------------------------------------------------------------------------
def big_eye(cx, cy, r) -> str:
    out = outlined(lumpy(cx, cy, r, r * 1.08, 0, seed=11, n=8, wob=0.04), '#ffffff', INK)
    out += outlined(circle(cx + r * 0.2, cy + r * 0.12, r * 0.5), '#ff4fa3', INK * 0.8)
    out += f'<path d="{circle(cx + r * 0.22, cy + r * 0.14, r * 0.25)}" fill="#000"/>'
    out += f'<path d="{circle(cx + r * 0.36, cy - r * 0.04, r * 0.1)}" fill="#fff"/>'
    return out


def arm(P, w0, w1, col, hand_at, s, rot, seed) -> str:
    """An outlined arm along P ending in a big mitten; its root and wrist refilled without ink so it joins the body
    and the hand seamlessly."""
    out = outlined(tube(P, w0, w1), col, INK)
    d, _ = mitten(*hand_at, s, rot, col, seed)
    out += outlined(d, col, INK)
    out += f'<path d="{lumpy(*P[-1], w1 * 0.9, w1 * 0.9, 0, 1, 7, 0.02)}" fill="{col}"/>'
    out += f'<path d="{lumpy(*P[0], w0 * 1.05, w0 * 1.05, 0, 2, 7, 0.02)}" fill="{col}"/>'
    return out


def v2_hello() -> Image.Image:
    """Big hello: a round eye opens on its face and its jaw drops into a grin, the raised mitten swings out into a big
    wave with motion crescents, and a second arm comes up on its other side, waving too."""
    out = ''
    P = bez((1540, 3595), (1630, 3630), (1740, 3640), (1830, 3600), 16)
    out += arm(P, 40, 38, ROSE, (1900, 3530), 95, 50, 2)
    P = bez((1470, 3520), (1400, 3500), (1320, 3440), (1285, 3330), 16)
    out += arm(P, 46, 42, PINK, (1270, 3230), 110, -24, 1)
    for (cx, cy, r, a0, a1) in [(1270, 3230, 200, 110, 160), (1270, 3230, 200, 20, 70), (1900, 3530, 175, 70, 115), (1900, 3530, 175, -5, 40)]:
        out += outlined(crescent(cx, cy, r, a0, a1, 26), '#ffffff', INK * 0.8)
    out += big_eye(1610, 3355, 52)
    grin = f'M{p(1580, 3440)}C{p(1610, 3445)} {p(1680, 3440)} {p(1712, 3425)}C{p(1712, 3490)} {p(1650, 3530)} {p(1600, 3500)}C{p(1585, 3485)} {p(1578, 3460)} {p(1580, 3440)}Z'
    out += outlined(grin, '#7a1030', INK)
    out += outlined(lumpy(1640, 3490, 38, 18, -8, seed=9), '#ff6f9a', INK * 0.7)
    return draw(out, MITTEN + ['f095'])


# ---- 3: fanfare horn (celebratory display) ------------------------------------------------------------------------
def band(P, i0, i1, wd) -> str:
    """A square-ended band across the tube along P, from sample i0 to i1, as wide as the tube."""
    L, R = [], []
    for i in range(i0, i1 + 1):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = wd(i) - 1
        L.append((P[i][0] + nx * w, P[i][1] + ny * w))
        R.append((P[i][0] - nx * w, P[i][1] - ny * w))
    return 'M' + 'L'.join(p(*q) for q in L + R[::-1]) + 'Z'


def v3_fanfare() -> Image.Image:
    """Fanfare: its long horn grows on into a candy trumpet, banded pink and yellow, curving up to a big bell, and
    streamers and puffs of candy colour blast out of it."""
    out = ''
    ang = -84  # the bell faces up
    bc = (1400.0, 3060.0)  # where the horn meets the bell
    bx, by = rel(*bc, ang, 150, 0)  # the bell's mouth
    for k, (a_, bend, L) in enumerate([(-175, 0.5, 210), (-135, -0.45, 200), (-95, 0.45, 190), (-55, -0.5, 200), (-15, 0.4, 210)]):
        a = math.radians(a_)
        P = bez((bx, by), (bx + math.cos(a) * L * 0.35, by + math.sin(a) * L * 0.35),
                (bx + math.cos(a + bend) * L * 0.7, by + math.sin(a + bend) * L * 0.7), (bx + math.cos(a - bend * 0.4) * L, by + math.sin(a - bend * 0.4) * L), 18)
        out += outlined(tube(P, 26, 20), CANDY[[0, 2, 3, 4, 5][k]], INK * 0.85)
    for k, (dx, dy, r) in enumerate([(-230, -60, 54), (-70, -190, 58), (120, -160, 50), (250, 30, 44)]):
        out += outlined(lumpy(bx + dx, by + dy, r, r * 0.9, 0, seed=20 + k), CANDY[[1, 6, 7, 1][k]], INK * 0.85)
    # the horn, growing on from its painted tip and curving up, then candy bands laid on without ink between
    P = bez(HORN_BASE, (1400, 3240), (1340, 3140), bc, 30)
    n = len(P)
    wd = lambda k: 34 + 34 * (k / (n - 1)) ** 2
    horn = tube(P, wd(0), wd(n - 1))
    out += f'<path d="{horn}" fill="#ff7eb6"/>'
    for k in range(4, n - 4, 7):
        out += f'<path d="{band(P, k, k + 3, wd)}" fill="#ffe066"/>'
    out += f'<path d="{horn[:-1]}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round" stroke-linecap="round"/>'
    bell = (f'M{p(*rel(*bc, ang, -10, -64))}C{p(*rel(*bc, ang, 70, -80))} {p(*rel(*bc, ang, 110, -150))} {p(*rel(*bc, ang, 150, -175))}'
            f'L{p(*rel(*bc, ang, 150, 175))}C{p(*rel(*bc, ang, 110, 150))} {p(*rel(*bc, ang, 70, 80))} {p(*rel(*bc, ang, -10, 64))}Z')
    out += outlined(bell, '#ff7eb6', INK)
    out += f'<path d="{tube([rel(*bc, ang, 60, 0), rel(*bc, ang, 95, 0)], 98, 120)}" fill="#ffe066"/>'
    out += f'<path d="{bell}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    out += f'<g transform="rotate({ang + 90} {bx:.1f} {by:.1f})">' + outlined(g.ellipse(bx, by, 178, 50), '#ffe066', INK) + outlined(g.ellipse(bx, by + 6, 126, 28), '#c2185b', INK * 0.8) + '</g>'
    return draw(out, MITTEN)


# ---- 4: eight feet (pun on 8') ------------------------------------------------------------------------------------
def leg(root, knee, ankle, col, sole, toe, seed) -> str:
    """A bent leg from inside the body out to a knee and down to a big round foot with a candy sole; toe is +1 or -1
    for the way the foot points."""
    P = bez(root, (knee[0] - toe * 30, knee[1] - 40), (knee[0] + toe * 30, knee[1] - 10), ankle, 18)
    out = outlined(sausage(P, 34, 30, seed), col, INK)
    fx, fy = ankle[0] + toe * 40, ankle[1] + 30
    out += outlined(lumpy(fx + toe * 4, fy + 36, 96, 36, 0, seed=seed + 50), sole, INK)
    out += outlined(lumpy(fx, fy, 92, 52, toe * 6, seed=seed), col, INK)
    out += f'<path d="{lumpy(ankle[0], ankle[1] + 6, 28, 28, 0, 3, 7, 0.02)}" fill="{col}"/>'
    return out


def v4_eight_feet() -> Image.Image:
    """Eight feet (the 8' drawbar): it stands up on eight legs, one after another, four bending out from behind its
    left side and four feet stepping out from under the mitten, big round pink feet with candy soles."""
    out = ''
    left = [((1320, 3600), (1130, 3560), (1010, 4030)), ((1315, 3720), (1180, 3700), (1140, 4070)),
            ((1335, 3840), (1250, 3830), (1270, 4100)), ((1380, 3930), (1350, 3940), (1400, 4115))]
    right = [((1470, 3900), (1520, 3980), (1540, 4115)), ((1500, 3860), (1640, 3950), (1670, 4120)),
             ((1520, 3820), (1760, 3930), (1800, 4110)), ((1540, 3780), (1880, 3900), (1930, 4090))]
    for k, (r, kn, an) in enumerate(left + right):
        out += leg(r, kn, an, [PINK, ROSE][k % 2], CANDY[k], -1 if k < 4 else 1, k)
    return draw(out, BODY + MITTEN)


# ---- 5: many hands (its own form dividing) ------------------------------------------------------------------------
def v5_many_hands() -> Image.Image:
    """Many hands: the raised hand splits again and again into a fan of waving mittens on long arms, spreading out
    round its shoulder like a peacock's tail, one more hand for every step."""
    out, roots = '', ''
    sx, sy = 1455.0, 3515.0
    cols = [PINK, ROSE, '#ff7eb6', '#ffb3cc', PINK, ROSE]
    for k, (ang, L) in enumerate([(236, 300), (206, 340), (176, 330), (148, 300), (122, 250)]):
        a = math.radians(ang)
        ex, ey = sx + math.cos(a) * L, sy + math.sin(a) * L
        P = bez((sx, sy), (sx + math.cos(a) * L * 0.35, sy + math.sin(a) * L * 0.35 - 25), (ex - math.cos(a) * L * 0.3, ey - math.sin(a) * L * 0.3), (ex, ey), 16)
        hx, hy = ex + math.cos(a) * 85, ey + math.sin(a) * 85
        out += outlined(tube(P, 40, 36), cols[k], INK)
        d, _ = mitten(hx, hy, 100, ang + 90 + 10, cols[k], k)
        out += outlined(d, cols[k], INK)
        out += f'<path d="{lumpy(ex, ey, 34, 34, 0, 1, 7, 0.02)}" fill="{cols[k]}"/>'
        roots += f'<path d="{lumpy(sx + math.cos(a) * 30, sy + math.sin(a) * 30, 44, 44, 0, 2, 7, 0.02)}" fill="{cols[k]}"/>'
    return draw(out + roots, MITTEN)


VERSIONS = [
    ('1-balloon-animal', 'Balloon animal', v1_balloon),
    ('2-big-hello', 'Big hello', v2_hello),
    ('3-fanfare', 'Fanfare horn', v3_fanfare),
    ('4-eight-feet', 'Eight feet', v4_eight_feet),
    ('5-many-hands', 'Many hands', v5_many_hands),
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


# ---- the build: balloon animal, one balloon per drawbar step --------------------------------------------------------
# Picked 2026-10-28: the creature twists up into a balloon animal from the bottom, one balloon inflating per drawbar
# step (body, neck, hand, head, snout, horn, ear), and on the last step the knot is tied at its snout and its balloon
# head opens one round eye. The painted creature fades away under the balloons (vanish over 0.1-0.9).
#
#     uv run scripts/wavingpink_endframes.py balloon   # progression strip and end frame
#     uv run scripts/wavingpink_endframes.py export    # docs/objects/lower-db3/build.json
import re as _re

STEP = 1 / 8
VANISH = (0.1, 0.9)
EYE_INK = 17
LOBE_INK = 'i0127'


def _win(k: int) -> tuple[float, float]:
    """The window of drawbar step k (1..8): it lands exactly on k/8."""
    return round((k - 1) * STEP, 4), round(k * STEP, 4)


def _r(q) -> list[float]:
    return [round(q[0], 1), round(q[1], 1)]


def balloon_items() -> list[dict]:
    """The balloons as sprite items, in drawing order (later on top); each arrives in its own drawbar step, growing
    from the end where it is twisted onto the one before."""
    body = bez((1395, 3612), (1355, 3700), (1342, 3830), (1372, 3950), 14)
    neck = bez(NECK_TOP, (1520, 3540), (1495, 3600), NECK_BOT, 12)
    hand = bez((1340, 3370), (1380, 3400), (1440, 3440), (1500, 3460), 12)
    horn = bez(HORN_TIP, (1430, 3225), (1490, 3280), HORN_BASE, 12)
    ear = bez((1650, 3235), (1680, 3215), (1715, 3200), (1748, 3192), 10)
    shapes = [  # (name, path, fill, step, grows from)
        ('horn', sausage(horn, 42, 42, 0), '#ff8fb8', 6, HORN_BASE),
        ('ear', sausage(ear, 32, 30, 5), '#ffb3cc', 7, ear[0]),
        ('hand', sausage(hand, 70, 70, 1), '#ff7eb6', 3, hand[-1]),
        ('body', sausage(body, 100, 96, 3), '#ff8fb8', 1, (1380, 4000)),
        ('neck', sausage(neck, 52, 52, 2), '#ff9fc4', 2, NECK_BOT),
        ('head', lumpy(*DOME, 82, 92, 10, seed=3), '#ff7eb6', 4, (1565, 3335)),
        ('snout', lumpy(1625, 3410, 100, 70, 4, seed=4), '#f9a3c4', 5, (1545, 3410)),
    ]
    # the outline of the lobe beside it (f244, no object's) is one of the creature's strokes and would fade with it:
    # keep a copy of it from the first step on
    x, y, w, h = m.IP[LOBE_INK]['bbox']
    items = [{'d': m.INKS[LOBE_INK], 'fill': '#000000', 'edge': 0, 'at': [round(x + w / 2, 1), round(y + h / 2, 1)], 'start': 0, 'end': 0.001, 'grow': 'scale'}]
    for name, d, fill, k, at in shapes:
        s, e = _win(k)
        items.append({'d': d, 'fill': fill, 'edge': INK, 'at': _r(at), 'start': s, 'end': e, 'grow': 'scale'})
    # the twists between balloons, each arriving with the balloon twisted on there
    for (x, y, rx, ry, rot, seed), k in [((1455, 3640, 32, 22, 20, 7), 2), ((1505, 3475, 30, 22, 60, 6), 3), ((1555, 3335, 34, 26, 30, 5), 4)]:
        s, e = _win(k)
        items.append({'d': lumpy(x, y, rx, ry, rot, seed=seed), 'fill': DEEP, 'edge': round(INK * 0.8, 1), 'at': [x, y],
                      'start': round(s + STEP * 0.3, 4), 'end': e, 'grow': 'scale'})
    # glossy shines, popping on as each balloon fills out
    for (x, y, rx, ry, rot), k in [((1320, 3720, 22, 60, 15), 1), ((1515, 3530, 30, 12, 100), 2), ((1375, 3385, 42, 15, 25), 3),
                                   ((1575, 3212, 36, 15, -30), 4), ((1610, 3385, 46, 15, -5), 5), ((1420, 3215, 40, 13, 40), 6),
                                   ((1700, 3203, 22, 9, -20), 7)]:
        s, e = _win(k)
        items.append({'d': lumpy(x, y, rx, ry, rot, seed=int(x), n=7, wob=0.05), 'fill': '#ffffff', 'edge': round(INK * 0.6, 1),
                      'at': [x, y], 'start': round(s + STEP * 0.5, 4), 'end': e, 'grow': 'scale'})
    # last step: the knot tied at the snout, and one round eye on the head balloon
    s, e = _win(8)
    knot = f'M{p(1716, 3402)}L{p(1770, 3380)}C{p(1792, 3398)} {p(1794, 3440)} {p(1770, 3457)}L{p(1716, 3432)}Z'
    items.append({'d': knot, 'fill': DEEP, 'edge': round(INK * 0.8, 1), 'at': [1716, 3417], 'start': s, 'end': round(s + STEP * 0.6, 4), 'grow': 'x'})
    ex, ey, er = 1628.0, 3268.0, 38.0
    items.append({'d': lumpy(ex, ey, er, er * 1.06, 0, seed=12, n=8, wob=0.03), 'fill': '#ffffff', 'edge': EYE_INK, 'at': [ex, ey],
                  'start': round(s + STEP * 0.3, 4), 'end': e, 'grow': 'scale'})
    items.append({'d': circle(ex + 8, ey + 6, 17), 'fill': '#000000', 'edge': 0, 'at': [ex + 8, ey + 6],
                  'start': round(s + STEP * 0.5, 4), 'end': e, 'grow': 'scale'})
    items.append({'d': circle(ex + 14, ey - 2, 6), 'fill': '#ffffff', 'edge': 0, 'at': [ex + 14, ey - 2],
                  'start': round(s + STEP * 0.7, 4), 'end': e, 'grow': 'scale'})
    return items


def _vanish_ink() -> list[str]:
    x, y, w, h = m.FP['f240']['bbox']
    out = []
    for sid in m.FP['f240']['ink']:
        bx, by, bw, bh = m.IP[sid]['bbox']
        if bx >= x - 40 and by >= y - 40 and bx + bw <= x + w + 40 and by + bh <= y + h + 40:
            out.append(sid)
    return out


def balloon_frame(t: float) -> Image.Image:
    """The app's stack at t: the creature's fill and ink fading (vanish), the balloons above everything (place over)."""
    gone = max(0.0, min(1.0, (t - VANISH[0]) / (VANISH[1] - VANISH[0])))
    tags = []
    for tag in m.FILL_TAGS:
        if 'id="f240"' in tag:
            tag = _re.sub(r'fill-opacity="([^"]*)"', lambda q: f'fill-opacity="{float(q.group(1)) * (1 - gone):.4f}"', tag)
        tags.append(tag)
    van = set(_vanish_ink())
    im = Image.new('RGBA', m.WASH.size, (255, 255, 255, 255))
    im.alpha_composite(m.WASH)
    im.alpha_composite(m.svg(''.join(tags)))
    im.alpha_composite(m.SCRIB)
    im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{d}"/>' for i, d in m.INKS.items() if i not in van) + '</g>'))
    if gone < 1:
        im.alpha_composite(m.svg(f'<g fill="#000" opacity="{1 - gone:.3f}">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in van) + '</g>'))
    im.alpha_composite(m.svg(g.sprite_svg(balloon_items(), t)))
    return im


def balloon_main() -> None:
    out = OUT.parent / 'balloon-animal'
    out.mkdir(parents=True, exist_ok=True)
    balloon_frame(1.0).save(out / 'end-frame.png')
    for name, frames in [('strip', [0, 0.25, 0.5, 0.75, 1.0]), ('steps', [k / 8 for k in range(9)])]:
        tiles = [balloon_frame(t) for t in frames]
        w, h = tiles[0].size
        sc = 0.42 if len(frames) == 5 else 0.3
        tw, th = int(w * sc), int(h * sc)
        strip = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        try:
            font = ImageFont.load_default(size=24)
        except TypeError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        strip.save(out / f'{name}.png')
    print('wrote', out)


def export() -> None:
    import json as _j
    build = {
        'label': "The pink creature waving: drag for the Lower 8' drawbar; it twists up into a pink balloon animal, "
                 'one balloon per step from the bottom, and its balloon head opens an eye',
        'effects': [
            {'effect': 'vanish', 'span': list(VANISH)},
            {'effect': 'sprites', 'place': 'over', 'items': balloon_items()},
        ],
    }
    path = ROOT / 'docs/objects/lower-db3/build.json'
    path.write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][1]['items']), 'shapes to', path)


if __name__ == '__main__' and 'balloon' in __import__('sys').argv[1:]:
    balloon_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
