// The bind editor (?debug, then Bind…): pick shapes of the painting, make them an object, and bind a parameter or
// a note to it with a gesture and effects. Preview applies it live; Save writes objects.json and mapping.json
// through the dev server (web/vite.config.ts), which then reloads the page with the editor still open; without a
// dev server (a built site) Save copies the JSON instead.
//
// It edits the curated mapping (mapping.json), whatever shuffle is showing.
import rawMappingJson from '../../mapping.json';
import rawObjectsJson from '../../art/golden-pyramid-with-tunnel-celebration/objects.json';
import type { ParamDesc, WebSynthlandHost } from '../runtime/types';
import { layers } from './art';
import type { Effects } from './effects';
import { EASES, EFFECTS, parseMapping, type Binding, type EffectKind, type Gesture, type Mapping } from './mapping';
import { fillParts, loadObjects } from './objects';
import type { PaintingLayer } from './painting';
import { noteName } from './shuffle';

const SVG = 'http://www.w3.org/2000/svg';
type Raw = Record<string, unknown>;
interface RawObjects { schema: string; canvas: number[]; objects: Record<string, { label?: string; parts: Record<string, string[]>; ink?: unknown }> }
interface RawMapping { schema: string; bindings: Raw[]; [k: string]: unknown }

export interface EditorDeps {
  layer: PaintingLayer;
  mapping: Mapping;
  host: WebSynthlandHost;
  effects: Effects | null;
  setPartsMode(on: boolean): void;
  onPartClick(cb: (id: string, add: boolean) => void): void;
}

const STATE_KEY = 'thingsynth.editor';
const SEL_KEY = 'thingsynth.editor.selection';

function el<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Record<string, string> = {}, ...kids: Array<Node | string>): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'text') e.textContent = v; else e.setAttribute(k, v);
  }
  e.append(...kids);
  return e;
}

export function mountEditor(d: EditorDeps): void {
  if (document.getElementById('editor')) return;
  const rawMapping = structuredClone(rawMappingJson) as unknown as RawMapping;
  const rawObjects = structuredClone(rawObjectsJson) as unknown as RawObjects;
  const objects = loadObjects();
  const ownerOf = new Map<string, string>();
  for (const o of objects.values()) for (const f of o.fills) ownerOf.set(f, o.id);
  const params = d.host.params().filter((p) => !p.hidden);
  const byParam = new Map(params.map((p) => [p.id, p]));
  try { sessionStorage.setItem(STATE_KEY, 'open'); } catch { /* storage off */ }
  d.setPartsMode(true);

  // ---- state ------------------------------------------------------------------------------------------------------
  let selection: string[] = [];
  try { selection = (JSON.parse(sessionStorage.getItem(SEL_KEY) ?? '[]') as string[]).filter((f) => fillParts.has(f)); } catch { selection = []; }

  // ---- panel ------------------------------------------------------------------------------------------------------
  const panel = el('aside', { id: 'editor', 'aria-label': 'Bind editor' });
  const close = el('button', { type: 'button', class: 'x', title: 'Close the editor', text: '×' });
  const selInfo = el('div', { class: 'sel' });
  const objSelect = el('select', { 'aria-label': 'Object' });
  const newName = el('input', { type: 'text', placeholder: 'new-object-name', 'aria-label': 'New object name', pattern: '[a-z0-9-]+' });
  const newLabel = el('input', { type: 'text', placeholder: 'What it is, in a few words', 'aria-label': 'New object label' });
  const newBox = el('div', { class: 'new' }, newName, newLabel);
  const target = el('select', { 'aria-label': 'Parameter or note' });
  const noteNum = el('input', { type: 'number', min: '21', max: '108', value: '60', 'aria-label': 'MIDI note' });
  const gesture = el('select', { 'aria-label': 'Gesture' });
  for (const g of ['', 'tap', 'drag-x', 'drag-y', 'hold', 'hover']) gesture.append(el('option', { value: g, text: g || '(display only)' }));
  const rMin = el('input', { type: 'number', step: 'any', 'aria-label': 'Range from' });
  const rMax = el('input', { type: 'number', step: 'any', 'aria-label': 'Range to' });
  const curve = el('select', { 'aria-label': 'Curve' }, el('option', { value: 'linear', text: 'linear' }), el('option', { value: 'log', text: 'log' }));
  const glide = el('input', { type: 'number', min: '0', step: '50', placeholder: '150', 'aria-label': 'Glide ms' });
  const label = el('input', { type: 'text', placeholder: 'Label (tooltip)', 'aria-label': 'Label' });
  const locked = el('input', { type: 'checkbox', 'aria-label': 'Locked against shuffle' });
  interface FxRow { on: HTMLInputElement; amount: HTMLInputElement; extra?: HTMLInputElement | HTMLSelectElement; from: HTMLInputElement; to: HTMLInputElement; ease: HTMLSelectElement }
  const fx = new Map<EffectKind, FxRow>();
  const fxBox = el('div', { class: 'fx' });
  for (const k of EFFECTS) {
    const on = el('input', { type: 'checkbox', id: `fx-${k}` });
    const amount = el('input', { type: 'number', step: '0.1', value: '1', 'aria-label': `${k} amount`, title: 'amount at the last frame' });
    let extra: HTMLInputElement | HTMLSelectElement | undefined;
    if (k === 'fill') { extra = el('select', { 'aria-label': 'fill from' }); for (const f of ['bottom', 'top', 'left', 'right']) extra.append(el('option', { value: f, text: f })); }
    if (k === 'scribble') extra = el('input', { type: 'number', min: '1', max: '64', value: '14', 'aria-label': 'scribble count' });
    const from = el('input', { type: 'number', min: '0', max: '1', step: '0.05', value: '0', 'aria-label': `${k} starts at`, title: 'starts at this point of the timeline' });
    const to = el('input', { type: 'number', min: '0', max: '1', step: '0.05', value: '1', 'aria-label': `${k} ends at`, title: 'ends at this point of the timeline' });
    const ease = el('select', { 'aria-label': `${k} easing` });
    for (const e of EASES) ease.append(el('option', { value: e, text: e }));
    fx.set(k, extra ? { on, amount, extra, from, to, ease } : { on, amount, from, to, ease });
    fxBox.append(el('label', { for: `fx-${k}` }, on, ` ${k}`), amount, extra ?? el('span'),
      el('div', { class: 'span' }, el('span', { text: 'span' }), from, to, ease));
  }
  const frameSlider = el('input', { type: 'range', min: '0', max: '1', step: '0.01', value: '0', 'aria-label': 'Preview frame' });
  const frameOut = el('span', { class: 'frame-out', text: 'live' });
  const frameRelease = el('button', { type: 'button', text: 'live', title: 'Back to following the parameter or note' });
  const status = el('div', { class: 'status', role: 'status' });
  const preview = el('button', { type: 'button', text: 'Preview' });
  const save = el('button', { type: 'button', class: 'primary', text: 'Save' });
  const remove = el('button', { type: 'button', text: 'Remove binding' });
  const copy = el('button', { type: 'button', text: 'Copy JSON' });
  const row = (text: string, ...kids: Node[]): HTMLElement => el('div', { class: 'row' }, el('span', { text }), ...kids);
  panel.append(
    close, el('h2', { text: 'Bind' }),
    el('p', { class: 'hint', text: 'Click a shape to select it, shift+click to add or remove shapes.' }), selInfo,
    row('Object', objSelect), newBox,
    row('Bind to', target, noteNum), row('Gesture', gesture), row('Range', rMin, rMax, curve), row('Glide ms', glide),
    row('Label', label), row('Locked', locked), el('h3', { text: 'Effects' }), fxBox,
    el('h3', { text: 'Frame' }), el('p', { class: 'hint', text: 'Scrub the saved animation from its first frame to its last; the organ is not touched.' }),
    row('Frame', frameSlider, frameOut, frameRelease),
    el('div', { class: 'buttons' }, preview, save, remove, copy), status,
  );
  document.body.append(panel);
  document.body.classList.add('editing');

  // ---- selection highlight in the hit layer -------------------------------------------------------------------------
  const hl = document.createElementNS(SVG, 'g');
  hl.classList.add('editor-sel');
  hl.setAttribute('transform', `scale(${d.mapping.size[0] / layers.canvas[0]})`);
  d.layer.svg.append(hl);
  const drawSel = (): void => {
    hl.replaceChildren(...selection.map((f) => {
      const p = document.createElementNS(SVG, 'path');
      p.setAttribute('d', d.layer.art.fills.get(f)?.getAttribute('d') ?? '');
      return p;
    }));
  };

  // ---- options ------------------------------------------------------------------------------------------------------
  const bindingFor = (t: string): Binding | undefined => d.mapping.bindings.find((b) => (t.startsWith('note:') ? b.kind === 'note' && String(b.note) === t.slice(5) : b.kind === 'param' && b.param === t));
  const fillTarget = (): void => {
    target.replaceChildren();
    const g1 = el('optgroup', { label: 'Parameters' });
    for (const p of params) {
      const b = bindingFor(p.id);
      g1.append(el('option', { value: p.id, text: `${p.id} · ${p.name}${b ? ` · on ${b.object.replace(/^#/, '')}` : ' · unbound'}` }));
    }
    target.append(g1, el('optgroup', { label: 'Notes' }, el('option', { value: 'note', text: 'a note…' })));
  };
  const fillObjects = (): void => {
    objSelect.replaceChildren(el('option', { value: '#new', text: '(new object from the selection)' }), el('option', { value: '#single', text: '(the selected shape on its own)' }));
    for (const o of objects.values()) if (!o.id.startsWith('#')) objSelect.append(el('option', { value: o.id, text: `${o.id}${o.label ? ` · ${o.label}` : ''}` }));
  };
  fillTarget();
  fillObjects();

  const defaults = (p: ParamDesc): Binding => {
    const base = { id: p.id.replace('.', '-'), object: objSelect.value, effects: [] as Binding['effects'] };
    if (p.type === 'int' && p.min === 0 && p.max === 8) return { kind: 'param', ...base, param: p.id, range: [0, 8], curve: 'linear', gesture: 'drag-y', effects: [{ effect: 'fill', amount: 1, from: 'bottom' }] };
    if (p.type === 'bool') return { kind: 'param', ...base, param: p.id, range: [0, 1], curve: 'linear', gesture: 'tap', effects: [{ effect: 'glow', amount: 1 }, { effect: 'blink', amount: 1 }] };
    if (p.type === 'choice') return { kind: 'param', ...base, param: p.id, range: [p.min, p.max], curve: 'linear', gesture: 'tap', effects: [{ effect: 'hue', amount: 0.6 }] };
    return { kind: 'param', ...base, param: p.id, range: [p.min, p.max], curve: 'linear', gesture: 'drag-x', effects: [{ effect: 'glow', amount: 1 }] };
  };
  const show = (b: Binding): void => {
    gesture.value = b.gesture ?? '';
    label.value = b.label ?? '';
    glide.value = b.glide !== undefined ? String(b.glide) : '';
    locked.checked = !!b.locked;
    const isParam = b.kind === 'param';
    rMin.disabled = rMax.disabled = curve.disabled = !isParam;
    if (isParam) { rMin.value = String(b.range[0]); rMax.value = String(b.range[1]); curve.value = b.curve; }
    for (const [k, f] of fx) {
      const spec = b.effects.find((e) => e.effect === k);
      f.on.checked = !!spec;
      f.amount.value = String(spec?.amount ?? 1);
      if (f.extra) f.extra.value = String((k === 'fill' ? spec?.from : spec?.count) ?? (k === 'fill' ? 'bottom' : '14'));
      f.from.value = String(spec?.span?.[0] ?? 0);
      f.to.value = String(spec?.span?.[1] ?? 1);
      f.ease.value = spec?.ease ?? 'linear';
    }
  };
  const onTarget = (): void => {
    const isNote = target.value === 'note';
    noteNum.hidden = !isNote;
    const t = isNote ? `note:${noteNum.value}` : target.value;
    const b = bindingFor(t);
    if (b) { show(b); return; }
    if (isNote) show({ kind: 'note', id: `note-${noteNum.value}`, object: objSelect.value, note: Number(noteNum.value), release: 300, gesture: 'hold',
      effects: [{ effect: 'glow', amount: 1.3 }, { effect: 'hue', amount: 0.25 }, { effect: 'boil', amount: 0.6 }] });
    else { const p = byParam.get(target.value); if (p) show(defaults(p)); }
  };
  target.addEventListener('change', onTarget);
  noteNum.addEventListener('change', onTarget);

  const onSelection = (): void => {
    drawSel();
    try { sessionStorage.setItem(SEL_KEY, JSON.stringify(selection)); } catch { /* storage off */ }
    const owners = new Set(selection.map((f) => ownerOf.get(f) ?? ''));
    const owner = owners.size === 1 ? Array.from(owners)[0] : '';
    const exact = owner && objects.get(owner)!.fills.length === selection.length ? owner : '';
    if (selection.length === 0) selInfo.textContent = 'Nothing selected.';
    else selInfo.textContent = `${selection.join(' ')}${owner ? ` · in ${owner}` : ' · in no object'}`;
    objSelect.value = exact || (owner && selection.length === 1 ? owner : selection.length === 1 && !owner ? '#single' : '#new');
    newBox.hidden = objSelect.value !== '#new';
    // Show what this object is bound to, if anything.
    const bound = d.mapping.bindings.find((b) => b.object === (objSelect.value === '#single' ? `#${selection[0]}` : objSelect.value));
    if (bound) {
      if (bound.kind === 'note') { target.value = 'note'; noteNum.value = String(bound.note); } else target.value = bound.param;
      noteNum.hidden = bound.kind !== 'note';
      show(bound);
    }
  };
  objSelect.addEventListener('change', () => { newBox.hidden = objSelect.value !== '#new'; });
  d.onPartClick((id, add) => {
    if (!add) selection = [id];
    else selection = selection.includes(id) ? selection.filter((f) => f !== id) : [...selection, id];
    onSelection();
  });

  // ---- building and writing -----------------------------------------------------------------------------------------
  const say = (msg: string, bad = false): void => { status.textContent = msg; status.classList.toggle('bad', bad); };
  const objectRef = (): { raw: Raw; objectsChanged: boolean } | null => {
    const v = objSelect.value;
    if (v === '#single') {
      if (selection.length !== 1) { say('Select exactly one shape to bind it on its own.', true); return null; }
      return { raw: { part: selection[0] }, objectsChanged: false };
    }
    if (v === '#new') {
      const name = newName.value.trim();
      if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) { say('Name the new object: lower-case letters, digits and dashes.', true); return null; }
      if (rawObjects.objects[name]) { say(`An object called ${name} exists already.`, true); return null; }
      if (selection.length === 0) { say('Select its shapes first.', true); return null; }
      const taken = selection.filter((f) => ownerOf.has(f));
      if (taken.length) { say(`${taken.join(' ')} already belong to ${taken.map((f) => ownerOf.get(f)).join(', ')}.`, true); return null; }
      rawObjects.objects[name] = { label: newLabel.value.trim() || name, parts: { body: selection.slice() }, ink: 'auto' };
      return { raw: { object: name }, objectsChanged: true };
    }
    return { raw: { object: v }, objectsChanged: false };
  };
  const buildRaw = (ref: Raw): Raw | null => {
    const isNote = target.value === 'note';
    const effects = Array.from(fx.entries()).filter(([, f]) => f.on.checked).map(([k, f]) => {
      const e: Raw = { effect: k, amount: Number(f.amount.value) || 1 };
      if (k === 'fill' && f.extra) e.from = f.extra.value;
      if (k === 'scribble' && f.extra && f.extra.value) e.count = Number(f.extra.value);
      const a = Number(f.from.value), b = Number(f.to.value);
      if (!(a === 0 && b === 1)) e.span = [a, b];
      if (f.ease.value !== 'linear') e.ease = f.ease.value;
      return e;
    });
    const b: Raw = isNote
      ? { id: `note-${noteNum.value}`, label: label.value || `${noteName(Number(noteNum.value))}: hold to play`, ...ref, note: Number(noteNum.value) }
      : { id: bindingFor(target.value)?.id ?? target.value.replace('.', '-'), label: label.value || undefined, ...ref, param: target.value,
        range: [Number(rMin.value), Number(rMax.value)], curve: curve.value };
    if (gesture.value) b.gesture = gesture.value as Gesture;
    if (glide.value) b.glide = Number(glide.value);
    if (locked.checked) b.locked = true;
    b.effects = effects;
    if (b.label === undefined) delete b.label;
    return b;
  };
  const sameTarget = (r: Raw): boolean => (target.value === 'note' ? r.note === Number(noteNum.value) : r.param === target.value);
  /** The raw mapping with this binding in place of the old one for the same parameter or note. */
  const nextMapping = (b: Raw | null): RawMapping => {
    const list = rawMapping.bindings.filter((r) => !sameTarget(r));
    if (b) {
      const firstNote = list.findIndex((r) => r.note !== undefined);
      if (b.note !== undefined || firstNote < 0) list.push(b); else list.splice(firstNote, 0, b);
    }
    return { ...rawMapping, bindings: list };
  };
  const validate = (m: RawMapping): Mapping | null => {
    try { return parseMapping(m); } catch (err) { say(err instanceof Error ? err.message : String(err), true); return null; }
  };
  const write = async (writes: Array<{ file: 'mapping' | 'objects'; content: unknown }>): Promise<boolean> => {
    try {
      const res = await fetch('/__thingsynth/save', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Thingsynth': '1' }, body: JSON.stringify({ writes }) });
      if (res.ok) return true;
      say(`Save failed: ${await res.text()}`, true);
    } catch {
      say('No dev server to save to: copied the JSON instead.', true);
      await navigator.clipboard?.writeText(JSON.stringify(writes, null, 2)).catch(() => undefined);
    }
    return false;
  };

  preview.addEventListener('click', () => {
    const ref = objectRef();
    if (!ref) return;
    if (ref.objectsChanged) { say('Preview needs an existing object or a single shape; Save creates new objects.', true); delete rawObjects.objects[newName.value.trim()]; return; }
    const m = validate(nextMapping(buildRaw(ref.raw)));
    if (!m) return;
    d.layer.setBindings(m.bindings);
    d.effects?.setBindings(m.bindings, 600);
    say('Previewing (not saved).');
  });
  save.addEventListener('click', async () => {
    const ref = objectRef();
    if (!ref) return;
    const m = nextMapping(buildRaw(ref.raw));
    if (!ref.objectsChanged && !validate(m)) return;
    const writes: Array<{ file: 'mapping' | 'objects'; content: unknown }> = [];
    if (ref.objectsChanged) writes.push({ file: 'objects', content: rawObjects });
    writes.push({ file: 'mapping', content: m });
    if (await write(writes)) say('Saved; reloading…');
  });
  remove.addEventListener('click', async () => {
    const t = target.value === 'note' ? `note:${noteNum.value}` : target.value;
    if (!bindingFor(t)) { say('Nothing bound to that yet.', true); return; }
    if (await write([{ file: 'mapping', content: nextMapping(null) }])) say('Removed; reloading…');
  });
  copy.addEventListener('click', () => {
    const ref = objectRef();
    if (!ref) return;
    const text = JSON.stringify(buildRaw(ref.raw), null, 2);
    if (ref.objectsChanged) delete rawObjects.objects[newName.value.trim()];
    void navigator.clipboard?.writeText(text).then(() => say('Copied the binding JSON.'), () => say('Could not copy; see the console.', true));
    console.log('[thingsynth] binding JSON:\n' + text);
  });
  // Frame: hold the binding being edited at a frame of its animation (as saved, or as previewed).
  let pinnedId: string | null = null;
  const currentId = (): string | null => {
    const t = target.value === 'note' ? `note:${noteNum.value}` : target.value;
    return bindingFor(t)?.id ?? null;
  };
  const unpin = (): void => {
    if (pinnedId) d.effects?.pin(pinnedId, null);
    pinnedId = null;
    frameOut.textContent = 'live';
  };
  frameSlider.addEventListener('input', () => {
    const id = currentId();
    if (!id) { say('Nothing bound to that yet: save or preview it first.', true); return; }
    if (pinnedId && pinnedId !== id) d.effects?.pin(pinnedId, null);
    pinnedId = id;
    d.effects?.pin(id, Number(frameSlider.value));
    frameOut.textContent = Number(frameSlider.value).toFixed(2);
  });
  frameRelease.addEventListener('click', unpin);
  target.addEventListener('change', unpin);
  close.addEventListener('click', () => {
    unpin();
    panel.remove(); hl.remove();
    document.body.classList.remove('editing');
    try { sessionStorage.removeItem(STATE_KEY); } catch { /* storage off */ }
    document.querySelector<HTMLButtonElement>('.bind-open')?.removeAttribute('disabled');
  });

  onSelection();
  if (!selection.length) onTarget();
}
