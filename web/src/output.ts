// The path from the organ to the speakers, owned by thingsynth (the runtime's `destination` option) so it can
// include a safety stage: with Drive up, many drawbars out and wander moving the levels, Tonewheel's output can
// pass full scale (measured +6 dBFS), which the browser would clip harshly. The stage is exactly linear up to
// -4.4 dBFS and rounds louder peaks with a tanh knee that never passes -1 dBFS. ?mute keeps everything running
// silently, as the runtime's own path did.

export interface Output {
  context: AudioContext;
  /** Connect the engine here. */
  input: AudioNode;
  /** What goes to the speakers (before ?mute), for meters and checks. */
  meter: AnalyserNode;
}

const CEILING = 0.89; // -1 dBFS
const KNEE = 0.6; // -4.4 dBFS: below this the stage is exactly linear

/** The transfer curve on the real signal: linear to the knee, then a tanh shoulder up to the ceiling. */
function shape(x: number): number {
  const a = Math.abs(x);
  if (a <= KNEE) return x;
  return Math.sign(x) * (KNEE + (CEILING - KNEE) * Math.tanh((a - KNEE) / (CEILING - KNEE)));
}

export function createOutput(muted: boolean): Output {
  const context = new AudioContext({ latencyHint: 'interactive' }); // starts suspended; the first gesture resumes it
  const input = context.createGain();
  const soft = context.createWaveShaper();
  // The curve spans inputs -1..1 (louder inputs take its end values): unity gain when quiet, never past the ceiling.
  // Inputs beyond full scale need headroom to be rounded rather than flattened, so the stage works at half level
  // and gives it back after the curve.
  const curve = new Float32Array(4097);
  for (let i = 0; i < curve.length; i++) curve[i] = shape(2 * (i / 2048 - 1)) / 2; // works at half level
  soft.curve = curve;
  soft.oversample = 'none'; // oversampling filters ring past the curve (measured -0.2 dBFS with '2x')
  const pre = context.createGain();
  pre.gain.value = 0.5;
  const post = context.createGain();
  const restore = context.createGain();
  restore.gain.value = 2;
  const meter = context.createAnalyser();
  meter.fftSize = 2048;
  input.connect(pre).connect(soft).connect(restore);
  restore.connect(meter);
  restore.connect(post);
  post.gain.value = muted ? 0 : 1;
  post.connect(context.destination);
  return { context, input, meter };
}
