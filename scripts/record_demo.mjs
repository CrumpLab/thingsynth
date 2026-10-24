// Record a demo video with sound: a headless Chrome (your installed one, a throwaway profile) plays a scripted
// performance on the painting while the page records its own organ output; ffmpeg muxes the two.
//
//   pnpm dev                                 (in another terminal; or pnpm build && pnpm preview)
//   node scripts/record_demo.mjs [url]       default http://localhost:5173/
//
// Writes docs/demo/thingsynth-demo.mp4 and docs/demo/poster.jpg. Needs ffmpeg on PATH and Google Chrome
// (CHROME=/path/to/chrome to use another). The page runs with ?debug for its controls (hidden for the video) and
// ?mute=1, so nothing plays through the speakers: the sound is taken from the page's output stage, before the mute.
import puppeteer from 'puppeteer-core';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASE = process.argv[2] ?? 'http://localhost:5173/';
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT = join(ROOT, 'docs', 'demo');
const W = 1000, H = 1036; // the painting square plus the bottom bar

const tmp = mkdtempSync(join(tmpdir(), 'thingsynth-demo-'));
mkdirSync(join(tmp, 'frames'));
mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  userDataDir: join(tmp, 'profile'),
  defaultViewport: { width: W, height: H, deviceScaleFactor: 1 },
  args: ['--autoplay-policy=no-user-gesture-required', '--hide-scrollbars', `--window-size=${W},${H}`],
});
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error('[page]', e.message));
  const url = new URL(BASE);
  url.searchParams.set('debug', '');
  url.searchParams.set('mute', '1');
  url.searchParams.set('preset', 'jazz-trio');
  url.searchParams.set('lite', '0');
  await page.goto(url.href, { waitUntil: 'load', timeout: 120_000 });
  await page.waitForFunction(() => window.thingsynth?.layer?.controls?.length > 40 && window.thingsynth?.wander && window.thingsynth?.effects, { timeout: 120_000 });

  // Presentation: no debug chrome on screen; start the organ; record its output.
  await page.evaluate(async () => {
    document.body.classList.remove('debug');
    const style = document.createElement('style');
    style.textContent = '.region-label, #hud, #start, #editor, #debug-link { display: none !important; }';
    document.head.append(style);
    for (const sel of ['#hud', '#start']) document.querySelector(sel).style.display = 'none';
    document.querySelectorAll('.region-label').forEach((e) => e.remove());
    const T = window.thingsynth;
    T.wander.setSpeed(0.55);
    T.wander.setAmount(0.7);
    await T.host.audio.start();
    // Record exactly what the speakers get: the page's output stage (web/src/output.ts), after its safety knee and
    // before ?mute. An AnalyserNode passes its input through, so its meter can feed the recorder.
    const dest = T.output.context.createMediaStreamDestination();
    T.output.meter.connect(dest);
    const rec = new MediaRecorder(dest.stream, { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 160_000 });
    window.__chunks = [];
    rec.ondataavailable = (e) => window.__chunks.push(e.data);
    window.__rec = rec;
  });
  await new Promise((r) => setTimeout(r, 1500)); // let the first paints settle

  const cdp = await page.createCDPSession();
  const frames = [];
  let n = 0;
  cdp.on('Page.screencastFrame', async (f) => {
    const file = join(tmp, 'frames', `${String(n++).padStart(5, '0')}.jpg`);
    writeFileSync(file, Buffer.from(f.data, 'base64'));
    frames.push({ t: f.metadata.timestamp, file });
    await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 90, maxWidth: W, maxHeight: H, everyNthFrame: 1 });
  const startedAt = await page.evaluate(() => { window.__rec.start(); return Date.now() / 1000; });
  console.log('recording...');

  // The performance, run inside the page for tight timing (about 44 s).
  await page.evaluate(async () => {
    const T = window.thingsynth, h = T.host;
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const hold = async (notes, ms, vel = 96) => { notes.forEach((x) => h.noteOn(x, vel)); await wait(ms); notes.forEach((x) => h.noteOff(x)); };
    const sweep = async (id, from, to, ms) => { const steps = Math.max(1, Math.round(ms / 50)); for (let i = 0; i <= steps; i++) { h.set(id, from + ((to - from) * i) / steps); await wait(50); } };
    // ii-V-I-VI in C, with a walking line underneath and a melody on top.
    const chords = [[50, 62, 65, 69, 72], [43, 59, 62, 65, 67], [48, 60, 64, 67, 71], [45, 61, 64, 67, 70]];
    const melody = [[74, 77, 76, 74], [71, 74, 72, 71], [72, 76, 79, 76], [73, 76, 79, 81]];
    const phrase = async (bars = 4, beat = 250) => {
      for (let b = 0; b < bars; b++) {
        const c = chords[b % 4], m = melody[b % 4];
        c.forEach((x) => h.noteOn(x, 88));
        for (const x of m) await hold([x], beat - 30, 104);
        c.forEach((x) => h.noteOff(x));
      }
    };
    await wait(800);                                           // the painting idles
    const drive = sweep('amp.drive', 0.15, 0.85, 4000);        // the pyramid heats while we play
    await phrase(4);
    await drive;
    await sweep('upper.db4', 0, 8, 1200);                      // drawbars fill the stalk forest
    await sweep('upper.db6', 0, 6, 900);
    T.wander.start();                                          // everything starts to drift
    await phrase(4);
    await phrase(4, 240);
    h.set('leslie.speed', 2);                                  // the curl spins up
    await phrase(4);
    h.loadPreset(T.host.presets().findIndex((p) => p.name === 'Rock Overdrive')); // a wave across the painting
    for (let i = 0; i < 6; i++) { await hold([36 + (i % 3) * 7, 48, 55, 60], 420, 110); await wait(80); }
    await T.shuffle(4821, true);                               // parameters and notes re-dealt
    await phrase(4, 230);
    h.set('leslie.speed', 1);
    T.wander.stop();
    await hold([36, 48, 55, 60, 64, 67, 71, 74], 2200, 100);   // a last chord, then the release
    await wait(1800);
  });

  await page.evaluate(() => new Promise((r) => { window.__rec.onstop = r; window.__rec.stop(); }));
  const endedAt = Date.now() / 1000;
  await cdp.send('Page.stopScreencast');
  const audio = await page.evaluate(async () => {
    const buf = new Uint8Array(await new Blob(window.__chunks, { type: 'audio/webm' }).arrayBuffer());
    let s = '';
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
    return btoa(s);
  });
  writeFileSync(join(tmp, 'audio.webm'), Buffer.from(audio, 'base64'));

  // Frames arrive only when the page repaints: hold each until the next, from the moment recording started.
  const used = frames.filter((f) => f.t >= startedAt - 0.5);
  const lines = [];
  for (let i = 0; i < used.length; i++) {
    const t = Math.max(used[i].t, startedAt);
    const next = i + 1 < used.length ? Math.max(used[i + 1].t, startedAt) : endedAt;
    lines.push(`file '${used[i].file}'`, `duration ${Math.max(0.001, next - t).toFixed(4)}`);
  }
  lines.push(`file '${used.at(-1).file}'`);
  writeFileSync(join(tmp, 'frames.txt'), lines.join('\n'));
  const length = endedAt - startedAt;
  console.log(`${used.length} frames over ${length.toFixed(1)} s (${(used.length / length).toFixed(1)} fps captured)`);

  const mp4 = join(OUT, 'thingsynth-demo.mp4');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', join(tmp, 'frames.txt'), '-i', join(tmp, 'audio.webm'),
    '-vf', 'fps=30,scale=800:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p',
    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-shortest', '-movflags', '+faststart', mp4], { stdio: 'inherit' });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(Math.min(22, length - 2)), '-i', mp4, '-frames:v', '1', '-q:v', '3', join(OUT, 'poster.jpg')], { stdio: 'inherit' });
  console.log(`wrote ${mp4}`);
} finally {
  await browser.close();
  if (process.env.KEEP) console.log(`kept ${tmp}`); else rmSync(tmp, { recursive: true, force: true });
}
