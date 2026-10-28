# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (Lower 1' drawbar fully out) for the horned creature's collar: the pale pink bell-shaped cape under
the magenta neck ring, top left, with a mint flipper lying across its right side.

    uv run scripts/collar_endframes.py
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
m.CROP = (374, 950, 1150, 1100)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/lower-db9/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 14
PINK, PINK_DEEP, MAGENTA, MINT = '#FFABA7', '#FF7FA8', '#FF38C9', '#72FFD5'
CANDY = ['#ffe066', '#7fe0c8', '#c4a3f0', '#ff9f43', '#2DFFF4', '#f64c76']
CAPE, FLIPPER = 'f251', 'f301'
RING_AND_MASK = ['f288', 'f289', 'f290', 'f296']  # the neck ring and the mask above it, laid back on top
FLIPPER_INK = ['i1477', 'i0636', 'i1478', 'i0637']
NECK = (548.0, 1440.0)  # the middle of the neck ring's bottom


_PLAIN: dict = {}


def cutout(src: Image.Image, fids: list[str]) -> Image.Image:
    """The named painted shapes (fills and their own ink) cut out of a rendering of the painting."""
    body = ''.join(f'<path d="{m.FILLS[f]}" stroke="#000" stroke-width="{INK + 4}" stroke-linejoin="round"/>' for f in fids)
    body += ''.join(f'<path d="{m.INKS[i]}"/>' for f in fids for i in m.own_ink(f))
    layer = src.copy()
    layer.putalpha(m.svg(f'<g fill="#000">{body}</g>').getchannel('A'))
    return layer


def draw(front: str = '', again: list[str] | None = None, over: str = '', fill_colour: dict | None = None,
         hide_ink: list[str] | None = None, patch: str = '') -> Image.Image:
    """New shapes drawn over the painting, then the `again` painted shapes cut out of the painting (with the same
    edits) and laid back on top, so the new parts come out from behind them; `over` goes on top of everything.
    `patch` paints over parts of the painting (scribbles included) before anything new is drawn."""
    kw = dict(fill_colour=fill_colour or {}, ink_over={i: '' for i in hide_ink or []})
    m.FRONT, m.FRONT_INK = [], []
    key = repr(sorted(kw['fill_colour'].items())) + repr(sorted(kw['ink_over'])) + repr(patch)
    if key not in _PLAIN:
        im = m.compose(**kw)
        if callable(patch):
            im = patch(im)
        elif patch:
            im.alpha_composite(m.svg(patch))
        _PLAIN[key] = im
    im = _PLAIN[key].copy()
    if front:
        im.alpha_composite(m.svg(front))
    if again:
        im.alpha_composite(cutout(_PLAIN[key], again))
    if over:
        im.alpha_composite(m.svg(over))
    return im


def sample(points) -> str:
    """The painting's average colour at these canvas points (as painted)."""
    if 'asis' not in _PLAIN:
        _PLAIN['asis'] = m.compose()
    im = _PLAIN['asis']
    x0, y0, w, h = m.CROP
    k = im.size[0] / w
    px = [im.getpixel((round((x - x0) * k), round((y - y0) * k))) for x, y in points]
    return '#' + ''.join(f'{round(sum(c[i] for c in px) / len(px)):02x}' for i in range(3))


def closed(P) -> str:
    """A smooth closed path through the points (Catmull-Rom as cubic Beziers)."""
    n = len(P)
    d = f'M{p(*P[0])}'
    for i in range(n):
        a, b, c, e = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        c1 = (b[0] + (c[0] - a[0]) / 6, b[1] + (c[1] - a[1]) / 6)
        c2 = (c[0] - (e[0] - b[0]) / 6, c[1] - (e[1] - b[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*c)}'
    return d + 'Z'


def place(local, x, y, ang_deg):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x + ca * u - sa * v, y + sa * u + ca * v) for u, v in local]


def lumpy(cx, cy, rx, ry, rot=0.0, seed=0, amp=0.07, n=11):
    rnd = random.Random(seed)
    loc = []
    for k in range(n):
        t = k / n * 2 * math.pi
        r = 1 + (rnd.random() - 0.5) * 2 * amp
        loc.append((math.cos(t) * rx * r, math.sin(t) * ry * r))
    return closed(place(loc, cx, cy, rot))


def petal(x, y, ang, L, w, seed) -> str:
    rnd = random.Random(seed)
    j = lambda v: v * (1 + (rnd.random() - 0.5) * 0.14)
    loc = [(0, -w * 0.22), (L * 0.3, -j(w * 0.48)), (L * 0.68, -j(w * 0.52)), (L * 0.93, -j(w * 0.3)), (L, 0),
           (L * 0.93, j(w * 0.3)), (L * 0.68, j(w * 0.52)), (L * 0.3, j(w * 0.48)), (0, w * 0.22)]
    return closed(place(loc, x, y, ang))


def band_strip(P, widths, cols, ink) -> str:
    """A ribbon along centreline P cut into len(cols) outlined bands, the width varying along it."""
    n = len(P)
    L, R = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = widths(i / (n - 1))
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    out = ''
    k = len(cols)
    for b in range(k):
        i0, i1 = round(b * (n - 1) / k), round((b + 1) * (n - 1) / k)
        poly = L[i0:i1 + 1] + R[i0:i1 + 1][::-1]
        out += outlined('M' + 'L'.join(p(*q) for q in poly) + 'Z', cols[b], ink)
    return out


def crescent(cx, cy, r, ang, thick, seed=0, sweep=35, col='#ffe066') -> str:
    """An outlined crescent (a ring of sound, a swish) round (cx, cy): an arc of radius r centred on angle ang,
    sweep degrees each way, thick at its middle and pointed at its ends."""
    a0, a1, am = math.radians(ang - sweep), math.radians(ang + sweep), math.radians(ang)
    e0 = (cx + math.cos(a0) * r, cy + math.sin(a0) * r)
    e1 = (cx + math.cos(a1) * r, cy + math.sin(a1) * r)
    rin = r - thick
    # the inner edge: a quadratic through the ends whose middle passes rin from the centre
    mid = (cx + math.cos(am) * rin, cy + math.sin(am) * rin)
    ctrl = (2 * mid[0] - (e0[0] + e1[0]) / 2, 2 * mid[1] - (e0[1] + e1[1]) / 2)
    d = f'M{p(*e0)}A{r:.1f} {r:.1f} 0 0 1 {p(*e1)}Q{p(*ctrl)} {p(*e0)}Z'
    return outlined(d, col, INK * 0.8)


def erase(fid: str, within: str, pad: float = 30, blur: float = 26):
    """A patch that paints the shape `fid` out of the painting: its pixels are filled from the surrounding colours
    of the shape `within` (a blur that ignores the hole and the ink), and the pencil scribbles are laid back over."""
    import numpy as np

    def fn(im: Image.Image) -> Image.Image:
        a = lambda body: np.asarray(m.svg(body).getchannel('A')).astype(float) / 255
        hole = a(f'<path d="{m.FILLS[fid]}" fill="#000" stroke="#000" stroke-width="{pad}" stroke-linejoin="round"/>') > 0.02
        ink = a('<g fill="#000" stroke="#000" stroke-width="8">' + ''.join(f'<path d="{d}"/>' for d in m.INKS.values()) + '</g>') > 0.02
        keep = (a(f'<path d="{m.FILLS[within]}" fill="#000"/>') > 0.9) & ~hole & ~ink
        rgb = np.asarray(im.convert('RGB')).astype(float)
        r = blur * im.size[0] / m.CROP[2] * 1.0
        x = np.arange(-int(3 * r), int(3 * r) + 1)
        kern = np.exp(-x * x / (2 * r * r))
        kern /= kern.sum()

        def bl(arr):
            arr = np.apply_along_axis(lambda v: np.convolve(v, kern, mode='same'), 1, arr)
            return np.apply_along_axis(lambda v: np.convolve(v, kern, mode='same'), 0, arr)
        w = bl(keep.astype(float))
        out = rgb.copy()
        for c in range(3):
            v = bl(rgb[..., c] * keep) / np.maximum(w, 1e-4)
            out[..., c] = np.where(hole, v, rgb[..., c])
        res = Image.fromarray(out.clip(0, 255).astype(np.uint8)).convert('RGBA')
        sc = m.SCRIB.copy()
        sc.putalpha(Image.fromarray((np.asarray(m.SCRIB.getchannel('A')) * hole).astype(np.uint8)))
        res.alpha_composite(sc)
        return res
    fn.__name__ = f'erase-{fid}-{within}'
    return fn


def hand(x, y, ang, s=1.0, col=MINT) -> str:
    """A big open mitten hand, wrist at (x, y), pointing along ang (degrees; -90 is up): four round fingers and a
    thumb coming seamlessly out of a lumpy palm."""
    a = ang + 90
    P = lambda u, v: place([(u * s, v * s)], x, y, a)[0]
    palm = lumpy(*P(0, -80), 82 * s, 92 * s, a, 21, 0.05)
    out = outlined(palm, col, INK)
    for k, (u, v, tilt) in enumerate([(-50, -175, -14), (-14, -192, -4), (24, -188, 6), (58, -166, 16)]):
        out += outlined(lumpy(*P(u, v), 25 * s, 50 * s, a + tilt, 30 + k, 0.05), col, INK * 0.9)
    out += outlined(lumpy(*P(-92, -100), 26 * s, 52 * s, a - 50, 40, 0.05), col, INK * 0.9)
    out += f'<path d="{lumpy(*P(0, -80), 72 * s, 82 * s, a, 21, 0.05)}" fill="{col}"/>'
    return out


def mitten(x, y, ang, s=1.0) -> str:
    """A lumpy mitten hand, wrist at (x, y), pointing along ang (degrees; -90 is up): three finger bumps and a
    thumb, one outline."""
    loc = [(-40, 0), (-58, -55), (-100, -80), (-122, -118), (-98, -132), (-66, -112), (-62, -140), (-48, -178),
           (-22, -160), (-6, -196), (24, -196), (34, -168), (52, -186), (74, -160), (72, -100), (60, -45), (40, 0)]
    a = ang + 90
    return closed(place([(u * s, v * s) for u, v in loc], x, y, a))


# ---- the five ------------------------------------------------------------------------------------------------------

def v1_blossom() -> Image.Image:
    """Blossom: the cape opens into a big flower round the creature's neck, eight lumpy pink petals fanning out from
    under the magenta ring (the ring its middle), one petal per drawbar step."""
    x, y = NECK
    angs = [-12, 18, 48, 78, 108, 138, 168, 198]
    out = ''
    for k in list(range(0, 8, 2)) + list(range(1, 8, 2)):
        a = angs[k]
        col = PINK if k % 2 == 0 else PINK_DEEP
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        out += outlined(petal(x, y, a, 310, 210, k), col, INK)
        out += outlined(petal(x + ca * 90, y + sa * 90, a, 170, 64, k + 20), '#ffd6e4', INK * 0.6)
    return draw(out, RING_AND_MASK)


ERASE_FLIPPER = None


def v2_wave() -> Image.Image:
    """Waving: the mint flipper tucked across the cape is an arm; it lifts out of the cape's edge and up, a big
    open mint hand waving at the top with swish crescents either side."""
    global ERASE_FLIPPER
    ERASE_FLIPPER = ERASE_FLIPPER or erase(FLIPPER, CAPE)
    patch = ERASE_FLIPPER
    P = bez((735, 1475), (830, 1450), (900, 1380), (905, 1270), 30)
    arm = outlined(tube(P, 54, 46), MINT, INK)
    hx, hy = P[-1]
    arm += hand(hx, hy + 40, -84, 1.0)
    arm += f'<path d="{tube(P[-8:], 42, 40)}" fill="{MINT}"/>'
    cres = crescent(hx - 10, hy - 110, 175, -160, 36, 1, 28) + crescent(hx - 10, hy - 110, 175, -20, 36, 2, 28)
    return draw(arm, [CAPE, FLIPPER], cres, hide_ink=FLIPPER_INK, patch=patch)


def offset(P, o, taper=None):
    """P moved sideways by o (times taper(u) along it, if given)."""
    n = len(P)
    out = []
    for i, (x, y) in enumerate(P):
        o_i = o * (taper(i / (n - 1)) if taper else 1)
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        out.append((x - dy / d * o_i, y + dx / d * o_i))
    return out


def v3_rainbow() -> Image.Image:
    """Rainbow: a fat candy rainbow pours out from behind the cape's edge, arcs over and lands in a puffy pink
    cloud, one band per drawbar step."""
    P = bez((610, 1530), (800, 1080), (1200, 1000), (1370, 1250), 60)
    tp = lambda u: 0.6 + 0.4 * min(1.0, u / 0.25)
    cols = [MAGENTA, '#f64c76', '#ff9f43', '#ffe066', '#a8ec6b', MINT, '#2DFFF4', '#c4a3f0']
    w = 34
    out = ''
    for j, c in enumerate(cols):
        o1, o2 = -w * 4 + j * w, -w * 4 + (j + 1) * w
        A, B = offset(P, o1, tp), offset(P, o2, tp)
        out += outlined('M' + 'L'.join(p(*q) for q in A + B[::-1]) + 'Z', c, INK * 0.75)
    ex, ey = P[-1]
    cloud = ''
    for k, (dx, dy, r) in enumerate([(-120, 20, 80), (-30, -40, 105), (90, -10, 90), (150, 50, 70), (40, 70, 95), (-90, 80, 75)]):
        cloud += outlined(lumpy(ex + dx, ey + dy, r, r * 0.9, 0, 50 + k, 0.06), '#ffd6e4', INK)
    cloud += f'<path d="{lumpy(ex + 10, ey + 25, 150, 85, 0, 60, 0.04)}" fill="#ffd6e4"/>'
    return draw(out + cloud, [CAPE, FLIPPER] + RING_AND_MASK)


def v4_foot() -> Image.Image:
    """One foot (the 1' drawbar): a big bare pink foot in a candy-striped sock kicks out from under the cape's hem,
    sole to us, toes up."""
    P = bez((600, 1515), (700, 1545), (790, 1560), (850, 1568), 16)
    leg = outlined(tube(P, 42, 44), PINK, INK)
    Q = bez((835, 1575), (870, 1563), (905, 1550), (945, 1530), 16)
    leg += band_strip(Q, lambda u: 50, [MAGENTA, '#ffe066', MAGENTA, '#ffe066'], INK)
    hx, hy = 935.0, 1515.0  # the heel
    toes = ''
    for (dx, dy, r) in [(-70, -255, 44), (-8, -278, 38), (46, -268, 33), (90, -245, 29), (124, -212, 25)]:
        x, y = place([(dx, dy)], hx, hy, 14)[0]
        toes += outlined(lumpy(x, y, r, r * 1.12, 14, int(r), 0.05), PINK, INK)
    sole = closed(place([(-60, 20), (-95, -60), (-105, -150), (-85, -215), (-20, -240), (60, -225), (115, -185),
                          (115, -120), (75, -60), (60, 0), (0, 40)], hx, hy, 14))
    out = leg + toes + outlined(sole, PINK, INK)
    out += outlined(lumpy(*place([(-10, -130)], hx, hy, 14)[0], 48, 70, 14, 9, 0.08), '#ffd6e4', INK * 0.6)
    return draw(out, [CAPE, FLIPPER])


def v5_bell() -> Image.Image:
    """Ringing bell: the bell-shaped cape becomes a big pink bell, swinging a little, a magenta lip round its rim, a
    mint clapper (the flipper's colour) swinging out below and rings of sound going out to the right."""
    cx, cy, tilt = 590.0, 1440.0, -11
    body = place([(-120, -20), (-140, 60), (-165, 150), (-215, 230), (-262, 275), (0, 300), (262, 275), (215, 230),
                  (165, 150), (140, 60), (120, -20), (0, -40)], cx, cy, tilt)
    lip = place([(-270, 262), (-280, 300), (-255, 335), (0, 352), (255, 335), (280, 300), (270, 262), (0, 290)], cx, cy, tilt)
    clap = place([(30, 395)], cx, cy, tilt)[0]
    out = outlined(tube([place([(10, 280)], cx, cy, tilt)[0], clap], 20, 18), '#a4763e', INK)
    out += outlined(lumpy(*clap, 66, 62, 0, 3, 0.05), MINT, INK)
    out += outlined(closed(body), PINK, INK) + outlined(closed(lip), MAGENTA, INK)
    out += outlined(lumpy(*place([(-95, 130)], cx, cy, tilt)[0], 30, 85, tilt - 12, 11, 0.06), '#ffd6e4', INK * 0.6)
    rings = ''.join(crescent(cx + 210, cy + 190, r, -12, 30, k, 46) for k, r in enumerate((140, 220, 300)))
    return draw(out + rings, RING_AND_MASK)


VERSIONS = [
    ('1-blossom', 'Blossom', v1_blossom),
    ('2-wave', 'Waving', v2_wave),
    ('3-rainbow', 'Rainbow', v3_rainbow),
    ('4-one-foot', 'One foot', v4_foot),
    ('5-ringing-bell', 'Ringing bell', v5_bell),
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


# ---- the build: waving ---------------------------------------------------------------------------------------------
# Drawbar steps land on k/8. Step 1: the flipper fades and is painted out (the cape colour patched over it) while the
# first arm segment swings up out of the cape's edge; steps 1-4: the arm rises a segment per step; step 5: the palm;
# step 6: the fingers and thumb open; steps 7-8: a swish crescent flicks out each side of the hand.
# In the app: vanish the `detail` role (the flipper), a cape-coloured patch `under` the object (it fills the flipper's
# notch in the cape and the band its outline leaves), and the
# arm `around` the object (above the ink, the cape and its 44 px outline band in front, so the root stays tucked in).

import re as _re

ARM = bez((735, 1475), (830, 1450), (900, 1380), (905, 1270), 40)
HAND_S = 1.25
VANISH = (0.0, 0.1)


def flipper_patch(pad: float = 15, bins: int = 22) -> str:
    """A lumpy leaf over the flipper and its outline: fitted to the flipper's pixels along its long axis, widened by
    an ink width and a little more."""
    import numpy as np
    x0, y0, w, h = 480, 1400, 340, 220
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}" width="{w}" height="{h}">'
           f'<path d="{m.FILLS[FLIPPER]}" fill="#000"/></svg>')
    a = np.asarray(Image.open(__import__('io').BytesIO(bytes(m.resvg_py.svg_to_bytes(svg_string=doc)))).getchannel('A')) > 128
    ys, xs = np.nonzero(a)
    pts = np.stack([xs + x0 + 0.5, ys + y0 + 0.5], 1)
    c = pts.mean(0)
    u = np.linalg.eigh(np.cov((pts - c).T))[1][:, -1]
    v = np.array([-u[1], u[0]])
    t, n = (pts - c) @ u, (pts - c) @ v
    edges = np.linspace(t.min() - 1, t.max() + 1, bins + 1)
    L, R = [], []
    for k in range(bins):
        sel = (t >= edges[k]) & (t < edges[k + 1])
        if not sel.any():
            continue
        tm = (edges[k] + edges[k + 1]) / 2
        lo, hi = n[sel].min() - pad, n[sel].max() + pad
        L.append(c + u * tm + v * hi)
        R.append(c + u * tm + v * lo)
    head = c + u * (t.min() - pad * 1.8) + v * ((L[0] @ v + R[0] @ v) / 2 - c @ v)
    tail = c + u * (t.max() + pad * 0.6) + v * ((L[-1] @ v + R[-1] @ v) / 2 - c @ v)
    ring = [head] + L + [tail] + R[::-1]
    return closed([tuple(q) for q in ring])


def limb(P, w0, w1) -> str:
    """An outlined-limb outline along P: flat at its start, a round cap at its end (bulging forward)."""
    n = len(P)
    Lp, Rp = [], []
    for i, (x, y) in enumerate(P):
        a, b = P[max(0, i - 1)], P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        wi = w0 + (w1 - w0) * i / (n - 1)
        Lp.append((x + nx * wi, y + ny * wi))
        Rp.append((x - nx * wi, y - ny * wi))
    (ax, ay), (bx, by) = P[-2], P[-1]
    base = math.atan2(by - ay, bx - ax)
    cap = [(bx + math.cos(base + math.pi / 2 - math.pi * k / 10) * w1, by + math.sin(base + math.pi / 2 - math.pi * k / 10) * w1) for k in range(1, 10)]
    return 'M' + 'L'.join(p(*q) for q in Lp + cap + Rp[::-1]) + 'Z'


def patch_colour() -> str:
    """The cape's median painted colour round the flipper (its fill, less the flipper and the ink)."""
    import numpy as np
    if 'asis' not in _PLAIN:
        _PLAIN['asis'] = m.compose()
    im = np.asarray(_PLAIN['asis'].convert('RGB'))
    ink = ''.join(f'<path d="{d}"/>' for d in m.INKS.values())
    cape = np.asarray(m.svg(f'<path d="{m.FILLS[CAPE]}" fill="#000"/>').getchannel('A')) > 200
    away = np.asarray(m.svg(f'<path d="{m.FILLS[FLIPPER]}" fill="#000" stroke="#000" stroke-width="40"/><g fill="#000" stroke="#000" stroke-width="10">{ink}</g>').getchannel('A')) > 10
    x0, y0, w, h = m.CROP
    k = im.shape[1] / w
    near = np.zeros_like(cape)
    near[round((1400 - y0) * k):round((1640 - y0) * k), round((480 - x0) * k):round((830 - x0) * k)] = True
    return '#' + ''.join(f'{int(v):02x}' for v in np.median(im[cape & ~away & near], axis=0))


def crescent_d(cx, cy, r, ang, thick, sweep) -> str:
    a0, a1, am = math.radians(ang - sweep), math.radians(ang + sweep), math.radians(ang)
    e0 = (cx + math.cos(a0) * r, cy + math.sin(a0) * r)
    e1 = (cx + math.cos(a1) * r, cy + math.sin(a1) * r)
    mid = (cx + math.cos(am) * (r - thick), cy + math.sin(am) * (r - thick))
    ctrl = (2 * mid[0] - (e0[0] + e1[0]) / 2, 2 * mid[1] - (e0[1] + e1[1]) / 2)
    return f'M{p(*e0)}A{r:.1f} {r:.1f} 0 0 1 {p(*e1)}Q{p(*ctrl)} {p(*e0)}Z'


def patch_items() -> list[dict]:
    cx, cy = 674.7, 1511.7  # the flipper's centroid
    col = patch_colour()
    return [dict(d=flipper_patch(), fill=col, edge=0, at=[cx, cy], start=VANISH[0], end=VANISH[1], grow='scale'),
            dict(d=lumpy(536, 1576, 34, 30, -25, 3, 0.05), fill=col, edge=0, at=[cx, cy], start=VANISH[0], end=VANISH[1], grow='scale')]


def wave_items() -> list[dict]:
    items: list[dict] = []
    n = len(ARM) - 1
    cuts = [round(n * f) for f in (0, 0.34, 0.57, 0.79, 1)]  # the first segment longer: much of it is tucked under the cape
    w = lambda i: 54 - 8 * i / n  # half-width along the arm
    segs = []
    for k in range(4):
        i0, i1 = max(0, cuts[k] - 2), cuts[k + 1]
        segs.append((ARM[i0:i1 + 1], w(i0), w(i1), k / 8, (k + 1) / 8))
    for P, w0, w1, a, b in segs:  # the outlined arm, a segment per step, each swinging out from its start
        items.append(dict(d=limb(P, w0, w1), fill=MINT, edge=INK, at=list(P[0]), start=a, end=b, grow='scale'))
    for P, w0, w1, a, b in segs:  # the same, fill only and an ink width narrower, over the joints
        items.append(dict(d=limb(P, w0 - INK / 2, w1 - INK / 2), fill=MINT, edge=0, at=list(P[0]), start=a, end=b, grow='scale'))
    hx, hy = ARM[-1]
    wx, wy = hx, hy + 40  # the wrist
    s, a = HAND_S, -84 + 90
    Q = lambda u, v: place([(u * s, v * s)], wx, wy, a)[0]
    palm = (Q(0, -80), 84 * s, 92 * s)
    items.append(dict(d=lumpy(*palm[0], palm[1], palm[2], a, 21, 0.06), fill=MINT, edge=INK, at=[wx, wy], start=4 / 8, end=5 / 8, grow='scale'))
    fingers = [(-52, -178, -16, 33, 56, 31), (-15, -196, -5, 34, 60, 32), (24, -191, 6, 33, 57, 33), (60, -168, 17, 30, 50, 34)]
    for u, v, tilt, rx, ry, seed in fingers:
        base = Q(u * 0.75, -110)
        items.append(dict(d=lumpy(*Q(u, v), rx * s, ry * s, a + tilt, seed, 0.1), fill=MINT, edge=INK, at=list(base), start=5 / 8, end=6 / 8, grow='scale'))
    items.append(dict(d=lumpy(*Q(-96, -102), 31 * s, 56 * s, a - 50, 40, 0.1), fill=MINT, edge=INK, at=list(Q(-55, -90)), start=5 / 8, end=6 / 8, grow='scale'))
    items.append(dict(d=lumpy(*palm[0], palm[1] - 10 * s, palm[2] - 10 * s, a, 21, 0.06), fill=MINT, edge=0, at=[wx, wy], start=4 / 8, end=5 / 8, grow='scale'))
    items.append(dict(d=limb(ARM[-8:], w(n - 7) - INK / 2, w(n) - INK / 2), fill=MINT, edge=0, at=[wx, wy], start=4 / 8, end=5 / 8, grow='scale'))
    c = Q(0, -100)
    sx, sy = c[0] + 45, c[1] - 10  # the swishes curve round a point just right of the palm
    for r, th, sw, k in ((150, 34, 58, 6), (215, 28, 48, 7)):  # they flick out on steps 7 and 8, off the mask's side
        items.append(dict(d=crescent_d(sx, sy, r, -12, th, sw), fill='#ffe066', edge=round(INK * 0.8, 1),
                          at=[round(c[0], 1), round(c[1], 1)], start=k / 8, end=(k + 1) / 8, grow='scale'))
    return items


def wave_frame(t: float) -> Image.Image:
    """A frame as the app draws it: the flipper faded by `vanish`, the patch on the object under its ink, the arm
    above the ink with the object's shapes (and a 44 px band round them) in front."""
    if t <= 0:
        return m.compose()
    fade = max(0.0, min(1.0, (t - VANISH[0]) / (VANISH[1] - VANISH[0])))
    obj = m.FILLS[CAPE] + m.FILLS[FLIPPER]
    patch = g.sprite_svg(patch_items(), t)  # `under`: just below the object's fills
    tags = m.FILL_TAGS
    fade_tag = lambda tg: _re.sub(r'fill-opacity="([^"]*)"', lambda q: f'fill-opacity="{float(q.group(1)) * (1 - fade):.3f}"', tg)
    m.FILL_TAGS = [fade_tag(tg) if f'id="{FLIPPER}"' in tg else (patch + tg) if f'id="{CAPE}"' in tg else tg for tg in tags]
    gone = [i for i in m.FP[FLIPPER]['ink'] if i in FLIPPER_INK or m.IP[i]['area'] < 50]
    try:
        im = m.compose(ink_over={i: '' for i in gone}) if fade >= 1 else m.compose()
        if 0 < fade < 1:
            im = Image.blend(im, m.compose(ink_over={i: '' for i in gone}), fade)
    finally:
        m.FILL_TAGS = tags
    x, y, w, h = m.CROP
    mask = (f'<mask id="front" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/>'
            f'<path d="{obj}" fill="#000" stroke="#000" stroke-width="44" stroke-linejoin="round"/></mask>')
    im.alpha_composite(m.svg(mask + f'<g mask="url(#front)">{g.sprite_svg(wave_items(), t)}</g>'))
    return im


def wave_main() -> None:
    out = OUT.parent / 'waving'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [wave_frame(t) for t in frames]
    tiles[-1].save(out / 'end-frame.png')
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
    steps = [wave_frame(k / 8) for k in range(9)]
    sw, sh = int(w * 0.3), int(h * 0.3)
    grid = Image.new('RGB', (sw * 9 + 100, sh + 50), 'white')
    d = ImageDraw.Draw(grid)
    for k, im in enumerate(steps):
        x = 10 + k * (sw + 10)
        d.text((x, 10), f'step {k}', fill='black', font=font)
        grid.paste(im.convert('RGB').resize((sw, sh), Image.LANCZOS), (x, 44))
    grid.save(out / 'steps.png')
    print('wrote', out)


def export() -> None:
    import json
    build = {
        'label': "The pink collar of the horned creature, top left: drag for the Lower 1' drawbar; its mint flipper "
                 'lifts out of the cape as an arm, a segment a step, a big hand opens at the top and swishes as it waves',
        'effects': [
            {'effect': 'vanish', 'parts': ['detail'], 'span': list(VANISH)},
            {'effect': 'sprites', 'place': 'under', 'items': patch_items()},
            {'effect': 'sprites', 'place': 'around', 'items': wave_items()},
        ],
    }
    for e in build['effects'][1:]:
        for it in e['items']:
            it['at'] = [round(v, 1) for v in it['at']]
            it['start'], it['end'] = round(it['start'], 4), round(it['end'], 4)
    dst = OUT.parent / 'build.json'
    dst.write_text(json.dumps(build, indent=2) + '\n')
    print('exported', sum(len(e.get('items', [])) for e in build['effects']), 'shapes to', dst)


if __name__ == '__main__':
    _argv = __import__('sys').argv[1:]
    if not _argv:
        main()
    elif 'wave' in _argv:
        wave_main()
    elif 'export' in _argv:
        export()
