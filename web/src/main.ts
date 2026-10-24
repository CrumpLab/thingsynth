// thingsynth: one painting by Matt Crump as the interface to Tonewheel (SynthLand's tonewheel organ).
// painting layer (SVG hit regions) -> mapping.json -> runtime host (createSynthlandHost) -> additive.wasm in an
// AudioWorklet. Plain DOM, no framework; the runtime is a verbatim copy of SynthLand's web/packages/runtime/src.
import { createSynthlandHost } from '../runtime/host';
import rawMapping from '../../mapping.json';
import { buildArt } from './art';
import { mountEffects } from './effects';
import { parseMapping } from './mapping';
import { loadObjects } from './objects';
import { mountPainting } from './painting';

const base = import.meta.env.BASE_URL;
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
    if (!objects.has(b.object)) console.warn(`[thingsynth] binding "${b.id}" names unknown object "${b.object}"`);
  }
  // Start building the painting first: its files load while the runtime fetches plugin.json and the presets.
  const art = buildArt(flat);
  stage.classList.add('loading');
  void art.ready.then(() => stage.classList.remove('loading'), (err: unknown) => {
    console.error('[thingsynth] painting failed to load', err);
    status.textContent = `painting failed to load: ${err instanceof Error ? err.message : String(err)}`;
  });
  const host = createSynthlandHost({
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

  // Warn about mapping entries that name a parameter Tonewheel does not have.
  const ids = new Set(host.params().map((p) => p.id));
  for (const r of [...mapping.regions, ...mapping.bindings]) {
    if (!ids.has(r.param)) console.warn(`[thingsynth] mapping entry "${r.id}" uses unknown param "${r.param}"`);
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

  // Audio state.
  host.audio.onState((running) => {
    startOverlay.classList.toggle('hidden', running);
    status.textContent = running ? `${host.audio.presetLabel()} · playing` : 'off';
  });
  const kick = (): void => { host.audio.start().catch((err: unknown) => { status.textContent = `audio failed: ${String(err)}`; }); };
  startOverlay.addEventListener('pointerdown', kick);
  startOverlay.addEventListener('keydown', kick);

  if (debug) {
    debugLink.textContent = 'exit debug';
    debugLink.href = location.pathname;
    const { mountDebug } = await import('./debug');
    await layer.ready;
    mountDebug(layer, mapping, host, await effectsReady);
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
