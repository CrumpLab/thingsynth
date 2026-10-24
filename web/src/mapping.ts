// mapping.json: what in the painting controls and shows which Tonewheel parameter.
//   v1 (thingsynth.mapping/1): `regions`, hand-drawn rects/polygons in image pixels that set a parameter.
//   v2 (thingsynth.mapping/2): adds `bindings`, which name an object from art/<slug>/objects.json (a group of the
//      painting's own fill shapes), the parameter it shows, an optional gesture that makes it a control, and the
//      effects that draw the parameter's value on the object. v2 keeps `regions` for anything not yet an object.
// This file knows nothing about the DOM or the engine: it parses, validates and does the value math.
import type { ParamDesc } from '../runtime/types';

export type Gesture = 'tap' | 'drag-x' | 'drag-y' | 'hold' | 'hover';
export type Curve = 'linear' | 'log';
export type Point = [number, number];

export type RegionShape = { rect: [number, number, number, number] } | { polygon: Point[] };

/** What every control shares: a parameter, its range and curve, and how a gesture moves it. */
export interface Control {
  /** Stable name used in debug output; defaults to `${param}#${index}`. */
  id: string;
  label?: string;
  gesture: Gesture;
  /** A Tonewheel parameter id from web/public/tonewheel/plugin.json (e.g. "amp.drive"). */
  param: string;
  /** Values in the parameter's real units; [min, max] may be reversed to invert the direction. */
  range: [number, number];
  curve: Curve;
  /** tap: how far one tap moves the value (default 1 for int/bool/choice, the whole range for floats). */
  step?: number;
}

export interface RegionEntry extends Control {
  region: RegionShape;
}

export type EffectKind = 'glow' | 'hue' | 'tint' | 'fill' | 'scribble' | 'grow' | 'rays' | 'eye' | 'flames' | 'wind' | 'swing' | 'sprites' | 'vanish' | 'boing' | 'line' | 'boil' | 'swell' | 'lean' | 'spin' | 'blink';
export const EFFECTS: readonly EffectKind[] = ['glow', 'hue', 'tint', 'fill', 'scribble', 'grow', 'rays', 'eye', 'flames', 'wind', 'swing', 'sprites', 'vanish', 'boing', 'line', 'boil', 'swell', 'lean', 'spin', 'blink'];

/** flames: one tongue, standing at `at` (canvas px), tilted `angle` degrees, `size` times the standard flame, starting
 * `delay` (0..1) into the effect's span. */
export interface FlameSpot { at: [number, number]; angle: number; size: number; delay: number }

/** wind: one band, a crescent round the centre at `radius`, sweeping from `from` to `to` degrees, `width` thick at
 * its middle, starting `start` (0..1) into the effect's span. */
/** sprites: one outlined shape, drawn at full size by `d` (canvas px), growing from `at` over [start, end] of the
 * effect's span: `grow` scale (both ways), x or y (one way). */
export interface Sprite {
  d: string; fill: string; edge: number; at: [number, number]; start: number; end: number; grow: 'scale' | 'x' | 'y';
  /** shrinks back to nothing over [outStart, outEnd] of the span */
  outStart?: number; outEnd?: number;
  /** instead of growing, revealed by a wedge round `at` sweeping from `from` to `to` degrees (0 = right, 90 = up) */
  sweep?: { from: number; to: number };
}

export interface WindBand { radius: number; from: number; to: number; width: number; color: string; start: number }
/** Older names still read: pulse and wobble were free-running; as frames of the timeline they are swell and lean. */
const EFFECT_ALIASES: Record<string, EffectKind> = { pulse: 'swell', wobble: 'lean' };
export type FillFrom = 'bottom' | 'top' | 'left' | 'right';
export type Ease = 'linear' | 'in' | 'out' | 'in-out';
export const EASES: readonly Ease[] = ['linear', 'in', 'out', 'in-out'];

export interface EffectSpec {
  effect: EffectKind;
  /** Roles from the object's `parts` to apply to; omitted = every fill of the object. */
  parts?: string[];
  /** Strength at the last frame, 1 = the effect's designed range; negative reverses direction. */
  amount: number;
  /** The part of the binding's timeline (0..1) this effect plays over, default [0, 1]. */
  span?: [number, number];
  /** How it moves through its span: linear (default), in (slow start), out (slow end), in-out. */
  ease?: Ease;
  /** fill: the edge the colour rises from (default bottom). */
  from?: FillFrom;
  /** fill: the leading edge, straight (default) or a gentle hand-drawn wave that rolls as it moves. */
  edge?: 'straight' | 'wave';
  /** fill: degrees the revealed colour's hue has turned by the last frame (it turns as the fill advances). */
  turn?: number;
  /** fill: a hue (OKLCH degrees, e.g. 50 = orange) the revealed colour moves to as the fill advances, the short way
   * round; every shape of the object converges on it (instead of `turn`, which turns each by the same amount). */
  toward?: number;
  /** fill: the revealed colour at the last frame (hex); it moves there from the shape's glowing colour as the fill
   * advances. Overrides `turn` and `toward`. */
  color?: string;
  /** scribble: how many pencil strokes at full value (default 14). grow: how many branches (default 8). rays: how
   * many rays (default 16). */
  count?: number;
  /** rays: the centre they fan out from. eye: the eye's centre. Canvas px. */
  at?: [number, number];
  /** rays: [inner radius, long ray length, short ray length]. eye: [half width, half height]. Canvas px. */
  size?: number[];
  /** rays, flames: shapes (fill ids) that stay in front of them, besides the object itself. */
  front?: string[];
  /** flames: where the tongues stand. */
  spots?: FlameSpot[];
  /** wind: its bands. */
  bands?: WindBand[];
  /** boing: where the eye springs to (canvas px), from `at`. */
  to?: [number, number];
  /** swing: degrees the parts turn about `at` by the last frame (negative = anticlockwise). */
  angle?: number;
  /** eye: draw it above the painting's ink (and over anything else drawn there before it). */
  over?: boolean;
  /** sprites: the shapes, and where they go: under the object, on it (clipped to it, under its ink), or over the ink. */
  items?: Sprite[];
  place?: 'under' | 'on' | 'over' | 'around';
}

interface BindingBase {
  id: string;
  label?: string;
  /** An object id from objects.json, or "#fNNN" when the mapping named a single `part`. */
  object: string;
  /** param bindings: tap | drag-x | drag-y | hold | hover. note bindings: tap | hold (plays the note). */
  gesture?: Gesture;
  effects: EffectSpec[];
  /** How long the picture takes to follow a change, ms (default 150; e.g. 1500 for a rotor spinning up). */
  glide?: number;
  /** Shuffle leaves a locked binding where it is. */
  locked?: boolean;
}

/** v2: an object of the painting bound to a parameter. Without `gesture` it only shows the value. */
export interface ParamBinding extends BindingBase, Omit<Control, 'gesture' | 'id' | 'label'> {
  kind: 'param';
}

/** v2: an object of the painting bound to a note: it shows the note's envelope (velocity, then release). */
export interface NoteBinding extends BindingBase {
  kind: 'note';
  /** MIDI note number, 21..108 on a piano. */
  note: number;
  /** Release time in ms after note-off (default 300). */
  release: number;
}

export type Binding = ParamBinding | NoteBinding;

export interface Mapping {
  schema: 'thingsynth.mapping/1' | 'thingsynth.mapping/2';
  image: string;
  size: [number, number];
  defaultPreset?: string;
  regions: RegionEntry[];
  bindings: Binding[];
}

/** Anything with a parameter, range and curve (regions and bindings), for the value math below. */
export type Ranged = Pick<Control, 'range' | 'curve'>;

export const GESTURES: readonly Gesture[] = ['tap', 'drag-x', 'drag-y', 'hold', 'hover'];

function fail(where: string, msg: string): never {
  throw new Error(`mapping.json ${where}: ${msg}`);
}

function isPoint(v: unknown): v is Point {
  return Array.isArray(v) && v.length === 2 && v.every((n) => typeof n === 'number' && Number.isFinite(n));
}

/** Validate the parsed JSON; throws a readable error for the first problem. */
export function parseMapping(raw: unknown): Mapping {
  if (!raw || typeof raw !== 'object') fail('', 'not an object');
  const m = raw as Record<string, unknown>;
  if (m.schema !== 'thingsynth.mapping/1' && m.schema !== 'thingsynth.mapping/2') fail('schema', 'expected "thingsynth.mapping/1" or "/2"');
  if (typeof m.image !== 'string') fail('image', 'expected a path string');
  if (!isPoint(m.size) || m.size[0] <= 0 || m.size[1] <= 0) fail('size', 'expected [width, height] in pixels');
  const rawRegions = m.regions ?? [];
  if (!Array.isArray(rawRegions)) fail('regions', 'expected an array');
  const regions = rawRegions.map((r, i) => parseRegion(r, i));
  let bindings: Binding[] = [];
  if (m.schema === 'thingsynth.mapping/2') {
    const rawBindings = m.bindings ?? [];
    if (!Array.isArray(rawBindings)) fail('bindings', 'expected an array');
    bindings = rawBindings.map((b, i) => parseBinding(b, i));
  } else if (m.bindings !== undefined) fail('bindings', 'needs schema "thingsynth.mapping/2"');
  const mapping: Mapping = { schema: m.schema, image: m.image, size: m.size, regions, bindings };
  if (typeof m.defaultPreset === 'string') mapping.defaultPreset = m.defaultPreset;
  return mapping;
}

/** The fields regions and bindings share: param, range, curve, id, label, step. */
function parseCommon(r: Record<string, unknown>, where: string, i: number): Omit<Control, 'gesture'> {
  if (typeof r.param !== 'string' || !r.param) fail(where, 'param must be a parameter id');
  if (!isPoint(r.range)) fail(where, 'range must be [min, max]');
  const curve = r.curve ?? 'linear';
  if (curve !== 'linear' && curve !== 'log') fail(where, 'curve must be linear or log');
  if (curve === 'log' && (r.range[0] <= 0 || r.range[1] <= 0)) fail(where, 'log curve needs a positive range');
  const c: Omit<Control, 'gesture'> = { id: typeof r.id === 'string' && r.id ? r.id : `${r.param}#${i}`, param: r.param, range: r.range, curve };
  if (typeof r.label === 'string') c.label = r.label;
  if (typeof r.step === 'number' && r.step > 0) c.step = r.step;
  return c;
}

function parseBinding(raw: unknown, i: number): Binding {
  const where = `bindings[${i}]`;
  if (!raw || typeof raw !== 'object') fail(where, 'not an object');
  const r = raw as Record<string, unknown>;
  const hasObject = typeof r.object === 'string' && r.object !== '';
  const hasPart = typeof r.part === 'string' && /^f\d+$/.test(r.part);
  if (hasObject === hasPart) fail(where, 'give exactly one of "object" (an id from objects.json) or "part" (a fill id like "f006")');
  const object = hasObject ? (r.object as string) : `#${r.part as string}`;
  if (typeof r.object === 'string' && r.object.startsWith('#')) fail(where, 'object ids may not start with "#"');
  const isNote = r.note !== undefined;
  if (isNote === (r.param !== undefined)) fail(where, 'give exactly one of "param" or "note"');
  if (r.gesture !== undefined && !GESTURES.includes(r.gesture as Gesture)) fail(where, `gesture must be one of ${GESTURES.join(', ')}`);
  if (isNote && r.gesture !== undefined && r.gesture !== 'tap' && r.gesture !== 'hold') fail(where, 'a note binding\'s gesture is tap or hold');
  if (r.glide !== undefined && (typeof r.glide !== 'number' || r.glide < 0)) fail(where, 'glide must be milliseconds >= 0');
  if (!Array.isArray(r.effects)) fail(where, 'effects must be an array (may be empty)');
  const effects = r.effects.map((e, k): EffectSpec => {
    const w = `${where}.effects[${k}]`;
    if (!e || typeof e !== 'object') fail(w, 'not an object');
    const o = e as Record<string, unknown>;
    const kind = (typeof o.effect === 'string' && EFFECT_ALIASES[o.effect]) || o.effect;
    if (!EFFECTS.includes(kind as EffectKind)) fail(w, `effect must be one of ${EFFECTS.join(', ')}`);
    const spec: EffectSpec = { effect: kind as EffectKind, amount: typeof o.amount === 'number' ? o.amount : 1 };
    if (o.hz !== undefined) fail(w, 'hz is gone: effects no longer run on their own clock, every frame follows the value');
    if (o.span !== undefined) {
      const sp = o.span;
      if (!Array.isArray(sp) || sp.length !== 2 || !sp.every((v) => typeof v === 'number' && v >= 0 && v <= 1) || sp[0] >= sp[1]) {
        fail(w, 'span must be [from, to] with 0 <= from < to <= 1');
      }
      spec.span = [sp[0], sp[1]];
    }
    if (o.ease !== undefined) {
      if (!EASES.includes(o.ease as Ease)) fail(w, `ease must be one of ${EASES.join(', ')}`);
      spec.ease = o.ease as Ease;
    }
    if (o.from !== undefined) {
      if (!['bottom', 'top', 'left', 'right'].includes(o.from as string)) fail(w, 'from must be bottom, top, left or right');
      spec.from = o.from as FillFrom;
    }
    if (o.edge !== undefined) {
      if (o.edge !== 'straight' && o.edge !== 'wave') fail(w, 'edge must be straight or wave');
      spec.edge = o.edge;
    }
    if (o.turn !== undefined) {
      if (typeof o.turn !== 'number' || Math.abs(o.turn) > 360) fail(w, 'turn must be degrees, -360..360');
      spec.turn = o.turn;
    }
    const isPt = (v: unknown): v is [number, number] => Array.isArray(v) && v.length === 2 && v.every((n) => typeof n === 'number');
    if (o.at !== undefined) { if (!isPt(o.at)) fail(w, 'at must be [x, y]'); spec.at = o.at; }
    if (o.size !== undefined) {
      if (!Array.isArray(o.size) || !o.size.every((n) => typeof n === 'number' && n > 0)) fail(w, 'size must be a list of positive numbers');
      spec.size = o.size as number[];
    }
    if (o.front !== undefined) {
      if (!Array.isArray(o.front) || !o.front.every((f) => typeof f === 'string' && /^f\d+$/.test(f))) fail(w, 'front must be a list of fill ids');
      spec.front = o.front as string[];
    }
    if (o.spots !== undefined) {
      if (!Array.isArray(o.spots)) fail(w, 'spots must be a list');
      spec.spots = o.spots.map((x, k) => {
        const q = x as Record<string, unknown>;
        if (!q || !isPt(q.at) || typeof q.angle !== 'number') fail(`${w}.spots[${k}]`, 'needs at [x, y] and angle');
        return { at: q.at, angle: q.angle, size: typeof q.size === 'number' ? q.size : 1, delay: typeof q.delay === 'number' ? q.delay : 0 };
      });
    }
    if (o.to !== undefined) { if (!isPt(o.to)) fail(w, 'to must be [x, y]'); spec.to = o.to; }
    if (o.place !== undefined) {
      if (!['under', 'on', 'over', 'around'].includes(o.place as string)) fail(w, 'place must be under, on, over or around');
      spec.place = o.place as 'under' | 'on' | 'over' | 'around';
    }
    if (o.items !== undefined) {
      if (!Array.isArray(o.items)) fail(w, 'items must be a list');
      spec.items = o.items.map((x, k) => {
        const q = x as Record<string, unknown>;
        if (!q || typeof q.d !== 'string' || !isPt(q.at)) fail(`${w}.items[${k}]`, 'needs d and at');
        const g = q.grow === 'x' || q.grow === 'y' ? q.grow : 'scale';
        const it: Sprite = { d: q.d, fill: typeof q.fill === 'string' ? q.fill : '#ffffff', edge: typeof q.edge === 'number' ? q.edge : 14, at: q.at,
          start: typeof q.start === 'number' ? q.start : 0, end: typeof q.end === 'number' ? q.end : 1, grow: g };
        if (typeof q.outStart === 'number' && typeof q.outEnd === 'number') { it.outStart = q.outStart; it.outEnd = q.outEnd; }
        const sw = q.sweep as Record<string, unknown> | undefined;
        if (sw && typeof sw.from === 'number' && typeof sw.to === 'number') it.sweep = { from: sw.from, to: sw.to };
        return it;
      });
    }
    if (o.angle !== undefined) { if (typeof o.angle !== 'number') fail(w, 'angle must be degrees'); spec.angle = o.angle; }
    if (o.over !== undefined) spec.over = o.over === true;
    if (o.bands !== undefined) {
      if (!Array.isArray(o.bands)) fail(w, 'bands must be a list');
      spec.bands = o.bands.map((x, k) => {
        const q = x as Record<string, unknown>;
        const num = (v: unknown, d: number): number => (typeof v === 'number' ? v : d);
        if (!q || typeof q.radius !== 'number' || typeof q.from !== 'number' || typeof q.to !== 'number') fail(`${w}.bands[${k}]`, 'needs radius, from and to');
        return { radius: q.radius, from: q.from, to: q.to, width: num(q.width, 50), color: typeof q.color === 'string' ? q.color : '#ffffff', start: num(q.start, 0) };
      });
    }
    if (o.color !== undefined) {
      if (typeof o.color !== 'string' || !/^#[0-9a-f]{6}$/i.test(o.color)) fail(w, 'color must be a hex colour like "#9cf27c"');
      spec.color = o.color;
    }
    if (o.toward !== undefined) {
      if (typeof o.toward !== 'number' || o.toward < 0 || o.toward > 360) fail(w, 'toward must be a hue, 0..360');
      spec.toward = o.toward;
    }
    if (o.count !== undefined) {
      if (typeof o.count !== 'number' || o.count < 1 || o.count > 64) fail(w, 'count must be 1..64');
      spec.count = Math.round(o.count);
    }
    if (o.parts !== undefined) {
      const parts = typeof o.parts === 'string' ? [o.parts] : o.parts;
      if (!Array.isArray(parts) || !parts.every((x) => typeof x === 'string')) fail(w, 'parts must be a role name or a list of them');
      spec.parts = parts as string[];
    }
    return spec;
  });
  let b: Binding;
  if (isNote) {
    if (typeof r.note !== 'number' || !Number.isInteger(r.note) || r.note < 0 || r.note > 127) fail(where, 'note must be a MIDI note number 0..127');
    if (r.release !== undefined && (typeof r.release !== 'number' || r.release < 0)) fail(where, 'release must be milliseconds >= 0');
    b = { kind: 'note', id: typeof r.id === 'string' && r.id ? r.id : `note-${r.note}#${i}`, object, note: r.note,
      release: typeof r.release === 'number' ? r.release : 300, effects };
    if (typeof r.label === 'string') b.label = r.label;
  } else b = { kind: 'param', ...parseCommon(r, where, i), object, effects };
  if (r.gesture !== undefined) b.gesture = r.gesture as Gesture;
  if (typeof r.glide === 'number') b.glide = r.glide;
  if (r.locked !== undefined) {
    if (typeof r.locked !== 'boolean') fail(where, 'locked must be true or false');
    if (r.locked) b.locked = true;
  }
  return b;
}

function parseRegion(raw: unknown, i: number): RegionEntry {
  const where = `regions[${i}]`;
  if (!raw || typeof raw !== 'object') fail(where, 'not an object');
  const r = raw as Record<string, unknown>;
  if (!GESTURES.includes(r.gesture as Gesture)) fail(where, `gesture must be one of ${GESTURES.join(', ')}`);
  const common = parseCommon(r, where, i);
  const shape = r.region as Record<string, unknown> | undefined;
  if (!shape || typeof shape !== 'object') fail(where, 'region must be { rect } or { polygon }');
  let region: RegionShape;
  if ('rect' in shape) {
    const q = shape.rect;
    if (!Array.isArray(q) || q.length !== 4 || !q.every((n) => typeof n === 'number')) fail(where, 'rect must be [x, y, w, h]');
    region = { rect: q as [number, number, number, number] };
  } else if ('polygon' in shape) {
    const pts = shape.polygon;
    if (!Array.isArray(pts) || pts.length < 3 || !pts.every(isPoint)) fail(where, 'polygon needs 3+ [x, y] points');
    region = { polygon: pts as Point[] };
  } else fail(where, 'region must be { rect } or { polygon }');
  return { ...common, region, gesture: r.gesture as Gesture };
}

/** Vertices of the shape (rects become four points) for drawing and the bounding box. */
export function shapePoints(s: RegionShape): Point[] {
  if ('polygon' in s) return s.polygon;
  const [x, y, w, h] = s.rect;
  return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
}

export interface Box { x: number; y: number; w: number; h: number }

export function boundingBox(s: RegionShape): Box {
  const pts = shapePoints(s);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { x: x0, y: y0, w: Math.max(1, x1 - x0), h: Math.max(1, y1 - y0) };
}

function clamp01(t: number): number { return t < 0 ? 0 : t > 1 ? 1 : t; }

/** Position 0..1 along the axis -> parameter value, through the curve. */
export function valueAt(entry: Ranged, t: number): number {
  const [a, b] = entry.range;
  const u = clamp01(t);
  if (entry.curve === 'log') return a * Math.pow(b / a, u);
  return a + (b - a) * u;
}

/** Parameter value -> position 0..1 (inverse of valueAt), used by the debug overlay. */
export function positionOf(entry: Ranged, v: number): number {
  const [a, b] = entry.range;
  if (a === b) return 0;
  if (entry.curve === 'log') return clamp01(Math.log(v / a) / Math.log(b / a));
  return clamp01((v - a) / (b - a));
}

/** Next value after a tap: step forward through the range, wrapping at the end. */
export function tapNext(entry: Ranged & Pick<Control, 'step'>, desc: ParamDesc | undefined, current: number): number {
  const [a, b] = entry.range;
  const lo = Math.min(a, b), hi = Math.max(a, b);
  const step = entry.step ?? (desc && desc.type !== 'float' ? 1 : hi - lo);
  if (step <= 0 || hi === lo) return lo;
  const eps = step * 1e-6;
  const next = current + step;
  return next > hi + eps ? lo : Math.min(hi, next);
}

/** Image-pixel position within the region's bounding box, as 0..1 along the gesture axis (up = 1 for drag-y). */
export function axisPosition(entry: Pick<Control, 'gesture'>, box: Box, p: Point): number {
  if (entry.gesture === 'drag-y') return 1 - (p[1] - box.y) / box.h;
  return (p[0] - box.x) / box.w;
}

/** Format an entry as the JSON Matt pastes into mapping.json (used by the region editor). */
export function formatEntry(entry: RegionEntry): string {
  const pts = 'polygon' in entry.region
    ? `{ "polygon": [${entry.region.polygon.map(([x, y]) => `[${x}, ${y}]`).join(', ')}] }`
    : `{ "rect": [${entry.region.rect.join(', ')}] }`;
  const lines = [
    `  "id": ${JSON.stringify(entry.id)},`,
    entry.label !== undefined ? `  "label": ${JSON.stringify(entry.label)},` : null,
    `  "region": ${pts},`,
    `  "gesture": ${JSON.stringify(entry.gesture)},`,
    `  "param": ${JSON.stringify(entry.param)},`,
    `  "range": [${entry.range[0]}, ${entry.range[1]}],`,
    `  "curve": ${JSON.stringify(entry.curve)}`,
  ].filter((l): l is string => l !== null);
  return `{\n${lines.join('\n')}\n}`;
}
