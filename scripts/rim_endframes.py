# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Leslie on) for the tunnel rim: the pale blue band that curves round the left of the tunnel in the
golden pyramid, from the tunnel's top (where the pink worm's ring hooks over it) down behind the acorn frog.

    uv run scripts/rim_endframes.py          # the five end frames and sheet
    uv run scripts/rim_endframes.py roll     # the chosen curl: progression strip and end frame
    uv run scripts/rim_endframes.py export   # docs/objects/leslie-on/build.json
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
m.CROP = (2790, 1150, 1250, 1150)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/leslie-on/endframes'
p, outlined, circle, ellipse, tube, bez, crescent = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.crescent
INK = 15
RIM = 'f218'
PALE, BLUE, DEEP = '#A9CFDC', '#7DB3DB', '#4f86b8'
CANDY = ['#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b']
# painted shapes that sit in front of the rim: the worm and its ring, the mushroom, the frog
IN_FRONT = ['f220', 'f201', 'f206', 'f207']
C = (3420.0, 1840.0)  # roughly the centre of the rim's arc

PTS = [(float(a), float(b)) for a, b in re.findall(r'(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)', m.FILLS[RIM])]


def edge(deg: float, inner: bool = False) -> tuple[float, float]:
    """The rim's outer (or inner) edge in the direction deg from C (0 = right, 90 = up)."""
    a = math.radians(deg)
    best, bd = None, None
    for x, y in PTS:
        ang = math.degrees(math.atan2(-(y - C[1]), x - C[0]))
        if abs((ang - deg + 180) % 360 - 180) < 4:
            d = math.hypot(x - C[0], y - C[1])
            if bd is None or (d < bd if inner else d > bd):
                best, bd = (x, y), d
    return best or (C[0] + math.cos(a) * 300, C[1] - math.sin(a) * 300)


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sx=1.0, sy=1.0) -> str:
    """A lumpy, hand-drawn round shape: n bumps round (x, y), a closed Catmull-Rom curve."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr * sx, y + math.sin(a) * rr * sy))
    return smooth(P)


def smooth(P, closed=True) -> str:
    n = len(P)
    d = f'M{p(*P[0])}'
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = P[i - 1] if (closed or i) else P[0], P[i], P[(i + 1) % n], P[(i + 2) % n] if (closed or i + 2 < n) else P[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + ('Z' if closed else '')


def rim_clip(body: str, cid: str = 'rim') -> str:
    return f'<defs><clipPath id="{cid}"><path d="{m.FILLS[RIM]}"/></clipPath></defs><g clip-path="url(#{cid})">{body}</g>'


def rim_ink() -> str:
    return '<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(RIM)) + '</g>'


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


def eye(cx, cy, r, look=(0.15, 0.1)) -> str:
    out = outlined(lump(cx, cy, r, 7, 0.06, 8), '#ffffff', INK * 0.9)
    out += outlined(circle(cx + look[0] * r, cy + look[1] * r, r * 0.5), '#ffe066', INK * 0.75)
    out += f'<path d="{circle(cx + look[0] * r, cy + look[1] * r, r * 0.26)}" fill="#000"/>'
    out += f'<path d="{circle(cx + look[0] * r + r * 0.15, cy + look[1] * r - r * 0.14, r * 0.1)}" fill="#fff"/>'
    return out


# ---- the band: where the rim lies along each direction from C --------------------------------------------------------
import io
import resvg_py

_BX, _BY, _BW, _BH = 2950, 1400, 700, 900


def _mask() -> Image.Image:
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_BX} {_BY} {_BW} {_BH}" width="{_BW}" height="{_BH}">'
           f'<path d="{m.FILLS[RIM]}" fill="#000"/></svg>')
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).getchannel('A')


MASK = _mask()


def band(deg: float) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Inner edge, middle and outer edge of the rim along the direction deg from C (0 = right, 90 = up)."""
    a = math.radians(deg)
    hit = []
    for r in range(0, 650, 2):
        x, y = C[0] + math.cos(a) * r, C[1] - math.sin(a) * r
        ix, iy = int(x - _BX), int(y - _BY)
        if 0 <= ix < _BW and 0 <= iy < _BH and MASK.getpixel((ix, iy)) > 128:
            hit.append(r)
    if not hit:
        return edge(deg, True), edge(deg), edge(deg)
    r0, r1 = hit[0], hit[-1]
    P = lambda r: (C[0] + math.cos(a) * r, C[1] - math.sin(a) * r)
    return P(r0), P((r0 + r1) / 2), P(r1)


def outer(deg: float) -> tuple[float, float]:
    return band(deg)[2]


def mid(deg: float) -> tuple[float, float]:
    return band(deg)[1]


def wpath(path, w0, w1, sway=0.0, waves=0.0) -> str:
    """A band along the centreline path, width w0 to w1, its edges swaying together (a ribbon), with a forked end."""
    n = len(path)
    L, R = [], []
    for i, (x, y) in enumerate(path):
        a, b = path[max(0, i - 1)], path[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = w0 + (w1 - w0) * u
        s = sway * math.sin(u * waves * math.pi)
        L.append((x + nx * (w + s), y + ny * (w + s)))
        R.append((x - nx * (w - s), y - ny * (w - s)))
    ex, ey = path[-1]
    px, py = path[-2]
    notch = (ex - (ex - px) * 2.2, ey - (ey - py) * 2.2)
    return 'M' + 'L'.join(p(*q) for q in L) + f'L{p(*notch)}L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def tubew(P, wf) -> str:
    """Like tube, but the half-width at each point is wf(u), u running 0..1 along P; round cap at the end."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = wf(i / (n - 1))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    w1 = wf(1.0)
    return 'M' + 'L'.join(p(*q) for q in L) + f'A{w1:.1f} {w1:.1f} 0 0 1 {p(*R[-1])}' + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def limb(P, w0, w1, col, edge_w=INK) -> str:
    """An outlined tapered limb whose root end is left open (no outline across it), so it joins what it grows from."""
    d = tube(P, w0, w1)
    return outlined(d, col, edge_w, d[:-1])


# ---- 1. snake: the rim turns into a pale blue snake curled round the tunnel ---------------------------------------
TOP_END = (3440.0, 1528.0)  # the rim's top end, at the tunnel's top, just right of the worm's ring


def v1_snake() -> Image.Image:
    """Curled snake: the rim becomes a snake coiled round the tunnel mouth; big candy spots along its back, its head
    rearing up off the top end over the tunnel with an open mouth and a round eye, its tail curling out at the foot."""
    marks = ''
    for k, deg in enumerate((112, 140, 166, 192, 218)):
        x, y = mid(deg)
        marks += outlined(lump(x, y, 46, 40 + k, 0.14, 7, math.radians(-deg), 1.0, 1.35), CANDY[(0, 3)[k % 2]], INK * 0.8)
    front = rim_clip(marks) + rim_ink()
    # neck along the tunnel's top, then rising
    P = bez((3425, 1535), (3560, 1545), (3540, 1430), (3650, 1405), 24)
    neck = tube(P, 24, 62)
    hx, hy = 3700.0, 1360.0
    head = lump(hx, hy, 118, 3, 0.06, 10, 0.3, 1.25, 0.85)
    jaw = f'M{p(hx + 30, hy + 30)}C{p(hx + 120, hy + 50)} {p(hx + 190, hy + 80)} {p(hx + 215, hy + 130)}C{p(hx + 150, hy + 150)} {p(hx + 50, hy + 125)} {p(hx - 30, hy + 75)}Z'
    mouth = f'M{p(hx + 40, hy + 30)}C{p(hx + 120, hy + 40)} {p(hx + 170, hy + 65)} {p(hx + 190, hy + 105)}C{p(hx + 130, hy + 105)} {p(hx + 70, hy + 85)} {p(hx + 10, hy + 60)}Z'
    tongue = tube(bez((hx + 110, hy + 80), (hx + 170, hy + 95), (hx + 200, hy + 140), (hx + 240, hy + 160), 12), 15, 13)
    fork = tube([(hx + 235, hy + 158), (hx + 290, hy + 150)], 13, 12) + tube([(hx + 235, hy + 158), (hx + 270, hy + 205)], 13, 12)
    out = outlined(neck, PALE, INK, neck[:-1])
    out += outlined(jaw, PALE, INK)
    out += outlined(mouth, '#f64c76', INK * 0.8)
    out += outlined(fork, '#ff5e7a', INK * 0.6) + outlined(tongue, '#ff5e7a', INK * 0.6)
    out += f'<path d="{tube(P[3:], 40, 52)}" fill="{PALE}"/>'  # melts the neck into the head
    out += outlined(head, PALE, INK)
    out += outlined(lump(hx - 60, hy + 25, 40, 9, 0.12, 7), CANDY[0], INK * 0.8)
    out += eye(hx + 10, hy - 30, 54)
    out += f'<path d="{ellipse(hx + 135, hy - 5, 10, 7, 20)}" fill="#000"/>'
    # the tail curling out of the foot, left along the ground and up
    T = bez((3150, 2110), (3060, 2160), (2960, 2150), (2930, 2060), 24)
    out += limb(T, 40, 18, PALE)
    return draw(front + out, IN_FRONT[1:])


# ---- 2. curl: the rim's top end grows on round the tunnel and rolls up into a big spiral --------------------------
def v2_curl() -> Image.Image:
    """Curl: the rim grows on from its top end round the tunnel's crown and rolls up into a big spiral, like a fern
    or a shell, candy striped as it winds."""
    path = bez((3425, 1535), (3540, 1540), (3640, 1520), (3700, 1430), 14)
    x, y = path[-1]
    a = math.atan2(path[-1][1] - path[-2][1], path[-1][0] - path[-2][0])
    r = 150.0
    n = 60
    for i in range(1, n + 1):
        step = 1.2 * 2 * math.pi / n
        rr = r * (1 - 0.55 * i / n)
        x += math.cos(a) * rr * step
        y += math.sin(a) * rr * step
        a -= step
        path.append((x, y))
    w = lambda u: 24 + 40 * math.sin(min(1, u * 5) * math.pi / 2) - 30 * max(0, u - 0.2) / 0.8
    N = len(path) - 1
    body = tubew(path, w)
    out = outlined(body, PALE, INK, body[:-1])
    # candy bands across the curl as it winds: chunks of the same tube, fill only, inside the outline
    for k, i0 in enumerate(range(16, N - 6, 9)):
        Ls, Rs = [], []
        for i in range(i0, i0 + 5):
            a, b = path[i - 1], path[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            dd = math.hypot(dx, dy) or 1
            nx, ny = -dy / dd, dx / dd
            ww = w(i / N) - 1
            Ls.append((path[i][0] + nx * ww, path[i][1] + ny * ww))
            Rs.append((path[i][0] - nx * ww, path[i][1] - ny * ww))
        out += f'<path d="M{"L".join(p(*q) for q in Ls + Rs[::-1])}Z" fill="{CANDY[(0, 3, 1)[k % 3]]}"/>'
    out += f'<path d="{body[:-1]}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    return draw(out, IN_FRONT[1:])


# ---- 3. plate spinning: the rim's top end rises as an arm and spins a big candy plate on one finger ----------------
def v3_plate() -> Image.Image:
    """Plate spinning: the rim's top end lifts up as a pale blue arm and spins a big candy plate on its fingertip, with
    whirl crescents round the plate."""
    P = bez((3425, 1535), (3600, 1555), (3720, 1560), (3790, 1500), 24)
    arm = tubew(P, lambda u: 24 + 24 * min(1, u * 3))
    out = outlined(arm, PALE, INK, arm[:-1])
    hx, hy = 3800.0, 1480.0
    finger = tube([(hx + 5, hy - 20), (hx + 10, hy - 115)], 23, 20)
    out += outlined(finger, PALE, INK)
    out += outlined(lump(hx, hy, 62, 11, 0.1, 8, 0.0, 1.0, 0.9), PALE, INK)
    out += outlined(tube([(hx - 50, hy - 5), (hx - 70, hy - 50)], 22, 20), PALE, INK * 0.9)  # thumb
    px, py = hx + 12, hy - 160
    plate = ellipse(px, py, 190, 66, -4)
    out += outlined(plate, '#ffe066', INK)
    out += outlined(ellipse(px, py - 4, 150, 50, -4), '#f64c76', INK * 0.8)
    out += outlined(ellipse(px, py - 6, 92, 30, -4), '#2DFFF4', INK * 0.8)
    out += outlined(ellipse(px, py - 7, 38, 13, -4), '#ffe066', INK * 0.7)
    for k, (a0, a1) in enumerate([(15, 65), (195, 245)]):
        d = g.crescent(px, py, 255, a0, a1, 70)
        d = m.warp_path(d, lambda x, y: (x, py + (y - py) * 0.5))
        out += outlined(d, '#ffffff', INK * 0.8)
    return draw(out, IN_FRONT[1:])


# ---- 4. ribbons: candy streamers whirl off the rim as if it were spinning ------------------------------------------
def v4_ribbons() -> Image.Image:
    """Twirling ribbons: big candy streamers fly off the rim's outside, swept round as if it were spinning fast."""
    out = ''
    rnd = random.Random(4)
    for k, deg in enumerate((92, 106, 148, 184, 220)):
        a = math.radians(deg)
        ox, oy = mid(deg)
        ox, oy = (ox + outer(deg)[0]) / 2, (oy + outer(deg)[1]) / 2
        tx, ty = math.sin(a), math.cos(a)   # along the rim, clockwise
        nx, ny = math.cos(a), -math.sin(a)  # outward
        L = (420 if k < 2 else 320) + rnd.random() * 80
        P0 = (ox, oy)
        P1 = (ox + tx * L * 0.15 + nx * 180, oy + ty * L * 0.15 + ny * 180)
        P2 = (ox + tx * L * 0.7 + nx * 120, oy + ty * L * 0.7 + ny * 120)
        P3 = (ox + tx * L + nx * 260, oy + ty * L + ny * 260)
        rb = wpath(bez(P0, P1, P2, P3, 30), 40, 36, 16, 3)
        out += outlined(rb, CANDY[(0, 1, 2, 3, 4)[k]], INK, rb[:-1])
    return draw(out, IN_FRONT)


# ---- 5. pinwheel blooms: three candy pinwheel flowers open on the rim ---------------------------------------------
def pinwheel(cx, cy, r, rot, cols, seed) -> str:
    out = ''
    n = 5
    rnd = random.Random(seed)
    for k in range(n):
        a = rot + k / n * 2 * math.pi
        tip = (cx + math.cos(a) * r * (0.95 + rnd.random() * 0.1), cy + math.sin(a) * r * (0.95 + rnd.random() * 0.1))
        back = (cx + math.cos(a + 0.95) * r * 0.62, cy + math.sin(a + 0.95) * r * 0.62)
        d = (f'M{p(cx + math.cos(a - 0.5) * r * 0.12, cy + math.sin(a - 0.5) * r * 0.12)}'
             f'C{p(cx + math.cos(a - 0.12) * r * 0.5, cy + math.sin(a - 0.12) * r * 0.5)} {p(cx + math.cos(a - 0.05) * r * 0.8, cy + math.sin(a - 0.05) * r * 0.8)} {p(*tip)}'
             f'C{p(cx + math.cos(a + 0.45) * r * 1.0, cy + math.sin(a + 0.45) * r * 1.0)} {p(cx + math.cos(a + 0.85) * r * 0.85, cy + math.sin(a + 0.85) * r * 0.85)} {p(*back)}'
             f'C{p(cx + math.cos(a + 0.6) * r * 0.4, cy + math.sin(a + 0.6) * r * 0.4)} {p(cx + math.cos(a + 0.2) * r * 0.2, cy + math.sin(a + 0.2) * r * 0.2)} {p(cx, cy)}Z')
        out += outlined(d, cols[k % len(cols)], INK * 0.9)
    out += outlined(lump(cx, cy, r * 0.24, seed, 0.12, 7), '#ffd23f', INK * 0.85)
    return out


def v5_pinwheels() -> Image.Image:
    """Pinwheel blooms: two big candy pinwheel flowers open out of the rim, their blades swirled as they turn."""
    out = ''
    for k, (deg, r) in enumerate([(150, 185), (208, 165)]):
        x, y = mid(deg)
        a = math.radians(deg)
        out += pinwheel(x + math.cos(a) * 70, y - math.sin(a) * 70, r, k * 0.7, [CANDY[(k + j) % 6] for j in (0, 1, 3)], 50 + k)
    return draw(out, IN_FRONT)


VERSIONS = [
    ('1-snake', 'Curled snake', v1_snake),
    ('2-curl', 'Curl', v2_curl),
    ('3-plate-spinning', 'Plate spinning', v3_plate),
    ('4-ribbons', 'Twirling ribbons', v4_ribbons),
    ('5-pinwheels', 'Pinwheel blooms', v5_pinwheels),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Leslie off)', m.compose())]
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


# ---- chosen: the curl ------------------------------------------------------------------------------------------------
# Picked under 5a: the rim's own form changes (rule 1), and a band rolling up into a spiral is the drawn reading of
# the rotating speaker switching on (rule 4). Made bigger than the end frame: the rim grows on from its top end over
# the tunnel's crown and rolls into a fat spiral of 2.2 turns, about 400 px across, in its own pale blue, with lumpy
# hand-drawn edges. Leslie is a switch, so it plays through on an 800 ms glide:
#   0-0.22     the band grows on from the rim's top end along the tunnel's crown (swept round the rim's arc centre);
#   0.2-0.76   it rolls up, one piece of about 200 degrees after another, each swept round the spiral's centre;
#   0.5-1      candy bands pop in along it, from the root to the tip of the curl, the last landing at 1.
# Each piece is an outlined layer then a fill-only layer a half-ink narrower, reaching back over the join, so the
# pieces and the root join without seams (as in the tongue). Inner turns are drawn after outer ones, so each turn
# lies over the one outside it, like a rolled-up band, and each piece's bands go in just after it so the next turn
# covers them too. It all goes `around`: above the ink, with the worm and its ring (f220) masked in front; the rim
# itself is not masked (an empty role `roll`), so the root lies over its end and hides the end's outline.
S = (3885.0, 1415.0)   # the spiral's centre
R0 = 200.0             # its outer radius where the band enters it
TH0 = -125.0           # where it enters (app degrees round S: 0 = right, 90 = up), rolling anticlockwise
TURNS = 2.2
ROOT_PT = (3418.0, 1533.0)  # inside the rim's top end, its flat start tucked under the worm's ring (masked in front)
NECK_N, PIECE_N, PIECES = 44, 66, 4
E = 2  # overlap at the joins, in points
BAND_COLS = ['#f64c76', '#c4a3f0', '#ffe066', '#2DFFF4']
GLIDE = 800


def app_ang(pt, c) -> float:
    return math.degrees(math.atan2(-(pt[1] - c[1]), pt[0] - c[0]))


def roll_path() -> tuple[list[tuple[float, float]], list[float]]:
    """The centreline from the rim's end to the spiral's tip, and the half-width at each point (lumpy)."""
    rnd = random.Random(218)
    ph = [rnd.random() * 6.3 for _ in range(4)]
    wob = lambda u: (1 + 0.09 * math.sin(2 * math.pi * 4.3 * u + ph[0]) + 0.06 * math.sin(2 * math.pi * 9.7 * u + ph[1])
                     + 0.035 * math.sin(2 * math.pi * 17.3 * u + ph[2]))
    # the spiral, by steps: the radius shrinks by about one band width per turn so the turns lie against each other
    hw = lambda f: 44 - 16 * f  # half-width along the spiral, f = 0..1
    total = TURNS * 360
    n = PIECE_N * PIECES
    sp, sw = [], []
    R = R0
    for i in range(n + 1):
        f = i / n
        th = math.radians(TH0 + total * f)
        rr = R + 5 * math.sin(f * 2 * math.pi * 5.1 + ph[3])
        sp.append((S[0] + math.cos(th) * rr, S[1] - math.sin(th) * rr))
        sw.append(hw(f))
        R -= (2 * hw(f) - 10) / 360 * (total / n)
    # the neck: from inside the rim's end along the tunnel's crown into the spiral, leaving along its tangent
    th = math.radians(TH0)
    tx, ty = -math.sin(th), -math.cos(th)  # screen direction of travel at the entry (anticlockwise)
    s0 = sp[0]
    neck = bez(ROOT_PT, (3560, 1470), (s0[0] - tx * 150, s0[1] - ty * 150), s0, NECK_N)
    nw = [27 + 17 * math.sin(min(1.0, k / NECK_N * 1.4) * math.pi / 2) for k in range(NECK_N + 1)]
    P = neck[:-1] + sp
    W = nw[:-1] + sw
    N = len(P) - 1
    W = [w * wob(i / N) for i, w in enumerate(W)]
    return P, W


def offsets(P, W, shrink=0.0):
    L, R = [], []
    n = len(P)
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = max(4.0, W[i] - shrink)
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L, R


def strip_d(L, R, i0, i1, cap=False, wcap=0.0) -> str:
    i0, i1 = max(0, i0), min(len(L) - 1, i1)
    d = 'M' + 'L'.join(p(*q) for q in L[i0:i1 + 1])
    if cap:
        d += f'A{wcap:.1f} {wcap:.1f} 0 0 1 {p(*R[i1])}'
    return d + 'L' + 'L'.join(p(*q) for q in R[i0:i1 + 1][::-1]) + 'Z'


def roll_item(d, fill, edge, at, s, e, **kw) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': 'scale'}
    o.update(kw)
    return o


def roll_items() -> list[dict]:
    P, W = roll_path()
    N = len(P) - 1
    Lo, Ro = offsets(P, W)
    Lf, Rf = offsets(P, W, INK / 2 + 1.5)
    # the segments: the neck, then the spiral's pieces
    cuts = [0, NECK_N] + [NECK_N + PIECE_N * (k + 1) for k in range(PIECES)]
    cuts[-1] = N
    times = [(0.0, 0.22)] + [(0.2 + 0.14 * k, 0.36 + 0.14 * k) for k in range(PIECES)]
    # bands: every so many points along it, popping in from the root to the tip over 0.5-1
    band_at = [i for i in range(30, N - 10, 19) if all(abs(i - c) > 2 * E + 5 for c in cuts[1:-1])]
    nb = len(band_at)
    items = []
    for k in range(len(cuts) - 1):
        i0, i1 = cuts[k], cuts[k + 1]
        last = k == len(cuts) - 2
        s, e = times[k]
        if k == 0:
            sw = {'from': round(app_ang(P[0], C) + 6, 2), 'to': round(app_ang(P[i1 + E], C) - 2, 2)}
            at = C
        else:
            a0 = TH0 + TURNS * 360 * (i0 - NECK_N) / (N - NECK_N)
            a1 = TH0 + TURNS * 360 * (i1 - NECK_N) / (N - NECK_N)
            sw = {'from': round(a0 - 4, 2), 'to': round(a1 + (30 if last else 4), 2)}
            at = S
        items.append(roll_item(strip_d(Lo, Ro, i0, i1 + (0 if last else E), last, W[N]), PALE, INK, at, s, e, sweep=sw))
        if k == 0:  # the root's fill reaches back into the rim's end, over the outlined root's flat start
            fd = strip_d(Lf, Rf, 0, i1, False)
            fsw = sw
            items.append(roll_item(root_fill(P, W), PALE, 0, P[0], 0.0, 0.06))
        else:
            fd = strip_d(Lf, Rf, i0 - 2 * E, i1, last, W[N] - INK / 2 - 1.5)
            fsw = {'from': round(sw['from'] - 10, 2), 'to': sw['to']}
        items.append(roll_item(fd, PALE, 0, at, s, e, sweep=fsw))
        for j, i in enumerate(band_at):
            if not (i0 < i < i1):
                continue
            q = band_at.index(i)
            bs = 0.5 + 0.38 * q / max(1, nb - 1)
            half = 4 + (q % 3 == 1)
            d = 'M' + 'L'.join(p(*pt) for pt in Lf[i - half:i + half + 1] + Rf[i - half:i + half + 1][::-1]) + 'Z'
            items.append(roll_item(d, BAND_COLS[q % 4], 0, P[i], bs, bs + 0.12))
    return items


def root_fill(P, W) -> str:
    """A fill-only lump at the root, reaching back into the rim's end, so the band grows out of it without a seam."""
    (x0, y0), (x1, y1) = P[0], P[3]
    a = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return ellipse(x0 - 4, y0 + 2, 30, W[0] - INK / 2 - 1.5, a)


def roll_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    im = m.compose()
    layer = m.svg(sprites_svg(roll_items(), t))
    cut = m.svg(f'<path d="{m.FILLS["f220"]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>').getchannel('A')
    a = layer.getchannel('A')
    layer.putalpha(Image.composite(Image.new('L', a.size, 0), a, cut))
    im.alpha_composite(layer)
    return im


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


def roll_strip(frames, out: Path, name: str) -> None:
    tiles = [roll_frame(t) for t in frames]
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
        d.text((x, 12), f'frame {tt:.2f}', fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    im.save(out / name)


def roll_main() -> None:
    m.CROP = (2950, 1020, 1250, 1180)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = OUT.parent / 'curl'
    out.mkdir(parents=True, exist_ok=True)
    roll_frame(1.0).save(out / 'end-frame.png')
    roll_strip([0, 0.25, 0.5, 0.75, 1.0], out, 'strip.png')
    roll_strip([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.85], out, 'steps.png')
    print('wrote', out, len(roll_items()), 'shapes')


LABEL = ("The tunnel rim: tap for the Leslie rotating speaker; it grows on over the tunnel's crown and rolls up into a "
         "fat pale blue spiral, and candy bands pop in along it as it spins")

if __name__ == '__main__' and 'roll' in __import__('sys').argv[1:]:
    roll_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': LABEL,
        'glide': GLIDE,
        'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['roll'], 'front': ['f220'], 'items': roll_items()}],
        'objectParts': {'roll': []},
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(roll_items()), 'shapes')
