# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower-manual vibrato on) for the river bank: the long, winding dark green ribbon that runs from
under the pink flower creature, down the left of the pale blue pool and along its bottom edge to the purple bulb.

    uv run scripts/bank_endframes.py          # the five end frames and sheet
    uv run scripts/bank_endframes.py chorus   # the chosen frog chorus: progression strip and end frame
    uv run scripts/bank_endframes.py export   # docs/objects/vib-lower/build.json
"""
from __future__ import annotations

import importlib.util
import io
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (1260, 1950, 1420, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/vib-lower/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
BANK = 'f157'
BULB = ['f080', 'f081']  # the purple bulb with the cyan ring, in front of the bank's right end

# ---- the bank's shape: a centreline down its middle, with the half-width on each side -------------------------------
_ROUGH = [(1512, 2348), (1551, 2434), (1595, 2514), (1654, 2580), (1720, 2639), (1793, 2683), (1867, 2720),
          (1940, 2749), (2013, 2771)]


def _mask(d: str, box=(1380, 2300, 1120, 560)) -> tuple[np.ndarray, tuple]:
    x, y, w, h = box
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{w}" height="{h}">'
           f'<path d="{d}" fill="#000"/></svg>')
    im = Image.open(io.BytesIO(bytes(m.resvg_py.svg_to_bytes(svg_string=doc)))).convert('RGBA')
    return np.array(im.getchannel('A')) > 128, box


def _resample(P, n):
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + math.dist(a, b))
    out = []
    for i in range(n):
        s = L[-1] * i / (n - 1)
        k = max(j for j in range(len(L) - 1) if L[j] <= s + 1e-9) if s < L[-1] else len(L) - 2
        u = (s - L[k]) / ((L[k + 1] - L[k]) or 1)
        out.append((P[k][0] + (P[k + 1][0] - P[k][0]) * u, P[k][1] + (P[k + 1][1] - P[k][1]) * u))
    return out


def _bank_frame(n=24):
    """Points down the bank's middle with the unit normal (pointing up/right, toward the pool) and the distance to
    each edge."""
    M, (bx, by, bw, bh) = _mask(m.FILLS[BANK])
    inside = lambda x, y: 0 <= int(x - bx) < bw and 0 <= int(y - by) < bh and M[int(y - by), int(x - bx)]
    P = _resample(_ROUGH, n)
    out = []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = dy / d, -dx / d  # left of travel: toward the pool
        if ny > 0 and nx < 0:
            nx, ny = -nx, -ny
        up = next((s for s in range(1, 300) if not inside(x + nx * s, y + ny * s)), 0)
        dn = next((s for s in range(1, 300) if not inside(x - nx * s, y - ny * s)), 0)
        c = (up - dn) / 2  # recentre on the band
        out.append(((x + nx * c, y + ny * c), (nx, ny), (up + dn) / 2, (up + dn) / 2))
    return out


FRAME = _bank_frame()


def at(u: float):
    """The bank at fraction u along it (0 = the top end under the flower creature, 1 = the bulb): middle point, normal
    toward the pool, half-widths toward the pool and away from it."""
    k = max(0, min(len(FRAME) - 1, round(u * (len(FRAME) - 1))))
    return FRAME[k]


def draw(front: str = '', again: list[str] | None = None, over: str = '', **kw) -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>', **kw)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im



def pt(u: float, off: float = 0.0):
    """A point on the bank at fraction u (0 the top end, 1 where it thins under the pool), moved `off` px along the
    normal toward the pool (negative: toward the path); and the normal."""
    f = max(0.0, min(1.0, u)) * (len(FRAME) - 1)
    k = min(int(f), len(FRAME) - 2)
    a = f - k
    (x0, y0), (nx0, ny0), h0, _ = FRAME[k]
    (x1, y1), (nx1, ny1), h1, _ = FRAME[k + 1]
    x, y = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
    nx, ny = nx0 + (nx1 - nx0) * a, ny0 + (ny1 - ny0) * a
    d = math.hypot(nx, ny) or 1
    nx, ny = nx / d, ny / d
    return (x + nx * off, y + ny * off), (nx, ny), h0 + (h1 - h0) * a


def closed(P) -> str:
    """A smooth closed curve through P (Catmull-Rom)."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def opened(P) -> str:
    """A smooth open curve through P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d


def lump(x, y, rx, ry=None, seed=0, wob=0.12, n=9, rot=0.0) -> str:
    """A lumpy, hand-drawn oval round (x, y), turned by rot (degrees)."""
    ry = rx if ry is None else ry
    rnd = random.Random(seed)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * c - v * s, y + u * s + v * c))
    return closed(P)


def sides(P, hw):
    """The two edges of a band of half-width hw(i/(n-1)) round the centreline P."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = hw(i / (n - 1))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L, R


def band(P, hw, cap=True) -> tuple[str, str]:
    """An outlined band round the centreline P: (fill path, outline path). The start end is left open (it grows out
    of something); the far end is rounded when cap."""
    L, R = sides(P, hw)
    if cap:
        (x, y), (x2, y2) = P[-1], P[-2]
        dx, dy = x - x2, y - y2
        d = math.hypot(dx, dy) or 1
        w = hw(1.0)
        tip = (x + dx / d * w * 0.9, y + dy / d * w * 0.9)
        edge = L + [tip] + R[::-1]
    else:
        edge = L + R[::-1]
    return opened(edge) + 'Z', opened(edge)


def blade(P, w0, seed=0) -> str:
    """A leaf blade: a band tapering from w0 to a point."""
    return band(P, lambda u: w0 * (1 - u) ** 0.8 + 1, cap=False)


def crescent(cx, cy, r, a0, a1, w) -> str:
    """A motion crescent from angle a0 to a1 (degrees) round (cx, cy), thickest in the middle: an outlined fill."""
    n = 24
    out, inn = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        t = w * math.sin(math.pi * u)
        out.append((cx + math.cos(a) * (r + t / 2), cy + math.sin(a) * (r + t / 2)))
        inn.append((cx + math.cos(a) * (r - t / 2), cy + math.sin(a) * (r - t / 2)))
    return opened(out + inn[::-1]) + 'Z'


def not_bank(body: str, key: str = 'nb') -> str:
    """Draw body only outside the bank (the app's "around" place: the bank's own shape stays in front)."""
    x, y, w, h = m.CROP
    return (f'<defs><mask id="{key}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/><path d="{m.FILLS[BANK]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/></mask></defs>'
            f'<g mask="url(#{key})">{body}</g>')


def ol(d, colour, w=INK, line=None) -> str:
    return outlined(d, colour, w, line)


# ---- the five --------------------------------------------------------------------------------------------------------
SERPENT, BELLY, FIN, MOUTH = '#5fc24a', '#d4f57a', '#ff5ea8', '#e0466a'


def wide_eye(x, y, r, look=(0.25, 0.15)) -> str:
    out = ol(lump(x, y, r, r * 1.05, 11, 0.06, 8), '#ffffff', INK * 0.9)
    px, py = x + look[0] * r, y + look[1] * r
    out += f'<path d="{lump(px, py, r * 0.5, r * 0.55, 12, 0.05, 8)}" fill="#111"/>'
    out += f'<path d="{circle(px + r * 0.16, py - r * 0.18, r * 0.15)}" fill="#fff"/>'
    return out


def v1_serpent() -> Image.Image:
    """River serpent: the bank rears up into a green serpent, humps arching out of it into the pool, its round top
    end lifting into a head that sings with its mouth wide open."""
    humps = ''
    # out in the pool past the bank's foot: humps arching out of the water, then a candy tail fin
    for k, (xa, xb, yb, h) in enumerate([(2030, 2230, 2742, 200), (2290, 2470, 2748, 175)]):
        P = []
        for i in range(25):
            s = i / 24
            a = math.pi * (1 - s)
            P.append(((xa + xb) / 2 + math.cos(a) * (xb - xa) / 2, yb - math.sin(a) * h))
        L, R = sides(P, lambda u: 44)
        humps += f'<path d="{opened(L + R[::-1])}Z" fill="{SERPENT}"/>'
        humps += f'<path d="{opened(L)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
        humps += f'<path d="{opened(R)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
        for j in range(3):  # a frilly candy fin along each hump's crest
            q = P[7 + j * 5]
            a = math.atan2(q[1] - yb, q[0] - (xa + xb) / 2)
            humps = ol(lump(q[0] + math.cos(a) * 52, q[1] + math.sin(a) * 52, 42, 30, 40 + k * 5 + j, 0.12, 7,
                            math.degrees(a)), FIN if j % 2 == 0 else '#ffb0d4', INK * 0.8) + humps
        for xf in (xa, xb):  # ripples round its feet
            humps += ol(lump(xf, yb + 6, 62, 20, 50 + k * 3 + int(xf), 0.15, 8), '#c4f7ff', INK * 0.75)
    tf = bez((2530, 2750), (2545, 2690), (2560, 2650), (2600, 2610), 14)
    f_, l_ = band(tf, lambda u: 34 - 10 * u)
    humps += ol(f_, SERPENT, INK, l_ + 'Z')
    humps += ol(lump(2635, 2565, 70, 44, 77, 0.12, 8, -40), FIN, INK)
    humps += ol(lump(2530, 2754, 62, 20, 78, 0.15, 8), '#c4f7ff', INK * 0.75)
    # the neck rises from the round top end and the head looks up and right, singing
    (x0, y0), _, _ = pt(0.06)
    neck = bez((x0, y0 + 30), (x0 - 20, y0 - 120), (x0 + 20, y0 - 210), (x0 + 90, y0 - 230), 24)
    nf, nl = band(neck, lambda u: 60 - 8 * u, cap=False)
    hx, hy = x0 + 120, y0 - 240
    head = ol(lump(hx, hy, 130, 95, 7, 0.08, 10, -12), SERPENT)
    head += ol(lump(hx + 60, hy + 42, 78, 34, 8, 0.1, 8, -18), MOUTH, INK * 0.9)  # the open mouth
    head += ol(lump(hx + 78, hy + 50, 34, 18, 9, 0.1, 7, -18), '#ff9fc4', INK * 0.7)  # its tongue
    head += wide_eye(hx - 10, hy - 30, 40)
    for j, (dx, dy, c) in enumerate([(-90, -60, FIN), (-40, -95, '#ffe066'), (20, -100, '#7fe0c8')]):
        head = ol(lump(hx + dx, hy + dy, 34, 50, 60 + j, 0.12, 7, dx * 0.4), c, INK * 0.8) + head
    body = not_bank(ol(nf, SERPENT, INK, nl)) + humps + head
    return draw(body, BULB)


def jelly_mould(x, y, W, H, colour, seed) -> str:
    """A wobbly jelly turned out of its mould, sitting at (x, y): a wide lower tier, a narrower domed top, ribs, a
    shine, and shake crescents either side."""
    rnd = random.Random(seed)
    j = lambda v: v * (1 + (rnd.random() - 0.5) * 0.06)
    half = [(W * 0.5, 0), (j(W * 0.52), -H * 0.22), (j(W * 0.46), -H * 0.46), (W * 0.36, -H * 0.54), (j(W * 0.34), -H * 0.74),
            (W * 0.2, -H * 0.95)]
    P = [(x + dx, y + dy) for dx, dy in half] + [(x, y - H * 1.0)] + [(x - dx, y + dy) for dx, dy in half[::-1]]
    P += [(x - W * 0.25, y + H * 0.04), (x + W * 0.25, y + H * 0.04)]
    d = closed(P)
    out = ''
    for side in (-1, 1):  # it shakes: crescents either side
        a0 = 90 - 90 * side
        out += ol(crescent(x, y - H * 0.45, W * 0.72, a0 - 20, a0 + 20, 42), '#ffffff', INK * 0.75)
    out += f'<path d="{d}" fill="{colour}" fill-opacity="0.9"/>'
    for dx in (-0.22, 0.0, 0.22):  # ribs from the mould
        out += f'<path d="{lump(x + dx * W, y - H * 0.25, W * 0.07, H * 0.2, seed + int(dx * 10), 0.1, 7)}" fill="#ffffff" fill-opacity="0.35"/>'
    out += f'<path d="{lump(x, y - H * 0.75, W * 0.18, H * 0.16, seed + 5, 0.1, 7)}" fill="#ffffff" fill-opacity="0.3"/>'
    out += f'<path d="{opened([P[2], P[3]])}" fill="none" stroke="#000" stroke-width="{INK * 0.6}" stroke-linecap="round"/>'
    out += f'<path d="{opened([P[-5], P[-6]])}" fill="none" stroke="#000" stroke-width="{INK * 0.6}" stroke-linecap="round"/>'
    out += f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    sh = bez((x - W * 0.3, y - H * 0.18), (x - W * 0.34, y - H * 0.4), (x - W * 0.2, y - H * 0.7), (x - W * 0.08, y - H * 0.86), 12)
    f, l = band(sh, lambda v: W * 0.035 * math.sin(math.pi * (0.1 + 0.8 * v)) + 4)
    out += ol(f, '#ffffff', INK * 0.6, l + 'Z')
    return out


def v2_jelly() -> Image.Image:
    """Wobbly jellies: the bank sets into a row of candy jellies turned out of their moulds, shaking, the biggest with
    a cherry on top."""
    out = ''
    for u, W, H, col, seed in [(0.12, 270, 250, '#9dff6a', 1), (0.52, 240, 215, '#ff6f9c', 2), (0.9, 210, 185, '#ffb347', 3)]:
        (x, y), _, _ = pt(u, -20)
        out += jelly_mould(x, y, W, H, col, seed)
        if seed == 1:
            cx, cy = x + 10, y - H - 60
            stem = bez((cx, cy - 40), (cx + 10, cy - 100), (cx + 40, cy - 130), (cx + 80, cy - 150), 16)
            sf, sl = band(stem, lambda v: 11 - 3 * v)
            out += ol(sf, '#4c9a3a', INK * 0.8, sl + 'Z')
            out += ol(lump(cx, cy, 70, 64, 21, 0.06, 9), '#f2304e')
            out += ol(lump(cx - 24, cy - 22, 18, 12, 22, 0.1, 7, -40), '#ffffff', INK * 0.6)
    return draw(out, BULB)


def frog(x, y, s, body, sac, seed) -> str:
    """A front-facing frog sitting at (x, y) (its feet), scale s, singing with its throat sac ballooned."""
    out = ''
    for dx in (-1, 1):  # back legs folded at its sides
        out += ol(lump(x + dx * 105 * s, y - 45 * s, 62 * s, 42 * s, seed + dx, 0.1, 8, dx * 20), body, INK)
    out += ol(lump(x, y - 110 * s, 125 * s, 105 * s, seed, 0.08, 10), body)
    for dx in (-1, 1):  # big eyes on top, wide awake, a lid of its own green over each
        out += ol(lump(x + dx * 60 * s, y - 196 * s, 54 * s, 52 * s, seed + 3 + dx, 0.06, 8), body)
        out += wide_eye(x + dx * 60 * s, y - 206 * s, 38 * s, (0.2, -0.25))
    out += ol(lump(x, y - 132 * s, 70 * s, 34 * s, seed + 7, 0.08, 9), MOUTH, INK * 0.9)
    out += ol(lump(x, y - 62 * s, 82 * s, 66 * s, seed + 8, 0.07, 9), sac)  # the throat sac, ballooned
    out += f'<path d="{lump(x - 30 * s, y - 85 * s, 20 * s, 12 * s, seed + 9, 0.1, 7, -30)}" fill="#fff" fill-opacity="0.85"/>'
    for dx in (-1, 1):  # front feet
        out += ol(lump(x + dx * 50 * s, y + 4 * s, 40 * s, 22 * s, seed + 11 + dx, 0.12, 7), body, INK * 0.9)
    for k, r in enumerate((40, 95)):  # warble rings from its song, out toward the pool
        out += ol(crescent(x, y - 110 * s, 130 * s + r * s, -42 + k * 4, 2 - k * 4, 42 * s), '#fff3a0', INK * 0.75)
    return out


def v3_frogs() -> Image.Image:
    """Frog chorus: two big frogs climb out onto the bank and sing, throat sacs ballooned, warble rings rising."""
    out = ''
    for u, s, body, sac, seed in [(0.22, 1.2, '#7fd36b', '#ff9fc4', 1), (0.86, 1.1, '#5cd6b8', '#ffe066', 20)]:
        (x, y), _, _ = pt(u, -15)
        out += frog(x, y, s, body, sac, seed)
    return draw(out, BULB)


def v4_cattails() -> Image.Image:
    """Swaying cattails: candy bulrushes shoot up along the bank on long stalks with blade leaves, leaning one way and
    the other as if caught mid-sway."""
    out = ''
    heads = ['#ff5ea8', '#ff9f43', '#c4a3f0', '#ff6b4a', '#ffe066']
    for k, u in enumerate((0.02, 0.26, 0.5, 0.74, 0.98)):
        (x, y), _, _ = pt(u)
        lean = math.radians((-1) ** k * 14 + 4)
        L = 470 - abs(k - 2) * 40
        top = (x + math.sin(lean) * L, y - math.cos(lean) * L)
        mid = (x + math.sin(lean) * L * 0.5 - (-1) ** k * 30, y - math.cos(lean) * L * 0.5)
        stalk = bez((x, y + 30), mid, mid, top, 24)
        for side in (-1, 1):
            a = lean + side * 0.45
            ln = 260 + 30 * side
            leaf = bez((x, y + 20), (x + math.sin(a) * ln * 0.4, y - math.cos(a) * ln * 0.4),
                       (x + math.sin(a) * ln * 0.8, y - math.cos(a) * ln * 0.75),
                       (x + math.sin(a + side * 0.5) * ln, y - math.cos(a + side * 0.5) * ln * 0.9), 20)
            f, l = blade(leaf, 30)
            out += ol(f, '#7fd36b' if side < 0 else '#5aa83e', INK * 0.9, l + 'Z')
        f, l = band(stalk, lambda v: 13 - 4 * v)
        out += ol(f, '#4c9a3a', INK * 0.9, l + 'Z')
        i0 = 13
        hp = stalk[i0:21]
        f, l = band(hp, lambda v: 40 + 6 * math.sin(math.pi * v))
        out += ol(lump(*stalk[17], 46, 105, k + 70, 0.07, 10, math.degrees(lean)), heads[k])
        out += f'<path d="{lump(stalk[16][0] - 14, stalk[16][1] - 8, 12, 50, k + 80, 0.1, 7, math.degrees(lean))}" fill="#fff" fill-opacity="0.6"/>'
        tip = stalk[22:]
        f, l = band(tip + [(top[0] + math.sin(lean) * 50, top[1] - math.cos(lean) * 50)], lambda v: 9 - 4 * v)
        out += ol(f, '#4c9a3a', INK * 0.8, l + 'Z')
    return draw(not_bank(out), BULB)


def through(K, per=14):
    """Points along a smooth curve through the key points K (Catmull-Rom), per points per span."""
    out = []
    n = len(K)
    for i in range(n - 1):
        p0, p1, p2, p3 = K[max(0, i - 1)], K[i], K[i + 1], K[min(n - 1, i + 2)]
        for j in range(per):
            t = j / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(K[-1])
    return out


def v5_streamer() -> Image.Image:
    """Ribbon dance: the bank's top end peels up off the ground and flies as a long candy-striped streamer, waving and
    twisting through the air above the pool, with a swallow-tail end."""
    (x0, y0), _, _ = pt(0.1)
    K = [(x0, y0 + 30), (x0 + 5, y0 - 90), (x0 + 60, y0 - 190), (x0 + 220, y0 - 250), (x0 + 400, y0 - 130),
         (x0 + 590, y0 - 270), (x0 + 780, y0 - 170), (x0 + 920, y0 - 280)]
    P = through(K, 16)
    N = len(P)
    tw = lambda u: math.cos(math.pi * max(0.0, u - 0.25) / 0.36)  # it twists over twice on its way
    hw = lambda u: max(7.0, 60 * abs(tw(u)) * (1 - 0.15 * u))
    L, R = sides(P, hw)
    cols = ['#ff5ea8', '#ffe066', '#7fe0c8', '#c4a3f0', '#ff9f43']
    back = ['#d63c86', '#e0bd3a', '#4fbfa6', '#9a7bd0', '#e0782a']
    out = ''
    step = 8
    for j, i in enumerate(range(0, N - 1, step)):
        e = min(N - 1, i + step)
        q = L[i:e + 1] + R[i:e + 1][::-1]
        u = (i + e) / 2 / (N - 1)
        c = SERPENT if j < 2 else (cols if tw(u) >= 0 else back)[j % 5]
        out += f'<path d="M{"L".join(p(*a) for a in q)}Z" fill="{c}" stroke="{c}" stroke-width="1.5"/>'
    for i in range(2 * step, N - 1, step):
        if hw(i / (N - 1)) > 20:
            out += f'<path d="{opened([L[i], R[i]])}" fill="none" stroke="#000" stroke-width="{INK * 0.6}" stroke-linecap="round"/>'
    (ex, ey), (px_, py_) = P[-1], P[-4]
    dx, dy = ex - px_, ey - py_
    d = math.hypot(dx, dy)
    dx, dy = dx / d, dy / d
    w = hw(1.0)
    tail = [L[-1], (ex + dx * 100 - dy * (w + 10), ey + dy * 100 + dx * (w + 10)), (ex + dx * 40, ey + dy * 40),
            (ex + dx * 100 + dy * (w + 10), ey + dy * 100 - dx * (w + 10)), R[-1]]
    tc = cols[((N - 1) // step) % 5]
    out += f'<path d="M{"L".join(p(*a) for a in tail)}Z" fill="{tc}" stroke="{tc}" stroke-width="2"/>'
    edge = opened(L) + f'L{"L".join(p(*a) for a in tail[1:-1])}L' + opened(R[::-1])[1:]
    out += f'<path d="{edge}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round" stroke-linecap="round"/>'
    return draw(not_bank(out), BULB)


VERSIONS = [
    ('1-serpent', 'River serpent', v1_serpent),
    ('2-jelly', 'Wobbly jelly', v2_jelly),
    ('3-frog-chorus', 'Frog chorus', v3_frogs),
    ('4-cattails', 'Swaying cattails', v4_cattails),
    ('5-streamer', 'Ribbon dance', v5_streamer),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (vibrato off)', m.compose())]
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


# ---- chosen: frog chorus -------------------------------------------------------------------------------------------
# Picked under 5a (rule 2, company arriving, like the ghost's twins): two frogs climb out onto the bank and sing, and
# their throat sacs ballooning are the vibrato. A switch, so one change plays through on an 800 ms glide: the first
# frog pops up on the bank (0-0.35), the second (0.25-0.6), their sleepy eyes open (0.5-0.7), their mouths open and
# their throat sacs swell (0.6-0.9), and a few fat song arcs come out toward the pool last (0.85-1). Drawn the
# painting's way: lumpy bodies with warts, heavy-outlined eye bumps with gold irises and slot pupils, lids of their
# own green; outlined and fill-only layers so the eye bumps melt into the heads.
GLIDE = 800
SONG = '#fff3a0'
IRIS = '#f5c64a'
FROGS = [  # u along the bank, scale, body, wart tone, sac, seed, pop window, eyes, mouth and sac, song arcs, their colour
    (0.3, 1.2, '#7fd36b', '#a8ec8a', '#ff9fc4', 1, (0.0, 0.35), (0.5, 0.65), 0.6, (0.85, 0.95), '#ffd3e6'),
    (0.86, 1.1, '#5cd6b8', '#93ead4', '#ffe066', 20, (0.25, 0.6), (0.55, 0.7), 0.65, (0.88, 1.0), SONG),
]


def arc_band(cx, cy, r, a0, a1, w) -> str:
    """A fat song arc: a band along the circle round (cx, cy) from a0 to a1 degrees, swelling in the middle and
    rounded at both ends."""
    n = 16
    P = [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r, cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * r)
         for i in range(n + 1)]
    L, R = sides(P, lambda v: w / 2 * (0.65 + 0.35 * math.sin(math.pi * v)))
    return closed(L[::2] + [P[-1]] + R[::-2] + [P[0]])


def chorus_frog(u, s, body, wart, sac, seed, pop, eyes, sing, song, song_col) -> list[dict]:
    (x, y), _, _ = pt(u, -15)
    feet = (x, y)
    P = lambda dx, dy: (x + dx * s, y + dy * s)
    a, b = pop
    items = []

    def add(d, fill, edge, at, s0, e0, out=None):
        o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
             'start': round(s0, 3), 'end': round(min(1.0, e0), 3), 'grow': 'scale'}
        if out:
            o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
        items.append(o)

    # the frog pops up out of the bank, every part growing from its feet
    for dx in (-1, 1):  # back legs folded at its sides
        add(lump(*P(dx * 108, -46), 66 * s, 44 * s, seed + dx, 0.14, 9, dx * 22), body, INK, feet, a, b)
    eyes_at = [P(dx * 62, -200) for dx in (-1, 1)]
    for k, (ex, ey) in enumerate(eyes_at):  # eye bumps, outlined, behind the head
        add(lump(ex, ey, 56 * s, 52 * s, seed + 3 + k, 0.08, 9), body, INK, feet, a, b)
    add(lump(*P(0, -114), 130 * s, 108 * s, seed, 0.12, 13), body, INK, feet, a, b)  # the lumpy body
    for k, (ex, ey) in enumerate(eyes_at):  # the same bumps fill-only over the head: no seam where they join
        add(lump(ex, ey, 56 * s - INK / 2, 52 * s - INK / 2, seed + 3 + k, 0.08, 9), body, 0, feet, a, b)
    for k, (dx, dy, r) in enumerate([(-92, -120, 22), (-70, -70, 16), (96, -105, 20)]):  # warts
        add(lump(*P(dx, dy), r * s, r * s * 0.8, seed + 30 + k, 0.15, 7), wart, 0, feet, a, b)
    for k, (ex, ey) in enumerate(eyes_at):  # gold irises, slot pupils
        add(lump(ex, ey - 2 * s, 44 * s, 41 * s, seed + 5 + k, 0.06, 9), IRIS, INK, feet, a, b)
        add(lump(ex + 2 * s, ey, 25 * s, 15 * s, seed + 7 + k, 0.08, 8), '#111111', 0, feet, a, b)
    for dx in (-1, 1):  # front feet
        add(lump(*P(dx * 54, 2), 42 * s, 22 * s, seed + 11 + dx, 0.14, 8), body, INK * 0.9, feet, a, b)
    add(lump(*P(0, -128), 58 * s, 9 * s, seed + 12, 0.1, 8), '#6b2a3e', INK * 0.6, feet, a, b)  # mouth shut
    # sleepy lids of its own green over the top of each eye; they lift away as it wakes, a glint arrives
    e0, e1 = eyes
    for k, (ex, ey) in enumerate(eyes_at):
        lid = lump(ex, ey - 28 * s, 52 * s, 30 * s, seed + 13 + k, 0.08, 9)
        add(lid, body, INK, feet, a, b, (e0, e0 + 0.005))  # pops up with the frog...
        top = (ex, ey - 50 * s)
        add(lid, body, INK, top, e0 - 0.005, e0, (e0, e1))  # ...and is swapped for one that lifts up into the bump
        add(lump(ex + 14 * s, ey - 16 * s, 10 * s, 9 * s, seed + 15 + k, 0.1, 7), '#ffffff', 0, (ex + 14 * s, ey - 16 * s), e1 - 0.06, e1 + 0.02)
    # it sings: the mouth opens, then the throat sac balloons out over its chest
    mouth = P(0, -128)
    add(lump(*mouth, 74 * s, 36 * s, seed + 17, 0.1, 9), MOUTH, INK * 0.9, mouth, sing, sing + 0.12)
    add(lump(*P(0, -60), 90 * s, 72 * s, seed + 8, 0.08, 10), sac, INK, P(0, -112), sing + 0.02, sing + 0.25)
    add(lump(*P(-34, -86), 24 * s, 13 * s, seed + 9, 0.12, 7, -30), '#ffffff', 0, P(-34, -86), sing + 0.15, sing + 0.27)
    # a few fat song arcs, out toward the pool
    c0, c1 = song
    for k, r in enumerate((180, 255)):
        cx, cy = P(0, -128)
        add(arc_band(cx, cy, r * s, -58 + k * 4, 14 - k * 4, (42 - k * 4) * s), song_col, INK * 0.9, P(60, -150),
            c0 + k * 0.03, c1 - (1 - k) * 0.03)
    return items


def chorus_items() -> list[dict]:
    return [o for f in FROGS for o in chorus_frog(*f)]


def chorus_frame(t: float) -> Image.Image:
    im = m.compose()
    if t > 0:
        im.alpha_composite(m.svg(g.sprite_svg(chorus_items(), t)))
    return im


def chorus_main() -> None:
    out = OUT.parent / 'frog-chorus'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [chorus_frame(t) for t in frames]
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
        d.text((x, 12), f'frame {tt:.2f}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    print('wrote', out)


if __name__ == '__main__' and 'chorus' in __import__('sys').argv[1:]:
    chorus_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': 'The river bank: tap for lower-manual vibrato; two frogs pop up on it, wake and sing, their throat sacs ballooning',
        'glide': GLIDE,
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': chorus_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(chorus_items()), 'shapes')
