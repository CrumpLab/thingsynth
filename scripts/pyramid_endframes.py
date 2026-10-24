# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Mock up five end frames (Drive at 1) for the golden pyramid, straight from the painting's layers.

    uv run scripts/pyramid_endframes.py

Writes docs/objects/pyramid-drive/endframes/{1..5}-*.png and sheet.png. Stack per version: wash, fills (the
pyramid's own shapes possibly reshaped or recoloured), anything drawn behind the pyramid, scribbles, ink, anything
drawn in front, then the creatures that sit on the pyramid redrawn on top, so new drawing never covers them.
Everything new is an outlined, filled shape in the painting's ink.
"""
from __future__ import annotations

import io
import json
import math
import random
import re
from pathlib import Path

import resvg_py
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
L = ROOT / 'art/golden-pyramid-with-tunnel-celebration/layers'
OUT = ROOT / 'docs/objects/pyramid-drive/endframes'
CROP = (2200, 380, 2370, 2120)  # x, y, w, h in canvas px
PX = 900  # output width
INK = '#000'

FILLS = dict(re.findall(r'<path id="(f\d+)"[^>]* d="([^"]*)"', (L / 'fills.svg').read_text()))
FILL_TAGS = re.findall(r'<path id="f\d+"[^>]*/>', (L / 'fills.svg').read_text())
INKS = dict(re.findall(r'<path id="(i\d+)" d="([^"]*)"', (L / 'ink.svg').read_text()))
PARTS = json.loads((L / 'parts.json').read_text())
FP = {f['id']: f for f in PARTS['fills']}
IP = {s['id']: s for s in PARTS['ink']}
PYR = ['f135', 'f136']
# The creatures and things painted on and around the pyramid: redrawn on top of anything new.
FRONT = ['f309', 'f310', 'f311', 'f231', 'f232', 'f233', 'f234', 'f235', 'f220', 'f219', 'f218', 'f204', 'f205', 'f206',
         'f207', 'f208', 'f209', 'f210', 'f211', 'f212', 'f213', 'f214', 'f215', 'f216', 'f217', 'f201', 'f184', 'f185',
         'f186', 'f187', 'f188', 'f189', 'f195', 'f196', 'f197', 'f198', 'f199', 'f200',
         'f162', 'f163', 'f180', 'f221', 'f222', 'f223', 'f224', 'f226', 'f227']


def own_ink(fid: str) -> list[str]:
    x, y, w, h = FP[fid]['bbox']
    out = []
    for s in FP[fid]['ink']:
        bx, by, bw, bh = IP[s]['bbox']
        if bx >= x - 0.12 * w and by >= y - 0.12 * h and bx + bw <= x + 1.12 * w and by + bh <= y + 1.12 * h:
            out.append(s)
    return out


FRONT_INK = sorted({s for f in FRONT for s in own_ink(f)})


def svg(body: str) -> Image.Image:
    x, y, w, h = CROP
    doc = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{PX}" height="{round(PX * h / w)}">{body}</svg>'
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=doc)))).convert('RGBA')


def raster(name: str) -> Image.Image:
    im = Image.open(L / name).convert('RGBA')  # 2475 px = canvas / 2
    x, y, w, h = CROP
    return im.crop((x // 2, y // 2, (x + w) // 2, (y + h) // 2)).resize((PX, round(PX * h / w)), Image.LANCZOS)


WASH, SCRIB = raster('wash.webp'), raster('scribbles.webp')


def p(x: float, y: float) -> str:
    return f'{x:.1f} {y:.1f}'


def outlined(d_fill: str, colour: str, width: float, d_line: str | None = None, extra: str = '') -> str:
    line = d_line or d_fill
    return (f'<path d="{d_fill}" fill="{colour}" {extra}/>'
            f'<path d="{line}" fill="none" stroke="{INK}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')


def warp_path(d: str, fn) -> str:
    nums = re.findall(r'[MCZmcz]|-?\d+\.?\d*', d)
    out, pend = [], None
    for t in nums:
        if t in 'MCZmcz':
            out.append(t)
            continue
        if pend is None:
            pend = float(t)
            continue
        x, y = fn(pend, float(t))
        pend = None
        out.append(f'{x:.1f} {y:.1f}')
    return ' '.join(out).replace(' C ', 'C').replace('M ', 'M').replace(' Z', 'Z')


front_lines = ''


def compose(fill_over: dict[str, str] | None = None, fill_colour: dict[str, str] | None = None, behind: str = '',
            front: str = '', ink_over: dict[str, str] | None = None, pyr_opaque: bool = False, behind_all: str = '',
            rescrib: str = '') -> Image.Image:
    fill_over, fill_colour, ink_over = fill_over or {}, fill_colour or {}, ink_over or {}
    tags = []
    for t in FILL_TAGS:
        fid = re.search(r'id="(f\d+)"', t).group(1)
        if fid in fill_over:
            t = re.sub(r' d="[^"]*"', f' d="{fill_over[fid]}"', t)
        if fid in fill_colour:
            t = re.sub(r'fill="#[0-9A-Fa-f]+"', f'fill="{fill_colour[fid]}"', t)
        if pyr_opaque and fid in PYR:
            t = re.sub(r' fill-opacity="[^"]*"', '', t)
        tags.append(t)
    body_fills = behind_all + ''.join(tags)
    if behind:
        # behind the pyramid: draw the new things, then the pyramid's faces again over them
        pyr = ''.join(t for t in tags if re.search(r'id="(f135|f136)"', t))
        body_fills += behind + pyr
    ink = ''.join(f'<path d="{ink_over.get(i, d)}"/>' for i, d in INKS.items())
    front_again = ''.join(t for t in tags if re.search(r'id="(f\d+)"', t).group(1) in FRONT)
    front_ink = ''.join(f'<path d="{INKS[i]}"/>' for i in FRONT_INK)
    im = WASH.copy()
    im.alpha_composite(svg(body_fills))
    im.alpha_composite(SCRIB)
    im.alpha_composite(svg(f'<g fill="#000">{ink}</g>'))
    if front:
        im.alpha_composite(svg(front))
        if rescrib:
            # the painting's pencil scribbles laid back over the new shapes
            mask = svg(rescrib).getchannel('A')
            sc = SCRIB.copy()
            sc.putalpha(Image.composite(SCRIB.getchannel('A'), Image.new('L', SCRIB.size, 0), mask))
            im.alpha_composite(sc)
            im.alpha_composite(svg(front_lines))
        im.alpha_composite(svg(front_again))
        im.alpha_composite(svg(f'<g fill="#000">{front_ink}</g>'))
    return im


# ---- geometry of the pyramid ---------------------------------------------------------------------------------------
# The faces' real corners, from the hulls of f135 (left face, a narrow sliver) and f136 (right face).
APEX = (3345.0, 712.0)
BASE_L, BASE_R = (2483.0, 1573.0), (4217.0, 1267.0)  # the ends of the two slopes
CENTRE = (3420.0, 1650.0)


def flame(base: tuple[float, float], h: float, w: float, angle: float, rnd: random.Random, outer: str, core: str, width: float) -> str:
    """An outlined flame tongue with an outlined core, standing on `base`, open at the base."""
    lean, wob = (rnd.random() - 0.5) * 0.5, rnd.random() * 0.15

    def shape(W: float, H: float) -> tuple[str, str]:
        side = (f'M{p(-W / 2, 0)}C{p(-W * (0.75 + wob), -H * 0.32)} {p(-W * 0.05, -H * 0.62)} {p(W * lean, -H)}'
                f'C{p(W * (0.32 + wob), -H * 0.6)} {p(W * 0.85, -H * 0.34)} {p(W / 2, 0)}')
        return side + 'Z', side
    of, ol = shape(w, h)
    cf, cl = shape(w * 0.5, h * 0.56)
    g = f'<g transform="translate({p(*base)}) rotate({angle:.1f})">'
    g += outlined(of, outer, width, ol) + outlined(cf, core, width * 0.75, cl)
    return g + '</g>'


def smooth(pts: list) -> str:
    """A closed Catmull-Rom curve through the points, as cubic Beziers: hand-drawn roundness."""
    n = len(pts)
    d = f'M{p(*pts[0])}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{p(*c1)} {p(*c2)} {p(*p2)}'
    return d + 'Z'


def along(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def slope_flames(rnd: random.Random, count: int, scale: float, colours=('#ff8a3d', '#ff6b4a', '#ff9f43', '#ff5e7a')) -> str:
    """Flames on the right slope (open sky there) and a big crown behind the apex creature."""
    out = []
    # crown: three big tongues fanning out just behind the apex
    for k, (dx, ang, hh) in enumerate([(-120, -22, 1.0), (40, -4, 1.25), (190, 18, 0.95)]):
        out.append(flame((APEX[0] + dx, APEX[1] + 70), 520 * scale * hh, 230 * scale * hh, ang, rnd, colours[k % 4], '#ffe066', 16))
    # down the right slope, shrinking
    for k in range(count):
        t = 0.16 + 0.72 * k / max(1, count - 1)
        b = along(APEX, BASE_R, t)
        h = 380 * scale * (1 - 0.55 * t) * (0.85 + rnd.random() * 0.3)
        out.append(flame((b[0] - 10, b[1] + 22), h, h * 0.45, 34 + rnd.random() * 10, rnd, colours[(k + 1) % 4], '#fff2a8', 13))
    return ''.join(out)


def puff_fn(a: float):
    R = 1200.0

    def fn(x: float, y: float) -> tuple[float, float]:
        dx, dy = x - CENTRE[0], y - CENTRE[1]
        r = math.hypot(dx, dy)
        k = 1 + a * max(0.0, 1 - (r / (R * 1.35)) ** 2)
        return CENTRE[0] + dx * k, CENTRE[1] + dy * k
    return fn


def puffed(a: float) -> tuple[dict[str, str], dict[str, str]]:
    fn = puff_fn(a)
    fills = {f: warp_path(FILLS[f], fn) for f in PYR}
    # the pyramid's own outline strokes: the long ones that run along its faces
    inks = {}
    for f in PYR:
        for s in FP[f]['ink']:
            x, y, w, h = IP[s]['bbox']
            if max(w, h) > 420 and s not in FRONT_INK:
                inks[s] = warp_path(INKS[s], fn)
    return fills, inks


def shine(cx: float, cy: float, rx: float, ry: float, rot: float) -> str:
    d = (f'M{p(cx - rx, cy)}A{rx:.1f} {ry:.1f} 0 1 1 {p(cx + rx, cy)}A{rx:.1f} {ry:.1f} 0 1 1 {p(cx - rx, cy)}Z')
    return f'<g transform="rotate({rot} {cx} {cy})">{outlined(d, "#ffffff", 11, extra="fill-opacity=\'0.9\'")}</g>'



RIDGE_B = (2950.0, 2330.0)
FACE_L_COL, FACE_R_COL = '#F6E9A0', '#F7BE9C'  # the faces' visible colours over the wash


def bulge_edge(a, b, amount: float, outward_sign: float, n: int = 24) -> list[tuple[float, float]]:
    """Points from a to b bulging sideways by `amount` at the middle (a soft arc)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln * outward_sign, dx / ln * outward_sign
    pts = []
    for i in range(n + 1):
        t = i / n
        k = amount * math.sin(math.pi * t) ** 0.8
        pts.append((a[0] + dx * t + nx * k, a[1] + dy * t + ny * k))
    return pts


def puffed_faces(bulge: float, col_l: str, col_r: str, ink: float = 30) -> tuple[str, str, str]:
    """The pyramid redrawn puffed: the faces' real outlines with the two slopes bulging outward. Returns (fills,
    outline, mask)."""
    a_l, a_r = (3338.0, 712.0), (3397.0, 776.0)
    slope_l = bulge_edge(a_l, BASE_L, bulge, 1.0)  # outward = left of apex->left corner
    slope_r = bulge_edge(a_r, BASE_R, bulge, -1.0)  # outward = right/up of apex->right corner
    left_rest = [(2569.0, 2187.0), (2616.0, 2282.0), (2734.0, 2393.0), (2766.0, 2373.0), (2937.0, 2133.0), (3384.0, 766.0)]
    right_rest = [(4305.0, 1514.0), (4302.0, 1535.0), (2952.0, 2206.0), (2940.0, 2142.0)]
    fl = 'M' + 'L'.join(p(*q) for q in slope_l + left_rest) + 'Z'
    fr = 'M' + 'L'.join(p(*q) for q in slope_r + right_rest) + 'Z'
    fills = f'<path d="{fl}" fill="{col_l}"/><path d="{fr}" fill="{col_r}"/>'
    lines = [slope_l, slope_r, [(3338.0, 712.0), (2937.0, 2133.0), (2766.0, 2373.0)], [BASE_R, (4305.0, 1514.0), (4302.0, 1535.0)]]
    outline = (f'<g fill="none" stroke="#000" stroke-width="{ink}" stroke-linejoin="round" stroke-linecap="round">'
               + ''.join(f'<path d="M{"L".join(p(*q) for q in ln)}"/>' for ln in lines) + '</g>')
    mask = f'<path d="{fl}" fill="#fff"/><path d="{fr}" fill="#fff"/>'
    return fills, outline, mask


def with_puff(bulge: float, col_l: str, col_r: str, under: str = '', over: str = '') -> Image.Image:
    global front_lines
    fills, outline, mask = puffed_faces(bulge, col_l, col_r)
    front_lines = outline + over
    try:
        return compose(front=under + fills, rescrib=mask)
    finally:
        front_lines = ''

# ---- the five versions --------------------------------------------------------------------------------------------
def v1_crown() -> Image.Image:
    """Flaming crown: big flames burst from behind the apex and run down the open right slope."""
    rnd = random.Random(1)
    return compose(front=slope_flames(rnd, 6, 1.0), fill_colour={'f135': '#FFD66C', 'f136': '#FF9A6A'})


def v2_puffed() -> Image.Image:
    """Puffed up: the pyramid swells like a balloon, slopes bulging, apex softened, with shiny highlights."""
    shines = shine(3010, 1150, 60, 150, 30) + shine(2960, 1420, 26, 50, 30) + shine(3900, 1180, 55, 120, -36)
    return with_puff(150, '#FFEC8A', '#FFB48A', over=shines)


def v3_puffed_torch() -> Image.Image:
    """Puffed and burning: the swollen pyramid glows hot orange with a flaming crown behind its apex."""
    rnd = random.Random(3)
    return with_puff(135, '#FFC24A', '#FF8A4F', under=slope_flames(rnd, 0, 1.2))


def v4_erupting() -> Image.Image:
    """Erupting: lava bursts from the apex and coats the top of the pyramid like icing, following both slopes, with
    fat drips hanging from its lower edge; blobs fly above."""
    rnd = random.Random(4)
    a_l, a_r = (3338.0, 712.0), (3397.0, 776.0)

    def icing(a, b, side: int) -> tuple[list, list]:
        outer, inner = [], []
        n = 40
        drips = [(0.15 + 0.7 * (k + rnd.random() * 0.6) / 4, 150 + rnd.random() * 230, 0.045 + rnd.random() * 0.025) for k in range(4)]
        for i in range(n + 1):
            t = i / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            depth = 110 * (1 - 0.45 * t) + sum(h * math.exp(-((t - c) / w) ** 4) for c, h, w in drips)
            outer.append((x, y - 18))
            inner.append((x, y + depth))
        return outer, inner
    ol, il = icing(a_l, BASE_L, -1)
    orr, ir = icing(a_r, BASE_R, 1)
    shape = ol[::-1] + orr + ir[::-1] + il
    d = smooth(shape)
    out = [outlined(d, '#ff8a3d', 16)]
    # flying blobs over the apex
    for k in range(7):
        ang = -math.pi / 2 + (rnd.random() - 0.5) * 1.6
        r = 220 + rnd.random() * 260
        cx, cy = APEX[0] + 40 + math.cos(ang) * r, APEX[1] - 80 + math.sin(ang) * r * 0.7
        sz = 28 + rnd.random() * 34
        bd = f'M{p(cx - sz, cy)}C{p(cx - sz, cy - sz * 1.4)} {p(cx + sz, cy - sz * 1.4)} {p(cx + sz, cy)}C{p(cx + sz, cy + sz)} {p(cx - sz, cy + sz)} {p(cx - sz, cy)}Z'
        out.append(outlined(bd, ['#ffb13b', '#ff6a3d', '#ffe066'][k % 3], 11))
    return compose(front=''.join(out), fill_colour={'f135': '#FFD66C', 'f136': '#FF9F7A'})


def v5_sun_eye() -> Image.Image:
    """Sun-pyramid: rays burst out behind it like a sunburst and a big eye opens on its face."""
    rays = []
    for k in range(16):
        a = math.pi + (k + 0.5) * math.pi / 16  # upper half, behind
        L_ = 1250 + (300 if k % 2 else 0)
        w = 0.13
        tip = (APEX[0] + 30 + math.cos(a) * L_, APEX[1] + 650 + math.sin(a) * L_)
        b1 = (APEX[0] + 30 + math.cos(a - w) * 380, APEX[1] + 650 + math.sin(a - w) * 380)
        b2 = (APEX[0] + 30 + math.cos(a + w) * 380, APEX[1] + 650 + math.sin(a + w) * 380)
        d = f'M{p(*b1)}L{p(*tip)}L{p(*b2)}Z'
        rays.append(outlined(d, '#ffd23f' if k % 2 else '#ff9f43', 12, extra='fill-opacity="0.95"'))
    # the eye on the right face: almond white, iris, pupil, highlight, lids
    cx, cy, rx, ry = 3720, 1420, 300, 165
    almond = f'M{p(cx - rx, cy)}C{p(cx - rx * 0.5, cy - ry * 1.5)} {p(cx + rx * 0.5, cy - ry * 1.5)} {p(cx + rx, cy)}C{p(cx + rx * 0.5, cy + ry * 1.5)} {p(cx - rx * 0.5, cy + ry * 1.5)} {p(cx - rx, cy)}Z'
    iris = f'M{p(cx - 125, cy + 10)}A125 125 0 1 1 {p(cx + 125, cy + 10)}A125 125 0 1 1 {p(cx - 125, cy + 10)}Z'
    pupil = f'M{p(cx - 55, cy + 15)}A55 55 0 1 1 {p(cx + 55, cy + 15)}A55 55 0 1 1 {p(cx - 55, cy + 15)}Z'
    hi = f'M{p(cx + 20, cy - 40)}A26 22 0 1 1 {p(cx + 72, cy - 40)}A26 22 0 1 1 {p(cx + 20, cy - 40)}Z'
    # an upper lid: a crescent in the face's colour over the top of the eye, outlined
    lid = (f'M{p(cx - rx - 20, cy + 5)}C{p(cx - rx * 0.5, cy - ry * 1.75)} {p(cx + rx * 0.5, cy - ry * 1.75)} {p(cx + rx + 20, cy + 5)}'
           f'C{p(cx + rx * 0.5, cy - ry * 1.15)} {p(cx - rx * 0.5, cy - ry * 1.15)} {p(cx - rx - 20, cy + 5)}Z')
    lash = outlined(lid, '#FF9F6A', 14)
    eye = outlined(almond, '#ffffff', 16) + outlined(iris, '#3fb6ff', 13) + f'<path d="{pupil}" fill="#000"/>' + f'<path d="{hi}" fill="#fff"/>' + lash
    return compose(behind=''.join(rays), front=eye, fill_colour={'f135': '#FFE680', 'f136': '#FFB47A'}, pyr_opaque=True)


VERSIONS = [
    ('1-flaming-crown', 'Flaming crown', v1_crown),
    ('2-puffed-up', 'Puffed up', v2_puffed),
    ('3-puffed-torch', 'Puffed and burning', v3_puffed_torch),
    ('4-erupting', 'Erupting', v4_erupting),
    ('5-sun-eye', 'Sunburst and eye', v5_sun_eye),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = compose()
    before.save(OUT / '0-as-painted.png')
    tiles = [('0  As painted (frame 0)', before)]
    for slug, title, fn in VERSIONS:
        im = fn()
        im.save(OUT / f'{slug}.png')
        tiles.append((f'{slug[0]}  {title}', im))
        print('wrote', slug)
    w, h = tiles[0][1].size
    s = 0.5
    tw, th = int(w * s), int(h * s)
    sheet = Image.new('RGB', (tw * 3 + 40, (th + 50) * 2 + 20), 'white')
    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = 10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 60)
        d.text((x, y), label, fill='black', font=font)
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 40))
    sheet.save(OUT / 'sheet.png')
    print('wrote sheet')


if __name__ == '__main__' and 'sun' not in __import__('sys').argv[1:]:
    main()


# ---- the chosen direction: sunburst and eye, with a small flaming crown -------------------------------------------
def ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def window(t: float, a: float, b: float) -> float:
    return ease((t - a) / (b - a))


EYE = (3720.0, 1420.0, 300.0, 165.0)  # cx, cy, rx, ry on the right face


def eye_svg(o: float) -> str:
    """The eye, open by o (0 shut: a curved slit; 1 fully open), outlined and filled; the iris is clipped to it."""
    cx, cy, rx, ry = EYE
    top = ry * 1.5 * max(0.06, o)
    almond = (f'M{p(cx - rx, cy)}C{p(cx - rx * 0.5, cy - top)} {p(cx + rx * 0.5, cy - top)} {p(cx + rx, cy)}'
              f'C{p(cx + rx * 0.5, cy + ry * 1.5 * max(0.06, o * 0.9 + 0.1))} {p(cx - rx * 0.5, cy + ry * 1.5 * max(0.06, o * 0.9 + 0.1))} {p(cx - rx, cy)}Z')
    look = 25 * o
    iris = f'M{p(cx - 125, cy + 10)}A125 125 0 1 1 {p(cx + 125, cy + 10)}A125 125 0 1 1 {p(cx - 125, cy + 10)}Z'
    pupil = f'M{p(cx - 55, cy + 15 + look)}A55 55 0 1 1 {p(cx + 55, cy + 15 + look)}A55 55 0 1 1 {p(cx - 55, cy + 15 + look)}Z'
    hi = f'M{p(cx + 20, cy - 40)}A26 22 0 1 1 {p(cx + 72, cy - 40)}A26 22 0 1 1 {p(cx + 20, cy - 40)}Z'
    inner = (f'<path d="{iris}" fill="#3fb6ff" stroke="#000" stroke-width="13"/><path d="{pupil}" fill="#000"/>'
             f'<path d="{hi}" fill="#fff"/>') if o > 0.12 else ''
    return (f'<defs><clipPath id="eye-clip"><path d="{almond}"/></clipPath></defs>'
            f'<path d="{almond}" fill="#ffffff"/><g clip-path="url(#eye-clip)">{inner}</g>'
            f'<path d="{almond}" fill="none" stroke="#000" stroke-width="16" stroke-linejoin="round"/>')


def rays_svg(g: float) -> str:
    """Sixteen alternating rays fanning out above the pyramid, grown to g (0..1) of their length."""
    if g <= 0:
        return ''
    out = []
    ox, oy = APEX[0] + 30, APEX[1] + 650
    for k in range(16):
        a = math.pi + (k + 0.5) * math.pi / 16
        full = 1250 + (300 if k % 2 else 0)
        length = 380 + (full - 380) * g
        w = 0.13
        tip = (ox + math.cos(a) * length, oy + math.sin(a) * length)
        b1 = (ox + math.cos(a - w) * 380, oy + math.sin(a - w) * 380)
        b2 = (ox + math.cos(a + w) * 380, oy + math.sin(a + w) * 380)
        out.append(outlined(f'M{p(*b1)}L{p(*tip)}L{p(*b2)}Z', '#ffd23f' if k % 2 else '#ff9f43', 12))
    return ''.join(out)


def crown_svg(c: float) -> str:
    """Flames standing on the open slopes either side of the apex creature, tilted outward, rising from their
    bases as c goes 0..1 (the nearer pair first)."""
    if c <= 0:
        return ''
    rnd = random.Random(11)
    a_l, a_r = (3338.0, 712.0), (3397.0, 776.0)
    spots = [(along(a_l, BASE_L, 0.2), -38, 1.0, 0.0), (along(a_r, BASE_R, 0.66), 32, 1.0, 0.0),
             (along(a_l, BASE_L, 0.36), -42, 0.75, 0.35), (along(a_r, BASE_R, 0.84), 36, 0.75, 0.35)]
    out = []
    for k, (base, ang, hh, delay) in enumerate(spots):
        g = ease((c - delay) / (1 - delay)) if c > delay else 0
        if g <= 0:
            continue
        h, w = 420 * hh, 200 * hh
        inner = flame((0, 0), h, w, 0, rnd, ['#ff8a3d', '#ff6b4a', '#ff9f43', '#ff5e7a'][k], '#ffe066', 15)
        out.append(f'<g transform="translate({p(base[0], base[1] + 20)}) rotate({ang}) scale({0.3 + 0.7 * g:.3f} {g:.3f})">{inner}</g>')
    return ''.join(out)


def sun_frame(t: float) -> Image.Image:
    """Drive at t: rays grow out first (0..0.6), the eye opens (0.25..0.8), the crown flames rise last (0.55..1),
    and the faces warm all the way."""
    g, o, c, w = window(t, 0.0, 0.6), window(t, 0.25, 0.8), window(t, 0.55, 1.0), t
    lc = '#{:02X}{:02X}{:02X}'.format(255, round(0xF0 - (0xF0 - 0xE0) * w), round(0xAC - (0xAC - 0x70) * w))
    rc = '#{:02X}{:02X}{:02X}'.format(255, round(0xBF - (0xBF - 0xA4) * w), round(0xAC - (0xAC - 0x6A) * w))
    if t <= 0:
        return compose()
    return compose(behind=rays_svg(g), front=crown_svg(c) + eye_svg(o), fill_colour={'f135': lc, 'f136': rc}, pyr_opaque=w > 0.5)


def sun_main() -> None:
    out = OUT.parent / 'sunburst'
    out.mkdir(parents=True, exist_ok=True)
    end = sun_frame(1.0)
    end.save(out / 'end-frame.png')
    frames = [0, 0.25, 0.5, 0.75, 1.0]
    tiles = [sun_frame(t) for t in frames]
    w, h = tiles[0].size
    s = 0.42
    tw, th = int(w * s), int(h * s)
    strip = Image.new('RGB', (tw * len(tiles) + 10 * (len(tiles) + 1), th + 60), 'white')
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(strip)
    for i, (t, im) in enumerate(zip(frames, tiles)):
        x = 10 + i * (tw + 10)
        d.text((x, 12), f'frame {t:.2f}', fill='black', font=font)
        strip.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 50))
    strip.save(out / 'strip.png')
    seq = [k / 20 for k in range(21)] + [k / 20 for k in range(19, 0, -1)]
    tmp = out / '_frames'
    tmp.mkdir(exist_ok=True)
    for i, t in enumerate(seq):
        sun_frame(t).convert('RGB').resize((480, round(480 * h / w)), Image.LANCZOS).save(tmp / f'{i:03d}.png')
    import subprocess, shutil
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-i', str(tmp / '%03d.png'), '-vf',
                    'split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0', str(out / 'sweep.gif')], check=True)
    shutil.rmtree(tmp)
    print('wrote', out)


if __name__ == '__main__' and 'sun' in __import__('sys').argv[1:]:
    sun_main()
