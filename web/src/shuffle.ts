// Shuffle: deal the parameters onto other objects of the painting, reproducibly from a seed.
//
// Locked bindings stay where they are. Every other parameter binding is dealt an object from the pool (every named
// object in objects.json not held by a locked binding), by a seeded Fisher-Yates shuffle, so a seed is shareable.
// The look follows the parameter: drive still heats, a drawbar still fills; what adapts to the new object is its
// shape: drags run along the object's long side and fills rise from the bottom of tall objects and from the left of
// wide ones. Roles named in effects (`parts`) belong to the old object, so on a new one the effect covers all of
// it. With `notes`, the 88 notes are also re-dealt over the same 88 note parts.
import type { Binding, EffectSpec, Gesture, NoteBinding, ParamBinding } from './mapping';
import type { ArtObject } from './objects';

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffled<T>(items: T[], rand: () => number): T[] {
  const a = items.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j]!, a[i]!];
  }
  return a;
}

const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
export const noteName = (n: number): string => `${NOTE_NAMES[n % 12]}${Math.floor(n / 12) - 1}`;

export interface ShuffleOptions {
  /** Also re-deal the notes over the note parts. */
  notes: boolean;
  /** A parameter's display name, for the new labels. */
  paramName: (id: string) => string;
}

export function shuffleBindings(curated: Binding[], objects: Map<string, ArtObject>, seed: number, opts: ShuffleOptions): Binding[] {
  const rand = mulberry32(seed);
  const params = curated.filter((b): b is ParamBinding => b.kind === 'param');
  const notes = curated.filter((b): b is NoteBinding => b.kind === 'note');
  const held = new Set(params.filter((b) => b.locked).map((b) => b.object));
  const pool = shuffled(Array.from(objects.values()).filter((o) => !o.id.startsWith('#') && !held.has(o.id)), rand);

  let next = 0;
  const dealt: Binding[] = params.map((b) => {
    if (b.locked) return b;
    const obj = pool[next++ % Math.max(1, pool.length)];
    if (!obj) return b;
    const [, , w, h] = obj.bbox;
    const tall = h > w * 1.15;
    const effects: EffectSpec[] = b.effects.map((e) => {
      const { parts: _parts, ...rest } = e;
      return rest.effect === 'fill' ? { ...rest, from: tall ? 'bottom' : 'left' } : rest;
    });
    let gesture: Gesture | undefined = b.gesture;
    if (gesture === 'drag-x' || gesture === 'drag-y') gesture = tall ? 'drag-y' : 'drag-x';
    const out: ParamBinding = { ...b, object: obj.id, effects, label: `${obj.label ?? obj.id}: ${opts.paramName(b.param)} (shuffled)` };
    if (gesture) out.gesture = gesture; else delete out.gesture;
    return out;
  });

  let noteBindings: Binding[] = notes;
  if (opts.notes && notes.length > 1) {
    const numbers = shuffled(notes.map((n) => n.note), rand);
    noteBindings = notes.map((n, i) => {
      const note = numbers[i]!;
      return { ...n, id: `note-${note}`, note, label: `${noteName(note)}: hold to play (shuffled)` };
    });
  }
  return [...dealt, ...noteBindings];
}
