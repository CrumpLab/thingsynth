# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Expression at 1, the swell pedal fully open) for the pink worm rising from the tunnel's rim.

    uv run scripts/worm_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mock', ROOT / 'scripts/pyramid_endframes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cs = importlib.util.spec_from_file_location('curl', ROOT / 'scripts/curl_endframes.py')
c = importlib.util.module_from_spec(cs)
cs.loader.exec_module(c)
m.CROP = (3020, 960, 980, 880)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/worm-expression/endframes'
p, outlined, swoosh, circle, ellipse, star = m.p, m.outlined, c.swoosh, c.circle, c.ellipse, c.star
INK = 16
WORM = 'f220'
BASE = (3312.0, 1680.0)   # the ring it rises from
HEAD = (3700.0, 1260.0)   # its droopy head
NOSE = (3600.0, 1300.0)   # under the hook, where a mouth would be
TUFT = (3530.0, 1130.0)   # the frilly tuft on its crown
PINK = '#F6D3E6'  # the worm as it reads over the wash (its fill is #FEC5FF at 70%)


def bell() -> Image.Image:
    """Trumpet: its head opens into a flared horn bell, pointing out to the right, sound waves rolling out of it."""
    x, y = HEAD[0] + 40, HEAD[1] + 20
    flare = (f'M{p(x - 40, y - 55)}C{p(x + 60, y - 70)} {p(x + 120, y - 150)} {p(x + 175, y - 170)}'
             f'L{p(x + 200, y + 150)}C{p(x + 130, y + 120)} {p(x + 60, y + 60)} {p(x - 40, y + 55)}Z')
    mouth = outlined(ellipse(x + 188, y - 10, 34, 160), '#7a2a4f', INK)
    waves = ''.join(swoosh(x + 190, y - 10, r, -40, 40, w, col) for r, w, col in [(110, 40, '#ffffff'), (190, 36, '#fbe0ff'), (270, 30, '#ffffff')])
    return m.compose(front=outlined(flare, '#f7b3f0', INK) + mouth + waves)


def rearing() -> Image.Image:
    """Rearing up: the whole worm stretches taller out of its ring and lifts its head high, outlined, the pyramid's face
    filling in where it was."""
    d = m.FILLS[WORM]
    ink = ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(WORM))
    near = ['f136', 'f219', 'f218']
    grow = ''.join(f'<path d="{m.FILLS[f]}" fill="{m.FP[f]["fill"]}" stroke="{m.FP[f]["fill"]}" stroke-width="200" stroke-linejoin="round"/>' for f in near)
    cover = (f'<defs><clipPath id="worm-gap"><path d="{d}" stroke="#000" stroke-width="40" stroke-linejoin="round"/></clipPath></defs>'
             f'<g clip-path="url(#worm-gap)"><path d="{d}" fill="#FFB89A" stroke="#FFB89A" stroke-width="40"/>{grow}</g>')
    bx, by = BASE
    worm = (f'<g transform="translate({bx} {by}) rotate(-14) scale(1.0 1.32) translate({-bx} {-by})">'
            f'<path d="{d}" fill="{PINK}"/><g fill="#000">{ink}</g></g>')
    return m.compose(fill_over={WORM: 'M0 0Z'}, front=worm, ink_over={i: 'M0 0Z' for i in m.own_ink(WORM)})


def singing() -> Image.Image:
    """Singing: a mouth opens under its droopy head and outlined music notes float out of it."""
    x, y = NOSE
    mouth = outlined(f'M{p(x - 70, y)}C{p(x - 60, y + 90)} {p(x + 60, y + 90)} {p(x + 70, y)}C{p(x + 30, y + 20)} {p(x - 30, y + 20)} {p(x - 70, y)}Z', '#7a2a4f', INK)
    tongue = outlined(f'M{p(x - 35, y + 45)}C{p(x - 20, y + 75)} {p(x + 25, y + 75)} {p(x + 35, y + 45)}Z', '#f64c76', INK * 0.7)

    def note(nx, ny, s, col, rot):
        head = f'<g transform="rotate(-20 {nx} {ny})">' + outlined(ellipse(nx, ny, 34 * s, 24 * s), col, INK * 0.8) + '</g>'
        stem = outlined(f'M{p(nx + 26 * s, ny - 6 * s)}L{p(nx + 26 * s, ny - 130 * s)}L{p(nx + 40 * s, ny - 130 * s)}L{p(nx + 40 * s, ny - 6 * s)}Z', col, INK * 0.7)
        flag = outlined(f'M{p(nx + 40 * s, ny - 130 * s)}C{p(nx + 90 * s, ny - 110 * s)} {p(nx + 95 * s, ny - 70 * s)} {p(nx + 70 * s, ny - 50 * s)}C{p(nx + 80 * s, ny - 80 * s)} {p(nx + 60 * s, ny - 95 * s)} {p(nx + 40 * s, ny - 100 * s)}Z', col, INK * 0.7)
        return f'<g transform="rotate({rot} {nx} {ny})">' + stem + flag + head + '</g>'
    notes = note(3640, 1560, 1.0, '#7fd8f5', -10) + note(3800, 1480, 0.85, '#ffe066', 8) + note(3880, 1640, 0.7, '#b4e0a2', -14)
    return m.compose(front=notes + mouth + tongue)


def blooming() -> Image.Image:
    """Blooming crest: the frilly tuft on its crown billows into a big scalloped crest of candy puffs."""
    rnd = random.Random(3)
    cx, cy = TUFT
    lobes = ''
    cols = ['#f2a6c6', '#ffe066', '#c4a3f0', '#7fd8f5', '#b4e0a2', '#ffb36b', '#f2a6c6']
    for k in range(7):
        a = math.radians(200 + k * 24)
        r = 210
        x, y = cx + math.cos(a) * r, cy + 70 + math.sin(a) * r
        lobes += outlined(circle(x, y, 70 + rnd.random() * 30), cols[k], INK)
    inner = ''.join(outlined(circle(cx + dx, cy + dy, rr), '#fff3fb', INK * 0.8) for dx, dy, rr in [(-110, -40, 60), (0, -80, 70), (110, -40, 60)])
    return m.compose(front=lobes + inner)


def ripples() -> Image.Image:
    """Ripples and bands: its body gains bold candy rings along its length and ripples spread from the hole it rises
    out of."""
    bx, by = BASE
    rings = ''.join(outlined(ellipse(bx, by + 10, rx, rx * 0.35), col, INK * 0.8)
                    for rx, col in [(330, '#c9f0ff'), (250, '#ffffff'), (175, '#a9cfdc')])
    # bands across the tube, along its centre line
    centre = [(3305, 1560), (3300, 1450), (3330, 1360), (3400, 1280), (3500, 1240)]
    bands = ''
    for k, (x, y) in enumerate(centre):
        nx, ny = centre[min(k + 1, len(centre) - 1)]
        px_, py_ = centre[max(k - 1, 0)]
        ang = math.degrees(math.atan2(ny - py_, nx - px_))
        bands += f'<g transform="rotate({ang:.0f} {x} {y})">' + outlined(f'M{p(x - 22, y - 70)}L{p(x + 22, y - 70)}L{p(x + 22, y + 70)}L{p(x - 22, y + 70)}Z', ['#f64c76', '#c4a3f0', '#ffe066', '#7fd8f5', '#f64c76'][k], INK * 0.8) + '</g>'
    clip = f'<defs><clipPath id="worm-body"><path d="{m.FILLS[WORM]}"/></clipPath></defs>'
    worm_ink = ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(WORM))
    worm = f'<path d="{m.FILLS[WORM]}" fill="{PINK}"/><g clip-path="url(#worm-body)">{bands}</g><g fill="#000">{worm_ink}</g>'
    return m.compose(front=clip + rings + worm)


VERSIONS = [
    ('1-trumpet', 'Trumpet bell', bell),
    ('2-rearing-up', 'Rearing up', rearing),
    ('3-singing', 'Singing', singing),
    ('4-blooming-crest', 'Blooming crest', blooming),
    ('5-ripples-bands', 'Ripples and bands', ripples),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = m.compose()
    before.save(OUT / '0-as-painted.png')
    tiles = [('0  As painted (quiet)', before)]
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


if __name__ == '__main__':
    main()
