# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (key click at its loudest) for the lying creature: the big grey creature lying across the bottom,
its blue mitten arm raised, a closed peach slit eye, two little ears and a lime tongue (its far end is the eye that
boings for percussion).

    uv run scripts/lying_endframes.py
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
m.CROP = (1350, 3350, 1400, 1200)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-click/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
GREY, BLUE, PEACH, LIME = '#D2D3D4', '#7BB7F3', '#ECC7B0', '#8ef05a'
HAND = (1720.0, 3770.0)
HEAD_FRONT = (2400.0, 3930.0)
SLIT = (2100.0, 3930.0)


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


def wedge(x, y, ang, r0, r1, w) -> str:
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa * w, ca * w
    return (f'M{p(x + ca * r0, y + sa * r0)}L{p(x + ca * r1 + nx, y + sa * r1 + ny)}'
            f'C{p(x + ca * (r1 + w), y + sa * (r1 + w))} {p(x + ca * (r1 + w), y + sa * (r1 + w))} {p(x + ca * r1 - nx, y + sa * r1 - ny)}Z')


def burst(x, y, angs, r0=150, r1=260, w=26, col='#ffe066') -> str:
    return ''.join(outlined(wedge(x, y, a, r0, r1, w), col, INK) for a in angs)


def v1_crab_claw() -> Image.Image:
    """Crab claw: its mitten hand turns into a big red crab pincer, snapping shut with a burst of clicks."""
    x, y = HAND
    a = math.radians(-130)
    ca, sa = math.cos(a), math.sin(a)
    k = 1.35
    R = lambda u, v: (x + ca * u * k - sa * v * k, y + sa * u * k + ca * v * k)
    upper = f'M{p(*R(-60, -70))}C{p(*R(80, -200))} {p(*R(250, -190))} {p(*R(300, -60))}C{p(*R(230, -50))} {p(*R(120, -50))} {p(*R(40, 0))}Z'
    lower = f'M{p(*R(-60, 60))}C{p(*R(60, 150))} {p(*R(200, 150))} {p(*R(250, 70))}C{p(*R(170, 30))} {p(*R(90, 30))} {p(*R(30, 10))}Z'
    out = outlined(lower, '#ff5a4a', INK) + outlined(upper, '#ff5a4a', INK)
    out += outlined(ellipse(x, y, 150, 130, -130), "#ff5a4a", INK)
    tip = R(290, 5)
    out += burst(*tip, [-200, -160, -120, -80], 80, 190, 24)
    return draw(out, [], '')


def v2_castanets() -> Image.Image:
    """Castanet jaws: its head opens a big clacking mouth at the front, rows of white teeth, the slit eye pops open."""
    x, y = HEAD_FRONT
    top = f'M{p(x - 230, y + 10)}C{p(x - 120, y - 40)} {p(x + 40, y - 150)} {p(x + 150, y - 140)}L{p(x + 160, y - 60)}C{p(x + 40, y - 40)} {p(x - 100, y + 20)} {p(x - 230, y + 30)}Z'
    mouth = f'M{p(x - 230, y + 20)}C{p(x - 80, y - 40)} {p(x + 120, y - 90)} {p(x + 160, y - 60)}C{p(x + 170, y + 40)} {p(x + 120, y + 130)} {p(x + 60, y + 170)}C{p(x - 40, y + 140)} {p(x - 160, y + 70)} {p(x - 230, y + 20)}Z'
    out = outlined(mouth, '#9b1f4b', INK)
    for k in range(4):
        u = 0.18 + k * 0.2
        tx, ty = x - 230 + u * 390, y + 20 - math.sin(u * 2.4) * 85
        out += outlined(f'M{p(tx - 32, ty - 8)}L{p(tx + 32, ty - 18)}L{p(tx + 28, ty + 52)}C{p(tx + 15, ty + 70)} {p(tx - 15, ty + 72)} {p(tx - 26, ty + 56)}Z', '#ffffff', INK * 0.9)
    for k in range(3):
        u = 0.3 + k * 0.22
        tx, ty = x - 160 + u * 280, y + 60 + u * 80
        out += outlined(f'M{p(tx - 30, ty + 10)}L{p(tx + 30, ty)}L{p(tx + 24, ty - 58)}C{p(tx + 10, ty - 74)} {p(tx - 14, ty - 72)} {p(tx - 26, ty - 56)}Z', '#ffffff', INK * 0.9)
    out += outlined(f'M{p(x + 70, y + 60)}C{p(x + 120, y + 40)} {p(x + 160, y + 120)} {p(x + 110, y + 150)}C{p(x + 70, y + 160)} {p(x + 40, y + 110)} {p(x + 70, y + 60)}Z', '#ff7fa8', INK * 0.9)
    sx, sy = SLIT
    out += outlined(ellipse(sx, sy, 92, 62, -12), '#ffffff', INK) + f'<path d="{circle(sx + 18, sy + 6, 30)}" fill="#000"/>'
    out += burst(x + 120, y - 20, [-60, -25, 10, 45], 110, 210, 22)
    return draw('', [], out)


def v3_keyboard() -> Image.Image:
    """Organ keys: its long grey body grows a manual of organ keys along it, white keys and black, one pressed down."""
    x0, y0, ang = 1560.0, 4300.0, -14
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x0 + ca * u - sa * v, y0 + sa * u + ca * v)
    out = outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(-20, -30), (600, -30), (600, 30), (-20, 30)]) + 'Z', '#3b3b5c', INK)
    W = 72
    for k in range(8):
        dv = 18 if k == 5 else 0
        out += outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(k * W, -200 + dv), (k * W + W, -200 + dv), (k * W + W, 0 + dv), (k * W, 0 + dv)]) + 'Z',
                        '#fffbe8' if k != 5 else '#ffe066', INK)
    for k in (1, 2, 4, 5, 6):
        u = k * W - 22
        out += outlined('M' + 'L'.join(p(*R(uu, v)) for uu, v in [(u, -200), (u + 44, -200), (u + 44, -80), (u, -80)]) + 'Z', '#20202e', INK * 0.8)
    out += burst(*R(5.5 * W, -210), [-150, -115, -80, -45], 60, 150, 20)
    return draw('', [], out)


def v4_woodpecker() -> Image.Image:
    """Woodpecker: its head grows a long yellow woodpecker beak and a red crest, its eye pops open, pecking with a
    burst of clicks."""
    x, y = HEAD_FRONT
    beak = f'M{p(x - 30, y - 70)}C{p(x + 100, y - 60)} {p(x + 230, y - 10)} {p(x + 300, y + 20)}C{p(x + 220, y + 40)} {p(x + 100, y + 70)} {p(x - 30, y + 60)}Z'
    out = outlined(beak, '#ffd23f', INK * 1.1)
    out += outlined(f'M{p(x - 20, y - 5)}C{p(x + 100, y + 5)} {p(x + 200, y + 15)} {p(x + 290, y + 20)}C{p(x + 200, y + 25)} {p(x + 100, y + 20)} {p(x - 20, y + 10)}Z', '#e0a000', INK * 0.5)
    for k, (cx, cy, ang, L) in enumerate([(2160, 3800, -110, 190), (2220, 3800, -80, 220), (2280, 3815, -55, 180)]):
        a = math.radians(ang)
        P = [(cx, cy), (cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5), (cx + math.cos(a) * L, cy + math.sin(a) * L)]
        out += outlined(tube(P, 46, 30), ['#f64c4c', '#ff2a4a', '#f64c76'][k], INK)
    sx, sy = SLIT
    out += outlined(circle(sx, sy, 62), '#ffffff', INK) + f'<path d="{circle(sx + 14, sy + 4, 28)}" fill="#000"/>'
    out += burst(x + 300, y + 20, [-50, -10, 30, 70], 70, 170, 22)
    return draw('', [], out)


def v5_snap() -> Image.Image:
    """Finger snap: its mitten hand opens into a big hand snapping its fingers, a burst of clicks flashing out."""
    x, y = HAND
    out = ''
    for ang, L, wdt in [(-175, 230, 38), (-145, 280, 40), (-112, 200, 38), (-85, 170, 36)]:
        a = math.radians(ang)
        out += outlined(tube([(x + math.cos(a) * 60, y + math.sin(a) * 60), (x + math.cos(a) * L, y + math.sin(a) * L)], wdt, wdt * 0.9), BLUE, INK)
    out += outlined(ellipse(x, y, 135, 120, -30), BLUE, INK)
    thumb = tube(bez((x + 70, y - 30), (x + 140, y - 140), (x + 60, y - 250), (x - 40, y - 270), 16), 42, 36)
    out += outlined(thumb, BLUE, INK)
    out += burst(x - 60, y - 290, [-170, -130, -90, -50, -10], 80, 200, 26)
    return draw(out, [], '')


VERSIONS = [
    ('1-crab-claw', 'Crab claw', v1_crab_claw),
    ('2-castanet-jaws', 'Castanet jaws', v2_castanets),
    ('3-organ-keys', 'Organ keys', v3_keyboard),
    ('4-woodpecker', 'Woodpecker', v4_woodpecker),
    ('5-finger-snap', 'Finger snap', v5_snap),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (no click)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.36
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
