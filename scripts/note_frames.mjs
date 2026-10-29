// Render many notes' animations from the app in one page load, for reviewing the 88 note animations:
//
//   node scripts/note_frames.mjs [url] [--notes 60,61,62] [--timing]
//
// Opens the app in a headless Chrome (your installed one, a throwaway profile), holds every other binding at its first
// frame, and for each note pins it at the hold times 0, 0.2, 1, 2, 3 and 4 s (frames 0 .. 1) and writes
// docs/objects/note-<n>/app-strip.png, cropped to the note's drawing at its last frame. --timing instead plays note 60
// for real (noteOn, wait, noteOff) and prints the frame shown at each moment, to check the steady hold pace.
// Needs the dev server running (pnpm dev) and ffmpeg.
import puppeteer from 'puppeteer-core';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (name, d) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args.splice(i, 2)[1] : d; };
const timing = args.includes('--timing');
if (timing) args.splice(args.indexOf('--timing'), 1);
const only = opt('notes', null);
const [base = 'http://localhost:5179/'] = args;
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const tmp = mkdtempSync(join(tmpdir(), 'thingsynth-notes-'));
const S = 1600;
const HOLD_S = [0, 0.2, 1, 2, 3, 4];

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, userDataDir: join(tmp, 'profile'),
  defaultViewport: { width: S, height: S + 36, deviceScaleFactor: 1 },
  args: ['--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'],
});
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error' && !m.text().startsWith('Failed to load resource')) errors.push(m.text()); });
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
  if (timing) {
    const out = await page.evaluate(async () => {
      const T = window.thingsynth;
      const sh = () => T.effects.shown().find((x) => x.id === 'note-60')?.value ?? NaN;
      const rows = [];
      const t0 = performance.now();
      T.host.noteOn(60, 100);
      for (const ms of [200, 1000, 2000, 3000, 4500]) {
        await new Promise((r) => setTimeout(r, ms - (performance.now() - t0)));
        rows.push([`${ms} ms held`, sh().toFixed(3)]);
      }
      T.host.noteOff(60);
      await new Promise((r) => setTimeout(r, 400));
      rows.push(['400 ms after release', sh().toFixed(3)]);
      return rows;
    });
    for (const [a, b] of out) console.log(`${a.padEnd(22)} frame ${b}`);
  } else {
    await page.evaluate(() => { const T = window.thingsynth; for (const b of T.mapping.bindings) T.effects.pin(b.id, 0); });
    const ids = await page.evaluate(() => window.thingsynth.mapping.bindings.filter((b) => b.kind === 'note').map((b) => b.id));
    const want = only ? only.split(',').map((n) => `note-${n.trim()}`) : ids;
    const settle = () => page.evaluate(async () => {
      const E = window.thingsynth.effects;
      const t0 = Date.now();
      await new Promise((r) => setTimeout(r, 80));
      while (E.moving() && Date.now() - t0 < 10000) await new Promise((r) => setTimeout(r, 40));
    });
    for (const id of want) {
      // the crop: the note's shape and everything its last frame draws
      await page.evaluate((bid) => window.thingsynth.effects.pin(bid, 1), id);
      await settle();
      const box = await page.evaluate((bid) => {
        const T = window.thingsynth;
        const b = T.mapping.bindings.find((x) => x.id === bid);
        const fid = b.object.slice(1);
        const els = [document.getElementById(fid)];
        for (const g of document.querySelectorAll('#ts-over path, [mask] path, g path[transform]')) {
          if (g.style.visibility === 'visible' && g.getBoundingClientRect().width > 0) els.push(g);
        }
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (const p of els) { const r = p.getBoundingClientRect(); if (!r.width) continue; x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); }
        const side = Math.max(x1 - x0, y1 - y0, 160) * 1.25;
        const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
        const x = Math.max(0, cx - side / 2), y = Math.max(0, cy - side / 2);
        return { x, y, width: Math.min(side, innerWidth - x), height: Math.min(side, innerHeight - y) };
      }, id);
      const files = [];
      for (const [k, s] of HOLD_S.entries()) {
        await page.evaluate((bid, v) => window.thingsynth.effects.pin(bid, v), id, s / 4);
        await settle();
        const f = join(tmp, `${id}-${k}.png`);
        await page.screenshot({ path: f, clip: box });
        files.push(f);
      }
      await page.evaluate((bid) => window.thingsynth.effects.pin(bid, 0), id);
      await settle();
      const dir = join(ROOT, 'docs', 'objects', id);
      mkdirSync(dir, { recursive: true });
      const W = 300;
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...files.flatMap((f) => ['-i', f]), '-filter_complex',
        `${files.map((_, k) => `[${k}:v]scale=${W}:${W},pad=iw+8:ih+8:4:4:white[v${k}]`).join(';')};${files.map((_, k) => `[v${k}]`).join('')}hstack=inputs=${files.length}`,
        join(dir, 'app-strip.png')]);
      console.log('wrote', join(dir, 'app-strip.png'));
    }
    await page.evaluate(() => { const T = window.thingsynth; for (const b of T.mapping.bindings) T.effects.pin(b.id, null); });
  }
  if (errors.length) { console.error('page errors:'); for (const e of errors.slice(0, 20)) console.error('  ', e); process.exitCode = 1; }
} finally {
  await browser.close();
  rmSync(tmp, { recursive: true, force: true });
}
