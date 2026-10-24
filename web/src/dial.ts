// A small rotary dial, plain DOM + SVG: drag up/down (shift for fine), scroll, arrow keys, Home/End; double-click
// resets. Values are 0..1. Exposed to assistive tech as a slider.
const SVG = 'http://www.w3.org/2000/svg';
const START = -135, SWEEP = 270; // degrees, 0 = up

function arc(r: number, a0: number, a1: number): string {
  const p = (a: number): string => {
    const t = ((a - 90) * Math.PI) / 180;
    return `${(18 + r * Math.cos(t)).toFixed(2)} ${(18 + r * Math.sin(t)).toFixed(2)}`;
  };
  return `M${p(a0)}A${r} ${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${p(a1)}`;
}

export interface Dial {
  el: HTMLElement;
  value(): number;
  set(v: number): void;
}

export function createDial(opts: { label: string; title: string; value: number; reset: number; onInput: (v: number) => void }): Dial {
  let value = Math.max(0, Math.min(1, opts.value));
  const el = document.createElement('div');
  el.className = 'dial';
  el.tabIndex = 0;
  el.title = opts.title;
  el.setAttribute('role', 'slider');
  el.setAttribute('aria-label', opts.title);
  el.setAttribute('aria-valuemin', '0');
  el.setAttribute('aria-valuemax', '100');
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', '0 0 36 36');
  const track = document.createElementNS(SVG, 'path');
  track.setAttribute('class', 'track');
  track.setAttribute('d', arc(13, START, START + SWEEP));
  const fill = document.createElementNS(SVG, 'path');
  fill.setAttribute('class', 'fill');
  const tick = document.createElementNS(SVG, 'line');
  tick.setAttribute('class', 'tick');
  tick.setAttribute('x1', '18'); tick.setAttribute('y1', '18'); tick.setAttribute('x2', '18'); tick.setAttribute('y2', '8');
  svg.append(track, fill, tick);
  const cap = document.createElement('span');
  cap.textContent = opts.label;
  el.append(svg, cap);

  const draw = (): void => {
    const a = START + SWEEP * value;
    fill.setAttribute('d', value > 0.002 ? arc(13, START, a) : '');
    tick.setAttribute('transform', `rotate(${a} 18 18)`);
    el.setAttribute('aria-valuenow', String(Math.round(value * 100)));
    el.setAttribute('aria-valuetext', `${Math.round(value * 100)}%`);
  };
  const set = (v: number, notify: boolean): void => {
    const nv = Math.max(0, Math.min(1, v));
    if (nv === value) return;
    value = nv;
    draw();
    if (notify) opts.onInput(value);
  };

  el.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    ev.preventDefault();
    ev.stopPropagation(); // not a painting gesture
    el.setPointerCapture(ev.pointerId);
    el.focus();
    let y = ev.clientY;
    const move = (e: PointerEvent): void => {
      set(value + (y - e.clientY) / (e.shiftKey ? 600 : 150), true);
      y = e.clientY;
    };
    const up = (): void => {
      el.removeEventListener('pointermove', move);
      el.removeEventListener('pointerup', up);
      el.removeEventListener('pointercancel', up);
    };
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', up);
  });
  el.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    set(value - Math.sign(ev.deltaY) * 0.04, true);
  }, { passive: false });
  el.addEventListener('keydown', (ev) => {
    const step = ev.shiftKey ? 0.01 : 0.05;
    const d = { ArrowUp: step, ArrowRight: step, ArrowDown: -step, ArrowLeft: -step, PageUp: 0.2, PageDown: -0.2 }[ev.key];
    if (d !== undefined) set(value + d, true);
    else if (ev.key === 'Home') set(0, true);
    else if (ev.key === 'End') set(1, true);
    else return;
    ev.preventDefault();
    ev.stopPropagation(); // keep arrows away from anything else listening on the window
  });
  el.addEventListener('dblclick', () => set(opts.reset, true));
  draw();
  return { el, value: () => value, set: (v) => set(v, false) };
}
