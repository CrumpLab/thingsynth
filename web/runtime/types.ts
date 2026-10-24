// Types shared by the runtime, the UI components and the viewer. Mirrors docs/skin-bridge.md.

export type ParamType = 'float' | 'int' | 'bool' | 'choice';

export interface ParamDesc {
  id: string;
  name: string;
  group: string;
  type: ParamType;
  min: number;
  max: number;
  default: number;
  unit: string;
  skew: number;
  smoothMs: number;
  description?: string;
  choices: string[] | null;
  hidden: boolean;
  /** false: not offered for host automation (plugin); presets still store it. */
  automatable?: boolean;
  /** Choice subset (manifest "choices"): the engine's full list... */
  engineChoices?: string[];
  /** ...and the engine index for each plugin choice index. Values in the bridge are plugin indices. */
  choiceMap?: number[];
}

export interface SkinTheme {
  accent?: string;
  panel?: string;
  text?: string;
  [key: string]: string | undefined;
}

export interface PluginManifest {
  id: string;
  name: string;
  kind: 'synth' | 'effect';
  core: string;
  version: string;
  family?: string;
  lineage?: string[];
  description?: string;
  codes?: { manufacturer: string; plugin: string };
  macros?: string[];
  presetCategories?: string[];
  /** Effects that take MIDI notes (plugin: VST3 event input, AU aumf). */
  acceptsMidi?: boolean;
  /** Instruments with an optional audio input (plugin: input bus disabled by default). */
  audioInput?: boolean;
  skin: { entry: string; width: number; height: number; theme?: SkinTheme };
  engine?: { core: string; name: string; version: string; options?: Record<string, unknown> };
  parameters: ParamDesc[];
}

export interface PresetSummary {
  index: number;
  name: string;
  category: string;
  tags: string[];
}

/** One entry of presets/index.json: the preset file plus its slug. */
export interface PresetFile {
  slug: string;
  schema?: string;
  plugin?: string;
  name: string;
  category: string;
  tags?: string[];
  author?: string;
  params: Record<string, number | string | boolean>;
  features?: Record<string, number>;
}

export interface MeterFrame {
  voices: number;
  outL: number;
  outR: number;
}

export type InputSource = 'none' | 'loop' | 'mic';

export interface Capabilities {
  midiKeyboard: boolean;
  audioInput: boolean;
  host: 'web' | 'plugin';
}

export interface SynthlandHost {
  ready(): Promise<void>;
  manifest(): PluginManifest;
  params(): ParamDesc[];
  get(id: string): number;
  set(id: string, value: number): void;
  beginGesture(id: string): void;
  endGesture(id: string): void;
  onParam(cb: (id: string, value: number) => void): () => void;
  presets(): PresetSummary[];
  currentPreset(): number;
  loadPreset(index: number): void;
  onPreset(cb: (index: number) => void): () => void;
  onMeter(cb: (m: MeterFrame) => void): () => void;
  noteOn(note: number, velocity: number): void;
  noteOff(note: number): void;
  capabilities(): Capabilities;
  resize(width: number, height: number): void;
  /** Host-specific native functions (plugin: e.g. 'chooseIr'); resolves undefined when the host has none. */
  call(name: string, ...args: unknown[]): Promise<unknown>;
  /** Engine telemetry: a few numbers whose layout is defined per engine (docs/skin-bridge.md). */
  onTelemetry(cb: (values: number[]) => void): () => void;
  /** The last telemetry frame ([] until one arrives or when the engine publishes none). */
  telemetry(): number[];
}

/** Web-only extensions. Skins feature-detect them (`'audio' in synthland`). */
export interface WebHostExtensions {
  audio: {
    /** Resolves once the AudioContext is running. Must be called from a user gesture the first time. */
    start(): Promise<void>;
    running(): boolean;
    onState(cb: (running: boolean) => void): () => void;
    inputSource(): InputSource;
    setInputSource(kind: InputSource): Promise<void>;
    onInputSource(cb: (kind: InputSource) => void): () => void;
    /** Index of the last loaded preset even when edited, or -1. */
    lastPreset(): number;
    edited(): boolean;
    /** Preset names with the "*" convention. */
    presetLabel(): string;
    /** The engine's output node (the AudioWorkletNode), or null before start(). */
    output(): AudioNode | null;
    /**
     * Feed this node into the engine input (effects, and synths with audioInput) instead of the loop/mic input.
     * While set, setInputSource() is ignored and the loop/mic source is stopped. null removes it.
     */
    setSource(node: AudioNode | null): void;
    /** Raw MIDI into the engine (types as in docs/wasm-abi.md: 0 on, 1 off, 2 cc, 3 bend, 4 at, 5 poly at, 6 all off). */
    midi(type: number, ch: number, d1: number, d2: number, bend: number): void;
    /** Release held notes, stop the worklet, disconnect, remove listeners. A shared AudioContext is left open. */
    dispose(): void;
  };
}

export type WebSynthlandHost = SynthlandHost & WebHostExtensions;

declare global {
  interface Window {
    synthland?: SynthlandHost;
    SYNTHLAND_CONFIG?: Partial<HostOptions>;
    /**
     * Hosts created by an embedding page (the viewer's tabletop), keyed by slot. A skin loaded with ?slot=<key>
     * in a same-origin iframe adopts window.parent.SYNTHLAND_SLOTS[key] instead of creating its own host.
     */
    SYNTHLAND_SLOTS?: Record<string, SynthlandHost>;
  }
}

export interface HostOptions {
  /** URL of plugin.json (default: ./plugin.json relative to the page). */
  pluginUrl: string;
  /** URL of presets/index.json (default: ./presets/index.json). */
  presetsUrl: string;
  /** Directory holding <core>.wasm (default: ../../../wasm/ relative to pluginUrl). */
  wasmBase: string;
  /** URL of the worklet module (default: ../../../runtime/worklet.js relative to pluginUrl). */
  workletUrl: string;
  /** Attach the computer keyboard as a piano (default true). */
  computerKeyboard: boolean;
  /** Request Web MIDI (default true). */
  webMidi: boolean;
  /** Use this AudioContext instead of creating one (the host never closes a context it did not create). */
  audioContext?: AudioContext;
  /**
   * Connect the engine output here instead of the host's own output gain and the speakers. ?mute=1 then is the
   * embedding page's job (it owns the path to the speakers).
   */
  destination?: AudioNode;
  /**
   * Install the window-level hooks (default true): start audio on the first gesture in this window and the
   * synthland:loadPreset / synthland:reset messages. Off for hosts an embedding page creates for several devices.
   */
  windowHooks?: boolean;
}
