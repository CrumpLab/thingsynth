// Web bridge.js: assigns window.synthland for a skin served by the web runtime.
// Built as an IIFE so skins can load it with a plain <script src="./bridge.js">.
//
// Inside the viewer's tabletop the skin is loaded as index.html?slot=<key> in a same-origin iframe; the parent page
// has already created the host for that slot (it owns the shared AudioContext and the audio graph), so the skin
// adopts window.parent.SYNTHLAND_SLOTS[key] instead of creating its own. Everything else is unchanged.
import { createSynthlandHost } from './host';
import type { SynthlandHost } from './types';

function slotHost(): SynthlandHost | null {
  const slot = new URLSearchParams(window.location.search).get('slot');
  if (slot === null || window.parent === window) return null;
  try {
    const host = window.parent.SYNTHLAND_SLOTS?.[slot];
    if (host) return host;
  } catch {
    /* cross-origin parent: not the tabletop */
  }
  console.warn(`[synthland] no host for slot ${slot} in the parent page; creating one`);
  return null;
}

if (!window.synthland) {
  window.synthland = slotHost() ?? createSynthlandHost();
}
