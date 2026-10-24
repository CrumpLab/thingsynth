// Messages between the main-thread host and the AudioWorklet processor.

export type ToWorklet =
  | { t: 'param'; i: number; v: number }
  | { t: 'params'; values: Array<[number, number]> }
  | { t: 'midi'; type: number; ch: number; d1: number; d2: number; bend: number }
  | { t: 'reset' }
  | { t: 'seed'; seed: number }
  | { t: 'close' };

export interface EngineParamJson {
  id: string;
  name: string;
  group: string;
  unit: string;
  type: string;
  min: number;
  max: number;
  def: number;
  skew: number;
  smoothMs: number;
  choices: string[] | null;
}

export type FromWorklet =
  | { t: 'ready'; params: EngineParamJson[]; isSynth: boolean; tail: number }
  | { t: 'error'; message: string }
  | { t: 'meter'; voices: number; outL: number; outR: number; telemetry?: number[] };

export interface ProcessorOptions {
  wasmBytes: ArrayBuffer;
  /** 'synth' engines get no input; 'effect' engines read up to 2 input channels. */
  kind: 'synth' | 'effect';
  /** Synths with manifest audioInput read the node input when something is connected to it. */
  audioInput?: boolean;
  seed: number;
  meterHz: number;
  initial: Array<[number, number]>;
}
