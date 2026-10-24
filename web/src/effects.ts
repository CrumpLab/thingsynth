// Effects: draw each bound parameter's value on its object, by changing the painting's own paths.
//   glow  the fills get more vivid and more solid: OKLCH chroma up, deepened just enough to hold that chroma
//         (pastels near white have no room for it otherwise), and less of the wash showing through
//   hue   the fills turn round the colour wheel, up to 60 degrees at amount 1 (negative turns the other way)
//   boil  the object's ink strokes jitter by a few pixels and a fraction of a degree, re-drawn 8 times a
//         second, the hand-drawn "line boil"; amplitude grows with the value, still at 0
// A binding's value is the parameter's position in its range (0..1 through the curve), so whatever moves the
// parameter (a drag, a preset, MIDI) moves the picture. Values glide (150 ms; 400 ms after a preset load).
// Several bindings may touch the same fill or stroke: hue turns add up, glows add up, boils take the largest.
import type { WebSynthlandHost } from '../runtime/types';
import type { Art } from './art';
import { hexToOklch, oklchToHex, type Oklch } from './color';
import { positionOf, type Binding } from './mapping';
import { fillParts, inkParts, type ArtObject } from './objects';

const HUE_DEG = 60;
const GLOW_CHROMA = 0.09;
const GLOW_DARKEN = 0.18;
const GLOW_OPACITY = 0.6;
const BOIL_PX = 10;
const BOIL_DEG = 0.6;
const BOIL_HZ = 8;
const GLIDE_MS = 150;
const PRESET_GLIDE_MS = 400;

interface FillState { el: SVGPathElement; hex: string; base: Oklch; opacity: number; hue: number; glow: number; written: string }
interface InkState { el: SVGPathElement; cx: number; cy: number; amp: number }
interface Live {
  binding: Binding;
  target: number;
  shown: number;
  /** fill id -> [hue turn per unit value, glow per unit value] */
  fills: Map<string, [number, number]>;
  /** ink id -> boil per unit value */
  ink: Map<string, number>;
}

export interface Effects {
  /** The value each binding currently shows (0..1), for the debug HUD. */
  shown(): Array<{ id: string; param: string; value: number }>;
  dispose(): void;
}

export function mountEffects(art: Art, host: WebSynthlandHost, objects: Map<string, ArtObject>, bindings: Binding[]): Effects {
  const fills = new Map<string, FillState>();
  const ink = new Map<string, InkState>();
  const live: Live[] = [];

  for (const binding of bindings) {
    const obj = objects.get(binding.object);
    if (!obj) continue; // painting.ts already warned
    const L: Live = { binding, target: 0, shown: 0, fills: new Map(), ink: new Map() };
    for (const spec of binding.effects) {
      if (spec.effect === 'boil') {
        for (const id of obj.ink) L.ink.set(id, Math.max(L.ink.get(id) ?? 0, Math.abs(spec.amount)));
        continue;
      }
      const ids = spec.parts ? spec.parts.flatMap((r) => {
        const got = obj.roles.get(r);
        if (!got) console.warn(`[thingsynth] binding "${binding.id}": object "${obj.id}" has no role "${r}"`);
        return got ?? [];
      }) : obj.fills;
      for (const id of ids) {
        const cur = L.fills.get(id) ?? [0, 0];
        if (spec.effect === 'hue') cur[0] += spec.amount * HUE_DEG;
        else cur[1] += spec.amount;
        L.fills.set(id, cur);
      }
    }
    for (const id of L.fills.keys()) {
      const el = art.fills.get(id);
      const part = fillParts.get(id);
      if (!el || !part || fills.has(id)) continue;
      fills.set(id, { el, hex: part.fill, base: hexToOklch(part.fill), opacity: part.opacity, hue: 0, glow: 0, written: '' });
    }
    for (const id of L.ink.keys()) {
      const el = art.ink.get(id);
      const part = inkParts.get(id);
      if (!el || !part || ink.has(id)) continue;
      ink.set(id, { el, cx: part.centroid[0], cy: part.centroid[1], amp: 0 });
    }
    live.push(L);
  }

  const read = (L: Live): number => positionOf(L.binding, host.get(L.binding.param));
  for (const L of live) L.target = L.shown = read(L);

  let glideMs = GLIDE_MS;
  let glideUntil = 0;
  let raf = 0;
  let last = 0;
  let lastBoil = 0;
  let disposed = false;

  const paintFills = (): void => {
    for (const f of fills.values()) { f.hue = 0; f.glow = 0; }
    for (const L of live) {
      for (const [id, [hue, glow]] of L.fills) {
        const f = fills.get(id);
        if (!f) continue;
        f.hue += hue * L.shown;
        f.glow += glow * L.shown;
      }
    }
    for (const f of fills.values()) {
      const g = Math.max(-1, Math.min(1.5, f.glow));
      const atRest = Math.abs(f.hue) < 0.05 && Math.abs(g) < 1e-3;
      // At rest the fill gets exactly the painted colour back (no round-trip drift).
      const col = atRest ? f.hex : oklchToHex(
        { l: f.base.l, c: Math.max(0, f.base.c + GLOW_CHROMA * g), h: (f.base.h + f.hue + 360) % 360 },
        GLOW_DARKEN * Math.max(0, g),
      );
      const op = atRest ? f.opacity : Math.max(0, Math.min(1, f.opacity + (1 - f.opacity) * GLOW_OPACITY * Math.max(0, g)));
      const key = `${col}/${op.toFixed(3)}`;
      if (key === f.written) continue;
      f.written = key;
      f.el.setAttribute('fill', col);
      if (op < 1) f.el.setAttribute('fill-opacity', op.toFixed(3));
      else f.el.removeAttribute('fill-opacity');
    }
  };

  const boil = (reroll: boolean): boolean => {
    for (const s of ink.values()) s.amp = 0;
    for (const L of live) for (const [id, a] of L.ink) {
      const s = ink.get(id);
      if (s) s.amp = Math.max(s.amp, a * L.shown);
    }
    let any = false;
    for (const s of ink.values()) {
      if (s.amp <= 0.002) {
        if (s.el.hasAttribute('transform')) s.el.removeAttribute('transform');
        continue;
      }
      any = true;
      if (!reroll) continue;
      const r = (): number => Math.random() * 2 - 1;
      const dx = r() * BOIL_PX * s.amp, dy = r() * BOIL_PX * s.amp, deg = r() * BOIL_DEG * s.amp;
      s.el.setAttribute('transform', `translate(${dx.toFixed(1)} ${dy.toFixed(1)}) rotate(${deg.toFixed(2)} ${s.cx} ${s.cy})`);
    }
    return any;
  };

  const frame = (now: number): void => {
    raf = 0;
    if (disposed) return;
    // Real elapsed time, uncapped: after a throttled or stalled stretch the glide catches up instead of crawling.
    const dt = last ? Math.max(0, now - last) : 16;
    last = now;
    const tau = now < glideUntil ? glideMs : GLIDE_MS;
    const a = 1 - Math.exp(-dt / tau);
    let moving = false;
    for (const L of live) {
      const d = L.target - L.shown;
      if (Math.abs(d) < 1e-3) L.shown = L.target;
      else { L.shown += d * a; moving = true; }
    }
    paintFills();
    const reroll = now - lastBoil >= 1000 / BOIL_HZ;
    if (reroll) lastBoil = now;
    const boiling = boil(reroll);
    if (moving || boiling) raf = requestAnimationFrame(frame);
    else last = 0;
  };
  const kick = (): void => {
    if (disposed) return;
    if (document.hidden) {
      // No frames in a background tab: jump to the targets so the picture is right when it is shown again.
      for (const L of live) L.shown = L.target;
      paintFills();
      boil(true);
      return;
    }
    if (!raf) raf = requestAnimationFrame(frame);
  };

  const offParam = host.onParam((id) => {
    let hit = false;
    for (const L of live) if (L.binding.param === id) { L.target = read(L); hit = true; }
    if (hit) kick();
  });
  const offPreset = host.onPreset(() => {
    glideMs = PRESET_GLIDE_MS;
    glideUntil = performance.now() + PRESET_GLIDE_MS * 2;
    for (const L of live) L.target = read(L);
    kick();
  });
  const onVis = (): void => { if (!document.hidden) kick(); };
  document.addEventListener('visibilitychange', onVis);

  paintFills();
  kick();

  return {
    shown: () => live.map((L) => ({ id: L.binding.id, param: L.binding.param, value: L.shown })),
    dispose: () => {
      disposed = true;
      offParam(); offPreset();
      document.removeEventListener('visibilitychange', onVis);
      if (raf) cancelAnimationFrame(raf);
    },
  };
}
