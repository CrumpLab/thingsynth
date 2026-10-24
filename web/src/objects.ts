// Objects: named groups of the painting's fill shapes (art/<slug>/objects.json), resolved against the parts
// table the extractor wrote (art/<slug>/layers/parts.json). An object has roles ("face-left", "eye", ...), each a
// list of fill ids, and the ink strokes that outline it ("auto" = every stroke that runs along one of its fills).
// A mapping binding may also name a single fill directly ("part": "f006"); that becomes an object "#f006" with
// one role, "body".
import objectsJson from '../../art/golden-pyramid-with-tunnel-celebration/objects.json';
import partsJson from '../../art/golden-pyramid-with-tunnel-celebration/layers/parts.json';

export interface FillPart {
  id: string; layer: number; n: number; fill: string; opacity: number;
  bbox: [number, number, number, number]; centroid: [number, number]; area: number;
  /** Ink strokes that run along this fill's edge, most adjacent first. */
  ink: string[];
}
export interface InkPart { id: string; layer: number; n: number; bbox: [number, number, number, number]; centroid: [number, number]; area: number }

const partsData = partsJson as unknown as { fills: FillPart[]; ink: InkPart[] };
export const fillParts = new Map(partsData.fills.map((f) => [f.id, f]));
export const inkParts = new Map(partsData.ink.map((s) => [s.id, s]));

export interface ArtObject {
  id: string;
  label?: string;
  /** role -> fill ids */
  roles: Map<string, string[]>;
  /** every fill id, in role order */
  fills: string[];
  ink: string[];
  /**
   * The outline strokes enclosed by the object (inside its box plus 10%). Effects that move the object (pulse,
   * wobble, spin, blink) move these with it and leave the borders it shares with neighbours where they are.
   */
  ownInk: string[];
  /** canvas pixels: x, y, w, h */
  bbox: [number, number, number, number];
  /** area-weighted centre of the fills, canvas pixels */
  centroid: [number, number];
}

interface ObjectDef { label?: string; parts: Record<string, string[]>; ink?: 'auto' | string[] }

function fail(id: string, msg: string): never {
  throw new Error(`objects.json ${id}: ${msg}`);
}

function finish(id: string, roles: Map<string, string[]>, ink: string[] | null, label?: string): ArtObject {
  const fills = Array.from(new Set(Array.from(roles.values()).flat()));
  const allInk = ink ?? Array.from(new Set(fills.flatMap((f) => fillParts.get(f)!.ink)));
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, ax = 0, ay = 0, at = 0;
  for (const f of fills) {
    const p = fillParts.get(f)!;
    const [x, y, w, h] = p.bbox;
    x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h);
    ax += p.centroid[0] * p.area; ay += p.centroid[1] * p.area; at += p.area;
  }
  const w = x1 - x0, h = y1 - y0;
  const ownInk = allInk.filter((s) => {
    const [x, y, sw, sh] = inkParts.get(s)!.bbox;
    return x >= x0 - 0.1 * w && y >= y0 - 0.1 * h && x + sw <= x1 + 0.1 * w && y + sh <= y1 + 0.1 * h;
  });
  const obj: ArtObject = {
    id, roles, fills, ink: allInk, ownInk, bbox: [x0, y0, w, h],
    centroid: at > 0 ? [ax / at, ay / at] : [x0 + w / 2, y0 + h / 2],
  };
  if (label) obj.label = label;
  return obj;
}

/** Look up an object by name, or make one from a single fill for "#fNNN" (a binding's "part"). */
export function resolveObject(objects: Map<string, ArtObject>, name: string): ArtObject | undefined {
  const known = objects.get(name);
  if (known) return known;
  if (name.startsWith('#') && fillParts.has(name.slice(1))) {
    const obj = finish(name, new Map([['body', [name.slice(1)]]]), null);
    objects.set(name, obj);
    return obj;
  }
  return undefined;
}

export function loadObjects(): Map<string, ArtObject> {
  const raw = objectsJson as unknown as { schema: string; objects: Record<string, ObjectDef> };
  if (raw.schema !== 'thingsynth.objects/1') fail('', 'expected schema "thingsynth.objects/1"');
  const out = new Map<string, ArtObject>();
  for (const [id, def] of Object.entries(raw.objects)) {
    if (id.startsWith('#')) fail(id, 'object names may not start with "#" (reserved for single parts)');
    const roles = new Map<string, string[]>();
    for (const [role, ids] of Object.entries(def.parts ?? {})) {
      for (const f of ids) if (!fillParts.has(f)) fail(id, `unknown fill ${f} in role ${role}`);
      roles.set(role, ids);
    }
    if (roles.size === 0 || Array.from(roles.values()).every((r) => r.length === 0)) fail(id, 'has no fills');
    if (Array.isArray(def.ink)) for (const s of def.ink) if (!inkParts.has(s)) fail(id, `unknown ink stroke ${s}`);
    out.set(id, finish(id, roles, Array.isArray(def.ink) ? def.ink : null, def.label));
  }
  return out;
}
