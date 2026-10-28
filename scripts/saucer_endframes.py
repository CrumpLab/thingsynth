# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (percussion volume at Soft) for the straw creature's saucer: the apricot ruff, top right, that
the lavender straw creature's long neck stands in, with an oval hole where the neck goes down through it.

    uv run scripts/saucer_endframes.py          # the five end frames and sheet
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (3500, 1000, 1100, 1200)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/perc-volume/endframes'
p, outlined, circle, ellipse, tube, bez, smooth = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, m.smooth
INK = 14
SAUCER = 'f186'
CREATURE = ['f187', 'f188', 'f189']  # the straw creature's see-through body and its pink-and-yellow ball
BALL = ['f188', 'f189']
HOLE = (4317.0, 1663.0)  # the oval hole the neck goes down through
APRICOT, APRICOT2 = '#FFCE75', '#ffb35c'
PINK, PINK2, ROSE = '#ffb3cf', '#ff8fb8', '#e8608f'
CREAM, CREAM2 = '#fff6e0', '#ffeccc'
LILAC, CYAN, LEMON, MINT = '#c9a8f5', '#8fe8ff', '#ffe66b', '#9df0c4'


def fills_only(body: str) -> str:
    return re.sub(r'<path [^>]*fill="none"[^>]*/>', '', body)


def strokes_only(body: str) -> str:
    return re.sub(r'<path (?![^>]*fill="none")[^>]*/>', '', body)


def layer(im: Image.Image, body: str) -> None:
    """New shapes laid on the picture the painting's way: the pencil scribbles show on their fills, not their ink."""
    if not body:
        return
    full = m.svg(body)
    im.alpha_composite(full)
    paper = full.convert('L').point(lambda v: 0 if v < 50 else 255 if v > 120 else int((v - 50) * 255 / 70))
    sc = m.SCRIB.copy()
    sc.putalpha(ImageChops.multiply(ImageChops.multiply(m.SCRIB.getchannel('A'), m.svg(fills_only(body)).getchannel('A')), paper))
    im.alpha_composite(sc)


def draw(front: str = '', again: list[str] | None = None, over: str = '', skip_ink: tuple[str, ...] = ()) -> Image.Image:
    """New shapes over the painting, then the named painted shapes (and their own ink, less skip_ink) laid back on
    top where the new shapes covered them, so the new parts sit behind them; `over` goes on top of everything."""
    im = m.compose()
    layer(im, front)
    if front and again:
        cover = m.svg(front).getchannel('A')
        fl = m.svg(''.join(t for t in m.FILL_TAGS if re.search(r'id="(f\d+)"', t).group(1) in again))
        ink = sorted({s for f in again for s in m.own_ink(f)} - set(skip_ink))
        ik = m.svg('<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink) + '</g>')
        sc = m.SCRIB.copy()
        sc.putalpha(ImageChops.multiply(m.SCRIB.getchannel('A'), fl.getchannel('A')))
        for part in (fl, sc, ik):
            part.putalpha(ImageChops.multiply(part.getchannel('A'), cover))
            im.alpha_composite(part)
    layer(im, over)
    return im


def lump(x, y, r, seed, wob=0.13, n=9, rot=0.0, sx=1.0, sy=1.0) -> str:
    """A lumpy, hand-drawn round shape round (x, y), stretched by sx, sy."""
    rnd = random.Random(seed)
    P = []
    for k in range(n):
        a = rot + k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.35
        rr = r * (1 + (rnd.random() - 0.5) * 2 * wob)
        P.append((x + math.cos(a) * rr * sx, y + math.sin(a) * rr * sy))
    return smooth(P)


def wobble(P, amt, seed):
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * amt, y + (rnd.random() - 0.5) * amt) for x, y in P]


# ---- 1. plush cushion ----------------------------------------------------------------------------------------------
def v1_cushion() -> Image.Image:
    """Plush cushion: the saucer swells into a fat pink velvet cushion, tufted and tasselled; the neck sinks into it."""
    L, T, R, B = (3950, 1710), (4290, 1455), (4572, 1590), (4225, 1925)
    cx, cy = 4270, 1690

    def edge(a, b, push):  # a bulging edge from a to b, pushed outward from the cushion's middle
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        d = math.hypot(mx - cx, my - cy)
        return (mx + (mx - cx) / d * push, my + (my - cy) / d * push)

    def pinch(c, k=0.9):  # corners pulled in a touch, so they read as stuffed points
        return (cx + (c[0] - cx) * k, cy + (c[1] - cy) * k)
    top = smooth(wobble([L, edge(L, T, 95), pinch(T, 1), edge(T, R, 70), R, edge(R, B, 100), B, edge(B, L, 95)], 12, 1))
    # its puffy side, seen below the top face along the two front edges
    side = smooth(wobble([(3955, 1730), (4010, 1880), (4220, 2010), (4440, 1930), (4566, 1730), (4566, 1640),
                          (4420, 1830), (4220, 1900), (4030, 1820)], 8, 2))
    out = outlined(side, PINK2, INK) + outlined(top, PINK, INK)
    out += outlined(lump(4120, 1610, 60, 3, 0.15, 7, sx=1.7, sy=0.65), '#ffd6e6', 0)  # a soft sheen
    # tufts: a button pulled into the stuffing, soft creases gathering round it
    for k, (x, y) in enumerate([(4105, 1735), (4285, 1835), (4455, 1715)]):
        for j in range(5):
            ang = j / 5 * 2 * math.pi + k
            c, sn = math.cos(ang), math.sin(ang)
            x0, y0, x1, y1 = x + c * 22 * 1.3, y + sn * 22 * 0.75, x + c * 78 * 1.3, y + sn * 78 * 0.75
            crease = (f'M{p(x0, y0)}Q{p((x0 + x1) / 2 - sn * 12, (y0 + y1) / 2 + c * 8)} {p(x1, y1)}'
                      f'Q{p((x0 + x1) / 2 + sn * 12, (y0 + y1) / 2 - c * 8)} {p(x0, y0)}Z')
            out += f'<path d="{crease}" fill="{ROSE}" fill-opacity="0.75"/>'
        out += outlined(lump(x, y, 26, 10 + k, 0.1, 6, sx=1.15, sy=0.85), ROSE, INK * 0.7)
    # tassels on the near corners: a golden knot and a flared fringe of three soft lobes
    for k, (x, y, dx) in enumerate([(3950, 1712, -20), (4225, 1925, 10)]):
        kx, ky = x + dx, y + 30
        fringe = smooth(wobble([(kx - 26, ky + 20), (kx - 40, ky + 110), (kx - 62, ky + 180), (kx - 32, ky + 205),
                                (kx - 10, ky + 185), (kx + 4, ky + 212), (kx + 22, ky + 188), (kx + 46, ky + 206),
                                (kx + 64, ky + 176), (kx + 40, ky + 110), (kx + 26, ky + 20)], 6, 20 + k))
        out += outlined(fringe, LEMON, INK * 0.85)
        out += outlined(lump(kx, ky + 105, 1, 25 + k, 0.08, 7, sx=44, sy=18), '#ffb52e', INK * 0.7)  # binding
        out += outlined(lump(kx, ky + 10, 40, 30 + k, 0.1, 7), '#ffb52e', INK * 0.85)
    return draw(out, CREATURE)


# ---- 2. sleepy sheep -----------------------------------------------------------------------------------------------
def v2_sheep() -> Image.Image:
    """Sleepy sheep: the saucer fluffs up into a woolly sheep, its dark face nodding off on the left, legs tucked
    under, the neck rising out of its fleece."""
    rnd = random.Random(5)
    out = ''
    # legs first, under the fleece
    for k, (x, y) in enumerate([(4110, 1830), (4230, 1870), (4400, 1850), (4510, 1800)]):
        P = [(x, y - 60), (x + 6, y + 40), (x + 2, y + 130)]
        out += outlined(tube(P, 34, 30), '#4a4452', INK)
        out += outlined(lump(x + 4, y + 150, 34, 40 + k, 0.1, 7, sx=1.15, sy=0.75), '#2e2a33', INK * 0.8)
    # the fleece: big outlined puffs round a lumpy body, then a fill-only core melting the inner joins
    cx, cy, rx, ry = 4300, 1680, 250, 165
    puffs = []
    n = 13
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.random() * 0.2
        px, py = cx + math.cos(a) * rx * 0.86, cy + math.sin(a) * ry * 0.82
        if px > 4500:
            px = 4500 + (px - 4500) * 0.4
        puffs.append((px, py, 78 + rnd.random() * 22))
    for k, (x, y, r) in enumerate(puffs):
        out += outlined(lump(x, y, r, 50 + k, 0.14, 7), CREAM if k % 3 else CREAM2, INK)
    out += f'<path d="{lump(cx, cy, 1, 70, 0.08, 9, sx=rx * 0.85, sy=ry * 0.8)}" fill="{CREAM}"/>'
    # a few curls of wool on top of the fleece
    for k, (x, y) in enumerate([(4170, 1640), (4420, 1700), (4280, 1770)]):
        out += outlined(lump(x, y, 46, 80 + k, 0.18, 6), CREAM2, INK * 0.8)
    # its face, nodding off on the left
    fx, fy = 3995, 1740
    head = ''
    for k, (dx, dy, a) in enumerate([(-55, -95, -150), (75, -95, -30)]):  # ears
        ar = math.radians(a)
        ex, ey = fx + dx, fy + dy
        ear = smooth([(ex, ey), (ex + math.cos(ar - 0.5) * 70, ey + math.sin(ar - 0.5) * 70),
                      (ex + math.cos(ar) * 120, ey + math.sin(ar) * 120), (ex + math.cos(ar + 0.5) * 70, ey + math.sin(ar + 0.5) * 70)])
        head += outlined(ear, '#4a4452', INK * 0.9)
        head += outlined(lump(ex + math.cos(ar) * 66, ey + math.sin(ar) * 66, 24, 90 + k, 0.1, 6, rot=ar, sx=1.6, sy=0.6), '#ff9fc4', 0)
    head += outlined(lump(fx, fy, 110, 95, 0.06, 9, sx=0.85, sy=1.0), '#4a4452', INK)
    head += outlined(lump(fx + 5, fy - 120, 62, 96, 0.18, 7, sx=1.3, sy=0.8), CREAM, INK * 0.9)  # topknot
    for dx in (-38, 42):  # sleepy closed eyes: soft lids
        ex, ey = fx + dx, fy - 10
        lid = f'M{p(ex - 30, ey)}C{p(ex - 20, ey + 26)} {p(ex + 20, ey + 26)} {p(ex + 30, ey)}C{p(ex + 14, ey + 10)} {p(ex - 14, ey + 10)} {p(ex - 30, ey)}Z'
        head += outlined(lid, CREAM, INK * 0.7)
    head += outlined(lump(fx, fy + 70, 30, 97, 0.1, 6, sx=1.3, sy=0.8), '#ff9fc4', INK * 0.7)  # nose
    out += head
    return draw(out, CREATURE)


# ---- 3. soft serve -------------------------------------------------------------------------------------------------
def tier(cx, y, w, h, seed) -> str:
    P = [(cx - w / 2, y), (cx - w * 0.36, y - h * 0.8), (cx - w * 0.1, y - h), (cx + w * 0.2, y - h * 0.95),
         (cx + w * 0.42, y - h * 0.6), (cx + w / 2, y), (cx + w * 0.3, y + h * 0.42), (cx, y + h * 0.5),
         (cx - w * 0.3, y + h * 0.42)]
    return smooth(wobble(P, 12, seed))


def v3_soft_serve() -> Image.Image:
    """Soft serve: a strawberry-and-vanilla swirl heaps up out of the saucer round the neck, the creature's ball
    sitting on top like a cherry, and soft drips running down over the saucer's rim."""
    out = ''
    # drips over the rim, in front of the saucer
    for k, (x, y, L, col) in enumerate([(4140, 1790, 160, CREAM), (4310, 1815, 220, PINK), (4480, 1775, 130, CREAM)]):
        d = smooth(wobble([(x - 50, y - 40), (x - 36, y + L * 0.5), (x - 28, y + L), (x, y + L + 34), (x + 28, y + L),
                           (x + 36, y + L * 0.5), (x + 50, y - 40)], 6, 100 + k))
        out += outlined(d, col, INK * 0.9)
    # a pool of melt filling the saucer, then the swirl's coils, widest first
    out += outlined(lump(4320, 1735, 1, 120, 0.05, 9, sx=245, sy=85), CREAM, INK)
    tiers = [(4315, 1720, 440, 150, PINK), (4305, 1625, 360, 140, CREAM), (4300, 1540, 280, 125, PINK),
             (4292, 1470, 190, 100, CREAM)]
    for k, (cx, y, w, h, col) in enumerate(tiers):
        out += outlined(tier(cx, y, w, h, 110 + k), col, INK)
    return draw(out, BALL)


# ---- 4. hushing petals ---------------------------------------------------------------------------------------------
def petal(bx, by, ang, L, W, seed) -> str:
    """A big soft petal standing on (bx, by), leaning by ang degrees from straight up."""
    a = math.radians(ang - 90)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (bx + ca * u - sa * v, by + sa * u + ca * v)
    P = [R(0, -W * 0.3), R(L * 0.35, -W * 0.56), R(L * 0.72, -W * 0.42), R(L * 0.93, -W * 0.12), R(L, W * 0.04),
         R(L * 0.9, W * 0.2), R(L * 0.72, W * 0.44), R(L * 0.35, W * 0.56), R(0, W * 0.3)]
    return smooth(wobble(P, 14, seed))


def v4_petals() -> Image.Image:
    """Hush: the saucer's rim curls up into big soft petals that fold in round the neck, like a flower closing for
    the night, the creature's ball just peeking out of the bud."""
    back, front = '', ''
    for k, (bx, by, ang, L, W, col) in enumerate([(4120, 1660, -26, 380, 240, APRICOT2), (4500, 1650, 22, 360, 220, APRICOT2),
                                                  (4300, 1610, 4, 400, 250, PINK)]):
        back += outlined(petal(bx, by, ang, L, W, 200 + k), col, INK)
    for k, (bx, by, ang, L, W, col) in enumerate([(4130, 1790, 30, 360, 230, PINK), (4500, 1770, -32, 350, 220, PINK),
                                                  (4310, 1830, -4, 320, 230, APRICOT)]):
        front += outlined(petal(bx, by, ang, L, W, 210 + k), col, INK)
    # the saucer below the petals, puffed up a little as the cup they spring from
    base = outlined(lump(4320, 1770, 1, 230, 0.08, 9, sx=250, sy=95), APRICOT, INK)
    return draw(back, CREATURE, base + front)


# ---- 5. feather plumes ---------------------------------------------------------------------------------------------
def plume(bx, by, ang, L, W, seed, col) -> str:
    """A soft feather: an almond vane along a gently S-curved quill, softly wavy, with a couple of splits in its
    edges, and the outlined quill running up it."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    side = 1 if math.cos(a) > 0.1 else -1  # droops outward, the way plumes do
    bend = (0.7 + rnd.random() * 0.3) * side
    n = 48
    spine = [(bx, by)]
    for i in range(1, n + 1):
        u = i / n
        th = a - 0.25 * side * math.sin(math.pi * u) + bend * u ** 2
        spine.append((spine[-1][0] + math.cos(th) * L / n, spine[-1][1] + math.sin(th) * L / n))
    notches = ([0.4, 0.66], [0.52, 0.8])

    def outline(Wk, wavy, cut):
        Lp, Rp = [], []
        for i, (x, y) in enumerate(spine):
            u = i / n
            q0, q1 = spine[max(0, i - 1)], spine[min(n, i + 1)]
            dx, dy = q1[0] - q0[0], q1[1] - q0[1]
            d = math.hypot(dx, dy) or 1
            nx, ny = -dy / d, dx / d
            w = Wk * (0.08 + 0.92 * math.sin(math.pi * min(1.0, u ** 0.85)) ** 0.75) if u > 0.08 else Wk * 0.08
            ws = []
            for k, ns in enumerate(notches):
                v = 1 + wavy * math.sin(i * 1.1 + seed + k * 2)
                if cut:
                    for un in ns:
                        v *= 1 - 0.5 * max(0.0, 1 - abs(u - un) / 0.035)
                ws.append(w * v)
            Lp.append((x + nx * ws[0], y + ny * ws[0]))
            Rp.append((x - nx * ws[1], y - ny * ws[1]))
        return smooth(Lp[1:] + [spine[-1]] + Rp[:0:-1])
    out = outlined(outline(W, 0.03, True), col, INK)
    out += outlined(outline(W * 0.45, 0.0, False), '#ffffff', 0, extra='fill-opacity="0.4"')
    out += outlined(tube(spine[:int(n * 0.86)], 12, 5), '#fffaf0', INK * 0.6)
    return out


def v5_plumes() -> Image.Image:
    """Plumes: big soft candy feather plumes fan up out of the saucer behind the creature, and two loose downy
    feathers drift down below."""
    out = ''
    cols = [PINK, LILAC, CYAN, LEMON, MINT, PINK2]
    # quills tucked in under the saucer's rim, clear of the hole the neck goes down
    fans = [(4120, 1700, -172, 560), (4130, 1650, -148, 620), (4170, 1600, -124, 640), (4250, 1575, -100, 600),
            (4460, 1600, -80, 560), (4520, 1640, -66, 380)]
    for k, (bx, by, ang, L) in enumerate(fans):
        out += plume(bx, by, ang, L, 150, 300 + k, cols[k])
    over = plume(3900, 1990, 195, 240, 70, 330, LILAC) + plume(4120, 2080, -15, 230, 66, 331, PINK)
    return draw(out, [SAUCER] + CREATURE, over)


VERSIONS = [
    ('1-plush-cushion', 'Plush cushion', v1_cushion),
    ('2-sleepy-sheep', 'Sleepy sheep', v2_sheep),
    ('3-soft-serve', 'Soft serve', v3_soft_serve),
    ('4-hushing-petals', 'Hushing petals', v4_petals),
    ('5-feather-plumes', 'Feather plumes', v5_plumes),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Normal)', m.compose())]
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


# ---- chosen: sleepy sheep ------------------------------------------------------------------------------------------
# Picked under 5a: the saucer morphs into something living with a face, and the face does something (nods off): the
# most literal "soft" (wool, hushed, asleep) as a big drawn thing. A switch, so one change plays through on a glide:
# the wool puffs swell over the saucer one after another round the neck (0-0.5), covering it whole, a fill-only core melts the puffs' inner joins and three curls settle on top; the head pops out on the left with its
# eyes wide open (0.4-0.62), the lids droop shut (0.64-0.86), and the legs drop last (0.72-0.97). Placed `around`,
# masked so the straw creature's see-through neck and its ball stay in front.
FACE, FACE2, EAR_PINK, HOOF = '#4a4452', '#615a6b', '#ff9fc4', '#2e2a33'
WOOL_C, WOOL_RX, WOOL_RY = (4300.0, 1680.0), 250.0, 165.0
HEAD = (3995.0, 1740.0)
GLIDE = 750


def it(d, fill, edge, at, s, e, grow='scale') -> dict:
    return {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
            'start': round(s, 3), 'end': round(min(1.0, e), 3), 'grow': grow}


def sheep_items() -> list[dict]:
    items = []
    # legs first, so they sit under the fleece; they drop last, one after another
    for k, (x, y) in enumerate([(4110, 1830), (4230, 1870), (4400, 1850), (4510, 1800)]):
        s = 0.72 + 0.05 * (1, 3, 0, 2)[k]
        items.append(it(tube([(x, y - 60), (x + 6, y + 40), (x + 2, y + 130)], 34, 30), FACE, INK, (x, y - 60), s, s + 0.16, 'y'))
        items.append(it(lump(x + 4, y + 150, 34, 40 + k, 0.1, 7, sx=1.15, sy=0.75), HOOF, INK * 0.8, (x + 4, y + 120), s + 0.08, s + 0.2))
    # the fleece: big scalloped puffs swelling one after another round the neck, from the back round to the front
    rnd = random.Random(5)
    cx, cy = WOOL_C
    n = 13
    puffs = []
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.random() * 0.2
        px, py = cx + math.cos(a) * WOOL_RX * 0.86, cy + math.sin(a) * WOOL_RY * 0.82
        if px > 4500:
            px = 4500 + (px - 4500) * 0.4
        puffs.append((px, py, 78 + rnd.random() * 22, a))
    order = sorted(range(n), key=lambda k: (math.sin(puffs[k][3]), k))  # the top (back) first, the front last
    for j, k in enumerate(order):
        x, y, r, _ = puffs[k]
        s = 0.02 + 0.32 * j / (n - 1)
        at = (cx + (x - cx) * 0.55, cy + (y - cy) * 0.55)
        items.append(it(lump(x, y, r, 50 + k, 0.14, 7), CREAM if k % 3 else CREAM2, INK, at, s, s + 0.16))
    items.append(it(lump(cx, cy, 1, 70, 0.08, 9, sx=WOOL_RX * 0.85, sy=WOOL_RY * 0.8), CREAM, 0, WOOL_C, 0.1, 0.5))
    for k, (x, y) in enumerate([(4170, 1640), (4420, 1700), (4280, 1770)]):
        items.append(it(lump(x, y, 46, 80 + k, 0.18, 6), CREAM2, INK * 0.8, (x, y), 0.42 + 0.04 * k, 0.56 + 0.04 * k))
    # the head pops out on the left, ears and topknot with it
    fx, fy = HEAD
    hs, he = 0.4, 0.6
    root = (fx + 70, fy - 10)  # where it comes out of the fleece
    for k, (dx, dy, a) in enumerate([(-55, -95, -150), (75, -95, -30)]):
        ar = math.radians(a)
        ex, ey = fx + dx, fy + dy
        ear = smooth([(ex, ey), (ex + math.cos(ar - 0.5) * 70, ey + math.sin(ar - 0.5) * 70),
                      (ex + math.cos(ar) * 120, ey + math.sin(ar) * 120), (ex + math.cos(ar + 0.5) * 70, ey + math.sin(ar + 0.5) * 70)])
        items.append(it(ear, FACE, INK * 0.9, (ex, ey), hs + 0.06, he + 0.04))
        items.append(it(lump(ex + math.cos(ar) * 66, ey + math.sin(ar) * 66, 24, 90 + k, 0.1, 6, rot=ar, sx=1.6, sy=0.6), EAR_PINK, 0,
                        (ex, ey), hs + 0.08, he + 0.05))
    items.append(it(lump(fx, fy, 110, 95, 0.06, 9, sx=0.85, sy=1.0), FACE, INK, root, hs, he))
    items.append(it(lump(fx + 5, fy - 120, 62, 96, 0.18, 7, sx=1.3, sy=0.8), CREAM, INK * 0.9, (fx + 5, fy - 90), hs + 0.08, he + 0.06))
    items.append(it(lump(fx, fy + 70, 30, 97, 0.1, 6, sx=1.3, sy=0.8), EAR_PINK, INK * 0.7, (fx, fy + 60), hs + 0.1, he + 0.06))
    # wide-open eyes, then the lids droop down over them and it nods off
    for dx in (-38, 42):
        ex, ey = fx + dx, fy - 12
        items.append(it(ellipse(ex, ey, 30, 26), '#ffffff', INK * 0.7, (ex, ey), hs + 0.08, he + 0.04))
        items.append(it(circle(ex + 4, ey + 6, 12), '#000000', 0, (ex, ey), hs + 0.12, he + 0.06))
        lid = (f'M{p(ex - 37, ey + 6)}C{p(ex - 37, ey - 40)} {p(ex + 37, ey - 40)} {p(ex + 37, ey + 6)}'
               f'C{p(ex + 22, ey + 30)} {p(ex - 22, ey + 30)} {p(ex - 37, ey + 6)}Z')
        items.append(it(lid, FACE2, INK * 0.7, (ex, ey - 32), 0.64, 0.86, 'y'))
    return items


def sheep_vanish() -> list[dict]:
    """No vanish: the fleece covers the saucer whole, and the app's vanish would also fade the ink of the oval hole
    the neck goes down through, leaving the neck's foot outline-less in a ring of bare background (tried: it read as
    a lime ring). Kept, the saucer shows only as a thin apricot rim round the neck in the mask's band: the neck going
    down into a hole in the fleece."""
    return []


def own_ink_app() -> list[str]:
    """The saucer's own ink the way the app picks it (objects.ts), which its vanish fades."""
    x0, y0, w, h = m.FP[SAUCER]['bbox']
    out = []
    for s in m.FP[SAUCER]['ink']:
        x, y, sw, sh = m.IP[s]['bbox']
        if x >= x0 - 0.1 * w and y >= y0 - 0.1 * h and x + sw <= x0 + 1.1 * w and y + sh <= y0 + 1.1 * h:
            if x >= x0 - 40 and y >= y0 - 40 and x + sw <= x0 + w + 40 and y + sh <= y0 + h + 40:
                out.append(s)
    return out


def sheep_frame(t: float, vanish: bool = True) -> Image.Image:
    if t <= 0:
        return m.compose()
    gone = 0.0
    if vanish:
        s0, s1 = sheep_vanish()[0]['span'] if sheep_vanish() else (2.0, 3.0)
        gone = max(0.0, min(1.0, (t - s0) / (s1 - s0)))
    im = m.compose(fill_over={SAUCER: 'M0 0Z'} if gone else None, ink_over={i: 'M0 0Z' for i in own_ink_app()} if gone else None)
    if 0 < gone < 1:  # the half-faded saucer, laid back over at its fading opacity
        before = m.compose()
        im = Image.blend(im, before, 1 - gone)
    # the app's `around` mask: the sprites are cut away over the creature and its ball, with a band as wide as the ink
    mask = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in CREATURE))
    sp = m.svg(g.sprite_svg(sheep_items(), t))
    sp.putalpha(ImageChops.multiply(sp.getchannel('A'), ImageChops.invert(mask.getchannel('A'))))
    im.alpha_composite(sp)
    return im


def strip(frames, tiles, path) -> None:
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    out = Image.new('RGB', (tw * len(tiles) + 10 * (len(tiles) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(out)
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.2f}', fill='black', font=font)
        out.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    out.save(path)


def sheep_main() -> None:
    out = OUT.parent / 'sleepy-sheep'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [sheep_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    strip(frames, tiles, out / 'strip.png')
    fine = [0.1, 0.3, 0.45, 0.6, 0.7, 0.85]
    strip(fine, [sheep_frame(t) for t in fine], out / 'strip-fine.png')
    print('wrote', out)


LABEL = ("The saucer: tap for percussion volume Normal or Soft; on Soft it fluffs up into a woolly sheep, puff by puff, "
         "its head pops out wide awake, then its eyes droop shut and it nods off")


def export() -> None:
    import json
    build = {'label': LABEL, 'glide': GLIDE,
             'effects': [{'effect': 'sprites', 'place': 'around', 'parts': ['none'], 'front': CREATURE, 'items': sheep_items()}]
             + sheep_vanish(),
             'objectParts': {'none': []}}
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']), 'sprites to', path)


if __name__ == '__main__' and 'sheep' in __import__('sys').argv[1:]:
    sheep_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
