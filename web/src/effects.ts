// Effects: draw each binding's value on its object by changing the painting's own paths.
//
//   colour   glow      more vivid and more solid: OKLCH chroma up; light colours deepen only as far as needed
//                      to hold that chroma, mid and dark colours lift towards light (so glow never dims a shape)
//            hue       turns round the colour wheel, 60 degrees at amount 1
//   reveal   fill      a vivid copy of the shape rises from an edge (bottom by default), like a drawbar
//            scribble  pencil loops in a deeper shade of the shape's colour draw themselves in, clipped to it
//   motion   boil      every outline stroke jitters a few px, re-drawn 8 times a second (hand-drawn line boil)
//            pulse     the object breathes: scale about its centre, depth follows the value
//            wobble    a heat-shimmer sway and skew, depth follows the value
//            spin      the object turns about its centre, speed follows the value; it stops where it is
//            blink     a quick squash and back, on note-on or when the value rises past half
//
// A parameter binding's value is the parameter's position in its range (0..1 through the curve), so a drag, a
// preset or MIDI all move the picture; it glides (150 ms, or the binding's `glide`). A note binding's value is an
// envelope: velocity/127 with a 10 ms attack, back to 0 over the binding's `release` after note-off. A preset load
// travels across the painting as a wave from its centre. While anything has happened in the last minute, unbound
// scenery idles: a slow colour drift, the pencil-scribble layer breathing, an occasional blink. With the system's
// reduced-motion setting on, the motion effects and idle are off and colours and reveals still follow.
import type { WebSynthlandHost } from '../runtime/types';
import { layers, type Art } from './art';
import { glowColour, hexToOklch, oklchToHex, type Oklch } from './color';
import { positionOf, type Binding, type EffectSpec } from './mapping';
import { fillParts, inkParts, resolveObject, type ArtObject } from './objects';

const SVG = 'http://www.w3.org/2000/svg';
const HUE_DEG = 60;
const GLOW_OPACITY = 0.6;
/** fill: the rising copy is the shape's own colour glowing this much (vivid, lighter for mid and dark colours). */
const FILL_GLOW = 1.4;
const BOIL_PX = 10, BOIL_DEG = 0.6, BOIL_HZ = 8;
const PULSE_DEPTH = 0.05, PULSE_HZ = 0.6;
const WOBBLE_PX = 10, WOBBLE_DEG = 2, WOBBLE_HZ = 1.6;
const SPIN_RPS = 0.75;
const BLINK_MS = 160;
const SCRIBBLE_COUNT = 14, SCRIBBLE_WIDTH = 6;
const GLIDE_MS = 150, PRESET_GLIDE_MS = 400, WAVE_MS = 450;
const ATTACK_MS = 10;
/**
 * The painting is redrawn at most this often. Any change inside the art SVG makes the browser re-rasterise the
 * whole painting (one layer of ~1,900 paths), so writing at the display's 120 Hz backs the raster threads up into
 * long frames; 30 Hz ("on twos") keeps motion smooth and matches hand-drawn animation.
 */
const PAINT_HZ = 30;
const IDLE_AFTER_MS = 60_000, IDLE_FILLS = 40, IDLE_HUE_DEG = 7, IDLE_FADE_MS = 2000, IDLE_HZ = 10, SCRIBBLE_DRIFT_PX = 6;

type Fill = { el: SVGPathElement; hex: string; base: Oklch; opacity: number; hue: number; glow: number; written: string };
type Move = { spec: EffectSpec; targets: SVGPathElement[]; cx: number; cy: number; phase: number };
type Reveal = { copy: SVGPathElement; rect: SVGRectElement; box: [number, number, number, number]; from: string; written: string };
type Scribble = { strokes: SVGPathElement[]; count: number; written: string };

interface Live {
  binding: Binding;
  obj: ArtObject;
  target: number;
  shown: number;
  tau: number;
  startAt: number;
  hueGlow: Map<string, [number, number]>;
  boil: Map<string, number>;
  moves: Move[];
  reveals: Reveal[];
  scribbles: Scribble[];
  spinRate: number;
  angle: number;
  blinks: boolean;
  blinkAt: number;
  /** Being replaced: fading to 0, then its added elements are removed. */
  retiring: boolean;
  added: Element[];
}

export interface Effects {
  /** Replace the bindings: unchanged ones stay, new ones fade in and old ones fade out over `handoverMs`. */
  setBindings(bindings: Binding[], handoverMs?: number): void;
  /** The value each binding currently shows (0..1), for the debug HUD and tests. */
  shown(): Array<{ id: string; value: number }>;
  /** Notes currently sounding (held or releasing). */
  notes(): number[];
  idle(): boolean;
  dispose(): void;
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
  const motionOK = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fills = new Map<string, Fill>();
  const boilWritten = new Map<SVGPathElement, string>();
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
  const partsOf = (obj: ArtObject, spec: EffectSpec, bindingId: string): string[] => spec.parts
    ? spec.parts.flatMap((r) => {
      const got = obj.roles.get(r);
      if (!got) console.warn(`[thingsynth] binding "${bindingId}": object "${obj.id}" has no role "${r}"`);
      return got ?? [];
    })
    : obj.fills;

  // ---- build: one binding's state and the elements it adds to the painting ------------------------------------------
  const build = (binding: Binding): Live | null => {
    const obj = resolveObject(objects, binding.object);
    if (!obj) return null; // main.ts warns
    const rand = rng(binding.id);
    const L: Live = {
      binding, obj, target: 0, shown: 0, tau: binding.glide ?? GLIDE_MS, startAt: 0,
      hueGlow: new Map(), boil: new Map(), moves: [], reveals: [], scribbles: [],
      spinRate: 0, angle: 0, blinks: false, blinkAt: -Infinity, retiring: false, added: [],
    };
    for (const spec of binding.effects) {
      const ids = partsOf(obj, spec, binding.id);
      switch (spec.effect) {
        case 'glow':
        case 'hue':
          for (const id of ids) {
            if (!fillState(id)) continue;
            const cur = L.hueGlow.get(id) ?? [0, 0];
            if (spec.effect === 'hue') cur[0] += spec.amount * HUE_DEG; else cur[1] += spec.amount;
            L.hueGlow.set(id, cur);
          }
          break;
        case 'boil':
          for (const s of obj.ink) L.boil.set(s, Math.max(L.boil.get(s) ?? 0, Math.abs(spec.amount)));
          break;
        case 'fill':
          for (const id of ids) {
            const orig = art.fills.get(id), part = fillParts.get(id);
            if (!orig || !part) continue;
            const clipId = `ts-reveal-${uid++}`;
            const clip = document.createElementNS(SVG, 'clipPath');
            clip.id = clipId;
            clip.setAttribute('clipPathUnits', 'userSpaceOnUse');
            const rect = document.createElementNS(SVG, 'rect');
            for (const a of ['x', 'y', 'width', 'height']) rect.setAttribute(a, '0');
            clip.append(rect);
            stack.defs.append(clip);
            L.added.push(clip);
            const copy = orig.cloneNode(false) as SVGPathElement;
            copy.removeAttribute('id');
            copy.dataset.revealOf = id;
            const b = hexToOklch(part.fill);
            copy.setAttribute('fill', glowColour(b, 0, FILL_GLOW * Math.abs(spec.amount)));
            copy.removeAttribute('fill-opacity');
            copy.setAttribute('clip-path', `url(#${clipId})`);
            copy.style.pointerEvents = 'none';
            orig.after(copy);
            L.added.push(copy);
            L.reveals.push({ copy, rect, box: part.bbox, from: spec.from ?? 'bottom', written: '' });
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
          const first = fillParts.get(ids[0] ?? '');
          const base = hexToOklch(first?.fill ?? '#888888');
          g.setAttribute('stroke', oklchToHex({ l: Math.max(0.2, base.l - 0.28), c: base.c + 0.06, h: base.h }));
          g.setAttribute('stroke-opacity', '0.75');
          g.setAttribute('stroke-width', String(SCRIBBLE_WIDTH));
          const count = spec.count ?? SCRIBBLE_COUNT;
          const [bx, by, bw, bh] = obj.bbox;
          const strokes: SVGPathElement[] = [];
          for (let k = 0; k < count; k++) strokes.push(scribbleStroke(g, rand, bx, by, bw, bh));
          stack.ink.before(g);
          L.added.push(g);
          L.scribbles.push({ strokes, count, written: '' });
          break;
        }
        case 'pulse':
        case 'wobble':
        case 'spin':
        case 'blink': {
          if (!motionOK) break;
          const targets: SVGPathElement[] = [];
          for (const id of ids) {
            const el = art.fills.get(id);
            if (el) targets.push(el);
          }
          for (const s of obj.ownInk) { const el = art.ink.get(s); if (el) targets.push(el); }
          const m: Move = { spec, targets, cx: obj.centroid[0], cy: obj.centroid[1], phase: rand() * Math.PI * 2 };
          L.moves.push(m);
          if (spec.effect === 'blink') L.blinks = true;
          break;
        }
      }
    }
    // Reveal copies move with their originals.
    for (const m of L.moves) for (const r of L.reveals) if (m.targets.some((t) => t.id === r.copy.dataset.revealOf)) m.targets.push(r.copy);
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

  // ---- idle scenery: unbound mid-sized fills, a deterministic sample (re-chosen when the bindings change) ----------
  let idleFills: Array<{ id: string; period: number; phase: number }> = [];
  const chooseIdle = (): void => {
    const bound = new Set(live.filter((L) => !L.retiring).flatMap((L) => L.obj.fills));
    const idleRand = rng('idle');
    idleFills = Array.from(fillParts.values())
      .filter((f) => !bound.has(f.id) && f.area > 15_000 && f.area < 200_000)
      .map((f) => ({ f, k: idleRand() }))
      .sort((a, b) => a.k - b.k)
      .slice(0, IDLE_FILLS)
      .map(({ f }) => ({ id: f.id, period: 7000 + idleRand() * 6000, phase: idleRand() * Math.PI * 2 }))
      .filter((x) => fillState(x.id));
  };
  chooseIdle();

  // ---- values -------------------------------------------------------------------------------------------------------
  const read = (L: Live): number => (L.binding.kind === 'param' ? positionOf(L.binding, host.get(L.binding.param)) : L.target);
  for (const L of live) if (L.binding.kind === 'param') L.target = L.shown = read(L);

  const [px, py, pw, ph] = layers.painted;
  const origin: [number, number] = [px + pw / 2, py + ph / 2];
  const maxDist = Math.hypot(pw / 2, ph / 2);

  let raf = 0, last = 0, lastBoil = 0, lastIdle = 0, nextIdleBlink = 0, lastPaint = 0, motionDt = 0;
  let lastActivity = -Infinity;
  let idleLevel = 0;
  /** Set when values moved since the last colour paint (a glide may settle between two paints). */
  let colourDirty = false;
  let disposed = false;
  const activity = (): void => { lastActivity = performance.now(); };

  // ---- painting -----------------------------------------------------------------------------------------------------
  const paintColours = (now: number): void => {
    for (const f of fills.values()) { f.hue = 0; f.glow = 0; }
    for (const L of live) for (const [id, [hue, glow]] of L.hueGlow) {
      const f = fills.get(id);
      if (f) { f.hue += hue * L.shown; f.glow += glow * L.shown; }
    }
    if (idleLevel > 0) for (const x of idleFills) {
      const f = fills.get(x.id);
      if (f) f.hue += IDLE_HUE_DEG * idleLevel * Math.sin((2 * Math.PI * now) / x.period + x.phase);
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
  };

  const paintReveals = (): void => {
    for (const L of live) {
      const v = Math.max(0, Math.min(1, L.shown));
      for (const r of L.reveals) {
        const [x, y, w, h] = r.box;
        let rx = x, ry = y, rw = w, rh = h;
        if (r.from === 'bottom') { ry = y + h * (1 - v); rh = h * v; }
        else if (r.from === 'top') rh = h * v;
        else if (r.from === 'left') rw = w * v;
        else { rx = x + w * (1 - v); rw = w * v; }
        const key = `${rx.toFixed(1)} ${ry.toFixed(1)} ${rw.toFixed(1)} ${rh.toFixed(1)}`;
        if (key === r.written) continue;
        r.written = key;
        r.rect.setAttribute('x', rx.toFixed(1)); r.rect.setAttribute('y', ry.toFixed(1));
        r.rect.setAttribute('width', rw.toFixed(1)); r.rect.setAttribute('height', rh.toFixed(1));
      }
      for (const s of L.scribbles) {
        const drawn = v * s.count;
        const key = drawn.toFixed(3);
        if (key === s.written) continue;
        s.written = key;
        s.strokes.forEach((p, i) => p.setAttribute('stroke-dashoffset', (1 - Math.max(0, Math.min(1, drawn - i))).toFixed(3)));
      }
    }
  };

  /** Motion: transforms per element, composed from every binding that moves it, plus the boil. */
  const paintMotion = (now: number, dt: number, reroll: boolean): boolean => {
    let busy = false;
    const parts = new Map<SVGPathElement, string[]>();
    const add = (el: SVGPathElement, t: string): void => { const l = parts.get(el); if (l) l.push(t); else parts.set(el, [t]); };
    const t = now / 1000;
    for (const L of live) {
      const v = L.shown;
      for (const m of L.moves) {
        const { cx, cy } = m;
        let tr = '';
        if (m.spec.effect === 'pulse' && v > 1e-3) {
          const s = 1 + m.spec.amount * PULSE_DEPTH * v * Math.sin(2 * Math.PI * (m.spec.hz ?? PULSE_HZ) * t + m.phase);
          tr = `translate(${cx.toFixed(1)} ${cy.toFixed(1)}) scale(${s.toFixed(4)}) translate(${(-cx).toFixed(1)} ${(-cy).toFixed(1)})`;
          busy = true;
        } else if (m.spec.effect === 'wobble' && v > 1e-3) {
          const hz = m.spec.hz ?? WOBBLE_HZ;
          const dx = m.spec.amount * WOBBLE_PX * v * Math.sin(2 * Math.PI * hz * t + m.phase);
          const k = m.spec.amount * WOBBLE_DEG * v * Math.sin(2 * Math.PI * hz * 1.3 * t + m.phase * 1.7);
          tr = `translate(${(cx + dx).toFixed(1)} ${cy.toFixed(1)}) skewX(${k.toFixed(3)}) translate(${(-cx).toFixed(1)} ${(-cy).toFixed(1)})`;
          busy = true;
        } else if (m.spec.effect === 'spin') {
          const rate = m.spec.amount * SPIN_RPS * v;
          if (Math.abs(rate) > 1e-4) { L.angle = (L.angle + 360 * rate * (dt / 1000)) % 360; busy = true; }
          if (Math.abs(L.angle) > 0.01) tr = `rotate(${L.angle.toFixed(2)} ${cx.toFixed(1)} ${cy.toFixed(1)})`;
        } else if (m.spec.effect === 'blink') {
          const p = (now - L.blinkAt) / BLINK_MS;
          if (p >= 0 && p < 1) {
            const s = 1 - 0.88 * Math.abs(m.spec.amount) * Math.sin(Math.PI * p);
            tr = `translate(${cx.toFixed(1)} ${cy.toFixed(1)}) scale(1 ${s.toFixed(3)}) translate(${(-cx).toFixed(1)} ${(-cy).toFixed(1)})`;
            busy = true;
          }
        }
        if (tr) for (const el of m.targets) add(el, tr);
      }
    }
    // Boil: amplitude per stroke = the largest from any binding; the jitter is re-rolled BOIL_HZ times a second.
    if (motionOK) {
      const amp = new Map<string, number>();
      for (const L of live) for (const [id, a] of L.boil) amp.set(id, Math.max(amp.get(id) ?? 0, a * L.shown));
      const r = (): number => Math.random() * 2 - 1;
      for (const [id, a] of amp) {
        const el = art.ink.get(id);
        if (!el) continue;
        if (a <= 0.002) { boilWritten.delete(el); continue; }
        busy = true;
        let b = boilWritten.get(el);
        if (reroll || !b) {
          const s = inkParts.get(id)!;
          b = `translate(${(r() * BOIL_PX * a).toFixed(1)} ${(r() * BOIL_PX * a).toFixed(1)}) rotate(${(r() * BOIL_DEG * a).toFixed(2)} ${s.centroid[0]} ${s.centroid[1]})`;
          boilWritten.set(el, b);
        }
        add(el, b);
      }
    }
    for (const [el, list] of parts) {
      const s = list.join(' ');
      if (el.getAttribute('transform') !== s) el.setAttribute('transform', s);
      transformed.add(el);
    }
    for (const el of Array.from(transformed)) {
      if (parts.has(el)) continue;
      el.removeAttribute('transform');
      transformed.delete(el);
    }
    return busy;
  };

  // ---- the loop -----------------------------------------------------------------------------------------------------
  const frame = (now: number): void => {
    raf = 0;
    if (disposed) return;
    const dt = last ? Math.max(0, now - last) : 16;
    last = now;
    let moving = false;
    if (live.some((L) => L.retiring && L.shown === 0)) {
      for (const L of live) if (L.retiring && L.shown === 0) retire(L);
      live = live.filter((L) => !(L.retiring && L.shown === 0));
      colourDirty = true;
    }
    for (const L of live) {
      if (now < L.startAt) { moving = true; continue; }
      const d = L.target - L.shown;
      if (d === 0) continue;
      colourDirty = true;
      if (Math.abs(d) < 1e-3) L.shown = L.target;
      else { L.shown += d * (L.tau > 0 ? 1 - Math.exp(-dt / L.tau) : 1); moving = true; }
    }
    // Idle fades in while there has been activity in the last minute, and out after.
    const idleWanted = motionOK && now - lastActivity < IDLE_AFTER_MS ? 1 : 0;
    if (idleLevel !== idleWanted) {
      const step = dt / IDLE_FADE_MS;
      idleLevel = idleWanted > idleLevel ? Math.min(1, idleLevel + step) : Math.max(0, idleLevel - step);
    }
    const idleTick = idleLevel > 0 && now - lastIdle >= 1000 / IDLE_HZ;
    if (idleTick) {
      lastIdle = now;
      const dx = SCRIBBLE_DRIFT_PX * idleLevel * Math.sin(now / 2300), dy = SCRIBBLE_DRIFT_PX * idleLevel * Math.cos(now / 3100);
      stack.scribbles.setAttribute('transform', `translate(${dx.toFixed(1)} ${dy.toFixed(1)})`);
      if (idleLevel === 1 && now >= nextIdleBlink) {
        const blinkers = live.filter((L) => L.blinks);
        const pick = blinkers[Math.floor(Math.random() * blinkers.length)];
        if (pick && nextIdleBlink > 0) pick.blinkAt = now;
        nextIdleBlink = now + 4000 + Math.random() * 5000;
      }
    } else if (idleLevel === 0 && stack.scribbles.hasAttribute('transform')) stack.scribbles.removeAttribute('transform');
    // Values advance every frame; the DOM is written at most PAINT_HZ times a second (spin integrates the time
    // between writes so its speed is exact).
    motionDt += dt;
    let busy = true;
    if (now - lastPaint >= 1000 / PAINT_HZ - 1) {
      lastPaint = now;
      if (colourDirty || idleTick || idleLevel !== idleWanted) { paintColours(now); colourDirty = false; }
      paintReveals();
      const reroll = now - lastBoil >= 1000 / BOIL_HZ;
      if (reroll) lastBoil = now;
      busy = paintMotion(now, motionDt, reroll);
      motionDt = 0;
    }
    if (moving || busy || idleLevel > 0 || idleWanted > 0) raf = requestAnimationFrame(frame);
    else { last = 0; motionDt = 0; }
  };
  const kick = (): void => {
    if (disposed) return;
    if (document.hidden) {
      // No frames in a background tab: jump to the targets so the picture is right when it is shown again.
      for (const L of live) { L.shown = L.target; L.startAt = 0; }
      paintColours(performance.now());
      paintReveals();
      return;
    }
    if (!raf) raf = requestAnimationFrame(frame);
  };

  // ---- inputs -------------------------------------------------------------------------------------------------------
  const offParam = host.onParam((id) => {
    let hit = false;
    for (const L of live) {
      if (L.retiring || L.binding.kind !== 'param' || L.binding.param !== id) continue;
      const before = L.target;
      L.target = read(L);
      L.tau = L.binding.glide ?? GLIDE_MS;
      L.startAt = 0;
      if (L.blinks && before < 0.5 && L.target >= 0.5) L.blinkAt = performance.now();
      hit = true;
    }
    // Only once audio runs: the boot-time preset load is not anybody playing.
    if (host.audio.running()) activity();
    if (hit || (idleLevel === 0 && host.audio.running())) kick();
  });
  const offPreset = host.onPreset((index) => {
    if (index < 0) return; // an edit, not a load
    const now = performance.now();
    for (const L of live) {
      if (L.retiring || L.binding.kind !== 'param') continue;
      L.target = read(L);
      L.tau = L.binding.glide ?? PRESET_GLIDE_MS;
      const [cx, cy] = L.obj.centroid;
      L.startAt = now + (WAVE_MS * Math.hypot(cx - origin[0], cy - origin[1])) / maxDist;
    }
    kick();
  });

  // Notes: wrap the host's note functions, which the computer keyboard, Web MIDI and touch all go through.
  const origOn = host.noteOn.bind(host), origOff = host.noteOff.bind(host);
  const sounding = new Set<number>();
  host.noteOn = (note, velocity) => {
    origOn(note, velocity);
    sounding.add(note);
    activity();
    const now = performance.now();
    for (const L of byNote.get(note) ?? []) {
      L.target = Math.max(0, Math.min(1, velocity / 127));
      L.tau = ATTACK_MS;
      L.startAt = 0;
      if (L.blinks) L.blinkAt = now;
    }
    kick();
  };
  host.noteOff = (note) => {
    origOff(note);
    sounding.delete(note);
    activity();
    for (const L of byNote.get(note) ?? []) {
      L.target = 0;
      L.tau = L.binding.kind === 'note' ? L.binding.release / 3 : GLIDE_MS;
    }
    kick();
  };
  const onPointer = (): void => { activity(); kick(); };
  window.addEventListener('pointerdown', onPointer, { passive: true });
  const onVis = (): void => { if (!document.hidden) kick(); };
  document.addEventListener('visibilitychange', onVis);

  paintColours(performance.now());
  paintReveals();
  kick();

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
      L.tau = handoverMs / 3;
      fresh.push(L);
    }
    const leaving = Array.from(old.values());
    for (const L of leaving) { L.retiring = true; L.target = 0; L.tau = handoverMs / 3; L.startAt = 0; }
    live = [...fresh, ...leaving, ...live.filter((L) => L.retiring)];
    indexNotes();
    chooseIdle();
    colourDirty = true;
    kick();
  };

  return {
    setBindings,
    shown: () => live.filter((L) => !L.retiring).map((L) => ({ id: L.binding.id, value: L.shown })),
    notes: () => Array.from(sounding).sort((a, b) => a - b),
    idle: () => idleLevel > 0,
    dispose: () => {
      disposed = true;
      offParam(); offPreset();
      host.noteOn = origOn; host.noteOff = origOff;
      window.removeEventListener('pointerdown', onPointer);
      document.removeEventListener('visibilitychange', onVis);
      if (raf) cancelAnimationFrame(raf);
    },
  };
}

/** One loopy pencil stroke, like the painting's scribble layer: a few elliptical loops drifting across the box. */
function scribbleStroke(into: SVGGElement, rand: () => number, bx: number, by: number, bw: number, bh: number): SVGPathElement {
  const m = Math.min(bw, bh);
  const loops = 2 + Math.floor(rand() * 4);
  const r = m * (0.08 + rand() * 0.14), squash = 0.45 + rand() * 0.45, tilt = rand() * Math.PI;
  const drift = m * (0.06 + rand() * 0.1), dir = rand() * Math.PI * 2;
  const cx0 = bx + bw * (0.15 + rand() * 0.7), cy0 = by + bh * (0.15 + rand() * 0.7);
  const n = loops * 22;
  let d = '';
  for (let i = 0; i <= n; i++) {
    const a = (i / 22) * Math.PI * 2;
    const ex = Math.cos(a) * r, ey = Math.sin(a) * r * squash;
    const x = cx0 + Math.cos(dir) * drift * (a / Math.PI) + ex * Math.cos(tilt) - ey * Math.sin(tilt);
    const y = cy0 + Math.sin(dir) * drift * (a / Math.PI) + ex * Math.sin(tilt) + ey * Math.cos(tilt);
    d += `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  const p = document.createElementNS(SVG, 'path');
  p.setAttribute('d', d);
  p.setAttribute('pathLength', '1');
  p.setAttribute('stroke-dasharray', '1 1');
  p.setAttribute('stroke-dashoffset', '1');
  into.append(p);
  return p;
}
