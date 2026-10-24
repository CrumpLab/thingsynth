// Colour math for the effects: sRGB hex <-> OKLCH (perceptually even lightness, chroma and hue, so a hue turn
// or a chroma lift looks equally strong on every candy colour of the painting), with gamut mapping by chroma
// reduction so shifted colours stay displayable and keep their lightness.

export interface Oklch { l: number; c: number; h: number }

const toLinear = (u: number): number => (u <= 0.04045 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4));
const toGamma = (u: number): number => (u <= 0.0031308 ? 12.92 * u : 1.055 * Math.pow(u, 1 / 2.4) - 0.055);

export function hexToOklch(hex: string): Oklch {
  const n = parseInt(hex.replace('#', ''), 16);
  const r = toLinear(((n >> 16) & 255) / 255), g = toLinear(((n >> 8) & 255) / 255), b = toLinear((n & 255) / 255);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const L = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s;
  const A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s;
  const B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s;
  return { l: L, c: Math.hypot(A, B), h: ((Math.atan2(B, A) * 180) / Math.PI + 360) % 360 };
}

function oklchToLinear({ l, c, h }: Oklch): [number, number, number] {
  const a = c * Math.cos((h * Math.PI) / 180), b = c * Math.sin((h * Math.PI) / 180);
  const l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s_ = (l - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
    -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
    -0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_,
  ];
}

const inGamut = (rgb: [number, number, number]): boolean => rgb.every((v) => v >= -1e-4 && v <= 1 + 1e-4);

/**
 * To hex, gamut-mapped. Out-of-gamut colours first give up lightness (down to `maxDarken`), the way a painter
 * deepens a colour to make it more saturated, and only then chroma. Pastels near white have almost no room for
 * chroma at their own lightness, so trimming chroma alone would wash them out instead of making them vivid.
 */
export function oklchToHex(col: Oklch, maxDarken = 0): string {
  let c = col;
  if (!inGamut(oklchToLinear(c)) && maxDarken > 0) {
    // smallest darkening that fits, if any does within maxDarken
    if (inGamut(oklchToLinear({ ...c, l: c.l - maxDarken }))) {
      let lo = 0, hi = maxDarken;
      for (let i = 0; i < 16; i++) {
        const mid = (lo + hi) / 2;
        if (inGamut(oklchToLinear({ ...c, l: c.l - mid }))) hi = mid; else lo = mid;
      }
      c = { ...c, l: c.l - hi };
    } else c = { ...c, l: c.l - maxDarken };
  }
  if (!inGamut(oklchToLinear(c))) {
    let lo = 0, hi = c.c;
    for (let i = 0; i < 18; i++) {
      const mid = (lo + hi) / 2;
      if (inGamut(oklchToLinear({ ...c, c: mid }))) lo = mid; else hi = mid;
    }
    c = { ...c, c: lo };
  }
  const rgb = oklchToLinear(c).map((v) => Math.round(Math.min(1, Math.max(0, toGamma(Math.min(1, Math.max(0, v))))) * 255));
  return '#' + rgb.map((v) => v.toString(16).padStart(2, '0')).join('');
}
