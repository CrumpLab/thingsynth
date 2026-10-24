# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (percussion harmonic: Third) for the big eye: the round orange-magenta eye of the lavender,
triangle-headed creature at the painting's right edge.

    uv run scripts/bigeye_endframes.py
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
m.CROP = (3800, 2450, 850, 800)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/perc-harmonic/endframes'
p, outlined, circle, ellipse, tube, bez, spiral = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.spiral
INK = 16
EYE = (4415.0, 2972.0, 128.0)  # the eye socket: centre and radius
HEAD = ['f176', 'f177', 'f178', 'f239']
LAV, MAG, ORANGE, YEL = '#ECA6FF', '#ff14c8', '#ffb347', '#F4FF0B'


def draw(front: str, again: list[str] | None = None, over: str = '') -> Image.Image:
    m.FRONT = again or []
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def in_socket(body: str, cid='sock') -> str:
    x, y, r = EYE
    return (f'<defs><clipPath id="{cid}"><path d="{circle(x, y, r)}"/></clipPath></defs><g clip-path="url(#{cid})">{body}</g>'
            f'<path d="{circle(x, y, r)}" fill="none" stroke="#000" stroke-width="{INK}"/>')


def v1_hypno() -> Image.Image:
    """Hypno eye: the eye turns into a big candy spiral winding into a yellow pupil."""
    x, y, r = EYE
    body = f'<path d="{circle(x, y, r)}" fill="{YEL}"/>'
    T = 2.2 * 2 * math.pi
    P = [(x + math.cos(t) * r * 1.05 * (1 - t / T * 0.85), y + math.sin(t) * r * 1.05 * (1 - t / T * 0.85)) for t in [T * i / 200 for i in range(201)]]
    body += outlined(tube(P, 22, 9), MAG, INK * 0.8)
    body += outlined(circle(x, y, 26), '#000', 1)
    return draw('', [], in_socket(body))


def v2_planet() -> Image.Image:
    """Ringed planet: the eyeball becomes a banded candy planet with a tilted ring sweeping round it."""
    x, y, r = EYE
    rot = -18
    ring = (f'<path d="{ellipse(x, y, r * 2.0, r * 0.5, rot)}{ellipse(x, y, r * 1.55, r * 0.32, rot)}" fill="#7ff2e0" fill-rule="evenodd" '
            f'stroke="#000" stroke-width="{INK}"/>')
    bands = f'<path d="{circle(x, y, r)}" fill="{ORANGE}"/>'
    for k, col in enumerate([MAG, '#ffe066', '#c4a3f0', MAG]):
        yy = y - r + (k + 0.6) * r * 0.5
        bands += outlined(f'M{p(x - r * 1.2, yy)}C{p(x - r * 0.4, yy - 30)} {p(x + r * 0.4, yy + 30)} {p(x + r * 1.2, yy)}L{p(x + r * 1.2, yy + 34)}C{p(x + r * 0.4, yy + 64)} {p(x - r * 0.4, yy + 4)} {p(x - r * 1.2, yy + 34)}Z', col, INK * 0.7)
    a = math.radians(rot)
    # the ring's front half: below the tilted line through the centre
    big = r * 3
    half = (f'M{p(x - math.cos(a) * big, y - math.sin(a) * big)}L{p(x + math.cos(a) * big, y + math.sin(a) * big)}'
            f'L{p(x + math.cos(a) * big - math.sin(a) * big, y + math.sin(a) * big + math.cos(a) * big)}'
            f'L{p(x - math.cos(a) * big - math.sin(a) * big, y - math.sin(a) * big + math.cos(a) * big)}Z')
    over = ring + in_socket(bands, 'pl') + f'<defs><clipPath id="front"><path d="{half}"/></clipPath></defs><g clip-path="url(#front)">{ring}</g>'
    return draw('', [], over)


def eye(x, y, r) -> str:
    """An eye the painting's way: lavender lid round it, an orange-to-magenta eyeball, a yellow pupil."""
    out = outlined(circle(x, y, r * 1.18), LAV, INK)
    out += outlined(circle(x, y, r), ORANGE, INK)
    out += outlined(f'M{p(x, y - r)}A{r:.1f} {r:.1f} 0 0 1 {p(x, y + r)}C{p(x - r * 0.3, y + r * 0.3)} {p(x + r * 0.2, y - r * 0.3)} {p(x, y - r)}Z', MAG, INK * 0.6)
    out += outlined(circle(x + r * 0.45, y + r * 0.1, r * 0.17), YEL, INK * 0.8)
    return out


def v3_three_eyes() -> Image.Image:
    """Three eyes: for the Third, two more eyes as big as its own bulge open on its head."""
    return draw('', [], eye(4300, 2770, 92) + eye(4215, 2960, 84))


def v4_disco() -> Image.Image:
    """Disco ball: the eye turns into a mirrored disco ball of lilac and silver tiles, throwing big sparkles."""
    x, y, r = EYE
    body = f'<path d="{circle(x, y, r)}" fill="#d9d4ee"/>'
    rnd = random.Random(4)
    step = 52
    for i in range(-3, 3):
        for j in range(-3, 3):
            tx, ty = x + i * step, y + j * step
            col = rnd.choice(['#ffffff', '#c9c3ea', '#a79fd8', '#f0d6ff', '#8fe9ff'])
            body += outlined(f'M{p(tx + 4, ty + 4)}L{p(tx + step - 4, ty + 4)}L{p(tx + step - 4, ty + step - 4)}L{p(tx + 4, ty + step - 4)}Z', col, INK * 0.5)
    over = in_socket(body)
    for sx, sy, s in [(4220, 2760, 70), (4560, 2750, 55), (4170, 3080, 50), (4300, 2640, 45)]:
        pts = []
        for k in range(8):
            a = math.radians(-90 + k * 45)
            rr = s if k % 2 == 0 else s * 0.28
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        over += outlined('M' + 'L'.join(p(*q) for q in pts) + 'Z', '#ffffff', INK * 0.8)
    return draw('', [], over)


def v5_peacock() -> Image.Image:
    """Peacock fan: a fan of big peacock feathers opens up behind the creature's head, each with its own eye spot."""
    cx, cy = 4380.0, 2930.0
    out = ''
    for k, ang in enumerate(range(-175, -55, 20)):
        a = math.radians(ang)
        L, W = 470, 120
        tx, ty = cx + math.cos(a) * L, cy + math.sin(a) * L
        nx, ny = -math.sin(a) * W, math.cos(a) * W
        bx, by = cx + math.cos(a) * 120, cy + math.sin(a) * 120
        feather = (f'M{p(bx, by)}C{p(bx + nx * 0.4, by + ny * 0.4)} {p(tx + nx, ty + ny)} {p(tx + math.cos(a) * 60, ty + math.sin(a) * 60)}'
                   f'C{p(tx - nx, ty - ny)} {p(bx - nx * 0.4, by - ny * 0.4)} {p(bx, by)}Z')
        out += outlined(feather, ['#3fbf8f', '#2ab3a6'][k % 2], INK)
        ex, ey = cx + math.cos(a) * (L - 40), cy + math.sin(a) * (L - 40)
        out += outlined(ellipse(ex, ey, 66, 54, ang), '#ffd23f', INK * 0.8)
        out += outlined(ellipse(ex, ey, 46, 38, ang), '#1f7ae0', INK * 0.8)
        out += outlined(ellipse(ex, ey, 24, 20, ang), '#5b2a86', INK * 0.6)
    return draw(out, HEAD)


VERSIONS = [
    ('1-hypno', 'Hypno eye', v1_hypno),
    ('2-planet', 'Ringed planet', v2_planet),
    ('3-three-eyes', 'Three eyes', v3_three_eyes),
    ('4-disco-ball', 'Disco ball', v4_disco),
    ('5-peacock-fan', 'Peacock fan', v5_peacock),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (Second)', m.compose())]
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
