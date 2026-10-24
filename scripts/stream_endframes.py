# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (upper vibrato on) for the stream: the pale blue pool fed by a thin arcing waterfall.

    uv run scripts/stream_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mock', ROOT / 'scripts/pyramid_endframes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cs = importlib.util.spec_from_file_location('curl', ROOT / 'scripts/curl_endframes.py')
c = importlib.util.module_from_spec(cs)
cs.loader.exec_module(c)
m.CROP = (1380, 1760, 1520, 1180)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/stream-vibrato/endframes'
p, outlined, circle, ellipse = m.p, m.outlined, c.circle, c.ellipse
INK = 16
WATER, SPLASH, FALL = 'f134', 'f156', 'f133'
AQUA = '#ACF9FF'


def pts(fid):
    n = [float(v) for v in re.findall(r'-?\d+\.?\d*', m.FILLS[fid])]
    return list(zip(n[0::2], n[1::2]))


def top_edge(fid, x0, x1, n=40):
    """The top of the shape's outline, sampled across [x0, x1]: the smallest y near each x."""
    P = pts(fid)
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        near = [q[1] for q in P if abs(q[0] - x) < (x1 - x0) / n]
        if near:
            out.append((x, min(near)))
    return out


def smooth_open(P) -> str:
    d = f'M{p(*P[0])}'
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d


def waves() -> Image.Image:
    """Waves: the flat surface rises into rolling, curling crests along its length, outlined white-capped curls."""
    edge = top_edge(WATER, 1760, 2640, 30)
    out = ''
    for k in range(6):
        x = 1820 + k * 150
        y = min((q[1] for q in edge if abs(q[0] - x) < 40), default=2500) + 10
        h, w = 135 + (k % 2) * 35, 170
        crest = (f'M{p(x - w / 2, y)}C{p(x - w / 2, y - h * 0.8)} {p(x + w * 0.1, y - h * 1.15)} {p(x + w * 0.45, y - h * 0.75)}'
                 f'C{p(x + w * 0.25, y - h * 0.75)} {p(x + w * 0.05, y - h * 0.5)} {p(x + w * 0.2, y - h * 0.25)}'
                 f'C{p(x + w * 0.3, y - h * 0.1)} {p(x + w / 2, y)} {p(x + w / 2, y)}Z')
        out += outlined(crest, AQUA, INK)
        out += outlined(f'M{p(x - w * 0.1, y - h * 0.85)}C{p(x + w * 0.1, y - h * 1.08)} {p(x + w * 0.38, y - h * 0.9)} {p(x + w * 0.42, y - h * 0.78)}C{p(x + w * 0.2, y - h * 0.8)} {p(x, y - h * 0.72)} {p(x - w * 0.1, y - h * 0.85)}Z', '#ffffff', INK * 0.7)
    return m.compose(front=out)


def fountain() -> Image.Image:
    """Fountain: the thin waterfall swells into three arcing jets, and the splash bursts into big outlined drops."""
    out = ''
    src = (1585.0, 2150.0)
    for k, (tx, ty, lift, w) in enumerate([(1980, 2480, 260, 42), (2120, 2520, 360, 36), (1870, 2470, 180, 34)]):
        mx, my = (src[0] + tx) / 2, min(src[1], ty) - lift
        d = (f'M{p(src[0] - w / 2, src[1])}Q{p(mx - w / 2, my)} {p(tx - w / 2, ty)}L{p(tx + w / 2, ty)}'
             f'Q{p(mx + w / 2, my + w)} {p(src[0] + w / 2, src[1])}Z')
        out += outlined(d, ['#c9f7ff', AQUA, '#e3fbff'][k], INK * 0.8)
    rnd = random.Random(2)
    for k in range(9):
        a = math.radians(200 + k * 17)
        r = 150 + rnd.random() * 90
        x, y = 2090 + math.cos(a) * r, 2470 + math.sin(a) * r * 0.9
        s = 22 + rnd.random() * 18
        drop = f'M{p(x, y - s * 1.6)}C{p(x + s, y - s * 0.4)} {p(x + s, y + s)} {p(x, y + s)}C{p(x - s, y + s)} {p(x - s, y - s * 0.4)} {p(x, y - s * 1.6)}Z'
        out += outlined(drop, '#ffffff' if k % 2 else AQUA, INK * 0.7)
    return m.compose(front=out)


def fish() -> Image.Image:
    """Leaping fish: three outlined candy fish arc up out of the water, a little splash ring under each."""
    out = ''
    for x, y, rot, col, s in [(1880, 2470, -35, '#ffb36b', 1.0), (2170, 2420, -20, '#f2a6c6', 1.15), (2440, 2470, 25, '#c4a3f0', 0.9)]:
        body = f'M{p(x - 90 * s, y)}C{p(x - 40 * s, y - 55 * s)} {p(x + 50 * s, y - 50 * s)} {p(x + 85 * s, y)}C{p(x + 50 * s, y + 50 * s)} {p(x - 40 * s, y + 55 * s)} {p(x - 90 * s, y)}Z'
        tail = f'M{p(x - 80 * s, y)}L{p(x - 150 * s, y - 50 * s)}L{p(x - 140 * s, y + 55 * s)}Z'
        eye = outlined(circle(x + 45 * s, y - 12 * s, 14 * s), '#ffffff', INK * 0.6) + f'<path d="{circle(x + 48 * s, y - 12 * s, 6 * s)}" fill="#000"/>'
        out += f'<g transform="rotate({rot} {x} {y})">' + outlined(tail, col, INK * 0.8) + outlined(body, col, INK * 0.8) + eye + '</g>'
        out += outlined(ellipse(x, y + 140 * s, 80 * s, 22 * s), '#ffffff', INK * 0.6)
    return m.compose(front=out)


def wavy_banks() -> Image.Image:
    """Wavy water: the pool's outline itself wobbles into a sine-wave edge all the way round, as if the vibrato
    were drawn into it, with a wavy line across its middle."""
    def wob(x, y):
        return x, y + 34 * math.sin(x / 55.0)
    d = m.warp_path(m.FILLS[WATER], wob)
    mid = smooth_open([(1760 + i * 45, 2650 + 22 * math.sin(i * 1.3)) for i in range(20)])
    body = (f'<path d="{d}" fill="{AQUA}" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
            f'<path d="{mid}" fill="none" stroke="#000" stroke-width="{INK * 0.7}" stroke-linecap="round"/>')
    return m.compose(fill_over={WATER: 'M0 0Z'}, ink_over={i: 'M0 0Z' for i in m.own_ink(WATER)}, front=body + f'<path d="{m.FILLS[SPLASH]}" fill="#fff" fill-opacity="0.82"/>')


def whirlpool() -> Image.Image:
    """Whirlpool: a big outlined spiral eddy opens in the middle of the pool, smaller eddies either side."""
    out = ''
    for cx, cy, R, turns in [(2230, 2690, 150, 2.6), (1900, 2700, 80, 2.0), (2520, 2640, 70, 2.0)]:
        P = []
        n = 90
        for i in range(n + 1):
            t = i / n
            a = t * math.pi * 2 * turns
            r = R * (1 - t * 0.85)
            P.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.45))
        band = smooth_open(P)
        out += (f'<path d="{band}" fill="none" stroke="#000" stroke-width="{INK * 2.4}" stroke-linecap="round"/>'
                f'<path d="{band}" fill="none" stroke="#e3fbff" stroke-width="{INK * 1.2}" stroke-linecap="round"/>')
    return m.compose(front=out)


VERSIONS = [
    ('1-waves', 'Waves', waves),
    ('2-fountain', 'Fountain', fountain),
    ('3-leaping-fish', 'Leaping fish', fish),
    ('4-wavy-water', 'Wavy water', wavy_banks),
    ('5-whirlpool', 'Whirlpool', whirlpool),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = m.compose()
    before.save(OUT / '0-as-painted.png')
    tiles = [('0  As painted (vibrato off)', before)]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.5
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


# ---- round two: the froth gets bubbly and becomes a little cloud ---------------------------------------------------
FROTH_C = (2097.0, 2505.0)
CLOUD_WHITE = '#ffffff'
CLOUD_SHADE = '#e9e2ff'


SCRIB_MASK = ['']  # the insides of the clouds drawn so far, where the painting's scribbles are laid back over


def puffs(circles, fill=CLOUD_WHITE, edge=INK) -> str:
    SCRIB_MASK[0] += ''.join(f'<path d="{circle(x, y, max(1, r - edge * 1.2))}" fill="#fff"/>' for x, y, r in circles)
    """A cloud as the union of circles: every circle outlined first, then every circle filled on top, so only the
    outer edge keeps its ink, the way the painting draws its clouds."""
    ink = ''.join(f'<path d="{circle(x, y, r)}" fill="#000" stroke="#000" stroke-width="{edge * 2}"/>' for x, y, r in circles)
    body = ''.join(f'<path d="{circle(x, y, r)}" fill="{fill}"/>' for x, y, r in circles)
    return ink + body


def bubble(x, y, r, fill='#e3fbff') -> str:
    return outlined(circle(x, y, r), fill, INK * 0.8) + f'<path d="{circle(x + r * 0.35, y - r * 0.35, r * 0.22)}" fill="#fff"/>'


def no_froth():
    return {'fill_over': {SPLASH: 'M0 0Z'}, 'ink_over': {i: 'M0 0Z' for i in m.own_ink(SPLASH)}}


def cloud_circles(cx, cy, s=1.0, seed=4):
    """A lumpy cloud: a ring of uneven bumps round a body, flatter at the bottom, like the painting's own clouds."""
    rnd = random.Random(seed)
    out = [(cx, cy + 10 * s, 120 * s)]
    n = 11
    for k in range(n):
        a = math.pi * (0.9 + 1.2 * k / (n - 1))  # over the top, from left round to right
        rx, ry = 190 * s, 105 * s
        r = (45 + rnd.random() * 45) * s
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry, r))
    for k in range(4):  # the flatter underside
        out.append((cx - 150 * s + k * 100 * s, cy + 70 * s, (45 + rnd.random() * 15) * s))
    return out


def b1_bubbly() -> Image.Image:
    """Bubbly froth: the splash boils up into a heap of round outlined bubbles, big at the base, small at the top."""
    rnd = random.Random(1)
    out = ''
    x0, y0 = FROTH_C
    for k in range(26):
        t = k / 25
        r = 60 - 40 * t + rnd.random() * 12
        x = x0 + (rnd.random() - 0.5) * 300 * (1 - 0.5 * t)
        y = y0 + 110 - 330 * t + (rnd.random() - 0.5) * 30
        out += bubble(x, y, r, ['#e3fbff', '#ffffff', '#f3e9ff'][k % 3])
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **no_froth())


def b2_cloud_rising() -> Image.Image:
    """Froth to cloud: the splash puffs up into a little cumulus cloud floating above the pool, a column of bubbles
    still rising from the water into it."""
    cx, cy = FROTH_C[0] + 20, FROTH_C[1] - 330
    out = ''
    for k, (x, y, r) in enumerate([(2090, 2470, 40), (2110, 2390, 32), (2080, 2320, 26), (2105, 2255, 20)]):
        out += bubble(x, y, r)
    out += puffs(cloud_circles(cx, cy, 0.95))
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **no_froth())


def b3_cloud_face() -> Image.Image:
    """Happy cloud: the froth becomes a round puffy cloud with a sleepy, smiling face, sitting on the water."""
    cx, cy = FROTH_C[0] + 10, FROTH_C[1] - 120
    out = puffs(cloud_circles(cx, cy, 1.05))
    for ex in (cx - 70, cx + 70):
        out += f'<path d="M{p(ex - 30, cy - 20)}C{p(ex - 15, cy + 5)} {p(ex + 15, cy + 5)} {p(ex + 30, cy - 20)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
    out += outlined(f'M{p(cx - 45, cy + 40)}C{p(cx - 30, cy + 95)} {p(cx + 30, cy + 95)} {p(cx + 45, cy + 40)}Z', '#f64c76', INK * 0.9)
    out += ''.join(f'<path d="{circle(x, cy + 30, 22)}" fill="#ffb3c8"/>' for x in (cx - 120, cx + 120))
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **no_froth())


def b4_rainbow() -> Image.Image:
    """Cloud and rainbow: the froth lifts into a cloud and a little candy rainbow arcs from it back down into the
    pool."""
    cx, cy = FROTH_C[0] + 40, FROTH_C[1] - 300
    out = ''
    cols = ['#ff7a8a', '#ffb36b', '#ffe066', '#9cf27c', '#7fd8f5', '#c4a3f0']
    ax, ay, R = cx + 330, cy + 300, 300
    for k, col in enumerate(cols):
        r_out, r_in = R - k * 26, R - (k + 1) * 26
        d = (f'M{p(ax - r_out, ay)}A{r_out} {r_out} 0 0 1 {p(ax + r_out, ay)}L{p(ax + r_in, ay)}'
             f'A{r_in} {r_in} 0 0 0 {p(ax - r_in, ay)}Z')
        out += outlined(d, col, INK * 0.7)
    out += puffs(cloud_circles(cx, cy, 0.8))
    out += puffs([(ax + R - 40, ay - 10, 55), (ax + R + 20, ay + 20, 45)], CLOUD_WHITE, INK)
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **no_froth())


def b5_raincloud() -> Image.Image:
    """Bubble cloud: the froth rises as a cloud made of bubbles (each puff an outlined bubble with a shine), dropping
    a few fat outlined droplets back into the pool."""
    cx, cy = FROTH_C[0] + 20, FROTH_C[1] - 300
    circles = cloud_circles(cx, cy, 0.9)
    out = puffs(circles, '#eafcff')
    out += ''.join(f'<path d="{circle(x + r * 0.35, y - r * 0.4, r * 0.18)}" fill="#fff"/>'
                   f'<path d="M{p(x - r * 0.55, y + r * 0.1)}A{r * 0.6:.1f} {r * 0.6:.1f} 0 0 0 {p(x + r * 0.1, y + r * 0.6)}" fill="none" stroke="#bfefff" stroke-width="10" stroke-linecap="round"/>'
                   for x, y, r in circles[:5])
    for x, y, s in [(cx - 90, cy + 190, 26), (cx + 10, cy + 230, 22), (cx + 110, cy + 200, 26), (cx - 30, cy + 300, 20)]:
        drop = f'M{p(x, y - s * 1.6)}C{p(x + s, y - s * 0.4)} {p(x + s, y + s)} {p(x, y + s)}C{p(x - s, y + s)} {p(x - s, y - s * 0.4)} {p(x, y - s * 1.6)}Z'
        out += outlined(drop, '#bff6ff', INK * 0.7)
    out += ''.join(outlined(ellipse(x, 2560, 50, 14), '#ffffff', INK * 0.6) for x in (cx - 90, cx + 110))
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **no_froth())


ROUND2 = [
    ('1-bubbly-froth', 'Bubbly froth', b1_bubbly),
    ('2-froth-to-cloud', 'Froth to cloud', b2_cloud_rising),
    ('3-happy-cloud', 'Happy cloud', b3_cloud_face),
    ('4-cloud-and-rainbow', 'Cloud and rainbow', b4_rainbow),
    ('5-bubble-cloud', 'Bubble cloud', b5_raincloud),
]


def round2() -> None:
    out = OUT.parent / 'froth'
    out.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (vibrato off)', m.compose())]
    for slug, title, fn in ROUND2:
        SCRIB_MASK[0] = ''
        im = fn()
        im.save(out / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.5
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
    sheet.save(out / 'sheet.png')
    print('wrote', out / 'sheet.png')


if __name__ == '__main__' and 'froth' in __import__('sys').argv[1:]:
    round2()


# ---- chosen: bubble cloud + rainbow ---------------------------------------------------------------------------------
def ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def win(t, a, b):
    return ease((t - a) / (b - a))


RAINBOW = ['#ff7a8a', '#ffb36b', '#ffe066', '#9cf27c', '#7fd8f5', '#c4a3f0']


def arc_band(ax, ay, r_out, r_in, a_end, n=40) -> str:
    """A rainbow band from the left foot (180 degrees) round over the top to a_end (degrees, 0 = right foot)."""
    pts_o, pts_i = [], []
    for i in range(n + 1):
        a = math.radians(180 - (180 - a_end) * i / n)
        pts_o.append((ax + math.cos(a) * r_out, ay - math.sin(a) * r_out))
        pts_i.append((ax + math.cos(a) * r_in, ay - math.sin(a) * r_in))
    return 'M' + 'L'.join(p(*q) for q in pts_o + pts_i[::-1]) + 'Z'


def combo_frame(t: float) -> Image.Image:
    """Vibrato at t: the froth bubbles up (0..0.3), a column of bubbles rises (0.1..0.45), the bubble cloud gathers
    above (0.25..0.6), the rainbow arcs out of it and down into the pool (0.5..0.85), droplets fall last (0.75..1)."""
    if t <= 0:
        return m.compose()
    SCRIB_MASK[0] = ''
    out = ''
    x0, y0 = FROTH_C
    rnd = random.Random(1)
    fb = win(t, 0.0, 0.3)
    for k in range(10):
        r = (55 - 3 * k + rnd.random() * 10) * fb
        x = x0 + (rnd.random() - 0.5) * 260
        y = y0 + 80 - 18 * k + (rnd.random() - 0.5) * 30
        if r > 2:
            out += bubble(x, y, r, ['#e3fbff', '#ffffff', '#f3e9ff'][k % 3])
    for k, (x, y, r) in enumerate([(2090, 2400, 38), (2110, 2320, 32), (2085, 2255, 26), (2105, 2195, 20)]):
        g = win(t, 0.1 + k * 0.07, 0.25 + k * 0.07)
        if g > 0.01:
            out += bubble(x, y, r * g)
    cx, cy = FROTH_C[0] + 20, FROTH_C[1] - 300
    cg = win(t, 0.25, 0.6)
    ax, ay, R = cx + 330, cy + 300, 300
    rg = win(t, 0.5, 0.85)
    bow = ''
    if rg > 0.01:
        for k, col in enumerate(RAINBOW):
            bow += outlined(arc_band(ax, ay, R - k * 26, R - (k + 1) * 26, 180 - 180 * rg), col, INK * 0.7)
        if rg > 0.95:
            bow += puffs([(ax + R - 40, ay - 10, 55), (ax + R + 20, ay + 20, 45)], CLOUD_WHITE, INK)
    out += bow
    if cg > 0.01:
        circles = [(cx + (x - cx) * cg, cy + (y - cy) * cg, r * cg) for x, y, r in cloud_circles(cx, cy, 0.9)]
        out += puffs(circles, '#eafcff')
        out += ''.join(f'<path d="{circle(x + r * 0.35, y - r * 0.4, r * 0.18)}" fill="#fff"/>' for x, y, r in circles[:6])
    dg = win(t, 0.75, 1.0)
    if dg > 0.01:
        for k, (x, y, s) in enumerate([(cx - 90, cy + 190, 26), (cx + 10, cy + 230, 22), (cx - 30, cy + 300, 20)]):
            g = win(t, 0.75 + k * 0.06, 0.9 + k * 0.03)
            if g > 0.01:
                s *= g
                drop = f'M{p(x, y - s * 1.6)}C{p(x + s, y - s * 0.4)} {p(x + s, y + s)} {p(x, y + s)}C{p(x - s, y + s)} {p(x - s, y - s * 0.4)} {p(x, y - s * 1.6)}Z'
                out += outlined(drop, '#bff6ff', INK * 0.7)
    kw = no_froth() if fb > 0.6 else {}
    return m.compose(front=out, rescrib=SCRIB_MASK[0], **kw)


def combo_main() -> None:
    out = OUT.parent / 'bubble-rainbow'
    out.mkdir(parents=True, exist_ok=True)
    combo_frame(1.0).save(out / 'end-frame.png')
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [combo_frame(t) for t in frames]
    w, h = tiles[0].size
    sc = 0.36
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
    import shutil
    import subprocess
    tmp = out / '_frames'
    tmp.mkdir(exist_ok=True)
    seq = [k / 20 for k in range(21)] + [k / 20 for k in range(19, 0, -1)]
    for i, tt in enumerate(seq):
        combo_frame(tt).convert('RGB').resize((560, round(560 * h / w)), Image.LANCZOS).save(tmp / f'{i:03d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', str(tmp / '%03d.png'), '-vf',
                    'split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0',
                    str(out / 'sweep.gif')], check=True)
    shutil.rmtree(tmp)
    print('wrote', out)


if __name__ == '__main__' and 'combo' in __import__('sys').argv[1:]:
    combo_main()
