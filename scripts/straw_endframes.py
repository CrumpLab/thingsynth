# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (upper drawbar 1 3/5', the tierce, fully out) for the straw creature, top right: a see-through
lavender body under a tan one-eyed head in an orange collar, a round bulb that runs down into a long tail pooling on
the saucer, with a straw crossing it and a pink-and-yellow egg in front.

    uv run scripts/straw_endframes.py
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
m.CROP = (3600, 380, 1250, 1600)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/upper-db7/endframes'
p, outlined, circle, tube, bez, spiral = m.p, m.outlined, g.circle, g.tube, g.bez, g.spiral
INK = 15
LAV, LAV_D, LAV_L = '#a99fff', '#8a7ff0', '#cdc6ff'
PINK, YEL, CYAN, LILAC, ORANGE, GREEN, TEAL = '#f64c76', '#ffe066', '#2DFFF4', '#c4a3f0', '#ff9f43', '#7fd36b', '#5cc28a'
CANDY = ['#ff9fc4', YEL, '#7fe0c8', LILAC, ORANGE, '#ff6b8a', CYAN, '#b6ff8f']
HEAD = ['f195', 'f196', 'f197', 'f198', 'f199', 'f200']  # the collar, head, mouth, ears: in front of new things
EGG = ['f188', 'f189']
BULB = (4170.0, 990.0)
POOL = (4317.0, 1663.0)


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


def lumpy(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.035, lumps=3, n=40) -> str:
    """A hand-drawn oval: uneven, slightly bumpy, rotated `rot` degrees."""
    rnd = random.Random(seed)
    ph = [rnd.random() * 6.28 for _ in range(2)]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        k = 1 + amt * math.sin(lumps * t + ph[0]) + amt * 0.5 * math.sin(2 * t + ph[1]) + amt * 0.25 * math.sin(7 * t + ph[0])
        x, y = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + c * x - s * y, cy + s * x + c * y))
    return m.smooth(pts)


def leaf(base, tip, w, bend=0.0, seed=0) -> str:
    """A lumpy pointed leaf (or reed blade) from base to tip, widest a third of the way, bent sideways by `bend`."""
    bx, by = base
    tx, ty = tip
    L = math.hypot(tx - bx, ty - by)
    ux, uy = (tx - bx) / L, (ty - by) / L
    nx, ny = -uy, ux
    rnd = random.Random(seed)
    left, right = [], []
    n = 14
    for i in range(n + 1):
        u = i / n
        off = bend * math.sin(math.pi * u) * L
        half = w * (math.sin(math.pi * min(1, u * 1.35)) ** 0.8 if u < 0.37 else (1 - u) / 0.63) * (1 + 0.06 * rnd.uniform(-1, 1))
        half = max(half, 0.0)
        cx, cy = bx + ux * L * u + nx * off, by + uy * L * u + ny * off
        left.append((cx + nx * half, cy + ny * half))
        right.append((cx - nx * half, cy - ny * half))
    pts = left + right[::-1][1:-1]
    return m.smooth(pts)


def wedge(cx, cy, r0, r1, a0, a1, n=12) -> str:
    A = [math.radians(a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    outer = [(cx + math.cos(a) * r1, cy + math.sin(a) * r1) for a in A]
    inner = [(cx + math.cos(a) * r0, cy + math.sin(a) * r0) for a in A[::-1]]
    return 'M' + 'L'.join(p(*q) for q in outer + inner) + 'Z'


def open_tube(P, w0, w1) -> tuple[str, str]:
    """A tube's fill and its outline left open at the root, so it joins whatever it grows out of without a seam."""
    d = tube(P, w0, w1)
    return d, d[:-1]


def mitten(cx, cy, r, ang, colour, seed, side=1) -> str:
    """A big round hand: a lumpy palm with a thumb, pointing along `ang` degrees."""
    a = math.radians(ang)
    tx, ty = cx + math.cos(a + 1.2 * side) * r * 0.9, cy + math.sin(a + 1.2 * side) * r * 0.9
    out = outlined(lumpy(tx, ty, r * 0.5, r * 0.32, ang + 70 * side, seed + 1), colour, INK * 0.9)
    out += outlined(lumpy(cx, cy, r, r * 0.82, ang, seed), colour, INK)
    return out


def crescent(cx, cy, r, a0, a1, w) -> str:
    n = 24
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        th = w * math.sin(math.pi * t) ** 0.9
        outer.append((cx + math.cos(a) * (r + th / 2), cy + math.sin(a) * (r + th / 2)))
        inner.append((cx + math.cos(a) * (r - th / 2), cy + math.sin(a) * (r - th / 2)))
    return outlined('M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z', '#ffffff', INK * 0.75)


# ---- the five ------------------------------------------------------------------------------------------------------

def cattail(base, top, head_len, head_w, colour, seed, bend=0.0) -> str:
    """A cattail: a slim outlined stem and a fat velvet head near its top, with a little spike."""
    bx, by = base
    tx, ty = top
    P = bez(base, (bx + (tx - bx) * 0.3 + bend, by + (ty - by) * 0.35), (bx + (tx - bx) * 0.75 + bend * 0.5, by + (ty - by) * 0.7), top, 20)
    out = outlined(tube(P, 16, 11), '#6cc35b', INK * 0.8)
    a = math.atan2(P[-1][1] - P[-4][1], P[-1][0] - P[-4][0])
    hx, hy = tx - math.cos(a) * head_len * 0.55, ty - math.sin(a) * head_len * 0.55
    out += outlined(lumpy(hx, hy, head_len / 2, head_w / 2, math.degrees(a), seed, amt=0.04), colour, INK)
    sx, sy = tx + math.cos(a) * 40, ty + math.sin(a) * 40
    out += outlined(tube([(tx - math.cos(a) * 10, ty - math.sin(a) * 10), (sx, sy)], 10, 6), '#6cc35b', INK * 0.7)
    return out


def v1_reeds() -> Image.Image:
    """Reeds (the tierce's reedy colour): a clump of reeds and fat candy cattails comes up out of its pool on the
    saucer, spreading to both sides of its tail."""
    out = ''
    # blades first (behind), then cattails
    blades = [((4205, 1680), (3900, 1250), 62, 0.06), ((4235, 1700), (4060, 1130), 54, -0.05),
              ((4440, 1680), (4545, 1060), 56, 0.06), ((4420, 1700), (4500, 1330), 50, -0.08)]
    for k, (b, t, w, bend) in enumerate(blades):
        out += outlined(leaf(b, t, w, bend, k), [GREEN, TEAL][k % 2], INK)
    cats = [((4195, 1700), (3960, 1330), 270, 78, ORANGE, -40), ((4230, 1710), (4130, 1180), 250, 74, PINK, -30),
            ((4445, 1700), (4520, 1180), 260, 76, '#a4763e', 25)]
    for k, (b, t, hl, hw, col, bend) in enumerate(cats):
        out += cattail(b, t, hl, hw, col, 10 + k, bend)
    return draw(out, EGG)


def v2_waving() -> Image.Image:
    """Waving: two lavender arms reach up out of its round body, either side of its head, big pink hands waving."""
    out = ''
    L = bez((4030, 1010), (3900, 980), (3820, 900), (3800, 760), 24)
    R = bez((4320, 960), (4430, 930), (4480, 840), (4470, 710), 24)
    for P in (L, R):
        f, line = open_tube(P, 52, 44)
        out += outlined(f, LAV, INK, line)
    out += mitten(3800, 690, 105, -100, '#ff9fc4', 3)
    out += mitten(4470, 625, 105, -80, '#ff9fc4', 7, side=-1)
    out += crescent(4470, 625, 170, -75, -30, 30)
    return draw(out, HEAD + EGG)


def v3_bloom() -> Image.Image:
    """Bloom: a ring of big candy petals opens behind its head and collar, and two broad leaves unfurl from its tail,
    so the whole creature becomes a flower on a stem."""
    cx, cy = 4200.0, 690.0
    out = ''
    angs = [150 + k * (240 / 7) for k in range(8)]
    for k, a in enumerate(angs):
        r = math.radians(a)
        mx, my = cx + math.cos(r) * 290, cy + math.sin(r) * 290
        out += outlined(lumpy(mx, my, 190, 95, a, 30 + k, amt=0.05), CANDY[k], INK)
    out += outlined(leaf((4420, 1330), (4700, 1150), 85, 0.12, 4), GREEN, INK)
    out += outlined(leaf((4330, 1560), (4040, 1520), 80, -0.15, 5), TEAL, INK)
    return draw(out, HEAD + EGG)


def v4_seahorse() -> Image.Image:
    """Seahorse: its body turns into a lavender seahorse: a striped candy fin fans
    from its back, plates ridge its tail and the tail's end curls up out of the pool into a spiral."""
    out = ''
    # fin: candy wedges fanning from the bulb's right side
    fx, fy = 4330.0, 1010.0
    cols = [PINK, YEL, CYAN, LILAC, ORANGE]
    for k in range(5):
        a0, a1 = -70 + k * 26, -70 + (k + 1) * 26
        out += outlined(wedge(fx, fy, 30, 250 + 25 * math.sin(k * 1.7), a0, a1), cols[k], INK)
    # tail plates
    for k, (x, y) in enumerate([(4430, 1230), (4425, 1340), (4395, 1450), (4385, 1560)]):
        out += outlined(leaf((x - 20, y), (x + 150, y + 30), 62, -0.08, 60 + k), [PINK, YEL, CYAN, LILAC][k], INK)
    # the curled tail tip coming out of the pool
    P = spiral(4425, 1690, math.radians(-15), 108, 1.15, 0.75, -1, 60)
    f, line = open_tube(P, 46, 18)
    out += outlined(f, LAV, INK, line)
    return draw(out, HEAD + EGG)


def open_curve(pts, per=10) -> list[tuple[float, float]]:
    """Points along an open Catmull-Rom curve through `pts`."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(per):
            u = j / per
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u ** 3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def v5_crazy_straw() -> Image.Image:
    """Crazy straw: its straw grows out of the body into a big candy-striped crazy straw that loops the loop twice
    over the pyramid and comes back up into its mouth."""
    # a short lead out of the painted straw's open top, then two loops (a prolate cycloid) climbing up and left over
    # the pyramid, then a swing back right into its mouth
    lead = bez((4203, 1000), (4170, 950), (4120, 890), (4040, 870), 10)[:-1]
    A, B, N = (4040.0, 870.0), (3740.0, 700.0), 2
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
    nx, ny = uy, -ux
    a = L / (2 * math.pi * N)
    bb = 3.3 * a
    loop = []
    for i in range(1, 121):
        t = i / 120 * 2 * math.pi * N
        along, side = a * t - bb * math.sin(t), bb * (1 - math.cos(t))
        loop.append((A[0] + ux * along + nx * side, A[1] + uy * along + ny * side))
    tail = bez(loop[-1], (3800, 560), (4010, 640), (4150, 735), 24)[1:]
    C = lead + loop + tail
    w = 28
    body = tube(C, w, w)
    out = f'<path d="{body}" fill="#ffffff"/>'
    seg = 6
    for k in range(0, len(C) - seg, seg * 2):
        out += f'<path d="{tube(C[k:k + seg + 1], w, w)}" fill="{PINK}"/>'
    # one outline, left open where it leaves the painted straw so the two join without a seam
    out2 = f'<path d="{body[:-1]}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    return draw(out + out2, ['f197', 'f195'] + EGG)


VERSIONS = [
    ('1-reeds', 'Reeds', v1_reeds),
    ('2-waving', 'Waving', v2_waving),
    ('3-bloom', 'Bloom', v3_bloom),
    ('4-seahorse', 'Seahorse', v4_seahorse),
    ('5-crazy-straw', 'Crazy straw', v5_crazy_straw),
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


# ---- chosen: bloom (3), on its own --------------------------------------------------------------------------------
# The tierce drawbar turns the straw creature into a flower, one thing per step: over step 1 two broad leaves unfurl
# from its tail (the stem), and the first petal opens behind its head; then one big candy petal per step goes round
# the ring, from the lower left over the top to the right, each landing on k/8 and overlapping the one before; the
# eighth lands at full. Placed "around": over the ink, with the body, the head, collar and ears and the egg in front.
EDGE_X = 4545.0  # the painting stops at about x 4570; nothing new goes past this
RING = (4190.0, 790.0)  # behind the collar: the petals grow out from behind the head and collar
TOP_Y = 420.0  # the painting's top edge is at about y 390
FRONT_IDS = HEAD + EGG
STEP = 1 / 8


def petal(cx, cy, ang, r0, length, width, seed) -> str:
    """A big, lumpy, slightly lopsided petal from r0 out to r0 + length along `ang` (degrees): narrow at its root,
    swelling to a broad round end, its two sides bulging differently."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    sk = rnd.uniform(-0.12, 0.12)  # lean of the tip to one side
    n = 14
    side_a, side_b = [], []
    for i in range(n + 1):
        u = i / n
        base = width * (0.28 + 0.72 * (1 - (1 - u) ** 2.2))  # narrow root, broad end
        wa = base * (1 + 0.08 * math.sin(5.0 * u + ph[0]) + 0.05 * math.sin(11 * u + ph[1]))
        wb = base * (1 + 0.08 * math.sin(4.3 * u + ph[2]) + 0.05 * math.sin(9 * u + ph[3]))
        r = r0 + length * u
        off = sk * width * u * u
        x, y = cx + ux * r + nx * off, cy + uy * r + ny * off
        side_a.append((x + nx * wa, y + ny * wa))
        side_b.append((x - nx * wb, y - ny * wb))
    # a round, uneven end: a half-ellipse from one side round to the other
    ex, ey = cx + ux * (r0 + length) + nx * sk * width, cy + uy * (r0 + length) + ny * sk * width
    wa, wb = math.hypot(side_a[-1][0] - ex, side_a[-1][1] - ey), math.hypot(side_b[-1][0] - ex, side_b[-1][1] - ey)
    cap = []
    for j in range(1, 8):
        t = math.pi * j / 8
        rr = (wa if t < math.pi / 2 else wb) * (1 + 0.06 * math.sin(3 * t + ph[1]))
        cap.append((ex + nx * math.cos(t) * rr + ux * math.sin(t) * width * 0.75,
                    ey + ny * math.cos(t) * rr + uy * math.sin(t) * width * 0.75))
    pts = side_a + cap + side_b[::-1]
    root = (cx + ux * r0, cy + uy * r0)
    return m.smooth([root] + pts)


def bloom_items() -> list[dict]:
    it = lambda d, fill, at, s, e: {'d': d, 'fill': fill, 'edge': INK, 'at': [round(at[0], 1), round(at[1], 1)],
                                    'start': round(s, 4), 'end': round(e, 4), 'grow': 'scale'}
    items = []
    # step 1: the leaves unfurl out of the tail, the lower one first
    lb, lt = (4345.0, 1565.0), (4045.0, 1515.0)
    rb, rt = (4415.0, 1300.0), (4540.0, 1065.0)
    items.append(it(leaf(lb, lt, 82, -0.15, 5), TEAL, lb, 0.0, 0.08))
    items.append(it(leaf(rb, rt, 70, 0.10, 4), GREEN, rb, 0.02, 0.1))
    # steps 1..8: one petal each, round the ring from the lower left, over the top, to the right
    cols = ['#ff9fc4', YEL, '#7fe0c8', LILAC, ORANGE, '#ff6b8a', CYAN, '#b6ff8f']
    # six on the roomy left (over the pyramid), two on the narrow right (over the cloud); the head and ears fill
    # the top, where petals would only peep out
    angs = [136, 154, 172, 190, 208, 226, 322, 346]
    cx, cy = RING
    r0, L, W = 90.0, 300.0, 82.0
    for k, ang in enumerate(angs):
        a = math.radians(ang)
        reach = r0 + L + W * 0.75  # centre to the far end of the round tip
        f = 1.0
        if math.cos(a) > 0:  # keep it inside the painting's right edge (its tip, plus its half-width)
            f = min(f, (EDGE_X - cx - W * 0.5) / (reach * math.cos(a)))
        if math.sin(a) < 0:  # and below its top edge
            f = min(f, (cy - TOP_Y - W * 0.5) / (reach * -math.sin(a)))
        # each opens within its own step and lands on it, so a whole step shows whole petals only
        s, e = k * STEP + (0.03 if k == 0 else 0.0), (k + 1) * STEP
        items.append(it(petal(cx, cy, ang, r0 * f, L * f, W * (0.85 + 0.15 * f), 30 + k), cols[k], RING, max(0.0, s), e))
    return items


def around_svg(items, t) -> str:
    """The app's "around" placement: the sprites over the ink, masked where the body and the front shapes are (with a
    band as wide as the ink, so their outlines stay visible)."""
    body = g.sprite_svg(items, t)
    if not body:
        return ''
    x, y, w, h = m.CROP
    holes = ''.join(f'<path d="{m.FILLS[f]}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/>'
                    for f in ['f187'] + FRONT_IDS)
    return (f'<defs><mask id="ar" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/>{holes}</mask></defs><g mask="url(#ar)">{body}</g>')


def bloom_frame(t: float) -> Image.Image:
    im = m.compose()
    layer = around_svg(bloom_items(), t)
    if layer:
        im.alpha_composite(m.svg(layer))
    return im


def bloom_main() -> None:
    m.CROP = (3600, 330, 1250, 1630)  # from just above the painting's top edge, where the upper petals reach
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = OUT.parent / 'bloom'
    out.mkdir(parents=True, exist_ok=True)
    bloom_frame(1.0).save(out / 'end-frame.png')
    for name, frames in (('strip.png', [0, 0.25, 0.5, 0.75, 1.0]), ('steps.png', [k / 8 for k in range(9)])):
        tiles = [bloom_frame(t) for t in frames]
        w, h = tiles[0].size
        sc = 0.42 if len(frames) == 5 else 0.25
        tw, th = int(w * sc), int(h * sc)
        strip = Image.new('RGB', (tw * len(frames) + 10 * (len(frames) + 1), th + 56), 'white')
        try:
            font = ImageFont.load_default(size=22)
        except TypeError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(strip)
        for i, (tt, im) in enumerate(zip(frames, tiles)):
            x = 10 + i * (tw + 10)
            d.text((x, 12), f'frame {tt:.3g}' if len(frames) == 5 else f'step {round(tt * 8)}', fill='black', font=font)
            strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 48))
        strip.save(out / name)
    print('wrote', out)


if __name__ == '__main__' and 'bloom' in __import__('sys').argv[1:]:
    bloom_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    build = {
        'label': "The lavender straw creature: drag for the Upper 1 3/5' drawbar; it becomes a flower: two leaves unfurl "
                 "from its tail, then a big candy petal opens behind its head with every step",
        'effects': [{'effect': 'sprites', 'place': 'around', 'front': FRONT_IDS, 'items': bloom_items()}],
    }
    (OUT.parent / 'build.json').write_text(_j.dumps(build, indent=2) + '\n')
    print('exported', len(bloom_items()), 'shapes to', OUT.parent / 'build.json')
