// The painting rebuilt from its PSD layers (tools/extract_psd.py): one static SVG whose user units are PSD canvas
// pixels, stacking the colour wash, the vector fills, the pencil scribbles and the vector ink, clipped to the
// painted area, with the published caption strip below. Every fill and ink stroke is its own <path> with a
// stable id (f001.., i0001..) so later milestones can animate them; nothing here moves yet.
//
// ?flat shows the published JPEG instead (fallback and for comparison).
import layersJson from '../../art/golden-pyramid-with-tunnel-celebration/layers/layers.json';
import fillsUrl from '../../art/golden-pyramid-with-tunnel-celebration/layers/fills.svg?url';
import inkUrl from '../../art/golden-pyramid-with-tunnel-celebration/layers/ink.svg?url';
import washUrl from '../../art/golden-pyramid-with-tunnel-celebration/layers/wash.webp?url';
import scribblesUrl from '../../art/golden-pyramid-with-tunnel-celebration/layers/scribbles.webp?url';
import captionUrl from '../../art/golden-pyramid-with-tunnel-celebration/layers/caption.webp?url';
import jpegUrl from '../../art/golden-pyramid-with-tunnel-celebration/golden-pyramid-with-tunnel-celebration.jpg';

const SVG = 'http://www.w3.org/2000/svg';
const TITLE = 'Golden Pyramid With Tunnel Celebration';

export interface LayersInfo {
  schema: 'thingsynth.layers/1';
  canvas: [number, number];
  /** The frame's hole: x, y, w, h in canvas pixels. */
  painted: [number, number, number, number];
  caption: { file: string; box: [number, number, number, number] };
  counts: { fills: number; ink: number };
}

export const layers = layersJson as unknown as LayersInfo;

export interface Art {
  /** The element to put in the stage (an <svg>, or an <img> in flat mode). */
  el: SVGSVGElement | HTMLImageElement;
  /** Resolves once the vector layers are in the DOM and the rasters have decoded. */
  ready: Promise<void>;
  /** Fill and ink paths by id (empty in flat mode). */
  fills: Map<string, SVGPathElement>;
  ink: Map<string, SVGPathElement>;
  /** The groups and images of the stack (null in flat mode), for effects that add or move layers. */
  stack: { fills: SVGGElement; ink: SVGGElement; scribbles: SVGImageElement; defs: SVGDefsElement } | null;
  flat: boolean;
}

function el<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number>): SVGElementTagNameMap[K] {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  return e;
}

/** Fetch one of the exported SVG files and move its paths into `into`, indexing them by id. */
async function loadPaths(url: string, into: SVGGElement, index: Map<string, SVGPathElement>): Promise<void> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`cannot load ${url}: ${res.status}`);
  const doc = new DOMParser().parseFromString(await res.text(), 'image/svg+xml');
  const root = doc.documentElement;
  if (root.nodeName !== 'svg') throw new Error(`${url} is not an SVG`);
  // ink.svg wraps its paths in <g fill="#000">; carry the group's attributes onto `into`.
  const wrapper = root.querySelector(':scope > g');
  if (wrapper) for (const a of Array.from(wrapper.attributes)) into.setAttribute(a.name, a.value);
  const frag = document.createDocumentFragment();
  for (const p of Array.from(root.querySelectorAll('path'))) {
    const node = document.importNode(p, false) as SVGPathElement;
    index.set(node.id, node);
    frag.append(node);
  }
  into.append(frag);
}

function loaded(img: SVGImageElement, url: string): Promise<void> {
  // The <image>'s own load event (HTMLImageElement.decode() never settles in a background tab, which would keep
  // the painting hidden until the tab is shown). Errors resolve too: a missing raster must not block the rest.
  return new Promise((resolve) => {
    img.addEventListener('load', () => resolve(), { once: true });
    img.addEventListener('error', () => { console.warn(`[thingsynth] could not load ${url}`); resolve(); }, { once: true });
    img.setAttribute('href', url);
  });
}

export function buildArt(flat: boolean): Art {
  const fills = new Map<string, SVGPathElement>();
  const ink = new Map<string, SVGPathElement>();
  if (flat) {
    const img = document.createElement('img');
    img.src = jpegUrl;
    img.alt = TITLE;
    img.draggable = false;
    img.className = 'painting';
    const ready = new Promise<void>((resolve) => {
      img.addEventListener('load', () => resolve(), { once: true });
      img.addEventListener('error', () => resolve(), { once: true });
    });
    return { el: img, ready, fills, ink, stack: null, flat: true };
  }

  const [W, H] = layers.canvas;
  const [px, py, pw, ph] = layers.painted;
  const [cx, cy, cw, ch] = layers.caption.box;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMid meet', role: 'img', 'aria-label': TITLE });
  svg.classList.add('painting', 'art');
  const defs = el('defs', {});
  const clip = el('clipPath', { id: 'ts-painted' });
  clip.append(el('rect', { x: px, y: py, width: pw, height: ph }));
  defs.append(clip);

  const paper = el('rect', { x: 0, y: 0, width: W, height: H, fill: '#fff' });
  const painted = el('g', { 'clip-path': 'url(#ts-painted)' });
  const wash = el('image', { x: 0, y: 0, width: W, height: H, preserveAspectRatio: 'none' });
  const fillsG = el('g', { id: 'ts-fills' });
  const scribbles = el('image', { x: 0, y: 0, width: W, height: H, preserveAspectRatio: 'none' });
  const inkG = el('g', { id: 'ts-ink' });
  painted.append(wash, fillsG, scribbles, inkG);
  const caption = el('image', { x: cx, y: cy, width: cw, height: ch, preserveAspectRatio: 'none' });
  svg.append(defs, paper, painted, caption);

  const ready = Promise.all([
    loadPaths(fillsUrl, fillsG, fills),
    loadPaths(inkUrl, inkG, ink),
    loaded(wash, washUrl),
    loaded(scribbles, scribblesUrl),
    loaded(caption, captionUrl),
  ]).then(() => {
    if (fills.size !== layers.counts.fills || ink.size !== layers.counts.ink) {
      console.warn(`[thingsynth] expected ${layers.counts.fills} fills and ${layers.counts.ink} ink paths, got ${fills.size} and ${ink.size}`);
    }
  });
  return { el: svg, ready, fills, ink, stack: { fills: fillsG, ink: inkG, scribbles, defs }, flat: false };
}
