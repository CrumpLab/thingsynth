// ?debug: region outlines and labels, a HUD with pointer image coordinates and the mapped parameter values, a
// console helper that prints image pixels on every click, and a tiny polygon editor:
//   shift+click   add a vertex          Backspace  remove the last vertex
//   Enter         print (and copy) a mapping.json entry for the polygon      Escape  clear it
import type { WebSynthlandHost } from '../runtime/types';
import { formatEntry, positionOf, type Mapping, type Point, type RegionEntry } from './mapping';
import type { PaintingLayer } from './painting';

const SVG = 'http://www.w3.org/2000/svg';

export function mountDebug(layer: PaintingLayer, mapping: Mapping, host: WebSynthlandHost): void {
  document.body.classList.add('debug');
  const [W, H] = mapping.size;

  // Labels at each region's first vertex.
  for (const [entry, poly] of layer.shapes) {
    const pts = poly.getAttribute('points')!.split(' ')[0]!.split(',').map(Number);
    const t = document.createElementNS(SVG, 'text');
    t.setAttribute('x', String((pts[0] ?? 0) + 12));
    t.setAttribute('y', String((pts[1] ?? 0) + 44));
    t.classList.add('region-label');
    t.textContent = `${entry.id} · ${entry.gesture} · ${entry.param}`;
    layer.svg.append(t);
  }

  // HUD
  const hud = document.createElement('div');
  hud.id = 'hud';
  const coords = document.createElement('div');
  coords.className = 'coords';
  const table = document.createElement('table');
  const rows = new Map<string, HTMLTableCellElement>();
  const mapped = Array.from(new Set(mapping.regions.map((r) => r.param)));
  for (const id of mapped) {
    const tr = document.createElement('tr');
    const name = document.createElement('td');
    name.textContent = id;
    const val = document.createElement('td');
    tr.append(name, val);
    table.append(tr);
    rows.set(id, val);
  }
  const help = document.createElement('div');
  help.className = 'help';
  help.innerHTML = 'click: log image px to console &middot; shift+click: add polygon point &middot; Enter: print entry &middot; Backspace/Esc: undo/clear';
  hud.append(coords, table, help);
  document.body.append(hud);

  const fmt = (id: string, v: number): string => {
    const d = host.params().find((p) => p.id === id);
    if (!d) return `${v} (unknown param!)`;
    if (d.type === 'choice' && d.choices) return `${d.choices[Math.round(v)] ?? v} (${Math.round(v)})`;
    if (d.type === 'bool') return v >= 0.5 ? 'on' : 'off';
    return `${d.type === 'float' ? v.toFixed(3) : Math.round(v)}${d.unit ? ' ' + d.unit : ''}`;
  };
  const refresh = (): void => {
    for (const [id, cell] of rows) cell.textContent = fmt(id, host.get(id));
    for (const [entry, poly] of layer.shapes) {
      poly.style.fillOpacity = String(0.08 + 0.35 * positionOf(entry, host.get(entry.param)));
    }
  };
  refresh();
  host.onParam(refresh);
  host.onPreset(refresh);

  // Pointer coordinates in image pixels.
  window.addEventListener('pointermove', (ev) => {
    const [x, y] = layer.toImage(ev.clientX, ev.clientY);
    const inside = x >= 0 && y >= 0 && x <= W && y <= H;
    coords.textContent = inside ? `x ${x}  y ${y}   (image ${W}×${H})` : `outside image (${W}×${H})`;
  });

  // Editor state.
  const draft: Point[] = [];
  const draftPoly = document.createElementNS(SVG, 'polygon');
  draftPoly.classList.add('draft');
  layer.svg.append(draftPoly);
  const dots = document.createElementNS(SVG, 'g');
  layer.svg.append(dots);
  const redraw = (): void => {
    draftPoly.setAttribute('points', draft.map(([x, y]) => `${x},${y}`).join(' '));
    dots.replaceChildren(...draft.map(([x, y]) => {
      const c = document.createElementNS(SVG, 'circle');
      c.setAttribute('cx', String(x)); c.setAttribute('cy', String(y)); c.setAttribute('r', '10');
      c.classList.add('draft-dot');
      return c;
    }));
  };
  const printDraft = (): void => {
    if (draft.length < 3) { console.warn('[thingsynth] need 3+ points (shift+click) before Enter'); return; }
    const entry: RegionEntry = {
      id: 'new-region', label: 'describe the painted thing here', region: { polygon: draft.map((p) => [...p] as Point) },
      gesture: 'drag-x', param: 'amp.drive', range: [0, 1], curve: 'linear',
    };
    const text = formatEntry(entry);
    console.log('[thingsynth] mapping.json entry (edit gesture/param/range):\n' + text);
    void navigator.clipboard?.writeText(text).then(() => console.log('[thingsynth] copied to clipboard')).catch(() => undefined);
  };

  layer.svg.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    const p = layer.toImage(ev.clientX, ev.clientY);
    if (ev.shiftKey) {
      ev.preventDefault();
      draft.push(p);
      redraw();
      console.log(`[thingsynth] point ${draft.length}: [${p[0]}, ${p[1]}]`);
    } else {
      const hit = (ev.target as Element).closest('.region') as SVGElement | null;
      console.log(`[thingsynth] click at image px [${p[0]}, ${p[1]}]${hit ? ` on region ${hit.dataset.id}` : ''}`);
    }
  });
  window.addEventListener('keydown', (ev) => {
    const tag = (document.activeElement as HTMLElement | null)?.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (ev.key === 'Enter') printDraft();
    else if (ev.key === 'Backspace') { draft.pop(); redraw(); }
    else if (ev.key === 'Escape') { draft.length = 0; redraw(); }
    else return;
    ev.preventDefault();
  });

  // Console access: thingsynth.host, thingsynth.mapping, thingsynth.set('amp.drive', 0.5), thingsynth.draft
  Object.assign(window, {
    thingsynth: {
      host, mapping, draft,
      set: (id: string, v: number) => host.set(id, v),
      get: (id: string) => host.get(id),
      params: () => host.params().filter((p) => !p.hidden).map((p) => `${p.id} [${p.min}..${p.max}] ${p.unit}`),
      entry: printDraft,
    },
  });
  console.log('[thingsynth] debug mode: window.thingsynth = { host, mapping, set, get, params, draft, entry }');
}
