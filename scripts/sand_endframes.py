# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Pedal 16' drawbar fully out) for the sandy ground, bottom right: the semi-transparent golden sand
under the creatures there. Most of it is hidden; its one open, characterful part is the dune peak, a sandy triangle
between the fan hand and the big-eye creature's pink snout, its point at about (4020, 2965), with the orange arch
lying across its foot. Every idea lives on that peak and rises up out of it, behind the fan hand, the snout and the
arch (masked by them, as the app's `around` placement does) and in front of the grey band and the blue fish's fins.

    uv run scripts/sand_endframes.py          # the five end frames and sheet
    uv run scripts/sand_endframes.py wake     # the chosen dune wakes: progression strip, steps and end frame
    uv run scripts/sand_endframes.py export   # docs/objects/pedal-db16/build.json
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
m.CROP = (3350, 2330, 1200, 1200)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/pedal-db16/endframes'
p, outlined, circle, tube, bez = m.p, m.outlined, g.circle, g.tube, g.bez
INK = 14
PEAK = (4020.0, 2965.0)
# the painted shapes standing on or in front of the sand that stay in front of anything rising out of it
FAN = ['f071', 'f088', 'f089', 'f090', 'f091']
BIGEYE = ['f176', 'f177', 'f178', 'f239']
ARCH = ['f063', 'f064', 'f065']
SANDS = ['f047', 'f053']  # the sand itself stays in front too: new things rise from behind its crest
KEEP = SANDS + FAN + BIGEYE + ARCH
# a sliver under the crest, between the peak and the snout, that no fill covers (only the wash): kept in front too
CREST_GAP = 'M4015 2968L4185 3040L4270 3090L4270 3330L4015 3330Z'
# the stretch of the long crest stroke (i0045, the big-eye's) that runs on up past the peak to the fish's belly: not
# laid back over the new shapes
INK_CUT = 'M3930 2760L4070 2760L4036 2950L3955 2950Z'
# the sand's own colours, as it shows on the peak (golden sand over the warm wash), and the candy palette
SAND, SAND_LT, SAND_DK = '#F2C27E', '#FBE0A6', '#E7A35E'
PINK, CYAN, YELLOW, LILAC, LIME, ORANGE = '#FF8FB8', '#2DFFF4', '#FFE24A', '#C4A3F0', '#9BE36B', '#FF9F43'


def draw(front: str, keep: list[str] | None = None, over: str = '') -> Image.Image:
    """`front` drawn above the painting but masked by the `keep` fills, whose ink is laid back on top (the app's
    `around`); `over` goes on top of everything."""
    keep = KEEP if keep is None else keep
    holes = ''.join(f'<path d="{m.FILLS[f]}" fill="#000"/>' for f in keep) + f'<path d="{CREST_GAP}" fill="#000"/>'
    ink = ''.join(f'<path d="{m.INKS[s]}"/>' for s in sorted({s for f in keep for s in kept_ink(f)}))
    body = (f'<defs><mask id="k" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect x="0" y="0" width="4950" height="4950" fill="#fff"/>{holes}</mask>'
            f'<mask id="c" maskUnits="userSpaceOnUse" x="0" y="0" width="4950" height="4950">'
            f'<rect x="0" y="0" width="4950" height="4950" fill="#fff"/><path d="{INK_CUT}" fill="#000"/></mask></defs>'
            f'<g mask="url(#k)">{front}</g><g fill="#000" mask="url(#c)">{ink}</g>')
    im = m.compose()
    im.alpha_composite(m.svg(body))
    if over:
        im.alpha_composite(m.svg(over))
    return im


def kept_ink(fid: str) -> list[str]:
    """The ink laid back over the kept fills. The sand's ink list also holds strokes of the shapes round it (the fish's
    fin edge reaching down to the peak), so for the sand only strokes lying within its own box are taken."""
    if fid not in SANDS:
        return m.own_ink(fid)
    x, y, w, h = m.FP[fid]['bbox']
    out = []
    for s in m.FP[fid]['ink']:
        bx, by, bw, bh = m.IP[s]['bbox']
        if bx >= x - 5 and by >= y - 5 and bx + bw <= x + w + 5 and by + bh <= y + h + 5:
            out.append(s)
    return out


def cr(P, closed=True) -> str:
    """A smooth Catmull-Rom curve through the points P."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n if closed else n - 1):
        p0 = P[i - 1] if (closed or i > 0) else P[0]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else P[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + ('Z' if closed else '')


def wobble(P, seed, amt=10.0):
    rnd = random.Random(seed)
    return [(x + (rnd.random() - 0.5) * 2 * amt, y + (rnd.random() - 0.5) * 2 * amt) for x, y in P]


def lump(x, y, rx, ry=None, seed=0, wob=0.12, n=9, rot=0.0) -> str:
    """A lumpy, hand-drawn oval round (x, y), turned by rot degrees."""
    ry = rx if ry is None else ry
    rnd = random.Random(seed)
    a0 = math.radians(rot)
    P = []
    for k in range(n):
        a = k / n * 2 * math.pi + (rnd.random() - 0.5) * 0.3
        f = 1 + (rnd.random() - 0.5) * 2 * wob
        u, v = math.cos(a) * rx * f, math.sin(a) * ry * f
        P.append((x + u * math.cos(a0) - v * math.sin(a0), y + u * math.sin(a0) + v * math.cos(a0)))
    return cr(P)


def open_shape(P, colour, width, seed=0, wob=8.0) -> str:
    """An outlined fill whose outline is left open along its first-to-last edge (where it joins the sand)."""
    P = wobble(P, seed, wob)
    return outlined(cr(P), colour, width, d_line=cr(P, closed=False))


def eye(x, y, r, look=(0.15, 0.1)) -> str:
    out = outlined(lump(x, y, r, r * 0.92, 11, 0.05, 10), '#ffffff', INK * 0.85)
    out += f'<path d="{circle(x + look[0] * r, y + look[1] * r, r * 0.5)}" fill="#2a1b12"/>'
    out += f'<path d="{circle(x + look[0] * r - r * 0.18, y + look[1] * r - r * 0.2, r * 0.15)}" fill="#ffffff"/>'
    return out


# ---- 1. the dune wakes: the peak heaves up into a big sleepy sand creature that opens an eye and hums -------------------
def v1_dune_creature() -> Image.Image:
    P = [(3690, 3330), (3700, 3080), (3730, 2860), (3800, 2700), (3920, 2610), (4050, 2630), (4150, 2720),
         (4210, 2880), (4230, 3060), (4240, 3330)]
    # two stubby sand arms flung up over the crest, behind the body
    out = outlined(tube(bez((3800, 2960), (3700, 2900), (3640, 2800), (3610, 2670), 16), 56, 50), SAND, INK)
    out += outlined(tube(bez((4120, 2860), (4220, 2800), (4250, 2680), (4235, 2560), 16), 54, 48), SAND, INK)
    out += open_shape(P, SAND, INK + 2, 3, 7)
    # wind ripples on its back: lighter lumpy bands, as the painting's sand ridges
    for (x, y, rx, ry, rot, s) in [(3850, 2700, 120, 34, -30, 4), (4120, 2800, 90, 28, 55, 5)]:
        out += outlined(lump(x, y, rx, ry, s, 0.18, 8, rot), SAND_LT, INK * 0.8)
    out += eye(3965, 2790, 82, (0.2, 0.15))
    # a wide round mouth humming the low note, a pink tongue lump inside
    out += outlined(lump(4035, 2915, 56, 62, 9, 0.1, 9, 10), '#7a2140', INK)
    out += f'<path d="{lump(4040, 2945, 32, 19, 10, 0.12, 8)}" fill="{PINK}"/>'
    out += outlined(lump(3870, 2905, 40, 26, 12, 0.15, 8), PINK, INK * 0.7)  # a blush
    return draw(out)


# ---- 2. sandworm: a big candy-banded worm arches up out of the peak and sings --------------------------------------------
def bands(P, w0, w1, cols, every=3) -> str:
    """Outlined bands across a tube, every few samples."""
    n = len(P)
    out = ''
    for i in range(0, n - every, every * 2):
        seg = []
        for j in (i, i + every):
            a, b = P[max(0, j - 1)], P[min(n - 1, j + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1
            nx, ny = -dy / d, dx / d
            w = (w0 + (w1 - w0) * j / (n - 1)) * 1.02
            seg.append(((P[j][0] + nx * w, P[j][1] + ny * w), (P[j][0] - nx * w, P[j][1] - ny * w)))
        (l0, r0), (l1, r1) = seg
        out += outlined(cr([l0, l1, r1, r0]), cols[(i // (every * 2)) % len(cols)], INK * 0.8)
    return out


def v2_sandworm() -> Image.Image:
    P = bez((4000, 3200), (4010, 2870), (3960, 2640), (3760, 2600), 36)
    out = outlined(tube(P, 82, 74), PINK, INK)
    out += bands(P[:-5], 82, 74, [YELLOW, CYAN], 3)
    hx, hy = 3700, 2610
    out += outlined(lump(hx, hy, 125, 112, 21, 0.08, 10, -15), PINK, INK)
    out += eye(hx + 20, hy - 40, 50, (-0.3, -0.1))
    out += outlined(lump(hx - 75, hy + 40, 44, 52, 22, 0.1, 9, 20), '#7a2140', INK * 0.9)  # singing
    out += f'<path d="{lump(hx - 72, hy + 62, 26, 16, 23, 0.12, 8)}" fill="#ff5e7a"/>'
    return draw(out)


# ---- 3. big foot: Pedal is a foot; a giant sandy foot pushes up out of the dune, toes spread ------------------------------
def v3_big_foot() -> Image.Image:
    ox, oy, rot, k = 3960, 3250, -8, 1.15
    a = math.radians(rot)
    R = lambda u, v: (ox + k * (u * math.cos(a) - v * math.sin(a)), oy + k * (u * math.sin(a) + v * math.cos(a)))
    sole = [R(*q) for q in [(-105, 0), (-115, -150), (-90, -300), (-140, -440), (-150, -540), (-80, -600), (40, -605),
                            (135, -560), (160, -460), (120, -310), (115, -150), (110, 0)]]
    out = outlined(cr(wobble(sole, 7, 5)), SAND, INK + 2)
    for j, (u, v, r) in enumerate([(-100, -640, 66), (-5, -672, 50), (64, -660, 44), (118, -626, 39), (156, -570, 34)]):
        tx, ty = R(u, v)
        out += outlined(lump(tx, ty, r * k, r * k * 1.28, 40 + j, 0.07, 9, rot), SAND, INK)
        nx, ny = R(u, v - r * 0.55)
        out += outlined(lump(nx, ny, r * k * 0.58, r * k * 0.5, 50 + j, 0.1, 8, rot), PINK, INK * 0.7)
    return draw(out)


# ---- 4. sand castle: the peak builds itself into a lumpy dribble castle flying candy pennants ----------------------------
def turret(x0, x1, top, seed, col=SAND) -> str:
    """A lumpy sand tower with three merlons, rising from behind the crest."""
    w = x1 - x0
    P = [(x0 + 8, 3250), (x0, top + 120), (x0 - 12, top + 40), (x0 - 8, top - 30), (x0 + w * 0.28, top - 30),
         (x0 + w * 0.3, top + 10), (x0 + w * 0.38, top + 12), (x0 + w * 0.38, top - 32), (x0 + w * 0.62, top - 32),
         (x0 + w * 0.62, top + 12), (x0 + w * 0.7, top + 10), (x0 + w * 0.72, top - 30), (x1 + 8, top - 30),
         (x1 + 12, top + 40), (x1, top + 120), (x1 - 8, 3250)]
    out = outlined(cr(wobble(P, seed, 5)), col, INK)
    out += outlined(lump((x0 + x1) / 2, top + 120, w * 0.13, w * 0.24, seed * 5, 0.08, 9), '#5a2a1a', INK * 0.8)  # a window
    return out


def pennant(x, y, h, col, seed) -> str:
    out = outlined(tube([(x, y), (x + 2, y - h)], 9, 8), '#a4763e', INK * 0.7)
    fx, fy = x + 4, y - h + 8
    out += outlined(cr(wobble([(fx, fy), (fx + 150, fy + 40), (fx, fy + 95)], seed, 6)), col, INK * 0.8)
    return out


def v4_sand_castle() -> Image.Image:
    out = outlined(cr(wobble([(3760, 3250), (3750, 2850), (4180, 2850), (4170, 3250)], 4, 6)), SAND_DK, INK)  # the wall
    out += turret(3640, 3800, 2730, 1)
    out += turret(4100, 4240, 2770, 2)
    out += turret(3860, 4060, 2580, 3, SAND_LT)
    out += pennant(3960, 2552, 150, PINK, 7) + pennant(3720, 2702, 120, CYAN, 8) + pennant(4170, 2742, 120, YELLOW, 9)
    return draw(out)


# ---- 5. desert bloom: a big friendly cactus comes up out of the dune, arms raised, and candy flowers open ----------------
def flower(x, y, r, petal, seed) -> str:
    out = ''
    for k in range(6):
        a = k / 6 * 2 * math.pi + seed
        out += outlined(lump(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75, r * 0.55, r * 0.42, seed * 9 + k, 0.1, 8,
                             math.degrees(a)), petal, INK * 0.75)
    out += outlined(lump(x, y, r * 0.45, None, seed * 3, 0.1, 8), YELLOW, INK * 0.75)
    return out


def v5_desert_bloom() -> Image.Image:
    G, G2 = '#7FD36B', '#B4F08F'
    out = ''
    # a round barrel cactus beside it, on the right of the peak
    out += outlined(lump(4130, 2930, 95, 115, 61, 0.1, 10), G, INK)
    out += outlined(lump(4110, 2930, 30, 85, 62, 0.15, 8), G2, INK * 0.7)
    out += flower(4135, 2805, 62, LILAC, 3)
    trunk = [(3945, 3330), (3940, 3000), (3930, 2800), (3925, 2650)]
    armL = bez((3935, 2960), (3800, 2975), (3770, 2900), (3775, 2770), 16)
    armR = bez((3935, 2900), (4040, 2905), (4060, 2830), (4055, 2730), 16)
    for P, w0, w1 in [(armL, 45, 42), (armR, 42, 40)]:
        out += outlined(tube(P, w0, w1), G, INK)
    out += outlined(tube(bez(*trunk, 20), 74, 66), G, INK)
    for P, w0, w1 in [(armL, 45, 42), (armR, 42, 40)]:  # melt the joins
        out += f'<path d="{tube(P[3:], w0 - INK / 2, w1 - INK / 2)}" fill="{G}"/>'
    out += f'<path d="{tube(bez(*trunk, 20), 74 - INK / 2, 66 - INK / 2)}" fill="{G}"/>'
    out += outlined(lump(3925, 2830, 22, 120, 63, 0.12, 9), G2, INK * 0.7)  # a pale rib
    out += flower(3925, 2610, 78, PINK, 1) + flower(3775, 2745, 50, ORANGE, 2) + flower(4055, 2705, 50, CYAN, 4)
    return draw(out)


VERSIONS = [
    ('1-dune-creature', 'The dune wakes', v1_dune_creature),
    ('2-sandworm', 'Sandworm', v2_sandworm),
    ('3-big-foot', 'Big foot', v3_big_foot),
    ('4-sand-castle', 'Sand castle', v4_sand_castle),
    ('5-desert-bloom', 'Desert bloom', v5_desert_bloom),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (16\' in)', m.compose())]
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


# ---- chosen: the dune wakes ----------------------------------------------------------------------------------------
# Picked under 5a, with a little of desert bloom: the dune's peak heaves up into a big sand creature that wakes, flings
# up its arms and hums the low note, and candy flowers pop open on its crown last. One arrival per drawbar step:
#   1 the hump rises from behind the crest      2 its crown heaves up on top, with wind ripples
#   3 its left arm goes up                       4 its right arm goes up
#   5 a sleepy, half-lidded eye opens            6 the lid lifts: wide awake
#   7 its mouth opens, humming, with a blush     8 three candy flowers pop open on its crown
# All `around`: masked off the sand itself, the fan hand, the big-eye and the arch (with the app's ink-wide band), so
# it rises from behind the dune's crest. The long crest stroke that ran on up past the peak to the fish's belly is
# covered by the hump (around draws above the ink), and the red under the snout's lip, which no fill covers, is kept
# clear by tucking the hump's lower right in under the crest.
STEP = 1 / 8
BODY_AT = (3960.0, 3120.0)
EYE_C, EYE_R = (3965.0, 2790.0), 82.0


def it(d, fill, edge, at, s, e, grow='scale', out=None) -> dict:
    o = {'d': d, 'fill': fill, 'edge': round(edge, 1), 'at': [round(at[0], 1), round(at[1], 1)],
         'start': round(s, 4), 'end': round(min(1.0, e), 4), 'grow': grow}
    if out:
        o['outStart'], o['outEnd'] = round(out[0], 4), round(min(1.0, out[1]), 4)
    return o


def lumpy_tube(P, w0, w1, seed, wob=7.0) -> str:
    """A chunky stub along the centreline P: lumpy sides and a round, lumpy end (no straight vector edges)."""
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
    dx, dy = ex - P[-2][0], ey - P[-2][1]
    d = math.hypot(dx, dy) or 1
    tx, ty, nx, ny = dx / d, dy / d, -dy / d, dx / d
    cap = [(ex + nx * w1 * math.cos(a) + tx * w1 * 1.1 * math.sin(a), ey + ny * w1 * math.cos(a) + ty * w1 * 1.1 * math.sin(a))
           for a in (math.radians(45), math.radians(90), math.radians(135))]
    pts = L[::3] + [L[-1]] + cap + [R[-1]] + R[::-3]
    return cr(wobble(pts, seed, wob))


BODY_P = [(3690, 3330), (3700, 3080), (3725, 2890), (3790, 2770), (3930, 2725), (4075, 2745), (4165, 2830), (4212, 2950),
          (4222, 3060), (4150, 3118), (4045, 3150), (3995, 3330)]


def body_d(inset: float = 0.0) -> str:
    """The hump. Its lower right tucks in under the crest rather than running down past the snout's lip, where the red
    under the lip is wash with no fill over it (the around mask would not hide the hump there)."""
    P = wobble(BODY_P, 3, 7)
    if inset:
        cx, cy = 3960.0, 3000.0
        P = [(x + (cx - x) * inset / math.hypot(cx - x, cy - y), y + (cy - y) * inset / math.hypot(cx - x, cy - y)) for x, y in P]
    return cr(P)


def crown_d() -> str:
    P = [(3770, 2800), (3790, 2690), (3870, 2615), (3975, 2595), (4075, 2625), (4135, 2700), (4140, 2800), (3950, 2850)]
    return cr(wobble(P, 13, 7))


ARM_L = bez((3800, 2900), (3720, 2850), (3655, 2760), (3630, 2650), 15)
ARM_R = bez((4120, 2860), (4180, 2780), (4200, 2680), (4190, 2580), 15)


def flower_items(x, y, r, petal, seed, s) -> list[dict]:
    out = []
    for k in range(6):
        a = k / 6 * 2 * math.pi + seed
        px, py = x + math.cos(a) * r * 0.72, y + math.sin(a) * r * 0.72
        out.append(it(lump(px, py, r * 0.52, r * 0.4, seed * 9 + k, 0.1, 8, math.degrees(a)), petal, INK * 0.8,
                      (x, y), s + 0.004 * k, s + 0.07 + 0.004 * k))
    out.append(it(lump(x, y, r * 0.44, None, seed * 3, 0.1, 8), YELLOW, INK * 0.8, (x, y), s + 0.03, s + 0.1))
    return out


def wake_items() -> list[dict]:
    S = STEP
    E = INK - 1  # inset for the fill-only layers that melt the joins
    items = []
    # outlined layers: arms, crown, body (each later one over the earlier)
    items.append(it(lumpy_tube(ARM_L, 62, 56, 21), SAND, INK, ARM_L[0], 2 * S, 3 * S))
    items.append(it(lumpy_tube(ARM_R, 60, 54, 22), SAND, INK, ARM_R[0], 3 * S, 4 * S))
    items.append(it(crown_d(), SAND, INK + 2, (3955, 2800), 1 * S, 2 * S))
    items.append(it(body_d(), SAND, INK + 2, BODY_AT, 0, 1 * S, 'y'))
    # fill-only layers over them: the arms over the body's edge where they leave it, then crown and body melted together
    items.append(it(lumpy_tube(ARM_L[:6], 62 - E / 2, 60 - E / 2, 21, 0), SAND, 0, ARM_L[0], 2 * S, 3 * S))
    items.append(it(lumpy_tube(ARM_R[:6], 60 - E / 2, 58 - E / 2, 22, 0), SAND, 0, ARM_R[0], 3 * S, 4 * S))
    crown_in = cr(wobble([(3790, 2800), (3805, 2700), (3880, 2630), (3975, 2612), (4068, 2640), (4120, 2705), (4122, 2800),
                          (3950, 2835)], 13, 2))
    body_in = body_d(E / 2 + 2)
    items.append(it(body_in, SAND, 0, BODY_AT, 0, 1 * S, 'y'))
    items.append(it(crown_in, SAND, 0, (3955, 2800), 1 * S, 2 * S))
    # wind ripples on its back, with the crown
    items.append(it(lump(3860, 2690, 115, 32, 4, 0.18, 8, -28), SAND_LT, INK * 0.8, (3860, 2690), 1.3 * S, 2 * S))
    items.append(it(lump(4110, 2790, 80, 26, 5, 0.18, 8, 62), SAND_LT, INK * 0.8, (4110, 2790), 1.5 * S, 2 * S))
    # the eye: open at step 5 under a heavy sleepy lid, which lifts away at step 6
    (ex, ey), r = EYE_C, EYE_R
    items.append(it(lump(ex, ey, r, r * 0.92, 11, 0.05, 10), '#ffffff', INK * 0.85, EYE_C, 4 * S, 5 * S))
    items.append(it(circle(ex + 0.18 * r, ey + 0.2 * r, r * 0.5), '#2a1b12', 0, EYE_C, 4.2 * S, 5 * S))
    items.append(it(circle(ex + 0.18 * r - r * 0.18, ey + 0.2 * r - r * 0.2, r * 0.15), '#ffffff', 0, EYE_C, 4.4 * S, 5 * S))
    lid = cr(wobble([(ex - r - 12, ey + 6), (ex - r * 0.9, ey - r * 0.6), (ex - r * 0.3, ey - r - 14), (ex + r * 0.4, ey - r - 12),
                     (ex + r * 0.95, ey - r * 0.5), (ex + r + 12, ey + 10), (ex + r * 0.4, ey + 24), (ex - r * 0.4, ey + 22)], 17, 3))
    items.append(it(lid, SAND_DK, INK * 0.85, (ex, ey - r - 10), 4 * S, 5 * S, 'y', (5 * S, 6 * S)))
    # the mouth opens, humming the low note, with a blush
    items.append(it(lump(4035, 2915, 56, 62, 9, 0.1, 9, 10), '#7a2140', INK, (4035, 2915), 6 * S, 7 * S))
    items.append(it(lump(4040, 2945, 32, 19, 10, 0.12, 8), PINK, 0, (4040, 2945), 6.3 * S, 7 * S))
    items.append(it(lump(3870, 2895, 42, 27, 12, 0.15, 8), PINK, INK * 0.7, (3870, 2895), 6.3 * S, 7 * S))
    # three candy flowers pop open on its crown, smaller than it by far
    for (x, y, r, col, sd, s) in [(3870, 2625, 50, PINK, 1, 7 * S), (3985, 2588, 58, CYAN, 2, 7.25 * S), (4085, 2630, 46, LILAC, 3, 7.5 * S)]:
        items += flower_items(x, y, r, col, sd, s)
    return items


def spr(items, t) -> str:
    """The app's drawSprites: ease-out cubic growth over each item's window, `x`/`y`/scale about its point."""
    e3 = lambda u: 1 - (1 - max(0.0, min(1.0, u))) ** 3
    out = ''
    for q in items:
        v = e3((t - q['start']) / max(1e-6, q['end'] - q['start']))
        if 'outStart' in q:
            v *= 1 - e3((t - q['outStart']) / max(1e-6, q['outEnd'] - q['outStart']))
        if v <= 0.01:
            continue
        x, y = q['at']
        sc = f'{v:.4f} 1' if q['grow'] == 'x' else f'1 {v:.4f}' if q['grow'] == 'y' else f'{v:.4f}'
        stroke = f' stroke="#000" stroke-width="{q["edge"]}" stroke-linejoin="round"' if q['edge'] > 0 else ''
        out += f'<path d="{q["d"]}" fill="{q["fill"]}"{stroke} transform="translate({x} {y}) scale({sc}) translate({-x} {-y})"/>'
    return out


def wake_frame(t: float) -> Image.Image:
    from PIL import ImageChops
    im = m.compose()
    if t <= 0:
        return im
    # `around`, as the app does it: above the ink, masked off the object's fills and the front ids with an ink-wide band
    layer = m.svg(spr(wake_items(), t))
    hole = m.svg('<rect x="0" y="0" width="4950" height="4950" fill="#fff"/>' + ''.join(
        f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>' for f in KEEP)).convert('L')
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), hole))
    im.alpha_composite(layer)
    return im


def wake_main() -> None:
    out = OUT.parent / 'dune-wakes'
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()

    def strip(frames, name, sc):
        tiles = [wake_frame(t) for t in frames]
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


if __name__ == '__main__' and 'wake' in __import__('sys').argv[1:]:
    wake_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The sandy ground: drag for the Pedal 16' drawbar; its dune wakes up one step at a time: a big sand "
                 'creature heaves up from behind the crest, flings up its arms, opens a sleepy eye and then wide, hums '
                 'the low note, and candy flowers pop open on its crown',
        'effects': [
            {'effect': 'sprites', 'place': 'around', 'front': FAN + BIGEYE + ARCH, 'items': wake_items()},
        ],
    }
    path = OUT.parent / 'build.json'
    path.write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(build['effects'][0]['items']), 'shapes to', path)
