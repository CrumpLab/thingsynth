# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (tonewheel leakage at its most) for the splash bush: the see-through green splash at the painting's
left edge, two pointed tips up top, a sawtoothed left side and scalloped lobes at the bottom, a pale cloverleaf in it
where the magenta stalk comes up, the eye tree's crown over its right side.

    uv run scripts/bush_endframes.py          # the five end frames and sheet
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
m.CROP = (370, 1820, 1000, 1520)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-leakage/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 14
BUSH = m.FILLS['f116']
BASE = (615.0, 3005.0)  # where its lobes sit at the bottom
TIP_L, TIP_R = (608.0, 2345.0), (760.0, 2238.0)
GREEN, GREEN2, PALEGREEN = '#7fe86a', '#5fd04f', '#b8f59a'
CANDY = ['#FF89FC', '#FFE47F', '#7FFFF6', '#c4a3f0', '#ff9f43', '#f64c76']
CROWN = ['f117', 'f119', 'f120']  # the eye tree's crown and eye, over its right side
EDGE = 372  # the painting's left edge on the canvas


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    clip = f'<defs><clipPath id="pb"><rect x="{EDGE}" y="390" width="4200" height="4000"/></clipPath></defs>'
    try:
        im = m.compose(front=f'{clip}<g clip-path="url(#pb)">{front}</g>' if front else '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(f'{clip}<g clip-path="url(#pb)">{over}</g>'))
    return im


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sx=1.0, sy=1.0) -> str:
    """A lumpy, hand-drawn round shape: n bumps round (x, y), a closed Catmull-Rom curve."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr * sx, y + math.sin(a) * rr * sy))
    return closed(P)


def closed(P) -> str:
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def wobble_tube(P, w0, w1, seed, wob=0.12, cap=True) -> str:
    """A tapered outlined shape along P whose width swells and narrows gently, like a hand-drawn stroke of paint."""
    rnd = random.Random(seed)
    ph, fr = rnd.random() * 6.3, 2 + rnd.random() * 2
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + wob * math.sin(fr * math.pi * u + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    pts = L
    if cap:  # a round end
        ex, ey = P[-1]
        a0 = math.atan2(L[-1][1] - ey, L[-1][0] - ex)
        r = math.hypot(L[-1][0] - ex, L[-1][1] - ey)
        pts = L + [(ex + math.cos(a0 - k / 4 * math.pi) * r, ey + math.sin(a0 - k / 4 * math.pi) * r) for k in (1, 2, 3)]
    return 'M' + 'L'.join(p(*q) for q in pts + R[::-1]) + 'Z'


def union(parts: list[str], fill: str, ink: float = INK, opacity: float = 1.0) -> str:
    """Several shapes merged into one outlined form: every outline at double width first, then every fill over them,
    so only the outer half of the outline shows and the joins are seamless."""
    op = f' fill-opacity="{opacity}"' if opacity < 1 else ''
    out = ''.join(f'<path d="{d}" fill="none" stroke="#000" stroke-width="{ink * 2}" stroke-linejoin="round"/>' for d in parts)
    if opacity < 1:  # one translucent layer, not one per part
        return out + f'<path d="{" ".join(parts)}" fill="{fill}"{op} fill-rule="nonzero"/>'
    return out + ''.join(f'<path d="{d}" fill="{fill}"/>' for d in parts)


def drop(x, y, r, ang, seed) -> str:
    """A lumpy teardrop, its point trailing back along ang (degrees)."""
    a = math.radians(ang)
    rnd = random.Random(seed)
    P = [(x - math.cos(a) * r * 2.2, y - math.sin(a) * r * 2.2)]
    for k in range(1, 8):
        b = a + math.pi - k / 8 * 2 * math.pi
        rr = r * (1 + (rnd.random() - 0.5) * 0.14) * (0.8 if k in (1, 7) else 1)
        P.append((x + math.cos(b) * rr, y + math.sin(b) * rr))
    return closed(P)


def eye(cx, cy, rx, ry, look=(0.0, -0.25)) -> str:
    out = outlined(lump(cx, cy, 1, 5, 0.06, 9, 0, rx, ry), '#ffffff', INK)
    px, py = cx + look[0] * rx, cy + look[1] * ry
    out += f'<path d="{ellipse(px, py, rx * 0.5, ry * 0.5)}" fill="#1b1b1b"/>'
    out += f'<path d="{circle(px + rx * 0.18, py - ry * 0.2, rx * 0.16)}" fill="#fff"/>'
    return out


# the pale cloverleaf in its middle is wash, not part of f116: a blob that fills it for a body made of the whole bush
CLOVER = lump(625, 2700, 1, 2, 0.08, 9, 0, 95, 170)


# ---- 1. ghost ------------------------------------------------------------------------------------------------------
def v1_ghost() -> Image.Image:
    """Ghost bush: the whole bush turns into a pale ghost, its two tips its ears: big round eyes open, a round
    'oooo' mouth, a wavy tail trailing off down to the left and one arm raised in a wave."""
    PALE = '#eef0ff'
    tail = wobble_tube(bez((600, 2900), (560, 3050), (480, 3090), (410, 3060), 24), 110, 36, 4, 0.18)
    arm = tube(bez((520, 2720), (440, 2680), (410, 2580), (430, 2470), 20), 50, 44)
    hand = lump(435, 2440, 64, 8, 0.1, 8)
    out = union([BUSH, CLOVER, tail, arm, hand], PALE)
    over = eye(560, 2590, 62, 76, (0.12, -0.1)) + eye(690, 2560, 56, 70, (0.05, -0.1))
    over += outlined(lump(630, 2760, 1, 11, 0.08, 9, 0, 40, 52), '#3a1030', INK)
    over += f'<path d="{ellipse(630, 2788, 24, 16)}" fill="#f64c76"/>'
    over += g.c.swoosh(435, 2440, 125, 195, 255, 26) + g.c.swoosh(435, 2440, 125, 290, 340, 26)
    return draw(out, CROWN, over)


# ---- 2. springing leaks --------------------------------------------------------------------------------------------
LEAKS = [  # hole, control points of the jet, its end, colour
    ((585, 2480), (560, 2280), (500, 2170), (470, 2250), '#7FFFF6'),
    ((725, 2330), (760, 2120), (870, 2040), (980, 2110), '#FF89FC'),
    ((690, 2880), (790, 2860), (860, 2900), (880, 2990), '#FFE47F'),
]


def v2_leaks() -> Image.Image:
    """Springing leaks: round holes pop open in it and a candy jet spurts out of each in an arc, breaking into drops
    and splashing into a puddle at its foot."""
    out = outlined(lump(880, 3090, 1, 21, 0.1, 11, 0, 160, 52), '#FFE47F', INK)
    for k, (h, *_rest) in enumerate(LEAKS):  # the holes first, so each jet comes out of its hole
        out += outlined(lump(h[0], h[1], 46, k + 30, 0.12, 8), '#2b2b3a', INK)
    for k, (h, c1, c2, e, col) in enumerate(LEAKS):
        P = bez(h, c1, c2, e, 30)
        out += outlined(wobble_tube(P, 24, 50, k, 0.1), col, INK)
        out += f'<path d="{wobble_tube([(x - 14, y - 14) for x, y in P[6:22]], 6, 9, k, 0.2)}" fill="#ffffff" fill-opacity="0.8"/>'
        a = math.atan2(P[-1][1] - P[-4][1], P[-1][0] - P[-4][0])
        ex, ey = e
        out += outlined(lump(ex + math.cos(a) * 120, ey + math.sin(a) * 120, 44, k + 3, 0.12, 8), col, INK)
        out += outlined(lump(ex + math.cos(a + 0.7) * 120, ey + math.sin(a + 0.7) * 120, 30, k + 9, 0.15, 7), col, INK * 0.85)
        out += outlined(lump(ex + math.cos(a - 0.6) * 200, ey + math.sin(a - 0.6) * 200, 24, k + 19, 0.15, 7), col, INK * 0.85)
    return draw(out, [])


# ---- 3. echo chorus ------------------------------------------------------------------------------------------------
def behind(body: str, ids: list[str], extra: list[str] | None = None) -> str:
    """`body` masked so the named painted fills (and extra shapes) stay in front of it."""
    holes = ''.join(f'<path d="{m.FILLS[f]}"/>' for f in ids) + ''.join(f'<path d="{d}"/>' for d in extra or [])
    mid = f'bm{abs(hash(tuple(ids))) % 9999}'
    return (f'<defs><mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="5000">'
            f'<rect x="0" y="0" width="4950" height="5000" fill="#fff"/><g fill="#000">{holes}</g></mask></defs>'
            f'<g mask="url(#{mid})">{body}</g>')


def v3_echoes() -> Image.Image:
    """Echo chorus: see-through candy copies of the bush fan open behind it from its foot, one for each of the other
    notes bleeding through, the farthest the faintest."""
    out = ''
    bx, by = 615.0, 2940.0
    for ang, s, col, op in [(30, 1.32, CANDY[3], 0.6), (-16, 1.28, CANDY[2], 0.65), (17, 1.4, CANDY[1], 0.7),
                            (-4, 1.36, CANDY[0], 0.75), (6, 1.18, CANDY[4], 0.8)]:
        t = f'translate({bx} {by}) rotate({ang}) scale({s}) translate({-bx} {-by})'
        out += (f'<g transform="{t}"><path d="{BUSH}" fill="{col}" fill-opacity="{op}"/>'
                f'<path d="{CLOVER}" fill="{col}" fill-opacity="{op}"/>'
                f'<path d="{BUSH}" fill="none" stroke="#000" stroke-width="{INK / s:.1f}" stroke-linejoin="round"/></g>')
    # keep their feet tucked in: nothing of them below the bush's bottom edge
    cut = 'M0 0L4950 0L4950 2600L800 2600L740 2860L690 2950L480 2940L425 2800L372 2760L0 2760Z'
    out = f'<defs><clipPath id="feet"><path d="{cut}"/></clipPath></defs><g clip-path="url(#feet)">{out}</g>'
    return draw_behind(behind(out, KEEP, [CLOVER]), KEEP)


def draw_behind(front: str, ink_of: list[str], over: str = '') -> Image.Image:
    """New shapes drawn, then only the ink of the named painted shapes laid back on top, then `over`."""
    clip = f'<defs><clipPath id="pb"><rect x="{EDGE}" y="390" width="4200" height="4000"/></clipPath></defs>'
    m.FRONT, m.FRONT_INK = [], sorted({s for f in ink_of for s in m.own_ink(f)})
    try:
        im = m.compose(front=f'{clip}<g clip-path="url(#pb)">{front}</g>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(f'{clip}<g clip-path="url(#pb)">{over}</g>'))
    return im


KEEP = ['f116', 'f113'] + CROWN  # what stays in front of anything coming out from behind the bush


# ---- 4. melting ---------------------------------------------------------------------------------------------------
DRIPS = [  # x where it leaves the bush's bottom edge, its length, half-width, colour
    (492, 270, 36, '#4fd447'),
    (595, 330, 40, '#6ad35a'),
]


def bottom_at(x: float) -> float:
    """The lowest point of the bush's fill outline at x: where a drip leaves it."""
    import re
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', BUSH)]
    return max(py for px, py in zip(nums[0::2], nums[1::2]) if abs(px - x) < 8)


def v4_melt() -> Image.Image:
    """Melting: the bush goes soft and runs: two fat drips sag out from under its bottom lobes and hang down over the
    pink below, a round drop swelling at the end of each, one already falling."""
    body, over = '', ''
    for k, (x, L, w, col) in enumerate(DRIPS):
        y = bottom_at(x) - 40
        P = bez((x, y), (x + 4, y + L * 0.3), (x - 6, y + L * 0.7), (x + 3, y + L), 20)
        drip = wobble_tube(P, w * 1.5, w * 0.62, k + 3, 0.1)
        bulb = lump(x + 3, y + L + w * 0.5, w * 1.3, k + 60, 0.08, 8)
        body += union([drip, bulb], col)
        body += f'<path d="{ellipse(x - w * 0.45, y + L + w * 0.3, w * 0.22, w * 0.34)}" fill="#ffffff" fill-opacity="0.75"/>'
    over += outlined(drop(494, 3330, 34, 90, 77), '#4fd447', INK)  # the falling drop
    return draw_behind(behind(body, KEEP, [CLOVER]), KEEP, over)


# ---- 5. bleeding hearts --------------------------------------------------------------------------------------------
STEMS = [  # root (behind the bush), controls, end; hearts at these fractions along it
    ((610, 2500), (580, 2060), (470, 2020), (490, 2170), (1.0,)),
    ((720, 2430), (790, 2000), (1080, 1940), (1170, 2160), (0.55, 1.0)),
]


def heart(x, y, r, seed, col='#FF89FC') -> str:
    """A bleeding-heart flower hanging at (x, y): a plump pink heart, point down, a white drop below its point."""
    rnd = random.Random(seed)
    j = lambda: (rnd.random() - 0.5) * r * 0.12
    d = (f'M{p(x, y - r * 0.55)}C{p(x - r * 0.25 + j(), y - r * 1.15 + j())} {p(x - r * 1.15 + j(), y - r * 0.9)} {p(x - r * 1.0, y - r * 0.15)}'
         f'C{p(x - r * 0.9 + j(), y + r * 0.4)} {p(x - r * 0.3, y + r * 0.7 + j())} {p(x, y + r * 0.95)}'
         f'C{p(x + r * 0.3, y + r * 0.7 + j())} {p(x + r * 0.9 + j(), y + r * 0.4)} {p(x + r * 1.0, y - r * 0.15)}'
         f'C{p(x + r * 1.15 + j(), y - r * 0.9)} {p(x + r * 0.25 + j(), y - r * 1.15 + j())} {p(x, y - r * 0.55)}Z')
    out = outlined(drop(x, y + r * 1.2, r * 0.32, 90, seed), '#ffffff', INK)
    out += outlined(d, col, INK)
    out += outlined(f'M{p(x, y - r * 0.5)}C{p(x - r * 0.25, y - r * 0.1)} {p(x - r * 0.25, y + r * 0.45)} {p(x, y + r * 0.85)}'
                    f'C{p(x - r * 0.05, y + r * 0.4)} {p(x - r * 0.05, y - r * 0.1)} {p(x, y - r * 0.5)}Z', '#f64c76', INK * 0.7)
    return out


def at_length(P, u):
    """The point a fraction u of the way along polyline P, by length."""
    seg = [math.dist(a, b) for a, b in zip(P, P[1:])]
    goal, run = u * sum(seg), 0.0
    for (a, b), d in zip(zip(P, P[1:]), seg):
        if run + d >= goal:
            t = (goal - run) / (d or 1)
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        run += d
    return P[-1]


def v5_hearts() -> Image.Image:
    """Bleeding hearts: two green stems arch up from behind it and over, and big pink heart flowers hang from them,
    a white drop at every point: the bush bleeds hearts."""
    body, over = '', ''
    for k, (r0, c1, c2, e, hs) in enumerate(STEMS):
        P = bez(r0, c1, c2, e, 40)
        body += outlined(wobble_tube(P, 36, 22, k + 7, 0.1), GREEN2, INK)
        for j, u in enumerate(hs):
            x, y = at_length(P, u)
            r = 96 - 8 * (j % 2)
            over += heart(x, y + r * 0.75, r, k * 10 + j, CANDY[0] if (j + k) % 2 else '#ffb3e6')
    return draw_behind(behind(body, KEEP, [CLOVER]), KEEP, over)


VERSIONS = [
    ('1-ghost', 'Ghost bush', v1_ghost),
    ('2-leaks', 'Springing leaks', v2_leaks),
    ('3-echoes', 'Echo chorus', v3_echoes),
    ('4-melting', 'Melting', v4_melt),
    ('5-bleeding-hearts', 'Bleeding hearts', v5_hearts),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (no leakage)', m.compose())]
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


# ---- chosen: ghost of itself ---------------------------------------------------------------------------------------
# Picked (by the coordinator, under 5a): the bush becomes a ghost of itself, on its own. Not a stock ghost pasted over
# it: its own silhouette stays (sawtooth side, scalloped lobes, its two tips as ears) and pales toward a see-through
# ghostly white-green (a `tint`, so the painting still faintly shows through), with the pale cloverleaf in it paling
# too. Then, in the painting's style, its eyes open from sleepy, a small round "oooo" mouth opens, an arm rises from its
# left side and waves, and a wavy tail trails off its bottom last. Timing across Leakage's range: pale 0-0.4, eyes
# 0.35-0.6, mouth 0.55-0.7, arm 0.65-0.9, tail 0.8-1.
#
#     uv run scripts/bush_endframes.py ghost    # progression strip and end frame
#     uv run scripts/bush_endframes.py export   # docs/objects/tg-leakage/build.json
GHOSTLY = '#eef9ea'      # the white-green the bush pales toward
TINT_AMOUNT = 0.72       # how far: colour 72% of the way, opacity 0.41 -> 0.83
TINT_SPAN = (0.0, 0.4)
FRONT_IDS = ['f113'] + CROWN  # the magenta stalk and the eye tree's crown stay in front of the paled cloverleaf


def _oklch(hex_: str):
    n = int(hex_.lstrip('#'), 16)
    lin = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    r, g_, b = (lin(((n >> s) & 255) / 255) for s in (16, 8, 0))
    l = (0.4122214708 * r + 0.5363325363 * g_ + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g_ + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g_ + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.793617785 * m_ - 0.0040720468 * s
    A = 1.9779984951 * l - 2.428592205 * m_ + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m_ - 0.808675766 * s
    return L, math.hypot(A, B), (math.degrees(math.atan2(B, A)) + 360) % 360


def _hex(L, C, H) -> str:
    def lin_rgb(c):
        a, b = c * math.cos(math.radians(H)), c * math.sin(math.radians(H))
        l_, m_, s_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, (L - 0.0894841775 * a - 1.291485548 * b) ** 3
        return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
                -0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_)
    rgb = lin_rgb(C)
    if not all(-1e-4 <= v <= 1 + 1e-4 for v in rgb):  # gamut: trim chroma, as the app does
        lo, hi = 0.0, C
        for _ in range(18):
            mid = (lo + hi) / 2
            if all(-1e-4 <= v <= 1 + 1e-4 for v in lin_rgb(mid)):
                lo = mid
            else:
                hi = mid
        rgb = lin_rgb(lo)
    gam = lambda u: 12.92 * u if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055
    return '#' + ''.join(f'{round(min(1, max(0, gam(min(1, max(0, v))))) * 255):02x}' for v in rgb)


def tinted(t: float) -> tuple[str, float]:
    """The bush's fill colour and opacity at frame t, the way the app's tint effect computes them."""
    base, op0 = '#609647', 0.405
    u = max(0.0, min(1.0, (t - TINT_SPAN[0]) / (TINT_SPAN[1] - TINT_SPAN[0])))
    u = min(1.0, u * TINT_AMOUNT)
    (l1, c1, h1), (l2, c2, h2) = _oklch(base), _oklch(GHOSTLY)
    dh = (((h2 - h1) % 360) + 540) % 360 - 180
    return _hex(l1 + (l2 - l1) * u, c1 + (c2 - c1) * u, (h1 + dh * u) % 360), op0 + (1 - op0) * u


PALE_PATCH = '#c2e3b6'   # the paled bush as it shows over the wash (sampled from the tinted render)
GHOST_INK = 12           # the bush's own outlines are about 12-14 px; the face is finer
EYE_WHITE, IRIS, LID = '#fffdf2', '#7FFFF6', '#d9eecf'


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 3), round(min(1.0, out[1]), 3)
    return o


def almond(cx, cy, rx, ry, tilt=0.0) -> str:
    """The painting's eye shape: an almond, a little fuller on top, slightly tilted."""
    a = math.radians(tilt)
    R = lambda x, y: (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
    return (f'M{p(*R(-rx, 0))}C{p(*R(-rx * 0.7, -ry * 1.3))} {p(*R(rx * 0.7, -ry * 1.3))} {p(*R(rx, 0))}'
            f'C{p(*R(rx * 0.7, ry * 1.2))} {p(*R(-rx * 0.7, ry * 1.2))} {p(*R(-rx, 0))}Z')


EYES = [(596, 2526, 60, 52, -8), (694, 2504, 48, 46, 6)]  # centre, half width, half height, tilt


def ghost_items() -> list[dict]:
    """Everything drawn over the paled bush: eyes, mouth, arm and tail, in the order they arrive."""
    items = []
    # eyes, 0.35-0.6: a heavy sleepy lid sits over each almond and lifts as the eye opens under it; iris, pupil, glint
    for k, (x, y, rx, ry, tl) in enumerate(EYES):
        s = 0.35 + 0.03 * k
        items.append(it(almond(x, y, rx, ry, tl), EYE_WHITE, GHOST_INK, (x, y), s, s + 0.12, 'y'))
        items.append(it(circle(x + 4, y + 6, ry * 0.62), IRIS, GHOST_INK * 0.85, (x + 4, y + 6), s + 0.08, s + 0.17))
        items.append(it(circle(x + 6, y + 8, ry * 0.3), '#1b1b1b', 0, (x + 6, y + 8), s + 0.12, s + 0.19))
        items.append(it(circle(x + 6 + ry * 0.2, y - ry * 0.05, ry * 0.12), '#ffffff', 0, (x + 6 + ry * 0.2, y), s + 0.16, s + 0.22))
        # the lid: the upper part of the almond, in the ghost's own pale, lifting away upward
        lid = (f'M{p(x - rx * 1.08, y + ry * 0.15)}C{p(x - rx * 0.75, y - ry * 1.45)} {p(x + rx * 0.75, y - ry * 1.45)} {p(x + rx * 1.08, y + ry * 0.15)}'
               f'C{p(x + rx * 0.4, y + ry * 0.42)} {p(x - rx * 0.4, y + ry * 0.42)} {p(x - rx * 1.08, y + ry * 0.15)}Z')
        items.append(it(lid, LID, GHOST_INK, (x, y - ry * 1.1), s, s + 0.04, 'y', (s + 0.08, s + 0.2)))
    # mouth, 0.55-0.7: a small round "oooo", dark inside, a pink tongue showing
    mx, my = 640, 2632
    items.append(it(lump(mx, my, 1, 11, 0.08, 9, 0, 30, 40), '#3a1030', GHOST_INK, (mx, my), 0.55, 0.66))
    items.append(it(ellipse(mx + 2, my + 20, 18, 12), '#f64c76', 0, (mx + 2, my + 24), 0.6, 0.7))
    # arm, 0.65-0.9: rises out of its left side, the hand opening last, motion crescents flicking out round it
    root, hand = (478, 2720), (430, 2400)
    P = bez(root, (430, 2650), (410, 2540), (426, 2445), 22)
    arm, palm = wobble_tube(P, 38, 34, 21, 0.08), lump(hand[0], hand[1], 54, 8, 0.12, 8)
    # outlines at double width first, then the fills over them: one form, no seam at the wrist
    items.append(it(arm, PALE_PATCH, INK * 2, root, 0.65, 0.8))
    items.append(it(palm, PALE_PATCH, INK * 2, (426, 2445), 0.72, 0.84))
    items.append(it(arm, PALE_PATCH, 0, root, 0.65, 0.8))
    items.append(it(palm, PALE_PATCH, 0, (426, 2445), 0.72, 0.84))
    items.append(it(lump(root[0] + 10, root[1] + 4, 44, 31, 0.1, 8), PALE_PATCH, 0, root, 0.65, 0.72))  # shoulder join
    for a0, a1, r in ((250, 288, 98), (304, 344, 98)):
        cres = g.c.swoosh(hand[0], hand[1], r, a0, a1, 30)
        d = re.search(r'<path d="([^"]+)"', cres).group(1)
        items.append(it(d, '#ffffff', GHOST_INK * 0.8, hand, 0.82, 0.9))
    # tail, 0.8-1: a wavy ghost tail out of its bottom lobes, trailing off down and to the left, curling at its tip
    T = bez((565, 2945), (545, 3075), (455, 3090), (420, 3035), 30)
    T += bez((420, 3035), (405, 3005), (412, 2975), (440, 2972), 10)[1:]
    items.append(it(wobble_tube(T, 66, 14, 41, 0.22), PALE_PATCH, INK, (565, 2950), 0.8, 1.0))
    items.append(it(lump(556, 2960, 52, 33, 0.1, 8), PALE_PATCH, 0, (556, 2960), 0.8, 0.86))  # its join
    return items


def clover_shape(cx: float = 622, cy: float = 2700) -> str:
    """The cloverleaf's own outline: from its middle, rays out to the first painted thing that bounds it (the bush's
    fill, the stalk, any ink), pushed 7 px further so the patch tucks under the ink; a smooth closed curve."""
    import io
    import numpy as np
    import resvg_py
    x0, y0, w, h = 470, 2480, 330, 470
    body = (f'<path d="{m.FILLS["f116"]}"/><path d="{m.FILLS["f113"]}"/>'
            + ''.join(f'<path d="{d}"/>' for d in m.INKS.values()))
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}" width="{w}" height="{h}">'
           f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fff"/><g fill="#000">{body}</g></svg>')
    a = np.array(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).convert('L')) < 128
    P = []
    for k in range(96):
        t = k / 96 * 2 * math.pi
        r = 4
        while r < 230:
            x, y = int(cx + math.cos(t) * r) - x0, int(cy + math.sin(t) * r) - y0
            if not (0 <= x < w and 0 <= y < h) or a[y, x]:
                break
            r += 1
        P.append((cx + math.cos(t) * (r + 7), cy + math.sin(t) * (r + 7)))
    return closed(P[::2])


def clover_items() -> list[dict]:
    """The pale cloverleaf in the bush (wash, not a fill) pales with it: a patch placed `under`, just below the bush's
    fills, so its own outline, the stalk's ink and the pencil scribbles stay on top."""
    seeds = [(622, 2700), (600, 2610), (585, 2700), (598, 2800), (640, 2800), (660, 2640)]  # its lobes, each seen whole
    return [it(clover_shape(x, y), PALE_PATCH, 0, (x, y), 0.05, 0.4) for x, y in seeds]


def sprites(items, t) -> str:
    """The app's drawSprites at frame t: each item eased out (cubic) over its window, grown by scale, x or y."""
    out = ''
    for o in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - o['start']) / max(1e-6, o['end'] - o['start'])))) ** 3
        if 'outStart' in o:
            u = max(0.0, min(1.0, (t - o['outStart']) / max(1e-6, o['outEnd'] - o['outStart'])))
            v *= 1 - (1 - (1 - u) ** 3)
        if v <= 0.01:
            continue
        x, y = o['at']
        sc = f'{v:.4f} 1' if o['grow'] == 'x' else f'1 {v:.4f}' if o['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{o["edge"]}" stroke-linejoin="round"' if o['edge'] > 0 else ''
        out += f'<path d="{o["d"]}" fill="{o["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


CLOVER_ITEMS = clover_items()


def ghost_frame(t: float) -> Image.Image:
    col, op = tinted(t)
    tags = m.FILL_TAGS
    m.FILL_TAGS = [re.sub(r'fill="#[0-9A-Fa-f]+" fill-opacity="[^"]*"', f'fill="{col}" fill-opacity="{op:.3f}"', s)
                   if 'id="f116"' in s else s for s in tags]
    # place "under": just below the bush's fills, so above the stalk (f113) and the background shapes
    under = sprites(CLOVER_ITEMS, t)
    m.FILL_TAGS = [f'{under}{s}' if 'id="f116"' in s else s for s in m.FILL_TAGS]
    try:
        im = m.compose()
    finally:
        m.FILL_TAGS = tags
    im.alpha_composite(m.svg(sprites(ghost_items(), t)))
    return im


def ghost_main() -> None:
    out = OUT.parent / 'ghost'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [ghost_frame(t) for t in frames]
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
    # the arrivals in close-up: one tile per beat of the timeline
    beats = [0.2, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    tiles = [ghost_frame(t).crop((0, 300, 560, 1300)) for t in beats]
    tw, th = 280, 500
    steps = Image.new('RGB', ((tw + 10) * len(beats) + 10, th + 56), 'white')
    d = ImageDraw.Draw(steps)
    for i, (tt, im) in enumerate(zip(beats, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'{tt:.2f}', fill='black', font=font)
        steps.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    steps.save(out / 'steps.png')
    print('wrote', out)


if __name__ == '__main__' and 'ghost' in __import__('sys').argv[1:]:
    ghost_main()


if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': ('The splash bush: drag for tonewheel Leakage; it turns into a ghost of itself: it pales see-through, its '
                  'eyes open from sleepy, it goes "oooo", an arm rises and waves and a wavy tail trails off last'),
        'effects': [
            {'effect': 'tint', 'color': GHOSTLY, 'amount': TINT_AMOUNT, 'span': list(TINT_SPAN)},
            {'effect': 'sprites', 'place': 'under', 'items': CLOVER_ITEMS},
            {'effect': 'sprites', 'place': 'over', 'items': ghost_items()},
        ],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(CLOVER_ITEMS) + len(ghost_items()), 'shapes')
