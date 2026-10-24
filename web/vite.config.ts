import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));
const repo = fileURLToPath(new URL('..', import.meta.url));

export default defineConfig({
  root: here,
  base: './',
  publicDir: 'public',
  build: { outDir: fileURLToPath(new URL('../dist', import.meta.url)), emptyOutDir: true, target: 'es2022' },
  server: {
    headers: { 'Cache-Control': 'no-store' },
    // The painting (art/) and mapping.json live outside web/.
    fs: { allow: [repo] },
  },
});
