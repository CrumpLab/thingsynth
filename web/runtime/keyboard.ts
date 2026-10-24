// Computer keyboard as a piano: A W S E D F T G Y H U J K, Z/X shift octave. Inactive while a text field is focused.

const KEYMAP: Record<string, number> = {
  KeyA: 0, KeyW: 1, KeyS: 2, KeyE: 3, KeyD: 4, KeyF: 5, KeyT: 6, KeyG: 7, KeyY: 8, KeyH: 9, KeyU: 10, KeyJ: 11,
  KeyK: 12, KeyO: 13, KeyL: 14, KeyP: 15, Semicolon: 16,
};

function textFieldFocused(): boolean {
  const el = document.activeElement as HTMLElement | null;
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
}

export function attachComputerKeyboard(
  target: Window,
  sink: { noteOn(n: number, v: number): void; noteOff(n: number): void },
  onOctave?: (base: number) => void,
): () => void {
  let base = 60;
  const held = new Map<string, number>();
  const down = (ev: KeyboardEvent): void => {
    if (ev.metaKey || ev.ctrlKey || ev.altKey || ev.repeat || textFieldFocused()) return;
    if (ev.code === 'KeyZ' || ev.code === 'KeyX') {
      base = Math.max(24, Math.min(96, base + (ev.code === 'KeyZ' ? -12 : 12)));
      onOctave?.(base);
      ev.preventDefault();
      return;
    }
    const off = KEYMAP[ev.code];
    if (off === undefined) return;
    const note = base + off;
    if (note > 127) return;
    held.set(ev.code, note);
    sink.noteOn(note, 100);
    ev.preventDefault();
  };
  const up = (ev: KeyboardEvent): void => {
    const note = held.get(ev.code);
    if (note === undefined) return;
    held.delete(ev.code);
    sink.noteOff(note);
  };
  const blur = (): void => {
    for (const note of held.values()) sink.noteOff(note);
    held.clear();
  };
  target.addEventListener('keydown', down);
  target.addEventListener('keyup', up);
  target.addEventListener('blur', blur);
  return () => {
    target.removeEventListener('keydown', down);
    target.removeEventListener('keyup', up);
    target.removeEventListener('blur', blur);
    blur();
  };
}
