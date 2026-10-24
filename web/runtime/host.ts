// The web implementation of window.synthland (docs/skin-bridge.md) on top of an AudioWorklet + WASM engine.
import type { FromWorklet, ProcessorOptions, ToWorklet } from './messages';
import type {
  Capabilities, HostOptions, InputSource, MeterFrame, ParamDesc, PluginManifest, PresetFile, PresetSummary,
  WebSynthlandHost,
} from './types';
import { renderDrumLoop } from './loop';
import { connectWebMidi } from './midi';
import { attachComputerKeyboard } from './keyboard';

type Listener<T extends unknown[]> = (...args: T) => void;

class Signal<T extends unknown[]> {
  private subs = new Set<Listener<T>>();
  on(cb: Listener<T>): () => void {
    this.subs.add(cb);
    return () => this.subs.delete(cb);
  }
  emit(...args: T): void {
    for (const cb of Array.from(this.subs)) cb(...args);
  }
}

function resolveDefaults(opts: Partial<HostOptions>): HostOptions {
  const base = typeof document !== 'undefined' ? document.baseURI : 'http://localhost/';
  const pluginUrl = new URL(opts.pluginUrl ?? './plugin.json', base).href;
  const root = new URL('../../../', pluginUrl).href; // plugins/<id>/skin/ -> site root
  return {
    pluginUrl,
    presetsUrl: new URL(opts.presetsUrl ?? './presets/index.json', pluginUrl).href,
    wasmBase: new URL(opts.wasmBase ?? 'wasm/', root).href,
    workletUrl: new URL(opts.workletUrl ?? 'runtime/worklet.js', root).href,
    computerKeyboard: opts.computerKeyboard ?? true,
    webMidi: opts.webMidi ?? true,
    audioContext: opts.audioContext,
    destination: opts.destination,
    windowHooks: opts.windowHooks ?? true,
  };
}

// addModule once per context and URL (hosts sharing a context share the processor registration).
const workletModules = new WeakMap<BaseAudioContext, Map<string, Promise<void>>>();
function addWorkletModule(ctx: BaseAudioContext, url: string): Promise<void> {
  let m = workletModules.get(ctx);
  if (!m) {
    m = new Map();
    workletModules.set(ctx, m);
  }
  let p = m.get(url);
  if (!p) {
    p = ctx.audioWorklet.addModule(url);
    p.catch(() => m.delete(url));
    m.set(url, p);
  }
  return p;
}

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

export function createSynthlandHost(options: Partial<HostOptions> = {}): WebSynthlandHost {
  const opts = resolveDefaults({ ...(typeof window !== 'undefined' ? window.SYNTHLAND_CONFIG : {}), ...options });

  let manifest: PluginManifest | null = null;
  let params: ParamDesc[] = [];
  let presetFiles: PresetFile[] = [];
  let summaries: PresetSummary[] = [];
  const byId = new Map<string, ParamDesc>();
  const indexOf = new Map<string, number>();
  const values = new Map<string, number>();

  let lastPreset = -1;
  let edited = false;

  const paramSignal = new Signal<[string, number]>();
  const presetSignal = new Signal<[number]>();
  const meterSignal = new Signal<[MeterFrame]>();
  const telemetrySignal = new Signal<[number[]]>();
  let telemetry: number[] = [];
  const stateSignal = new Signal<[boolean]>();
  const inputSignal = new Signal<[InputSource]>();

  let ctx: AudioContext | null = null;
  let ownsCtx = false;
  let disposed = false;
  let upstream: AudioNode | null = null; // setSource(): an embedding page's node feeding the engine input
  const teardown: Array<() => void> = [];
  let node: AudioWorkletNode | null = null;
  let outGain: GainNode | null = null;
  let wasmBytes: ArrayBuffer | null = null;
  let engineReady = false;
  let starting: Promise<void> | null = null;
  let midiInputs = 0;
  let inputKind: InputSource = 'none';
  let inputNode: AudioNode | null = null;
  let inputStream: MediaStream | null = null;
  let loopBuffer: AudioBuffer | null = null;
  const heldNotes = new Set<number>();

  const post = (m: ToWorklet): void => {
    if (!disposed) node?.port.postMessage(m);
  };

  // ---- loading --------------------------------------------------------------------------------
  const readyPromise = (async () => {
    const res = await fetch(opts.pluginUrl);
    if (!res.ok) throw new Error(`cannot load ${opts.pluginUrl}: ${res.status}`);
    manifest = (await res.json()) as PluginManifest;
    params = manifest.parameters;
    params.forEach((p, i) => {
      byId.set(p.id, p);
      indexOf.set(p.id, i);
      values.set(p.id, p.default);
    });
    try {
      const pr = await fetch(opts.presetsUrl);
      if (pr.ok) {
        const list = (await pr.json()) as PresetFile[];
        presetFiles = Array.isArray(list) ? list : [];
      }
    } catch {
      presetFiles = [];
    }
    summaries = presetFiles.map((p, index) => ({ index, name: p.name, category: p.category, tags: p.tags ?? [] }));
    // Prefetch the wasm so the first gesture starts quickly.
    void fetch(new URL(`${manifest.core}.wasm`, opts.wasmBase).href)
      .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(`wasm ${r.status}`))))
      .then((b) => {
        wasmBytes = b;
      })
      .catch((err: unknown) => console.warn('[synthland] wasm prefetch failed', err));
  })();

  // ---- value conversion -----------------------------------------------------------------------
  // Preset values: choices by name (the plugin's choices) or by engine index (mapped into a choice subset).
  const coerce = (p: ParamDesc, raw: number | string | boolean): number => {
    if (typeof raw === 'boolean') return raw ? 1 : 0;
    if (typeof raw === 'string') {
      if (p.choices) {
        const i = p.choices.indexOf(raw);
        if (i >= 0) return i;
      }
      const n = Number(raw);
      return Number.isFinite(n) ? fromEngineChoice(p, n) : p.default;
    }
    return fromEngineChoice(p, raw);
  };
  const fromEngineChoice = (p: ParamDesc, v: number): number => {
    if (p.type !== 'choice' || !p.choiceMap) return v;
    const k = p.choiceMap.indexOf(Math.round(v));
    return k >= 0 ? k : p.default;
  };
  // Bridge value (plugin units; subset choices as plugin index) -> what the engine expects.
  const toEngine = (p: ParamDesc | undefined, v: number): number => {
    if (!p || p.type !== 'choice' || !p.choiceMap) return v;
    return p.choiceMap[Math.min(p.choiceMap.length - 1, Math.max(0, Math.round(v)))] ?? v;
  };
  const normalizeValue = (p: ParamDesc, v: number): number => {
    if (!Number.isFinite(v)) return p.default;
    let x = clamp(v, p.min, p.max);
    if (p.type !== 'float') x = Math.round(x);
    return x;
  };

  // ---- audio ----------------------------------------------------------------------------------
  const startAudio = async (): Promise<void> => {
    if (disposed) return Promise.resolve();
    if (starting) return starting;
    starting = (async () => {
      await readyPromise;
      if (!manifest) throw new Error('no manifest');
      if (disposed) return;
      if (!ctx) {
        if (opts.audioContext) ctx = opts.audioContext;
        else {
          ctx = new AudioContext({ latencyHint: 'interactive' });
          ownsCtx = true;
        }
        if (!opts.destination) {
          outGain = ctx.createGain();
          // ?mute=1 on the page (or its same-origin parent, the viewer) silences the speakers while the engine,
          // meters and voice counts keep running: for automated browser checks that must not be heard.
          outGain.gain.value = isMuted() ? 0 : 1;
          outGain.connect(ctx.destination);
        }
        const c = ctx;
        const onState = (): void => stateSignal.emit(c.state === 'running' && engineReady);
        c.addEventListener('statechange', onState);
        teardown.push(() => c.removeEventListener('statechange', onState));
      }
      if (ctx.state !== 'running') await ctx.resume();
      if (!node) {
        if (!wasmBytes) {
          const r = await fetch(new URL(`${manifest.core}.wasm`, opts.wasmBase).href);
          if (!r.ok) throw new Error(`cannot load wasm for ${manifest.core}`);
          wasmBytes = await r.arrayBuffer();
        }
        await addWorkletModule(ctx, opts.workletUrl);
        if (disposed) return;
        const initial: Array<[number, number]> = params.map((p, i) => [i, toEngine(p, values.get(p.id) ?? p.default)]);
        const processorOptions: ProcessorOptions = {
          wasmBytes: wasmBytes.slice(0),
          kind: manifest.kind,
          audioInput: manifest.kind === 'synth' && manifest.audioInput === true,
          seed: 1,
          meterHz: 20,
          initial,
        };
        node = new AudioWorkletNode(ctx, 'synthland-engine', {
          numberOfInputs: manifest.kind === 'effect' || manifest.audioInput === true ? 1 : 0,
          numberOfOutputs: 1,
          outputChannelCount: [2],
          channelCount: 2,
          channelCountMode: 'explicit',
          processorOptions,
        });
        node.port.onmessage = (ev: MessageEvent<FromWorklet>) => {
          const m = ev.data;
          if (m.t === 'meter') {
            meterSignal.emit({ voices: m.voices, outL: m.outL, outR: m.outR });
            if (m.telemetry && m.telemetry.length > 0) {
              telemetry = m.telemetry;
              telemetrySignal.emit(telemetry);
            }
          }
          else if (m.t === 'ready') {
            engineReady = true;
            stateSignal.emit(ctx?.state === 'running');
            // Sanity check: engine order must match plugin.json order.
            const mism = m.params.findIndex((q, i) => params[i]?.id !== q.id);
            if (mism >= 0) console.warn('[synthland] parameter order mismatch at', mism, m.params[mism]?.id);
          } else if (m.t === 'error') console.error('[synthland] worklet:', m.message);
        };
        node.connect(opts.destination ?? outGain!);
        if (upstream) upstream.connect(node);
        else if (inputNode) inputNode.connect(node);
      }
      stateSignal.emit(true);
    })();
    try {
      await starting;
    } catch (err) {
      starting = null;
      throw err;
    }
  };

  const disconnectInput = (): void => {
    if (inputNode) {
      try {
        inputNode.disconnect();
      } catch {
        /* already disconnected */
      }
      if (inputNode instanceof AudioBufferSourceNode) inputNode.stop();
    }
    inputNode = null;
    if (inputStream) {
      for (const tr of inputStream.getTracks()) tr.stop();
      inputStream = null;
    }
  };

  const setInputSource = async (kind: InputSource): Promise<void> => {
    if (kind === inputKind && inputNode) return;
    if (upstream) {
      // The embedding page feeds this engine (setSource); loop and mic stay off meanwhile.
      if (inputKind !== 'none') {
        inputKind = 'none';
        inputSignal.emit('none');
      }
      return;
    }
    await startAudio();
    if (!ctx || !node || upstream) return;
    disconnectInput();
    if (kind === 'loop') {
      loopBuffer ??= renderDrumLoop(ctx);
      const src = ctx.createBufferSource();
      src.buffer = loopBuffer;
      src.loop = true;
      src.connect(node);
      src.start();
      inputNode = src;
    } else if (kind === 'mic') {
      try {
        inputStream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
        });
        const src = ctx.createMediaStreamSource(inputStream);
        src.connect(node);
        inputNode = src;
      } catch (err) {
        console.warn('[synthland] microphone unavailable', err);
        kind = 'none';
      }
    }
    inputKind = kind;
    inputSignal.emit(kind);
  };

  // ---- MIDI -----------------------------------------------------------------------------------
  const midiSink = {
    midi: (type: number, ch: number, d1: number, d2: number, bend: number) => {
      post({ t: 'midi', type, ch, d1, d2, bend });
    },
    noteOn: (note: number, vel: number) => {
      if (!disposed) host.noteOn(note, vel);
    },
    noteOff: (note: number) => {
      if (!disposed) host.noteOff(note);
    },
  };

  if (typeof window !== 'undefined') {
    void readyPromise.then(() => {
      if (disposed) return;
      if (manifest?.kind !== 'synth' && manifest?.acceptsMidi !== true) return;
      if (opts.webMidi) {
        void connectWebMidi(midiSink, (n) => {
          midiInputs = n;
        });
      }
      if (opts.computerKeyboard) teardown.push(attachComputerKeyboard(window, midiSink));
    });
    if (opts.windowHooks) {
      // Start audio on the first gesture anywhere in the skin.
      const kick = (): void => {
        startAudio().catch((err: unknown) => console.error('[synthland] audio start failed', err));
      };
      for (const type of ['pointerdown', 'keydown', 'touchstart'] as const) {
        window.addEventListener(type, kick, { once: true, passive: true, capture: true });
        teardown.push(() => window.removeEventListener(type, kick, { capture: true }));
      }
    }
  }

  // ---- the host object ------------------------------------------------------------------------
  const host: WebSynthlandHost = {
    ready: () => readyPromise,
    manifest: () => {
      if (!manifest) throw new Error('synthland: manifest not loaded yet (await ready())');
      return manifest;
    },
    params: () => params,
    get: (id) => values.get(id) ?? byId.get(id)?.default ?? 0,
    set: (id, value) => {
      const p = byId.get(id);
      if (!p) return;
      const v = normalizeValue(p, value);
      if (values.get(id) === v) return;
      values.set(id, v);
      post({ t: 'param', i: indexOf.get(id) ?? -1, v: toEngine(p, v) });
      if (!edited && lastPreset >= 0) {
        edited = true;
        presetSignal.emit(-1);
      }
      paramSignal.emit(id, v);
    },
    beginGesture: () => undefined,
    endGesture: () => undefined,
    onParam: (cb) => paramSignal.on(cb),
    presets: () => summaries,
    currentPreset: () => (edited ? -1 : lastPreset),
    loadPreset: (index) => {
      const file = presetFiles[index];
      if (!file) return;
      const batch: Array<[number, number]> = [];
      const changed: Array<[string, number]> = [];
      for (const p of params) {
        const raw = file.params[p.id];
        const v = normalizeValue(p, raw === undefined ? p.default : coerce(p, raw));
        batch.push([indexOf.get(p.id) ?? 0, toEngine(p, v)]);
        if (values.get(p.id) !== v) {
          values.set(p.id, v);
          changed.push([p.id, v]);
        }
      }
      post({ t: 'params', values: batch });
      lastPreset = index;
      edited = false;
      for (const [id, v] of changed) paramSignal.emit(id, v);
      presetSignal.emit(index);
    },
    onPreset: (cb) => presetSignal.on(cb),
    onMeter: (cb) => meterSignal.on(cb),
    noteOn: (note, velocity) => {
      if (!engineReady) {
        startAudio().catch(() => undefined);
      }
      heldNotes.add(note);
      post({ t: 'midi', type: 0, ch: 0, d1: note & 127, d2: clamp(Math.round(velocity), 1, 127), bend: 0 });
    },
    noteOff: (note) => {
      heldNotes.delete(note);
      post({ t: 'midi', type: 1, ch: 0, d1: note & 127, d2: 0, bend: 0 });
    },
    capabilities: (): Capabilities => ({
      midiKeyboard: midiInputs > 0,
      audioInput: manifest?.kind === 'effect' || manifest?.audioInput === true,
      host: 'web',
    }),
    // The web host has no native functions (user files are plugin-only for now).
    call: () => Promise.resolve(undefined),
    onTelemetry: (cb) => telemetrySignal.on(cb),
    telemetry: () => telemetry,
    resize: (width, height) => {
      if (typeof window !== 'undefined' && window.parent !== window) {
        window.parent.postMessage({ type: 'synthland:resize', width, height }, '*');
      }
    },
    audio: {
      start: startAudio,
      running: () => ctx?.state === 'running' && engineReady,
      onState: (cb) => stateSignal.on(cb),
      inputSource: () => inputKind,
      setInputSource,
      onInputSource: (cb) => inputSignal.on(cb),
      lastPreset: () => lastPreset,
      edited: () => edited,
      presetLabel: () => {
        const s = summaries[lastPreset];
        if (!s) return edited || lastPreset < 0 ? 'Init' + (edited ? ' *' : '') : '';
        return s.name + (edited ? ' *' : '');
      },
      output: () => node,
      setSource: (src) => {
        if (src === upstream || disposed) return;
        if (upstream && node) {
          try {
            upstream.disconnect(node);
          } catch {
            /* not connected */
          }
        }
        upstream = src;
        if (src) {
          disconnectInput();
          if (inputKind !== 'none') {
            inputKind = 'none';
            inputSignal.emit('none');
          }
          if (node) src.connect(node);
        }
      },
      midi: (type, ch, d1, d2, bend) => midiSink.midi(type, ch, d1, d2, bend),
      dispose: () => {
        if (disposed) return;
        for (const n of Array.from(heldNotes)) host.noteOff(n);
        heldNotes.clear();
        post({ t: 'midi', type: 6, ch: 0, d1: 0, d2: 0, bend: 0 });
        disposed = true;
        for (const fn of teardown.splice(0)) fn();
        disconnectInput();
        if (upstream && node) {
          try {
            upstream.disconnect(node);
          } catch {
            /* not connected */
          }
        }
        upstream = null;
        if (node) {
          node.port.postMessage({ t: 'close' } satisfies ToWorklet);
          node.port.onmessage = null;
          node.disconnect();
          node = null;
        }
        outGain?.disconnect();
        outGain = null;
        engineReady = false;
        if (ownsCtx && ctx) void ctx.close().catch(() => undefined);
        ctx = null;
        stateSignal.emit(false);
      },
    },
  };

  // Debug/automation hooks for the embedding page (same origin).
  if (typeof window !== 'undefined' && opts.windowHooks) {
    const onMessage = (ev: MessageEvent): void => {
      const d = ev.data as { type?: string; index?: number } | null;
      if (!d || typeof d !== 'object') return;
      if (d.type === 'synthland:loadPreset' && typeof d.index === 'number') host.loadPreset(d.index);
      if (d.type === 'synthland:reset') post({ t: 'reset' });
    };
    window.addEventListener('message', onMessage);
    teardown.push(() => window.removeEventListener('message', onMessage));
  }

  return host;
}

function isMuted(): boolean {
  const has = (w: Window | null): boolean => {
    try { return !!w && new URLSearchParams(w.location.search).has('mute'); } catch { return false; }
  };
  return has(window) || (window.parent !== window && has(window.parent));
}
