# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (upper drawbar 2 2/3', the twelfth, fully out) for the horned mask: the tall orange mask, top left,
with two blue-grey horns tipped ochre, a yellow almond eye, a wavy magenta-and-cyan striped panel down its right side,
red lips and a pink collar.

    uv run scripts/mask_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (330, 340, 1150, 1250)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/upper-db5/endframes'
p, outlined, circle, ellipse, bez, smooth = m.p, m.outlined, g.circle, g.ellipse, g.bez, m.smooth
INK = 15

BODY = ['f289']
EYE = ['f295', 'f296']
MOUTH = ['f290']
PANEL = ['f297', 'f299', 'f300', 'f298']
HORNS = ['f291', 'f293', 'f292', 'f294']
COLLAR = ['f288']
MASK = BODY + EYE + MOUTH + PANEL + HORNS + COLLAR
# the colours as they read on the paper
ORANGE, HORN_L, HORN_R, OCHRE = '#ffb072', '#6fb0c0', '#4a8090', '#cdb544'
MAGENTA, CYAN, ICE, YELLOW, LIPS = '#ff3fcf', '#2fd9ff', '#b5f1ff', '#ffd709', '#ff4d6a'


def draw(front: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    """The painting with `front` drawn over its ink but cut away wherever the `again` shapes (their fills and own ink)
    are, so new parts come out from behind them with the painted outline unbroken; `over` goes on top of everything."""
    im = m.compose()
    if front:
        lay = m.svg(front)
        if again:
            ink = sorted({s for f in again for s in m.own_ink(f)})
            cut = ''.join(f'<path d="{m.FILLS[f]}"/>' for f in again) + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink)
            hole = m.svg(f'<g fill="#000">{cut}</g>').getchannel('A')
            lay.putalpha(ImageChops.multiply(lay.getchannel('A'), ImageChops.invert(hole)))
        im.alpha_composite(lay)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def draw_on(im: Image.Image, front: str, again: list[str], over: str = '') -> Image.Image:
    """Another layer of new shapes on an image already drawn, cut away behind the `again` shapes."""
    lay = m.svg(front)
    ink = sorted({s for f in again for s in m.own_ink(f)})
    cut = ''.join(f'<path d="{m.FILLS[f]}"/>' for f in again) + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink)
    hole = m.svg(f'<g fill="#000">{cut}</g>').getchannel('A')
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), ImageChops.invert(hole)))
    im.alpha_composite(lay)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def limb(P, w0, w1, seed=0, amt=0.08, cap=True) -> str:
    """A tapered, slightly lumpy outlined limb along the centreline P, rounded at its far end."""
    rnd = random.Random(seed)
    ph = rnd.random() * 6.3
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + amt * math.sin(u * 9 + ph))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    if cap:
        ex, ey = P[-1]
        bx, by = P[-2]
        d = math.hypot(ex - bx, ey - by) or 1
        tip = (ex + (ex - bx) / d * w1 * 0.9, ey + (ey - by) / d * w1 * 0.9)
        pts = L + [tip] + R[::-1]
    else:
        pts = L + R[::-1]
    return smooth_open(pts)


def smooth_open(pts) -> str:
    """Closed Catmull-Rom through the points (the start and end joined by the curve, as in m.smooth)."""
    return smooth(pts)


def lumpy(cx, cy, rx, ry, seed, lumps=3, amt=0.05, rot=0.0) -> str:
    rnd = random.Random(seed)
    ph = [rnd.random() * 6.28 for _ in range(2)]
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for i in range(36):
        t = i / 36 * 2 * math.pi
        k = 1 + amt * math.sin(lumps * t + ph[0]) + amt * 0.5 * math.sin(3 * t + ph[1])
        x, y = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return smooth(pts)


def leafy(base, ang, length, width, seed=0, bend=0.15) -> str:
    """A petal or leaf: pointed-round, from `base` in direction `ang` (degrees), lumpy edges."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    pts = []
    for i in range(13):
        u = i / 12
        w = width / 2 * math.sin(math.pi * u ** 0.8) ** 0.8 * (1 + 0.06 * rnd.uniform(-1, 1))
        s = bend * length * math.sin(math.pi * u)
        pts.append((base[0] + ux * length * u + nx * (w + s), base[1] + uy * length * u + ny * (w + s)))
    for i in range(11, 0, -1):
        u = i / 12
        w = width / 2 * math.sin(math.pi * u ** 0.8) ** 0.8 * (1 + 0.06 * rnd.uniform(-1, 1))
        s = bend * length * math.sin(math.pi * u)
        pts.append((base[0] + ux * length * u - nx * (w - s), base[1] + uy * length * u - ny * (w - s)))
    return smooth(pts)


# ---- 1 antlers --------------------------------------------------------------------------------------------------------
# tines: (horn colour, centreline control points, base half-width, tip half-width)
TINES = [
    (HORN_L, ((452, 700), (525, 690), (585, 640), (600, 540)), 42, 30),
    (HORN_L, ((440, 610), (490, 585), (515, 520), (505, 445)), 38, 28),
    (HORN_R, ((760, 640), (850, 630), (920, 580), (950, 470)), 46, 32),
    (HORN_R, ((715, 715), (800, 745), (900, 745), (990, 680)), 44, 30),
]


def v1_antlers() -> Image.Image:
    """Antlers: both horns branch, tine after tine, into big antlers, each tine tipped ochre like the horns' own tips."""
    out = ''
    for k, (col, ctrl, w0, w1) in enumerate(TINES):
        P = bez(*ctrl, n=24)
        out += outlined(limb(P, w0, w1, k, amt=0.05), col, INK)
        tip = P[int(len(P) * 0.7):]
        out += outlined(limb(tip, w1 * 1.04, w1 * 0.85, k + 9, amt=0.03), OCHRE, INK)
    return draw(out, HORNS + BODY + PANEL + EYE + MOUTH)


# ---- 2 singing --------------------------------------------------------------------------------------------------------
def hand(cx, cy, ang, col, r=58, seed=0) -> str:
    """A mitten hand: a lumpy palm with a thumb, pointing in direction `ang`."""
    a = math.radians(ang)
    th = math.radians(ang - 70)
    out = outlined(leafy((cx, cy), math.degrees(th), r * 1.25, r * 0.75, seed, 0.05), col, INK)
    out += outlined(lumpy(cx + math.cos(a) * r * 0.45, cy + math.sin(a) * r * 0.45, r * 1.05, r * 0.82, seed, rot=ang), col, INK)
    return out


def v2_singing() -> Image.Image:
    """Singing: its eye pops wide and looks up, its lips open into a big singing O, and two orange arms fling up out
    of its collar."""
    arms = ''
    PL = bez((500, 1420), (420, 1400), (405, 1300), (440, 1210), 24)
    PR = bez((640, 1400), (760, 1370), (820, 1240), (830, 1120), 24)
    for P, sd, ang, r in ((PL, 1, -95, 50), (PR, 2, -80, 62)):
        arms += outlined(limb(P, 36, 32, sd, cap=False), ORANGE, INK)
        hx, hy = P[-1]
        arms += hand(hx, hy, ang, ORANGE, r, sd)
    ex, ey = 514, 1088
    face = f'<path d="{lumpy(ex - 2, ey, 52, 98, 2, amt=0.02)}" fill="{ORANGE}"/>'
    face += outlined(lumpy(ex, ey, 64, 84, 3, amt=0.03), '#ffffff', INK)
    face += outlined(lumpy(ex + 4, ey - 22, 30, 34, 4, amt=0.03), YELLOW, INK * 0.8)
    face += f'<path d="{circle(ex + 4, ey - 24, 15)}" fill="#000"/>' + f'<path d="{circle(ex + 14, ey - 34, 6)}" fill="#fff"/>'
    mx, my = 592, 1278
    face += outlined(lumpy(mx, my, 92, 78, 5, amt=0.04), LIPS, INK)
    face += outlined(lumpy(mx, my + 4, 58, 50, 6, amt=0.05), '#5a0d2a', INK * 0.8)
    face += outlined(lumpy(mx + 6, my + 34, 36, 18, 7, amt=0.05), '#ff8fb0', INK * 0.6)
    return draw(arms, COLLAR, face)


# ---- 3 rainbow ribbons ------------------------------------------------------------------------------------------------
def ribbon(y0, y1, x0, x1, amp, phase, w, col, seed) -> str:
    """A wavy outlined band streaming right from inside the panel, flaring a little and ending in a swallowtail."""
    n = 40
    C = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n + amp * (i / n) ** 0.7 * math.sin(phase + i / n * 2 * math.pi * 1.3)) for i in range(n + 1)]
    L, R = [], []
    for i, (x, y) in enumerate(C):
        a, b = C[max(0, i - 1)], C[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        ww = w * (0.85 + 0.35 * i / n)
        L.append((x + nx * ww, y + ny * ww))
        R.append((x - nx * ww, y - ny * ww))
    ex, ey = C[-1]
    bx, by = C[-4]
    notch = (ex - (ex - bx) * 0.9, ey - (ey - by) * 0.9)
    d = 'M' + 'L'.join(p(*q) for q in L) + f'L{p(*notch)}L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'
    return outlined(d, col, INK)


def v3_ribbons() -> Image.Image:
    """Rainbow ribbons: the wavy bands of its striped panel pour out of its face as big candy ribbons streaming away
    to the right, one band after another."""
    out = ''
    bands = [(830, 760, MAGENTA, 0.0), (920, 900, CYAN, 0.6), (1000, 1040, ICE, 1.2), (1090, 1180, YELLOW, 1.8)]
    for k, (y0, y1, col, ph) in enumerate(bands):
        out += ribbon(y0, y1, 690, 1300 - k * 30, 70, ph, 44, col, k)
    return draw(out, PANEL + BODY + EYE + MOUTH)


# ---- 4 candle ---------------------------------------------------------------------------------------------------------
def v4_candle() -> Image.Image:
    """Candle: it lights up like a tall candle: a big flame stands up from its crown between the horns, a glow
    swells behind, and cream wax drips run down its face."""
    halo = outlined(lumpy(570, 570, 185, 170, 11, lumps=7, amt=0.05), '#fff3a0', INK * 0.8)
    flame = m.flame((562, 728), 320, 210, 0, random.Random(4), '#ffcf3a', '#ff6b4a', INK)
    flame += m.flame((562, 700), 110, 52, 0, random.Random(8), '#ffffff', '#ffffff', INK * 0.6)
    flame += outlined(limb([(562, 740), (562, 692)], 9, 9, 0, amt=0), '#3a2a1a', INK * 0.6)
    wax = smooth([(452, 830), (470, 765), (510, 727), (560, 714), (605, 726), (642, 752), (650, 788), (640, 820), (644, 900),
                  (630, 938), (610, 922), (608, 832), (588, 812), (566, 822), (564, 862), (548, 886), (530, 868), (528, 822),
                  (506, 815), (490, 832), (490, 958), (472, 996), (454, 974), (450, 880)])
    im = draw(halo, HORNS + BODY + PANEL)
    im.alpha_composite(m.svg(flame))
    return draw_on(im, outlined(wax, '#fff1d8', INK), HORNS)


# ---- 5 snail ----------------------------------------------------------------------------------------------------------
def shell(cx, cy, r, turns=4) -> str:
    """A candy spiral shell the painting's way: lumpy rounds nested toward the left (where it meets the head), each a
    band of the panel's colours, outlined."""
    out = ''
    cols = [MAGENTA, CYAN, ICE, MAGENTA, CYAN, ICE]
    x, y, rr = cx, cy, r
    for k in range(turns):
        out += outlined(lumpy(x, y, rr, rr * 0.94, 40 + k, amt=0.03), cols[k], INK)
        x, y, rr = x - rr * 0.28, y + rr * 0.08, rr * 0.66
    return out


def eyeball(cx, cy, r, look=(0.25, 0.1)) -> str:
    out = outlined(lumpy(cx, cy, r, r * 1.05, 50, amt=0.03), '#ffffff', INK)
    px, py = cx + look[0] * r, cy + look[1] * r
    out += outlined(circle(px, py, r * 0.45), YELLOW, INK * 0.8) + f'<path d="{circle(px, py, r * 0.22)}" fill="#000"/>'
    return out + f'<path d="{circle(px + r * 0.12, py - r * 0.14, r * 0.08)}" fill="#fff"/>'


def v5_snail() -> Image.Image:
    """Snail: it turns into a big snail: a candy spiral shell swells out of its back, in its striped panel's colours,
    and the tips of its horns swell into eyes on stalks."""
    back = shell(860, 930, 225)
    eyes = eyeball(445, 478, 66, (-0.1, 0.2)) + eyeball(712, 455, 68, (0.25, 0.25))
    return draw(back, MASK, eyes)


VERSIONS = [
    ('1-antlers', 'Antlers', v1_antlers),
    ('2-singing', 'Singing, arms up', v2_singing),
    ('3-rainbow-ribbons', 'Rainbow ribbons', v3_ribbons),
    ('4-candle', 'Candle', v4_candle),
    ('5-snail', 'Snail', v5_snail),
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


# ---- chosen: the snail -------------------------------------------------------------------------------------------------
# Picked: 5 Snail, with the singing mouth from 2 as the last beat. The drawbar's eight steps each add one thing:
#   1  the left horn's tip swells into a sleepy eye on its stalk      5  the third turn (ice)
#   2  the right one does the same                                    6  the fourth turn winds into the centre (magenta)
#   3  the shell's first, outer turn sweeps round out of its back      7  both eyes open wide
#   4  the second turn winds in inside it (cyan)                      8  its lips open into a big singing O
# The shell is a true spiral built from the striped panel's wavy bands: each turn is one outlined band whose inner
# edge is the next turn's outer edge, revealed by a wedge sweeping clockwise from where it leaves the head. It sits
# `around` (behind the mask, its horns, panel and collar); the eyes and mouth go `over`.
STEP = 1 / 8
SHELL_C = (842.0, 935.0)
SHELL_R0, SHELL_B = 245.0, 52.0
SHELL_COLS = [MAGENTA, CYAN, ICE, MAGENTA]
FRONT_IDS = ['f288', 'f291', 'f292', 'f293', 'f294', 'f295', 'f297', 'f298', 'f299', 'f300']
OWN_IDS = ['f289', 'f290', 'f296']
EYES = [(445.0, 478.0, 66.0), (712.0, 455.0, 66.0)]
MOUTH_C = (592.0, 1278.0)


def it(d, fill, edge, at, s, e, grow='scale', out=None, sweep=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 3), 'end': round(e, 3), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 3), round(out[1], 3)
    if sweep:
        x['sweep'] = {'from': sweep[0], 'to': sweep[1]}
    return x


def shell_edge(phi: float) -> float:
    """The spiral's radius at screen angle phi (degrees, clockwise from the right, 180 = where it leaves the head),
    with the panel's waves running along it."""
    r = SHELL_R0 - SHELL_B * (phi - 180) / 360
    k = max(0.25, r / SHELL_R0)
    a = math.radians(phi)
    return max(6.0, r + k * (9 * math.sin(5 * a + 0.6) + 6 * math.sin(3 * a + 1.9)))


def shell_turn(k: int) -> str:
    cx, cy = SHELL_C
    n = 90
    outer, inner = [], []
    for i in range(n + 1):
        phi = 180 + 360 * k + 360 * i / n
        a = math.radians(phi)
        ro, ri = shell_edge(phi), shell_edge(phi + 360)
        outer.append((cx + math.cos(a) * ro, cy + math.sin(a) * ro))
        inner.append((cx + math.cos(a) * ri, cy + math.sin(a) * ri))
    return 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'


def shell_items() -> list[dict]:
    items = []
    for k in range(4):
        s = (2 + k) * STEP
        items.append(it(shell_turn(k), SHELL_COLS[k], INK, SHELL_C, s, s + STEP, sweep=(180, -180)))
    # a round nub closes the spiral's eye as the last turn arrives
    items.append(it(lumpy(SHELL_C[0] - 6, SHELL_C[1], 26, 24, 60, amt=0.04), MAGENTA, INK * 0.8, SHELL_C, 6 * STEP - STEP * 0.3, 6 * STEP))
    return items


def eye_items() -> list[dict]:
    items = []
    for j, (x, y, r) in enumerate(EYES):
        s = j * STEP
        base = (x, y + r)  # it swells out of the horn's tip from below
        top = (x, y - r * 1.05)
        items.append(it(lumpy(x, y, r, r * 1.05, 50, amt=0.03), '#ffffff', INK, base, s, s + STEP * 0.8))
        # sleepy: the iris low, looking down, under a heavy ochre lid
        items.append(it(circle(x + r * 0.05, y + r * 0.45, r * 0.4), YELLOW, INK * 0.8, base, s + STEP * 0.1, s + STEP * 0.85, out=(6 * STEP + STEP * 0.2, 6 * STEP + STEP * 0.7)))
        items.append(it(circle(x + r * 0.05, y + r * 0.5, r * 0.18), '#000', 0, base, s + STEP * 0.1, s + STEP * 0.85, out=(6 * STEP + STEP * 0.2, 6 * STEP + STEP * 0.7)))
        lid = (f'M{p(x - r * 1.0, y + r * 0.12)}C{p(x - r * 1.05, y - r * 0.75)} {p(x - r * 0.5, y - r * 1.08)} {p(x, y - r * 1.08)}'
               f'C{p(x + r * 0.5, y - r * 1.08)} {p(x + r * 1.05, y - r * 0.75)} {p(x + r * 1.0, y + r * 0.12)}'
               f'C{p(x + r * 0.5, y + r * 0.3)} {p(x - r * 0.5, y + r * 0.3)} {p(x - r * 1.0, y + r * 0.12)}Z')
        items.append(it(lid, OCHRE, INK, top, s + STEP * 0.45, s + STEP, grow='y', out=(6 * STEP, 6 * STEP + STEP * 0.7)))
        # step 7, awake: a big iris looking up and out swells over the sleepy one
        lx, ly = x + (-0.1 if j == 0 else 0.25) * r, y - 0.05 * r
        c = (lx, ly)
        items.append(it(circle(lx, ly, r * 0.48), YELLOW, INK * 0.8, c, 6 * STEP + STEP * 0.3, 7 * STEP))
        items.append(it(circle(lx, ly, r * 0.24), '#000', 0, c, 6 * STEP + STEP * 0.35, 7 * STEP))
        items.append(it(circle(lx + r * 0.12, ly - r * 0.14, r * 0.09), '#ffffff', 0, c, 6 * STEP + STEP * 0.5, 7 * STEP))
    return items


def mouth_items() -> list[dict]:
    mx, my = MOUTH_C
    s = 7 * STEP
    return [it(lumpy(mx, my, 92, 78, 5, amt=0.04), LIPS, INK, (mx, my), s, s + STEP * 0.6),
            it(lumpy(mx, my + 4, 58, 50, 6, amt=0.05), '#5a0d2a', INK * 0.8, (mx, my + 4), s + STEP * 0.25, s + STEP * 0.85),
            it(lumpy(mx + 6, my + 34, 36, 18, 7, amt=0.05), '#ff8fb0', INK * 0.6, (mx + 6, my + 40), s + STEP * 0.5, 1.0)]


def over_items() -> list[dict]:
    return eye_items() + mouth_items()


def ease3(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def sprites(items, t: float) -> str:
    """The app's drawSprites at u = t: growth by scale, x or y round `at`, shrinking over outStart..outEnd, or a wedge
    sweep round `at` (0 = right, 90 = up)."""
    out = ''
    for k, e in enumerate(items):
        v = ease3((t - e['start']) / max(1e-6, e['end'] - e['start']))
        if 'outStart' in e:
            v *= 1 - ease3((t - e['outStart']) / max(1e-6, e['outEnd'] - e['outStart']))
        x, y = e['at']
        stroke = f' stroke="#000" stroke-width="{e["edge"]}" stroke-linejoin="round"' if e['edge'] > 0 else ''
        if 'sweep' in e:
            if v <= 0.005:
                continue
            a0 = e['sweep']['from']
            a1 = a0 + (e['sweep']['to'] - a0) * v
            pts = [(x, y)] + [(x + math.cos(math.radians(a0 + (a1 - a0) * i / 24)) * 5000, y - math.sin(math.radians(a0 + (a1 - a0) * i / 24)) * 5000) for i in range(25)]
            out += f'<clipPath id="sw{k}"><path d="M{"L".join(p(*q) for q in pts)}Z"/></clipPath>'
            out += f'<path d="{e["d"]}" fill="{e["fill"]}"{stroke} clip-path="url(#sw{k})"/>'
            continue
        if v <= 0.01:
            continue
        sc = f'{v:.4f} 1' if e['grow'] == 'x' else f'1 {v:.4f}' if e['grow'] == 'y' else f'{v:.4f}'
        out += f'<path d="{e["d"]}" fill="{e["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def snail_frame(t: float) -> Image.Image:
    """`around` as the app does it: above the ink, masked out over the mask's own fills and the front ids, each with a
    44 px band round it so their outlines stay in front; then `over`."""
    im = m.compose()
    if t <= 0:
        return im
    lay = m.svg(sprites(shell_items(), t) or '<g/>')
    cut = ''.join(f'<path d="{m.FILLS[f]}" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in OWN_IDS + FRONT_IDS)
    hole = m.svg(f'<g fill="#000">{cut}</g>').getchannel('A')
    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), ImageChops.invert(hole)))
    im.alpha_composite(lay)
    ov = sprites(over_items(), t)
    if ov:
        im.alpha_composite(m.svg(ov))
    return im


def strip(frames, path, sc) -> None:
    tiles = [snail_frame(t) for t in frames]
    w, h = tiles[0].size
    tw, th = int(w * sc), int(h * sc)
    im = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.3g}' + (f'  (step {round(tt * 8)})' if abs(tt * 8 - round(tt * 8)) < 1e-6 else ''), fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    im.save(path)
    return tiles


def snail_main() -> None:
    out = OUT.parent / 'snail'
    out.mkdir(parents=True, exist_ok=True)
    tiles = strip([0, 0.25, 0.5, 0.75, 1.0], out / 'strip.png', 0.4)
    tiles[-1].save(out / 'end-frame.png')
    strip([k / 8 for k in range(9)], out / 'steps.png', 0.24)
    strip([0.3125, 0.4375, 0.5625, 0.6875, 0.8125, 0.9375], out / 'mid-steps.png', 0.3)
    print('wrote', out)


def export() -> None:
    import json
    build = {
        'label': "The horned mask: drag for the Upper 2 2/3' drawbar; it turns into a snail, step by step: its horn tips swell "
                 'into sleepy eyes, a candy spiral shell winds out of its back one turn at a time, its eyes open and it sings',
        'effects': [
            {'effect': 'sprites', 'place': 'around', 'front': FRONT_IDS, 'items': shell_items()},
            {'effect': 'sprites', 'place': 'over', 'items': over_items()},
        ],
    }
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', len(shell_items()) + len(over_items()), 'shapes to', path)


if __name__ == '__main__' and 'snail' in __import__('sys').argv[1:]:
    snail_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
