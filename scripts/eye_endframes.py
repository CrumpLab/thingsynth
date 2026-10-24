# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (percussion on) for the sleepy round eye at the end of the grey lying creature.

    uv run scripts/eye_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mock', ROOT / 'scripts/pyramid_endframes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cs = importlib.util.spec_from_file_location('curl', ROOT / 'scripts/curl_endframes.py')
c = importlib.util.module_from_spec(cs)
cs.loader.exec_module(c)
m.CROP = (1640, 3880, 1000, 690)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/eye-percussion/endframes'
p, outlined, circle, ellipse, star, swoosh = m.p, m.outlined, c.circle, c.ellipse, c.star, c.swoosh
INK = 18
EYE = (2110.0, 4365.0)
R = 122.0
LID = '#9195B2'
LOWER = '#91ADB2'


def open_eye(cx, cy, r, pupil='#000', iris='#f5d76e', lashes=True, look=(0.0, 0.0)) -> str:
    """The eye wide awake: an outlined white ball, its yellow iris (the painting's own colour) and a dark pupil, the
    purple lid rolled up into a thin crescent at the top, with lashes."""
    out = outlined(circle(cx, cy, r), '#ffffff', INK)
    out += outlined(circle(cx + look[0], cy + 12 + look[1], r * 0.48), iris, INK * 0.8)
    out += f'<path d="{circle(cx + look[0], cy + 12 + look[1], r * 0.22)}" fill="{pupil}"/>'
    out += f'<path d="{circle(cx + look[0] + r * 0.14, cy - r * 0.05 + look[1], r * 0.08)}" fill="#fff"/>'
    lid = (f'M{p(cx - r * 1.02, cy - r * 0.25)}C{p(cx - r * 0.8, cy - r * 1.2)} {p(cx + r * 0.8, cy - r * 1.2)} {p(cx + r * 1.02, cy - r * 0.25)}'
           f'C{p(cx + r * 0.6, cy - r * 0.8)} {p(cx - r * 0.6, cy - r * 0.8)} {p(cx - r * 1.02, cy - r * 0.25)}Z')
    out += outlined(lid, LID, INK)
    if lashes:
        for k in range(-2, 3):
            a = math.radians(-90 + k * 26)
            x1, y1 = cx + math.cos(a) * r * 0.98, cy + math.sin(a) * r * 0.98
            x2, y2 = cx + math.cos(a) * r * 1.38, cy + math.sin(a) * r * 1.38
            w = 9
            nx, ny = -math.sin(a) * w, math.cos(a) * w
            lash = f'M{p(x1 - nx, y1 - ny)}L{p(x2, y2)}L{p(x1 + nx, y1 + ny)}Z'
            out += outlined(lash, '#000', 6)
    return out


def hide_eye():
    ids = ['f019', 'f020', 'f021', 'f022']
    return {'fill_over': {f: 'M0 0Z' for f in ids}, 'ink_over': {i: 'M0 0Z' for f in ids for i in m.own_ink(f)}}


def v1_awake() -> Image.Image:
    """Wide awake: the lid rolls up, the eye pops wide open with lashes, looking up."""
    return m.compose(front=open_eye(*EYE, R * 1.12, look=(0, -14)), **hide_eye())


def v2_boing() -> Image.Image:
    """Boing: the eye springs out on a coiled stalk, wide open, with motion lines behind it."""
    bx, by = EYE
    tx, ty = bx + 120, by - 330
    coil = []
    for i in range(80):
        t = i / 79
        x = bx + (tx - bx) * t + 45 * math.sin(t * math.pi * 8)
        y = by + (ty - by) * t
        coil.append((x, y))
    d = 'M' + 'L'.join(p(*q) for q in coil)
    spring = (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK * 2.2}" stroke-linecap="round" stroke-linejoin="round"/>'
              f'<path d="{d}" fill="none" stroke="{LOWER}" stroke-width="{INK}" stroke-linecap="round" stroke-linejoin="round"/>')
    lines = swoosh(tx, ty, 190, 110, 150, 30) + swoosh(tx, ty, 190, 30, 70, 30)
    return m.compose(front=spring + lines + open_eye(tx, ty, R, look=(10, -6)), **hide_eye())


def v3_sparkle() -> Image.Image:
    """Ding: the eye snaps open and a burst of outlined sparkles and short rays flies out round it."""
    cx, cy = EYE
    out = ''
    for k in range(10):
        a = math.radians(k * 36 + 10)
        r0, r1 = R * 1.5, R * (2.1 if k % 2 else 1.8)
        w = 0.12
        d = (f'M{p(cx + math.cos(a - w) * r0, cy + math.sin(a - w) * r0)}L{p(cx + math.cos(a) * r1, cy + math.sin(a) * r1)}'
             f'L{p(cx + math.cos(a + w) * r0, cy + math.sin(a + w) * r0)}Z')
        out += outlined(d, '#ffe066' if k % 2 else '#ffb36b', INK * 0.7)
    for k, (dx, dy, s, col) in enumerate([(-280, -160, 62, '#f2a6c6'), (280, -130, 56, '#7fd8f5'), (-260, 120, 50, '#b4e0a2'), (290, 130, 56, '#c4a3f0')]):
        out += star(cx + dx, cy + dy, s, col)
    return m.compose(front=out + open_eye(cx, cy, R * 1.05), **hide_eye())


def v4_more_eyes() -> Image.Image:
    """Eyes everywhere: the eye opens and two smaller eyes pop open beside it on the grey creature, all looking the
    same way."""
    cx, cy = EYE
    out = open_eye(cx, cy, R * 1.05, look=(18, -8))
    out += open_eye(cx - 260, cy - 250, R * 0.62, look=(12, -6), lashes=False)
    out += open_eye(cx - 330, cy - 400, R * 0.5, look=(10, -4), lashes=False)
    return m.compose(front=out, **hide_eye())


def v5_star_pupil() -> Image.Image:
    """Starstruck: the eye opens and its pupil becomes a bright outlined star; little hearts pop above it."""
    cx, cy = EYE
    out = open_eye(cx, cy, R * 1.08, pupil='#f5d76e')
    out += star(cx, cy + 12, R * 0.42, '#ffb36b')
    for dx, dy, s in [(-120, -230, 1.0), (40, -280, 0.8), (170, -210, 0.9)]:
        x, y = cx + dx, cy + dy
        h = 34 * s
        heart = (f'M{p(x, y + h)}C{p(x - h * 1.6, y)} {p(x - h, y - h * 1.2)} {p(x, y - h * 0.4)}'
                 f'C{p(x + h, y - h * 1.2)} {p(x + h * 1.6, y)} {p(x, y + h)}Z')
        out += outlined(heart, '#f64c76', INK * 0.7)
    return m.compose(front=out, **hide_eye())


VERSIONS = [
    ('1-wide-awake', 'Wide awake', v1_awake),
    ('2-boing', 'Boing', v2_boing),
    ('3-sparkle', 'Ding sparkle', v3_sparkle),
    ('4-more-eyes', 'More eyes', v4_more_eyes),
    ('5-starstruck', 'Starstruck', v5_star_pupil),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (percussion off)', m.compose())]
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


# ---- chosen: boing ------------------------------------------------------------------------------------------------
GREY = '#D2D3D4'


def clamp01(u):
    return max(0.0, min(1.0, u))


def ease_out(u):
    return 1 - (1 - clamp01(u)) ** 3


def ease_back(u):
    """Out-back: overshoots a little and settles, the spring's boing."""
    u = clamp01(u)
    c1 = 1.9
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


def eye_at(cx, cy, r, o, look=(0.0, 0.0)) -> str:
    """The eye open by o: white ball, iris and pupil, the lid coming down over it from the top (o = 0: half shut, as
    painted; o = 1: rolled up into a thin crescent), lashes once it is open."""
    out = outlined(circle(cx, cy, r), '#ffffff', INK)
    out += outlined(circle(cx + look[0], cy + 12 + look[1], r * 0.48), '#f5d76e', INK * 0.8)
    out += f'<path d="{circle(cx + look[0], cy + 12 + look[1], r * 0.22)}" fill="#000"/>'
    out += f'<path d="{circle(cx + look[0] + r * 0.14, cy - r * 0.05 + look[1], r * 0.08)}" fill="#fff"/>'
    edge = cy + r * (0.05 - 0.75 * o)  # where the lid's lower edge crosses the middle
    lid = (f'<defs><clipPath id="ball{cx:.0f}{cy:.0f}"><path d="{circle(cx, cy, r)}"/></clipPath></defs>'
           f'<g clip-path="url(#ball{cx:.0f}{cy:.0f})"><path d="M{p(cx - r * 1.1, cy - r * 1.2)}L{p(cx + r * 1.1, cy - r * 1.2)}'
           f'L{p(cx + r * 1.1, edge - r * 0.1)}C{p(cx + r * 0.5, edge + r * 0.25)} {p(cx - r * 0.5, edge + r * 0.25)} {p(cx - r * 1.1, edge - r * 0.1)}Z" '
           f'fill="{LID}" stroke="#000" stroke-width="{INK}"/></g>')
    out += lid + f'<path d="{circle(cx, cy, r)}" fill="none" stroke="#000" stroke-width="{INK}"/>'
    if o > 0.7:
        k = (o - 0.7) / 0.3
        for j in range(-2, 3):
            a = math.radians(-90 + j * 26)
            x1, y1 = cx + math.cos(a) * r * 0.98, cy + math.sin(a) * r * 0.98
            x2, y2 = cx + math.cos(a) * r * (1 + 0.38 * k), cy + math.sin(a) * r * (1 + 0.38 * k)
            nx, ny = -math.sin(a) * 9, math.cos(a) * 9
            out += outlined(f'M{p(x1 - nx, y1 - ny)}L{p(x2, y2)}L{p(x1 + nx, y1 + ny)}Z', '#000', 6)
    return out


def boing_frame(t: float) -> Image.Image:
    """Percussion at t: the eye opens in place (0..0.25), springs out on its coil with an overshoot (0.2..0.8), and
    the motion lines flick out last (0.65..1)."""
    if t <= 0:
        return m.compose()
    bx, by = EYE
    tx, ty = bx + 120, by - 330
    o = ease_out(t / 0.25)
    e = ease_back((t - 0.2) / 0.6)
    ex, ey = bx + (tx - bx) * e, by + (ty - by) * e
    out = ''
    # the nub on the creature where the eye sat, and the coil from it to the eye
    nub = outlined(ellipse(bx, by + 2, 108, 126), GREY, INK)  # an empty grey cup over the eye's old footprint
    out += nub
    if e > 0.02:
        coil = []
        turns = 8 * max(0.2, abs(e))
        for i in range(80):
            u = i / 79
            coil.append((bx + (ex - bx) * u + 45 * math.sin(u * math.pi * turns), by + 20 + (ey - by - 20) * u))
        d = 'M' + 'L'.join(p(*q) for q in coil)
        out += (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{INK * 2.2}" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="{d}" fill="none" stroke="{LOWER}" stroke-width="{INK}" stroke-linecap="round" stroke-linejoin="round"/>')
    lg = ease_out((t - 0.65) / 0.35)
    if lg > 0.02:
        out += swoosh(ex, ey, 190, 110, 110 + 40 * lg, 30 * lg) + swoosh(ex, ey, 190, 70 - 40 * lg, 70, 30 * lg)
    out += eye_at(ex, ey, R, o, look=(10 * o, -6 * o))
    return m.compose(front=out, **hide_eye())


def boing_main() -> None:
    out = OUT.parent / 'boing'
    out.mkdir(parents=True, exist_ok=True)
    boing_frame(1.0).save(out / 'end-frame.png')
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [boing_frame(t) for t in frames]
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
    import shutil
    import subprocess
    tmp = out / '_frames'
    tmp.mkdir(exist_ok=True)
    seq = [k / 24 for k in range(25)] + [k / 24 for k in range(23, 0, -1)]
    for i, tt in enumerate(seq):
        boing_frame(tt).convert('RGB').resize((520, round(520 * h / w)), Image.LANCZOS).save(tmp / f'{i:03d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', str(tmp / '%03d.png'), '-vf',
                    'split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0',
                    str(out / 'sweep.gif')], check=True)
    shutil.rmtree(tmp)
    print('wrote', out)


if __name__ == '__main__' and 'boing' in __import__('sys').argv[1:]:
    boing_main()
