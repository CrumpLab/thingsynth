// The painting layer: the art (web/src/art.ts) full-bleed, letterboxed, never cropped, with an SVG hit layer on
// top whose coordinate system is mapping.json's image-pixel grid, so regions are drawn and hit-tested unchanged.
// The art and the hit layer are separate SVGs of the same aspect in the same box, so they line up exactly and
// changes in the hit layer (debug outlines, highlights) never make the browser repaint the painting.
import type { WebSynthlandHost } from '../runtime/types';
import type { Art } from './art';
import {
  axisPosition, boundingBox, shapePoints, tapNext, valueAt, type Mapping, type Point, type RegionEntry,
} from './mapping';

const SVG = 'http://www.w3.org/2000/svg';

export interface PaintingLayer {
  svg: SVGSVGElement;
  art: Art;
  /** Screen (client) coordinates -> image pixels. */
  toImage(clientX: number, clientY: number): Point;
  /** One SVG element per region, in mapping order. */
  shapes: Map<RegionEntry, SVGPolygonElement>;
  /** Called with the entry and the value just sent to the host. */
  onChange(cb: (entry: RegionEntry, value: number) => void): void;
}

export function mountPainting(stage: HTMLElement, art: Art, mapping: Mapping, host: WebSynthlandHost): PaintingLayer {
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

  const listeners: Array<(entry: RegionEntry, value: number) => void> = [];
  const send = (entry: RegionEntry, value: number): void => {
    host.set(entry.param, value);
    const v = host.get(entry.param);
    for (const cb of listeners) cb(entry, v);
  };
  const desc = (id: string) => host.params().find((p) => p.id === id);

  const shapes = new Map<RegionEntry, SVGPolygonElement>();
  for (const entry of mapping.regions) {
    const el = document.createElementNS(SVG, 'polygon');
    el.setAttribute('points', shapePoints(entry.region).map(([x, y]) => `${x},${y}`).join(' '));
    el.classList.add('region', `g-${entry.gesture}`);
    el.dataset.id = entry.id;
    if (entry.label) {
      const title = document.createElementNS(SVG, 'title');
      title.textContent = entry.label;
      el.append(title);
    }
    svg.append(el);
    shapes.set(entry, el);
    bindGesture(el, entry, toImage, send, () => desc(entry.param), host);
  }

  return { svg, art, toImage, shapes, onChange: (cb) => { listeners.push(cb); } };
}

function bindGesture(
  el: SVGElement,
  entry: RegionEntry,
  toImage: (x: number, y: number) => Point,
  send: (entry: RegionEntry, v: number) => void,
  desc: () => ReturnType<WebSynthlandHost['params']>[number] | undefined,
  host: WebSynthlandHost,
): void {
  const box = boundingBox(entry.region);
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
