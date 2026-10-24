# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Leslie mic angle at 180) for the coral tongue: the long salmon band that runs under the acorn frog
and hooks up at the right into a rounded tip.

    uv run scripts/tongue_endframes.py
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
m.CROP = (3300, 1450, 1150, 1000)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/leslie-mic-angle/endframes'
p, outlined, circle, ellipse, tube, bez, spiral = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.spiral
INK = 16
CORAL = '#FF7580'
TONGUE = 'f184'
TIP = (4148.0, 1775.0)
IN_FRONT = ['f209', 'f210', 'f211', 'f212', 'f213', 'f214', 'f215', 'f217', 'f206', 'f201', 'f207']


def draw(front: str = '', again: list[str] | None = None, over: str = '', colour: str | None = None) -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>', fill_colour={TONGUE: colour} if colour else None)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def on_tongue(body: str, cid: str = 'tg') -> str:
    return f'<defs><clipPath id="{cid}"><path d="{m.FILLS[TONGUE]}"/></clipPath></defs><g clip-path="url(#{cid})">{body}</g>'


def v1_candy_cane() -> Image.Image:
    """Candy cane: the coral hook turns into a giant candy cane, wide white stripes wrapping round it."""
    body = ''
    for k in range(-12, 14):
        x0 = 3300 + k * 110
        body += outlined(f'M{p(x0, 2500)}L{p(x0 + 55, 2500)}L{p(x0 + 55 + 700, 1500)}L{p(x0 + 700, 1500)}Z', '#ffffff', INK * 0.8)
    return draw(on_tongue(body), IN_FRONT, colour='#f23a4a')


def v2_snake() -> Image.Image:
    """Snake: the band becomes a long snake, darker diamonds down its back, its tip a snake's head with eyes and a
    forked tongue flicking."""
    body = ''
    for k in range(-10, 12):
        x0 = 3350 + k * 140
        for j in range(-6, 7):
            cx, cy = x0 + j * 70, 2400 - j * 100
            body += outlined(f'M{p(cx, cy - 40)}L{p(cx + 32, cy)}L{p(cx, cy + 40)}L{p(cx - 32, cy)}Z', '#d9475a', INK * 0.5)
    x, y = TIP
    head = f'M{p(x - 90, y + 70)}C{p(x - 130, y - 60)} {p(x - 40, y - 150)} {p(x + 20, y - 150)}C{p(x + 90, y - 150)} {p(x + 130, y - 60)} {p(x + 90, y + 70)}Z'
    over = outlined(head, CORAL, INK)
    for ex in (x - 45, x + 50):
        over += outlined(circle(ex, y - 70, 30), '#fffb8a', INK * 0.8) + f'<path d="{ellipse(ex, y - 70, 7, 22)}" fill="#000"/>'
    fork = f'M{p(x + 5, y - 140)}L{p(x - 5, y - 250)}L{p(x - 50, y - 300)}L{p(x - 10, y - 270)}L{p(x + 10, y - 300)}L{p(x + 20, y - 250)}Z'
    over = outlined(fork, '#e0185b', INK * 0.8) + over
    return draw(on_tongue(body), IN_FRONT, over)


def v3_glove() -> Image.Image:
    """Pointing glove: its tip turns into a big white cartoon glove, index finger pointing the way."""
    x, y = TIP[0], TIP[1] - 60
    out = outlined(f'M{p(x - 85, y + 80)}L{p(x + 85, y + 80)}L{p(x + 80, y + 150)}L{p(x - 80, y + 150)}Z', '#ffffff', INK)
    out += outlined(tube([(x - 30, y - 40), (x - 150, y - 300)], 50, 46), '#ffffff', INK)
    for dx, dy in ((10, -95), (60, -75), (100, -35)):
        out += outlined(ellipse(x + dx, y + dy, 50, 42, 30), '#ffffff', INK)
    out += outlined(tube(bez((x - 80, y + 10), (x - 160, y - 20), (x - 190, y - 80), (x - 170, y - 130), 12), 44, 40), '#ffffff', INK)
    out += outlined(ellipse(x, y, 125, 105), '#ffffff', INK)
    out += outlined(ellipse(x - 5, y - 5, 108, 90), '#ffffff', 0.1)
    for k in range(3):
        out += outlined(f'M{p(x - 30 - 30 * k, y + 20)}C{p(x - 10 - 30 * k, y - 10)} {p(x + 10 - 30 * k, y - 10)} {p(x + 30 - 30 * k, y + 20)}C{p(x + 10 - 30 * k, y + 5)} {p(x - 10 - 30 * k, y + 5)} {p(x - 30 - 30 * k, y + 20)}Z', '#2b2b2b', 1) if False else ''
    return draw(out, [], '')


def v4_curl() -> Image.Image:
    """Rolled up: its tip keeps going and rolls up into a big spiral curl, like a party blower winding in."""
    x, y = TIP
    P = [(x, y + 60)] + spiral(x, y, math.radians(-95), 210, 1.4, 0.85, -1, 50)
    out = outlined(tube(P, 62, 22), CORAL, INK)
    return draw(out, [], '')


def v5_microphone() -> Image.Image:
    """Microphone: its tip holds up a big chrome microphone (the Leslie's own mic), sound waves going into it."""
    x, y = TIP
    a = math.radians(-100)
    hx, hy = x + math.cos(a) * 150, y + math.sin(a) * 150
    out = outlined(tube([(x, y), (hx, hy)], 34, 40), '#3b3b5c', INK)
    out += outlined(circle(hx + math.cos(a) * 90, hy + math.sin(a) * 90, 105), '#d9dbe6', INK * 1.1)
    gx, gy = hx + math.cos(a) * 90, hy + math.sin(a) * 90
    out += outlined(ellipse(gx, gy + 10, 108, 26, -10), '#b8bccc', INK * 0.8)
    for dx, dy in [(-40, -50), (0, -60), (40, -50), (-55, -10), (55, -10)]:
        out += f'<path d="{circle(gx + dx, gy + dy, 11)}" fill="#7a7f94"/>'
    out += outlined(ellipse(gx - 45, gy - 55, 22, 14, -35), '#ffffff', INK * 0.5)
    for k in range(3):
        out += outlined(g.crescent(gx, gy, 150 + 55 * k, 150, 210, 32 - 6 * k), ['#2DFFF4', '#ffe066', '#ff9fc4'][k], INK * 0.8)
    out += outlined(tube([(x - 60, y + 30), (x - 20, y - 60)], 36, 30), CORAL, INK)
    return draw(out, [], '')


VERSIONS = [
    ('1-candy-cane', 'Candy cane', v1_candy_cane),
    ('2-snake', 'Snake', v2_snake),
    ('3-pointing-glove', 'Pointing glove', v3_glove),
    ('4-rolled-up', 'Rolled up', v4_curl),
    ('5-microphone', 'Microphone', v5_microphone),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (0 degrees)', m.compose())]
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
