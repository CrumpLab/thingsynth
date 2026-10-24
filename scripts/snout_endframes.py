# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Leslie mic distance at its farthest) for the lavender snout: a pale cream head facing left, a
pink snout with an orange nostril that a pale blue straw goes into, a sleepy yellow eye at the right.

    uv run scripts/snout_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (550, 1000, 1450, 900)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/leslie-mic-distance/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
CREAM, PINK, YEL, ORANGE = '#FFE3A7', '#FFA7E6', '#FDFF44', '#ff9f2a'
SNOUT_FRONT = (1100.0, 1545.0)
NOSTRIL = (1223.0, 1517.0)
EYE = (1440.0, 1505.0)
HEAD = ['f250', 'f252', 'f256', 'f255', 'f307']


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


def open_eye(x, y, rx=88, ry=62) -> str:
    return (outlined(ellipse(x, y, rx, ry, -5), '#ffffff', INK) + outlined(circle(x - 14, y + 4, ry * 0.62), YEL, INK * 0.8)
            + f'<path d="{circle(x - 14, y + 4, ry * 0.3)}" fill="#000"/>' + f'<path d="{circle(x - 4, y - 8, ry * 0.12)}" fill="#fff"/>')


def v1_trunk() -> Image.Image:
    """Elephant trunk: the pink snout stretches into a long elephant trunk that curls down and lifts its tip in a
    trumpet flare."""
    x, y = SNOUT_FRONT
    P = bez((x + 60, y), (x - 250, y + 40), (x - 420, y + 260), (x - 300, y + 330), 28)
    P += bez(P[-1], (x - 200, y + 380), (x - 120, y + 260), (x - 210, y + 160), 14)[1:]
    out = outlined(tube(P, 92, 46), PINK, INK)
    for k in range(5, len(P) - 6, 5):
        (ax, ay), (bx, by) = P[k], P[k + 1]
        d = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / d, (bx - ax) / d
        w = 92 - 46 * k / len(P)
        out += outlined(ellipse(ax, ay, w * 0.85, 9, math.degrees(math.atan2(ny, nx))), '#ff86d6', INK * 0.5)
    tx, ty = P[-1]
    out += outlined(ellipse(tx, ty, 70, 40, -30), PINK, INK) + outlined(ellipse(tx, ty, 40, 20, -30), ORANGE, INK * 0.8)
    return draw(out, ['f252'], open_eye(*EYE))


def v2_ears() -> Image.Image:
    """Listening ears: two huge ears unfurl up from behind its head, pink inside, cupped to hear from far away."""
    out = ''
    for bx, by, ang, col in [(1330, 1360, -125, '#ffd38a'), (1520, 1370, -60, '#ffd38a')]:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        R = lambda u, v: (bx + ca * u - sa * v, by + sa * u + ca * v)
        ear = f'M{p(*R(0, -70))}C{p(*R(200, -180))} {p(*R(380, -120))} {p(*R(380, 0))}C{p(*R(380, 120))} {p(*R(200, 180))} {p(*R(0, 70))}Z'
        inner = f'M{p(*R(60, -40))}C{p(*R(200, -120))} {p(*R(320, -80))} {p(*R(320, 0))}C{p(*R(320, 80))} {p(*R(200, 120))} {p(*R(60, 40))}Z'
        out += outlined(ear, col, INK) + outlined(inner, '#ff9fd6', INK * 0.8)
    return draw(out, HEAD, open_eye(*EYE))


def v3_bubble() -> Image.Image:
    """Bubblegum: a huge pink bubblegum bubble blows out of its snout."""
    x, y, r = 880.0, 1470.0, 210.0
    out = outlined(circle(x, y, r), '#ff9fe0', INK * 1.1)
    out += outlined(ellipse(x - 80, y - 90, 55, 32, -35), '#ffffff', INK * 0.6)
    out += outlined(ellipse(x + 95, y + 110, 20, 14, -35), '#ffffff', INK * 0.5)
    return draw('', [], out)


def v4_telescope() -> Image.Image:
    """Telescope: a brass telescope slides out from its eye, section after section, a big cyan lens at the end."""
    x, y = EYE
    a = math.radians(-8)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x + ca * u - sa * v, y + sa * u + ca * v)
    out = ''
    for u0, u1, w, col in [(320, 470, 58, '#f0c75a'), (180, 340, 70, '#e6b44c'), (40, 200, 84, '#d9a23c')]:
        out += outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(u0, -w), (u1, -w), (u1, w), (u0, w)]) + 'Z', col, INK)
        out += outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(u1 - 22, -w - 8), (u1, -w - 8), (u1, w + 8), (u1 - 22, w + 8)]) + 'Z', '#b8862e', INK * 0.8)
    out += outlined(ellipse(*R(470, 0), 30, 64, -8), '#2DFFF4', INK)
    out += outlined(ellipse(*R(462, -24), 8, 16, -8), '#ffffff', INK * 0.4)
    return draw('', [], open_eye(*EYE) + out)


def v5_accordion() -> Image.Image:
    """Accordion snout: its snout stretches far out to the left in pink pleated bellows, the snout tip and nostril
    at the far end."""
    x, y = SNOUT_FRONT
    out = ''
    n = 8
    for k in range(n):
        u0, u1 = x + 40 - k * 55, x + 40 - (k + 1) * 55
        h0, h1 = (95, 70) if k % 2 == 0 else (70, 95)
        out += outlined(f'M{p(u0, y - h0)}L{p(u1, y - h1)}L{p(u1, y + h1)}L{p(u0, y + h0)}Z', ['#ffa7e6', '#ff86d6'][k % 2], INK * 0.9)
    tx = x + 40 - n * 55
    out += outlined(ellipse(tx - 20, y, 70, 100), PINK, INK) + outlined(ellipse(tx - 30, y - 10, 22, 30), ORANGE, INK * 0.8)
    return draw('', [], out + open_eye(*EYE))


VERSIONS = [
    ('1-elephant-trunk', 'Elephant trunk', v1_trunk),
    ('2-listening-ears', 'Listening ears', v2_ears),
    ('3-bubblegum', 'Bubblegum', v3_bubble),
    ('4-telescope', 'Telescope', v4_telescope),
    ('5-accordion-snout', 'Accordion snout', v5_accordion),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (close)', m.compose())]
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


# ---- chosen: telescope --------------------------------------------------------------------------------------------
# Mic distance from close to far: the sleepy eye fades (0..0.15) as a wide-open eye opens (0.05..0.25), then the
# brass telescope slides out of it one section after another (0.2..0.45, 0.4..0.65, 0.6..0.85), and the cyan lens
# and its glint come last (0.8..1).
def telescope_items() -> list[dict]:
    x, y = EYE
    a = math.radians(-8)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x + ca * u - sa * v, y + sa * u + ca * v)
    items = []
    A = lambda d, f, e, at, s, t, grow='scale': items.append({'d': d, 'fill': f, 'edge': round(e, 1), 'at': [round(at[0], 1), round(at[1], 1)],
                                                               'start': round(s, 3), 'end': round(t, 3), 'grow': grow})
    ex, ey = EYE
    A(ellipse(ex, ey, 88, 62, -5), '#ffffff', INK, (ex, ey), 0.05, 0.22, 'y')
    A(circle(ex - 14, ey + 4, 62 * 0.62), YEL, INK * 0.8, (ex - 14, ey + 4), 0.1, 0.25)
    A(circle(ex - 14, ey + 4, 62 * 0.3), '#000000', 0, (ex - 14, ey + 4), 0.12, 0.27)
    A(circle(ex - 4, ey - 8, 62 * 0.12), '#ffffff', 0, (ex - 4, ey - 8), 0.18, 0.28)
    secs = [(320, 470, 58, '#f0c75a', 0.6, 0.85), (180, 340, 70, '#e6b44c', 0.4, 0.65), (40, 200, 84, '#d9a23c', 0.2, 0.45)]
    for u0, u1, w, col, s, t in secs:
        A('M' + 'L'.join(p(*R(u, v)) for u, v in [(u0, -w), (u1, -w), (u1, w), (u0, w)]) + 'Z', col, INK, R(u0, 0), s, t, 'x')
        A('M' + 'L'.join(p(*R(u, v)) for u, v in [(u1 - 22, -w - 8), (u1, -w - 8), (u1, w + 8), (u1 - 22, w + 8)]) + 'Z', '#b8862e', INK * 0.8, R(u0, 0), s, t, 'x')
    A(ellipse(*R(470, 0), 30, 64, -8), '#2DFFF4', INK, R(470, 0), 0.8, 0.92)
    A(ellipse(*R(462, -24), 8, 16, -8), '#ffffff', INK * 0.4, R(462, -24), 0.88, 1.0)
    return items


def tele_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    kw = {}
    if t >= 0.08:
        kw = {'fill_over': {'f256': 'M0 0Z'}, 'ink_over': {i: 'M0 0Z' for i in m.own_ink('f256')}}
    im = m.compose(front='<g/>', **kw)
    im.alpha_composite(m.svg(g.sprite_svg(telescope_items(), t)))
    return im


def tele_main() -> None:
    out = OUT.parent / 'telescope'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [tele_frame(t) for t in frames]
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


if __name__ == '__main__' and 'telescope' in __import__('sys').argv[1:]:
    tele_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    op = ROOT / 'art/golden-pyramid-with-tunnel-celebration/objects.json'
    O = _j.loads(op.read_text())
    objs = O['objects'] if 'objects' in O else O
    objs['lavender-snout']['label'] = 'The cream snout creature, left: a pink snout with a straw in its nostril and a sleepy yellow eye'
    objs['lavender-snout']['parts'] = {'body': ['f250'], 'snout': ['f252'], 'eye': ['f256']}
    op.write_text(_j.dumps(O, indent=2) + '\n')
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'leslie-mic-distance':
            b['label'] = 'The snout creature: drag for the Leslie mic distance; its eye opens and a telescope slides out of it'
            b['effects'] = [{'effect': 'vanish', 'parts': ['eye'], 'span': [0.0, 0.15]},
                            {'effect': 'sprites', 'place': 'over', 'items': telescope_items()}]
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', len(telescope_items()), 'shapes')
