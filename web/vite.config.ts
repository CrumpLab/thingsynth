import { defineConfig, type Plugin } from 'vite';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const here = fileURLToPath(new URL('.', import.meta.url));
const repo = fileURLToPath(new URL('..', import.meta.url));

/**
 * Dev-only write-back for the bind editor (?debug, Bind): POST /__thingsynth/save with
 * { "writes": [ { "file": "mapping" | "objects", "content": {...} }, ... ] } rewrites mapping.json and/or
 * art/<slug>/objects.json in one request (two requests could straddle the reload the first write causes).
 * Only those two files, only with the expected schema, and only with the X-Thingsynth header (a cross-site page
 * cannot send a custom header without a CORS preflight, which this server never approves). Not in builds.
 */
function editorWriteBack(): Plugin {
  const files: Record<string, { path: string; schema: string }> = {
    mapping: { path: resolve(repo, 'mapping.json'), schema: 'thingsynth.mapping/2' },
    objects: { path: resolve(repo, 'art/golden-pyramid-with-tunnel-celebration/objects.json'), schema: 'thingsynth.objects/1' },
  };
  return {
    name: 'thingsynth-editor-write-back',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__thingsynth/save', (req, res) => {
        const fail = (code: number, msg: string): void => { res.statusCode = code; res.end(msg); };
        if (req.method !== 'POST') return fail(405, 'POST only');
        if (req.headers['x-thingsynth'] !== '1') return fail(403, 'missing X-Thingsynth header');
        let body = '';
        req.setEncoding('utf8');
        req.on('data', (chunk: string) => { body += chunk; if (body.length > 2_000_000) req.destroy(); });
        req.on('end', () => {
          try {
            const { writes } = JSON.parse(body) as { writes?: Array<{ file?: string; content?: { schema?: string } }> };
            if (!Array.isArray(writes) || writes.length === 0) return fail(400, 'writes must be a non-empty array');
            const checked = writes.map(({ file, content }) => {
              const target = file ? files[file] : undefined;
              if (!target) throw new Error('file must be "mapping" or "objects"');
              if (!content || content.schema !== target.schema) throw new Error(`content.schema must be "${target.schema}"`);
              return { path: target.path, text: JSON.stringify(content, null, 2) + '\n' };
            });
            // Objects first: a mapping may name an object the same save creates.
            checked.sort((a, b) => Number(a.path.endsWith('mapping.json')) - Number(b.path.endsWith('mapping.json')));
            for (const w of checked) writeFileSync(w.path, w.text);
            res.setHeader('Content-Type', 'text/plain');
            res.end('saved');
          } catch (err) {
            fail(400, `bad request: ${err instanceof Error ? err.message : String(err)}`);
          }
        });
      });
    },
  };
}

export default defineConfig({
  root: here,
  base: './',
  publicDir: 'public',
  plugins: [editorWriteBack()],
  build: {
    outDir: fileURLToPath(new URL('../dist', import.meta.url)), emptyOutDir: true, target: 'es2022',
    rollupOptions: { input: { main: resolve(here, 'index.html'), about: resolve(here, 'about.html') } },
  },
  server: {
    headers: { 'Cache-Control': 'no-store' },
    // The painting (art/) and mapping.json live outside web/.
    fs: { allow: [repo] },
  },
});
