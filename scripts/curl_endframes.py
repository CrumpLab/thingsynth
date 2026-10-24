# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (rotor speed Fast) for the sleepy green creature whose curled ear is the rotor control.

    uv run scripts/curl_endframes.py

Reuses the layer compositor in pyramid_endframes.py with this object's crop. Writes
docs/objects/curl-rotor/endframes/{0..5}-*.png and sheet.png.
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
m.CROP = (375, 3720, 1525, 860)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/curl-rotor/endframes'
p, outlined = m.p, m.outlined

HEAD = (925.0, 4233.0)
EYE = (927.0, 4222.0)
EAR_L = (612.0, 4396.0)
EAR_R = (1150.0, 4410.0)
CAP_TOP = (1300.0, 4030.0)
INK = 20


def circle(cx, cy, r) -> str:
    return f'M{p(cx - r, cy)}A{r:.1f} {r:.1f} 0 1 1 {p(cx + r, cy)}A{r:.1f} {r:.1f} 0 1 1 {p(cx - r, cy)}Z'


def ellipse(cx, cy, rx, ry, rot=0.0) -> str:
    d = f'M{p(cx - rx, cy)}A{rx:.1f} {ry:.1f} 0 1 1 {p(cx + rx, cy)}A{rx:.1f} {ry:.1f} 0 1 1 {p(cx - rx, cy)}Z'
    return d if not rot else d  # rotation applied by the caller with a transform


def swoosh(cx, cy, r, a0, a1, w, colour='#ffffff') -> str:
    """A motion arc: a crescent from angle a0 to a1 (degrees) round (cx, cy), thickest in the middle, outlined."""
    n = 28
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        th = w * math.sin(math.pi * t) ** 0.9
        outer.append((cx + math.cos(a) * (r + th / 2), cy + math.sin(a) * (r + th / 2)))
        inner.append((cx + math.cos(a) * (r - th / 2), cy + math.sin(a) * (r - th / 2)))
    d = 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'
    return outlined(d, colour, INK * 0.75)


def star(cx, cy, r, colour='#ffe066') -> str:
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return outlined('M' + 'L'.join(p(*q) for q in pts) + 'Z', colour, INK * 0.8)


def wide_eye(cx, cy, look=(0.0, 0.0), scale=1.0) -> str:
    """The sleepy eye redrawn wide awake: a big outlined white with a large pupil and a highlight."""
    rx, ry = 120 * scale, 95 * scale
    return (outlined(ellipse(cx, cy, rx, ry), '#ffffff', INK) +
            f'<path d="{circle(cx + look[0], cy + look[1], 44 * scale)}" fill="#000"/>' +
            f'<path d="{circle(cx + look[0] + 16, cy + look[1] - 16, 13 * scale)}" fill="#fff"/>')


# ---- five ideas -------------------------------------------------------------------------------------------------
def v1_propeller() -> Image.Image:
    """Propeller cap: a propeller sprouts from the top of its striped cap and whirls, motion arcs around the blades;
    the creature wakes up wide-eyed."""
    x, y = CAP_TOP
    stem = f'M{p(x - 16, y + 30)}L{p(x - 12, y - 130)}L{p(x + 12, y - 130)}L{p(x + 16, y + 30)}Z'
    hub_y = y - 150
    blades = (f'<g transform="rotate(-8 {x} {hub_y})">' + outlined(ellipse(x - 150, hub_y, 150, 34), '#ff5e7a', INK) +
              outlined(ellipse(x + 150, hub_y, 150, 34), '#7c4fe8', INK) + '</g>')
    hub = outlined(circle(x, hub_y, 30), '#ffe066', INK)
    arcs = swoosh(x, hub_y, 215, 200, 252, 52) + swoosh(x, hub_y, 215, 18, 70, 52) + swoosh(x, hub_y, 262, 150, 186, 34)
    return m.compose(front=outlined(stem, '#eb9bb2', INK) + arcs + blades + hub + wide_eye(*EYE, look=(0, -20)))


def v2_pinwheel_ear() -> Image.Image:
    """Pinwheel ear: the curled ear opens into a spinning pinwheel of candy petals, swooshes round it."""
    cx, cy = EAR_L
    petals = []
    cols = ['#ebe49b', '#f2a6c6', '#ffe066', '#b4e0a2', '#c4a3f0', '#ffb36b']
    for k in range(6):
        a = math.radians(k * 60 + 15)
        tip = (cx + math.cos(a) * 170, cy + math.sin(a) * 170)
        side = (cx + math.cos(a + 0.9) * 95, cy + math.sin(a + 0.9) * 95)
        d = f'M{p(cx, cy)}Q{p(*side)} {p(*tip)}Q{p(cx + math.cos(a - 0.15) * 60, cy + math.sin(a - 0.15) * 60)} {p(cx, cy)}Z'
        petals.append(outlined(d, cols[k], INK))
    hub = outlined(circle(cx, cy, 26), '#e84f7c', INK)
    arcs = swoosh(cx, cy, 228, -152, -92, 48) + swoosh(cx, cy, 228, 28, 88, 48)
    return m.compose(front=''.join(petals) + hub + arcs)


def v3_dizzy() -> Image.Image:
    """Dizzy: spinning has made it giddy: its eye becomes a spiral, stars and little planets orbit its head on a
    swoosh, and its tongue lolls out further."""
    cx, cy = EYE
    spiral = []
    for i in range(80):
        t = i / 79
        a = t * math.pi * 5.2
        r = 8 + 70 * t
        spiral.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8))
    eye = outlined(ellipse(cx, cy, 110, 86), '#ffffff', INK)
    sp = f'<path d="M{"L".join(p(*q) for q in spiral)}" fill="none" stroke="#000" stroke-width="12" stroke-linecap="round"/>'
    hx, hy = HEAD[0], HEAD[1] - 230
    orbit = swoosh(hx, hy + 60, 260, 195, 345, 44, '#c4a3f0')
    items = star(hx - 230, hy + 20, 46) + star(hx + 20, hy - 70, 38, '#ffb36b') + star(hx + 250, hy + 30, 42, '#f2a6c6')
    items += outlined(circle(hx - 110, hy - 40, 22), '#7fd8f5', INK * 0.8) + outlined(circle(hx + 150, hy - 50, 18), '#b4e0a2', INK * 0.8)
    tx, ty = 880.0, 4400.0
    tongue = f'M{p(tx - 60, ty - 30)}C{p(tx - 70, ty + 90)} {p(tx + 40, ty + 140)} {p(tx + 60, ty + 30)}L{p(tx + 50, ty - 30)}Z'
    return m.compose(front=orbit + items + outlined(tongue, '#f64c76', INK) + eye + sp)


def v4_whirlwind() -> Image.Image:
    """Whirlwind: the lavender ground spins up into a whirlwind wrapped round the creature: outlined bands of wind
    sweep around it, with a few leaves and petals caught up in it; its ears blow back."""
    cx, cy = HEAD[0] + 80, HEAD[1] + 40
    bands = ''
    cols = ['#d6c7ff', '#ffffff', '#c4a3f0', '#e7e0ff']
    for k, (r, a0, a1, w) in enumerate([(330, 160, 330, 70), (430, 190, 350, 60), (270, -20, 120, 56), (490, 10, 140, 50)]):
        bands += swoosh(cx, cy, r, a0, a1, w, cols[k])
    rnd = random.Random(5)
    bits = ''
    for k in range(5):
        a = math.radians(200 + k * 33)
        r = 380 + rnd.random() * 80
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        leaf = f'M{p(x - 34, y)}Q{p(x, y - 30)} {p(x + 34, y)}Q{p(x, y + 30)} {p(x - 34, y)}Z'
        bits += f'<g transform="rotate({rnd.random() * 180:.0f} {x:.0f} {y:.0f})">' + outlined(leaf, ['#b4e0a2', '#f2a6c6', '#ffe066'][k % 3], INK * 0.8) + '</g>'
    return m.compose(front=bands + bits + wide_eye(*EYE, look=(-20, -10), scale=0.95))


def v5_racing() -> Image.Image:
    """Racing: the sleepy creature is suddenly going full speed: wide awake, outlined speed streaks stream back from
    its cap to the right, and round dust puffs kick up behind it."""
    out = ''
    rnd = random.Random(7)
    for k, (y, x0, length, w) in enumerate([(4060, 1430, 300, 46), (4150, 1500, 380, 56), (4245, 1520, 300, 48),
                                            (4330, 1500, 360, 52), (3990, 1330, 220, 36)]):
        x1 = x0 + length
        d = (f'M{p(x0, y - w / 2)}C{p(x0 + length * 0.4, y - w / 2)} {p(x1 - 30, y - w * 0.15)} {p(x1, y)}'
             f'C{p(x1 - 30, y + w * 0.15)} {p(x0 + length * 0.4, y + w / 2)} {p(x0, y + w / 2)}'
             f'C{p(x0 - w * 0.6, y + w / 2)} {p(x0 - w * 0.6, y - w / 2)} {p(x0, y - w / 2)}Z')
        out += outlined(d, ['#ffffff', '#e7e0ff', '#ffffff', '#d6c7ff', '#ffffff'][k], INK * 0.8)
    for k in range(5):
        cx, cy, r = 1460 + k * 85 + rnd.random() * 30, 4470 - rnd.random() * 40, 40 + rnd.random() * 30
        lobes = ''.join(f'<path d="{circle(cx + dx, cy + dy, r * rr)}" fill="#f4efff"/>' for dx, dy, rr in [(-r * 0.6, 8, 0.7), (0, -10, 1), (r * 0.6, 6, 0.75)])
        rings = ''.join(f'<path d="{circle(cx + dx, cy + dy, r * rr)}" fill="none" stroke="#000" stroke-width="{INK * 0.7}"/>' for dx, dy, rr in [(-r * 0.6, 8, 0.7), (0, -10, 1), (r * 0.6, 6, 0.75)])
        out += rings + lobes
    return m.compose(front=out + wide_eye(*EYE, look=(-25, -5)))


VERSIONS = [
    ('1-propeller-cap', 'Propeller cap', v1_propeller),
    ('2-pinwheel-ear', 'Pinwheel ear', v2_pinwheel_ear),
    ('3-dizzy', 'Dizzy', v3_dizzy),
    ('4-whirlwind', 'Whirlwind', v4_whirlwind),
    ('5-racing', 'Racing', v5_racing),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = m.compose()
    before.save(OUT / '0-as-painted.png')
    tiles = [('0  As painted (Stop)', before)]
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
