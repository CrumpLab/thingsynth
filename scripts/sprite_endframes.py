# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (pedal sustain at its longest) for the orange sprite: the orange star-shaped creature with its arms
out, a yellow head with a sleepy cyan eye, sitting on the green bush.

    uv run scripts/sprite_endframes.py
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
m.CROP = (1950, 1350, 1050, 1050)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/pedal-sustain/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
ORANGE, YEL, CYAN, TEAL = '#FF6D2D', '#FFF42D', '#2DFFF4', '#306C69'
SPRITE = ['f221', 'f222', 'f223', 'f224']
HEAD, EYE, BODY = (2450.0, 1790.0), (2420.0, 1830.0), (2450.0, 1985.0)
ARM_L, ARM_R = (2225.0, 1908.0), (2685.0, 1936.0)


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


def sleepy_eye(x, y, r) -> str:
    out = outlined(circle(x, y, r), CYAN, INK)
    out += (f'<defs><clipPath id="se{x:.0f}"><path d="{circle(x, y, r)}"/></clipPath></defs><g clip-path="url(#se{x:.0f})">'
            f'<path d="M{p(x - r * 1.2, y - r * 0.1)}C{p(x - r * 0.4, y - r * 0.35)} {p(x + r * 0.4, y - r * 0.35)} {p(x + r * 1.2, y - r * 0.1)}L{p(x + r * 1.2, y + r * 1.2)}L{p(x - r * 1.2, y + r * 1.2)}Z" '
            f'fill="{TEAL}" stroke="#000" stroke-width="{INK}"/></g>')
    return out + f'<path d="{circle(x, y, r)}" fill="none" stroke="#000" stroke-width="{INK}"/>'


def v1_taffy() -> Image.Image:
    """Taffy arms: its arms stretch out long and droopy like pulled taffy, curling up at the ends into round
    mitten hands."""
    out = ''
    for P in (bez(ARM_L, (2080, 1990), (1990, 1900), (1990, 1740), 30), bez(ARM_R, (2820, 2010), (2920, 1920), (2910, 1760), 30)):
        out += outlined(tube(P, 50, 44), ORANGE, INK)
        out += outlined(circle(*P[-1], 62), ORANGE, INK)
        hx, hy = P[-1]
        out += outlined(ellipse(hx + (-50 if hx < 2450 else 50), hy + 10, 30, 22, 30), ORANGE, INK * 0.9)
        out += f'<path d="{circle(hx, hy, 52)}" fill="{ORANGE}"/>'
    return draw(out, SPRITE)


def v2_jellyfish() -> Image.Image:
    """Jellyfish: its head swells into a big see-through jelly bell and its drips become long wavy tentacles trailing
    down over the bush."""
    x, y = HEAD[0], HEAD[1] + 60
    out = ''
    rnd = random.Random(2)
    for k in range(7):
        x0 = x - 190 + k * 63
        pts = [(x0 + 30 * math.sin(i / 5 + k), y + 60 + i * 26) for i in range(18)]
        out += outlined(tube(pts, 26, 14), ['#ff9f43', '#f64c76', '#ffb3d1'][k % 3], INK * 0.9)
    bell = (f'M{p(x - 250, y + 70)}C{p(x - 260, y - 260)} {p(x + 260, y - 260)} {p(x + 250, y + 70)}'
            + ''.join(f'C{p(x + 250 - 62.5 * i - 15, y + 120)} {p(x + 250 - 62.5 * (i + 1) + 15, y + 120)} {p(x + 250 - 62.5 * (i + 1), y + 70)}' for i in range(8)) + 'Z')
    out += outlined(bell, '#ffb07a', INK * 1.1).replace('fill="#ffb07a"', 'fill="#ffb07a" fill-opacity="0.88"')
    out += outlined(ellipse(x - 120, y - 120, 50, 26, -30), '#ffffff', INK * 0.6)
    out += sleepy_eye(x - 20, y - 40, 62)
    return draw('', [], out)


def v3_wings() -> Image.Image:
    """Butterfly wings: two pairs of big candy butterfly wings open out from behind it, each with an eye spot."""
    bx, by = BODY[0], BODY[1] - 60
    out = ''
    for side in (-1, 1):
        up = (f'M{p(bx, by)}C{p(bx + side * 120, by - 330)} {p(bx + side * 420, by - 330)} {p(bx + side * 380, by - 80)}'
              f'C{p(bx + side * 350, by + 20)} {p(bx + side * 150, by + 30)} {p(bx, by)}Z')
        lo = (f'M{p(bx, by + 20)}C{p(bx + side * 260, by + 30)} {p(bx + side * 330, by + 140)} {p(bx + side * 260, by + 250)}'
              f'C{p(bx + side * 180, by + 330)} {p(bx + side * 60, by + 180)} {p(bx, by + 20)}Z')
        out += outlined(up, '#c4a3f0' if side < 0 else '#ff9fc4', INK) + outlined(lo, '#ffe066', INK)
        out += outlined(circle(bx + side * 270, by - 160, 62), '#f64c76', INK) + outlined(circle(bx + side * 270, by - 160, 30), '#2DFFF4', INK * 0.8)
        out += outlined(circle(bx + side * 200, by + 150, 40), '#ff9f43', INK * 0.8)
    return draw(out, SPRITE)


def v4_starfish() -> Image.Image:
    """Starfish: it grows into a big starfish, five fat rounded arms reaching out, each with a row of bumps."""
    bx, by = BODY
    out = ''
    for ang in (-90, -15, 55, 125, 195):
        a = math.radians(ang)
        P = [(bx + math.cos(a) * L, by + math.sin(a) * L) for L in range(0, 341, 20)]
        out += outlined(tube(P, 95, 40), ORANGE, INK)
        for L in range(140, 321, 55):
            out += outlined(circle(bx + math.cos(a) * L, by + math.sin(a) * L, 22 - L * 0.03), '#ffd0a6', INK * 0.6)
    return draw(out, SPRITE)


def v5_balloon() -> Image.Image:
    """Hot-air balloon: its yellow head inflates into a big striped hot-air balloon, its sleepy eye on the front,
    ropes down to its shoulders."""
    x, y, R = HEAD[0], HEAD[1] - 230, 230
    out = ''
    for sx in (-110, 110):
        out += outlined(tube([(x + sx * 0.9, y + R * 0.8), (x + sx * 0.75, HEAD[1] + 60)], 12, 12), '#a4763e', INK * 0.7)
    out += outlined(f'M{p(x - R, y)}A{R} {R} 0 1 1 {p(x + R, y)}C{p(x + R, y + R * 0.6)} {p(x + 70, y + R * 0.95)} {p(x + 60, y + R * 1.05)}L{p(x - 60, y + R * 1.05)}C{p(x - 70, y + R * 0.95)} {p(x - R, y + R * 0.6)} {p(x - R, y)}Z', YEL, INK * 1.1)
    for k, col in enumerate(['#ff9f43', '#f64c76', '#ff9f43']):
        cx = x + (k - 1) * 150
        out += outlined(f'M{p(cx, y - R * 0.98)}C{p(cx - 55, y - R * 0.4)} {p(cx - 45, y + R * 0.6)} {p(x + (cx - x) * 0.25, y + R * 1.02)}C{p(cx + 45, y + R * 0.6)} {p(cx + 55, y - R * 0.4)} {p(cx, y - R * 0.98)}Z', col, INK * 0.8)
    out += sleepy_eye(x - 30, y + 20, 70)
    return draw(out, ['f221'])


VERSIONS = [
    ('1-taffy-arms', 'Taffy arms', v1_taffy),
    ('2-jellyfish', 'Jellyfish', v2_jellyfish),
    ('3-butterfly-wings', 'Butterfly wings', v3_wings),
    ('4-starfish', 'Starfish', v4_starfish),
    ('5-hot-air-balloon', 'Hot-air balloon', v5_balloon),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (short)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.42
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


# ---- chosen: starfish, then butterfly wings, then jellyfish (4 -> 3 -> 2) -----------------------------------------
# Sustain from short to long morphs it three times: starfish arms grow out of its body (0..0.25) and draw back in
# (0.38..0.5) as butterfly wings open (0.35..0.58); the wings fold away (0.68..0.8) while the sprite itself fades
# (0.66..0.8) and a jellyfish bell swells out of its head (0.68..0.88), its sleepy eye opens on the bell and the
# tentacles drop down over the bush (0.75..1).
def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 3), 'end': round(e, 3), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 3), round(out[1], 3)
    return x


def lidded_eye(x, y, r, at, s, e) -> list[dict]:
    """The sleepy eye as sprites (no clip): cyan ball, a teal lid filling it below a curve, the black ring."""
    lid = (f'M{p(x - r * 0.995, y - r * 0.1)}A{r:.1f} {r:.1f} 0 1 0 {p(x + r * 0.995, y - r * 0.1)}'
           f'C{p(x + r * 0.4, y - r * 0.35)} {p(x - r * 0.4, y - r * 0.35)} {p(x - r * 0.995, y - r * 0.1)}Z')
    return [it(circle(x, y, r), CYAN, INK, at, s, e), it(lid, TEAL, INK, at, s, e), it(circle(x, y, r), 'none', INK, at, s, e)]


def around_items() -> list[dict]:
    """Starfish arms and butterfly wings: behind the sprite, above the bush."""
    bx, by = BODY
    items = []
    for k, ang in enumerate((-90, -15, 55, 125, 195)):
        a = math.radians(ang)
        P = [(bx + math.cos(a) * L, by + math.sin(a) * L) for L in range(0, 341, 20)]
        s = 0.02 + 0.03 * k
        items.append(it(tube(P, 95, 40), ORANGE, INK, BODY, s, s + 0.18, out=(0.38, 0.5)))
        for L in range(140, 321, 55):
            c = (bx + math.cos(a) * L, by + math.sin(a) * L)
            items.append(it(circle(*c, 22 - L * 0.03), '#ffd0a6', INK * 0.6, BODY, s + 0.08, s + 0.2, out=(0.38, 0.5)))
    wx, wy = BODY[0], BODY[1] - 60
    for side in (-1, 1):
        up = (f'M{p(wx, wy)}C{p(wx + side * 120, wy - 330)} {p(wx + side * 420, wy - 330)} {p(wx + side * 380, wy - 80)}'
              f'C{p(wx + side * 350, wy + 20)} {p(wx + side * 150, wy + 30)} {p(wx, wy)}Z')
        lo = (f'M{p(wx, wy + 20)}C{p(wx + side * 260, wy + 30)} {p(wx + side * 330, wy + 140)} {p(wx + side * 260, wy + 250)}'
              f'C{p(wx + side * 180, wy + 330)} {p(wx + side * 60, wy + 180)} {p(wx, wy + 20)}Z')
        o = (0.68, 0.8)
        items += [it(lo, '#ffe066', INK, (wx, wy), 0.35, 0.55, out=o), it(up, '#c4a3f0' if side < 0 else '#ff9fc4', INK, (wx, wy), 0.37, 0.58, out=o),
                  it(circle(wx + side * 270, wy - 160, 62), '#f64c76', INK, (wx, wy), 0.37, 0.58, out=o),
                  it(circle(wx + side * 270, wy - 160, 30), '#2DFFF4', INK * 0.8, (wx, wy), 0.37, 0.58, out=o),
                  it(circle(wx + side * 200, wy + 150, 40), '#ff9f43', INK * 0.8, (wx, wy), 0.35, 0.55, out=o)]
    return items


def jelly_items() -> list[dict]:
    """The jellyfish: above everything."""
    x, y = HEAD[0], HEAD[1] + 60
    items = []
    for k in range(7):
        x0 = x - 190 + k * 63
        pts = [(x0 + 30 * math.sin(i / 5 + k), y + 60 + i * 26) for i in range(18)]
        s = 0.75 + 0.025 * ((k * 3) % 7)
        items.append(it(tube(pts, 26, 14), ['#ff9f43', '#f64c76', '#ffb3d1'][k % 3], INK * 0.9, (x0, y + 60), s, min(1.0, s + 0.18), 'y'))
    bell = (f'M{p(x - 250, y + 70)}C{p(x - 260, y - 260)} {p(x + 260, y - 260)} {p(x + 250, y + 70)}'
            + ''.join(f'C{p(x + 250 - 62.5 * i - 15, y + 120)} {p(x + 250 - 62.5 * (i + 1) + 15, y + 120)} {p(x + 250 - 62.5 * (i + 1), y + 70)}' for i in range(8)) + 'Z')
    items.append(it(bell, '#ffb07a', INK * 1.1, HEAD, 0.68, 0.88))
    items.append(it(ellipse(x - 120, y - 120, 50, 26, -30), '#ffffff', INK * 0.6, HEAD, 0.74, 0.9))
    items += lidded_eye(x - 20, y - 40, 62, (x - 20, y - 40), 0.75, 0.9)
    return items


def morph_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    gone = t >= 0.73  # the sprite's fade (0.66..0.8), shown as gone past its middle
    kw = {}
    if gone:
        kw = {'fill_over': {f: 'M0 0Z' for f in SPRITE}, 'ink_over': {i: 'M0 0Z' for f in SPRITE for i in m.own_ink(f)}}
    m.FRONT = [] if gone else SPRITE
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=g.sprite_svg(around_items(), t) or '<g/>', **kw)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    jel = g.sprite_svg(jelly_items(), t)
    if jel:
        im.alpha_composite(m.svg(jel))
    return im


def morph_main() -> None:
    out = OUT.parent / 'starfish-wings-jellyfish'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.2, 0.4, 0.55, 0.7, 0.85, 1.0]
    tiles = [morph_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
    w, h = tiles[0].size
    sc = 0.26
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * len(frames) + 80, th + 56), 'white')
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.2f}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / 'strip.png')
    print('wrote', out)


if __name__ == '__main__' and 'morph' in __import__('sys').argv[1:]:
    morph_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    op = ROOT / 'art/golden-pyramid-with-tunnel-celebration/objects.json'
    O = _j.loads(op.read_text())
    objs = O['objects'] if 'objects' in O else O
    objs['orange-sprite']['label'] = 'The orange sprite on the bush, with its yellow head and sleepy eye'
    objs['orange-sprite']['parts'] = {'body': ['f221'], 'head': ['f222'], 'eye': ['f223', 'f224']}
    op.write_text(_j.dumps(O, indent=2) + '\n')
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'pedal-sustain':
            b['label'] = 'The orange sprite: drag for Pedal Sustain; it morphs into a starfish, then a butterfly, then a jellyfish'
            b['effects'] = [{'effect': 'sprites', 'place': 'around', 'front': ['f222', 'f223', 'f224'], 'items': around_items()},
                            {'effect': 'vanish', 'span': [0.66, 0.8]},
                            {'effect': 'sprites', 'place': 'over', 'items': jelly_items()}]
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', len(around_items()) + len(jelly_items()), 'shapes')
