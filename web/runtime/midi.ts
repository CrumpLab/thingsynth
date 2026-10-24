// Web MIDI: every input feeds the engine. Resolves to false when unavailable.

export interface MidiSink {
  midi(type: number, ch: number, d1: number, d2: number, bend: number): void;
  noteOn(note: number, vel: number): void;
  noteOff(note: number): void;
}

export async function connectWebMidi(sink: MidiSink, onChange: (inputs: number) => void): Promise<boolean> {
  if (typeof navigator === 'undefined' || !('requestMIDIAccess' in navigator)) return false;
  let access: MIDIAccess;
  try {
    access = await navigator.requestMIDIAccess({ sysex: false });
  } catch {
    return false;
  }
  const handler = (ev: MIDIMessageEvent): void => {
    const d = ev.data;
    if (!d || d.length === 0) return;
    const status = d[0] ?? 0;
    const ch = status & 0x0f;
    const d1 = d[1] ?? 0;
    const d2 = d[2] ?? 0;
    switch (status & 0xf0) {
      case 0x90:
        if (d2 > 0) sink.noteOn(d1, d2);
        else sink.noteOff(d1);
        break;
      case 0x80:
        sink.noteOff(d1);
        break;
      case 0xb0:
        if (d1 === 123 || d1 === 120) sink.midi(6, ch, 0, 0, 0);
        else sink.midi(2, ch, d1, d2, 0);
        break;
      case 0xe0:
        sink.midi(3, ch, d1, d2, ((d2 << 7) | d1) - 8192);
        break;
      case 0xd0:
        sink.midi(4, ch, d1, 0, 0);
        break;
      case 0xa0:
        sink.midi(5, ch, d1, d2, 0);
        break;
    }
  };
  const attach = (): void => {
    let n = 0;
    access.inputs.forEach((input) => {
      input.onmidimessage = handler;
      if (input.state === 'connected') n++;
    });
    onChange(n);
  };
  attach();
  access.onstatechange = attach;
  return true;
}
