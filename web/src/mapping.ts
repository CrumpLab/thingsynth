// mapping.json: regions of the painting (image pixel coordinates) bound to Tonewheel parameters.
// This file knows nothing about the DOM or the engine: it parses, validates and does the value math.
import type { ParamDesc } from '../runtime/types';

export type Gesture = 'tap' | 'drag-x' | 'drag-y' | 'hold' | 'hover';
export type Curve = 'linear' | 'log';
export type Point = [number, number];

export type RegionShape = { rect: [number, number, number, number] } | { polygon: Point[] };

export interface RegionEntry {
  /** Stable name used in debug output; defaults to `${param}#${index}`. */
  id: string;
  label?: string;
  region: RegionShape;
  gesture: Gesture;
  /** A Tonewheel parameter id from web/public/tonewheel/plugin.json (e.g. "amp.drive"). */
  param: string;
  /** Values in the parameter's real units; [min, max] may be reversed to invert the direction. */
  range: [number, number];
  curve: Curve;
  /** tap: how far one tap moves the value (default 1 for int/bool/choice, the whole range for floats). */
  step?: number;
}

export interface Mapping {
  schema: 'thingsynth.mapping/1';
  image: string;
  size: [number, number];
  defaultPreset?: string;
  regions: RegionEntry[];
}

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
  if (m.schema !== 'thingsynth.mapping/1') fail('schema', 'expected "thingsynth.mapping/1"');
  if (typeof m.image !== 'string') fail('image', 'expected a path string');
  if (!isPoint(m.size) || m.size[0] <= 0 || m.size[1] <= 0) fail('size', 'expected [width, height] in pixels');
  if (!Array.isArray(m.regions)) fail('regions', 'expected an array');
  const regions = m.regions.map((r, i) => parseRegion(r, i));
  const mapping: Mapping = { schema: 'thingsynth.mapping/1', image: m.image, size: m.size, regions };
  if (typeof m.defaultPreset === 'string') mapping.defaultPreset = m.defaultPreset;
  return mapping;
}

function parseRegion(raw: unknown, i: number): RegionEntry {
  const where = `regions[${i}]`;
  if (!raw || typeof raw !== 'object') fail(where, 'not an object');
  const r = raw as Record<string, unknown>;
  if (typeof r.param !== 'string' || !r.param) fail(where, 'param must be a parameter id');
  if (!GESTURES.includes(r.gesture as Gesture)) fail(where, `gesture must be one of ${GESTURES.join(', ')}`);
  if (!isPoint(r.range)) fail(where, 'range must be [min, max]');
  const curve = r.curve ?? 'linear';
  if (curve !== 'linear' && curve !== 'log') fail(where, 'curve must be linear or log');
  if (curve === 'log' && (r.range[0] <= 0 || r.range[1] <= 0)) fail(where, 'log curve needs a positive range');
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
  const entry: RegionEntry = {
    id: typeof r.id === 'string' && r.id ? r.id : `${r.param}#${i}`,
    region,
    gesture: r.gesture as Gesture,
    param: r.param,
    range: r.range,
    curve,
  };
  if (typeof r.label === 'string') entry.label = r.label;
  if (typeof r.step === 'number' && r.step > 0) entry.step = r.step;
  return entry;
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
export function valueAt(entry: RegionEntry, t: number): number {
  const [a, b] = entry.range;
  const u = clamp01(t);
  if (entry.curve === 'log') return a * Math.pow(b / a, u);
  return a + (b - a) * u;
}

/** Parameter value -> position 0..1 (inverse of valueAt), used by the debug overlay. */
export function positionOf(entry: RegionEntry, v: number): number {
  const [a, b] = entry.range;
  if (a === b) return 0;
  if (entry.curve === 'log') return clamp01(Math.log(v / a) / Math.log(b / a));
  return clamp01((v - a) / (b - a));
}

/** Next value after a tap: step forward through the range, wrapping at the end. */
export function tapNext(entry: RegionEntry, desc: ParamDesc | undefined, current: number): number {
  const [a, b] = entry.range;
  const lo = Math.min(a, b), hi = Math.max(a, b);
  const step = entry.step ?? (desc && desc.type !== 'float' ? 1 : hi - lo);
  if (step <= 0 || hi === lo) return lo;
  const eps = step * 1e-6;
  const next = current + step;
  return next > hi + eps ? lo : Math.min(hi, next);
}

/** Image-pixel position within the region's bounding box, as 0..1 along the gesture axis (up = 1 for drag-y). */
export function axisPosition(entry: RegionEntry, box: Box, p: Point): number {
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
