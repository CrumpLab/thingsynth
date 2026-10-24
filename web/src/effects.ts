// Effects: each binding drives one animation of its object, from a first frame (t = 0) to a last frame (t = 1).
// The frame shown is a function of the binding's value and nothing else: a continuous parameter shows the frame at
// its position in its range; a note or an on/off parameter plays from the first frame to the last when it turns on
// and back when it turns off. Nothing moves on its own: between changes every object holds its frame. The only
// motion is the glide from one frame to the next when a value changes (and a preset load reaching objects as a wave
// from the painting's centre).
//
// An animation is the binding's list of effects, all evaluated at the same t. Each effect may play over part of the
// timeline (`span`: [from, to], default [0, 1]) with an easing (`ease`: linear, in, out, in-out), so an object can,
// say, fill during the first half and then glow. At its own local u (0..1), with strength `amount`:
//
//   glow      colour more vivid and more solid: OKLCH chroma up; light colours deepen only as far as needed to hold
//             it, mid and dark colours lift towards light
//   hue       the colour turns round the wheel, 60 degrees at amount 1 (negative turns the other way)
//   fill      a vivid copy of the object revealed from an edge (`from`: bottom, top, left, right), one level across
//             all its shapes, like a drawbar; `edge: "wave"` gives the level a hand-drawn wave that rolls as it moves,
//             `turn` turns the revealed colour's hue (degrees by the last frame) as it advances, `toward` moves every
//             shape's revealed colour to one hue instead, `color` moves it to one exact colour
//   scribble  pencil loops drawn in, clipped to the shape, in the painting's own scribble style (`count` strokes)
//   grow      new growth sprouts from the object, drawn in the painting's own idiom: curving branches in its thick
//             black ink, each ending in a spiral tendril or a little eye-bud, with candy-coloured leaves along them.
//             One branch per 1/count of the timeline (a drawbar's 8 steps grow 8 branches), climbing the shape from
//             its base and alternating sides; within its step a branch draws itself out, then its leaves unfurl,
//             then its tip appears. Seeded per binding, so a frame always shows the same drawing
//   line      the object's linework from less of itself to more of itself: at u = 0 thinner, lighter and broken by
//             small gaps like an unfinished sketch; at 0.5 exactly as painted; at 1 bolder, with a second hand-drawn
//             pass of every stroke just beside the first (thinning, gaps and boldness scale with `amount`)
//   boil      the outline redrawn: the lines bend further from their own shape as u grows, a new drawing every
//             1/12 of the way, so dragging makes them writhe and holding keeps them still; the original at 0
//   swell     the object grows about its centre, 8% at amount 1 (negative shrinks)
//   lean      the object leans from its base, 10 degrees at amount 1 (negative leans left)
//   spin      the object turns about its centre, 180 degrees at amount 1
//   blink     the object squashes shut towards its centre line (an eye closing)
//
// swell, lean, spin and blink move the object's fills and the ink it encloses; the borders it shares with neighbours
// stay. With the system's reduced-motion setting, frames are reached without gliding.
import type { WebSynthlandHost } from '../runtime/types';
import { layers, type Art } from './art';
import { glowColour, hexToOklch, mixOklch, oklchToHex, type Oklch } from './color';
import { positionOf, type Binding, type Ease, type EffectSpec } from './mapping';
import { fillParts, inkParts, resolveObject, type ArtObject } from './objects';

const SVG = 'http://www.w3.org/2000/svg';
const HUE_DEG = 60;
const GLOW_OPACITY = 0.6;
/** fill: the revealed copy is the shape's own colour glowing this much (vivid, lighter for mid and dark colours). */
const FILL_GLOW = 1.4;
/**
 * line: at amount 1, how much thinner the strokes get at the start (canvas px eroded from each side; the painting's
 * lines are 14 to 40 px wide), how much of them the gaps take, how much bolder they get at the end, and the second pass:
 * its opacity, how far beside the first it sits, and how differently it is drawn (px of bending).
 */
const LINE_THIN_PX = 4, LINE_GAPS = 0.3, LINE_BOLD_PX = 5, ECHO_OPACITY = 0.6, ECHO_OFFSET_PX = 9, ECHO_BEND_PX = 10;
/** boil: how far lines bend at u = 1 (canvas px), and how many distinct drawings there are from 0 to 1. */
const BOIL_PX = 12, BOIL_FRAMES = 12;
/** Wavelengths of the bending field in canvas px: long enough that both edges of a stroke move together. */
const BOIL_WAVE: readonly [number, number] = [170, 260];
const SWELL = 0.08, LEAN_DEG = 10, SPIN_DEG = 180, BLINK_SHUT = 0.88;
const SCRIBBLE_COUNT = 14, SCRIBBLE_WIDTH = 10, SCRIBBLE_OPACITY = 0.55;
/**
 * The real scribble layer's colours, measured from scribbles.webp (hue share of its pencil pixels): lavender 30%,
 * yellow 15%, pink 13%, purple 9%, blue 7%, gold 5%, green 5%; pastel, lightness ~0.8.
 */
const SCRIBBLE_PALETTE: ReadonlyArray<[string, number]> = [
  ['#c4a3f0', 30], ['#efe38a', 15], ['#f2a6c6', 13], ['#b38be8', 9], ['#9fbcec', 7], ['#f0d27a', 5], ['#b4e0a2', 5],
];
/**
 * Glides, as time constants (ms): a parameter change (or the binding's own `glide`), a preset load, a note playing
 * its animation to the last frame. A note's way back is its binding's `release` (ms to settle, so release / 3).
 */
const GLIDE_MS = 150, PRESET_GLIDE_MS = 400, WAVE_MS = 450, NOTE_ON_MS = 50;
/**
 * The painting is redrawn at most this often while something is changing. Any change inside the art SVG makes the
 * browser re-rasterise the whole painting (one layer of ~1,900 paths), so writing at the display's 120 Hz backs the
 * raster threads up into long frames.
 */
const PAINT_HZ = 30;
/** Lite: small touch screens (phones), or ?lite; ?lite=0 turns it off. Redrawn at most 20 times a second. */
const LITE = ((): boolean => {
  const q = new URLSearchParams(location.search);
  if (q.has('lite')) return q.get('lite') !== '0';
  return matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 800;
})();
const PAINT_EVERY_MS = 1000 / (LITE ? 20 : PAINT_HZ);

type Fill = { el: SVGPathElement; hex: string; base: Oklch; opacity: number; hue: number; glow: number; written: string };
type Reveal = {
  copy: SVGPathElement; clip: SVGPathElement; base: Oklch; glow: number; turn: number; to: Oklch | null;
  box: [number, number, number, number]; from: string; wave: boolean; written: string; colour: string;
};
type Scribble = { strokes: SVGPathElement[]; count: number; written: string };

/** One effect of an animation, with what it acts on. */
interface Track {
  spec: EffectSpec;
  span: [number, number];
  ease: (u: number) => number;
  /** glow, hue */
  fills: string[];
  /** boil */
  ink: string[];
  /** fill */
  reveals: Reveal[];
  /** scribble */
  scribble?: Scribble;
  /** line: the filter on the object's strokes, its knobs, and the second pass */
  line?: {
    paths: SVGPathElement[]; filterId: string; morph: SVGFEMorphologyElement; mask: SVGFEFuncAElement;
    echo: SVGGElement; under: SVGGElement; written: string;
  };
  /** grow: the features, each with when it grows and how */
  growth?: Growth;
  /** swell, lean, spin, blink: the elements moved, and the centre and base point they move about */
  targets: SVGPathElement[];
  centre: [number, number];
  base: [number, number];
}

interface Live {
  binding: Binding;
  obj: ArtObject;
  /** the frame the binding is heading for, and the one shown (0..1) */
  target: number;
  shown: number;
  tau: number;
  startAt: number;
  tracks: Track[];
  /** Being replaced: going back to frame 0, then its added elements are removed. */
  retiring: boolean;
  added: Element[];
  /** Held at a frame by the editor's Frame slider (the value is ignored meanwhile), or null. */
  pinned: number | null;
}

export interface Effects {
  /** Replace the bindings: unchanged ones stay, new ones play in and old ones play out over `handoverMs`. */
  setBindings(bindings: Binding[], handoverMs?: number): void;
  /** The frame each binding currently shows (0..1), for the debug HUD and tests. */
  shown(): Array<{ id: string; value: number }>;
  /** Notes currently sounding. */
  notes(): number[];
  /** True while frames are gliding; false means every object is holding still. */
  moving(): boolean;
  /** Hold a binding at a frame (0..1) regardless of its value, or release it with null (the editor's Frame slider). */
  pin(bindingId: string, frame: number | null): void;
  /** Lite mode (small touch screens, or ?lite). */
  lite: boolean;
  dispose(): void;
}

const EASES: Record<Ease, (u: number) => number> = {
  linear: (u) => u,
  in: (u) => u * u,
  out: (u) => 1 - (1 - u) * (1 - u),
  'in-out': (u) => (u < 0.5 ? 2 * u * u : 1 - 2 * (1 - u) * (1 - u)),
};

/** A track's own position (0..1) at the binding's frame t. */
function local(tr: Track, t: number): number {
  const [a, b] = tr.span;
  const u = b > a ? (t - a) / (b - a) : t >= b ? 1 : 0;
  return tr.ease(Math.max(0, Math.min(1, u)));
}

function rng(seedText: string): () => number {
  let h = 2166136261;
  for (let i = 0; i < seedText.length; i++) h = Math.imul(h ^ seedText.charCodeAt(i), 16777619);
  return () => {
    h = (h + 0x6d2b79f5) | 0;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mountEffects(art: Art, host: WebSynthlandHost, objects: Map<string, ArtObject>, bindings: Binding[]): Effects {
  const stack = art.stack;
  if (!stack) throw new Error('effects need the layered painting');
  const instant = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fills = new Map<string, Fill>();
  const inkOriginal = new Map<string, string>();
  const boilCache = new Map<string, string>();
  const boilShown = new Map<string, string>();
  const transformed = new Set<SVGPathElement>();
  let live: Live[] = [];
  const byNote = new Map<number, Live[]>();
  let uid = 0;

  const fillState = (id: string): Fill | undefined => {
    let f = fills.get(id);
    if (f) return f;
    const el = art.fills.get(id), part = fillParts.get(id);
    if (!el || !part) return undefined;
    f = { el, hex: part.fill, base: hexToOklch(part.fill), opacity: part.opacity, hue: 0, glow: 0, written: '' };
    fills.set(id, f);
    return f;
  };
  // The pencil grain for scribbles: fractal noise as a speckled mask, shared by every scribble group.
  let pencilId = '';
  const pencilFilter = (): string => {
    if (pencilId) return pencilId;
    pencilId = 'ts-pencil';
    const f = document.createElementNS(SVG, 'filter');
    f.id = pencilId;
    f.setAttribute('x', '-2%'); f.setAttribute('y', '-2%'); f.setAttribute('width', '104%'); f.setAttribute('height', '104%');
    const turb = document.createElementNS(SVG, 'feTurbulence');
    turb.setAttribute('type', 'fractalNoise'); turb.setAttribute('baseFrequency', '0.45'); turb.setAttribute('numOctaves', '2');
    turb.setAttribute('seed', '7'); turb.setAttribute('result', 'noise');
    const cm = document.createElementNS(SVG, 'feColorMatrix');
    cm.setAttribute('in', 'noise'); cm.setAttribute('type', 'matrix'); cm.setAttribute('result', 'grain');
    cm.setAttribute('values', '0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.6 0 0 0 -0.6');
    const comp = document.createElementNS(SVG, 'feComposite');
    comp.setAttribute('in', 'SourceGraphic'); comp.setAttribute('in2', 'grain'); comp.setAttribute('operator', 'in');
    f.append(turb, cm, comp);
    stack.defs.append(f);
    return pencilId;
  };
  const partsOf = (obj: ArtObject, spec: EffectSpec, bindingId: string): string[] => spec.parts
    ? spec.parts.flatMap((r) => {
      const got = obj.roles.get(r);
      if (!got) console.warn(`[thingsynth] binding "${bindingId}": object "${obj.id}" has no role "${r}"`);
      return got ?? [];
    })
    : obj.fills;

  // ---- build: one binding's animation and the elements it adds to the painting --------------------------------------
  const build = (binding: Binding): Live | null => {
    const obj = resolveObject(objects, binding.object);
    if (!obj) return null; // main.ts warns
    const rand = rng(binding.id);
    const L: Live = { binding, obj, target: 0, shown: 0, tau: binding.glide ?? GLIDE_MS, startAt: 0, tracks: [], retiring: false, added: [], pinned: null };
    const [bx, by, bw, bh] = obj.bbox;
    for (const spec of binding.effects) {
      const ids = partsOf(obj, spec, binding.id);
      const tr: Track = {
        spec, span: spec.span ?? [0, 1], ease: EASES[spec.ease ?? 'linear'],
        fills: [], ink: [], reveals: [], targets: [], centre: obj.centroid, base: [bx + bw / 2, by + bh],
      };
      switch (spec.effect) {
        case 'glow':
        case 'hue':
          tr.fills = ids.filter((id) => fillState(id));
          break;
        case 'boil':
          tr.ink = obj.ink.filter((s) => art.ink.has(s));
          break;
        case 'grow': {
          const host = ids.map((id) => art.fills.get(id)).find((p): p is SVGPathElement => !!p);
          if (!host) break;
          const g = document.createElementNS(SVG, 'g');
          g.style.pointerEvents = 'none';
          stack.ink.after(g);
          L.added.push(g);
          tr.growth = buildGrowth(g, host, obj.bbox, spec.count ?? GROW_COUNT, Math.abs(spec.amount) || 1, rand);
          break;
        }
        case 'line': {
          const paths = obj.ink.map((s) => art.ink.get(s)).filter((p): p is SVGPathElement => !!p);
          if (!paths.length) break;
          // One filter for the object's strokes: erode or dilate, then a noise mask that opens gaps.
          const filterId = `ts-line-${uid++}`;
          const f = document.createElementNS(SVG, 'filter');
          f.id = filterId;
          f.setAttribute('filterUnits', 'userSpaceOnUse');
          f.setAttribute('x', String(bx - 60)); f.setAttribute('y', String(by - 60));
          f.setAttribute('width', String(bw + 120)); f.setAttribute('height', String(bh + 120));
          const morph = document.createElementNS(SVG, 'feMorphology');
          morph.setAttribute('in', 'SourceGraphic'); morph.setAttribute('operator', 'erode'); morph.setAttribute('radius', '0');
          morph.setAttribute('result', 'weight');
          const noise = document.createElementNS(SVG, 'feTurbulence');
          noise.setAttribute('type', 'fractalNoise'); noise.setAttribute('baseFrequency', '0.03'); noise.setAttribute('numOctaves', '2');
          noise.setAttribute('seed', String(1 + Math.floor(rand() * 999))); noise.setAttribute('result', 'noise');
          const ct = document.createElementNS(SVG, 'feComponentTransfer');
          ct.setAttribute('in', 'noise'); ct.setAttribute('result', 'mask');
          const fa = document.createElementNS(SVG, 'feFuncA');
          fa.setAttribute('type', 'linear'); fa.setAttribute('slope', '0'); fa.setAttribute('intercept', '1');
          ct.append(fa);
          const comp = document.createElementNS(SVG, 'feComposite');
          comp.setAttribute('in', 'weight'); comp.setAttribute('in2', 'mask'); comp.setAttribute('operator', 'in');
          f.append(morph, noise, ct, comp);
          stack.defs.append(f);
          L.added.push(f);
          // The second pass: every stroke redrawn a little differently, beside the first, hidden until past 0.5.
          const echo = document.createElementNS(SVG, 'g');
          echo.setAttribute('fill', '#000');
          echo.setAttribute('opacity', '0');
          echo.style.pointerEvents = 'none';
          const er = rng(`${binding.id}#echo`);
          for (const p of paths) {
            const e = document.createElementNS(SVG, 'path');
            e.setAttribute('d', wobblePath(p.getAttribute('d') ?? '', ECHO_BEND_PX * Math.abs(spec.amount), er));
            echo.append(e);
          }
          stack.ink.append(echo);
          L.added.push(echo);
          // Under the strokes, the object's own colour: the painting's shapes stop at the ink, so where a line thins
          // or breaks this shows instead of white paper. Only below the middle frame.
          const bodyId = obj.roles.get('body')?.[0] ?? obj.fills[0] ?? '';
          const under = document.createElementNS(SVG, 'g');
          under.setAttribute('fill', fillParts.get(bodyId)?.fill ?? '#888888');
          under.setAttribute('opacity', '0');
          under.style.pointerEvents = 'none';
          for (const p of paths) {
            const c = document.createElementNS(SVG, 'path');
            c.setAttribute('d', p.getAttribute('d') ?? '');
            under.append(c);
          }
          stack.ink.before(under);
          L.added.push(under);
          tr.line = { paths, filterId, morph, mask: fa, echo, under, written: '' };
          break;
        }
        case 'fill':
          for (const id of ids) {
            const orig = art.fills.get(id), part = fillParts.get(id);
            if (!orig || !part) continue;
            const clipId = `ts-reveal-${uid++}`;
            const clip = document.createElementNS(SVG, 'clipPath');
            clip.id = clipId;
            clip.setAttribute('clipPathUnits', 'userSpaceOnUse');
            const shape = document.createElementNS(SVG, 'path');
            shape.setAttribute('d', 'M0 0Z');
            clip.append(shape);
            stack.defs.append(clip);
            L.added.push(clip);
            const copy = orig.cloneNode(false) as SVGPathElement;
            copy.removeAttribute('id');
            copy.dataset.revealOf = id;
            copy.removeAttribute('fill-opacity');
            copy.setAttribute('clip-path', `url(#${clipId})`);
            copy.style.pointerEvents = 'none';
            orig.after(copy);
            L.added.push(copy);
            // One level for the whole object: every shape's reveal uses the object's box.
            tr.reveals.push({
              copy, clip: shape, base: hexToOklch(part.fill), glow: FILL_GLOW * Math.abs(spec.amount),
              turn: spec.toward !== undefined ? hueDelta(hexToOklch(part.fill).h, spec.toward) : spec.turn ?? 0,
              to: spec.color ? hexToOklch(spec.color) : null,
              box: obj.bbox, from: spec.from ?? 'bottom', wave: spec.edge === 'wave', written: '', colour: '',
            });
          }
          break;
        case 'scribble': {
          const clipId = `ts-scribble-${uid++}`;
          const clip = document.createElementNS(SVG, 'clipPath');
          clip.id = clipId;
          for (const id of ids) {
            const use = document.createElementNS(SVG, 'use');
            use.setAttribute('href', `#${id}`);
            clip.append(use);
          }
          stack.defs.append(clip);
          L.added.push(clip);
          const g = document.createElementNS(SVG, 'g');
          g.setAttribute('clip-path', `url(#${clipId})`);
          g.setAttribute('fill', 'none');
          g.setAttribute('stroke-linecap', 'round');
          g.setAttribute('stroke-linejoin', 'round');
          g.style.pointerEvents = 'none';
          g.setAttribute('stroke-opacity', String(SCRIBBLE_OPACITY));
          g.setAttribute('stroke-width', String(SCRIBBLE_WIDTH));
          g.setAttribute('filter', `url(#${pencilFilter()})`);
          const count = spec.count ?? SCRIBBLE_COUNT;
          const strokes: SVGPathElement[] = [];
          for (let k = 0; k < count; k++) strokes.push(scribbleStroke(g, rand, bx, by, bw, bh));
          stack.ink.before(g);
          L.added.push(g);
          tr.scribble = { strokes, count, written: '' };
          break;
        }
        case 'swell':
        case 'lean':
        case 'spin':
        case 'blink': {
          for (const id of ids) { const el = art.fills.get(id); if (el) tr.targets.push(el); }
          // Restricted to roles (`parts`): those shapes' own centre, base and enclosed ink, not the whole object's.
          let ink = obj.ownInk;
          if (spec.parts) {
            let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, ax = 0, ay = 0, at = 0;
            for (const id of ids) {
              const p = fillParts.get(id);
              if (!p) continue;
              const [x, y, w, h] = p.bbox;
              x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h);
              ax += p.centroid[0] * p.area; ay += p.centroid[1] * p.area; at += p.area;
            }
            if (at > 0) {
              const mw = (x1 - x0) * 0.15, mh = (y1 - y0) * 0.15;
              tr.centre = [ax / at, ay / at];
              tr.base = [(x0 + x1) / 2, y1];
              ink = Array.from(new Set(ids.flatMap((id) => fillParts.get(id)?.ink ?? []))).filter((s) => {
                const b = inkParts.get(s)?.bbox;
                return !!b && b[0] >= x0 - mw && b[1] >= y0 - mh && b[0] + b[2] <= x1 + mw && b[1] + b[3] <= y1 + mh;
              });
            }
          }
          for (const s of ink) { const el = art.ink.get(s); if (el) tr.targets.push(el); }
          break;
        }
      }
      L.tracks.push(tr);
    }
    // Reveal copies move with their originals.
    const copies = L.tracks.flatMap((t) => t.reveals);
    for (const t of L.tracks) {
      if (!t.targets.length) continue;
      for (const r of copies) if (t.targets.some((el) => el.id === r.copy.dataset.revealOf)) t.targets.push(r.copy);
    }
    return L;
  };
  const retire = (L: Live): void => {
    for (const tr of L.tracks) if (tr.line) for (const p of tr.line.paths) {
      if (p.getAttribute('filter') === `url(#${tr.line.filterId})`) p.removeAttribute('filter');
    }
    for (const el of L.added) el.remove();
    L.added = [];
  };
  const indexNotes = (): void => {
    byNote.clear();
    for (const L of live) {
      if (L.retiring || L.binding.kind !== 'note') continue;
      const list = byNote.get(L.binding.note) ?? [];
      list.push(L);
      byNote.set(L.binding.note, list);
    }
  };
  for (const binding of bindings) {
    const L = build(binding);
    if (L) live.push(L);
  }
  indexNotes();

  // ---- values -------------------------------------------------------------------------------------------------------
  const read = (L: Live): number => (L.binding.kind === 'param' ? positionOf(L.binding, host.get(L.binding.param)) : L.target);
  for (const L of live) if (L.binding.kind === 'param') L.target = L.shown = read(L);
  const glideOf = (ms: number): number => (instant ? 0 : ms);

  const [px, py, pw, ph] = layers.painted;
  const origin: [number, number] = [px + pw / 2, py + ph / 2];
  const maxDist = Math.hypot(pw / 2, ph / 2);

  let raf = 0, last = 0, lastPaint = 0;
  let dirty = true;
  let moving = false;
  let disposed = false;

  // ---- painting: every frame is computed from the bindings' frames alone ----------------------------------------------
  const paint = (): void => {
    // Colours
    for (const f of fills.values()) { f.hue = 0; f.glow = 0; }
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.fills.length) continue;
      const u = local(tr, L.shown);
      for (const id of tr.fills) {
        const f = fills.get(id);
        if (!f) continue;
        if (tr.spec.effect === 'hue') f.hue += tr.spec.amount * HUE_DEG * u; else f.glow += tr.spec.amount * u;
      }
    }
    for (const f of fills.values()) {
      const g = Math.max(-1, Math.min(1.5, f.glow));
      const atRest = Math.abs(f.hue) < 0.05 && Math.abs(g) < 1e-3;
      const col = atRest ? f.hex : glowColour(f.base, f.hue, g);
      const op = atRest ? f.opacity : Math.max(0, Math.min(1, f.opacity + (1 - f.opacity) * GLOW_OPACITY * Math.max(0, g)));
      const key = `${col}/${op.toFixed(3)}`;
      if (key === f.written) continue;
      f.written = key;
      f.el.setAttribute('fill', col);
      if (op < 1) f.el.setAttribute('fill-opacity', op.toFixed(3)); else f.el.removeAttribute('fill-opacity');
    }

    // Reveals and scribbles
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.reveals.length && !tr.scribble) continue;
      const u = local(tr, L.shown);
      for (const r of tr.reveals) {
        const d = revealPath(r.box, r.from, u, r.wave);
        if (d !== r.written) { r.written = d; r.clip.setAttribute('d', d); }
        const colour = r.to
          ? oklchToHex(mixOklch(hexToOklch(glowColour(r.base, 0, r.glow)), r.to, u))
          : glowColour(r.base, r.turn * u, r.glow);
        if (colour !== r.colour) { r.colour = colour; r.copy.setAttribute('fill', colour); }
      }
      const s = tr.scribble;
      if (s) {
        const drawn = u * s.count;
        const key = drawn.toFixed(3);
        if (key !== s.written) {
          s.written = key;
          s.strokes.forEach((p, i) => p.setAttribute('stroke-dashoffset', (1 - Math.max(0, Math.min(1, drawn - i))).toFixed(3)));
        }
      }
    }

    // Moves: one transform per element, composed from every track that moves it.
    const parts = new Map<SVGPathElement, string[]>();
    const add = (el: SVGPathElement, t: string): void => { const l = parts.get(el); if (l) l.push(t); else parts.set(el, [t]); };
    const about = ([x, y]: [number, number], inner: string): string =>
      `translate(${x.toFixed(1)} ${y.toFixed(1)}) ${inner} translate(${(-x).toFixed(1)} ${(-y).toFixed(1)})`;
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.targets.length) continue;
      const u = local(tr, L.shown);
      if (u < 1e-4) continue;
      const a = tr.spec.amount;
      let t = '';
      if (tr.spec.effect === 'swell') t = about(tr.centre, `scale(${(1 + a * SWELL * u).toFixed(4)})`);
      else if (tr.spec.effect === 'lean') t = about(tr.base, `skewX(${(-a * LEAN_DEG * u).toFixed(3)})`);
      else if (tr.spec.effect === 'spin') t = `rotate(${(a * SPIN_DEG * u).toFixed(2)} ${tr.centre[0].toFixed(1)} ${tr.centre[1].toFixed(1)})`;
      else if (tr.spec.effect === 'blink') t = about(tr.centre, `scale(1 ${(1 - BLINK_SHUT * Math.min(1, Math.abs(a)) * u).toFixed(4)})`);
      if (t) for (const el of tr.targets) add(el, t);
    }
    for (const [el, list] of parts) {
      const t = list.join(' ');
      if (el.getAttribute('transform') !== t) el.setAttribute('transform', t);
      transformed.add(el);
    }
    for (const el of Array.from(transformed)) {
      if (parts.has(el)) continue;
      el.removeAttribute('transform');
      transformed.delete(el);
    }

    // Grow: each feature at its own progress through its window of the timeline.
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.growth) continue;
      const t = local(tr, L.shown);
      for (const f of tr.growth.features) {
        const p = Math.max(0, Math.min(1, (t - f.from) / (f.to - f.from)));
        const key = p.toFixed(3);
        if (key === f.written) continue;
        f.written = key;
        if (f.kind === 'draw') {
          f.el.setAttribute('stroke-dashoffset', (1 - p).toFixed(4));
          f.el.style.visibility = p > 0 ? 'visible' : 'hidden';
        } else {
          const s = p <= 0 ? 0 : popEase(p);
          f.el.style.visibility = p > 0 ? 'visible' : 'hidden';
          f.el.setAttribute('transform', `translate(${f.at[0].toFixed(1)} ${f.at[1].toFixed(1)}) scale(${s.toFixed(4)}) translate(${(-f.at[0]).toFixed(1)} ${(-f.at[1]).toFixed(1)})`);
        }
      }
    }

    // Line: one filter per track on its object's strokes; below the middle thinner and gappier, above it bolder with
    // the second pass showing. At exactly 0.5 the strokes are left as painted (no filter at all).
    const filtered = new Map<SVGPathElement, string>();
    for (const L of live) for (const tr of L.tracks) {
      const ln = tr.line;
      if (!ln) continue;
      const u = local(tr, L.shown);
      const a = Math.abs(tr.spec.amount);
      const less = Math.max(0, 1 - 2 * u), more = Math.max(0, 2 * u - 1);
      const key = `${less.toFixed(3)}/${more.toFixed(3)}`;
      if (key !== ln.written) {
        ln.written = key;
        if (less > 0) {
          ln.morph.setAttribute('operator', 'erode');
          ln.morph.setAttribute('radius', (LINE_THIN_PX * a * less).toFixed(2));
          // Noise alpha sits around 0.5; this keeps coverage full at less = 0 and opens gaps over LINE_GAPS of it at 1.
          const t = 0.5 - 0.3 + LINE_GAPS * a * less * 0.6;
          ln.mask.setAttribute('slope', '12');
          ln.mask.setAttribute('intercept', (-12 * t + 0.5).toFixed(3));
        } else {
          ln.morph.setAttribute('operator', 'dilate');
          ln.morph.setAttribute('radius', (LINE_BOLD_PX * a * more).toFixed(2));
          ln.mask.setAttribute('slope', '0');
          ln.mask.setAttribute('intercept', '1');
        }
        ln.under.setAttribute('opacity', less > 0 ? '1' : '0');
        ln.echo.setAttribute('opacity', (ECHO_OPACITY * Math.min(1, a) * more).toFixed(3));
        const off = ECHO_OFFSET_PX * a * more;
        ln.echo.setAttribute('transform', `translate(${off.toFixed(1)} ${(-off * 0.7).toFixed(1)})`);
      }
      if (less > 0 || more > 0) for (const p of ln.paths) filtered.set(p, ln.filterId);
    }
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.line) continue;
      for (const p of tr.line.paths) {
        const want = filtered.get(p);
        const has = p.getAttribute('filter');
        if (want && has !== `url(#${want})`) p.setAttribute('filter', `url(#${want})`);
        else if (!want && has) p.removeAttribute('filter');
      }
    }

    // Boil: per stroke, the depth is the largest any track asks for; the drawing is the one for that depth.
    const depth = new Map<string, number>();
    for (const L of live) for (const tr of L.tracks) {
      if (!tr.ink.length) continue;
      const v = Math.abs(tr.spec.amount) * local(tr, L.shown);
      for (const id of tr.ink) depth.set(id, Math.max(depth.get(id) ?? 0, v));
    }
    for (const [id, v] of depth) {
      const el = art.ink.get(id);
      if (!el) continue;
      if (!inkOriginal.has(id)) inkOriginal.set(id, el.getAttribute('d') ?? '');
      const orig = inkOriginal.get(id)!;
      const k = Math.min(BOIL_FRAMES * 2, Math.round(v * BOIL_FRAMES));
      let d = orig;
      if (k > 0) {
        const key = `${id}@${k}`;
        let drawn = boilCache.get(key);
        if (drawn === undefined) {
          drawn = wobblePath(orig, (BOIL_PX * k) / BOIL_FRAMES, rng(id), k * 0.9);
          boilCache.set(key, drawn);
        }
        d = drawn;
      }
      if ((boilShown.get(id) ?? orig) === d) continue;
      boilShown.set(id, d);
      el.setAttribute('d', d);
    }
    for (const [id, d] of boilShown) {
      if (depth.has(id)) continue;
      const orig = inkOriginal.get(id);
      if (orig !== undefined && d !== orig) art.ink.get(id)?.setAttribute('d', orig);
      boilShown.delete(id);
    }
  };

  // ---- the loop runs only while some frame is gliding -------------------------------------------------------------
  const frame = (now: number): void => {
    raf = 0;
    if (disposed) return;
    const dt = last ? Math.max(0, now - last) : 16;
    last = now;
    moving = false;
    if (live.some((L) => L.retiring && L.shown === 0)) {
      for (const L of live) if (L.retiring && L.shown === 0) retire(L);
      live = live.filter((L) => !(L.retiring && L.shown === 0));
      dirty = true;
    }
    for (const L of live) {
      if (now < L.startAt) { moving = true; continue; }
      const d = L.target - L.shown;
      if (d === 0) continue;
      dirty = true;
      if (Math.abs(d) < 1e-3) L.shown = L.target;
      else { L.shown += d * (L.tau > 0 ? 1 - Math.exp(-dt / L.tau) : 1); moving = true; }
    }
    if (dirty && now - lastPaint >= PAINT_EVERY_MS - 1) {
      lastPaint = now;
      dirty = false;
      paint();
    }
    if (moving || dirty) raf = requestAnimationFrame(frame);
    else last = 0;
  };
  const kick = (): void => {
    if (disposed) return;
    if (document.hidden) {
      // No frames in a background tab: jump to the targets so the picture is right when it is shown again.
      for (const L of live) { L.shown = L.target; L.startAt = 0; }
      paint();
      dirty = false;
      return;
    }
    if (!raf) raf = requestAnimationFrame(frame);
  };

  // ---- inputs: parameters, presets, notes -------------------------------------------------------------------------
  const offParam = host.onParam((id) => {
    let hit = false;
    for (const L of live) {
      if (L.retiring || L.pinned !== null || L.binding.kind !== 'param' || L.binding.param !== id) continue;
      L.target = read(L);
      L.tau = glideOf(L.binding.glide ?? GLIDE_MS);
      L.startAt = 0;
      hit = true;
    }
    if (hit) kick();
  });
  const offPreset = host.onPreset((index) => {
    if (index < 0) return; // an edit, not a load
    const now = performance.now();
    for (const L of live) {
      if (L.retiring || L.pinned !== null || L.binding.kind !== 'param') continue;
      L.target = read(L);
      L.tau = glideOf(L.binding.glide ?? PRESET_GLIDE_MS);
      const [cx, cy] = L.obj.centroid;
      L.startAt = instant ? 0 : now + (WAVE_MS * Math.hypot(cx - origin[0], cy - origin[1])) / maxDist;
    }
    kick();
  });

  // Notes: wrap the host's note functions, which the computer keyboard, Web MIDI and touch all go through. Note-on
  // plays the animation to its last frame; note-off plays it back over the binding's release.
  const origOn = host.noteOn.bind(host), origOff = host.noteOff.bind(host);
  const sounding = new Set<number>();
  host.noteOn = (note, velocity) => {
    origOn(note, velocity);
    sounding.add(note);
    for (const L of byNote.get(note) ?? []) { if (L.pinned !== null) continue; L.target = 1; L.tau = glideOf(NOTE_ON_MS); L.startAt = 0; }
    kick();
  };
  host.noteOff = (note) => {
    origOff(note);
    sounding.delete(note);
    for (const L of byNote.get(note) ?? []) {
      if (L.pinned !== null) continue;
      L.target = 0;
      L.tau = glideOf(L.binding.kind === 'note' ? L.binding.release / 3 : GLIDE_MS);
    }
    kick();
  };
  const onVis = (): void => { if (!document.hidden) kick(); };
  document.addEventListener('visibilitychange', onVis);

  paint();
  dirty = false;

  const setBindings = (next: Binding[], handoverMs = 1200): void => {
    const key = (b: Binding): string => JSON.stringify(b);
    const old = new Map<string, Live>();
    for (const L of live) if (!L.retiring) old.set(key(L.binding), L);
    const fresh: Live[] = [];
    for (const b of next) {
      const same = old.get(key(b));
      if (same) { fresh.push(same); old.delete(key(b)); continue; }
      const L = build(b);
      if (!L) continue;
      L.shown = 0;
      L.target = L.binding.kind === 'param' ? read(L) : 0;
      L.tau = glideOf(handoverMs / 3);
      fresh.push(L);
    }
    const leaving = Array.from(old.values());
    for (const L of leaving) { L.retiring = true; L.target = 0; L.tau = glideOf(handoverMs / 3); L.startAt = 0; }
    live = [...fresh, ...leaving, ...live.filter((L) => L.retiring)];
    indexNotes();
    dirty = true;
    kick();
  };

  return {
    setBindings,
    shown: () => live.filter((L) => !L.retiring).map((L) => ({ id: L.binding.id, value: L.shown })),
    notes: () => Array.from(sounding).sort((a, b) => a - b),
    moving: () => raf !== 0 || moving,
    pin: (bindingId, frame) => {
      for (const L of live) {
        if (L.retiring || L.binding.id !== bindingId) continue;
        L.pinned = frame === null ? null : Math.max(0, Math.min(1, frame));
        L.target = L.pinned ?? (L.binding.kind === 'param' ? read(L) : sounding.has(L.binding.note) ? 1 : 0);
        L.tau = glideOf(60);
        L.startAt = 0;
      }
      kick();
    },
    lite: LITE,
    dispose: () => {
      disposed = true;
      offParam(); offPreset();
      host.noteOn = origOn; host.noteOff = origOff;
      document.removeEventListener('visibilitychange', onVis);
      if (raf) cancelAnimationFrame(raf);
    },
  };
}

// ---- grow ----------------------------------------------------------------------------------------------------------

const GROW_COUNT = 8;
/** Line weights in canvas px, close to the painting's own ink (its strokes are 14 to 40 px wide). */
const GROW_STEM_PX = 26, GROW_EDGE_PX = 16;
const LEAF_COLOURS = ['#9cf27c', '#c6f58a', '#7fe8b0', '#f2ef7a', '#b4e0a2'];
const BUD_COLOURS = ['#f2a6c6', '#c4a3f0', '#ffb36b', '#7fd8f5', '#ff8fa3'];

interface GrowFeature {
  kind: 'draw' | 'pop';
  el: SVGElement;
  /** the window of the effect's timeline (0..1) it grows over */
  from: number;
  to: number;
  /** pop: the point it grows out of */
  at: [number, number];
  written: string;
}
interface Growth { features: GrowFeature[] }

/** A pop that overshoots a little and settles, like something unfurling. */
function popEase(p: number): number {
  const c = 1.6;
  const q = p - 1;
  return 1 + (c + 1) * q * q * q + c * q * q;
}

type Pt = [number, number];
const add = (a: Pt, b: Pt): Pt => [a[0] + b[0], a[1] + b[1]];
const mul = (a: Pt, k: number): Pt => [a[0] * k, a[1] * k];
const rot = (a: Pt, deg: number): Pt => {
  const r = (deg * Math.PI) / 180, c = Math.cos(r), s = Math.sin(r);
  return [a[0] * c - a[1] * s, a[0] * s + a[1] * c];
};
const norm = (a: Pt): Pt => { const l = Math.hypot(a[0], a[1]) || 1; return [a[0] / l, a[1] / l]; };
const poly = (pts: Pt[]): string => pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join('');

/**
 * Lay out the growth on a host shape: `count` branches, climbing from its base, alternating sides. Each branch
 * starts on the shape's edge at its height, curves outward and upward, and ends in a spiral tendril or an eye-bud,
 * with one or two leaves along it. Everything is drawn into `g` hidden; the paint step reveals it frame by frame.
 */
function buildGrowth(g: SVGGElement, host: SVGPathElement, box: [number, number, number, number], count: number, size: number, rand: () => number): Growth {
  const [bx, by, bw, bh] = box;
  // The host's outline, sampled, to find its left and right edges at any height.
  const total = host.getTotalLength();
  const outline: Pt[] = [];
  for (let i = 0; i < 600; i++) { const q = host.getPointAtLength((total * i) / 600); outline.push([q.x, q.y]); }
  const edge = (y: number, side: -1 | 1): Pt | null => {
    const band = outline.filter((p) => Math.abs(p[1] - y) < bh * 0.03);
    if (!band.length) return null;
    return band.reduce((best, p) => (side < 0 ? (p[0] < best[0] ? p : best) : (p[0] > best[0] ? p : best)));
  };
  const features: GrowFeature[] = [];
  const mk = <K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string>): SVGElementTagNameMap[K] => {
    const e = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    e.style.visibility = 'hidden';
    g.append(e);
    return e;
  };
  // Branch length follows the shape's height (a tall stalk grows long branches), capped by its size overall.
  const scale = Math.min(bh, Math.max(bw, bh) * 0.9) * size;
  for (let k = 0; k < count; k++) {
    const from = k / count, to = (k + 1) / count;
    const win = (a: number, b: number): [number, number] => [from + (to - from) * a, from + (to - from) * b];
    const side: -1 | 1 = k % 2 === 0 ? -1 : 1;
    const y = by + bh * (0.92 - 0.8 * ((k + 0.5) / count)) + (rand() - 0.5) * bh * 0.04;
    const A = edge(y, side);
    if (!A) continue;
    // Outward, then turned upward 25..55 degrees, with a bend one way or the other.
    const lean = 25 + rand() * 30;
    const dir = norm(rot([side, 0], side < 0 ? lean : -lean));
    const nrm: Pt = [-dir[1], dir[0]];
    const len = scale * (0.24 + rand() * 0.14);
    const bend = (rand() < 0.5 ? -1 : 1) * len * (0.12 + rand() * 0.1);
    const P1 = add(add(A, mul(dir, len * 0.35)), mul(nrm, bend));
    const P2 = add(add(A, mul(dir, len * 0.75)), mul(nrm, -bend * 0.6));
    const P3 = add(A, mul(dir, len));
    const stem: Pt[] = [];
    for (let i = 0; i <= 28; i++) {
      const t = i / 28, u = 1 - t;
      stem.push([
        u * u * u * A[0] + 3 * u * u * t * P1[0] + 3 * u * t * t * P2[0] + t * t * t * P3[0],
        u * u * u * A[1] + 3 * u * u * t * P1[1] + 3 * u * t * t * P2[1] + t * t * t * P3[1],
      ]);
    }
    const tipDir = norm([P3[0] - P2[0], P3[1] - P2[1]]);
    const curl = k % 2 === 0;
    if (curl) {
      // A spiral tendril continuing the stem: just over a turn, tightening, curling upward.
      const r0 = len * 0.13, turn = side < 0 ? 1 : -1;
      let a0 = Math.atan2(tipDir[1], tipDir[0]) - turn * Math.PI / 2;
      const centre = add(P3, mul(rot(tipDir, turn * 90), r0));
      for (let i = 1; i <= 26; i++) {
        const t = i / 26, r = r0 * (1 - 0.65 * t), a = a0 + turn * t * Math.PI * 2.3;
        stem.push([centre[0] + Math.cos(a) * r, centre[1] + Math.sin(a) * r]);
      }
      a0 = 0;
    }
    const branch = mk('path', { d: poly(stem), fill: 'none', stroke: '#000', 'stroke-width': String(GROW_STEM_PX), 'stroke-linecap': 'round', 'stroke-linejoin': 'round', pathLength: '1', 'stroke-dasharray': '1 1', 'stroke-dashoffset': '1' });
    const [b0, b1] = win(0, curl ? 0.75 : 0.6);
    features.push({ kind: 'draw', el: branch, from: b0, to: b1, at: A, written: '' });

    // One or two leaves along the stem, on alternating sides of it.
    const leaves = 1 + (rand() < 0.6 ? 1 : 0);
    for (let j = 0; j < leaves; j++) {
      const s = 0.45 + j * 0.3 + rand() * 0.08;
      const qi = Math.min(27, Math.round(s * 28));
      const Q = stem[qi]!, T = norm([stem[qi + 1]![0] - Q[0], stem[qi + 1]![1] - Q[1]]);
      const D = norm(rot(T, (j % 2 ? 1 : -1) * (45 + rand() * 20)));
      const N: Pt = [-D[1], D[0]];
      const l = len * (0.34 + rand() * 0.14), w = l * 0.42;
      const tip = add(Q, mul(D, l));
      const c1 = add(add(Q, mul(D, l * 0.5)), mul(N, w)), c2 = add(add(Q, mul(D, l * 0.5)), mul(N, -w));
      const leaf = mk('g', {});
      const body = document.createElementNS(SVG, 'path');
      body.setAttribute('d', `M${Q[0].toFixed(1)} ${Q[1].toFixed(1)}Q${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${tip[0].toFixed(1)} ${tip[1].toFixed(1)}Q${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${Q[0].toFixed(1)} ${Q[1].toFixed(1)}Z`);
      body.setAttribute('fill', LEAF_COLOURS[Math.floor(rand() * LEAF_COLOURS.length)]!);
      body.setAttribute('stroke', '#000'); body.setAttribute('stroke-width', String(GROW_EDGE_PX)); body.setAttribute('stroke-linejoin', 'round');
      const rib = document.createElementNS(SVG, 'path');
      const ribEnd = add(Q, mul(D, l * 0.72));
      rib.setAttribute('d', `M${Q[0].toFixed(1)} ${Q[1].toFixed(1)}L${ribEnd[0].toFixed(1)} ${ribEnd[1].toFixed(1)}`);
      rib.setAttribute('stroke', '#000'); rib.setAttribute('stroke-width', String(GROW_EDGE_PX * 0.6)); rib.setAttribute('stroke-linecap', 'round');
      leaf.append(body, rib);
      const [l0, l1] = win(0.35 + j * 0.18, 0.75 + j * 0.12);
      features.push({ kind: 'pop', el: leaf, from: l0, to: Math.min(to, l1), at: Q, written: '' });
    }

    if (!curl) {
      // An eye-bud at the tip: a candy bulb with an eye, like the painting's many eyes in things.
      const r = len * 0.16;
      const C = add(P3, mul(tipDir, r * 0.85));
      const bud = mk('g', {});
      const bulb = document.createElementNS(SVG, 'ellipse');
      bulb.setAttribute('cx', C[0].toFixed(1)); bulb.setAttribute('cy', C[1].toFixed(1));
      bulb.setAttribute('rx', r.toFixed(1)); bulb.setAttribute('ry', (r * 0.9).toFixed(1));
      bulb.setAttribute('fill', BUD_COLOURS[Math.floor(rand() * BUD_COLOURS.length)]!);
      bulb.setAttribute('stroke', '#000'); bulb.setAttribute('stroke-width', String(GROW_EDGE_PX));
      const white = document.createElementNS(SVG, 'ellipse');
      white.setAttribute('cx', C[0].toFixed(1)); white.setAttribute('cy', C[1].toFixed(1));
      white.setAttribute('rx', (r * 0.55).toFixed(1)); white.setAttribute('ry', (r * 0.42).toFixed(1));
      white.setAttribute('fill', '#fff'); white.setAttribute('stroke', '#000'); white.setAttribute('stroke-width', String(GROW_EDGE_PX * 0.7));
      const look = mul(tipDir, r * 0.2);
      const pupil = document.createElementNS(SVG, 'circle');
      pupil.setAttribute('cx', (C[0] + look[0]).toFixed(1)); pupil.setAttribute('cy', (C[1] + look[1]).toFixed(1));
      pupil.setAttribute('r', (r * 0.22).toFixed(1)); pupil.setAttribute('fill', '#000');
      bud.append(bulb, white, pupil);
      const [e0, e1] = win(0.6, 1);
      features.push({ kind: 'pop', el: bud, from: e0, to: e1, at: P3, written: '' });
    }
  }
  return { features };
}

/** The shorter turn (degrees, -180..180) from hue a to hue b. */
function hueDelta(a: number, b: number): number {
  return ((((b - a) % 360) + 540) % 360) - 180;
}

/**
 * The clip for a fill at u (0..1): the part of the box covered from the `from` edge, with a straight leading edge or
 * a gentle wave (about 2% of the box, three crests across) whose phase rolls with u, so the surface undulates as the
 * level moves and holds still when it holds.
 */
function revealPath(box: [number, number, number, number], from: string, u: number, wave: boolean): string {
  const [x, y, w, h] = box;
  if (u <= 0) return 'M0 0Z';
  const vertical = from === 'bottom' || from === 'top';
  const span = vertical ? w : h, depth = vertical ? h : w;
  const amp = wave && u < 1 ? Math.min(depth * 0.02, depth * u * 0.5, depth * (1 - u) * 0.5) : 0;
  const n = amp > 0 ? 48 : 1;
  const pts: string[] = [];
  for (let i = 0; i <= n; i++) {
    const s = i / n;
    const off = amp * Math.sin(s * Math.PI * 6 + u * Math.PI * 4);
    const along = (vertical ? x : y) + s * span;
    let p: number;
    if (from === 'bottom') p = y + h * (1 - u) + off;
    else if (from === 'top') p = y + h * u + off;
    else if (from === 'left') p = x + w * u + off;
    else p = x + w * (1 - u) + off;
    pts.push(vertical ? `${along.toFixed(1)} ${p.toFixed(1)}` : `${p.toFixed(1)} ${along.toFixed(1)}`);
  }
  // close along the `from` edge, a little beyond the box so outlines never show a seam
  const e = 4;
  if (from === 'bottom') pts.push(`${x + w + e} ${y + h + e}`, `${x - e} ${y + h + e}`);
  else if (from === 'top') pts.push(`${x + w + e} ${y - e}`, `${x - e} ${y - e}`);
  else if (from === 'left') pts.push(`${x - e} ${y + h + e}`, `${x - e} ${y - e}`);
  else pts.push(`${x + w + e} ${y + h + e}`, `${x + w + e} ${y - e}`);
  return `M${pts.join('L')}Z`;
}

/**
 * One pencil stroke like the painting's scribble layer: one to three and a half long, loose loops, drifting across
 * the object's box, with a slightly irregular radius, in a colour from the layer's palette.
 */
function scribbleStroke(into: SVGGElement, rand: () => number, bx: number, by: number, bw: number, bh: number): SVGPathElement {
  const m = Math.min(bw, bh);
  const turns = 1 + rand() * 2.5;
  const r = m * (0.18 + rand() * 0.24), squash = 0.35 + rand() * 0.5, tilt = rand() * Math.PI;
  const drift = m * (0.15 + rand() * 0.15), dir = rand() * Math.PI * 2, wob = rand() * Math.PI * 2;
  const cx0 = bx + bw * rand(), cy0 = by + bh * rand();
  const per = 28, n = Math.round(turns * per);
  let d = '';
  for (let i = 0; i <= n; i++) {
    const a = (i / per) * Math.PI * 2;
    const rr = r * (1 + 0.08 * Math.sin(3 * a + wob));
    const ex = Math.cos(a) * rr, ey = Math.sin(a) * rr * squash;
    const x = cx0 + Math.cos(dir) * drift * (a / Math.PI) + ex * Math.cos(tilt) - ey * Math.sin(tilt);
    const y = cy0 + Math.sin(dir) * drift * (a / Math.PI) + ex * Math.sin(tilt) + ey * Math.cos(tilt);
    d += `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  const total = SCRIBBLE_PALETTE.reduce((t, [, w]) => t + w, 0);
  let pick = rand() * total, colour = SCRIBBLE_PALETTE[0]![0];
  for (const [c, w] of SCRIBBLE_PALETTE) { if ((pick -= w) <= 0) { colour = c; break; } }
  const p = document.createElementNS(SVG, 'path');
  p.setAttribute('d', d);
  p.setAttribute('stroke', colour);
  p.setAttribute('pathLength', '1');
  p.setAttribute('stroke-dasharray', '1 1');
  p.setAttribute('stroke-dashoffset', '1');
  into.append(p);
  return p;
}

/**
 * One redrawn version of an outline: every point of the path is pushed by a smooth field (two crossed sine waves per
 * axis with phases from the stroke's id, moved on by `shift`), so both edges of a stroke move together and the line
 * bends along its length instead of breaking up. The path is Fresco's absolute M/C/Z; numbers come in x y pairs.
 */
function wobblePath(d: string, px: number, rand: () => number, shift = 0): string {
  const [p0, p1, p2, p3] = [rand(), rand(), rand(), rand()].map((v) => v * Math.PI * 2 + shift) as [number, number, number, number];
  const [l1, l2] = BOIL_WAVE;
  const tokens = d.match(/[MCZmcz]|-?\d+\.?\d*(?:e[-+]?\d+)?/gi) ?? [];
  let out = '';
  let pending: number | null = null;
  for (const t of tokens) {
    if (/^[a-z]$/i.test(t)) { out += t; continue; }
    const v = Number(t);
    if (pending === null) { pending = v; continue; }
    const x = pending, y = v;
    pending = null;
    const nx = x + px * (0.6 * Math.sin(x / l1 + p0) + 0.4 * Math.sin(y / l2 + p1));
    const ny = y + px * (0.6 * Math.sin(y / l1 + p2) + 0.4 * Math.sin(x / l2 + p3));
    out += `${/[0-9.]$/.test(out) ? ' ' : ''}${nx.toFixed(1)} ${ny.toFixed(1)}`;
  }
  return out;
}
