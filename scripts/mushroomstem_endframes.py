# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Upper 8' drawbar fully out) for the mushroom stem: the pale mint stem under the bright green
sleepy-eyed cap, top centre, with a curled hand on its right holding a blue drop.

    uv run scripts/mushroomstem_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (1450, 380, 1150, 1150)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/upper-db3/endframes'
p, outlined, circle, tube, bez, smooth = m.p, m.outlined, g.circle, g.tube, g.bez, m.smooth
INK = 13
STEM = '#c9efd6'      # the stem's pale mint, made opaque
DROP = '#4f8fbf'      # the blue drop it holds
CAP = ['f268', 'f278', 'f287']
SPIKES = ['f229', 'f230', 'f226']
DROP_INK = ['i1475', 'i0634']
CURL_INK = ['i1476', 'i0635', 'i1474', 'i0633', 'i1463', 'i0622', 'i1462', 'i0621']
CANDY = ['#ff9f43', '#FF5CED', '#ffe066', '#c4a3f0', '#f64c76', '#2DFFF4', '#ff9fc4', '#7fd36b']

# the stem's edges (canvas px), sampled from f263
LEFT = [(1866, 725), (1872, 775), (1879, 825), (1885, 875), (1891, 925), (1896, 975), (1901, 1025), (1905, 1075),
        (1906, 1150), (1906, 1225), (1904, 1275)]
RIGHT = [(2030, 725), (2015, 775), (2003, 825), (1996, 870), (1989, 920), (1984, 970), (1981, 1020), (1979, 1075),
         (1979, 1150), (1980, 1225), (1984, 1275)]


def edge(side: list, y: float) -> float:
    for (x0, y0), (x1, y1) in zip(side, side[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return side[-1][0] if y > side[-1][1] else side[0][0]


def draw(front: str = '', again: list[str] | None = None, over: str = '', ink: list[str] | None = None,
         **kw) -> Image.Image:
    """New shapes, then the named painted shapes and their ink (plus any extra ink ids) laid back on top; `over`
    goes on top of everything."""
    again = again or []
    m.FRONT = again
    m.FRONT_INK = sorted({s for f in again for s in m.own_ink(f)} | set(ink or []))
    try:
        im = m.compose(front=front or '<g/>', **kw)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def lump(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.05, n=14) -> str:
    """A lumpy hand-drawn ellipse, rotated by rot degrees."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        k = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def outside_stem(body: str) -> str:
    """Clip new shapes to outside the stem, so they come out from behind its edge."""
    return (f'<defs><clipPath id="out"><path clip-rule="evenodd" d="M0 0H4950V4950H0Z{m.FILLS["f263"]}"/></clipPath>'
            f'</defs><g clip-path="url(#out)">{body}</g>')


# ---- 1. shelf fungi -------------------------------------------------------------------------------------------------
def bracket(y, side, w, h, cols, seed, tilt=-10.0, at=None) -> str:
    """A shelf fungus coming out of the stem's edge at height y: a flat fan with a cream gill rim underneath and
    bands of colour on top, like turkey-tail, tilted up and out by `tilt` degrees."""
    x = (edge(LEFT if side < 0 else RIGHT, y) if at is None else at) - side * 30
    rnd = random.Random(seed)
    a = -math.radians(tilt) * side
    R = lambda u, v: (x + u * math.cos(a) - v * math.sin(a), y + u * math.sin(a) + v * math.cos(a))

    def fan(k):
        rnd = random.Random(seed)  # the same wobble for each band, so the bands run parallel
        pts = []
        for i in range(11):
            t = math.pi / 2 - i / 10 * math.pi  # top at the stem, round the rim, back under to the stem
            r = 1 + 0.05 * (rnd.random() * 2 - 1)
            c = abs(math.cos(t)) ** 0.55
            pts.append(R(side * c * w * k * r, -math.sin(t) * (h * k if t > 0 else h * 0.3) * r))
        return smooth([R(-side * 10, -h * k * 0.95)] + pts + [R(-side * 10, h * 0.22)])

    gx, gy = R(side * w * 0.48, h * 0.16)
    out = outlined(lump(gx, gy, w * 0.5, h * 0.3, math.degrees(a), seed + 1), '#fff4d6', INK * 0.85)
    out += outlined(fan(1.0), cols[1], INK)
    out += outlined(fan(0.72), cols[0], INK * 0.8)
    return out


def v1_shelf() -> Image.Image:
    """Shelf fungi: candy bracket mushrooms sprout one above another from both sides of the stem, a step each."""
    # one per drawbar step: the left side climbs to the cap, the right side only below and above the curled hand
    spec = [(1295, 1, 240, 112, 8), (1250, -1, 240, 112, 12), (1175, 1, 215, 104, 12), (1105, -1, 225, 108, 10),
            (960, -1, 210, 100, 14), (1010, 1, 165, 82, 16, 2125), (820, -1, 190, 92, 12), (795, 1, 150, 72, 10)]
    pairs = [(CANDY[0], '#ffe066'), (CANDY[1], '#ff9fc4'), (CANDY[3], '#f4ecff'), (CANDY[4], '#ff9f43'),
             (CANDY[5], '#d6fff9'), (CANDY[7], '#e8ff9a'), (CANDY[2], '#fff7c2'), (CANDY[6], '#ffffff')]
    order = sorted(range(len(spec)), key=lambda k: spec[k][0])  # upper ones first, lower ones overlap them
    body = ''.join(bracket(*spec[k][:4], pairs[k], k * 11, *spec[k][4:]) for k in order)
    return draw(outside_stem(body), ['f285'], ink=m.own_ink('f263') + DROP_INK)


# ---- 2. hooray --------------------------------------------------------------------------------------------------------
def mitten(cx, cy, r, ang, col, thumb=1) -> list[str]:
    """A big mitten hand at (cx, cy) pointing at ang degrees, its thumb out to one side: [thumb, palm] paths."""
    a = math.radians(ang)
    t = a + thumb * 1.25
    return [lump(cx + math.cos(t) * r * 0.85, cy + math.sin(t) * r * 0.85, r * 0.55, r * 0.32,
                 math.degrees(t), 3), lump(cx, cy, r * 1.2, r * 0.9, ang, 4)]


STEM_PATH = smooth(LEFT + [(1930, 1310), (1990, 1340)] + RIGHT[::-1] + [(2045, 690), (1960, 690), (1900, 700)])


def v2_hooray() -> Image.Image:
    """Hooray: the curled hand unrolls into a long arm that lifts the blue drop high beside the cap, and a second arm
    rises from the other side, waving."""
    P = bez((1930, 1040), (1790, 1080), (1680, 1020), (1640, 900), 24)     # left arm, out and up, waving
    Q = bez((1960, 905), (2100, 880), (2250, 905), (2280, 730), 24)       # right arm, out of the curl, hand up high
    shapes = [tube(P, 48, 42), tube(Q, 52, 46), STEM_PATH] + mitten(1622, 840, 70, -125, STEM, -1) \
        + mitten(2285, 670, 72, -85, STEM, 1)
    body = ''.join(f'<path d="{d}" fill="{STEM}" stroke="#000" stroke-width="{INK * 2}" stroke-linejoin="round"/>' for d in shapes)
    body += ''.join(f'<path d="{d}" fill="{STEM}"/>' for d in shapes)  # one merged body, no seams
    drop = (f'<g transform="translate(2300 530) rotate(-55) scale(1.3) translate(-2140 -888)">'
            f'{outlined(m.FILLS["f285"], DROP, INK / 1.3)}</g>')
    wave = ''.join(outlined(g.crescent(1622, 840, r, a0, a1, 30), '#ffffff', INK * 0.8)
                   for r, a0, a1 in ((125, 95, 150), (175, 100, 145)))
    # the old curl and drop painted out: blank their ink and hide the drop
    blank = {i: 'M0 0' for i in CURL_INK + DROP_INK}
    return draw(body, CAP + SPIKES, drop + wave, ink_over=blank, fill_colour={'f285': 'none'})


# ---- 3. veiled lady ---------------------------------------------------------------------------------------------------
def v3_veil() -> Image.Image:
    """Veiled lady: a lacy candy net skirt drops from under the cap and flares out round the stem to the spikes."""
    top_y, bot_y = 735, 1265
    half = lambda y: 75 + 195 * ((y - top_y) / (bot_y - top_y)) ** 1.6
    cx = lambda y: 1945 + 20 * (y - top_y) / (bot_y - top_y)
    rnd = random.Random(7)
    left, right, hem = [], [], []
    for i in range(7):
        y = top_y + (bot_y - top_y) * i / 7
        left.append((cx(y) - half(y), y))
        right.append((cx(y) + half(y), y))
    n = 10
    for i in range(n + 1):
        x = cx(bot_y) - half(bot_y) + 2 * half(bot_y) * i / n
        hem.append((x, bot_y + (40 if i % 2 else 5) + rnd.uniform(-6, 6)))
    skirt = smooth(left + hem + right[::-1])
    holes = ''
    y, r = top_y + 70, 0
    while y < bot_y:
        step = 100
        x = cx(y) - half(y) - (step / 2 if r % 2 else 0)
        while x < cx(y) + half(y) + step:
            hx, hy = x + rnd.uniform(-6, 6), y + rnd.uniform(-5, 5)
            if abs(hx - cx(hy)) + 42 < half(hy) - 4 and hy + 36 < bot_y - 10:
                holes += lump(hx, hy, 38, 36, rnd.uniform(-20, 20), r * 31 + int(x), 0.14, 8)
            x += step
        y += 88
        r += 1
    big = 'M0 0H4950V4950H0Z'
    lace = (f'<defs><clipPath id="net"><path clip-rule="evenodd" d="{big}{holes}"/></clipPath>'
            f'<clipPath id="sk"><path d="{skirt}"/></clipPath></defs>'
            f'<g clip-path="url(#net)"><path d="{skirt}" fill="#ff9fc4"/>'
            f'<path d="{skirt}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/></g>'
            f'<g clip-path="url(#sk)"><path d="{holes}" fill="none" stroke="#000" stroke-width="{INK * 0.85}" stroke-linejoin="round"/></g>')
    ring = outlined(lump(1945, top_y + 10, 100, 34, -6, 2), '#FF5CED', INK)  # the ring it hangs from
    return draw(lace + ring, CAP + SPIKES + ['f285'], ink=DROP_INK + ['i1476', 'i0635', 'i1474', 'i0633'])


# ---- 4. organ pipe ----------------------------------------------------------------------------------------------------
def v4_pipe() -> Image.Image:
    """8' pipe: the stem turns into a big golden organ pipe, the eight-foot fundamental, singing out of its mouth
    with rings of sound."""
    x0, x1, y0, y1 = 1858, 2042, 700, 1420
    rnd = random.Random(4)
    ys = [y0 + (y1 - y0) * i / 6 for i in range(7)]
    body = smooth([(x0 + rnd.uniform(-7, 7), y) for y in ys] + [((x0 + x1) / 2, y1 + 8)]
                  + [(x1 + rnd.uniform(-7, 7), y) for y in ys[::-1]] + [((x0 + x1) / 2, y0 - 8)])
    out = outlined(body, '#ffd23f', INK)
    out += f'<path d="{tube([(x0 + 38, y0 + 40), (x0 + 34, y1 - 40)], 14, 14)}" fill="#fff4b0"/>'
    # top rim
    out += outlined(lump((x0 + x1) / 2, y0, (x1 - x0) / 2 + 8, 26, 0, 1), '#ffe066', INK)
    # the mouth: a dark singing arch with an upper lip
    mx, my = (x0 + x1) / 2, 1020
    mouth = smooth([(mx - 60, my + 58), (mx - 64, my - 5), (mx - 38, my - 70), (mx + 4, my - 95), (mx + 42, my - 64),
                    (mx + 62, my), (mx + 58, my + 60)])
    out += outlined(mouth, '#3a1030', INK)
    out += outlined(lump(mx, my + 40, 40, 22, 0, 5), '#f64c76', INK * 0.8)
    out += outlined(smooth([(mx - 74, my + 56), (mx, my + 50), (mx + 74, my + 58), (mx + 52, my + 102), (mx, my + 108), (mx - 52, my + 100)]), '#ffb300', INK)
    # sound rings to the left (outlined crescents)
    rings = ''
    for k, r in enumerate((150, 240, 330)):
        a0, a1 = math.radians(150), math.radians(210)
        w = 26 - 4 * k
        outer = [(mx + math.cos(a0 + (a1 - a0) * i / 16) * (r + w), my + math.sin(a0 + (a1 - a0) * i / 16) * (r + w)) for i in range(17)]
        inner = [(mx + math.cos(a1 - (a1 - a0) * i / 16) * (r - w), my + math.sin(a1 - (a1 - a0) * i / 16) * (r - w)) for i in range(17)]
        rings += outlined('M' + 'L'.join(p(*q) for q in outer + inner) + 'Z', CANDY[[1, 5, 2][k]], INK * 0.85)
    return draw(out, CAP + SPIKES + ['f285'], rings, ink=DROP_INK + ['i1476', 'i0635', 'i1474', 'i0633'])


# ---- 5. pot belly -----------------------------------------------------------------------------------------------------
def v5_belly() -> Image.Image:
    """Pot belly: the stem swells into a big round bulb of a body, a pale tummy patch on it, the curled hand
    resting on top holding its drop."""
    pts = [(1880, 800), (1855, 900), (1780, 990), (1735, 1110), (1760, 1240), (1870, 1320), (2030, 1325),
           (2160, 1265), (2215, 1140), (2175, 1010), (2080, 920), (2005, 830), (1995, 760), (1875, 750)]
    belly = smooth(pts)
    out = outlined(belly, STEM, INK)
    out += f'<path d="{lump(1938, 780, 64, 60, 0, 2, 0.02)}" fill="{STEM}"/>'  # merge into the stem, no seam
    out += outlined(g.crescent(1975, 1130, 175, 150, 215, 34), '#ffffff', INK * 0.8)  # a shine on its roundness
    out += outlined(lump(2010, 1205, 26, 20, 0, 4, 0.15), '#e98fb0', INK * 0.8)  # belly button
    return draw(out, CAP + SPIKES + ['f285'], ink=DROP_INK + CURL_INK)


VERSIONS = [
    ('1-shelf-fungi', 'Shelf fungi', v1_shelf),
    ('2-hooray', 'Hooray', v2_hooray),
    ('3-veiled-lady', 'Veiled lady', v3_veil),
    ('4-organ-pipe', "8' pipe", v4_pipe),
    ('5-pot-belly', 'Pot belly', v5_belly),
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


# ---- chosen: hooray -------------------------------------------------------------------------------------------------
# Picked: Hooray on its own. Upper 8' from 0 to 8: the curled hand unrolls into a long arm, lifting its blue drop a
# little higher each step (steps 1-4); the second arm rises from the stem's left side (steps 5-7); motion crescents
# flick round the waving hand (step 8). Each pose of an arm arrives on its step while the pose before shrinks away,
# so the arm reads as one arm moving. The painted drop fades on step 1 (vanish, role "drop") and a sprite drop rides
# the hand. A shoulder the shape of the painted curl covers it (and the cyan wash inside it) from step 1. Arms,
# shoulder and the patches that hide the joins are all one colour, the stem's own aqua-mint where they leave it, and
# drawn as an outlined layer under a fill-only layer, so they merge into the stem with no seam.

ARM = '#74efd2'       # the stem where the arms leave it: pale aqua-mint (its fill over the wash there)
DROPC = '#4a9cbc'     # the drop as painted
SKY = '#c0fbd6'       # the sky round the drop
STEP = 1 / 8
# The painted curl's two lines (centrelines, canvas px): the hooked top line and the long lower line.
CURL_TOP = [(1952, 937), (1948, 918), (1958, 898), (1981, 875), (2015, 858), (2050, 855), (2080, 860), (2094, 866)]
CURL_LOW = [(2127, 945), (2120, 972), (2090, 1005), (2050, 1035), (2010, 1060), (1975, 1075), (1942, 1084)]
R_SHOULDER = (2040.0, 955.0)
L_SHOULDER = (1910.0, 965.0)


def ltube(P, w0, w1, seed) -> str:
    """A lumpy tapered limb along P: its width swells and pinches a little, hand-drawn."""
    rnd = random.Random(seed)
    ph, n = rnd.random() * 6.28, len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = i / (n - 1)
        w = (w0 + (w1 - w0) * u) * (1 + 0.07 * math.sin(u * 9 + ph))
        L.append((x + nx * w * (1 + 0.03 * rnd.uniform(-1, 1)), y + ny * w))
        R.append((x - nx * w * (1 + 0.03 * rnd.uniform(-1, 1)), y - ny * w))
    pts = L + R[::-1]
    return smooth(pts[::2] if len(pts) > 40 else pts)


def drop_path(gx, gy, deg, s=1.2) -> str:
    """The painted drop, its pointed base set into the grip at (gx, gy), turned by deg and scaled by s."""
    d = m.FILLS['f285']
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    nums = re.findall(r'[MCZ]|-?\d+\.?\d*', d)
    out, pend = [], None
    for t in nums:
        if t in 'MCZ':
            out.append(t)
            continue
        if pend is None:
            pend = float(t)
            continue
        x, y = (pend - 2040) * s, (float(t) - 956) * s
        out.append(p(gx + x * ca - y * sa, gy + x * sa + y * ca))
        pend = None
    return ' '.join(out).replace('M ', 'M').replace(' C ', 'C').replace(' Z', 'Z')


def arm_pose(shoulder, ctrl, hand, w0, w1, hand_ang, thumb, seed):
    """One pose of an arm: (thumb, [limb, palm]); the thumb peeks out from behind the palm."""
    P = bez(shoulder, ctrl[0], ctrl[1], hand, 22)
    th, palm = mitten(hand[0], hand[1], 56, hand_ang, ARM, thumb)
    return th, [ltube(P, w0, w1, seed), palm]


R_POSES = [  # (elbow controls, hand, hand angle, drop turn)
    (((2090, 935), (2140, 915)), (2150, 850), -65, -20),
    (((2110, 945), (2200, 935)), (2215, 795), -72, -34),
    (((2130, 950), (2240, 940)), (2260, 730), -80, -48),
    (((2140, 945), (2270, 935)), (2285, 665), -85, -60),
]
L_POSES = [
    (((1870, 960), (1810, 950)), (1760, 915), -165),
    (((1860, 960), (1765, 950)), (1715, 855), -130),
    (((1855, 955), (1735, 945)), (1675, 785), -110),
]


def hooray_items() -> list[dict]:
    E2 = INK * 2  # the outlined layer's stroke: the fill-only layer on top covers its inner half
    outl, fills, drops, thumbs = [], [], [], []

    def timed(d, at, start, end, out=None, fill=ARM, edge=INK):
        it = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 4),
              'end': round(end, 4), 'grow': 'scale'}
        if out:
            it['outStart'], it['outEnd'] = round(out[0], 4), round(out[1], 4)
        return it

    def add(d, at, start, end, out=None):
        it = {'d': d, 'at': [round(at[0], 1), round(at[1], 1)], 'start': round(start, 4), 'end': round(end, 4), 'grow': 'scale'}
        if out:
            it['outStart'], it['outEnd'] = round(out[0], 4), round(out[1], 4)
        outl.append({**it, 'fill': ARM, 'edge': E2})
        fills.append({**it, 'fill': ARM, 'edge': 0})

    # step 1 (popping in at once): the shoulder over the painted curl, its lines laid on the painted ones
    shoulder = smooth(CURL_TOP + [(2112, 884), (2130, 914)] + CURL_LOW + [(1946, 1040), (1948, 980)])
    add(shoulder, R_SHOULDER, 0.0, 0.04)
    for k, (ctrl, hand, ang, turn) in enumerate(R_POSES):
        out = ((k + 1) * STEP, (k + 2) * STEP) if k < len(R_POSES) - 1 else None
        th, ds = arm_pose((2030, 950), ctrl, hand, 42, 34, ang, 1, 20 + k)
        thumbs.append(timed(th, R_SHOULDER, k * STEP, (k + 1) * STEP, out))
        for d in ds:
            add(d, R_SHOULDER, k * STEP, (k + 1) * STEP, out)
        a = math.radians(ang)
        grip = (hand[0] + math.cos(a) * 34, hand[1] + math.sin(a) * 34)
        dit = {'d': drop_path(grip[0], grip[1], turn, 1.05), 'fill': DROPC, 'edge': INK, 'at': [round(R_SHOULDER[0], 1), round(R_SHOULDER[1], 1)],
               'start': round(k * STEP, 4), 'end': round((k + 1) * STEP, 4), 'grow': 'scale'}
        if out:
            dit['outStart'], dit['outEnd'] = round(out[0], 4), round(out[1], 4)
        drops.append(dit)
    for j, (ctrl, hand, ang) in enumerate(L_POSES):
        s = (4 + j) * STEP
        out = (s + STEP, s + 2 * STEP) if j < len(L_POSES) - 1 else None
        th, ds = arm_pose((1917, 965), ctrl, hand, 40, 33, ang, -1, 40 + j)
        thumbs.append(timed(th, L_SHOULDER, s, s + STEP, out))
        for d in ds:
            add(d, L_SHOULDER, s, s + STEP, out)
    # a fill-only band of the stem's own aqua across its inside where the arms leave it (the painted stem is that
    # colour there), hiding the curl's inner ends and the limbs' starts, so no line crosses a join
    y0, y1 = 905, 1040
    band = (f'M{p(edge(LEFT, y0) + 1, y0)}L{p(2000, y0 - 4)}L{p(2004, 1054)}L{p(1950, 1072)}'
            f'L{p(edge(LEFT, y1) + 1, y1)}Z')
    patches = [{'d': band, 'at': [1950.0, 972.0], 'start': 0.0, 'end': 0.04}]
    patches = [{**q, 'fill': ARM, 'edge': 0, 'grow': 'scale'} for q in patches]
    # the wash under the painted drop is cyan: a fill-only shape in the sky's mint over it, so it reads as background
    sky = [{'d': lump(2150, 884, 130, 74, -28, 11, 0.03), 'fill': SKY, 'edge': 0, 'at': [2150.0, 884.0], 'start': 0.0, 'end': 0.04,
            'grow': 'scale'}]
    # step 8: motion crescents flick out round the waving hand
    hx, hy = L_POSES[-1][1]
    flicks = [{'d': g.crescent(hx, hy, r, a0, a1, 30), 'fill': '#ffffff', 'edge': round(INK * 0.8, 1), 'at': [hx, hy],
               'start': round(7 * STEP + 0.03 * k, 4), 'end': round(1.0 - 0.03 * (1 - k), 4), 'grow': 'scale'}
              for k, (r, a0, a1) in enumerate(((125, 95, 150), (175, 100, 145)))]
    return sky + drops + thumbs + outl + fills + patches + flicks


def hooray_frame(t: float) -> Image.Image:
    """Preview as the app draws it: the painted drop fading over step 1, the sprites over everything."""
    if t <= 0:
        return m.compose()
    u = min(1.0, t / STEP)
    kw = {}
    if u >= 0.5:
        kw = {'ink_over': {i: 'M0 0' for i in DROP_INK + ['i1476', 'i0635', 'i1474', 'i0633']},
              'fill_colour': {'f285': 'none'}}
    im = m.compose(**kw)
    im.alpha_composite(m.svg(g.sprite_svg(hooray_items(), t)))
    return im


def strip(frames, path, label) -> None:
    tiles = [hooray_frame(t) for t in frames]
    w, h = tiles[0].size
    sc, cols = 0.42, min(5, len(frames))
    rows = math.ceil(len(frames) / cols)
    tw, th = int(w * sc), int(h * sc)
    im = Image.new('RGB', (tw * cols + 10 * (cols + 1), (th + 46) * rows + 10), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for i, (tt, tile) in enumerate(zip(frames, tiles)):
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 46)
        d.text((x, y), label(tt), fill='black', font=font)
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 34))
    im.save(path)


def hooray_main() -> None:
    out = OUT.parent / 'hooray'
    out.mkdir(parents=True, exist_ok=True)
    hooray_frame(1.0).save(out / 'end-frame.png')
    strip([0, 0.25, 0.5, 0.75, 1.0], out / 'strip.png', lambda t: f'frame {t:.2f}')
    strip([k / 8 for k in range(9)] + [0.5 / 8], out / 'steps.png', lambda t: f'step {t * 8:g}')
    print('wrote', out)


BUILD = {
    'label': "The mushroom stem, top centre: drag for the Upper 8' drawbar; its curled hand unrolls into a long arm that "
             "lifts its blue drop higher each step, then a second arm rises and waves",
    'objectParts': {'drop': ['f285']},
}


def export() -> None:
    import json
    items = hooray_items()
    b = {'label': BUILD['label'],
         'effects': [{'effect': 'sprites', 'place': 'over', 'items': items},
                     {'effect': 'vanish', 'parts': ['drop'], 'span': [0, STEP]}],
         'objectParts': BUILD['objectParts']}
    path = OUT.parent / 'build.json'
    path.write_text(json.dumps(b, indent=2) + '\n')
    print('exported', len(items), 'shapes to', path)


if __name__ == '__main__' and 'build' in __import__('sys').argv[1:]:
    hooray_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    export()
