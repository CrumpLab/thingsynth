# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower 4' drawbar fully out) for the pink figure, bottom centre: a long coral neck rising up-left
out of the orange disc, its head a blue ring mouth with a purple tongue poking out, a magenta ear flap on the neck, a
hump on its right carrying the yellow heart, and a long coral arm lying down to the left.

    uv run scripts/pinkfigure_endframes.py
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
m.CROP = (1800, 2250, 1300, 1400)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db4/endframes'
p, outlined, circle, tube, bez, spiral = m.p, m.outlined, g.circle, g.tube, g.bez, g.spiral
INK = 15
NECK, ARM, RING, TONGUE, EAR = '#c8a468', '#f2503c', '#48DAFF', '#D848FF', '#FF48D6'
PINK, YELLOW, CYAN, LILAC, ORANGE, GREEN, MINT = '#ff9fc4', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b', '#7fe0c8'
HEAD = (2427.0, 2924.0)  # the blue ring mouth (f080), facing up-left
RING_ANG = -53.0  # its long axis
NECK_L = (2412.0, 3112.0)  # a point on the neck's left outline
HEAD_IDS = ['f080', 'f081']


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


def rot(x, y, ang, ox=0.0, oy=0.0):
    a = math.radians(ang)
    return ox + x * math.cos(a) - y * math.sin(a), oy + x * math.sin(a) + y * math.cos(a)


def lumpy(cx, cy, rx, ry, ang=0.0, n=10, jit=0.07, seed=0) -> str:
    """A hand-drawn, slightly lumpy oval."""
    rnd = random.Random(seed)
    pts = []
    for k in range(n):
        t = k / n * 2 * math.pi + rnd.uniform(-0.12, 0.12)
        f = 1 + rnd.uniform(-jit, jit)
        pts.append(rot(math.cos(t) * rx * f, math.sin(t) * ry * f, ang, cx, cy))
    return m.smooth(pts)


def petal(bx, by, ang, L, W, seed=0, squash=1.0) -> str:
    """A lumpy petal or leaf from (bx, by) pointing along ang, length L, width W."""
    rnd = random.Random(seed)
    j = lambda v: v * (1 + rnd.uniform(-0.08, 0.08))
    loc = [(-0.04 * L, 0), (0.08 * L, -j(0.3 * W)), (0.42 * L, -j(0.52 * W)), (0.8 * L, -j(0.42 * W)), (L, -0.1 * W),
           (L, 0.1 * W), (0.8 * L, j(0.42 * W)), (0.42 * L, j(0.52 * W)), (0.08 * L, j(0.3 * W))]
    return m.smooth([rot(x, y * squash, ang, bx, by) for x, y in loc])


def open_line(d: str) -> str:
    """A tube's outline left open at its base, so it joins the shape it grows from without a seam."""
    return d.rstrip('Z')


def head_copy(dx, dy) -> str:
    """The ring mouth and tongue as painted, moved by (dx, dy): fills and their own ink."""
    out = f'<g transform="translate({dx:.1f} {dy:.1f})">'
    for f in ['f081', 'f080']:
        out += f'<path d="{m.FILLS[f]}" fill="{TONGUE if f == "f081" else RING}"/>'
    ink = sorted({s for f in HEAD_IDS for s in m.own_ink(f)})
    out += '<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in ink) + '</g>'
    return out + '</g>'


def eye(cx, cy, r, look=(-0.35, -0.3)) -> str:
    out = outlined(lumpy(cx, cy, r, r * 1.08, 0, 9, 0.04, 3), '#ffffff', INK)
    px, py = cx + look[0] * r, cy + look[1] * r
    out += outlined(circle(px, py, r * 0.46), '#3a2a5a', INK * 0.7)
    out += f'<path d="{circle(px - r * 0.14, py - r * 0.16, r * 0.14)}" fill="#fff"/>'
    return out


# ---- 1  morph: the ring head blooms into a trumpet flower ----------------------------------------------------------
def v1_flower() -> Image.Image:
    """Trumpet flower: the ring mouth opens into a big candy flower, petals round it; the tongue stays as its
    stamen, and two leaves grow from the neck."""
    hx, hy = HEAD
    out = ''
    # two leaves out of the neck's left side
    for (bx, by, a, L, W, col, sd) in [(2455, 3160, 205, 290, 150, GREEN, 4), (2500, 3235, 162, 280, 140, '#5cc85a', 5)]:
        d = petal(bx, by, a, L, W, sd)
        out += outlined(d, col, INK)
    # outer petals: a rosette tilted like the ring, skipping where the neck runs down to the right
    rnd = random.Random(2)
    outer = [a for a in range(-160, 200, 52) if not 30 < (a % 360) < 118]
    for k, a in enumerate(outer):
        a += rnd.uniform(-8, 8)
        x, y = rot(math.cos(math.radians(a)) * 60, math.sin(math.radians(a)) * 40, RING_ANG + 90, hx, hy)
        out += outlined(petal(x, y, a, rnd.uniform(300, 360), rnd.uniform(220, 260), 10 + k, 0.9), [PINK, '#ff7fb0'][k % 2], INK)
    for k, a in enumerate(outer):
        a2 = a + 26 + rnd.uniform(-6, 6)
        if 30 < (a2 % 360) < 118:
            continue
        out += outlined(petal(hx, hy, a2, rnd.uniform(200, 250), 150, 30 + k), YELLOW, INK * 0.9)
    return draw(out, HEAD_IDS)


# ---- 2  character: an arm rises and reaches up, an eye opens -------------------------------------------------------
def hand(cx, cy, R, ang, seed=0) -> str:
    """A big open mitten hand: one lumpy outline with four fat fingers and a thumb, fingers along ang."""
    rnd = random.Random(seed)
    pts = []
    fingers = [-62, -24, 12, 46]
    n = 40
    for k in range(n):
        t = -180 + k * 360 / n
        r = R
        for fa in fingers:
            d = abs((t - fa + 180) % 360 - 180)
            r = max(r, R * (1 + 0.95 * max(0.0, 1 - d / 15) ** 0.7))
        d = abs((t - 105 + 180) % 360 - 180)  # thumb
        r = max(r, R * (1 + 0.7 * max(0.0, 1 - d / 20) ** 0.7))
        r *= 1 + rnd.uniform(-0.03, 0.03)
        pts.append(rot(math.cos(math.radians(t)) * r, math.sin(math.radians(t)) * r, ang, cx, cy))
    return m.smooth(pts)


def v2_reach() -> Image.Image:
    """Reaching up: a coral arm rises out of the neck and stretches up high, a big pink hand open at the top; a
    wide-awake eye opens on its neck, looking up at it."""
    P = bez((2440, 3120), (2340, 3080), (2250, 3020), (2190, 2920), 16)
    P += bez((2190, 2920), (2140, 2840), (2115, 2780), (2122, 2680), 14)[1:]
    arm = tube(P, 56, 50)
    out = outlined(arm, ARM, INK, open_line(arm))
    out += outlined(hand(2125, 2640, 105, -85, 2), PINK, INK)
    for k, (a0, a1, r) in enumerate([(-215, -165, 250), (-15, 30, 240)]):
        out += g.c.swoosh(2125, 2640, r, a0, a1, 40, '#ffffff')
    return draw(out, HEAD_IDS, eye(2482, 3062, 64, (-0.4, -0.35)))


# ---- 3  celebration: candy streamers burst out of the mouth --------------------------------------------------------
def streamer(x0, y0, a0, L, turns, sign, w, col, seed=0) -> str:
    a = math.radians(a0)
    mid = (x0 + math.cos(a) * L, y0 + math.sin(a) * L)
    P = bez((x0, y0), (x0 + math.cos(a) * L * 0.35, y0 + math.sin(a) * L * 0.35 + 30 * sign),
            (mid[0] - math.cos(a) * L * 0.3, mid[1] - math.sin(a) * L * 0.3 - 40 * sign), mid, 18)
    hd = math.atan2(P[-1][1] - P[-2][1], P[-1][0] - P[-2][0])
    P += spiral(mid[0], mid[1], hd, 120, turns, 0.45, sign, 40)[1:]
    return outlined(tube(P, w, w * 0.6), col, INK * 0.9)


def v3_streamers() -> Image.Image:
    """Party: a burst of fat candy streamers shoots out of the ring mouth and curls, with big candy confetti."""
    hx, hy = HEAD
    out = outlined(lumpy(hx - 40, hy - 40, 150, 110, RING_ANG, 11, 0.12, 7), '#fff4c2', INK)
    cols = [PINK, YELLOW, CYAN, LILAC, ORANGE]
    for k, (a, L, s) in enumerate([(-205, 360, 1), (-152, 430, -1), (-100, 440, 1), (-48, 360, -1)]):
        out += streamer(hx - 20, hy - 20, a, L, 0.75, s, 46, cols[k], k)
    rnd = random.Random(4)
    for k, (x, y) in enumerate([(2000, 2700), (2180, 2450), (2420, 2400), (2640, 2560), (2050, 2950), (2300, 2600)]):
        out += outlined(lumpy(x, y, 66, 46, rnd.uniform(0, 180), 7, 0.12, k), cols[(k + 2) % 5], INK * 0.9)
    return draw('', [], out + head_copy(0, 0))


# ---- 4  pun: up an octave, the same head again, higher up ----------------------------------------------------------
def v4_octave() -> Image.Image:
    """Up an octave: the neck stretches up out of the ring mouth and the same head pops out again higher up, the
    note repeated an octave above, tongue and all."""
    hx, hy = HEAD
    dx, dy = -110, -420
    P = bez((hx + 10, hy + 10), (hx - 10, hy - 140), (hx + dx + 40, hy + dy + 180), (hx + dx + 10, hy + dy + 20), 20)
    out = outlined(tube(P, 64, 60), NECK, INK)
    out += head_copy(dx, dy)
    return draw(out, ['f080'], '')


# ---- 5  its own form: the tongue unrolls long and curls up ---------------------------------------------------------
def v5_tongue() -> Image.Image:
    """Long tongue: the purple tongue unrolls out of the ring, long and fat, sweeping up and curling at the tip."""
    P = bez((2420, 2905), (2300, 2860), (2120, 2860), (2060, 2680), 22)
    hd = math.atan2(P[-1][1] - P[-2][1], P[-1][0] - P[-2][0])
    P += spiral(P[-1][0], P[-1][1], hd, 85, 1.2, 0.8, 1, 50)[1:]
    t = tube(P, 52, 30)
    out = outlined(t, TONGUE, INK, open_line(t))
    out += f'<path d="{tube(P[3:40], 14, 8)}" fill="#ee9bff"/>'
    return draw(out, ['f080'], '')


VERSIONS = [
    ('1-trumpet-flower', 'Trumpet flower', v1_flower),
    ('2-reaching-up', 'Reaching up', v2_reach),
    ('3-streamers', 'Streamers', v3_streamers),
    ('4-octave-up', 'Up an octave', v4_octave),
    ('5-long-tongue', 'Long tongue', v5_tongue),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (drawbar in)', m.compose())]
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


# ---- chosen: up an octave, with the wide eye (4 + the eye from 2) ------------------------------------------------
# The Lower 4' drawbar, 0 to 8, one arrival per step: a wide eye opens on the neck (steps 1-2, its pupil looking up);
# a new neck rises out from behind the ring mouth one segment per step (steps 2-6); the same head, ring and tongue as
# painted, pops out on top with an overshoot (step 7); its tongue pokes out further (step 8).
STEP = 1 / 8
OCT = (-110.0, -420.0)  # the second head's offset from the painted one
NECK_P = bez((HEAD[0] + 10, HEAD[1] + 10), (HEAD[0] - 10, HEAD[1] - 140), (HEAD[0] + OCT[0] + 40, HEAD[1] + OCT[1] + 180),
             (HEAD[0] + OCT[0] + 10, HEAD[1] + OCT[1] + 20), 40)
EYE_AT, EYE_R = (2482.0, 3062.0), 64.0
LOOK = (-0.2, -0.5)
TW = 42.0  # half the new tongue's width: a little wider than the painted one, so it covers it


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    x = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(s, 4), 'end': round(e, 4), 'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = round(out[0], 4), round(out[1], 4)
    return x


def moved(d: str, dx: float, dy: float, s: float = 1.0, at=(0.0, 0.0)) -> str:
    """A painted path moved by (dx, dy), then scaled by s round `at`."""
    return m.warp_path(d, lambda x, y: (at[0] + (x + dx - at[0]) * s, at[1] + (y + dy - at[1]) * s))


def captube(P, w0, w1) -> str:
    """Like ghost's tube, but the round cap at the end is built from points, so it always bulges outward."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = w0 + (w1 - w0) * i / (n - 1)
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    ex, ey = P[-1]
    hd = math.atan2(ey - P[-2][1], ex - P[-2][0])
    cap = [(ex + math.cos(hd + math.pi / 2 - math.pi * k / 12) * w1, ey + math.sin(hd + math.pi / 2 - math.pi * k / 12) * w1) for k in range(1, 12)]
    return 'M' + 'L'.join(p(*q) for q in L + cap + R[::-1]) + 'Z'


def neck_items() -> list[dict]:
    """Five ever-longer necks, one per step, each rising (grow y) from the base over its step; every one covers the last
    exactly, so the neck simply gets longer."""
    items = []
    n = len(NECK_P) - 1
    base = NECK_P[0]
    for k in range(1, 6):
        P = NECK_P[: round(n * (0.42 + 0.58 * k / 5)) + 1]
        s = k * STEP
        items.append(it(captube(P, 64, 62 - 0.4 * k), NECK, INK, base, s, s + STEP, "y"))
    return items


def head_items() -> list[dict]:
    """The painted head again, up an octave: an outlined swell that pops up big and sinks back (the overshoot), the
    ring and tongue with their own ink growing in over it, then the tongue poking out further."""
    dx, dy = OCT
    at = (HEAD[0] + dx, HEAD[1] + dy)
    s7, s8 = 6 * STEP, 7 * STEP
    big = 1.22
    items = [it(moved(m.FILLS['f081'], dx, dy, big, at), TONGUE, INK, at, s7, s7 + 0.5 * STEP, out=(s7 + 0.5 * STEP, s8)),
             it(moved(m.FILLS['f080'], dx, dy, big, at), RING, INK, at, s7, s7 + 0.5 * STEP, out=(s7 + 0.5 * STEP, s8))]
    # step 8: the tongue pokes out further; under the head copy so the ring stays in front
    grow_in = (s7 + 0.25 * STEP, s8)
    tongue_ink = [i for i in m.own_ink('f081') if i not in m.own_ink('f080')]
    ring_ink = m.own_ink('f080')
    gone = (s8, s8 + 0.6 * STEP)  # the painted tongue draws back into the ring as the long one comes out
    items += [it(moved(m.FILLS['f081'], dx, dy), TONGUE, 0, at, *grow_in, out=gone)]
    items += [it(moved(m.INKS[i], dx, dy), '#000', 0, at, *grow_in, out=gone) for i in tongue_ink]
    # step 8: a longer tongue pokes out of the ring over the painted one, under the ring
    P = bez((2462 + dx, 2918 + dy), (2300 + dx, 2885 + dy), (2170 + dx, 2860 + dy), (2085 + dx, 2770 + dy), 24)
    items += [it(captube(P, 40, 50), TONGUE, INK, P[0], s8, 1.0),
              it(captube(P[8:21], 9, 12), '#ee9bff', 0, P[0], s8, 1.0)]
    items += [it(moved(m.FILLS['f080'], dx, dy), RING, 0, at, *grow_in)]
    items += [it(moved(m.INKS[i], dx, dy), '#000', 0, at, *grow_in) for i in ring_ink]
    return items


def eye_items() -> list[dict]:
    x, y = EYE_AT
    r = EYE_R
    px, py = x + LOOK[0] * r, y + LOOK[1] * r
    return [it(lumpy(x, y, r, r * 1.08, 0, 9, 0.04, 3), '#ffffff', INK, (x, y), 0.0, STEP, 'y'),
            it(circle(px, py, r * 0.46), '#3a2a5a', INK * 0.7, (px, py), 0.5 * STEP, 2 * STEP),
            it(circle(px - r * 0.14, py - r * 0.16, r * 0.14), '#ffffff', 0, (px - r * 0.14, py - r * 0.16), 1.2 * STEP, 2 * STEP)]


FRONT_IDS = ['f080', 'f081']


def around_items() -> list[dict]:
    return neck_items() + head_items()


def masked(body: str) -> str:
    """The app's 'around' placement: above the ink, with the object's own shapes and the front ids (and a band as wide
    as the ink round them) cut out, so they stay in front."""
    cut = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>'
                  for f in ['f075', 'f082'] + FRONT_IDS)
    return (f'<defs><mask id="pfm" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect width="4950" height="4950" fill="#fff"/>{cut}</mask></defs><g mask="url(#pfm)">{body}</g>')


def octave_frame(t: float) -> Image.Image:
    im = m.compose()
    if t <= 0:
        return im
    a = g.sprite_svg(around_items(), t)
    if a:
        im.alpha_composite(m.svg(masked(a)))
    e = g.sprite_svg(eye_items(), t)
    if e:
        im.alpha_composite(m.svg(e))
    return im


def octave_main(frames=(0, 0.25, 0.5, 0.75, 1.0), name='strip.png') -> None:
    out = OUT.parent / 'octave-up'
    out.mkdir(parents=True, exist_ok=True)
    tiles = [octave_frame(t) for t in frames]
    if frames[-1] == 1.0:
        tiles[-1].save(out / 'end-frame.png')
    w, h = tiles[0].size
    sc = 0.42
    tw, th = int(w * sc), int(h * sc)
    strip = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (tt, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {tt:.3g}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
    strip.save(out / name)
    print('wrote', out / name)


def build() -> dict:
    return {
        'label': "The pink figure: drag for the Lower 4' drawbar; it opens an eye, its neck rises out of its ring mouth "
                 'step by step and the same head pops out on top, an octave up, poking its tongue out further',
        'effects': [{'effect': 'sprites', 'place': 'around', 'front': FRONT_IDS, 'items': around_items()},
                    {'effect': 'sprites', 'place': 'over', 'items': eye_items()}],
    }


if __name__ == '__main__' and 'octave' in __import__('sys').argv[1:]:
    octave_main()
    octave_main(tuple(k / 8 for k in range(9)), 'steps.png')

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    dest = OUT.parent / 'build.json'
    dest.write_text(_j.dumps(build(), indent=2) + '\n')
    print('exported', dest)
