// Build web/public/tonewheel/presets/index.json from the preset files, in bank.json order (as SynthLand's
// web/scripts/sync-assets.mjs does), so the runtime's loadPreset(index) sees the same list as SynthLand.
import { readdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'web', 'public', 'tonewheel', 'presets');
const presets = [];
for (const f of readdirSync(dir)) {
  if (!f.endsWith('.json') || f === 'bank.json' || f === 'index.json' || f === 'anchors.json') continue;
  const p = JSON.parse(readFileSync(join(dir, f), 'utf8'));
  if (p && p.schema === 'synthland.preset/1' && p.name && p.params) {
    presets.push({ slug: f.replace(/\.json$/, ''), name: p.name, category: p.category ?? 'Uncategorized',
      tags: p.tags ?? [], author: p.author, params: p.params, features: p.features });
  }
}
let order = null;
if (existsSync(join(dir, 'bank.json'))) order = JSON.parse(readFileSync(join(dir, 'bank.json'), 'utf8')).order ?? null;
if (Array.isArray(order)) {
  const rank = new Map(order.map((s, i) => [s, i]));
  presets.sort((a, b) => (rank.get(a.slug) ?? 1e9) - (rank.get(b.slug) ?? 1e9) || a.name.localeCompare(b.name));
} else presets.sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));
writeFileSync(join(dir, 'index.json'), JSON.stringify(presets));
console.log(`[presets] ${presets.length} presets -> ${join(dir, 'index.json')}`);
