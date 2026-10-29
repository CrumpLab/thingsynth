// Shuffle: deal the controls onto other animations of the painting, reproducibly from a seed.
//
// Every animation now belongs to its object: the drawing is made for that shape, in its place. So a shuffle keeps
// each object with its own animation and deals the controls over them instead, across everything: the 47 parameters
// and the 88 notes are shuffled together over all 135 animated objects, so a note can land on the sand dune and a
// drawbar on a tiny bud. Every animation runs from frame 0 to frame 1, so any control can drive any of them: a
// parameter shows its position in its range, a held note plays through over its hold time.
//
// Locked bindings stay as they are, control and animation together. What adapts to the new object is the gesture:
// drags run along the object's long side; a note is held wherever it lands; a parameter with no gesture (shown, not
// touched) stays that way. A switch keeps a glide so its animation plays through (its own, else the animation's, else
// 800 ms); a continuous parameter keeps its own glide, so dragging stays direct.
import type { Binding, EffectSpec, Gesture, NoteBinding, ParamBinding } from './mapping';
import { resolveObject, type ArtObject } from './objects';

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

const SWITCH_GLIDE_MS = 800;

export interface ShuffleOptions {
  /** A parameter's display name, for the new labels. */
  paramName: (id: string) => string;
}

/** An animation: an object of the painting and the effects drawn for it. */
interface Animation { object: string; effects: EffectSpec[]; glide?: number; name: string }

/** What the object is called, for labels: objects.json's label for a named object; for a single shape (a note's),
 * the curated label up to its first colon. */
function nameOf(b: Binding, obj: ArtObject | undefined): string {
  if (!b.object.startsWith('#') && obj?.label) return obj.label;
  const head = b.label?.split(':')[0]?.trim();
  return head && !/^[A-G]#?-?\d$/.test(head) ? head : obj?.label ?? b.object;
}

export function shuffleBindings(curated: Binding[], objects: Map<string, ArtObject>, seed: number, opts: ShuffleOptions): Binding[] {
  const rand = mulberry32(seed);
  const free = curated.filter((b) => !(b.kind === 'param' && b.locked));
  const animations: Animation[] = shuffled(free.map((b) => {
    const a: Animation = { object: b.object, effects: b.effects, name: nameOf(b, resolveObject(objects, b.object)) };
    if (b.glide !== undefined) a.glide = b.glide;
    return a;
  }), rand);

  const dealt = new Map<Binding, Binding>();
  free.forEach((control, i) => {
    const anim = animations[i]!;
    const obj = resolveObject(objects, anim.object);
    const tall = obj ? obj.bbox[3] > obj.bbox[2] * 1.15 : true;
    if (control.kind === 'note') {
      const out: NoteBinding = {
        kind: 'note', id: control.id, object: anim.object, effects: anim.effects, note: control.note,
        release: control.release, hold: control.hold, gesture: control.gesture ?? 'hold',
        label: `${anim.name}: hold ${noteName(control.note)} to play (shuffled)`,
      };
      dealt.set(control, out);
      return;
    }
    let gesture: Gesture | undefined = control.gesture;
    if (gesture === 'drag-x' || gesture === 'drag-y') gesture = tall ? 'drag-y' : 'drag-x';
    const { glide: _glide, gesture: _gesture, locked: _locked, ...rest } = control;
    const out: ParamBinding = { ...rest, object: anim.object, effects: anim.effects, label: `${anim.name}: ${opts.paramName(control.param)} (shuffled)` };
    if (gesture) out.gesture = gesture;
    const isSwitch = gesture === 'tap' || gesture === undefined;
    const glide = isSwitch ? control.glide ?? anim.glide ?? SWITCH_GLIDE_MS : control.glide;
    if (glide !== undefined) out.glide = glide;
    dealt.set(control, out);
  });
  return curated.map((b) => dealt.get(b) ?? b);
}
