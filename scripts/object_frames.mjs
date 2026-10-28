// Render one binding's animation, first frame to last, for reviewing an object's animation:
//
//   node scripts/object_frames.mjs <binding-id> [url] [--out dir] [--frames 5] [--tag name] [--context]
//
// Opens the app in a headless Chrome (your installed one, a throwaway profile), holds the binding at each frame with
// the editor's pin (the organ is not touched), and writes into docs/objects/<binding-id>/ (or --out). Every other
// binding is held at its first frame so only this one shows (--context leaves them at their current values):
//   <tag>-strip.png   frames 0, 0.25 .. 1 side by side, cropped to the object, frame values underneath
//   <tag>-sweep.gif   a loop from the first frame to the last and back
// --pad <share> widens the crop around the object (default 0.12); --crop x,y,w,h (canvas px) crops there instead, for big
// objects whose change lives in one part. Needs the dev server running (pnpm dev) and ffmpeg.
import puppeteer from 'puppeteer-core';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (name, d) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args.splice(i, 2)[1] : d; };
const context = args.includes('--context');
if (context) args.splice(args.indexOf('--context'), 1);
const outArg = opt('out', null), frames = Number(opt('frames', '5')), tag = opt('tag', 'current'), pad = Number(opt('pad', '0.12'));
const cropArg = opt('crop', null);
const [id, base = 'http://localhost:5173/'] = args;
if (!id) { console.error('usage: node scripts/object_frames.mjs <binding-id> [url] [--frames 5] [--tag name]'); process.exit(1); }
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT = outArg ? resolve(outArg) : join(ROOT, 'docs', 'objects', id);
mkdirSync(OUT, { recursive: true });
const tmp = mkdtempSync(join(tmpdir(), 'thingsynth-frames-'));
const S = 1600; // viewport: the painting large enough for detail

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, userDataDir: join(tmp, 'profile'),
  defaultViewport: { width: S, height: S + 36, deviceScaleFactor: 1 },
  args: ['--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'],
});
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error('[page]', e.message));
  const url = new URL(base);
  url.searchParams.set('debug', ''); url.searchParams.set('mute', '1'); url.searchParams.set('lite', '0');
  await page.goto(url.href, { waitUntil: 'load', timeout: 120_000 });
  await page.waitForFunction(() => window.thingsynth?.effects && window.thingsynth?.layer?.controls?.length > 0, { timeout: 120_000 });
  await page.evaluate(() => {
    document.body.classList.remove('debug');
    const style = document.createElement('style');
    style.textContent = '.region-label, #hud, #start, #editor, #bar, .hits { display: none !important; }';
    document.head.append(style);
  });
  if (!context) {
    await page.evaluate((bindingId) => {
      const T = window.thingsynth;
      for (const b of T.mapping.bindings) if (b.id !== bindingId) T.effects.pin(b.id, 0);
    }, id);
  }
  // the object's box on screen, from its fills
  const box = await page.evaluate(([bindingId, pad]) => {
    const T = window.thingsynth;
    const b = T.mapping.bindings.find((x) => x.id === bindingId);
    if (!b) throw new Error(`no binding ${bindingId}`);
    const ids = b.object.startsWith('#') ? [b.object.slice(1)] : T.objects.get(b.object).fills;
    const paths = ids.map((f) => document.getElementById(f)).filter(Boolean);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const p of paths) { const r = p.getBoundingClientRect(); x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); }
    const m = Math.max(x1 - x0, y1 - y0) * pad;
    return { x: Math.max(0, x0 - m), y: Math.max(0, y0 - m), width: x1 - x0 + 2 * m, height: y1 - y0 + 2 * m };
  }, [id, pad]);
  if (cropArg) {
    const [cx, cy, cw, ch] = cropArg.split(',').map(Number);
    Object.assign(box, await page.evaluate(([bindingId, c]) => {
      const T = window.thingsynth;
      const b = T.mapping.bindings.find((x) => x.id === bindingId);
      const fid = b.object.startsWith('#') ? b.object.slice(1) : T.objects.get(b.object).fills[0];
      const svg = document.getElementById(fid).ownerSVGElement;
      const m = svg.getScreenCTM();
      const pt = (x, y) => { const q = svg.createSVGPoint(); q.x = x; q.y = y; return q.matrixTransform(m); };
      const a = pt(c[0], c[1]), z = pt(c[0] + c[2], c[1] + c[3]);
      return { x: Math.max(0, a.x), y: Math.max(0, a.y), width: z.x - a.x, height: z.y - a.y };
    }, [id, [cx, cy, cw, ch]]));
  }
  const settle = () => page.evaluate(async () => {
    const E = window.thingsynth.effects;
    const t0 = Date.now();
    await new Promise((r) => setTimeout(r, 80));
    while (E.moving() && Date.now() - t0 < 10000) await new Promise((r) => setTimeout(r, 40));
  });
  // The frame's label is drawn by the page, inside the crop (this ffmpeg may lack drawtext).
  await page.evaluate((b) => {
    const tag = document.createElement('div');
    tag.id = 'frame-tag';
    Object.assign(tag.style, { position: 'fixed', left: `${b.x + 8}px`, top: `${b.y + 8}px`, zIndex: 99, padding: '3px 8px',
      font: '600 20px ui-monospace, Menlo, monospace', color: '#fff', background: 'rgba(0,0,0,0.6)', borderRadius: '4px' });
    document.body.append(tag);
  }, box);
  const shoot = async (f, file) => {
    await page.evaluate((bid, v) => { window.thingsynth.effects.pin(bid, v); document.getElementById('frame-tag').textContent = `frame ${v.toFixed(2)}`; }, id, f);
    await settle();
    await page.screenshot({ path: file, clip: box });
  };
  // strip
  const stripFiles = [];
  for (let k = 0; k < frames; k++) {
    const f = frames === 1 ? 1 : k / (frames - 1);
    const file = join(tmp, `s${k}.png`);
    await shoot(f, file);
    stripFiles.push({ f, file });
  }
  const W = 360;
  const inputs = stripFiles.flatMap((s) => ['-i', s.file]);
  const labels = stripFiles.map((s, k) => `[${k}:v]scale=${W}:-2,pad=iw+8:ih+8:4:4:white[v${k}]`).join(';');
  if (stripFiles.length === 1) execFileSync('cp', [stripFiles[0].file, join(OUT, `${tag}-strip.png`)]);
  else execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex',
    `${labels};${stripFiles.map((_, k) => `[v${k}]`).join('')}hstack=inputs=${stripFiles.length}`, join(OUT, `${tag}-strip.png`)]);
  // sweep: 0 -> 1 -> 0
  const n = 24, sweep = [];
  for (let k = 0; k <= n; k++) sweep.push(k / n);
  for (let k = n - 1; k > 0; k--) sweep.push(k / n);
  let i = 0;
  for (const f of sweep) await shoot(f, join(tmp, `w${String(i++).padStart(3, '0')}.png`));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '12', '-i', join(tmp, 'w%03d.png'), '-vf',
    'scale=480:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0', join(OUT, `${tag}-sweep.gif`)]);
  await page.evaluate((bid) => window.thingsynth.effects.pin(bid, null), id);
  writeFileSync(join(OUT, 'README.md'), `# ${id}\n\nRendered with \`node scripts/object_frames.mjs ${id}\`: \`*-strip.png\` shows frames 0 to 1, \`*-sweep.gif\` loops first to last frame and back.\n`);
  console.log(`wrote ${join(OUT, `${tag}-strip.png`)} and ${tag}-sweep.gif`);
} finally {
  await browser.close();
  rmSync(tmp, { recursive: true, force: true });
}
