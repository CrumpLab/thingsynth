// thingsynth: one painting by Matt Crump as the interface to Tonewheel (SynthLand's tonewheel organ).
// painting layer (SVG hit regions) -> mapping.json -> runtime host (createSynthlandHost) -> additive.wasm in an
// AudioWorklet. Plain DOM, no framework; the runtime is a verbatim copy of SynthLand's web/packages/runtime/src.
import { createSynthlandHost } from '../runtime/host';
import rawMapping from '../../mapping.json';
import { buildArt } from './art';
import { createOutput } from './output';
import { mountEffects } from './effects';
import { parseMapping } from './mapping';
import { loadObjects, resolveObject } from './objects';
import { createWander } from './wander';
import { shuffleBindings } from './shuffle';
import { mountPainting } from './painting';

// Absolute: the runtime resolves presets and wasm relative to the plugin URL, so a relative base (the './' the
// production build uses to live under /thingsynth/ on Pages) would double the path.
const base = new URL(import.meta.env.BASE_URL, document.baseURI).href;
const query = new URLSearchParams(location.search);
const debug = query.has('debug');
const flat = query.has('flat');

const stage = document.getElementById('stage')!;
const startOverlay = document.getElementById('start')!;
const presetSelect = document.getElementById('preset') as HTMLSelectElement;
const status = document.getElementById('status')!;
const debugLink = document.getElementById('debug-link') as HTMLAnchorElement;

async function boot(): Promise<void> {
  const mapping = parseMapping(rawMapping);
  const objects = loadObjects();
  for (const b of mapping.bindings) {
    if (!resolveObject(objects, b.object)) console.warn(`[thingsynth] binding "${b.id}" names unknown object or part "${b.object.replace(/^#/, '')}"`);
  }
  // Start building the painting first: its files load while the runtime fetches plugin.json and the presets.
  const art = buildArt(flat);
  stage.classList.add('loading');
  void art.ready.then(() => stage.classList.remove('loading'), (err: unknown) => {
    console.error('[thingsynth] painting failed to load', err);
    status.textContent = `painting failed to load: ${err instanceof Error ? err.message : String(err)}`;
  });
  const output = createOutput(query.has('mute'));
  const host = createSynthlandHost({
    audioContext: output.context,
    destination: output.input,
    pluginUrl: `${base}tonewheel/plugin.json`,
    presetsUrl: `${base}tonewheel/presets/index.json`,
    wasmBase: `${base}wasm/`,
    workletUrl: `${base}runtime/worklet.js`,
    computerKeyboard: true,
    webMidi: true,
    windowHooks: true, // first pointerdown/keydown anywhere starts audio
  });
  await host.ready();
  const manifest = host.manifest();
  document.getElementById('start-title')!.textContent = `Golden Pyramid With Tunnel Celebration · ${manifest.name}`;
  if (matchMedia('(pointer: coarse)').matches) {
    startOverlay.querySelector('.hint')!.textContent = 'Tap to start the organ. Hold the small shapes to play notes; drag or tap the bigger ones to change the sound.';
  }

  // Warn about mapping entries that name a parameter Tonewheel does not have.
  const ids = new Set(host.params().map((p) => p.id));
  for (const r of [...mapping.regions, ...mapping.bindings]) {
    if ('param' in r && !ids.has(r.param)) console.warn(`[thingsynth] mapping entry "${r.id}" uses unknown param "${r.param}"`);
  }

  const layer = mountPainting(stage, art, mapping, host, objects);
  if (!debug) layer.onChange((entry, v) => { status.textContent = `${entry.param} = ${fmtValue(host, entry.param, v)}`; });
  // Effects draw the bound parameters on the painting's own paths (not in ?flat, which has none).
  const effectsReady = art.flat ? Promise.resolve(null) : art.ready.then(() => mountEffects(art, host, objects, mapping.bindings), () => null);

  // Presets: the select mirrors the runtime's list; ?preset=<slug> or mapping.defaultPreset picks the first one.
  const presets = host.presets();
  const slugs = (await fetch(`${base}tonewheel/presets/index.json`).then((r) => r.json()) as Array<{ slug: string }>).map((p) => p.slug);
  for (const p of presets) {
    const o = document.createElement('option');
    o.value = String(p.index);
    o.textContent = `${p.category} · ${p.name}`;
    presetSelect.append(o);
  }
  const want = query.get('preset') ?? mapping.defaultPreset ?? '';
  const initial = Math.max(0, slugs.indexOf(want));
  if (presets.length > 0) host.loadPreset(initial);
  presetSelect.value = String(host.currentPreset());
  presetSelect.addEventListener('change', () => {
    host.loadPreset(Number(presetSelect.value));
    presetSelect.blur();
  });
  host.onPreset((i) => { if (i >= 0) presetSelect.value = String(i); });

  // The bottom bar wraps on narrow windows: the painting sits just above it, however tall it gets.
  const bar = document.getElementById('bar')!;
  new ResizeObserver(() => { document.documentElement.style.setProperty('--bar-h', `${bar.offsetHeight}px`); }).observe(bar);

  // Wander: every visible parameter random-walks around the preset (web/src/wander.ts). ?wander starts it;
  // ?wander-speed= and ?wander-amount= (0..1) override its defaults.
  const num = (k: string): number | undefined => { const v = Number(query.get(k)); return query.has(k) && Number.isFinite(v) ? v : undefined; };
  const speed = num('wander-speed'), amount = num('wander-amount');
  const wander = createWander(host, { ...(speed !== undefined && { speed }), ...(amount !== undefined && { amount }) });
  const wanderBtn = document.getElementById('wander') as HTMLButtonElement;
  wander.onChange((on) => {
    wanderBtn.setAttribute('aria-pressed', String(on));
  });
  wanderBtn.addEventListener('click', () => { if (wander.running()) wander.stop(); else wander.start(); });
  if (query.has('wander')) wander.start();

  // Shuffle: deal every control, parameters and notes together, onto the painting's animated objects from a seed
  // (web/src/shuffle.ts). ?seed=<n> opens a shuffle; the Shuffle button deals a new seed and writes it into the
  // address so it can be shared; the x goes back to the curated mapping.
  const shuffleBtn = document.getElementById('shuffle') as HTMLButtonElement;
  const shuffleLabel = shuffleBtn.textContent ?? '';
  const unshuffleBtn = document.getElementById('unshuffle') as HTMLButtonElement;
  const paramName = (id: string): string => host.params().find((p) => p.id === id)?.name ?? id;
  const applyShuffle = async (seed: number | null): Promise<void> => {
    const next = seed === null ? mapping.bindings : shuffleBindings(mapping.bindings, objects, seed, { paramName });
    await layer.ready;
    layer.setBindings(next);
    (await effectsReady)?.setBindings(next, 1200);
    const url = new URL(location.href);
    url.searchParams.delete('notes'); // older links: notes are always dealt now
    if (seed === null) url.searchParams.delete('seed'); else url.searchParams.set('seed', String(seed));
    history.replaceState(null, '', url);
    unshuffleBtn.hidden = seed === null;
    shuffleBtn.textContent = shuffleLabel;
    if (seed !== null) shuffleBtn.append(Object.assign(document.createElement('span'), { className: 'seed', textContent: ` · ${seed}` }));
  };
  shuffleBtn.addEventListener('click', () => { void applyShuffle(1 + Math.floor(Math.random() * 9999)); });
  unshuffleBtn.addEventListener('click', () => { void applyShuffle(null); });
  const seedParam = Number(query.get('seed'));
  if (query.has('seed') && Number.isInteger(seedParam)) void applyShuffle(seedParam);

  // Audio state.
  const showStatus = (): void => {
    status.textContent = host.audio.running() ? `${host.audio.presetLabel()} · playing` : 'off';
  };
  host.audio.onState((running) => {
    startOverlay.classList.toggle('hidden', running);
    showStatus();
  });
  host.onPreset(() => showStatus()); // loads and the first edit ("*")
  const kick = (): void => { host.audio.start().catch((err: unknown) => { status.textContent = `audio failed: ${String(err)}`; }); };
  startOverlay.addEventListener('pointerdown', kick);
  startOverlay.addEventListener('keydown', kick);

  if (debug) {
    debugLink.textContent = 'exit debug';
    debugLink.href = location.pathname;
    const { mountDebug } = await import('./debug');
    await layer.ready;
    mountDebug(layer, mapping, host, await effectsReady);
    Object.assign((window as unknown as { thingsynth: object }).thingsynth, { wander, shuffle: applyShuffle, layer, output, objects });
  }
}

function fmtValue(host: ReturnType<typeof createSynthlandHost>, id: string, v: number): string {
  const d = host.params().find((p) => p.id === id);
  if (d?.type === 'choice' && d.choices) return d.choices[Math.round(v)] ?? String(v);
  if (d?.type === 'bool') return v >= 0.5 ? 'on' : 'off';
  return d?.type === 'float' ? v.toFixed(2) : String(Math.round(v));
}

boot().catch((err: unknown) => {
  console.error(err);
  status.textContent = err instanceof Error ? err.message : String(err);
  startOverlay.querySelector('.hint')!.textContent = `Could not start: ${status.textContent}`;
});
