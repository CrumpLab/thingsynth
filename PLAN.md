# thingsynth: plan

*Written 2026-10-23. Status: pipeline wired end to end with placeholder regions; waiting for Matt's instructions
on which parts of the painting control which parameters.*

## 1. Goal

Make one painting, *Golden Pyramid With Tunnel Celebration* (Colorlands, digital, 2022, 2475 × 2475 px), an
interactive web page that is also a playable Tonewheel organ. The painting is the whole interface: there are no
knobs or drawbars drawn on top of it. Regions of the painted image (the pyramid, the tunnel, the stream, a
creature) respond to taps, drags, holds or hovers and set Tonewheel parameters. Notes come from the computer
keyboard or Web MIDI. Effectively, Tonewheel is reskinned with Matt's art.

Constraints: framework-free TypeScript in strict mode (SynthLand style); the SynthLand runtime and engine are
copied in verbatim and never edited here; the parameter mapping is data (`mapping.json`), not code, so the
authoring loop is "edit JSON, reload".

## 2. Architecture

```
  PSD ── tools/extract_psd.py ──► art/<slug>/layers/  (wash, fills.svg, scribbles, ink.svg, caption)
                                │
                                ▼
  <svg viewBox="0 0 4950 4950"> the painting rebuilt, static          web/src/art.ts
      white paper, then clipped to the painted area: wash image, 312 fill paths,
      scribble image, 1,630 ink paths; the caption strip below
  <svg viewBox="0 0 2475 2475"> hit layer, same box, on top           web/src/painting.ts
                                │  one <polygon> per region, pointer events,
                                │  screen -> image px via getScreenCTM()
                                ▼
  mapping.json ─────────► parse + validate, gesture -> value curve       web/src/mapping.ts
                                │  host.set(paramId, valueInRealUnits)
                                ▼
  SynthLand web runtime (copy) ─ createSynthlandHost()                  web/runtime/host.ts
      loads plugin.json + presets/index.json, Web MIDI, computer keyboard,
      prefetches additive.wasm, posts {param,i,v} / {midi,...} to the worklet
                                │
                                ▼
  AudioWorklet 'synthland-engine'                                        web/runtime/worklet.ts
      instantiates additive.wasm (sl_create / sl_set_param / sl_midi / sl_process)
      128-frame quanta, stereo out, meter + telemetry back to the host
                                │
                                ▼
  web/public/wasm/additive.wasm  (Tonewheel = the additive core in "Tonewheel" topology)
```

Key points:

- **Coordinates.** The SVG hit layer uses `viewBox="0 0 W H"` with `preserveAspectRatio="xMidYMid meet"` and
  the same box as the letterboxed image, so SVG user units *are* image pixels. Regions in `mapping.json` are
  written in image pixels and never converted; resizing the window changes nothing in the data.
- **Parameters are addressed by id in real units** (`amp.drive` 0..1, `tg.master` in Hz, drawbars 0..8, choices
  as index). The runtime clamps, rounds ints/choices, and maps choice subsets to engine indices; thingsynth only
  computes a value from the pointer position.
- **Audio starts on a user gesture.** The start overlay (or the runtime's own first-gesture hook) calls
  `host.audio.start()`; the preset chosen by `?preset=` or `mapping.defaultPreset` is loaded before that, so
  the first note already has the right registration.
- **Debug mode** (`?debug`) is a lazy-loaded module (`web/src/debug.ts`) so the normal page carries none of it.

## 3. The mapping schema (`mapping.json`)

```jsonc
{
  "schema": "thingsynth.mapping/1",
  "image": "art/golden-pyramid-with-tunnel-celebration/golden-pyramid-with-tunnel-celebration.jpg",
  "size": [2475, 2475],            // image pixels; regions are in this space
  "defaultPreset": "jazz-trio",    // optional: slug of the preset loaded at start
  "regions": [
    {
      "id": "pyramid",                               // optional, used in debug output
      "label": "The golden pyramid: drive",          // optional, tooltip and notes
      "region": { "rect": [x, y, w, h] },            // or { "polygon": [[x, y], [x, y], ...] } (3+ points)
      "gesture": "drag-x",                           // tap | drag-x | drag-y | hold | hover
      "param": "amp.drive",                          // a Tonewheel parameter id (section 4)
      "range": [0, 1],                               // in the parameter's real units; reverse to invert
      "curve": "linear",                             // linear | log (log needs a positive range)
      "step": 1                                      // optional, tap only: how far one tap moves
    }
  ]
}
```

Gesture semantics (implemented in `web/src/painting.ts` and `web/src/mapping.ts`):

| gesture | what happens | value |
| --- | --- | --- |
| `tap` | pointer down inside the region | steps from the current value by `step` (default 1 for int, bool and choice parameters; the whole range for floats, i.e. a toggle) and wraps from `range[1]` back to `range[0]` |
| `drag-x` | press and move; pointer is captured so the drag continues outside the region | horizontal position across the region's bounding box, 0 at the left edge, 1 at the right, through the curve into `range` |
| `drag-y` | same, vertical | 1 at the top edge, 0 at the bottom (up = more) |
| `hold` | press and release | `range[1]` while held, `range[0]` on release (momentary) |
| `hover` | pointer moves over the region without pressing (ignored for touch) | like `drag-x` |

Curves: `linear` is `a + (b - a) * t`; `log` is `a * (b / a) ^ t` (use it for Hz and ms ranges). The same
parameter may appear in several regions; the last gesture wins. A region naming a parameter Tonewheel does not
have is reported in the console and otherwise ignored. Regions are drawn in file order; a later region on top
receives the pointer events where they overlap.

### 3.1 v2: objects and bindings

`"schema": "thingsynth.mapping/2"` keeps `regions` (as above) and adds `bindings`. A binding binds an
**object**, a named group of the painting's own fill shapes from `art/<slug>/objects.json`, to a parameter.
The parameter's value is drawn on the object, and an optional gesture makes the object itself the control (its
hit area is its own outline, not a rectangle).

```jsonc
// art/<slug>/objects.json
{ "schema": "thingsynth.objects/1", "canvas": [4950, 4950],
  "objects": {
    "golden-pyramid": { "label": "The golden pyramid, both faces",
                        "parts": { "face-left": ["f135"], "face-right": ["f136"] },   // role -> fill ids
                        "ink": "auto" } } }      // "auto": every stroke that runs along one of its fills

// mapping.json
{ "schema": "thingsynth.mapping/2", "image": "...", "size": [2475, 2475],
  "bindings": [
    { "id": "pyramid-drive", "object": "golden-pyramid", "param": "amp.drive", "range": [0, 1], "curve": "linear",
      "gesture": "drag-x",                         // optional; tap | drag-x | drag-y | hold | hover
      "effects": [ { "effect": "hue", "amount": -0.3 },             // optional "parts": role or [roles]
                   { "effect": "glow", "amount": 1 },
                   { "effect": "boil", "amount": 1 } ] } ],
  "regions": [ ... ] }
```

The value drawn is the parameter's position in `range` through `curve` (0..1), so a drag, a preset or MIDI all
move the picture. Effects (`web/src/effects.ts`), at amount 1 and value 1:

| effect | on | what it does |
| --- | --- | --- |
| `glow` | fills | OKLCH chroma +0.09, deepened by up to 0.18 lightness only as far as needed to hold that chroma (pastels near white have no room for it otherwise), opacity 60% of the way to solid |
| `hue` | fills | turns the hue by 60 degrees (negative amounts turn the other way) |
| `boil` | ink | every outline stroke jitters by up to 10 canvas px and 0.6 degrees about its centre, re-drawn 8 times a second; still at 0 |

Values glide (150 ms, 400 ms after a preset load). Several bindings may touch the same fill or stroke: hue turns
and glows add up, boils take the largest. Fill ids (`f001`..) and ink ids (`i0001`..) come from the extractor
and are stable as long as the PSD's drawing does not change; `?debug`'s parts mode (backquote) shows the id of
the shape under the pointer.

Possible later additions (not implemented): `"params": [...]`
to fan one gesture out to several parameters, `"relative": true` for drags that nudge from the current value
instead of setting an absolute position, `"note"` regions that play a pitch instead of setting a parameter,
and a `"transition"` (ms) for smoothing taps.

## 4. Tonewheel parameters

Tonewheel exposes 47 of the additive engine's 261 parameters; the rest are hidden by the manifest (fixed per
plugin: topology, Leslie physics, the partial tables of the "Partials" topology, envelopes and filters that the
organ does not use). Any id below works in `mapping.json`. Values are real units; choices and bools are set by
index (0, 1, ...). Source: `web/public/tonewheel/plugin.json` (generated upstream from
`upstream/tonewheel/manifest.json` + `upstream/additive/params.json`).

The eight **macros** the manifest puts first, and therefore the most natural candidates for the biggest
regions: `leslie.speed`, `amp.drive`, `upper.db1`, `upper.db2`, `upper.db3`, `upper.db4`, `perc.on`, `vib.mode`.

| id | name | group | type | range | default | unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `voice.manuals` | Manual Mode | Voice | choice | 0 Channels / 1 Split / 2 Upper | Channels |  | Channels: upper on MIDI ch 1 (and ch 4..16), lower ch 2, pedals ch 3. Split: one keyboard, keys below Split Point play the lower manual. Upper: every channel plays the upper manual. |
| `voice.split` | Split Point | Voice | int | 36 .. 72 | 60 |  | Lowest MIDI note of the upper manual in Split mode. |
| `voice.pedal_split` | Pedal Split | Voice | choice | 0 Off / 1 C1 / 2 D1 / 3 E1 / 4 F1 / 5 G1 / 6 A1 / 7 B1 / 8 C2 / 9 D2 / 10 E2 / 11 F2 / 12 G2 / 13 A2 / 14 B2 / 15 C3 | Off |  | Split mode: keys below this note play the pedals (monophonic, lowest note wins). C4 = MIDI 60. |
| `tg.tuning` | Tuning | Generator | choice | 0 Gear / 1 Equal | Gear |  | Gear: 20 rev/s x teeth x gear ratio (the generator's own small errors). Equal: 12-TET. |
| `tg.master` | Master Tune | Generator | float | 430 .. 450 | 440 | Hz |  |
| `tg.complex` | Complex Wheels | Generator | bool | 0 off / 1 on | on |  | Wheels 1..12 carry odd harmonics (near square), as the low wheels do. |
| `tg.leakage` | Leakage | Generator | float | -90 .. -30 | -60 | dB | Every wheel faintly present while any key is held. |
| `tg.crosstalk` | Crosstalk | Generator | float | -80 .. -20 | -40 | dB | Same-shaft wheel four octaves away and neighbouring wheels added to every keyed wheel. |
| `tg.age` | Wheel Age | Generator | float | 0 .. 1 | 0.3 |  | Random per-wheel level spread, 0 to 3 dB (seeded). |
| `tg.click` | Key Click | Generator | float | 0 .. 1 | 0.5 |  | Contact stagger and bounce depth on key down; 0 = clickless. |
| `tg.click_release` | Release Click | Generator | float | 0 .. 1 | 0.25 |  | Same on key up. |
| `upper.db1` | Upper 16' | Upper | int | 0 .. 8 | 8 |  |  |
| `upper.db2` | Upper 5 1/3' | Upper | int | 0 .. 8 | 8 |  |  |
| `upper.db3` | Upper 8' | Upper | int | 0 .. 8 | 8 |  |  |
| `upper.db4` | Upper 4' | Upper | int | 0 .. 8 | 0 |  |  |
| `upper.db5` | Upper 2 2/3' | Upper | int | 0 .. 8 | 0 |  |  |
| `upper.db6` | Upper 2' | Upper | int | 0 .. 8 | 0 |  |  |
| `upper.db7` | Upper 1 3/5' | Upper | int | 0 .. 8 | 0 |  |  |
| `upper.db8` | Upper 1 1/3' | Upper | int | 0 .. 8 | 0 |  |  |
| `upper.db9` | Upper 1' | Upper | int | 0 .. 8 | 0 |  |  |
| `lower.db1` | Lower 16' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db2` | Lower 5 1/3' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db3` | Lower 8' | Lower | int | 0 .. 8 | 8 |  |  |
| `lower.db4` | Lower 4' | Lower | int | 0 .. 8 | 8 |  |  |
| `lower.db5` | Lower 2 2/3' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db6` | Lower 2' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db7` | Lower 1 3/5' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db8` | Lower 1 1/3' | Lower | int | 0 .. 8 | 0 |  |  |
| `lower.db9` | Lower 1' | Lower | int | 0 .. 8 | 0 |  |  |
| `pedal.db16` | Pedal 16' | Pedal | int | 0 .. 8 | 6 |  |  |
| `pedal.db8` | Pedal 8' | Pedal | int | 0 .. 8 | 3 |  |  |
| `pedal.sustain` | Pedal Sustain | Pedal | float | 0 .. 2000 | 0 | ms | skew 0.4; Release time of the pedals (later consoles); 0 = B3 behaviour. |
| `perc.on` | Percussion | Percussion | bool | 0 off / 1 on | off |  | Upper manual only. Steals the 1' drawbar. |
| `perc.harmonic` | Perc Harmonic | Percussion | choice | 0 Second / 1 Third | Third |  | Second = 4' wheel, Third = 2 2/3' wheel of each keyed note. |
| `perc.decay` | Perc Decay | Percussion | choice | 0 Slow / 1 Fast | Fast |  |  |
| `perc.volume` | Perc Volume | Percussion | choice | 0 Normal / 1 Soft | Normal |  | Normal: full percussion and the upper drawbars drop 4.4 dB. Soft: percussion 6 dB lower, drawbars unchanged. |
| `vib.mode` | Vibrato | Vibrato | choice | 0 V1 / 1 V2 / 2 V3 / 3 C1 / 4 C2 / 5 C3 | C3 |  | Scanner vibrato depth (V) or vibrato mixed with dry (C, chorus). |
| `vib.upper` | Vibrato Upper | Vibrato | bool | 0 off / 1 on | off |  |  |
| `vib.lower` | Vibrato Lower | Vibrato | bool | 0 off / 1 on | off |  |  |
| `amp.expression` | Expression | Amp | float | 0 .. 1 | 1 |  | Swell pedal; MIDI CC 11 scales it further. |
| `amp.drive` | Drive | Amp | float | 0 .. 1 | 0.15 |  | Tube preamp and speaker amp overdrive. |
| `leslie.on` | Leslie | Leslie | bool | 0 off / 1 on | on |  | Off: the dry preamp signal on both channels. |
| `leslie.speed` | Rotor Speed | Leslie | choice | 0 Stop / 1 Slow / 2 Fast | Slow |  | Target speed; the rotors accelerate and brake with inertia. Mod wheel above half = Fast. |
| `leslie.balance` | Horn/Drum | Leslie | float | -12 .. 12 | 0 | dB |  |
| `leslie.mic_distance` | Mic Distance | Leslie | float | 20 .. 150 | 42 | cm |  |
| `leslie.mic_angle` | Mic Spread | Leslie | float | 0 .. 180 | 120 | deg |  |
| `out.level` | Volume | Output | float | -30 .. 12 | -8 | dB |  |

Hidden parameters can still be set through `host.set()` if a mapping ever wants them (for example
`leslie.horn_fast` or `vib.rate`); they are listed with descriptions in `upstream/additive/params.json`.
Setting them is off-manifest and not covered by presets, so prefer the 47 above.

## 5. Presets

- The 110 Tonewheel presets are copied as files into `web/public/tonewheel/presets/` and indexed by
  `scripts/build_preset_index.mjs` into `index.json` in the bank order (`bank.json`), exactly as SynthLand's
  viewer does, so `loadPreset(index)` means the same thing in both places.
- A preset is loaded whole by the runtime (`host.loadPreset`); unlisted parameters go back to their defaults.
  Loading a preset also moves every mapped region's value (the debug HUD shows it); a gesture afterwards marks
  the preset edited (`Jazz Trio *`).
- The page picks the preset from `?preset=<slug>`, else `mapping.defaultPreset`, else the first in the bank.
  The bottom bar's select switches presets at any time. Nothing is saved: reload returns to the default.
- Open: whether thingsynth should ship with one curated registration (a single preset baked into
  `mapping.json`) and hide the preset select, or keep the whole bank. The mapping can also set drawbars
  directly, so a region could *be* a registration (a `tap` through a set of drawbar values is the "params" fan-out
  in section 3's later additions).

## 6. Authoring workflow (what Matt does to assign parameters)

1. `pnpm dev`, open `http://localhost:5173/?debug`.
2. Hover: the HUD's first line shows the pointer in image pixels. Click anywhere: the console prints
   `click at image px [x, y]` (and the region hit, if any).
3. Draw a region: shift+click around the painted thing (3+ points, any shape). Backspace removes the last
   point, Escape clears. Press Enter: the console prints a complete `mapping.json` entry for that polygon and
   copies it to the clipboard. For a rectangle, two clicks give you `[x, y, w, h]` by hand.
4. Paste the entry into `mapping.json` under `regions`, set `id`, `label`, `gesture`, `param` (section 4),
   `range` and `curve`. Vite reloads the page on save; the new region appears outlined in debug mode with its
   label, and its fill brightens with the parameter's value.
5. Try it: drag or tap the region while holding a key; the HUD table shows the parameter's live value.
6. Repeat. When the painting is fully mapped, drop `?debug`; the plain page shows no outlines, only the
   bottom bar (preset, status, a `debug` link). The status line prints the last parameter change so the
   mapping is still discoverable without the overlay.

From the console in debug mode, `thingsynth.params()` lists the ids with ranges and units,
`thingsynth.set('amp.drive', 0.5)` / `thingsynth.get(id)` poke the engine, and `thingsynth.host` is the
full runtime host (`docs/skin-bridge.md` upstream describes it).

Mapping instructions can arrive in any form (a list of "the pyramid is drive, left to right", or a sketch);
the conversion to coordinates is step 3 and takes about a minute per region.

## 7. Repo and sync

`UPSTREAM.md` records the SynthLand commit the copies came from and `scripts/sync_upstream.sh` re-copies them.
The additive engine's `.wasm` is committed here (upstream it is a build output), so the repo builds with only
Node and pnpm. `pnpm build` typechecks the app, the runtime copy and the worklet copy, then builds `dist/`
(a static site, about 12 MB uncompressed, about 6.4 MB over the wire with gzip on the two SVGs; the scribble
layer, 3 MB of WebP, is the largest piece). Nothing is deployed yet.

## 8. Open questions

- **Which regions, which parameters.** Waiting for Matt. Until then `mapping.json` holds three placeholders
  (drive, the Upper 16' drawbar, rotor speed) in arbitrary rectangles.
- **Discoverability on the plain page.** With no outlines, how does a visitor find the live regions? Options:
  a brief hint on hover (cursor already changes), a one-time "glow" of all regions after start, or nothing
  (the piece is a seek-and-find painting; finding the sounds could be the point).
- **Notes from the painting.** Should some regions play notes (a creature per pitch, a keyboard along the
  stream) in addition to the computer keyboard and MIDI? That is the `note` region type in section 3.
- **Touch.** Hover is pointer-only; on phones, `hold` and `drag` work, `hover` does nothing. Fine for now.
- **Presets vs. one registration.** Section 5.
- **Deploy.** Not done on purpose. When wanted: it is a static `dist/`, so Coolify + nginx like the other
  instances, or GitHub Pages. `base: './'` in the Vite config keeps it subpath-friendly.
- **Image size.** The 2475 px JPEG is 0.6 MB; fine. If regions need to be authored more precisely than the
  JPEG shows, ask Matt for the original.
- **Runtime drift.** The runtime is a copy; if SynthLand changes the worklet ABI or `HostOptions`, re-sync and
  fix `web/src/main.ts`. A thin `@synthland/runtime` npm package upstream would make this a dependency instead.

## 9. Next: the animation layer

[docs/animation-layer-plan.md](docs/animation-layer-plan.md) (approved 2026-10-24) rebuilds the painting from
the PSD's vector layers and animates its own fill shapes and ink strokes so the 47 parameters and 88 notes each
own something visible. Milestones 1 and 2 are done: `tools/extract_psd.py` exports the layers into
`art/<slug>/layers/`, the page draws the painting from them, `?debug` has a parts mode for picking shapes, and
mapping.json v2 binds the golden pyramid to Drive with glow, hue and boil (section 3.1). Next is milestone 3,
the rest of the effect vocabulary and the note parts.
