// A short synthesized drum-ish loop for feeding effects when no microphone is wanted. No sample files.

export function renderDrumLoop(ctx: BaseAudioContext, bpm = 108, bars = 2): AudioBuffer {
  const sr = ctx.sampleRate;
  const beat = 60 / bpm;
  const length = Math.floor(bars * 4 * beat * sr);
  const buf = ctx.createBuffer(2, length, sr);
  const L = buf.getChannelData(0);
  const R = buf.getChannelData(1);
  let seed = 12345;
  const rnd = (): number => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296 - 0.5;
  };
  const add = (t0: number, gen: (t: number) => number, dur: number, pan = 0): void => {
    const s0 = Math.floor(t0 * sr);
    const n = Math.floor(dur * sr);
    const gl = Math.SQRT1_2 * (1 - pan * 0.7);
    const gr = Math.SQRT1_2 * (1 + pan * 0.7);
    for (let i = 0; i < n && s0 + i < length; i++) {
      const v = gen(i / sr);
      L[s0 + i] = (L[s0 + i] ?? 0) + v * gl;
      R[s0 + i] = (R[s0 + i] ?? 0) + v * gr;
    }
  };
  const kick = (t: number): number => {
    const f = 42 + 110 * Math.exp(-t * 28);
    return Math.sin(2 * Math.PI * f * t + 0.5) * Math.exp(-t * 9) * 0.9;
  };
  const snare = (t: number): number => {
    const tone = Math.sin(2 * Math.PI * 190 * t) * Math.exp(-t * 22) * 0.4;
    return (tone + rnd() * 1.2 * Math.exp(-t * 16)) * 0.6;
  };
  const hat = (t: number): number => rnd() * Math.exp(-t * 90) * 0.35;
  const openHat = (t: number): number => rnd() * Math.exp(-t * 14) * 0.25;
  const clave = (t: number): number => Math.sin(2 * Math.PI * 1800 * t) * Math.exp(-t * 60) * 0.35;

  for (let bar = 0; bar < bars; bar++) {
    const b0 = bar * 4 * beat;
    add(b0, kick, 0.5);
    add(b0 + 2 * beat, kick, 0.5);
    add(b0 + 2.75 * beat, kick, 0.4);
    add(b0 + beat, snare, 0.35);
    add(b0 + 3 * beat, snare, 0.35);
    for (let e = 0; e < 8; e++) add(b0 + e * beat * 0.5, e === 6 ? openHat : hat, 0.2, 0.4);
    if (bar % 2 === 1) add(b0 + 3.5 * beat, clave, 0.12, -0.5);
  }
  return buf;
}
