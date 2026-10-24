// Bundle the AudioWorklet processor (web/runtime/worklet.ts) to web/public/runtime/worklet.js. The worklet runs in
// its own global scope, so Vite cannot serve it as part of the page bundle; esbuild does it as in SynthLand.
import { build } from 'esbuild';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
await build({
  entryPoints: [resolve(root, 'web/runtime/worklet.ts')],
  outfile: resolve(root, 'web/public/runtime/worklet.js'),
  bundle: true,
  format: 'esm',
  target: 'es2022',
  sourcemap: true,
  logLevel: 'info',
});
