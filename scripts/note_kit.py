# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Shared kit for the 88 note animations. Each note is one painted shape; holding the note plays its animation from
frame 0 (as painted) to frame 1 over NOTE_HOLD_S seconds, and letting go plays it back quickly.

    uv run scripts/note_kit.py sheet            # contact sheets of every note shape in context: docs/notes/contact-*.jpg
    uv run scripts/note_kit.py sheet 60 61 62   # just these notes, one sheet

A batch script (scripts/notes_<batch>.py) imports this kit, defines each note's design as app effects (sprites and
vanish), and calls `run(DESIGNS)`:

    uv run scripts/notes_<batch>.py             # every design's strip (0, 0.2, 1, 2, 3, 4 s held)
    uv run scripts/notes_<batch>.py 60          # just note-60
    uv run scripts/notes_<batch>.py export      # docs/objects/note-<n>/build.json for each

A design is a dict: {'note': 60, 'label': '...', 'effects': [...], 'crop': (x, y, w, h) optional, 'again': [fill ids
to keep in front in the preview] optional}. Effects are exactly what goes into mapping.json.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
gs = importlib.util.spec_from_file_location('ghost', ROOT / 'scripts/ghost_endframes.py')
g = importlib.util.module_from_spec(gs)
gs.loader.exec_module(g)
m = g.m
p, outlined, circle, ellipse, tube, bez, spiral = m.p, m.outlined, g.circle, g.ellipse, g.tube, g.bez, g.spiral

NOTE_HOLD_S = 4.0
#: preview frames: as painted, a short tap, then each second of the hold
TIMES = [0.0, 0.2, 1.0, 2.0, 3.0, 4.0]
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_M = json.loads((ROOT / 'mapping.json').read_text())
NOTES = {b['id']: b for b in _M['bindings'] if b['id'].startswith('note-')}


def name(n: int) -> str:
    return f'{NAMES[n % 12]}{n // 12 - 1}'


def shape_of(note: int) -> str:
    return NOTES[f'note-{note}']['part']


def auto_crop(fid: str, side: float | None = None) -> tuple[int, int, int, int]:
    x, y, w, h = m.FP[fid]['bbox']
    s = side or max(900.0, 2.4 * max(w, h))
    cx, cy = x + w / 2, y + h / 2
    x0 = min(max(0.0, cx - s / 2), 4950 - s)
    y0 = min(max(0.0, cy - s / 2), 4950 - s)
    return (round(x0), round(y0), round(s), round(s))


def set_crop(crop) -> None:
    m.CROP = tuple(crop)
    m.WASH, m.SCRIB = m.raster('wash.webp'), m.raster('scribbles.webp')


def sprite_svg(items, t) -> str:
    """Sprites at frame t, with the app's easing: grow (scale, x or y) or a sweep wedge, and shrinking out."""
    out = ''
    for it in items:
        v = 1 - (1 - max(0.0, min(1.0, (t - it['start']) / max(1e-6, it['end'] - it['start'])))) ** 3
        if 'outStart' in it:
            u = max(0.0, min(1.0, (t - it['outStart']) / max(1e-6, it['outEnd'] - it['outStart'])))
            v *= (1 - u) ** 3
        if v <= 0.01:
            continue
        x, y = it['at']
        stroke = f' stroke="#000" stroke-width="{it["edge"]}" stroke-linejoin="round"' if it['edge'] > 0 else ''
        if it.get('sweep'):
            a0, a1 = math.radians(it['sweep']['from']), math.radians(it['sweep']['to'])
            a = a0 + (a1 - a0) * v
            r = 6000
            n = max(2, int(abs(a - a0) / 0.2) + 1)
            pts = [(x + r * math.cos(a0 + (a - a0) * k / n), y - r * math.sin(a0 + (a - a0) * k / n)) for k in range(n + 1)]
            cid = f'sw{id(it)}{int(t * 1000)}'
            out += (f'<clipPath id="{cid}"><path d="M{p(x, y)}' + ''.join(f'L{p(*q)}' for q in pts) + 'Z"/></clipPath>'
                    f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} clip-path="url(#{cid})"/>')
            continue
        sx, sy = {'scale': (v, v), 'x': (v, 1), 'y': (1, v)}[it.get('grow', 'scale')]
        out += f'<path d="{it["d"]}" fill="{it["fill"]}"{stroke} transform="translate({x} {y}) scale({sx:.4f} {sy:.4f}) translate({-x} {-y})"/>'
    return out


def _u(spec, t) -> float:
    a, b = spec.get('span', [0, 1])
    return max(0.0, min(1.0, (t - a) / (b - a))) if b > a else (1.0 if t >= b else 0.0)


def frame(design: dict, t: float) -> Image.Image:
    """The preview at frame t: the painting, the note's shape faded as far as `vanish` says, sprites placed under /
    around / on / over it."""
    fid = shape_of(design['note'])
    again = [fid] + list(design.get('again', []))
    gone = max([_u(e, t) for e in design['effects'] if e['effect'] == 'vanish'] or [0.0])
    under, around, over, on = '', '', '', ''
    own_hidden = False
    fronts: list[str] = []
    for e in design['effects']:
        if e['effect'] != 'sprites':
            continue
        s = sprite_svg(e['items'], _u(e, t))
        place = e.get('place', 'over')
        if place == 'under':
            under += s
        elif place == 'around':
            around += s
            fronts += e.get('front', [])
            if e.get('own') is False:
                own_hidden = True
        elif place == 'on':
            on += f'<clipPath id="on{fid}"><path d="{m.FILLS[fid]}"/></clipPath><g clip-path="url(#on{fid})">{s}</g>'
        else:
            over += s
    fill_over, ink_over = {}, {}
    if own_hidden:
        # around with own: false, the shape does not stay in front of the sprites
        again = [f for f in again if f != fid]
    if gone >= 0.5:
        fill_over[fid] = 'M0 0Z'
        ink_over = {i: 'M0 0Z' for i in m.own_ink(fid)}
        again = [f for f in again if f != fid]
    m.FRONT = list(dict.fromkeys(again + fronts))
    m.FRONT_INK = sorted({s for f in m.FRONT for s in m.own_ink(f)})
    try:
        im = m.compose(front=(under + around) or '<g/>', fill_over=fill_over, ink_over=ink_over)
    finally:
        m.FRONT, m.FRONT_INK = [], []
    if on:
        im.alpha_composite(m.svg(on))
        im.alpha_composite(m.svg('<g fill="#000">' + ''.join(f'<path d="{m.INKS[i]}"/>' for i in m.own_ink(fid)) + '</g>'))
    if over:
        im.alpha_composite(m.svg(over))
    return im


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def strip(design: dict) -> Path:
    n = design['note']
    set_crop(design.get('crop') or auto_crop(shape_of(n)))
    out = ROOT / 'docs/objects' / f'note-{n}'
    out.mkdir(parents=True, exist_ok=True)
    tiles = [frame(design, s / NOTE_HOLD_S) for s in TIMES]
    w, h = tiles[0].size
    tw = 300
    th = round(h * tw / w)
    im = Image.new('RGB', (len(tiles) * (tw + 8) + 8, th + 44), 'white')
    d = ImageDraw.Draw(im)
    for k, (s, tile) in enumerate(zip(TIMES, tiles)):
        x = 8 + k * (tw + 8)
        d.text((x, 10), f'{s:g} s held', fill='black', font=_font(20))
        im.paste(tile.convert('RGB').resize((tw, th), Image.LANCZOS), (x, 38))
    im.save(out / 'strip.png')
    print('wrote', out / 'strip.png')
    return out / 'strip.png'


def export(design: dict) -> None:
    n = design['note']
    out = ROOT / 'docs/objects' / f'note-{n}'
    out.mkdir(parents=True, exist_ok=True)
    for e in design['effects']:
        for it in e.get('items', []):
            for k in ('d',):
                if 'j' in it[k] or 'nan' in it[k]:
                    raise SystemExit(f'note-{n}: bad path data in a sprite')
    build = {'label': design['label'], 'effects': design['effects']}
    (out / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    print('exported', out / 'build.json')


def run(designs: list[dict]) -> None:
    args = sys.argv[1:]
    if args and args[0] == 'export':
        for d in designs:
            export(d)
        return
    want = {int(a) for a in args if a.isdigit()}
    for d in designs:
        if not want or d['note'] in want:
            strip(d)


# ---- contact sheets ------------------------------------------------------------------------------------------------

def context_tile(n: int, px: int = 420) -> Image.Image:
    fid = shape_of(n)
    set_crop(auto_crop(fid, max(1000.0, 3.0 * max(m.FP[fid]['bbox'][2:]))))
    im = m.compose()
    im.alpha_composite(m.svg(f'<path d="{m.FILLS[fid]}" fill="none" stroke="#00e5ff" stroke-width="{m.CROP[2] / 120:.0f}" '
                             f'stroke-dasharray="{m.CROP[2] / 60:.0f} {m.CROP[2] / 90:.0f}"/>'))
    im = im.convert('RGB').resize((px, px), Image.LANCZOS)
    x, y, w, h = m.FP[fid]['bbox']
    lab = Image.new('RGB', (px, px + 30), 'white')
    lab.paste(im, (0, 30))
    ImageDraw.Draw(lab).text((6, 5), f'note-{n} {name(n)}  {fid} {m.FP[fid]["fill"]} {w:.0f}x{h:.0f}', fill='black', font=_font(17))
    return lab


def sheets(notes: list[int], per: int = 12, cols: int = 4) -> None:
    out = ROOT / 'docs/notes'
    out.mkdir(parents=True, exist_ok=True)
    for s in range(0, len(notes), per):
        chunk = notes[s:s + per]
        tiles = [context_tile(n) for n in chunk]
        w, h = tiles[0].size
        rows = math.ceil(len(tiles) / cols)
        sheet = Image.new('RGB', (cols * (w + 8) + 8, rows * (h + 8) + 8), 'white')
        for k, t in enumerate(tiles):
            sheet.paste(t, (8 + (k % cols) * (w + 8), 8 + (k // cols) * (h + 8)))
        f = out / f'contact-{chunk[0]}-{chunk[-1]}.jpg'
        sheet.save(f, quality=85)
        print('wrote', f)


if __name__ == '__main__' and sys.argv[1:2] == ['sheet']:
    picked = [int(a) for a in sys.argv[2:]] or sorted(int(k[5:]) for k in NOTES)
    sheets(picked)
