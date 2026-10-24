// ?debug: region outlines and labels, a HUD with pointer image coordinates and the mapped parameter values, a
// console helper that prints image pixels on every click, and a tiny polygon editor:
//   shift+click   add a vertex          Backspace  remove the last vertex
//   Enter         print (and copy) a mapping.json entry for the polygon      Escape  clear it
// Parts mode (press ` (backquote), or open with ?debug=parts; p is a note on the computer keyboard): the pointer hits the painting's own fill shapes instead of
// the mapping regions; the shape under the pointer is outlined and its id, colour, area and box are shown;
// click logs the full parts.json record.
import type { WebSynthlandHost } from '../runtime/types';
import { layers } from './art';
import type { Effects } from './effects';
import { formatEntry, positionOf, type Mapping, type Point, type RegionEntry } from './mapping';
import { fillParts, type FillPart } from './objects';
import type { PaintingLayer } from './painting';

const SVG = 'http://www.w3.org/2000/svg';

export function mountDebug(layer: PaintingLayer, mapping: Mapping, host: WebSynthlandHost, effects: Effects | null): void {
  document.body.classList.add('debug');
  const [W, H] = mapping.size;

  // Labels at each control's top-left corner, rebuilt when the bindings change (shuffle, editor).
  let labels: SVGTextElement[] = [];
  const drawLabels = (): void => {
    for (const t of labels) t.remove();
    labels = layer.controls.map(({ control, box }) => {
      const t = document.createElementNS(SVG, 'text');
      t.setAttribute('x', String(box.x + 12));
      t.setAttribute('y', String(box.y + 44));
      t.classList.add('region-label');
      t.textContent = `${control.param}`;
      layer.svg.append(t);
      return t;
    });
  };
  drawLabels();
  layer.onRebind(() => { drawLabels(); refresh(); });

  // HUD
  const hud = document.createElement('div');
  hud.id = 'hud';
  const coords = document.createElement('div');
  coords.className = 'coords';
  const table = document.createElement('table');
  const rows = new Map<string, HTMLTableCellElement>();
  const mapped = Array.from(new Set([...mapping.regions, ...mapping.bindings].flatMap((r) => ('param' in r ? [r.param] : []))));
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
  help.innerHTML = 'click: log image px to console &middot; shift+click: add polygon point &middot; Enter: print entry &middot; Backspace/Esc: undo/clear &middot; <b>`</b>: parts mode &middot; ';
  const bindBtn = document.createElement('button');
  bindBtn.type = 'button';
  bindBtn.className = 'bind-open';
  bindBtn.textContent = 'Bind…';
  bindBtn.title = 'Open the bind editor: pick shapes, make objects, bind parameters and notes';
  help.append(bindBtn);
  const partLine = document.createElement('div');
  partLine.className = 'part';
  const liveLine = document.createElement('div');
  liveLine.className = 'live';
  hud.append(coords, partLine, liveLine, table, help);
  if (effects) {
    const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const noteName = (n: number): string => `${names[n % 12]}${Math.floor(n / 12) - 1}`;
    window.setInterval(() => {
      const held = effects.notes();
      liveLine.textContent = `notes: ${held.length ? held.map(noteName).join(' ') : '-'} · idle ${effects.idle() ? 'on' : 'off'}`;
    }, 150);
  }
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
    for (const { control, els } of layer.controls) {
      const o = String(0.08 + 0.35 * positionOf(control, host.get(control.param)));
      for (const el of els) el.style.fillOpacity = o;
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

  // Parts mode: hover and click the painting's own fill shapes.
  const scale = W / layers.canvas[0];
  const hilite = document.createElementNS(SVG, 'path');
  hilite.classList.add('part-hilite');
  hilite.setAttribute('transform', `scale(${scale})`);
  layer.svg.append(hilite);
  let partsMode = false;
  const setPartsMode = (on: boolean): void => {
    if (layer.art.flat) { console.warn('[thingsynth] parts mode needs the layered painting (drop ?flat)'); return; }
    partsMode = on;
    document.body.classList.toggle('parts-mode', on);
    hilite.removeAttribute('d');
    partLine.textContent = on ? 'parts mode: hover a shape' : '';
    console.log(`[thingsynth] parts mode ${on ? 'on' : 'off'}`);
  };
  const partOf = (t: EventTarget | null): FillPart | undefined => {
    const id = t instanceof SVGPathElement && t.id.startsWith('f') ? t.id : '';
    return id ? fillParts.get(id) : undefined;
  };
  const artEl = layer.art.el;
  artEl.addEventListener('pointermove', (ev) => {
    if (!partsMode) return;
    const part = partOf(ev.target);
    const path = part ? layer.art.fills.get(part.id) : undefined;
    if (!part || !path) { hilite.removeAttribute('d'); partLine.textContent = 'parts mode: hover a shape'; return; }
    hilite.setAttribute('d', path.getAttribute('d') ?? '');
    const [x, y, w, h] = part.bbox.map(Math.round);
    partLine.textContent = `${part.id}  ${part.fill}${part.opacity < 1 ? ` @${part.opacity.toFixed(2)}` : ''}  area ${part.area.toLocaleString()}  box ${x},${y} ${w}×${h}  ink ${part.ink.length}`;
  });
  const partClicks: Array<(id: string, add: boolean) => void> = [];
  artEl.addEventListener('pointerdown', (ev) => {
    if (!partsMode) return;
    const part = partOf(ev.target);
    if (!part) return;
    console.log(`[thingsynth] part ${part.id}`, part);
    for (const cb of partClicks) cb(part.id, (ev as PointerEvent).shiftKey);
  });
  if (new URLSearchParams(location.search).get('debug') === 'parts') setPartsMode(true);

  // The bind editor (web/src/editor.ts), opened from the HUD; it stays open across the reloads its saves cause.
  const openEditor = async (): Promise<void> => {
    const { mountEditor } = await import('./editor');
    mountEditor({ layer, mapping, host, effects, setPartsMode, onPartClick: (cb) => { partClicks.push(cb); } });
    bindBtn.disabled = true;
  };
  bindBtn.addEventListener('click', () => { void openEditor(); });
  try { if (sessionStorage.getItem('thingsynth.editor') === 'open') void openEditor(); } catch { /* storage off */ }

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
    if ((ev.code === 'Backquote' || ev.key === '`') && !ev.metaKey && !ev.ctrlKey && !ev.altKey) setPartsMode(!partsMode);
    else if (ev.key === 'Enter') printDraft();
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
      art: layer.art,
      part: (id: string) => fillParts.get(id),
      effects,
      partsMode: setPartsMode,
    },
  });
  console.log('[thingsynth] debug mode: window.thingsynth = { host, mapping, set, get, params, draft, entry, art, part, partsMode, effects }');
}
