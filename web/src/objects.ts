// Objects: named groups of the painting's fill shapes (art/<slug>/objects.json), resolved against the parts
// table the extractor wrote (art/<slug>/layers/parts.json). An object has roles ("face-left", "eye", ...), each a
// list of fill ids, and the ink strokes that outline it ("auto" = every stroke that runs along one of its fills).
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
  /** canvas pixels: x, y, w, h */
  bbox: [number, number, number, number];
}

interface ObjectDef { label?: string; parts: Record<string, string[]>; ink?: 'auto' | string[] }

function fail(id: string, msg: string): never {
  throw new Error(`objects.json ${id}: ${msg}`);
}

export function loadObjects(): Map<string, ArtObject> {
  const raw = objectsJson as unknown as { schema: string; objects: Record<string, ObjectDef> };
  if (raw.schema !== 'thingsynth.objects/1') fail('', 'expected schema "thingsynth.objects/1"');
  const out = new Map<string, ArtObject>();
  for (const [id, def] of Object.entries(raw.objects)) {
    const roles = new Map<string, string[]>();
    const fills: string[] = [];
    for (const [role, ids] of Object.entries(def.parts ?? {})) {
      for (const f of ids) if (!fillParts.has(f)) fail(id, `unknown fill ${f} in role ${role}`);
      roles.set(role, ids);
      for (const f of ids) if (!fills.includes(f)) fills.push(f);
    }
    if (fills.length === 0) fail(id, 'has no fills');
    let ink: string[];
    if (Array.isArray(def.ink)) {
      for (const s of def.ink) if (!inkParts.has(s)) fail(id, `unknown ink stroke ${s}`);
      ink = def.ink;
    } else ink = Array.from(new Set(fills.flatMap((f) => fillParts.get(f)!.ink)));
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const f of fills) {
      const [x, y, w, h] = fillParts.get(f)!.bbox;
      x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h);
    }
    const obj: ArtObject = { id, roles, fills, ink, bbox: [x0, y0, x1 - x0, y1 - y0] };
    if (def.label) obj.label = def.label;
    out.set(id, obj);
  }
  return out;
}
