# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Five end frames (lower drawbar 6 fully out) for the horned blue ghost under the big cloud.

    uv run scripts/ghost_endframes.py
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
cs = importlib.util.spec_from_file_location('curl', ROOT / 'scripts/curl_endframes.py')
c = importlib.util.module_from_spec(cs)
cs.loader.exec_module(c)
m.CROP = (2350, 600, 1100, 1150)
m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')
m.FRONT, m.FRONT_INK = [], []
OUT = ROOT / 'docs/objects/lower-db6/endframes'
p, outlined, circle, ellipse, swoosh = m.p, m.outlined, c.circle, c.ellipse, c.swoosh
INK = 14
PALE, BLUE, MAGENTA, LIME = '#BEDAF0', '#5FA3D8', '#FF1ABE', '#d4f55a'
HORN_L, HORN_R = '#FF5E1A', '#FFA782'
BODY = ['f231', 'f232', 'f233']
EYE = (2850.0, 1152.0, 24.0, 118.0)


def comp(front: str, again: list[str], over: str = '') -> Image.Image:
    """New shapes drawn, then the named painted shapes (and their ink) laid back on top, so the new parts come out
    from behind them; `over` goes on top of everything."""
    m.FRONT = again
    m.FRONT_INK = sorted({s for f in again for s in m.own_ink(f)})
    try:
        im = m.compose(front=front or '<g/>')
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if over:
        im.alpha_composite(m.svg(over))
    return im


def tube(P, w0, w1) -> str:
    """A tapered outlined limb along the centreline P (no bare lines): width w0 at the start to w1 at the end, with a
    round cap at the end."""
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
    return 'M' + 'L'.join(p(*q) for q in L) + f'A{w1:.1f} {w1:.1f} 0 0 1 {p(*R[-1])}' + 'L' + 'L'.join(p(*q) for q in R[::-1]) + 'Z'


def bez(P0, P1, P2, P3, n=30):
    out = []
    for i in range(n + 1):
        u = i / n
        k = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3]
        out.append((sum(a * q[0] for a, q in zip(k, (P0, P1, P2, P3))), sum(a * q[1] for a, q in zip(k, (P0, P1, P2, P3)))))
    return out


def spiral(x0, y0, a0, r0, turns, shrink, sign, n=60):
    """A curl starting at (x0, y0) heading in direction a0 (radians), its radius shrinking as it winds in."""
    P = [(x0, y0)]
    x, y, a = x0, y0, a0
    for i in range(n):
        u = i / n
        r = r0 * (1 - shrink * u)
        step = (turns * 2 * math.pi) / n
        x += math.cos(a) * r * step
        y += math.sin(a) * r * step
        a += sign * step
        P.append((x, y))
    return P


def wide_eye(cx, cy, r) -> str:
    out = outlined(circle(cx, cy, r), '#ffffff', INK)
    out += outlined(circle(cx + 6, cy + 10, r * 0.5), LIME, INK * 0.8)
    out += f'<path d="{circle(cx + 6, cy + 10, r * 0.24)}" fill="#000"/>'
    out += f'<path d="{circle(cx + 6 + r * 0.16, cy - r * 0.05, r * 0.09)}" fill="#fff"/>'
    return out


def v1_boo() -> Image.Image:
    """Boo! Two pale blue arms fling up from behind the ghost with little mitten hands, and its slit eye pops into a
    big round eye."""
    arms = ''
    for P, col in [(bez((2790, 1300), (2700, 1260), (2600, 1150), (2560, 990)), PALE), (bez((3100, 1280), (3200, 1220), (3260, 1110), (3250, 960)), BLUE)]:
        arms += outlined(tube(P, 46, 40), col, INK)
        hx, hy = P[-1]
        arms += outlined(ellipse(hx, hy - 20, 52, 60), col, INK)
        for dx in (-34, 0, 34):
            arms += outlined(ellipse(hx + dx, hy - 72, 17, 30), col, INK * 0.8)
        arms += outlined(ellipse(hx, hy - 20, 44, 52), col, 0.1)
    over = outlined(ellipse(EYE[0], EYE[1], 30, 124), PALE, 0.1) + wide_eye(EYE[0], EYE[1] - 10, 62)
    return comp(arms, BODY + ['f234', 'f235'], over)


def v2_ram_horns() -> Image.Image:
    """Ram horns: both horns grow on from their tips and curl round into big ridged spirals."""
    out = ''
    for (tx, ty), a0, sign, col, fid in [((2625, 835), math.radians(-120), -1, HORN_L, 'f234'), ((3060, 855), math.radians(-60), 1, HORN_R, 'f235')]:
        P = [(tx + 30 * math.cos(a0 + math.pi), ty + 30 * math.sin(a0 + math.pi))] + spiral(tx, ty, a0, 120, 1.25, 0.75, sign)
        out += outlined(tube(P, 44, 12), col, INK)
        for k in range(6, len(P) - 8, 7):
            (x, y), (x2, y2) = P[k], P[k + 1]
            d = math.hypot(x2 - x, y2 - y) or 1
            nx, ny = -(y2 - y) / d, (x2 - x) / d
            w = 44 - 32 * k / len(P)
            out += outlined(f'M{p(x + nx * w * 0.9, y + ny * w * 0.9)}L{p(x - nx * w * 0.9 + 6, y - ny * w * 0.9)}L{p(x - nx * w * 0.9 + 14, y - ny * w * 0.9 + 4)}L{p(x + nx * w * 0.9 + 8, y + ny * w * 0.9 + 4)}Z', '#000', 1)
    return comp(out, ['f234', 'f235'] + BODY)


def v3_blower() -> Image.Image:
    """Party blower: the magenta at its bottom unrolls into a striped party blower curling out to the left, with a
    burst of confetti at the end."""
    P = [(2830, 1515)] + [(2830 - 250 * u, 1515 - 60 * math.sin(u * 2.2)) for u in [i / 16 for i in range(1, 17)]]
    P += spiral(P[-1][0], P[-1][1], math.radians(170), 105, 1.1, 0.65, 1, 36)[1:]
    out = ''
    cols = [MAGENTA, '#ffe066']
    seg = 4
    for k in range(0, len(P) - seg, seg):
        out += outlined(tube(P[k:k + seg + 1], 50 - 26 * k / len(P), 50 - 26 * (k + seg) / len(P)), cols[(k // seg) % 2], INK * 0.8)
    rnd = random.Random(3)
    ex, ey = P[-1]
    for _ in range(14):
        a = rnd.random() * 2 * math.pi
        r = 110 + rnd.random() * 150
        x, y = ex + math.cos(a) * r, ey + math.sin(a) * r
        s = 18 + rnd.random() * 10
        out += outlined(ellipse(x, y, s, s * 0.55, rnd.random() * 180), rnd.choice(['#ffe066', '#2DFFF4', '#f64c76', '#c4a3f0', LIME]), INK * 0.6)
    return comp('', [], out)


def v4_wave() -> Image.Image:
    """Waving: the lime hand on its right swells into a big open hand on a blue arm, raised and waving, with motion
    crescents."""
    P = bez((3080, 1330), (3180, 1300), (3250, 1200), (3250, 1060))
    hx, hy = P[-1]
    out = outlined(tube(P, 44, 40), BLUE, INK)
    cx, cy = hx, hy - 50
    hand = ''
    for ang, ln in ((-165, 150), (-125, 205), (-95, 225), (-65, 205), (-35, 170)):
        a = math.radians(ang)
        hand += outlined(tube([(cx + math.cos(a) * 30, cy + math.sin(a) * 30), (cx + math.cos(a) * ln, cy + math.sin(a) * ln)], 34, 30), LIME, INK)
    hand += outlined(ellipse(cx, cy + 10, 92, 98), LIME, INK)
    # open the palm's outline where the fingers join: refill the joins without ink
    for ang in (-160, -122, -95, -68, -40):
        a = math.radians(ang)
        hand += f'<path d="{ellipse(cx + math.cos(a) * 82, cy + math.sin(a) * 82 + 6, 28, 28)}" fill="{LIME}"/>'
    out += hand
    out += swoosh(hx, hy - 40, 200, 20, 70, 22) + swoosh(hx, hy - 40, 200, 110, 160, 22)
    return comp(out, BODY)


def ghost(cx, top, w, h, eye=True) -> str:
    """A little ghost the painting's way: a bullet shape, pale left half, deeper blue right half, a slit eye, small
    horns, a magenta foot."""
    r = w / 2
    body = (f'M{p(cx - r * 0.95, top + h)}C{p(cx - r * 1.05, top + h * 0.35)} {p(cx - r * 0.45, top)} {p(cx, top)}'
            f'C{p(cx + r * 0.45, top)} {p(cx + r * 1.0, top + h * 0.4)} {p(cx + r * 1.3, top + h)}Z')
    cid = f'gh{cx:.0f}'
    out = outlined(tube(bez((cx - r * 0.3, top + h * 0.3), (cx - r * 1.2, top + h * 0.25), (cx - r * 1.5, top), (cx - r * 1.2, top - h * 0.2), 16), r * 0.32, r * 0.12), HORN_L, INK * 0.8)
    out += outlined(tube(bez((cx + r * 0.3, top + h * 0.3), (cx + r * 1.2, top + h * 0.25), (cx + r * 1.5, top), (cx + r * 1.2, top - h * 0.2), 16), r * 0.3, r * 0.12), HORN_R, INK * 0.8)
    out += f'<defs><clipPath id="{cid}"><path d="{body}"/></clipPath></defs>'
    out += f'<path d="{body}" fill="{PALE}"/>'
    out += f'<g clip-path="url(#{cid})"><rect x="{cx:.1f}" y="{top - 10:.1f}" width="{w:.1f}" height="{h + 20:.1f}" fill="{BLUE}"/>'
    out += f'<path d="{ellipse(cx - r * 0.1, top + h, r * 0.75, r * 0.6)}" fill="{MAGENTA}" stroke="#000" stroke-width="{INK * 0.8}"/></g>'
    out += f'<path d="{body}" fill="none" stroke="#000" stroke-width="{INK}" stroke-linejoin="round"/>'
    out += f'<path d="M{p(cx, top + 2)}L{p(cx, top + h)}" fill="none" stroke="#000" stroke-width="{INK * 0.8}"/>'
    if eye:
        out += outlined(ellipse(cx - r * 0.4, top + h * 0.4, r * 0.2, h * 0.19), LIME, INK * 0.8)
    return out


def v5_twins() -> Image.Image:
    """Twins: two little copies of the ghost peek out from behind it, one each side, horns and slit eyes and all."""
    out = f'<g transform="rotate(-14 2660 1500)">{ghost(2660, 1190, 170, 380)}</g><g transform="rotate(12 3220 1560)">{ghost(3220, 1290, 140, 300)}</g>'
    return comp(out, BODY + ['f234', 'f235'])


VERSIONS = [
    ('1-boo', 'Boo!', v1_boo),
    ('2-ram-horns', 'Ram horns', v2_ram_horns),
    ('3-party-blower', 'Party blower', v3_blower),
    ('4-waving', 'Waving', v4_wave),
    ('5-twins', 'Twins', v5_twins),
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


# ---- chosen: waving with twins (4 + 5) ----------------------------------------------------------------------------
# One list of sprites drives both the mockup and the app (the app's drawSprites plays the same windows and easing).
import re as _re


def rot_path(d: str, ox: float, oy: float, deg: float) -> str:
    """Rotate an M/L/C/A/Z path about (ox, oy)."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda x, y: (ox + (x - ox) * ca - (y - oy) * sa, oy + (x - ox) * sa + (y - oy) * ca)
    out = []
    for cmd, args in _re.findall(r'([MLCAZ])([^MLCAZ]*)', d):
        v = [float(t) for t in _re.findall(r'-?\d+\.?\d*', args)]
        if cmd == 'A':
            rx, ry, xr, la, sw, x, y = v
            out.append(f'A{rx:.1f} {ry:.1f} {xr + deg:.1f} {int(la)} {int(sw)} {p(*R(x, y))}')
        elif cmd == 'Z':
            out.append('Z')
        else:
            out.append(cmd + ' '.join(p(*R(v[i], v[i + 1])) for i in range(0, len(v), 2)))
    return ''.join(out)


def twin_items(cx, top, w, h, deg, start, end) -> list[dict]:
    """A little ghost as sprites: horns, pale body, its deeper blue right half, a magenta foot, a slit eye; it pops
    up from its base."""
    r = w / 2
    bot = top + h
    body = (f'M{p(cx - r * 0.95, bot)}C{p(cx - r * 1.05, top + h * 0.35)} {p(cx - r * 0.45, top)} {p(cx, top)}'
            f'C{p(cx + r * 0.45, top)} {p(cx + r * 1.0, top + h * 0.4)} {p(cx + r * 1.3, bot)}Z')
    right = f'M{p(cx, top)}C{p(cx + r * 0.45, top)} {p(cx + r * 1.0, top + h * 0.4)} {p(cx + r * 1.3, bot)}L{p(cx, bot)}Z'
    fx0, fx1 = cx - r * 0.8, cx + r * 0.7
    foot = f'M{p(fx0, bot)}C{p(fx0, bot - r * 0.8)} {p(fx1, bot - r * 0.8)} {p(fx1, bot)}Z'
    hornL = tube(bez((cx - r * 0.3, top + h * 0.3), (cx - r * 1.2, top + h * 0.25), (cx - r * 1.5, top), (cx - r * 1.2, top - h * 0.2), 16), r * 0.32, r * 0.12)
    hornR = tube(bez((cx + r * 0.3, top + h * 0.3), (cx + r * 1.2, top + h * 0.25), (cx + r * 1.5, top), (cx + r * 1.2, top - h * 0.2), 16), r * 0.3, r * 0.12)
    eye = ellipse(cx - r * 0.4, top + h * 0.4, r * 0.2, h * 0.19)
    ox, oy = cx, bot
    at = [round(ox, 1), round(oy, 1)]
    E = round(INK * 0.9, 1)
    return [{'d': rot_path(d, ox, oy, deg), 'fill': f, 'edge': e, 'at': at, 'start': start, 'end': end, 'grow': 'scale'}
            for d, f, e in [(hornL, HORN_L, E), (hornR, HORN_R, E), (body, PALE, INK), (right, BLUE, E), (foot, MAGENTA, E), (eye, LIME, E)]]


def crescent(cx, cy, r, a0, a1, w) -> str:
    """A motion crescent: an outlined band along an arc, pointed at both ends."""
    n = 16
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        t = math.sin(u * math.pi) * w / 2
        outer.append((cx + math.cos(a) * (r + t), cy - math.sin(a) * (r + t)))
        inner.append((cx + math.cos(a) * (r - t), cy - math.sin(a) * (r - t)))
    return 'M' + 'L'.join(p(*q) for q in outer + inner[::-1]) + 'Z'


def wave_items() -> list[dict]:
    """The waving arm: a blue arm with a big lime hand grows out from behind the ghost's right side (scaling from the
    shoulder), then two motion crescents flick out round the hand."""
    sx, sy = 3080.0, 1330.0
    P = bez((sx, sy), (3180, 1300), (3250, 1200), (3250, 1060))
    hx, hy = P[-1]
    cx, cy = hx, hy - 50
    items = []
    A = lambda d, f, e: items.append({'d': d, 'fill': f, 'edge': e, 'at': [sx, sy], 'start': 0.45, 'end': 0.85, 'grow': 'scale'})
    A(tube(P, 44, 40), BLUE, INK)
    fingers = ((-165, 150), (-125, 205), (-95, 225), (-65, 205), (-35, 170))
    for ang, ln in fingers:
        a = math.radians(ang)
        A(tube([(cx + math.cos(a) * 30, cy + math.sin(a) * 30), (cx + math.cos(a) * ln, cy + math.sin(a) * ln)], 34, 30), LIME, INK)
    A(ellipse(cx, cy + 10, 92, 98), LIME, INK)
    for ang, _ in fingers:
        a = math.radians(ang)
        A(ellipse(cx + math.cos(a) * 82, cy + math.sin(a) * 82 + 6, 28, 28), LIME, 0)
    for k, (a0, a1) in enumerate([(10, 70), (110, 170)]):
        items.append({'d': crescent(cx, cy, 270, a0, a1, 34), 'fill': '#ffffff', 'edge': round(INK * 0.8, 1), 'at': [round(cx, 1), round(cy, 1)],
                      'start': 0.8 + 0.06 * k, 'end': 0.94 + 0.06 * k, 'grow': 'scale'})
    return items


def combo_items() -> list[dict]:
    return (twin_items(2660, 1190, 170, 380, -14, 0.0, 0.42) + twin_items(3220, 1290, 140, 300, 12, 0.15, 0.55) + wave_items())


FRONT_IDS = ['f232', 'f233', 'f234', 'f235']


def sprite_svg(items, t) -> str:
    out = ''
    for it in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - it['start']) / (it['end'] - it['start'])))) ** 3
        if 'outStart' in it:
            u = max(0.0, min(1.0, (t - it['outStart']) / (it['outEnd'] - it['outStart'])))
            v *= 1 - (1 - (1 - u) ** 3)
        if v <= 0.01:
            continue
        x, y = it['at']
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({v:.4f}) translate({-x} {-y})"/>'
    return out


def combo_frame(t: float) -> Image.Image:
    if t <= 0:
        return m.compose()
    return comp(sprite_svg(combo_items(), t), ['f231'] + FRONT_IDS)


def combo_main() -> None:
    out = OUT.parent / 'waving-twins'
    out.mkdir(parents=True, exist_ok=True)
    combo_frame(1.0).save(out / 'end-frame.png')
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [combo_frame(t) for t in frames]
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


if __name__ == '__main__' and 'combo' in __import__('sys').argv[1:]:
    combo_main()

if __name__ == '__main__' and 'export' in __import__('sys').argv[1:]:
    import json as _j
    mp = ROOT / 'mapping.json'
    M = _j.loads(mp.read_text())
    for b in M['bindings']:
        if b['id'] == 'lower-db6':
            b['label'] = "The blue ghost with orange horns, top centre: the Lower 2' drawbar; drag up and its twins pop up beside it and it waves"
            b['effects'] = [{'effect': 'sprites', 'place': 'around', 'front': FRONT_IDS, 'items': combo_items()}]
    mp.write_text(_j.dumps(M, indent=2) + '\n')
    print('exported', len(combo_items()), 'shapes')
