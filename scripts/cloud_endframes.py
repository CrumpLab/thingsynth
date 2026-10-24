# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (wheel age at 1) for the big pale cloud behind the pyramid's apex.

    uv run scripts/cloud_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('mock', ROOT / 'scripts/pyramid_endframes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cs = importlib.util.spec_from_file_location('curl', ROOT / 'scripts/curl_endframes.py')
c = importlib.util.module_from_spec(cs)
cs.loader.exec_module(c)
ss = importlib.util.spec_from_file_location('stream', ROOT / 'scripts/stream_endframes.py')
st = importlib.util.module_from_spec(ss)
ss.loader.exec_module(st)
m.CROP = (2250, 380, 1450, 900)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/cloud-age/endframes'
p, outlined, circle, ellipse, star = m.p, m.outlined, c.circle, c.ellipse, c.star
puffs, SCRIB_MASK = st.puffs, st.SCRIB_MASK
INK = 16
CLOUD = 'f193'
CW = '#F8F0FA'  # the cloud as it reads over the wash
FRONT = ['f309', 'f310', 'f311', 'f231', 'f232', 'f233', 'f234', 'f235', 'f135', 'f136', 'f220', 'f192']


def top_edge(x0, x1, n=60):
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', m.FILLS[CLOUD])]
    P = list(zip(nums[0::2], nums[1::2]))
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        near = [q[1] for q in P if abs(q[0] - x) < (x1 - x0) / n]
        if near:
            out.append((x, min(near)))
    return out


def comp(front: str, **kw) -> Image.Image:
    """Compose with the shapes painted in front of the cloud (pyramid, apex creature, ghost) drawn back on top."""
    m.FRONT = FRONT
    m.FRONT_INK = sorted({s for f in FRONT for s in m.own_ink(f)})
    try:
        return m.compose(front=front, rescrib=SCRIB_MASK[0], **kw)
    finally:
        m.FRONT, m.FRONT_INK = [], []


def v1_old_man() -> Image.Image:
    """Old man cloud: wheel age makes the cloud an old fellow: sleepy droopy eyes, bushy brows and a long wispy
    beard of cloud curling down over the pyramid."""
    SCRIB_MASK[0] = ''
    cx, cy = 2930.0, 600.0
    out = ''
    beard = [(cx - 90, cy + 160, 70), (cx, cy + 190, 85), (cx + 95, cy + 160, 70), (cx - 50, cy + 270, 65), (cx + 50, cy + 280, 65),
             (cx, cy + 370, 60), (cx - 20, cy + 450, 45), (cx + 10, cy + 520, 32)]
    out += puffs(beard, CW)
    for ex in (cx - 85, cx + 85):
        out += outlined(f'M{p(ex - 50, cy - 50)}C{p(ex - 25, cy - 95)} {p(ex + 30, cy - 90)} {p(ex + 55, cy - 55)}C{p(ex + 25, cy - 70)} {p(ex - 25, cy - 70)} {p(ex - 50, cy - 50)}Z', '#ffffff', INK * 0.8)
        out += f'<path d="M{p(ex - 40, cy)}C{p(ex - 20, cy + 22)} {p(ex + 20, cy + 22)} {p(ex + 40, cy)}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linecap="round"/>'
    out += outlined(ellipse(cx, cy + 70, 34, 26), '#f2a6c6', INK * 0.8)
    return comp(out)


def v2_billowing() -> Image.Image:
    """Billowing: the cloud swells taller, new outlined puffs heaping up along its top, bigger and bigger towards
    the middle."""
    SCRIB_MASK[0] = ''
    edge = top_edge(2420, 3320, 40)
    rnd = random.Random(2)
    circles = []
    for k, (x, y) in enumerate(edge[::3]):
        t = 1 - abs(k / (len(edge[::3]) - 1) - 0.5) * 2
        r = 70 + 90 * t + rnd.random() * 30
        circles.append((x, y + 30 - r * 0.6, r))
    return comp(puffs(circles, CW))


def v3_storm() -> Image.Image:
    """Stormy: the cloud darkens to a bruised lavender, rain of short outlined dashes falls and a candy lightning
    bolt cracks down from it."""
    SCRIB_MASK[0] = ''
    out = ''
    rnd = random.Random(3)
    for k in range(16):
        x = 2450 + rnd.random() * 800
        y = 900 + rnd.random() * 300
        out += outlined(f'M{p(x, y)}L{p(x - 18, y + 60)}L{p(x - 8, y + 62)}L{p(x + 10, y + 2)}Z', '#bfe3ff', 8)
    bolt = [(2600, 760), (2540, 940), (2600, 945), (2520, 1140), (2690, 900), (2620, 895), (2690, 760)]
    out += outlined('M' + 'L'.join(p(*q) for q in bolt) + 'Z', '#ffe066', INK)
    return comp(out, fill_colour={CLOUD: '#A99BC8'})


def v4_mossy() -> Image.Image:
    """Overgrown: the old cloud sprouts tiny spotted mushrooms and little flowers along its top edge, like moss on
    something left out a long time."""
    SCRIB_MASK[0] = ''
    edge = top_edge(2420, 3320, 30)
    out = ''
    rnd = random.Random(4)
    for k, (x, y) in enumerate(edge[1::3]):
        if k % 2 == 0:
            h = 60 + rnd.random() * 40
            stem = f'M{p(x - 14, y + 10)}L{p(x - 10, y - h)}L{p(x + 10, y - h)}L{p(x + 14, y + 10)}Z'
            cap = f'M{p(x - 55, y - h + 5)}C{p(x - 50, y - h - 70)} {p(x + 50, y - h - 70)} {p(x + 55, y - h + 5)}Z'
            col = ['#f64c76', '#ffb36b', '#c4a3f0'][k % 3]
            out += outlined(stem, '#fff3e6', INK * 0.8) + outlined(cap, col, INK * 0.8)
            out += ''.join(f'<path d="{circle(x + dx, y - h - 28 + dy, 8)}" fill="#fff"/>' for dx, dy in [(-22, 4), (8, -14), (26, 6)])
        else:
            stem = f'M{p(x, y + 5)}C{p(x - 10, y - 40)} {p(x + 10, y - 60)} {p(x, y - 85)}'
            out += f'<path d="{stem}" fill="none" stroke="#000" stroke-width="{INK * 1.6}" stroke-linecap="round"/><path d="{stem}" fill="none" stroke="#7fd36b" stroke-width="{INK * 0.6}" stroke-linecap="round"/>'
            for j in range(5):
                a = math.radians(j * 72)
                out += outlined(circle(x + math.cos(a) * 22, y - 95 + math.sin(a) * 22, 16), '#ffe066', INK * 0.6)
            out += outlined(circle(x, y - 95, 12), '#f64c76', INK * 0.6)
    return comp(out)


def v5_gears() -> Image.Image:
    """Tonewheels: old brass gears (the organ's own tonewheels) push up out of the cloud's top, worn, with rust
    spots."""
    SCRIB_MASK[0] = ''
    out = ''
    for cx, cy, R, teeth, col in [(2650, 520, 120, 12, '#d9b65c'), (2880, 470, 85, 9, '#e6c873'), (3080, 540, 105, 11, '#cfa94e')]:
        pts = []
        for k in range(teeth * 2):
            a = math.pi * 2 * k / (teeth * 2)
            r = R if k % 2 == 0 else R * 0.8
            a2 = a + math.pi / (teeth * 2)
            pts += [(cx + math.cos(a) * r, cy + math.sin(a) * r), (cx + math.cos(a2) * r, cy + math.sin(a2) * r)]
        out += outlined('M' + 'L'.join(p(*q) for q in pts) + 'Z', col, INK)
        out += outlined(circle(cx, cy, R * 0.32), '#a8843a', INK * 0.8)
        rnd = random.Random(int(cx))
        out += ''.join(f'<path d="{circle(cx + (rnd.random() - 0.5) * R, cy + (rnd.random() - 0.5) * R, 10 + rnd.random() * 8)}" fill="#b5652f" fill-opacity="0.8"/>' for _ in range(4))
    cover = puffs([(x, 700, r) for x, r in [(2560, 140), (2720, 150), (2880, 140), (3040, 150), (3180, 120)]], CW)
    return comp(out + cover)


VERSIONS = [
    ('1-old-man', 'Old man cloud', v1_old_man),
    ('2-billowing', 'Billowing', v2_billowing),
    ('3-stormy', 'Stormy', v3_storm),
    ('4-overgrown', 'Overgrown', v4_mossy),
    ('5-tonewheels', 'Tonewheels', v5_gears),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SCRIB_MASK[0] = ''
    tiles = [('0  As painted (new wheels)', m.compose())]
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
