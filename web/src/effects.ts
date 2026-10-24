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
//             shape's revealed colour to one hue instead
//   scribble  pencil loops drawn in, clipped to the shape, in the painting's own scribble style (`count` strokes)
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
import { glowColour, hexToOklch, type Oklch } from './color';
import { positionOf, type Binding, type Ease, type EffectSpec } from './mapping';
import { fillParts, resolveObject, type ArtObject } from './objects';

const SVG = 'http://www.w3.org/2000/svg';
const HUE_DEG = 60;
const GLOW_OPACITY = 0.6;
/** fill: the revealed copy is the shape's own colour glowing this much (vivid, lighter for mid and dark colours). */
const FILL_GLOW = 1.4;
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
  copy: SVGPathElement; clip: SVGPathElement; base: Oklch; glow: number; turn: number;
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
        case 'blink':
          for (const id of ids) { const el = art.fills.get(id); if (el) tr.targets.push(el); }
          for (const s of obj.ownInk) { const el = art.ink.get(s); if (el) tr.targets.push(el); }
          break;
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
        const colour = glowColour(r.base, r.turn * u, r.glow);
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
