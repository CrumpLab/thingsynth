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

export type EffectKind = 'glow' | 'hue' | 'boil';
export const EFFECTS: readonly EffectKind[] = ['glow', 'hue', 'boil'];

export interface EffectSpec {
  effect: EffectKind;
  /** Roles from the object's `parts` to apply to (fill effects); omitted = every fill of the object. */
  parts?: string[];
  /** Strength, 1 = the effect's full designed range; negative reverses hue direction. */
  amount: number;
}

/** v2: an object of the painting bound to a parameter. Without `gesture` it only shows the value. */
export interface Binding extends Omit<Control, 'gesture'> {
  object: string;
  gesture?: Gesture;
  effects: EffectSpec[];
}

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
  if (typeof r.object !== 'string' || !r.object) fail(where, 'object must be an id from objects.json');
  if (r.gesture !== undefined && !GESTURES.includes(r.gesture as Gesture)) fail(where, `gesture must be one of ${GESTURES.join(', ')}`);
  if (!Array.isArray(r.effects)) fail(where, 'effects must be an array (may be empty)');
  const effects = r.effects.map((e, k): EffectSpec => {
    const w = `${where}.effects[${k}]`;
    if (!e || typeof e !== 'object') fail(w, 'not an object');
    const o = e as Record<string, unknown>;
    if (!EFFECTS.includes(o.effect as EffectKind)) fail(w, `effect must be one of ${EFFECTS.join(', ')}`);
    const spec: EffectSpec = { effect: o.effect as EffectKind, amount: typeof o.amount === 'number' ? o.amount : 1 };
    if (o.parts !== undefined) {
      const parts = typeof o.parts === 'string' ? [o.parts] : o.parts;
      if (!Array.isArray(parts) || !parts.every((x) => typeof x === 'string')) fail(w, 'parts must be a role name or a list of them');
      spec.parts = parts as string[];
    }
    return spec;
  });
  const b: Binding = { ...parseCommon(r, where, i), object: r.object, effects };
  if (r.gesture !== undefined) b.gesture = r.gesture as Gesture;
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
