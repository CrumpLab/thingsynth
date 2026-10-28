# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (percussion decay at Fast) for the pink cap: the pale pink top band of the striped stack beside the
sleepy green creature, bottom left, with its own half-lidded purple eye.

    uv run scripts/cap_endframes.py          # the five end frames and sheet
    uv run scripts/cap_endframes.py hare     # the chosen hare: progression strip and end frame
    uv run scripts/cap_endframes.py export   # docs/objects/perc-decay/build.json
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
m.CROP = (650, 3480, 1350, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/perc-decay/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 17          # the cap's own outlines
FINE = 12         # small new features
PINK, DEEP, PURPLE, RED = '#EB9BB2', '#E84F7C', '#7C4FE8', '#F64C65'
IRIS = '#9b2cf2'
CAP, HEAD = 'f004', 'f007'
STRIPES = ['f004', 'f003', 'f002', 'f013']
EYE = (1368.0, 4122.0)  # the cap's own purple eye
HINGE = (1105.0, 4150.0)


def subpaths(fid: str) -> list[list[tuple[float, float]]]:
    out = []
    for sp in re.findall(r'M[^M]*', m.FILLS[fid]):
        n = [float(v) for v in re.findall(r'-?\d+\.?\d*', sp)]
        out.append(list(zip(n[::2], n[1::2])))
    return out


CAP_OUT = subpaths(CAP)[0]  # the outer edge, without the hole the eye sits in
_r = max(range(len(CAP_OUT)), key=lambda i: CAP_OUT[i][0] - 0.3 * CAP_OUT[i][1])
BOTTOM = [q for q in CAP_OUT[_r:] if q[1] > 4060] + [q for q in CAP_OUT[:40] if q[0] > 1150]  # tip, along the bottom, left


def poly(P) -> str:
    return 'M' + 'L'.join(p(*q) for q in P) + 'Z'


def blob(P, seed=0, wob=0.0) -> str:
    """A closed, hand-drawn curve through P (Catmull-Rom), each point nudged a little."""
    rnd = random.Random(seed)
    P = [(x + (rnd.random() - 0.5) * wob, y + (rnd.random() - 0.5) * wob) for x, y in P]
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        d += f'C{p(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)} {p(p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)} {p(*p2)}'
    return d + 'Z'


def lump(x, y, r, seed, wob=0.13, n=8) -> str:
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    return blob(P)


def rot(q, ang, c=HINGE):
    a = math.radians(ang)
    dx, dy = q[0] - c[0], q[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def open_eye(x, y, rx, ry, look=(0.25, -0.1), seed=1) -> str:
    out = outlined(blob([(x + math.cos(a) * rx, y + math.sin(a) * ry) for a in [k / 9 * 2 * math.pi for k in range(9)]], seed, 8),
                   '#ffffff', FINE + 2)
    ix, iy = x + look[0] * rx, y + look[1] * ry
    out += outlined(lump(ix, iy, ry * 0.66, seed + 5, 0.06), IRIS, FINE)
    out += f'<path d="{circle(ix + 4, iy + 2, ry * 0.32)}" fill="#000"/>'
    out += f'<path d="{circle(ix - ry * 0.2, iy - ry * 0.24, ry * 0.13)}" fill="#fff"/>'
    return out


def draw(front: str = '', again: list[str] | None = None, over: str = '', hide_ink: list[str] | None = None,
         fill_over: dict[str, str] | None = None) -> Image.Image:
    """New shapes drawn in front of the painting, then the named painted shapes (and their ink, less hide_ink) laid
    back on top; `over` goes on top of everything."""
    hide = set(hide_ink or [])
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)} - hide)
    try:
        im = m.compose(front=front or '<g/>', fill_over=fill_over, ink_over={i: 'M0 0Z' for i in hide})
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


EYE_INK = ['i0930', 'i0116', 'i0124', 'i0940']  # the purple eye's rim and its lashed lid line
CAP_SOLID = {CAP: poly(CAP_OUT)}                # the cap without its eye hole


def ear(base, ang, length, width, bend, seed) -> tuple[str, str]:
    """A long hare's ear from base along ang (degrees), its tip bending sideways by bend; and its inner lining."""
    a = math.radians(ang)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)

    def at(u, v):
        b = bend * u * u
        return (base[0] + ux * u * length + nx * (v + b), base[1] + uy * u * length + ny * (v + b))
    prof = [(0, 0.40), (0.25, 0.52), (0.55, 0.50), (0.8, 0.38), (0.95, 0.18)]
    side = [at(u, w * width) for u, w in prof]
    tip = at(1.0, 0)
    other = [at(u, -w * width) for u, w in reversed(prof)]
    outer = blob(side + [tip] + other, seed, 22)
    lin = [(0.24, 0.2), (0.5, 0.25), (0.75, 0.18), (0.87, 0.08)]
    inner = blob([at(u, w * width) for u, w in lin] + [at(0.93, 0)] + [at(u, -w * width) for u, w in reversed(lin)] + [at(0.15, 0)], seed + 3, 6)
    return outer, inner


def v1_hare() -> Image.Image:
    """Hare: the cap turns into a hare (Fast): two long pink ears spring up out of it, its sleepy purple eye opens wide
    and a round nose swells at its tip."""
    front = ''
    for base, ang, L, W, b, s in [((1215, 4075), -114, 400, 120, -70, 1), ((1395, 4060), -76, 430, 125, 95, 2)]:
        o, i = ear(base, ang, L, W, b, s)
        front += outlined(o, PINK, INK) + outlined(i, DEEP, FINE)
    over = open_eye(*EYE, 92, 74, (0.3, -0.15))
    over += outlined(lump(1552, 4100, 54, 7, 0.1), DEEP, FINE + 2)
    over += f'<path d="{ellipse(1538, 4082, 16, 11, -20)}" fill="#ffd0dc"/>'
    return draw(front, [CAP, HEAD], over, EYE_INK, CAP_SOLID)


def v2_jaws() -> Image.Image:
    """Snap: the cap is a jaw. It hinges up from the creature's head, opening a dark mouth over the deep pink stripe
    with a candy tongue and big round teeth, and its purple eye pops open on top."""
    ang = -32
    up = [rot(q, ang) for q in CAP_OUT]
    upb = [rot(q, ang) for q in BOTTOM]
    wedge = poly(upb + BOTTOM[::-1])
    mouth = outlined(poly(CAP_OUT), '#5c0f33', INK) + outlined(wedge, '#5c0f33', INK)
    mouth += f'<path d="{poly(CAP_OUT)}" fill="#5c0f33"/><path d="{wedge}" fill="#5c0f33"/>'
    # the tongue lying along the lower jaw, its tip curling up at the front
    lo = BOTTOM[::-1]  # the lower jaw, left to right
    top = [(x - 10, y - 58 - 30 * math.sin(math.pi * k / (len(lo) - 1))) for k, (x, y) in enumerate(lo)][::8]
    tongue = blob([(x, y - 6) for x, y in lo[::8]][1:-1] + [(1590, 4035), (1560, 3995)] + top[::-1][1:], 4, 6)
    mouth += outlined(tongue, '#ff6f91', FINE + 2)
    mouth += outlined(blob([(1280, 4170), (1400, 4135), (1480, 4080), (1488, 4092), (1405, 4152), (1285, 4185)], 5, 0), '#e04a72', 0)
    teeth = ''
    for k, u in enumerate((0.25, 0.48, 0.7)):  # upper teeth hang from the lifted jaw, lower ones stand on the stripe
        i = int(u * (len(BOTTOM) - 1))
        tx, ty = rot(BOTTOM[i], ang)
        teeth += outlined(blob([(tx - 30, ty - 12), (tx + 30, ty - 12), (tx + 26, ty + 40), (tx, ty + 58), (tx - 26, ty + 40)], k, 4), '#fffbe6', FINE)
        bx, by = BOTTOM[int((u + 0.1) * (len(BOTTOM) - 1))]
        teeth += outlined(blob([(bx - 28, by + 12), (bx + 28, by + 12), (bx + 24, by - 34), (bx, by - 52), (bx - 24, by - 34)], k + 9, 4), '#fffbe6', FINE)
    jaw = outlined(poly(up), PINK, INK)
    ex, ey = rot(EYE, ang)
    jaw += open_eye(ex, ey, 88, 70, (0.35, 0.0))
    return draw(mouth + teeth + jaw, [HEAD], '', EYE_INK, {CAP: 'M0 0Z'})


def v3_party_hat() -> Image.Image:
    """Party hat: the cap's dome rises into a tall party cone banded in the cap's own stripes, a big yellow pom-pom on
    top and two candy streamers curling off it."""
    L, R, A = (1140.0, 4075.0), (1515.0, 4070.0), (1405.0, 3650.0)
    side = lambda a, b, n: [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u) for u in [k / n for k in range(n)]]
    cone = blob(side(L, A, 5)[:] + side(A, R, 5) + [(1330, 4110)], 3, 14)
    bands = ''
    cols = [DEEP, PURPLE, PINK, RED, '#ffe066', DEEP]
    for k in range(6):  # wavy bands slanting across the cone, bottom up
        y0 = 4120 - k * 78
        bands += outlined(f'M1000 {y0 - 78}C1200 {y0 - 126} 1400 {y0 - 26} 1700 {y0 - 98}L1700 {y0}C1400 {y0 + 72} 1200 {y0 - 48} 1000 {y0}Z',
                          cols[k], FINE)
    front = f'<defs><clipPath id="cone"><path d="{cone}"/></clipPath></defs><path d="{cone}" fill="{PINK}"/>'
    front += f'<g clip-path="url(#cone)">{bands}</g>'
    front += f'<path d="{cone}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    for P, col, s in [(bez(A, (1250, 3560), (1130, 3640), (1170, 3760), 20), '#2DFFF4', 1),
                      (bez(A, (1580, 3560), (1700, 3660), (1640, 3790), 20), '#a8ec6b', 2)]:
        front += outlined(tube(P, 24, 16), col, FINE)
    front += outlined(lump(A[0], A[1] - 30, 78, 11, 0.16, 9), '#ffe066', INK)
    front += outlined(lump(A[0] - 22, A[1] - 52, 28, 12, 0.1), '#fff6b0', 0)
    return draw(front, [CAP, HEAD])


def bottom_y(x: float) -> float:
    """The cap's bottom edge (its join with the deep pink stripe) at x."""
    P = sorted(BOTTOM)
    if x <= P[0][0]:
        return P[0][1]
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
    return P[-1][1]


def v4_toadstool() -> Image.Image:
    """Toadstool: decay as something living. The cap swells into a big lopsided toadstool, white spots across it and a
    frilled cream rim of gills under its edge, its sleepy purple eye still on its brow."""
    xs = [1060 + k * 58 for k in range(11)]
    rim = [(x, min(bottom_y(x), 4235) if x < 1545 else 4120 - (x - 1545) * 0.5) for x in xs]
    scal = []
    for (x0, y0), (x1, y1) in zip(rim, rim[1:]):
        scal += [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 20)]
    scal.append(rim[-1])
    gill = outlined(blob(scal + [(x, y - 80) for x, y in rim[::-2]], 4, 3), '#FFF9AD', FINE + 2)
    edge = [(x, y - 36) for x, y in rim]
    dome = blob(edge[::2][::-1][:1] + [(1665, 4020), (1620, 3880), (1500, 3790), (1370, 3790), (1265, 3845), (1195, 3950),
                                         (1110, 4030), (1050, 4130)] + edge[::2], 8, 10)
    front = gill + outlined(dome, DEEP, INK)
    for x, y, r, s in [(1235, 3960, 52, 1), (1390, 3870, 56, 2), (1540, 3880, 50, 3), (1610, 4010, 38, 4), (1150, 4060, 34, 5),
                       (1265, 4050, 30, 6)]:
        front += outlined(lump(x, y, r, s + 20, 0.16, 7), '#fffdf4', FINE)
    # the sleepy eye, kept as painted: the hole in the cap filled purple, its rim and lashed lid laid back over it
    front += f'<path d="{poly(subpaths(CAP)[1])}" fill="{IRIS}"/>'
    front += '<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in EYE_INK) + '</g>'
    return draw(front, [HEAD], '', EYE_INK, {CAP: 'M0 0Z'})


def ribbon(P, w0, w1, notch=40) -> str:
    """A ribbon along P, w0 to w1 wide, its end cut in a swallowtail."""
    n = len(P)
    Lf, Rt = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = w0 + (w1 - w0) * i / (n - 1)
        Lf.append((x + nx * w, y + ny * w))
        Rt.append((x - nx * w, y - ny * w))
    ex, ey = P[-1]
    dx, dy = ex - P[-2][0], ey - P[-2][1]
    d = math.hypot(dx, dy)
    nt = (ex - dx / d * notch, ey - dy / d * notch)
    return 'M' + 'L'.join(p(*q) for q in Lf) + f'L{p(*nt)}L' + 'L'.join(p(*q) for q in Rt[::-1]) + 'Z'


def v5_streamers() -> Image.Image:
    """Streamers: Fast. The cap's own stripes pull out behind it to the right into long waving ribbons, as if it were
    racing off, pink, deep pink, purple and red."""
    front = ''
    rows = [((1480, 4085), PINK, 0), ((1490, 4200), DEEP, 1.2), ((1450, 4320), PURPLE, 2.3), ((1440, 4420), RED, 3.1)]
    for (x, y), col, ph in rows[::-1]:
        P = [(x + u * 430, y - u * 150 + math.sin(u * 2 * math.pi * 1.1 + ph) * 50 * u) for u in [k / 30 for k in range(31)]]
        front += outlined(ribbon(P, 46, 30, 36), col, INK)
    return draw(front, STRIPES + [HEAD])


VERSIONS = [
    ('1-hare', 'Hare', v1_hare),
    ('2-snap', 'Snap', v2_jaws),
    ('3-party-hat', 'Party hat', v3_party_hat),
    ('4-toadstool', 'Toadstool', v4_toadstool),
    ('5-streamers', 'Streamers', v5_streamers),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Slow)', m.compose())]
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


# ---- chosen: hare -------------------------------------------------------------------------------------------------
# Picked under 5a: the cap, which already has its own eye, morphs into an animal, and the morph is a playful literal
# reading of the switch: the squat painted cap is the tortoise (Slow), the hare is Fast. A switch, so one change plays
# through on a 750 ms glide: the sleepy eye opens first (a pink lid patch swells over it, then the white, the iris,
# the pupil and the glint), the left ear springs up, then the right with an overshoot (a longer ear springs up first
# and sinks back into it), and the round nose pops out at the tip last. The ears sit behind the cap ('around', the
# green head in front too); the eye and nose go over everything.
#
#     uv run scripts/cap_endframes.py hare     # progression strip and end frame
#     uv run scripts/cap_endframes.py export   # docs/objects/perc-decay/build.json
GLIDE = 750
NOSE = (1552.0, 4100.0)
# (base, angle, length, width, bend, seed, start); both on the cap's right half, clear of the cyan creature's eye
# above its left half: the left ear shorter and nearly upright, the right one longer, leaning out and bending over
EARS = [((1300.0, 4058.0), -99.0, 405.0, 118.0, 45.0, 11, 0.24),
        ((1425.0, 4060.0), -70.0, 430.0, 126.0, 100.0, 23, 0.46)]
# the lid patch: a fill-only pink shape inside the cap that covers the sleepy eye's rim and lashed lid line
PATCH = blob([(1205, 4075), (1255, 4046), (1345, 4040), (1435, 4044), (1495, 4075), (1502, 4122), (1462, 4168), (1400, 4198),
              (1300, 4204), (1228, 4170), (1200, 4120)], 31, 0)


def hare_ear(base, ang, length, width, bend, seed, stretch=1.0) -> tuple[str, str]:
    """A lumpy, lopsided hare's ear from base along ang (degrees), its tip bending sideways by bend; and its lining.
    Each side has its own uneven profile, so no two ears (and no two sides) match."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    L = length * stretch

    def at(u, v):
        b = bend * u * u * stretch
        return (base[0] + ux * u * L + nx * (v + b), base[1] + uy * u * L + ny * (v + b))
    us = [0.0, 0.16, 0.34, 0.52, 0.68, 0.82, 0.93]
    shape = [0.40, 0.50, 0.55, 0.52, 0.45, 0.34, 0.18]
    left = [at(u, w * width * (0.88 + rnd.random() * 0.26)) for u, w in zip(us, shape)]
    right = [at(u, -w * width * (0.85 + rnd.random() * 0.24)) for u, w in zip(us, shape)]
    tip = at(1.0, (rnd.random() - 0.5) * width * 0.25)
    outer = blob(left + [tip] + right[::-1], seed, 26)
    lin = [(0.22, 0.2), (0.4, 0.25), (0.56, 0.24), (0.7, 0.17), (0.79, 0.08)]
    li = [at(u, w * width * (0.85 + rnd.random() * 0.3)) for u, w in lin]
    ri = [at(u, -w * width * (0.8 + rnd.random() * 0.3)) for u, w in lin]
    inner = blob(li + [at(0.84, width * 0.03)] + ri[::-1] + [at(0.14, 0)], seed + 3, 12)
    return outer, inner


def it(d, fill, edge, at, s, e, out=None, grow='scale') -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


def ear_items() -> list[dict]:
    """The ears, behind the cap: each springs up from its base, its deep pink lining following."""
    items = []
    for k, (base, ang, L, W, b, seed, s) in enumerate(EARS):
        if k == 1:  # the overshoot: a longer ear springs up first and sinks back behind the real one
            o, i = hare_ear(base, ang, L, W, b, seed, 1.14)
            items += [it(o, PINK, INK, base, s, s + 0.16, (s + 0.18, s + 0.32)),
                      it(i, DEEP, FINE, base, s + 0.03, s + 0.18, (s + 0.18, s + 0.32))]
        o, i = hare_ear(base, ang, L, W, b, seed)
        items += [it(o, PINK, INK, base, s + 0.02, s + 0.24), it(i, DEEP, FINE, base, s + 0.07, s + 0.27)]
    return items


def face_items() -> list[dict]:
    """The eye opening wide over the sleepy one, and the nose: over everything."""
    x, y = EYE
    rx, ry, look = 92, 74, (0.3, -0.15)
    ix, iy = x + look[0] * rx, y + look[1] * ry
    white = blob([(x + math.cos(a) * rx, y + math.sin(a) * ry) for a in [k / 9 * 2 * math.pi for k in range(9)]], 1, 8)
    items = [it(PATCH, PINK, 0, EYE, 0.0, 0.1),
             it(white, '#ffffff', FINE + 2, EYE, 0.04, 0.24, grow='y'),
             it(lump(ix, iy, ry * 0.66, 6, 0.06), IRIS, FINE, (ix, iy), 0.12, 0.28),
             it(circle(ix + 4, iy + 2, ry * 0.32), '#000', 0, (ix + 4, iy + 2), 0.16, 0.3),
             it(circle(ix - ry * 0.2, iy - ry * 0.24, ry * 0.13), '#fff', 0, (ix - ry * 0.2, iy - ry * 0.24), 0.22, 0.34)]
    nx, ny = NOSE
    items += [it(lump(nx, ny, 54, 7, 0.1), DEEP, FINE + 2, (nx - 30, ny), 0.78, 0.94),
              it(ellipse(nx - 14, ny - 18, 16, 11, -20), '#ffd0dc', 0, (nx - 14, ny - 18), 0.86, 1.0)]
    return items


def around_mask(body: str, front: list[str]) -> str:
    """The app's 'around' placement: above the ink, masked out over the cap and the front fills plus a 44 px band, so
    they and their outlines stay in front."""
    cut = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in [CAP] + front)
    return (f'<defs><mask id="ar" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect width="4950" height="4950" fill="#fff"/>{cut}</mask></defs><g mask="url(#ar)">{body}</g>')


def hare_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    im = m.compose(front=around_mask(g.sprite_svg(ear_items(), t), [HEAD]))
    face = g.sprite_svg(face_items(), t)
    if face:
        im.alpha_composite(m.svg(face))
    return im


def hare_main() -> None:
    out = OUT.parent / 'hare'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [hare_frame(t) for t in frames]
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
        d.text((x, 12), f'frame {tt:.2f}' + ('  Slow' if tt == 0 else '  Fast' if tt == 1 else ''), fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    print('wrote', out)


if __name__ == '__main__' and 'hare' in __import__('sys').argv[1:]:
    hare_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The pink cap: tap for percussion decay Slow or Fast; at Fast it turns into a hare: its sleepy eye opens '
                 'wide, two long ears spring up and its nose pops out',
        'glide': GLIDE,
        'effects': [{'effect': 'sprites', 'place': 'around', 'front': [HEAD], 'items': ear_items()},
                    {'effect': 'sprites', 'place': 'over', 'items': face_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(ear_items()) + len(face_items()), 'shapes')
