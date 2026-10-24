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
