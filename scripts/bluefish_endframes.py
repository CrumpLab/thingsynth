# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower drawbar 2 2/3', the twelfth, fully out) for the blue-purple fish, right of centre: a
translucent cyan fish (f179) with two big fins raised like arms, a striped head-lobe at its lower left and a long
body sweeping right into a hooked crescent tail.

    uv run scripts/bluefish_endframes.py
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
m.CROP = (3300, 1950, 1300, 1200)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db5/endframes'
p, outlined, circle, tube, bez, swoosh = m.p, m.outlined, g.circle, g.tube, g.bez, g.c.swoosh
INK = 13
FISH = 'f179'
TEAL, BLUE, PURPLE, MAGENTA, PALE = '#2AD6CC', '#3E9EF2', '#A77CF0', '#E27BFF', '#BFF6FF'
CANDY = ['#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b', '#ff9fc4']
HEAD = (3700.0, 2820.0)  # the lower-left tip of the striped head-lobe
TAIL_TOP, TAIL_LOW = (4185.0, 2548.0), (4190.0, 2828.0)  # the crescent tail's two points
FIN_L, FIN_R = (3785.0, 2262.0), (3905.0, 2350.0)  # the raised fins' tips


def draw(front: str = '', again: list[str] | None = None, over: str = '', fish_ink: bool = False) -> Image.Image:
    """`front` is drawn over the painting, then the `again` fills (and their ink) are laid back on top, then `over`.
    With fish_ink the fish's own outlines are laid back over `front` too (use with behind())."""
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT + ([FISH] if fish_ink else []) for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def behind(body: str) -> str:
    """New shapes coming out from behind the fish: masked off where the fish's fill is, so the painted fish (its
    translucent cyan unchanged) stays in front; the fish's own ink is laid back over them by draw(behind=True)."""
    return (f'<defs><mask id="nofish" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect x="0" y="0" width="4950" height="4950" fill="#fff"/><path d="{m.FILLS[FISH]}" fill="#000"/></mask></defs>'
            f'<g mask="url(#nofish)">{body}</g>')


def smooth_closed(P) -> str:
    """A closed Catmull-Rom curve through the points, as cubic beziers."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def blob(cx, cy, rx, ry, rot=0.0, seed=0, wob=0.07, n=12) -> str:
    """A lumpy hand-drawn oval."""
    rnd = random.Random(seed)
    a0 = math.radians(rot)
    P = []
    for k in range(n):
        t = k / n * 2 * math.pi
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        x, y = math.cos(t) * rx * f, math.sin(t) * ry * f
        P.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return smooth_closed(P)


def sliver(P, w) -> str:
    """A tapered ink stroke the painting's way (a filled black sliver, thick in the middle, pointed at both ends)."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * math.sin(math.pi * (0.08 + 0.84 * i / (n - 1))) ** 0.7
        L.append((x + nx * ww, y + ny * ww))
        R.append((x - nx * ww, y - ny * ww))
    return f'<path d="M{"L".join(p(*q) for q in L + R[::-1])}Z" fill="#000"/>'


def eye(cx, cy, r, look=(0.15, 0.1), iris=PURPLE) -> str:
    out = outlined(blob(cx, cy, r, r * 1.05, 0, 7, 0.04), '#ffffff', INK)
    ix, iy = cx + look[0] * r, cy + look[1] * r
    out += outlined(circle(ix, iy, r * 0.55), iris, INK * 0.8)
    out += f'<path d="{circle(ix, iy, r * 0.28)}" fill="#000"/>'
    out += f'<path d="{circle(ix + r * 0.18, iy - r * 0.2, r * 0.11)}" fill="#fff"/>'
    return out


def fish_copy(scale: float, dx: float, dy: float, rot: float, colour: str) -> str:
    """The fish itself, redrawn smaller (its own fill path and ink) as a solid shape."""
    x, y, w, h = m.FP[FISH]['bbox']
    cx, cy = x + w / 2, y + h / 2
    t = f'translate({dx:.1f} {dy:.1f}) rotate({rot}) scale({scale}) translate({-cx:.1f} {-cy:.1f})'
    ink = ''.join(f'<path d="{m.INKS[s]}"/>' for s in m.own_ink(FISH))
    thicken = max(0.0, (10 - 13 * scale) / scale)  # so its outlines stay the painting's weight, not shrunk
    return (f'<g transform="translate({cx:.1f} {cy:.1f})"><g transform="{t}"><path d="{m.FILLS[FISH]}" fill="{colour}"/>'
            f'<g fill="#000" stroke="#000" stroke-width="{thicken:.1f}" stroke-linejoin="round">{ink}</g></g></g>')


# ---- the five --------------------------------------------------------------------------------------------------------

def fan(ox, oy, angs, rads, ys=1.0, bulge=0.45, root=50) -> tuple[str, list]:
    """A fin fanned out from (ox, oy): a ray tip at each angle (degrees) and radius, a rounded lobe bulging outward
    between each pair of tips, closed back at the root. Returns the path and the tips."""
    tips = [(ox + math.cos(math.radians(a)) * r, oy + math.sin(math.radians(a)) * r * ys) for a, r in zip(angs, rads)]
    a0, a1 = math.radians(angs[0] - 90), math.radians(angs[-1] + 90)
    d = f'M{p(ox + math.cos(a0) * root, oy + math.sin(a0) * root)}L{p(*tips[0])}'
    for (ax, ay), (bx, by), a, b in zip(tips, tips[1:], angs, angs[1:]):
        m_ = math.radians((a + b) / 2)
        ux, uy = math.cos(m_), math.sin(m_) * ys
        h = math.hypot(bx - ax, by - ay) * bulge * 1.3
        d += f'C{p(ax + ux * h, ay + uy * h)} {p(bx + ux * h, by + uy * h)} {p(bx, by)}'
    return d + f'L{p(ox + math.cos(a1) * root, oy + math.sin(a1) * root)}Z', tips


def ribbon(P, w, notch=True) -> str:
    """A flat ribbon of half-width w along P, its end cut in a swallowtail."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        L.append((x - dy / d * w, y + dx / d * w))
        R.append((x + dy / d * w, y - dx / d * w))
    (x1, y1), (x0, y0) = P[-1], P[-3]
    d = math.hypot(x1 - x0, y1 - y0) or 1
    tip = [(x1 - (x1 - x0) / d * w * 1.1, y1 - (y1 - y0) / d * w * 1.1)] if notch else []
    return 'M' + 'L'.join(p(*q) for q in L + tip + R[::-1]) + 'Z'


def v1_betta() -> Image.Image:
    """Betta: its crescent tail unfurls into a huge flowing veil, scalloped and rayed, and its two raised fins grow
    long flowing veils of their own, as a fighting fish's do."""
    ox, oy = 4070.0, 2700.0
    angs = [-84, -64, -45, -27, -9, 9, 24]
    rads = [360, 420, 440, 430, 420, 380, 300]
    veil, tips = fan(ox, oy, angs, rads, 0.9, 0.42, 70)
    inner, _ = fan(ox, oy, angs, [r * 0.6 for r in rads], 0.9, 0.42, 50)
    out = outlined(veil, PURPLE, INK) + f'<path d="{inner}" fill="{BLUE}"/>'
    for x, y in tips:
        out += sliver(bez((ox + 40, oy), (ox + (x - ox) * 0.35, oy + (y - oy) * 0.3), (ox + (x - ox) * 0.65, oy + (y - oy) * 0.7), (ox + (x - ox) * 0.9, oy + (y - oy) * 0.9), 16), 7)
    # the raised fins flare into veils that stream back over its body, up and to the right
    for (fx, fy), angs2, rads2, col in [((3770, 2330), (-112, -92, -72, -52), (230, 270, 260, 200), MAGENTA),
                                        ((3890, 2420), (-68, -48, -28, -8), (220, 260, 250, 190), PURPLE)]:
        d, t2 = fan(fx, fy, angs2, rads2, 1.0, 0.4, 40)
        out += outlined(d, col, INK)
        for x, y in t2:
            out += sliver(bez((fx, fy), (fx + (x - fx) * 0.3, fy + (y - fy) * 0.3), (fx + (x - fx) * 0.6, fy + (y - fy) * 0.65), (fx + (x - fx) * 0.88, fy + (y - fy) * 0.88), 14), 6)
    return draw(behind(out), [], '', fish_ink=True)


def v2_wings() -> Image.Image:
    """Flying fish: the two raised fins spread out into big ribbed wings, one each side, and it takes off."""
    out = ''
    for (rx, ry), angs, rads, inner in [((3745, 2430), (-118, -142, -166, 170), (360, 420, 400, 290), MAGENTA),
                                        ((3890, 2470), (-62, -38, -14, 10), (360, 420, 400, 290), PURPLE)]:
        if angs[0] < -90:
            angs = angs[::-1]
            rads = rads[::-1]
            angs = [a if a < 0 else a - 360 for a in angs]
        d, tips = fan(rx, ry, angs, rads, 1.0, 0.35, 50)
        di, _ = fan(rx, ry, angs, [r * 0.5 for r in rads], 1.0, 0.35, 35)
        cid = f'wing{rx:.0f}'
        rays = ''.join(sliver(bez((rx, ry), (rx + (x - rx) * 0.35, ry + (y - ry) * 0.3), (rx + (x - rx) * 0.7, ry + (y - ry) * 0.72), (rx + (x - rx) * 0.9, ry + (y - ry) * 0.9), 16), 8) for x, y in tips)
        out += f'<defs><clipPath id="{cid}"><path d="{d}"/></clipPath></defs>'
        out += f'<path d="{d}" fill="#8FE0F5"/><g clip-path="url(#{cid})"><path d="{di}" fill="{inner}"/>{rays}</g>'
        out += f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    return draw(behind(out), [], '', fish_ink=True)


def v3_singing() -> Image.Image:
    """Singing: a big eye opens on its head, its mouth opens wide at the head's tip, and big round bubbles rise out of
    it one after another, its fins up like arms."""
    hx, hy = HEAD
    out = eye(3800, 2650, 52, (-0.25, 0.1))
    out += outlined(blob(hx - 5, hy - 5, 70, 52, -40, 3, 0.05), '#7a1f3d', INK)
    out += outlined(blob(hx + 10, hy + 12, 40, 22, -40, 5, 0.06), '#ff7aa8', INK * 0.7)
    rnd = random.Random(2)
    for k, (x, y, r) in enumerate([(3590, 2720, 42), (3500, 2590, 58), (3560, 2420, 72), (3430, 2270, 88), (3610, 2140, 100)]):
        out += outlined(blob(x, y, r, r, 0, 20 + k, 0.05), PALE, INK)
        out += outlined(blob(x - r * 0.35, y - r * 0.35, r * 0.28, r * 0.16, -45, 30 + k, 0.05), '#ffffff', INK * 0.6)
    return draw('', [], out)


def v4_streamers() -> Image.Image:
    """Carp streamer: it becomes a koinobori, the festival carp windsock: long candy ribbons stream out of its tail and
    a big ringed festival eye opens on its head."""
    out = ''
    cols = ['#ff9f43', '#c4a3f0', '#2DFFF4', '#ffe066', '#f64c76']
    for k in range(5):
        ang = math.radians(-6 - k * 17)
        ca, sa = math.cos(ang), math.sin(ang)
        x0, y0 = 4110 + 8 * k, 2790 - k * 52
        L = 300 + (2 - abs(k - 2)) * 35
        P = []
        for i in range(31):
            u = i / 30
            wv = 22 * math.sin(u * 5.5 + k * 0.9) * u ** 0.6
            P.append((x0 + ca * L * u - sa * wv, y0 + sa * L * u + ca * wv))
        out += outlined(ribbon(P, 30), cols[k], INK)
    hx, hy = 3770, 2700
    over = outlined(blob(hx, hy, 72, 72, 0, 9, 0.03), '#ffffff', INK)
    over += outlined(circle(hx - 8, hy + 4, 46), '#ffe066', INK * 0.8)
    over += f'<path d="{circle(hx - 8, hy + 4, 26)}" fill="#000"/>' + f'<path d="{circle(hx + 4, hy - 8, 9)}" fill="#fff"/>'
    return draw(behind(out), [], over, fish_ink=True)


def v5_harmonics() -> Image.Image:
    """Its harmonics: the twelfth is the third harmonic, so two smaller copies of the fish swim up with it, about
    half its size and a third, like the overtones riding over a note."""
    out = fish_copy(0.55, 4370 - 3926, 2215 - 2563, 8, PURPLE)
    out += fish_copy(0.42, 3470 - 3926, 2320 - 2563, -10, '#2DE0E0')
    return draw('', [], out)


VERSIONS = [
    ('1-betta', 'Betta veils', v1_betta),
    ('2-flying-fish', 'Flying fish', v2_wings),
    ('3-singing', 'Singing', v3_singing),
    ('4-carp-streamer', 'Carp streamer', v4_streamers),
    ('5-harmonics', 'Harmonics', v5_harmonics),
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


# ---- chosen: betta veils, with a face ---------------------------------------------------------------------------
# Picked: 1 Betta veils, plus the eye and open mouth from 3 Singing as the smaller secondary (no bubbles). The tail
# veil is fabric rather than a peacock fan: uneven flowing lobes with ruffled ends and wavy folds.
# Lower 2 2/3' is a drawbar (0..8), so every step lands something:
#   step 1 (0-0.125)       an eye opens on its head and its mouth opens at the head's tip;
#   steps 2-6 (0.125-0.75)  the tail veil unfurls, one lobe a step, from the top round to the right;
#   steps 7-8 (0.75-1)     the left fin, then the right fin, flare into veils of their own.
# The veils are placed 'around' (above the ink, masked off the fish so its translucent cyan and outline stay in
# front); the face is placed 'over'.
TAIL_ROOT = (4070.0, 2790.0)
EYE_AT, EYE_R = (3800.0, 2650.0), 52.0
MOUTH_AT = (3695.0, 2815.0)


def unit(deg):
    a = math.radians(deg)
    return math.cos(a), math.sin(a)


def lobe(O, phi, L, W, bend, seed, w0=34.0, folds=2) -> tuple[str, list[str]]:
    """A flowing fabric lobe from O heading phi (screen degrees), length L, widening to W at its ruffled end, its
    centreline bending by `bend` degrees as it goes. Returns the outline path and its fold slivers."""
    rnd = random.Random(seed)
    ox, oy = O
    (a0x, a0y), (a1x, a1y), (a2x, a2y) = unit(phi), unit(phi + bend * 0.5), unit(phi + bend)
    C = bez(O, (ox + a0x * L * 0.35, oy + a0y * L * 0.35), (ox + a1x * L * 0.7, oy + a1y * L * 0.7), (ox + a2x * L, oy + a2y * L), 24)
    n = len(C)

    def frame(i):
        a, b = C[max(0, i - 1)], C[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        return dx / d, dy / d, -dy / d, dx / d

    ph1, ph2 = rnd.random() * 6, rnd.random() * 6
    left, right = [], []
    for i, (x, y) in enumerate(C):
        u = i / (n - 1)
        w = w0 + (W - w0) * u ** 0.9
        tx, ty, nx, ny = frame(i)
        left.append((x + nx * w * (1 + 0.1 * math.sin(u * 7 + ph1)), y + ny * w * (1 + 0.1 * math.sin(u * 7 + ph1))))
        right.append((x - nx * w * (1 + 0.1 * math.sin(u * 6 + ph2)), y - ny * w * (1 + 0.1 * math.sin(u * 6 + ph2))))
    # the ruffled end: a few rounded lumps of uneven width and height
    k = rnd.choice((2, 3, 3))
    cuts = sorted(rnd.uniform(0.2, 0.8) for _ in range(k - 1))
    segs = list(zip([0.0] + cuts, cuts + [1.0]))
    hs = [rnd.uniform(28, 70) for _ in segs]
    tx, ty, nx, ny = frame(n - 1)
    ex, ey = C[-1]
    end = []
    for j in range(1, 16):
        t = j / 16
        h = 0.0
        for (a, b), hh in zip(segs, hs):
            if a <= t <= b:
                h = hh * math.sin(math.pi * (t - a) / (b - a)) ** 0.8
        h += 22 * math.sin(math.pi * t)
        wl = left[-1], right[-1]
        bx = wl[0][0] + (wl[1][0] - wl[0][0]) * t
        by = wl[0][1] + (wl[1][1] - wl[0][1]) * t
        end.append((bx + tx * h, by + ty * h))
    d = smooth_closed(left + end + right[::-1])
    slivers = []
    for q in range(folds):
        o = rnd.uniform(-0.5, 0.5) if folds > 1 else 0.0
        o = (-0.42 + 0.84 * q / max(1, folds - 1)) * (0.8 + 0.3 * rnd.random()) if folds > 1 else o
        u1 = rnd.uniform(0.7, 0.92)
        P = []
        for i in range(n):
            u = i / (n - 1)
            if u < 0.18 or u > u1:
                continue
            x, y = C[i]
            _, _, nx2, ny2 = frame(i)
            w = (w0 + (W - w0) * u ** 0.9) * (o + 0.12 * math.sin(u * 9 + q * 2 + ph1))
            P.append((x + nx2 * w, y + ny2 * w))
        slivers.append(sliver(P, 6.5))
    return d, slivers


def sliver_d(svg_path: str) -> str:
    return svg_path.split('d="', 1)[1].split('"', 1)[0]


TAIL_LOBES = [  # heading, length, width, bend, colour, inner colour
    (-84, 360, 105, 22, '#8C7CF0', '#6FA8F5'),
    (-62, 430, 125, 18, '#B07CF5', '#8C9CF8'),
    (-40, 470, 120, 14, '#D58BF5', '#B07CF5'),
    (-20, 420, 115, 12, '#9C78E8', '#6FA8F5'),
    (-10, 250, 82, -8, '#C98AF5', '#A77CF0'),
]
FIN_LOBES = [  # root, heading, length, width, bend, colour, window
    ((3778.0, 2300.0), -104, 250, 78, 30, '#E27BFF', (0.75, 0.875)),
    ((3778.0, 2300.0), -78, 225, 70, 34, '#C98AF5', (0.75, 0.875)),
    ((3893.0, 2400.0), -62, 245, 78, 26, '#A77CF0', (0.875, 1.0)),
    ((3893.0, 2400.0), -36, 210, 68, 28, '#8C7CF0', (0.875, 1.0)),
]


def veil_items() -> list[dict]:
    items = []

    def add(O, phi, L, W, bend, col, inner, s, e, seed):
        d, sl = lobe(O, phi, L, W, bend, seed)
        at = [round(O[0], 1), round(O[1], 1)]
        base = {'at': at, 'start': round(s, 3), 'end': round(e, 3), 'grow': 'scale'}
        items.append({'d': d, 'fill': col, 'edge': INK, **base})
        if inner:
            di, _ = lobe(O, phi, L * 0.55, W * 0.62, bend * 0.6, seed, w0=26, folds=0)
            items.append({'d': di, 'fill': inner, 'edge': 0, **base})
        for x in sl:
            items.append({'d': sliver_d(x), 'fill': '#000', 'edge': 0, **base})

    for k, (phi, L, W, bend, col, inner) in enumerate(TAIL_LOBES):
        add(TAIL_ROOT, phi, L, W, bend, col, inner, (k + 1) / 8, (k + 2) / 8, 40 + k)
    for k, (O, phi, L, W, bend, col, (s, e)) in enumerate(FIN_LOBES):
        add(O, phi, L, W, bend, col, None, s, e, 60 + k)
    return items


def face_items() -> list[dict]:
    ex, ey = EYE_AT
    r = EYE_R
    ix, iy = ex - 0.25 * r, ey + 0.1 * r
    eye_win = {'at': [ex, ey], 'start': 0.0, 'end': 0.125, 'grow': 'y'}
    mouth_win = {'at': list(MOUTH_AT), 'start': 0.03, 'end': 0.125, 'grow': 'scale'}
    mx, my = MOUTH_AT
    return [
        {'d': blob(ex, ey, r, r * 1.05, 0, 7, 0.04), 'fill': '#ffffff', 'edge': INK, **eye_win},
        {'d': circle(ix, iy, r * 0.55), 'fill': PURPLE, 'edge': round(INK * 0.8, 1), **eye_win},
        {'d': circle(ix, iy, r * 0.28), 'fill': '#000', 'edge': 0, **eye_win},
        {'d': circle(ix + r * 0.18, iy - r * 0.2, r * 0.11), 'fill': '#fff', 'edge': 0, **eye_win},
        {'d': blob(mx, my, 70, 52, -40, 3, 0.05), 'fill': '#7a1f3d', 'edge': INK, **mouth_win},
        {'d': blob(mx + 15, my + 17, 40, 22, -40, 5, 0.06), 'fill': '#ff7aa8', 'edge': round(INK * 0.7, 1), **mouth_win},
    ]


def effects() -> list[dict]:
    return [{'effect': 'sprites', 'place': 'around', 'items': veil_items()},
            {'effect': 'sprites', 'place': 'over', 'items': face_items()}]


def ease3(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def sprites_svg(items, t) -> str:
    """The app's drawSprites, for the preview: easeOut3 over each item's window, grown about `at` by scale, x or y."""
    out = ''
    for it in items:
        v = ease3((t - it['start']) / max(1e-6, it['end'] - it['start']))
        if 'outStart' in it:
            v *= 1 - ease3((t - it['outStart']) / max(1e-6, it['outEnd'] - it['outStart']))
        if v <= 0.01:
            continue
        x, y = it['at']
        sc = f'{v:.4f} 1' if it['grow'] == 'x' else f'1 {v:.4f}' if it['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def around(body: str) -> str:
    """The app's 'around' placement: above the ink, masked off the object's fills plus a 44 px band round them."""
    return (f'<defs><mask id="ar" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect width="4950" height="4950" fill="#fff"/><path d="{m.FILLS[FISH]}" fill="#000" stroke="#000" '
            f'stroke-width="44" stroke-linejoin="round"/></mask></defs><g mask="url(#ar)">{body}</g>')


def chosen_frame(t: float) -> Image.Image:
    im = m.compose()
    if t > 0:
        im.alpha_composite(m.svg(around(sprites_svg(veil_items(), t)) + sprites_svg(face_items(), t)))
    return im


def chosen_main() -> None:
    out = OUT.parent / 'betta-veils'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [chosen_frame(t) for t in frames]
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
        d.text((x, 12), f'frame {tt:.2f}  (step {round(tt * 8)})', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    steps = [chosen_frame(k / 8).convert('RGB').resize((tw, th), Image.LANCZOS) for k in range(9)]
    grid = Image.new('RGB', (tw * 3 + 40, (th + 46) * 3 + 10), 'white')
    d = ImageDraw.Draw(grid)
    for k, im in enumerate(steps):
        x, y = 10 + (k % 3) * (tw + 10), 10 + (k // 3) * (th + 46)
        d.text((x, y), f'step {k}', fill='black', font=font)
        grid.paste(im, (x, y + 34))
    grid.save(out / 'steps.png')
    print('wrote', out)


def export() -> None:
    import json
    build = {
        'label': "The blue-purple fish: drag for the Lower 2 2/3' drawbar; it wakes and opens its mouth, its tail "
                 'unfurls into a flowing betta veil a lobe at a time, and its fins flare into veils last',
        'effects': effects(),
    }
    path = ROOT / 'docs/objects/lower-db5/build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', sum(len(e['items']) for e in build['effects']), 'shapes to', path)


if __name__ == '__main__':
    import sys as _s
    if len(_s.argv) == 1:
        main()
    elif _s.argv[1] == 'build':
        chosen_main()
    elif _s.argv[1] == 'export':
        export()
