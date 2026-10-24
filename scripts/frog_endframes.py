# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (complex tonewheels on) for the acorn frog: the pale yellow body with a little blue head and two
acorns on its back.

    uv run scripts/frog_endframes.py
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
m.CROP = (2950, 1350, 1100, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-complex/endframes'
p, outlined, circle, ellipse, tube, bez, crescent, comp = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.crescent, g.comp
INK = 14
YEL, HEAD, NUT, CAP, PINK = '#F8FF8F', '#7DB3DB', '#E4DE75', '#A4763E', '#FF7580'
LEAF = '#7fd36b'
BODY = ['f206', 'f207', 'f201']
ACORNS = ['f212', 'f214', 'f211', 'f213']
TOPS = [(3490.0, 1838.0), (3705.0, 2005.0)]  # the acorn caps' tops
NUTS = [(3486.0, 1960.0, 80.0), (3703.0, 2150.0, 95.0)]  # nut centres and half widths


ACORN_CENTRES = [(3488.0, 1925.0, 100.0), (3705.0, 2107.0, 112.0)]  # centre and rough radius of each acorn


def hidden_acorns() -> dict:
    """The acorns taken out of the painting (fills and their own ink), for the versions that morph them."""
    return {'fill_over': {f: 'M0 0Z' for f in ACORNS},
            'ink_over': {i: 'M0 0Z' for i, q in m.IP.items() if inside(q['bbox'])}}


def inside(b, box=(3370, 1805, 3870, 2270)) -> bool:
    x, y, w, h = b
    return x >= box[0] and y >= box[1] and x + w <= box[2] and y + h <= box[3]


def draw(front: str, hide: bool = True, again: list[str] | None = None) -> Image.Image:
    kw = hidden_acorns() if hide else {}
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        return m.compose(front=front or '<g/>', **kw)
    finally:
        m.FRONT, m.FRONT_INK = [], []


def blob(cx, cy, r, seed, lumps=7, amt=0.08) -> str:
    """A lumpy round shape, the painting's hand-drawn kind of circle."""
    rnd = random.Random(seed)
    ph = [rnd.random() * 6.28 for _ in range(3)]
    pts = []
    for i in range(48):
        t = i / 48 * 2 * math.pi
        rr = r * (1 + amt * math.sin(lumps * t + ph[0]) + amt * 0.5 * math.sin(3 * t + ph[1]))
        pts.append((cx + math.cos(t) * rr, cy + math.sin(t) * rr))
    return m.smooth(pts + pts[:1]) if hasattr(m, 'smooth') else 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def poly(pts) -> str:
    return 'M' + 'L'.join(p(*q) for q in pts) + 'Z'


def flower(cx, cy, r, petal, centre) -> str:
    out = ''
    for j in range(6):
        a = math.radians(j * 60 - 90)
        out += outlined(ellipse(cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62, r * 0.45, r * 0.3, j * 60 - 90), petal, INK)
    return out + outlined(circle(cx, cy, r * 0.34), centre, INK)


def v1_balloon_cactus() -> Image.Image:
    """Balloon cactus: each acorn swells into a bulbous blue-green cactus of stacked balloon pads, pale ribs down
    each pad and a big candy flower on top."""
    out = ''
    for k, (x, y, r) in enumerate(ACORN_CENTRES):
        pads = [(x, y + r * 0.3, r * 1.35), (x + r * 0.35 * (1 - 2 * k), y - r * 1.15, r * 1.0), (x - r * 0.1, y - r * 2.15, r * 0.7)]
        cols = ['#5cc9c0', '#6fd6b8', '#7fe0c8']
        for j, (px, py, pr) in enumerate(pads):
            out += outlined(blob(px, py, pr, 10 * k + j), cols[j], INK * 1.1)
            for dx in (-0.45, 0.0, 0.45):
                out += outlined(ellipse(px + dx * pr, py + pr * 0.05, pr * 0.1, pr * 0.62), '#c9f5e6', INK * 0.6)
        fx, fy, fr = pads[-1][0], pads[-1][1] - pads[-1][2] * 0.85, 95
        out += flower(fx, fy, fr, ['#f64c76', '#ff9fc4'][k], '#ffe066')
    return draw(out)


def drip(x, y, w, L) -> str:
    return tube([(x, y), (x + 4, y + L * 0.5), (x, y + L)], w, w * 1.15)


def v2_graffiti_eyes() -> Image.Image:
    """Graffiti eyeballs: the acorns pop into two big spray-painted eyeballs with a bright drop shadow, candy irises,
    and white paint dripping down off them."""
    out = ''
    for k, (x, y, r) in enumerate(ACORN_CENTRES):
        R = r * 1.3
        out += outlined(blob(x + 26, y + 26, R, 30 + k, 5, 0.05), ['#b44cff', '#ff5ced'][k], INK * 1.3)
        for j, (dx, L) in enumerate([(-0.45, 150), (0.05, 230), (0.5, 120)]):
            out += outlined(drip(x + dx * R, y + R * 0.75, 26 - 4 * j, L), '#ffffff', INK)
        out += outlined(blob(x, y, R, 20 + k, 5, 0.05), '#ffffff', INK * 1.6)
        look = (-0.18 * R, 0.05 * R) if k == 0 else (-0.22 * R, -0.12 * R)
        ix, iy = x + look[0], y + look[1]
        out += outlined(circle(ix, iy, R * 0.52), ['#2DFFF4', '#ffe066'][k], INK * 1.2)
        out += f'<path d="{circle(ix, iy, R * 0.26)}" fill="#000"/>'
        out += outlined(ellipse(ix + R * 0.18, iy - R * 0.2, R * 0.13, R * 0.09, -30), '#ffffff', INK * 0.6)
    return draw(out)


def v3_party_balloons() -> Image.Image:
    """Party balloons: the acorns float up off its back as two big shiny balloons on curling ribbons tied to it."""
    out = ''
    for k, (x, y, r) in enumerate(ACORN_CENTRES):
        bx, by = x + (-60 if k == 0 else 70), y - 240 - 40 * k
        rx, ry = 135, 165
        ribbon = bez((x, y + 40), (x + 50 * (1 - 2 * k), y - 20), (bx - 40 * (1 - 2 * k), by + ry + 80), (bx, by + ry + 25), 24)
        out += outlined(tube(ribbon, 11, 11), ['#ffe066', '#2DFFF4'][k], INK * 0.8)
        out += outlined(poly([(bx, by + ry - 10), (bx - 30, by + ry + 35), (bx + 30, by + ry + 35)]), ['#f64c76', '#c4a3f0'][k], INK)
        out += outlined(ellipse(bx, by, rx, ry), ['#f64c76', '#c4a3f0'][k], INK * 1.2)
        out += outlined(ellipse(bx - rx * 0.4, by - ry * 0.4, rx * 0.2, ry * 0.3, 25), '#ffffff', INK * 0.6)
    return draw(out)


def v4_big_croak() -> Image.Image:
    """Big croak: a huge pink throat sac balloons out under the little blue head, its eye pops wide open, and fat
    sound rings roll out to the left."""
    out = outlined(blob(3150, 2255, 140, 7, 4, 0.04), '#ff9fc4', INK * 1.2)
    out += outlined(ellipse(3095, 2195, 48, 28, -35), '#ffffff', INK * 0.6)
    over = outlined(circle(3290, 2110, 58), '#ffffff', INK) + f'<path d="{circle(3278, 2116, 26)}" fill="#000"/>'
    over += f'<path d="{circle(3295, 2098, 9)}" fill="#fff"/>'
    for k in range(3):
        over += outlined(crescent(3150, 2255, 200 + 70 * k, 125, 235, 46 - 6 * k), ['#ffffff', '#ffe066', '#2DFFF4'][k], INK)
    return draw(out, hide=False, again=[], ) if False else _croak(out, over)


def _croak(out, over) -> Image.Image:
    im = draw(out, hide=False, again=['f201'])
    im.alpha_composite(m.svg(over))
    return im


def v5_frog_face() -> Image.Image:
    """Frog face: the two acorns become a pair of huge bulging frog eyes on top of the body, and a wide grin opens
    across its front with pink cheeks."""
    out = ''
    mouth = (f'M{p(3300, 2150)}C{p(3400, 2245)} {p(3560, 2255)} {p(3660, 2205)}'
             f'C{p(3600, 2300)} {p(3400, 2310)} {p(3300, 2150)}Z')
    out += outlined(mouth, '#c2185b', INK * 1.2)
    out += outlined(ellipse(3480, 2262, 70, 22, 4), '#ff7fa8', INK * 0.8)
    for x, y, r in ACORN_CENTRES:
        out += outlined(blob(x, y, r * 1.4, int(x), 5, 0.04), YEL, INK * 1.2)
        out += outlined(circle(x, y - 5, r * 0.98), '#ffffff', INK)
        out += f'<path d="{ellipse(x, y, r * 0.58, r * 0.3)}" fill="#000"/>'
        out += outlined(ellipse(x + r * 0.32, y - r * 0.38, r * 0.17, r * 0.12, -25), '#ffffff', INK * 0.5)
        out += outlined(f'M{p(x - r * 1.05, y - r * 0.35)}C{p(x - r * 0.6, y - r * 1.25)} {p(x + r * 0.6, y - r * 1.25)} {p(x + r * 1.05, y - r * 0.35)}C{p(x + r * 0.5, y - r * 0.75)} {p(x - r * 0.5, y - r * 0.75)} {p(x - r * 1.05, y - r * 0.35)}Z', '#c8e85a', INK)
    out += outlined(circle(3330, 2235, 48), '#ff9fc4', INK * 0.8)
    return draw(out)


VERSIONS = [
    ('1-balloon-cactus', 'Balloon cactus', v1_balloon_cactus),
    ('2-graffiti-eyes', 'Graffiti eyeballs', v2_graffiti_eyes),
    ('3-party-balloons', 'Party balloons', v3_party_balloons),
    ('4-big-croak', 'Big croak', v4_big_croak),
    ('5-frog-face', 'Frog face', v5_frog_face),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (pure)', m.compose())]
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


# ---- chosen: graffiti eyeballs ------------------------------------------------------------------------------------
# One sprite list drives the mockup and the app. Timeline (tap: complex on, glided): the acorns fade (0..0.2), the
# white eyeballs pop up where they sat (0.1..0.5), the drop shadows land behind them (0.15..0.55), irises and pupils
# open (0.3..0.7), the shines catch (0.5..0.75), and the white paint drips run down last (0.55..0.95).
def eyes_items() -> list[dict]:
    items = []
    R2 = lambda x, y: [round(x, 1), round(y, 1)]
    for k, (x, y, r) in enumerate(ACORN_CENTRES):
        o = 0.08 * k
        R = r * 1.3
        A = lambda d, f, e, at, s, t, grow='scale': items.append({'d': d, 'fill': f, 'edge': round(e, 1), 'at': at, 'start': round(s + o, 3), 'end': round(t + o, 3), 'grow': grow})
        A(blob(x + 26, y + 26, R, 30 + k, 5, 0.05), ['#b44cff', '#ff5ced'][k], INK * 1.3, R2(x + 26, y + 26), 0.15, 0.55)
        for j, (dx, L) in enumerate([(-0.45, 150), (0.05, 230), (0.5, 120)]):
            top = (x + dx * R, y + R * 0.75)
            A(drip(*top, 26 - 4 * j, L), '#ffffff', INK, R2(*top), 0.55 + 0.05 * j, 0.85 + 0.05 * j, 'y')
        A(blob(x, y, R, 20 + k, 5, 0.05), '#ffffff', INK * 1.6, R2(x, y), 0.1, 0.5)
        look = (-0.18 * R, 0.05 * R) if k == 0 else (-0.22 * R, -0.12 * R)
        ix, iy = x + look[0], y + look[1]
        A(circle(ix, iy, R * 0.52), ['#2DFFF4', '#ffe066'][k], INK * 1.2, R2(ix, iy), 0.3, 0.65)
        A(circle(ix, iy, R * 0.26), '#000000', 0, R2(ix, iy), 0.35, 0.7)
        A(ellipse(ix + R * 0.18, iy - R * 0.2, R * 0.13, R * 0.09, -30), '#ffffff', INK * 0.6, R2(ix + R * 0.18, iy - R * 0.2), 0.5, 0.75)
    return items


def eyes_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    return draw(g.sprite_svg(eyes_items(), t), hide=t >= 0.1)


def eyes_main() -> None:
    out = OUT.parent / 'graffiti-eyes'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [eyes_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
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
    print('wrote', out)


if __name__ == '__main__' and 'eyes' in __import__('sys').argv[1:]:
    eyes_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    op = ROOT / 'art/golden-pyramid-with-tunnel-celebration/objects.json'
    O = _j.loads(op.read_text())
    objs = O['objects'] if 'objects' in O else O
    objs['acorn-frog']['label'] = 'The frog body under the acorns, with its two acorns'
    objs['acorn-frog']['parts']['acorns'] = ACORNS
    op.write_text(_j.dumps(O, indent=2) + '\n')
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'tg-complex':
            b['label'] = 'The acorn frog: tap for complex or pure tonewheels; complex turns its acorns into two graffiti eyeballs'
            b['glide'] = 800
            b['effects'] = [{'effect': 'vanish', 'parts': ['acorns'], 'span': [0.0, 0.2]},
                            {'effect': 'sprites', 'place': 'over', 'items': eyes_items()}]
        if b['id'] == 'note-57':
            b['part'] = 'f216'
        if b['id'] == 'note-60':
            b['part'] = 'f217'
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', len(eyes_items()), 'shapes')
