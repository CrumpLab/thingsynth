// The painting layer: the art (web/src/art.ts) full-bleed, letterboxed, never cropped, with an SVG hit layer on
// top whose coordinate system is mapping.json's image-pixel grid, so regions are drawn and hit-tested unchanged.
// The art and the hit layer are separate SVGs of the same aspect in the same box, so they line up exactly and
// changes in the hit layer (debug outlines, highlights) never make the browser repaint the painting.
//
// Controls come from two places: v1 regions (hand-drawn rects and polygons) and v2 bindings with a gesture,
// whose hit area is the bound object's own fill outlines, cloned into the hit layer once the art has loaded.
import type { WebSynthlandHost } from '../runtime/types';
import type { Art } from './art';
import { layers } from './art';
import { resolveObject, type ArtObject } from './objects';
import {
  axisPosition, boundingBox, shapePoints, tapNext, valueAt, type Binding, type Box, type Control, type Mapping,
  type NoteBinding, type Point,
} from './mapping';

const SVG = 'http://www.w3.org/2000/svg';

export interface ControlShape {
  control: Control;
  /** The hit element: a <polygon> for regions, a <g> of the object's outlines for bindings. */
  el: SVGGraphicsElement;
  /** Bounding box in mapping (image-pixel) coordinates; gestures measure positions against it. */
  box: Box;
  binding?: Binding;
}

export interface PaintingLayer {
  svg: SVGSVGElement;
  art: Art;
  /** Screen (client) coordinates -> image pixels. */
  toImage(clientX: number, clientY: number): Point;
  /** Every parameter control, regions first then bindings, in mapping order. Binding shapes arrive with `ready`. */
  controls: ControlShape[];
  /** Note bindings with a gesture: the object plays its note when touched. */
  notePads: Array<{ binding: NoteBinding; el: SVGGraphicsElement; box: Box }>;
  /** Resolves when every control's hit shape is in place. */
  ready: Promise<void>;
  /** Called with the control and the value just sent to the host. */
  onChange(cb: (control: Control, value: number) => void): void;
}

export function mountPainting(
  stage: HTMLElement, art: Art, mapping: Mapping, host: WebSynthlandHost, objects: Map<string, ArtObject>,
): PaintingLayer {
  const [W, H] = mapping.size;

  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.classList.add('hits');
  stage.append(art.el, svg);

  const toImage = (clientX: number, clientY: number): Point => {
    const ctm = svg.getScreenCTM();
    if (!ctm) return [0, 0];
    const p = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse());
    return [Math.round(p.x), Math.round(p.y)];
  };

  const listeners: Array<(control: Control, value: number) => void> = [];
  const send = (control: Control, value: number): void => {
    host.set(control.param, value);
    const v = host.get(control.param);
    for (const cb of listeners) cb(control, v);
  };
  const desc = (id: string) => host.params().find((p) => p.id === id);
  const label = (el: SVGElement, control: Control): void => {
    el.classList.add('region', `g-${control.gesture}`);
    el.dataset.id = control.id;
    if (control.label) {
      const title = document.createElementNS(SVG, 'title');
      title.textContent = control.label;
      el.append(title);
    }
  };

  const controls: ControlShape[] = [];
  const notePads: PaintingLayer['notePads'] = [];
  for (const entry of mapping.regions) {
    const el = document.createElementNS(SVG, 'polygon');
    el.setAttribute('points', shapePoints(entry.region).map(([x, y]) => `${x},${y}`).join(' '));
    label(el, entry);
    svg.append(el);
    const box = boundingBox(entry.region);
    controls.push({ control: entry, el, box });
    bindGesture(el, entry, box, toImage, send, () => desc(entry.param), host);
  }

  // Bindings with a gesture: the object's fills, in canvas units, scaled into mapping units.
  const k = W / layers.canvas[0];
  const ready = art.ready.catch(() => undefined).then(() => {
    for (const binding of mapping.bindings) {
      if (!binding.gesture) continue;
      const obj = resolveObject(objects, binding.object);
      if (!obj) continue; // main.ts warns
      const g = document.createElementNS(SVG, 'g');
      g.setAttribute('transform', `scale(${k})`);
      const ds = obj.fills.map((id) => art.fills.get(id)?.getAttribute('d')).filter((d): d is string => !!d);
      if (ds.length > 0) {
        for (const d of ds) {
          const p = document.createElementNS(SVG, 'path');
          p.setAttribute('d', d);
          g.append(p);
        }
      } else {
        // ?flat has no vector fills: fall back to the object's bounding box.
        const [x, y, w, h] = obj.bbox;
        const r = document.createElementNS(SVG, 'rect');
        r.setAttribute('x', String(x)); r.setAttribute('y', String(y)); r.setAttribute('width', String(w)); r.setAttribute('height', String(h));
        g.append(r);
      }
      svg.append(g);
      const [x, y, w, h] = obj.bbox;
      const box: Box = { x: x * k, y: y * k, w: Math.max(1, w * k), h: Math.max(1, h * k) };
      if (binding.kind === 'note') {
        g.classList.add('region', 'note-pad', `g-${binding.gesture}`);
        g.dataset.id = binding.id;
        notePads.push({ binding, el: g, box });
        bindNote(g, binding, host);
        continue;
      }
      const control: Control = { id: binding.id, gesture: binding.gesture, param: binding.param, range: binding.range, curve: binding.curve };
      if (binding.label) control.label = binding.label;
      if (binding.step !== undefined) control.step = binding.step;
      label(g, control);
      controls.push({ control, el: g, box, binding });
      bindGesture(g, control, box, toImage, send, () => desc(control.param), host);
    }
  });

  return { svg, art, toImage, controls, notePads, ready, onChange: (cb) => { listeners.push(cb); } };
}

/** A note binding's object as a pad: hold sounds while pressed, tap sounds for a moment. */
function bindNote(el: SVGElement, binding: NoteBinding, host: WebSynthlandHost): void {
  el.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0 || ev.shiftKey) return;
    void host.audio.start().catch(() => undefined);
    host.noteOn(binding.note, 100);
    if (binding.gesture === 'tap') {
      window.setTimeout(() => host.noteOff(binding.note), 220);
      return;
    }
    el.setPointerCapture(ev.pointerId);
    const release = (): void => {
      host.noteOff(binding.note);
      el.removeEventListener('pointerup', release);
      el.removeEventListener('pointercancel', release);
    };
    el.addEventListener('pointerup', release);
    el.addEventListener('pointercancel', release);
  });
}

function bindGesture(
  el: SVGElement,
  entry: Control,
  box: Box,
  toImage: (x: number, y: number) => Point,
  send: (entry: Control, v: number) => void,
  desc: () => ReturnType<WebSynthlandHost['params']>[number] | undefined,
  host: WebSynthlandHost,
): void {
  const start = (): void => { void host.audio.start().catch(() => undefined); };
  const atPointer = (ev: PointerEvent): number => valueAt(entry, axisPosition(entry, box, toImage(ev.clientX, ev.clientY)));

  switch (entry.gesture) {
    case 'tap':
      el.addEventListener('pointerdown', (ev) => {
        if (ev.button !== 0 || ev.shiftKey) return;
        start();
        send(entry, tapNext(entry, desc(), host.get(entry.param)));
      });
      break;
    case 'hold':
      el.addEventListener('pointerdown', (ev) => {
        if (ev.button !== 0 || ev.shiftKey) return;
        start();
        el.setPointerCapture(ev.pointerId);
        host.beginGesture(entry.param);
        send(entry, entry.range[1]);
        const release = (): void => {
          send(entry, entry.range[0]);
          host.endGesture(entry.param);
          el.removeEventListener('pointerup', release);
          el.removeEventListener('pointercancel', release);
        };
        el.addEventListener('pointerup', release);
        el.addEventListener('pointercancel', release);
      });
      break;
    case 'drag-x':
    case 'drag-y':
      el.addEventListener('pointerdown', (ev) => {
        if (ev.button !== 0 || ev.shiftKey) return;
        start();
        ev.preventDefault();
        el.setPointerCapture(ev.pointerId);
        host.beginGesture(entry.param);
        send(entry, atPointer(ev));
        const move = (e: PointerEvent): void => send(entry, atPointer(e));
        const end = (): void => {
          host.endGesture(entry.param);
          el.removeEventListener('pointermove', move);
          el.removeEventListener('pointerup', end);
          el.removeEventListener('pointercancel', end);
        };
        el.addEventListener('pointermove', move);
        el.addEventListener('pointerup', end);
        el.addEventListener('pointercancel', end);
      });
      break;
    case 'hover':
      el.addEventListener('pointermove', (ev) => {
        if (ev.pointerType === 'touch' && ev.buttons === 0) return;
        send(entry, atPointer(ev));
      });
      break;
  }
}
