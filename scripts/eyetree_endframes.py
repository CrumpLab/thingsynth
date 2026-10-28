# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Upper 2' drawbar fully out) for the eye tree: the green teardrop crown on the left with one big
half-lidded eye, a lumpy right edge, and a purple stalk rising into it.

    uv run scripts/eyetree_endframes.py
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
m.CROP = (380, 1650, 1250, 1500)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/upper-db6/endframes'
p, outlined, circle, ellipse, tube, bez, smooth = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, m.smooth
INK = 13
CROWN = ['f117', 'f119', 'f120']
GREEN, LEAF, LIME, OLIVE, BUTTER = '#74E070', '#4FC46A', '#ACE84F', '#68971E', '#FFE47F'
PURPLE, MAGENTA, PINK = '#A434F4', '#F434E6', '#FF89FC'
EYE = (893.0, 2578.0)
TOP = (962.0, 2392.0)  # the crown's crest
TIP = (900.0, 3045.0)  # the crown's bottom point
_AS: Image.Image | None = None


def as_painted() -> Image.Image:
    global _AS
    if _AS is None:
        _AS = m.compose()
    return _AS


def relay(im: Image.Image, ids: list[str]) -> None:
    """The painted shapes `ids` (their fills, pencil and own ink, exactly as painted) laid back on top of `im`. The
    crown's fill is translucent over the wash, so its painted pixels are pasted rather than its fill redrawn."""
    ink = sorted({s for f in ids for s in m.own_ink(f)})
    mask = m.svg(''.join(f'<path d="{m.FILLS[f]}" fill="#fff"/>' for f in ids)
                 + ''.join(f'<path d="{m.INKS[s]}" fill="#fff"/>' for s in ink)).getchannel('A')
    im.paste(as_painted(), (0, 0), mask)


def draw(new: str = '', again: list[str] | None = None, over: str = '') -> Image.Image:
    im = m.compose(front=new or '<g/>')
    if again:
        relay(im, again)
    if over:
        im.alpha_composite(m.svg(over))
    return im


def lumpy(cx, cy, rx, ry, lobes, depth, rot=0.0, seed=0, n=None) -> str:
    """A hand-drawn blob: an ellipse whose rim swells into `lobes` bumps of uneven size."""
    rnd = random.Random(seed)
    n = n or lobes * 4
    ph = [rnd.uniform(0.7, 1.3) for _ in range(lobes)]
    r = math.radians(rot)
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + depth * ph[(i * lobes // n) % lobes] * abs(math.sin(a * lobes / 2)) ** 0.7 + rnd.uniform(-0.03, 0.03)
        x, y = math.cos(a) * rx * k, math.sin(a) * ry * k
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return smooth(pts)


def petal(cx, cy, ang, L, W) -> str:
    """A rounded teardrop petal or feather from (cx, cy) out along `ang` degrees."""
    a = math.radians(ang)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    P = lambda u, v: (cx + ux * u + vx * v, cy + uy * u + vy * v)
    return (f'M{p(*P(0, 0))}C{p(*P(L * 0.2, -W * 0.9))} {p(*P(L * 0.9, -W * 1.1))} {p(*P(L, 0))}'
            f'C{p(*P(L * 0.95, W * 1.0))} {p(*P(L * 0.25, W * 0.95))} {p(*P(0, 0))}Z')


def round_eye(cx, cy, r, look=(0.0, 0.0)) -> str:
    lx, ly = look
    out = outlined(ellipse(cx, cy, r * 0.95, r), '#ffffff', INK)
    out += outlined(circle(cx + lx, cy + ly, r * 0.55), OLIVE, INK * 0.8)
    out += f'<path d="{circle(cx + lx, cy + ly, r * 0.28)}" fill="#000"/>'
    out += f'<path d="{circle(cx + lx + r * 0.18, cy + ly - r * 0.2, r * 0.11)}" fill="#fff"/>'
    return out


def v1_songbird() -> Image.Image:
    """Songbird: the crown turns into a bird's head and body: a big orange beak opens singing out of its left side,
    a magenta wing lifts on its lumpy right, and three candy crest feathers fan up from its top."""
    behind = ''
    for ang, L, col in [(-128, 250, '#FF7FD8'), (-100, 290, '#FFE47F'), (-72, 240, '#7FFFF6')]:
        behind += outlined(petal(TOP[0] + (ang + 100) * 1.2, TOP[1] + 60, ang, L, 62), col, INK)
    wing = smooth([(1110, 2780), (1180, 2600), (1300, 2470), (1450, 2390), (1500, 2420), (1460, 2490), (1500, 2530),
                   (1440, 2600), (1470, 2650), (1390, 2700), (1400, 2760), (1290, 2790), (1200, 2830)])
    behind += outlined(wing, MAGENTA, INK)
    for k, (x, y, a) in enumerate([(1250, 2700, -38), (1300, 2620, -40), (1350, 2540, -42)]):
        behind += outlined(petal(x, y, a, 170 - k * 20, 38), PINK, INK * 0.8)
    # the beak, open, its base tucked behind the crown so it comes out of its edge without a seam
    mouth = 'M780 2580L560 2655L780 2720Z'
    up_f = 'M790 2550C690 2530 590 2550 500 2620C600 2634 700 2638 790 2640Z'
    up_l = 'M790 2550C690 2530 590 2550 500 2620C600 2634 700 2638 790 2640'
    lo_f = 'M790 2660C700 2665 620 2675 545 2700C620 2745 710 2760 790 2750Z'
    lo_l = 'M790 2660C700 2665 620 2675 545 2700C620 2745 710 2760 790 2750'
    beak = f'<path d="{mouth}" fill="#c2185b"/>' + outlined(lo_f, BUTTER, INK, lo_l) + outlined(up_f, '#FF8C24', INK, up_l)
    return draw(behind + beak, CROWN + ['f118'])


def v2_wake_wave() -> Image.Image:
    """Waking and waving: its sleepy eye opens round and two leafy branch arms rise from behind it, one each side,
    lumpy leaf hands up."""
    arms = ''
    for P, hand in [(bez((800, 2760), (700, 2740), (590, 2620), (560, 2440)), (548, 2370)),
                    (bez((1120, 2720), (1240, 2700), (1340, 2590), (1380, 2430)), (1392, 2360))]:
        arms += outlined(tube(P, 44, 36), LEAF, INK)
        arms += outlined(lumpy(*hand, 92, 105, 5, 0.22, rot=-90, seed=int(hand[0])), LIME, INK)
    over = round_eye(EYE[0] - 2, EYE[1], 122, (-28, 8))
    return draw(arms, CROWN + ['f118'], over)


def flower(cx, cy, R, cols, seed, rot=0.0) -> str:
    rnd = random.Random(seed)
    out = ''
    for k in range(5):
        a = rot + k * 72 + rnd.uniform(-8, 8)
        out += outlined(petal(cx, cy, a, R * rnd.uniform(0.92, 1.08), R * 0.55), cols[k % len(cols)], INK)
    out += outlined(lumpy(cx, cy, R * 0.34, R * 0.34, 6, 0.12, seed=seed), '#FFFE7F', INK)
    return out


def v3_blossom() -> Image.Image:
    """In bloom: big candy blossoms burst open all round the crown's edge, with fat buds between them."""
    out = ''
    spots = [((900, 2395), 150, ['#FF7FD8', '#FFA5EA'], 0), ((1120, 2445), 140, ['#FFE47F', '#FFCB7F'], 20),
             ((1215, 2680), 145, ['#7FFFF6', '#AFE6FF'], 40), ((740, 2560), 135, ['#CA47FF', '#FFA5EA'], 30),
             ((790, 2870), 120, ['#FFFE7F', '#FFE47F'], 50)]
    for k, ((x, y), R, cols, rot) in enumerate(spots):
        out += flower(x, y, R, cols, k + 3, rot)
    for x, y, a, col in [(1015, 2370, -75, '#FF89FC'), (760, 2715, 185, '#7FFFF6'), (1170, 2860, 20, '#FF807F')]:
        out += outlined(petal(x, y, a, 150, 62), col, INK)
    return draw(out, [], '')


CROWN_PTS = [(900, 3045), (850, 2960), (790, 2820), (745, 2680), (730, 2580), (750, 2480), (800, 2420), (880, 2388),
             (960, 2385), (1040, 2410), (1072, 2450), (1110, 2462), (1168, 2492), (1148, 2560), (1202, 2610),
             (1150, 2690), (1188, 2748), (1168, 2805), (1110, 2880), (1040, 2960), (960, 3032)]
FOOT = (975.0, 3250.0)


def mini_tree(base: tuple[float, float], s: float, rot: float, fill: str, lid: str, low: str, stem: str, k: int) -> str:
    """The tree redrawn smaller after the painting's own: a teardrop crown lumpy down its right side, the half-lidded
    almond eye, and a stalk rising into it; stood with the stalk's foot on `base`, ink at the full weight."""
    bx, by = base
    tr = f'translate({bx} {by}) rotate({rot}) scale({s}) translate({-FOOT[0]} {-FOOT[1]})'
    w = INK / s
    eye = 'M800 2600C790 2510 850 2462 915 2465C990 2470 1005 2560 990 2610C975 2665 920 2695 870 2690C825 2685 805 2650 800 2600Z'
    lidd = 'M820 2470C860 2520 905 2560 910 2610C915 2660 890 2700 870 2760L1100 2760L1100 2440Z'
    out = f'<g transform="{tr}" stroke="#000" stroke-width="{w:.1f}" stroke-linejoin="round" stroke-linecap="round">'
    out += f'<path d="{smooth(CROWN_PTS)}" fill="{fill}"/>'
    out += f'<clipPath id="eye{k}"><path d="{eye}"/></clipPath>'
    out += f'<path d="{eye}" fill="{low}"/><path d="{lidd}" fill="{lid}" stroke="none" clip-path="url(#eye{k})"/>'
    out += f'<path d="M820 2470C860 2520 905 2560 910 2610C915 2660 890 2720 860 2770" fill="none"/>'
    out += f'<path d="{eye}" fill="none"/>'
    out += f'<path d="{tube([(FOOT[0], FOOT[1]), (985, 2980), (995, 2700)], 44, 34)}" fill="{stem}"/>'
    return out + '</g>'


def v4_octaves() -> Image.Image:
    """Two octaves up: two more of it stack up out of its crest, each smaller and brighter than the one below, like
    the fifteenth sitting two octaves over the fundamental."""
    c2 = mini_tree((965, 2480), 0.58, -5, '#B6F25A', '#7FB52A', '#FFF27A', MAGENTA, 2)
    c3 = mini_tree((930, 2030), 0.37, 6, '#FFF27A', '#E0B92A', '#ffffff', '#FF89FC', 3)
    im = draw(c3 + c2, CROWN + ['f118'])
    return im


def v5_whistle() -> Image.Image:
    """Whistling: a round puckered mouth opens under its eye and a fat curling ribbon of whistle
    streams out to the left with bright bubbles of sound."""
    P = bez((850, 2840), (700, 2900), (530, 2840), (500, 2660), 24)
    P += g.spiral(P[-1][0], P[-1][1], math.radians(-85), 130, 0.55, 0.35, 1, 18)[1:]
    ribbon = ''
    cols = ['#AFE6FF', '#ffffff']
    seg = 6
    for k in range(0, len(P) - seg, seg):
        ribbon += outlined(tube(P[k:k + seg + 1], 60 - 30 * k / len(P), 60 - 30 * (k + seg) / len(P)), cols[(k // seg) % 2], INK)
    for x, y, r, col in [(700, 2520, 72, '#7FFFF6'), (760, 2330, 58, '#FFFE7F'), (590, 2300, 50, '#FF89FC')]:
        ribbon += outlined(lumpy(x, y, r, r, 5, 0.08, seed=int(x)), col, INK)
        ribbon += f'<path d="{ellipse(x - r * 0.3, y - r * 0.35, r * 0.22, r * 0.14, -30)}" fill="#fff"/>'
    mouth = outlined(lumpy(892, 2832, 80, 76, 6, 0.1, seed=4), '#FF5B80', INK) + outlined(circle(894, 2835, 35), '#3a0d2a', INK * 0.7)
    return draw('', [], mouth + ribbon)


VERSIONS = [
    ('1-songbird', 'Songbird', v1_songbird),
    ('2-wake-and-wave', 'Wake and wave', v2_wake_wave),
    ('3-in-bloom', 'In bloom', v3_blossom),
    ('4-two-octaves-up', 'Two octaves up', v4_octaves),
    ('5-whistling', 'Whistling', v5_whistle),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (drawbar in)', as_painted())]
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


# ---- chosen: the songbird, with its eye waking ---------------------------------------------------------------------
# Picked: 1 Songbird with the round waking eye from 2, the beak bigger and open singing, the wing lumpier. Upper 2' is
# a drawbar (0..8), so each step lands one arrival on k/8: three crest feathers one by one (steps 1-3), the upper beak
# (4), the lower beak swinging open with the mouth (5), the wing (6), its feathers (7), the eye waking (8). Crest, beak
# and wing tuck behind the crown: they go in an `around` layer masked by the crown, its eye and the eye tree f118
# in front. The eye goes `over`.
STEP = 1 / 8
AROUND_FRONT = ['f120', 'f118']  # the object's own fills (f117, f119) are masked anyway; these stay in front too


def jitter(pts, amt, seed):
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in pts]


def item(d, fill, edge, at, k0, k1=None, grow='scale', **kw) -> dict:
    """A sprite arriving over steps k0..k1 (in eighths; fractions allowed inside a step)."""
    k1 = k0 + 1 if k1 is None else k1
    it = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
          'start': round(k0 * STEP, 4), 'end': round(k1 * STEP, 4), 'grow': grow}
    it.update(kw)
    return it


def bird_around() -> list[dict]:
    items = []
    # crest: three candy feathers fanning up out of its top, one per step; roots hidden behind the crown
    for k, (ang, L, W, col, seed) in enumerate([(-130, 255, 66, '#FF7FD8', 1), (-100, 300, 70, '#FFE47F', 2), (-70, 250, 64, '#7FFFF6', 3)]):
        root = (TOP[0] + (ang + 100) * 1.3, TOP[1] + 70)
        a = math.radians(ang)
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        P = lambda u, v: (root[0] + ux * u + vx * v, root[1] + uy * u + vy * v)
        side = [(0, -W * 0.45), (L * 0.3, -W * 0.85), (L * 0.62, -W * 1.0), (L * 0.88, -W * 0.7), (L, -W * 0.1),
                (L * 0.95, W * 0.5), (L * 0.7, W * 0.95), (L * 0.38, W * 0.8), (L * 0.1, W * 0.5)]
        d = smooth(jitter([P(u, v) for u, v in side], 7, seed))
        items.append(item(d, col, INK, root, k))
    # the beak: the mouth and the lower half open on step 5, the upper half comes out on step 4
    mouth = smooth(jitter([(800, 2585), (690, 2615), (560, 2660), (520, 2690), (580, 2715), (700, 2725), (800, 2725)], 4, 7))
    lower = smooth(jitter([(810, 2665), (720, 2680), (620, 2705), (535, 2745), (500, 2775), (560, 2800), (660, 2805),
                           (750, 2790), (815, 2770)], 5, 8))
    upper = smooth(jitter([(815, 2530), (740, 2512), (650, 2515), (560, 2535), (475, 2575), (455, 2600), (520, 2630),
                           (620, 2650), (720, 2660), (815, 2655)], 5, 9))
    items.append(item(mouth, '#c2185b', INK, (790, 2660), 4.15, 5))
    items.append(item(lower, BUTTER, INK, (800, 2720), 4, 5))
    items.append(item(upper, '#FF8C24', INK, (800, 2595), 3, 4))
    # nostril dot on the upper beak, small and filled
    items.append(item(ellipse(690, 2575, 18, 11, -12), '#7a3a00', 0, (690, 2575), 3.6, 4))
    # the wing: a lumpy hand-drawn wing lifting out of its right side, high enough to clear the eye tree f118, scalloped along its trailing edge
    wing = smooth(jitter([(1110, 2720), (1115, 2600), (1160, 2490), (1240, 2400), (1330, 2340), (1420, 2302), (1478, 2308),
                          (1470, 2355), (1505, 2390), (1450, 2425), (1480, 2480), (1415, 2510), (1440, 2565), (1365, 2590),
                          (1375, 2650), (1295, 2655), (1270, 2715), (1200, 2710), (1165, 2760)], 9, 11))
    items.append(item(wing, MAGENTA, INK, (1140, 2670), 5, 6))
    # its feathers: three lumpy pink feathers laid along it, back to front, inside step 7
    for k, (x, y, a, L, W) in enumerate([(1215, 2640, -36, 190, 46), (1240, 2550, -38, 200, 44), (1270, 2460, -40, 180, 40)]):
        ar = math.radians(a)
        ux, uy, vx, vy = math.cos(ar), math.sin(ar), -math.sin(ar), math.cos(ar)
        P = lambda u, v: (x + ux * u + vx * v, y + uy * u + vy * v)
        side = [(0, -W * 0.5), (L * 0.35, -W * 0.95), (L * 0.75, -W * 0.85), (L, 0), (L * 0.78, W * 0.8), (L * 0.4, W * 0.95), (0, W * 0.5)]
        d = smooth(jitter([P(u, v) for u, v in side], 5, 20 + k))
        items.append(item(d, PINK, INK * 0.9, (x, y), 6 + k * 0.25, 6.5 + k * 0.25))
    return items


def bird_over() -> list[dict]:
    """The eye wakes on the last step: the white opens from its middle, the iris and pupil arrive, then the glint."""
    cx, cy, r = EYE[0] - 2, EYE[1], 122
    lx, ly = -30, 8
    white = smooth(jitter([(cx + math.cos(a) * r * 0.97, cy + math.sin(a) * r) for a in [i / 12 * 2 * math.pi for i in range(12)]], 4, 30))
    return [
        item(white, '#ffffff', INK, (cx, cy), 7, 7.6, 'y'),
        item(circle(cx + lx, cy + ly, r * 0.55), OLIVE, INK * 0.8, (cx + lx, cy + ly), 7.35, 7.85),
        item(circle(cx + lx, cy + ly, r * 0.28), '#000000', 0, (cx + lx, cy + ly), 7.5, 7.95),
        item(circle(cx + lx + r * 0.18, cy + ly - r * 0.2, r * 0.11), '#ffffff', 0, (cx + lx + r * 0.18, cy + ly - r * 0.2), 7.7, 8),
    ]


def sprites(items, t) -> str:
    """Preview of the app's sprites: the same growth easing as ghost_endframes.sprite_svg, with 'x' and 'y' grows."""
    out = ''
    for it in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - it['start']) / (it['end'] - it['start'])))) ** 3
        if v <= 0.01:
            continue
        x, y = it['at']
        sc = f'{v:.4f} 1' if it['grow'] == 'x' else f'1 {v:.4f}' if it['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def bird_frame(t: float) -> Image.Image:
    im = m.compose()
    if t <= 0:
        return im
    # `around`: above the ink, masked off the object's fills and the front ids (with an ink-wide band round them)
    layer = m.svg(sprites(bird_around(), t))
    ids = ['f117', 'f119'] + AROUND_FRONT
    hole = m.svg('<rect x="0" y="0" width="4950" height="4950" fill="#fff"/>' + ''.join(
        f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in ids)).convert('L')
    from PIL import ImageChops
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), hole))
    im.alpha_composite(layer)
    im.alpha_composite(m.svg(sprites(bird_over(), t)))
    return im


def bird_main() -> None:
    out = OUT.parent / 'songbird'
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()

    def strip(frames, name, sc):
        tiles = [bird_frame(t) for t in frames]
        w, h = tiles[0].size
        tw, th = int(w * sc), int(h * sc)
        im = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        d = ImageDraw.Draw(im)
        for i, (tt, tile) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}', fill='black', font=font)
            im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        im.save(out / name)
        return tiles
    tiles = strip([0, 0.25, 0.5, 0.75, 1.0], 'strip.png', 0.42)
    tiles[-1].save(out / 'end-frame.png')
    strip([k / 8 for k in range(9)], 'steps.png', 0.26)
    print('wrote', out)


if __name__ == '__main__' and 'songbird' in __import__('sys').argv[1:]:
    bird_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The eye tree: drag for the Upper 2' drawbar; it turns into a songbird, one step at a time: crest "
                 'feathers fan up, its beak comes out and opens singing, a lumpy wing lifts and feathers, and its eye wakes last',
        'effects': [
            {'effect': 'sprites', 'place': 'around', 'front': AROUND_FRONT, 'items': bird_around()},
            {'effect': 'sprites', 'place': 'over', 'items': bird_over()},
        ],
    }
    path = ROOT / 'docs/objects/upper-db6/build.json'
    path.write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']) + len(build['effects'][1]['items']), 'shapes to', path)
