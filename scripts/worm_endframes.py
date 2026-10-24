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
    worm = f'<path d="{m.FILLS[WORM]}" fill="#FEC5FF" fill-opacity="0.7"/><g clip-path="url(#worm-body)">{bands}</g><g fill="#000">{worm_ink}</g>'
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


if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    main()


# ---- the chosen direction: trumpet bell + blooming crest + ripples and bands --------------------------------------
def ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def win(t: float, a: float, b: float) -> float:
    return ease((t - a) / (b - a))


CENTRE = [(3305, 1560), (3300, 1450), (3330, 1360), (3400, 1280), (3500, 1240)]
BAND_COLS = ['#f64c76', '#c4a3f0', '#ffe066', '#7fd8f5', '#f64c76']
RINGS = [(330, '#c9f0ff'), (250, '#ffffff'), (175, '#a9cfdc')]


def combo_frame(t: float) -> Image.Image:
    """Expression at t: ripples spread from the hole first (0..0.45, innermost first), bands climb the body from the
    base (0.15..0.7), the crest blooms (0.4..0.85), and the bell flares open last (0.55..1) with its sound waves."""
    if t <= 0:
        return m.compose()
    bx, by = BASE
    rings = ''
    for k, (rx, col) in enumerate(RINGS):  # largest first, so the smaller sit on top; the innermost appears first
        start = (len(RINGS) - 1 - k) * 0.12
        g = win(t, start, start + 0.3)
        if g > 0.01:
            rings += outlined(ellipse(bx, by + 10, rx * g, rx * 0.35 * g), col, INK * 0.8)
    bands = ''
    for k, (x, y) in enumerate(CENTRE):
        g = win(t, 0.15 + k * 0.1, 0.3 + k * 0.1)
        if g <= 0.01:
            continue
        nx, ny = CENTRE[min(k + 1, len(CENTRE) - 1)]
        px_, py_ = CENTRE[max(k - 1, 0)]
        ang = math.degrees(math.atan2(ny - py_, nx - px_))
        hw = 22 * g
        bands += f'<g transform="rotate({ang:.0f} {x} {y})">' + outlined(f'M{p(x - hw, y - 70)}L{p(x + hw, y - 70)}L{p(x + hw, y + 70)}L{p(x - hw, y + 70)}Z', BAND_COLS[k], INK * 0.8) + '</g>'
    clip = f'<defs><clipPath id="worm-body"><path d="{m.FILLS[WORM]}"/></clipPath></defs>'
    worm_ink = ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(WORM))
    worm = f'<path d="{m.FILLS[WORM]}" fill="#FEC5FF" fill-opacity="0.7"/><g clip-path="url(#worm-body)">{bands}</g><g fill="#000">{worm_ink}</g>'
    # crest: puffs grow from the tuft, outer ring then inner
    cg = win(t, 0.4, 0.85)
    crest = ''
    if cg > 0.01:
        rnd = random.Random(3)
        cx, cy = TUFT
        cols = ['#f2a6c6', '#ffe066', '#c4a3f0', '#7fd8f5', '#b4e0a2', '#ffb36b', '#f2a6c6']
        for k in range(7):
            a = math.radians(200 + k * 24)
            r = 210 * cg
            rr = (70 + rnd.random() * 30) * cg
            crest += outlined(circle(cx + math.cos(a) * r, cy + 70 + math.sin(a) * r, rr), cols[k], INK)
        crest += ''.join(outlined(circle(cx + dx * cg, cy + dy * cg, rr * cg), '#fff3fb', INK * 0.8) for dx, dy, rr in [(-110, -40, 60), (0, -80, 70), (110, -40, 60)])
    # bell: flares from the head; waves follow
    bg = win(t, 0.55, 1.0)
    bell_svg = ''
    if bg > 0.01:
        x, y = HEAD[0] + 40, HEAD[1] + 20
        L, H = 200 * bg, 160 * bg + 55 * (1 - bg)
        flare = (f'M{p(x - 40, y - 55)}C{p(x + 60 * bg, y - 55 - 15 * bg)} {p(x + 120 * bg, y - 55 - 95 * bg)} {p(x + 0.875 * L, y - H - 10 * bg)}'
                 f'L{p(x + L, y + H - 10 * bg)}C{p(x + 130 * bg, y + 55 + 65 * bg)} {p(x + 60 * bg, y + 55 + 5 * bg)} {p(x - 40, y + 55)}Z')
        bell_svg = outlined(flare, '#f7b3f0', INK) + outlined(ellipse(x + L - 12 * bg, y - 10, 34 * bg + 4, H), '#7a2a4f', INK)
        for k, (r, w, col) in enumerate([(110, 40, '#ffffff'), (190, 36, '#fbe0ff'), (270, 30, '#ffffff')]):
            wg = win(t, 0.7 + k * 0.08, 0.9 + k * 0.05)
            if wg > 0.01:
                bell_svg += swoosh(x + L - 10, y - 10, r * (0.6 + 0.4 * wg), -40 * wg, 40 * wg, w * wg, col)
    return m.compose(fill_over={WORM: 'M0 0Z'}, ink_over={i: 'M0 0Z' for i in m.own_ink(WORM)},
                     front=clip + rings + worm + crest + bell_svg)


def combo_main() -> None:
    m.CROP = (3020, 960, 1280, 880)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = OUT.parent / 'combined'
    out.mkdir(parents=True, exist_ok=True)
    combo_frame(1.0).save(out / 'end-frame.png')
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [combo_frame(t) for t in frames]
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * 5 + 60, th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (t, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {t:.2f}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    import shutil
    import subprocess
    tmp = out / '_frames'
    tmp.mkdir(exist_ok=True)
    seq = [k / 20 for k in range(21)] + [k / 20 for k in range(19, 0, -1)]
    for i, t in enumerate(seq):
        combo_frame(t).convert('RGB').resize((480, round(480 * h / w)), Image.LANCZOS).save(tmp / f'{i:03d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', str(tmp / '%03d.png'), '-vf',
                    'split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0',
                    str(out / 'sweep.gif')], check=True)
    shutil.rmtree(tmp)
    print('wrote', out)


if __name__ == '__main__' and 'combo' in __import__('sys').argv[1:]:
    combo_main()


def export_effects() -> list[dict]:
    """The approved worm progression as the app's sprites effects (same shapes, colours and windows as combo_frame)."""
    import math as _m

    def poly(pts):
        return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'

    def crescent_d(cx, cy, r, a0, a1, w):
        n, outer, inner = 28, [], []
        for i in range(n + 1):
            t = i / n
            a = _m.radians(a0 + (a1 - a0) * t)
            th = w * _m.sin(_m.pi * t) ** 0.9
            outer.append((cx + _m.cos(a) * (r + th / 2), cy + _m.sin(a) * (r + th / 2)))
            inner.append((cx + _m.cos(a) * (r - th / 2), cy + _m.sin(a) * (r - th / 2)))
        return poly(outer + inner[::-1])

    bx, by = BASE
    rings = []
    for k, (rx, col) in enumerate(RINGS):
        st = (len(RINGS) - 1 - k) * 0.12
        rings.append({'d': ellipse(bx, by + 10, rx, rx * 0.35), 'fill': col, 'edge': INK * 0.8, 'at': [bx, by + 10], 'start': st, 'end': st + 0.3, 'grow': 'scale'})
    bands = []
    for k, (x, y) in enumerate(CENTRE):
        nx, ny = CENTRE[min(k + 1, len(CENTRE) - 1)]
        px_, py_ = CENTRE[max(k - 1, 0)]
        a = _m.atan2(ny - py_, nx - px_)
        rot = lambda dx, dy: (x + dx * _m.cos(a) - dy * _m.sin(a), y + dx * _m.sin(a) + dy * _m.cos(a))
        d = poly([rot(-22, -70), rot(22, -70), rot(22, 70), rot(-22, 70)])
        bands.append({'d': d, 'fill': BAND_COLS[k], 'edge': INK * 0.8, 'at': [x, y], 'start': 0.15 + k * 0.1, 'end': 0.3 + k * 0.1, 'grow': 'x'})
    import random as _r
    rnd = _r.Random(3)
    cx, cy = TUFT
    cols = ['#f2a6c6', '#ffe066', '#c4a3f0', '#7fd8f5', '#b4e0a2', '#ffb36b', '#f2a6c6']
    crest = []
    for k in range(7):
        a = _m.radians(200 + k * 24)
        rr = 70 + rnd.random() * 30
        crest.append({'d': circle(cx + _m.cos(a) * 210, cy + 70 + _m.sin(a) * 210, rr), 'fill': cols[k], 'edge': INK, 'at': [cx, cy + 70], 'start': 0.4, 'end': 0.85, 'grow': 'scale'})
    for dx, dy, rr in [(-110, -40, 60), (0, -80, 70), (110, -40, 60)]:
        crest.append({'d': circle(cx + dx, cy + dy, rr), 'fill': '#fff3fb', 'edge': INK * 0.8, 'at': [cx, cy], 'start': 0.4, 'end': 0.85, 'grow': 'scale'})
    x, y = HEAD[0] + 40, HEAD[1] + 20
    flare = (f'M{p(x - 40, y - 55)}C{p(x + 60, y - 70)} {p(x + 120, y - 150)} {p(x + 175, y - 170)}'
             f'L{p(x + 200, y + 150)}C{p(x + 130, y + 120)} {p(x + 60, y + 60)} {p(x - 40, y + 55)}Z')
    bell = [{'d': flare, 'fill': '#f7b3f0', 'edge': INK, 'at': [x - 40, y], 'start': 0.55, 'end': 1.0, 'grow': 'scale'},
            {'d': ellipse(x + 188, y - 10, 38, 160), 'fill': '#7a2a4f', 'edge': INK, 'at': [x - 40, y], 'start': 0.55, 'end': 1.0, 'grow': 'scale'}]
    for k, (r, w, col) in enumerate([(110, 40, '#ffffff'), (190, 36, '#fbe0ff'), (270, 30, '#ffffff')]):
        bell.append({'d': crescent_d(x + 190, y - 10, r, -40, 40, w), 'fill': col, 'edge': INK * 0.8, 'at': [x + 190, y - 10],
                     'start': 0.7 + k * 0.08, 'end': 0.9 + k * 0.05, 'grow': 'scale'})
    rnd2 = lambda v: [round(q, 1) for q in v]
    for it in rings + bands + crest + bell:
        it['at'] = rnd2(it['at'])
        it['edge'] = round(it['edge'], 1)
    return [{'effect': 'sprites', 'place': 'around', 'items': rings},
            {'effect': 'sprites', 'place': 'on', 'items': bands},
            {'effect': 'sprites', 'place': 'over', 'items': crest + bell}]


if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'worm-expression':
            b['label'] = 'The worm swells with Expression: drag up and down; ripples spread, bands climb it, its crest blooms and its head flares into a trumpet'
            b['effects'] = export_effects()
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', sum(len(e['items']) for e in export_effects()), 'shapes')
