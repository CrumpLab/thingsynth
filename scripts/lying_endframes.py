# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (key click at its loudest) for the lying creature: the big grey creature lying across the bottom,
its blue mitten arm raised, a closed peach slit eye, two little ears and a lime tongue (its far end is the eye that
boings for percussion).

    uv run scripts/lying_endframes.py
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
m.CROP = (1350, 3350, 1400, 1200)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
OUT = ROOT / 'docs/objects/tg-click/endframes'
p, outlined, circle, ellipse, tube, bez = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez
INK = 15
GREY, BLUE, PEACH, LIME = '#D2D3D4', '#7BB7F3', '#ECC7B0', '#8ef05a'
HAND = (1720.0, 3770.0)
HEAD_FRONT = (2400.0, 3930.0)
SLIT = (2100.0, 3930.0)


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


def wedge(x, y, ang, r0, r1, w) -> str:
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa * w, ca * w
    return (f'M{p(x + ca * r0, y + sa * r0)}L{p(x + ca * r1 + nx, y + sa * r1 + ny)}'
            f'C{p(x + ca * (r1 + w), y + sa * (r1 + w))} {p(x + ca * (r1 + w), y + sa * (r1 + w))} {p(x + ca * r1 - nx, y + sa * r1 - ny)}Z')


def burst(x, y, angs, r0=150, r1=260, w=26, col='#ffe066') -> str:
    return ''.join(outlined(wedge(x, y, a, r0, r1, w), col, INK) for a in angs)


def v1_crab_claw() -> Image.Image:
    """Crab claw: its mitten hand turns into a big red crab pincer, snapping shut with a burst of clicks."""
    x, y = HAND
    a = math.radians(-130)
    ca, sa = math.cos(a), math.sin(a)
    k = 1.35
    R = lambda u, v: (x + ca * u * k - sa * v * k, y + sa * u * k + ca * v * k)
    upper = f'M{p(*R(-60, -70))}C{p(*R(80, -200))} {p(*R(250, -190))} {p(*R(300, -60))}C{p(*R(230, -50))} {p(*R(120, -50))} {p(*R(40, 0))}Z'
    lower = f'M{p(*R(-60, 60))}C{p(*R(60, 150))} {p(*R(200, 150))} {p(*R(250, 70))}C{p(*R(170, 30))} {p(*R(90, 30))} {p(*R(30, 10))}Z'
    out = outlined(lower, '#ff5a4a', INK) + outlined(upper, '#ff5a4a', INK)
    out += outlined(ellipse(x, y, 150, 130, -130), "#ff5a4a", INK)
    tip = R(290, 5)
    out += burst(*tip, [-200, -160, -120, -80], 80, 190, 24)
    return draw(out, [], '')


def v2_castanets() -> Image.Image:
    """Castanet jaws: its head opens a big clacking mouth at the front, rows of white teeth, the slit eye pops open."""
    x, y = HEAD_FRONT
    top = f'M{p(x - 230, y + 10)}C{p(x - 120, y - 40)} {p(x + 40, y - 150)} {p(x + 150, y - 140)}L{p(x + 160, y - 60)}C{p(x + 40, y - 40)} {p(x - 100, y + 20)} {p(x - 230, y + 30)}Z'
    mouth = f'M{p(x - 230, y + 20)}C{p(x - 80, y - 40)} {p(x + 120, y - 90)} {p(x + 160, y - 60)}C{p(x + 170, y + 40)} {p(x + 120, y + 130)} {p(x + 60, y + 170)}C{p(x - 40, y + 140)} {p(x - 160, y + 70)} {p(x - 230, y + 20)}Z'
    out = outlined(mouth, '#9b1f4b', INK)
    for k in range(4):
        u = 0.18 + k * 0.2
        tx, ty = x - 230 + u * 390, y + 20 - math.sin(u * 2.4) * 85
        out += outlined(f'M{p(tx - 32, ty - 8)}L{p(tx + 32, ty - 18)}L{p(tx + 28, ty + 52)}C{p(tx + 15, ty + 70)} {p(tx - 15, ty + 72)} {p(tx - 26, ty + 56)}Z', '#ffffff', INK * 0.9)
    for k in range(3):
        u = 0.3 + k * 0.22
        tx, ty = x - 160 + u * 280, y + 60 + u * 80
        out += outlined(f'M{p(tx - 30, ty + 10)}L{p(tx + 30, ty)}L{p(tx + 24, ty - 58)}C{p(tx + 10, ty - 74)} {p(tx - 14, ty - 72)} {p(tx - 26, ty - 56)}Z', '#ffffff', INK * 0.9)
    out += outlined(f'M{p(x + 70, y + 60)}C{p(x + 120, y + 40)} {p(x + 160, y + 120)} {p(x + 110, y + 150)}C{p(x + 70, y + 160)} {p(x + 40, y + 110)} {p(x + 70, y + 60)}Z', '#ff7fa8', INK * 0.9)
    sx, sy = SLIT
    out += outlined(ellipse(sx, sy, 92, 62, -12), '#ffffff', INK) + f'<path d="{circle(sx + 18, sy + 6, 30)}" fill="#000"/>'
    out += burst(x + 120, y - 20, [-60, -25, 10, 45], 110, 210, 22)
    return draw('', [], out)


def v3_keyboard() -> Image.Image:
    """Organ keys: its long grey body grows a manual of organ keys along it, white keys and black, one pressed down."""
    x0, y0, ang = 1560.0, 4300.0, -14
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x0 + ca * u - sa * v, y0 + sa * u + ca * v)
    out = outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(-20, -30), (600, -30), (600, 30), (-20, 30)]) + 'Z', '#3b3b5c', INK)
    W = 72
    for k in range(8):
        dv = 18 if k == 5 else 0
        out += outlined('M' + 'L'.join(p(*R(u, v)) for u, v in [(k * W, -200 + dv), (k * W + W, -200 + dv), (k * W + W, 0 + dv), (k * W, 0 + dv)]) + 'Z',
                        '#fffbe8' if k != 5 else '#ffe066', INK)
    for k in (1, 2, 4, 5, 6):
        u = k * W - 22
        out += outlined('M' + 'L'.join(p(*R(uu, v)) for uu, v in [(u, -200), (u + 44, -200), (u + 44, -80), (u, -80)]) + 'Z', '#20202e', INK * 0.8)
    out += burst(*R(5.5 * W, -210), [-150, -115, -80, -45], 60, 150, 20)
    return draw('', [], out)


def v4_woodpecker() -> Image.Image:
    """Woodpecker: its head grows a long yellow woodpecker beak and a red crest, its eye pops open, pecking with a
    burst of clicks."""
    x, y = HEAD_FRONT
    beak = f'M{p(x - 30, y - 70)}C{p(x + 100, y - 60)} {p(x + 230, y - 10)} {p(x + 300, y + 20)}C{p(x + 220, y + 40)} {p(x + 100, y + 70)} {p(x - 30, y + 60)}Z'
    out = outlined(beak, '#ffd23f', INK * 1.1)
    out += outlined(f'M{p(x - 20, y - 5)}C{p(x + 100, y + 5)} {p(x + 200, y + 15)} {p(x + 290, y + 20)}C{p(x + 200, y + 25)} {p(x + 100, y + 20)} {p(x - 20, y + 10)}Z', '#e0a000', INK * 0.5)
    for k, (cx, cy, ang, L) in enumerate([(2160, 3800, -110, 190), (2220, 3800, -80, 220), (2280, 3815, -55, 180)]):
        a = math.radians(ang)
        P = [(cx, cy), (cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5), (cx + math.cos(a) * L, cy + math.sin(a) * L)]
        out += outlined(tube(P, 46, 30), ['#f64c4c', '#ff2a4a', '#f64c76'][k], INK)
    sx, sy = SLIT
    out += outlined(circle(sx, sy, 62), '#ffffff', INK) + f'<path d="{circle(sx + 14, sy + 4, 28)}" fill="#000"/>'
    out += burst(x + 300, y + 20, [-50, -10, 30, 70], 70, 170, 22)
    return draw('', [], out)


def v5_snap() -> Image.Image:
    """Finger snap: its mitten hand opens into a big hand snapping its fingers, a burst of clicks flashing out."""
    x, y = HAND
    out = ''
    for ang, L, wdt in [(-175, 230, 38), (-145, 280, 40), (-112, 200, 38), (-85, 170, 36)]:
        a = math.radians(ang)
        out += outlined(tube([(x + math.cos(a) * 60, y + math.sin(a) * 60), (x + math.cos(a) * L, y + math.sin(a) * L)], wdt, wdt * 0.9), BLUE, INK)
    out += outlined(ellipse(x, y, 135, 120, -30), BLUE, INK)
    thumb = tube(bez((x + 70, y - 30), (x + 140, y - 140), (x + 60, y - 250), (x - 40, y - 270), 16), 42, 36)
    out += outlined(thumb, BLUE, INK)
    out += burst(x - 60, y - 290, [-170, -130, -90, -50, -10], 80, 200, 26)
    return draw(out, [], '')


VERSIONS = [
    ('1-crab-claw', 'Crab claw', v1_crab_claw),
    ('2-castanet-jaws', 'Castanet jaws', v2_castanets),
    ('3-organ-keys', 'Organ keys', v3_keyboard),
    ('4-woodpecker', 'Woodpecker', v4_woodpecker),
    ('5-finger-snap', 'Finger snap', v5_snap),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (no click)', m.compose())]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
    w, h = tiles[0][1].size
    s = 0.36
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


# ---- round two: the narwhal direction ------------------------------------------------------------------------------
# Matt: "go more in a narwhal direction". Narwhals click to echolocate, so key click turns the grey creature into a
# narwhal: a long spiral tusk grows from its head, in five variations.
NOUT = ROOT / 'docs/objects/tg-click/narwhal'
TUSK_BASE, TUSK_ANG, TUSK_LEN = (2380.0, 3925.0), -14.0, 480.0
SPOTS = [(1640, 4230, 46, 30), (1760, 4170, 60, 38), (1700, 4330, 40, 26), (1880, 4250, 52, 34), (1980, 4170, 38, 26), (2010, 4320, 44, 28),
         (1850, 4080, 34, 22), (2230, 3860, 40, 26), (2320, 3950, 30, 20), (1570, 4380, 36, 24)]


def tusk(cols=('#fff6dc', '#e9dcb8'), bands=8) -> str:
    """A long tapering tusk with a spiral twist: skewed bands of alternating ivory, each outlined."""
    x, y = TUSK_BASE
    a = math.radians(TUSK_ANG)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x + ca * u - sa * v, y + sa * u + ca * v)
    w = lambda u: 58 * (1 - u / TUSK_LEN) + 6
    out = ''
    for k in range(bands):
        u0, u1 = TUSK_LEN * k / bands, TUSK_LEN * (k + 1) / bands
        sk = (u1 - u0) * 0.45
        quad = [R(u0, -w(u0)), R(u1, -w(u1)), R(u1 + sk if k < bands - 1 else u1, w(u1)), R(u0 + sk, w(u0))]
        if k == bands - 1:
            quad = [R(u0, -w(u0)), R(TUSK_LEN + 20, 0), R(u0 + sk, w(u0))]
        out += outlined('M' + 'L'.join(p(*q) for q in quad) + 'Z', cols[k % 2], INK)
    return out


def tusk_tip():
    a = math.radians(TUSK_ANG)
    return (TUSK_BASE[0] + math.cos(a) * (TUSK_LEN + 20), TUSK_BASE[1] + math.sin(a) * (TUSK_LEN + 20))


def friendly_eye() -> str:
    sx, sy = SLIT
    return (outlined(ellipse(sx, sy, 78, 58, -12), '#ffffff', INK) + f'<path d="{circle(sx + 16, sy + 6, 30)}" fill="#1b2a5a"/>'
            + f'<path d="{circle(sx + 26, sy - 6, 10)}" fill="#ffffff"/>')


def spots() -> str:
    return ''.join(outlined(ellipse(x, y, rx, ry, -14), '#9fa8bf', INK * 0.6) for x, y, rx, ry in SPOTS)


def crescent_arc(x, y, r, a0, a1, w, col) -> str:
    return outlined(g.crescent(x, y, r, a0, a1, w), col, INK * 0.8)


def fluke() -> str:
    """The raised mitten becomes a narwhal's tail fluke: two broad lobes with a notch, held up in a wave."""
    x, y = 1810.0, 3860.0
    a = math.radians(-90)
    ca, sa = math.cos(a), math.sin(a)
    k = 1.1
    R = lambda u, v: (x + (ca * u - sa * v) * k, y + (sa * u + ca * v) * k)
    d = (f'M{p(*R(-30, 0))}C{p(*R(60, -30))} {p(*R(110, -170))} {p(*R(230, -250))}'
         f'C{p(*R(200, -170))} {p(*R(230, -80))} {p(*R(175, 0))}'
         f'C{p(*R(230, 80))} {p(*R(200, 170))} {p(*R(230, 250))}'
         f'C{p(*R(110, 170))} {p(*R(60, 30))} {p(*R(-30, 0))}Z')
    return outlined(d, '#9fb6d6', INK)


def n1_tusk() -> Image.Image:
    """Ivory tusk: a long spiral ivory tusk grows out of its head, and its slit eye opens into a friendly round eye."""
    return draw('', [], tusk() + friendly_eye())


def n2_echo() -> Image.Image:
    """Echo clicks: the tusk plus rings of echolocation clicks rolling out from its tip."""
    tx, ty = tusk_tip()
    rings = ''.join(crescent_arc(tx, ty, 80 + 65 * k, -40 + 14, 40 + 14, 40 - 6 * k, ['#2DFFF4', '#ffffff', '#ffe066'][k]) for k in range(3))
    return draw('', [], tusk() + friendly_eye() + rings)


def n3_spotted() -> Image.Image:
    """Spotted narwhal: the tusk, and the grey hide takes on a narwhal's blue-grey mottled spots."""
    return draw('', [], spots() + tusk() + friendly_eye())


def n4_fluke() -> Image.Image:
    """Tail wave: the tusk, and the raised mitten arm turns into a narwhal's tail fluke waving up."""
    return draw('', [], fluke() + tusk() + friendly_eye())


def n5_party() -> Image.Image:
    """Party narwhal: a candy-striped tusk, sparkles at its tip, and a fountain spouting from its blowhole."""
    x, y = 2230.0, 3790.0
    out = ''
    col = [(x, y - 40), (x - 10, y - 140), (x + 10, y - 240)]
    out += outlined(tube(col, 34, 26), '#bff6ff', INK)
    for k, ang in enumerate((-160, -125, -55, -20)):
        a = math.radians(ang)
        P = bez((x + 10, y - 250), (x + math.cos(a) * 80, y - 300), (x + math.cos(a) * 170, y - 280 + 60), (x + math.cos(a) * 200, y - 160), 16)
        out += outlined(tube(P, 20, 12), '#bff6ff', INK * 0.9)
        dx, dy = P[-1]
        out += outlined(f'M{p(dx, dy + 10)}C{p(dx + 22, dy + 40)} {p(dx + 18, dy + 70)} {p(dx, dy + 70)}C{p(dx - 18, dy + 70)} {p(dx - 22, dy + 40)} {p(dx, dy + 10)}Z', '#bff6ff', INK * 0.8)
    tx, ty = tusk_tip()
    stars = ''
    for sx, sy, s in [(tx + 40, ty - 70, 55), (tx + 90, ty + 30, 40), (tx - 30, ty - 120, 34)]:
        pts = []
        for q in range(8):
            a = math.radians(-90 + q * 45)
            rr = s if q % 2 == 0 else s * 0.3
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        stars += outlined('M' + 'L'.join(p(*q) for q in pts) + 'Z', '#ffe066', INK * 0.8)
    return draw('', [], out + tusk(('#ff9fc4', '#ffffff')) + friendly_eye() + stars)


NARWHALS = [
    ('1-ivory-tusk', 'Ivory tusk', n1_tusk),
    ('2-echo-clicks', 'Echo clicks', n2_echo),
    ('3-spotted', 'Spotted narwhal', n3_spotted),
    ('4-tail-wave', 'Tail wave', n4_fluke),
    ('5-party-narwhal', 'Party narwhal', n5_party),
]


def narwhal_main() -> None:
    NOUT.mkdir(parents=True, exist_ok=True)
    tiles = [('0  As painted (no click)', m.compose())]
    for slug, title, fn in NARWHALS:
        im = fn()
        im.save(NOUT / f'{slug}.png')
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
    sheet.save(NOUT / 'sheet.png')
    print('wrote', NOUT / 'sheet.png')


if __name__ == '__main__' and 'narwhal' in __import__('sys').argv[1:]:
    m.CROP = (1450, 3300, 1800, 1250)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    narwhal_main()


# ---- chosen: party narwhal ----------------------------------------------------------------------------------------
# Key click from none to loudest: the slit eye fades (0..0.15) as a friendly round eye opens (0.05..0.3), the candy
# tusk grows out of its head (0.15..0.6), the blowhole fountain spouts up and splashes out (0.5..0.85), the drops fall
# and the sparkles pop at the tusk's tip (0.75..1).
def tusk_parts(cols=('#ff9fc4', '#ffffff'), bands=8) -> list[tuple[str, str]]:
    x, y = TUSK_BASE
    a = math.radians(TUSK_ANG)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda u, v: (x + ca * u - sa * v, y + sa * u + ca * v)
    w = lambda u: 58 * (1 - u / TUSK_LEN) + 6
    out = []
    for k in range(bands):
        u0, u1 = TUSK_LEN * k / bands, TUSK_LEN * (k + 1) / bands
        sk = (u1 - u0) * 0.45
        quad = [R(u0, -w(u0)), R(u1, -w(u1)), R(u1 + sk, w(u1)), R(u0 + sk, w(u0))] if k < bands - 1 else [R(u0, -w(u0)), R(TUSK_LEN + 20, 0), R(u0 + sk, w(u0))]
        out.append(('M' + 'L'.join(p(*q) for q in quad) + 'Z', cols[k % 2]))
    return out


def party_items() -> list[dict]:
    items = []
    A = lambda d, f, e, at, s, t, grow='scale': items.append({'d': d, 'fill': f, 'edge': round(e, 1), 'at': [round(at[0], 1), round(at[1], 1)],
                                                               'start': round(s, 3), 'end': round(t, 3), 'grow': grow})
    # the friendly eye opening
    sx, sy = 2095.0, 3938.0
    A(ellipse(sx, sy, 108, 74, -12), '#ffffff', INK, (sx, sy), 0.05, 0.25, 'y')
    A(circle(sx + 22, sy + 6, 38), '#1b2a5a', 0, (sx + 22, sy + 6), 0.12, 0.3)
    A(circle(sx + 36, sy - 8, 12), '#ffffff', 0, (sx + 36, sy - 8), 0.2, 0.32)
    # the tusk, band by band from the head out
    parts = tusk_parts()
    for k, (d, col) in enumerate(parts):
        s = 0.15 + 0.045 * k
        A(d, col, INK, TUSK_BASE, s, s + 0.12)
    # the fountain
    x, y = 2230.0, 3790.0
    A(tube([(x, y - 40), (x - 10, y - 140), (x + 10, y - 240)], 34, 26), '#bff6ff', INK, (x, y - 40), 0.5, 0.65, 'y')
    for k, ang in enumerate((-160, -125, -55, -20)):
        a = math.radians(ang)
        P = bez((x + 10, y - 250), (x + math.cos(a) * 80, y - 300), (x + math.cos(a) * 170, y - 280 + 60), (x + math.cos(a) * 200, y - 160), 16)
        A(tube(P, 20, 12), '#bff6ff', INK * 0.9, (x + 10, y - 250), 0.62 + 0.02 * k, 0.8 + 0.02 * k)
        dx, dy = P[-1]
        A(f'M{p(dx, dy + 10)}C{p(dx + 22, dy + 40)} {p(dx + 18, dy + 70)} {p(dx, dy + 70)}C{p(dx - 18, dy + 70)} {p(dx - 22, dy + 40)} {p(dx, dy + 10)}Z',
          '#bff6ff', INK * 0.8, (dx, dy + 40), 0.75 + 0.03 * k, 0.9 + 0.03 * k)
    # sparkles at the tip
    tx, ty = tusk_tip()
    for k, (sx2, sy2, s) in enumerate([(tx + 40, ty - 70, 55), (tx + 90, ty + 30, 40), (tx - 30, ty - 120, 34)]):
        pts = []
        for q in range(8):
            a = math.radians(-90 + q * 45)
            rr = s if q % 2 == 0 else s * 0.3
            pts.append((sx2 + math.cos(a) * rr, sy2 + math.sin(a) * rr))
        A('M' + 'L'.join(p(*q) for q in pts) + 'Z', '#ffe066', INK * 0.8, (sx2, sy2), 0.8 + 0.05 * k, 0.9 + 0.05 * k)
    return items


def party_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    kw = {}
    if t >= 0.08:  # the slit eye's fade, shown as gone past its middle
        kw = {'fill_over': {f: 'M0 0Z' for f in ('f023', 'f024')}, 'ink_over': {i: 'M0 0Z' for f in ('f023', 'f024') for i in m.own_ink(f)}}
    im = m.compose(front='<g/>', **kw)
    im.alpha_composite(m.svg(g.sprite_svg(party_items(), t)))
    return im


def party_main() -> None:
    m.CROP = (1450, 3300, 1800, 1250)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
    out = ROOT / 'docs/objects/tg-click/party-narwhal'
    out.mkdir(parents=True, exist_ok=True)
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [party_frame(t) for t in frames]
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
    print('wrote', out)


if __name__ == '__main__' and 'party' in __import__('sys').argv[1:]:
    party_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    op = ROOT / 'art/golden-pyramid-with-tunnel-celebration/objects.json'
    O = _j.loads(op.read_text())
    objs = O['objects'] if 'objects' in O else O
    objs['lying-creature']['label'] = 'The big grey creature lying across the bottom, its mitten arm up, a closed peach slit eye'
    objs['lying-creature']['parts'] = {'body': ['f014'], 'eye': ['f023', 'f024']}
    op.write_text(_j.dumps(O, indent=2) + '\n')
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'tg-click':
            b['label'] = 'The lying creature: drag across for Key Click; it turns into a party narwhal, candy tusk, spouting fountain and all'
            b['effects'] = [{'effect': 'vanish', 'parts': ['eye'], 'span': [0.0, 0.15]},
                            {'effect': 'sprites', 'place': 'over', 'items': party_items()}]
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', len(party_items()), 'shapes')
