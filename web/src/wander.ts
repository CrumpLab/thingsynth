// Wander: every visible Tonewheel parameter takes its own random walk around the current preset, so the painting
// keeps moving while you play.
//
//   float and int parameters  a mean-reverting walk (Ornstein-Uhlenbeck) in the parameter's 0..1 range, pulled back
//                             towards its centre; ints (drawbars) step when the walk crosses a whole number
//   bool and choice           now and then switch to another setting, and tend to come back to the centre's
//
// speed (0..1) sets the time scale, from a 40 s drift to a 1 s flutter; amount (0..1) sets how far the walks
// stray (up to 0.4 of each range, as a standard deviation) and how often switches flip. The centre is the preset's
// value; loading a preset re-centres every walk, and setting a parameter yourself (dragging its object, MIDI)
// re-centres that one on your value. Stopping returns every parameter to its centre.
import type { ParamDesc, WebSynthlandHost } from '../runtime/types';

/** Held: changes which keys play which manual, not the sound. */
const HELD = new Set(['voice.manuals']);
/** Gentler: loudness and pitch should drift, not jump. */
const DEPTH: Record<string, number> = { 'out.level': 0.25, 'tg.master': 0.15 };
/** A 16 s drift, drawbars straying about one step, a switch flipping every few seconds: lively without glitching. */
const DEFAULT_SPEED = 0.25, DEFAULT_AMOUNT = 0.25;
const TICK_MS = 100;
const MAX_SD = 0.4;

interface Walk {
  p: ParamDesc;
  /** centre and position, 0..1 in the parameter's range (choices and bools: index) */
  centre: number;
  x: number;
  depth: number;
}

export interface Wander {
  start(): void;
  stop(): void;
  running(): boolean;
  /** 0..1 */
  speed(): number;
  setSpeed(v: number): void;
  /** 0..1 */
  amount(): number;
  setAmount(v: number): void;
  onChange(cb: (running: boolean) => void): () => void;
}

function gauss(): number {
  let u = 0;
  while (u === 0) u = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * Math.random());
}

export function createWander(host: WebSynthlandHost, opts: { speed?: number; amount?: number } = {}): Wander {
  let speed = opts.speed ?? DEFAULT_SPEED;
  let amount = opts.amount ?? DEFAULT_AMOUNT;
  let timer = 0;
  let last = 0;
  let writing = false;
  /** Set when someone other than wander changes a parameter after the last preset load. */
  let touched = false;
  const listeners = new Set<(running: boolean) => void>();

  const walks: Walk[] = host.params()
    .filter((p) => !p.hidden && !HELD.has(p.id))
    .map((p) => ({ p, centre: 0, x: 0, depth: DEPTH[p.id] ?? 1 }));
  const discrete = (p: ParamDesc): boolean => p.type === 'bool' || p.type === 'choice';
  const norm = (p: ParamDesc, v: number): number => (p.max === p.min ? 0 : (v - p.min) / (p.max - p.min));
  const real = (p: ParamDesc, x: number): number => p.min + x * (p.max - p.min);
  const recentre = (w: Walk): void => {
    const v = host.get(w.p.id);
    w.centre = discrete(w.p) ? Math.round(v) : norm(w.p, v);
    w.x = w.centre;
  };
  for (const w of walks) recentre(w);

  /** Seconds: 40 s at speed 0, 1 s at speed 1, geometric in between (about 6 s at the middle). */
  const tau = (): number => Math.pow(40, 1 - speed);

  const set = (w: Walk, v: number): void => {
    writing = true;
    try { host.set(w.p.id, v); } finally { writing = false; }
  };

  const tick = (): void => {
    const now = performance.now();
    const dt = Math.min(2, (now - last) / 1000); // seconds; a throttled tab takes a bigger step, not a jump
    last = now;
    if (dt <= 0) return;
    const t = tau();
    const decay = Math.exp(-dt / t);
    for (const w of walks) {
      const { p } = w;
      if (discrete(p)) {
        const n = p.type === 'bool' ? 2 : (p.choices?.length ?? Math.round(p.max - p.min) + 1);
        if (n < 2) continue;
        const cur = Math.round(w.x);
        if (cur !== w.centre && Math.random() < dt / t) w.x = w.centre; // drift home
        else if (Math.random() < (amount * w.depth * dt) / (2 * t)) {
          let next = Math.floor(Math.random() * (n - 1));
          if (next >= cur - p.min) next += 1;
          w.x = p.min + next;
        } else continue;
        set(w, w.x);
        continue;
      }
      // Ornstein-Uhlenbeck step, exact for any dt; reflect at the ends of the range.
      const sd = MAX_SD * amount * w.depth;
      let x = w.centre + (w.x - w.centre) * decay + sd * Math.sqrt(1 - decay * decay) * gauss();
      if (x < 0) x = -x;
      if (x > 1) x = 2 - x;
      w.x = Math.max(0, Math.min(1, x));
      const v = real(p, w.x);
      if (p.type === 'int') { if (Math.round(v) !== Math.round(host.get(p.id))) set(w, Math.round(v)); }
      else set(w, v);
    }
  };

  // Re-centre: on preset loads (index >= 0; -1 is "edited"), and per parameter when someone else sets it.
  host.onPreset((i) => {
    if (i < 0) return;
    touched = false;
    for (const w of walks) recentre(w);
  });
  host.onParam((id) => {
    if (writing) return;
    const w = walks.find((k) => k.p.id === id);
    if (!w) return;
    recentre(w);
    touched = true;
  });

  const emit = (): void => { for (const cb of listeners) cb(timer !== 0); };
  const api: Wander = {
    start: () => {
      if (timer) return;
      for (const w of walks) recentre(w);
      last = performance.now();
      timer = window.setInterval(tick, TICK_MS);
      emit();
    },
    stop: () => {
      if (!timer) return;
      window.clearInterval(timer);
      timer = 0;
      // Untouched since a preset load: reload it, which also clears the "edited" mark. Otherwise return each
      // parameter to its centre, keeping the user's own changes.
      const preset = host.audio.lastPreset();
      if (!touched && preset >= 0) host.loadPreset(preset);
      else for (const w of walks) {
        w.x = w.centre;
        set(w, discrete(w.p) ? w.centre : real(w.p, w.centre));
      }
      emit();
    },
    running: () => timer !== 0,
    speed: () => speed,
    setSpeed: (v) => { speed = Math.max(0, Math.min(1, v)); },
    amount: () => amount,
    setAmount: (v) => { amount = Math.max(0, Math.min(1, v)); },
    onChange: (cb) => { listeners.add(cb); return () => listeners.delete(cb); },
  };
  return api;
}
