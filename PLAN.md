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

A binding names either an `object` from objects.json or a single fill as `"part": "f006"`, and either a `param`
(with `range` and `curve`) or a `note`. Optional: `gesture`, `glide` (ms the picture takes to follow, default 150;
1500 makes a rotor spin up and brake), and for notes `release` (ms after note-off, default 300).

```jsonc
{ "id": "curl-rotor", "object": "spiral-curl", "param": "leslie.speed", "range": [0, 2], "curve": "linear",
  "gesture": "tap", "glide": 1500, "effects": [ { "effect": "spin" } ] }
{ "id": "note-64", "part": "f119", "note": 64, "gesture": "hold",          // hold: plays while pressed; tap: briefly
  "effects": [ { "effect": "glow", "amount": 1.3 }, { "effect": "hue", "amount": 0.25 }, { "effect": "boil", "amount": 0.6 } ] }
```

**Each binding is one animation of its object, from a first frame to a last frame, and the frame shown is a
function of the binding's value and nothing else.** A continuous parameter shows the frame at its position in
`range` through `curve` (0..1). A note, or an on/off parameter, plays from the first frame to the last when it
turns on and back when it turns off. Nothing moves on its own: between changes every object holds its frame, and
the only motion is the glide from one frame to the next when a value changes.

An animation is the binding's list of effects, all evaluated at the same frame t. Every effect takes `amount`
(its strength at the last frame), optional `parts` (a role or list of roles), and optionally `span`, the part of
the timeline it plays over (`[from, to]`, default `[0, 1]`), and `ease` (`linear`, `in`, `out`, `in-out`), so an
object can, say, fill over the first half of its timeline and glow over the second. At amount 1 and the end of its
span (`web/src/effects.ts`):

| effect | on | last frame | options |
| --- | --- | --- | --- |
| `glow` | fills | more vivid and more solid: OKLCH chroma +0.09; light colours deepen only as far as needed to hold it, mid and dark colours lift towards light; opacity 60% of the way to solid | |
| `hue` | fills | the hue turned 60 degrees (negative turns the other way) | |
| `fill` | fills | a vivid copy of the object fully revealed from an edge, one level across all its shapes, like a drawbar pulled out | `from`: bottom, top, left, right; `edge`: straight or wave (a hand-drawn surface that rolls as it moves); `turn` (degrees the colour turns as it advances), `toward` (a hue, OKLCH degrees, every shape's colour moves to) or `color` (an exact colour it moves to) |
| `scribble` | fills | pencil loops in the painting's own scribble style, all drawn in, clipped to the shape | `count` (default 14) |
| `grow` | object | new growth sprouts in the painting's idiom, everything a coloured shape with a black outline (no bare lines): tapered branches in the shape's own colour, outlined in its finer ink (11 px) and open at the base so they join without a seam, each ending in a spiral tendril or an eye-bud, with candy-coloured leaves; one branch per 1/count of the timeline, climbing the shape from its base on alternating sides; each draws itself out, then its leaves unfurl, then its tip appears; seeded, so a frame always shows the same drawing | `count` (default 8), `parts` (the shape it grows from) |
| `rays` | above fills | a sunburst: `count` outlined triangles fanning over the upper half from `at`, growing from the inner ring to full length; masked so the object and the `front` shapes stay in front | `at`, `size` [inner, long, short], `count`, `front` |
| `eye` | object | an almond eye on the object, opening from a slit to wide: white, outlined, blue iris, pupil, highlight; just above the object's own shapes, so things painted on it stay in front | `at`, `size` [half width, half height] |
| `flames` | above ink | outlined tongues with yellow cores at `spots`, each rising from its base from its own delay; masked (with an outline-wide margin) so the object and the `front` shapes stay in front | `spots` [{at, angle, size, delay}], `front` |
| `wind` | above ink | outlined crescent bands round `at`, each sweeping from `from` to `to` degrees and thickening from its own `start`, then `count` leaves and petals caught up in it | `at`, `bands` [{radius, from, to, width, color, start}], `count` |
| `swing` | parts | the parts (a limb) turn about the pivot `at` by `angle` degrees, as an outlined copy with their own ribs above the ink; the neighbouring shapes grow into the place they leave | `parts`, `at`, `angle` |
| `boing` | over ink | the eye springing out: an empty cup where it sat, the eye opening in place, then springing out to `to` on a coil with an overshoot, motion lines last | `at`, `to`, `size` [eye radius, cup rx, cup ry] |
| `vanish` | fills | the shapes and their own lines fade away (the froth giving way to bubbles) | |
| `sprites` | anywhere | a list of outlined shapes, each growing from its own point (both ways, or only x or y) over its own window of the span, optionally shrinking back out over a later window (`outStart`, `outEnd`) or revealed by a sweeping wedge instead of growing (`sweep` {from, to} degrees); `place` under the object, on it (clipped to it), over the ink, or around it (over the ink, masked so the object stays in front). Mockup scripts export their geometry straight into it | `items` [{d, fill, edge, at, start, end, grow}], `place` |
| `tint` | fills | the colour moves to `color` and the shape turns solid | `color` |
| `line` | ink | the linework from less of itself to more of itself: at the first frame thinner (4 px eroded from each side) and broken by gaps like an unfinished sketch, the object's own colour showing where lines thin; exactly as painted at the middle; at the last frame bolder (5 px) with a second hand-drawn pass of every stroke beside the first | |
| `boil` | ink | the outline redrawn, its lines bent up to 12 canvas px; a new drawing every 1/12 of the way, so dragging makes them writhe and holding keeps them still | |
| `swell` | object | 8% larger about its centre (negative shrinks) | |
| `lean` | object | leaning 10 degrees from its base (negative leans left) | |
| `spin` | object | turned 180 degrees about its centre | |
| `blink` | object | squashed shut towards its centre line, like an eye closing | |

"Object" effects move the object's fills together with the ink strokes enclosed by it (`ownInk`), leaving the
borders it shares with neighbours in place; restricted to roles (`parts`), they move those shapes about their own
centre or base with only the ink those shapes enclose (a bud swelling on a stalk). (`pulse` and `wobble` in older mappings are read as `swell` and
`lean`.)

Changes glide: 150 ms for a parameter (or the binding's `glide`), about 150 ms for a note to reach its last frame,
the binding's `release` (default 300 ms) to go back. A preset load reaches objects as a wave from the painting's
centre (up to 450 ms of delay at the corners) with 400 ms glides. Several bindings may touch the same fill or
stroke: hue turns and glows add up, boils take the largest depth, moves compose. The painting is redrawn only while
something is changing, at most 30 times a second (every change inside the art SVG re-rasterises the whole
painting). With the system's reduced-motion setting, frames are reached without gliding.

In the bind editor each effect row has its span and easing, and the **Frame** slider scrubs the selected binding's
animation from its first frame to its last without touching the organ, to see an animation while shaping it.
`node scripts/object_frames.mjs <binding-id> [url] --tag <name>` renders one binding's animation (with the dev
server running) into `docs/objects/<binding-id>/`: a strip of frames 0 to 1 and a loop from first frame to last and
back, for reviewing objects one at a time.

Objects reworked so far (`docs/objects/`, process in `docs/object-animation-pattern.md`): **pyramid-drive**, sunburst
and eye: rays grow out behind the pyramid (Drive 0 to 0.6), a big eye opens on its right face (0.25 to 0.8), small
flames rise on its slopes (0.55 to 1), and its faces warm throughout; chosen by Matt from five mocked-up end frames
(`scripts/pyramid_endframes.py`). **sleepy-creature** (rotor speed), whirlwind: wind bands sweep in round the sleepy
green creature and its eye opens by Slow; its little baguette arm swings up and leaves are caught up by Fast
(`scripts/curl_endframes.py`). The arm used to be note 51's shape; that note moved to f259. **pyramid-worm** (Expression), bell, crest and bands:
ripples spread from its hole, candy bands climb its body, its tuft blooms into a crest, and its head flares into a
trumpet with sound waves (`scripts/worm_endframes.py`, whose `export` writes the shapes into `mapping.json`). **stream** (upper vibrato),
bubble cloud and rainbow: the froth bubbles up, bubbles rise and gather into a cloud of bubbles and shrink away into
it, a candy rainbow sweeps out of it into the pool, and it rains (`scripts/stream_endframes.py`). **bottom-eye**
(percussion), boing: the sleepy eye opens and springs out on a coil from a grey cup (`scripts/eye_endframes.py`); note
103 moved off its iris to f087. **cloud** (wheel age), overgrown: spotted mushrooms and little flowers sprout one by one along
the big cloud's top edge (`scripts/cloud_endframes.py`, `export` writes them into `mapping.json`). **horned-ghost** (lower drawbar 6), waving twins: two
little copies of the ghost pop up beside it and it waves a big lime hand (`scripts/ghost_endframes.py`). **acorn-frog** (complex
tonewheels), graffiti eyeballs: its acorns turn into two big dripping spray-painted eyeballs (`scripts/frog_endframes.py`);
notes 57 and 60 moved off the acorns to the petals f216 and f217. **tunnel** (vibrato mode), rainbow rings and eyes:
each mode brings rings up out of the tunnel's depth, then two eyes open in the dark (`scripts/tunnel_endframes.py`).
**big-eye** (percussion harmonic), disco peacock: a peacock fan opens behind its head and its eye turns into a disco
ball (`scripts/bigeye_endframes.py`). **orange-sprite** (pedal sustain), three morphs: starfish, then butterfly, then
jellyfish (`scripts/sprite_endframes.py`).
**stalk-drawbar-16 and stalk-drawbar-513**, sap rising: a green sap with a wavy surface climbs each stalk with the
drawbar, turning a luminous light green (#9cf27c) towards the top; each bud on the stalk (roles `bud-1`..) swells
24% and glows just as the sap reaches its height; and the stalk grows (`grow`): one new branch per drawbar step,
climbing from the base on alternating sides, each drawing itself out, unfurling leaves and ending in a spiral
tendril or an eye-bud, so a fully pulled drawbar is a much busier, leafier plant. (A `line` version that thickened
the strokes was tried first and replaced: Matt wanted the drawing itself to grow.)

Fill ids (`f001`..) and ink ids (`i0001`..) come from the extractor and are stable as long as the PSD's drawing does
not change; `?debug`'s parts mode (backquote) shows the id of the shape under the pointer. The parts table also
records how much of each fill is visible (`visible`, `visibleArea`): shapes sit inside their ink lines, so almost
all are 98-99% visible; 10 of 312 are fully hidden and should not be bound.

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

## 5.1 Wander

While playing, only the notes change the picture; everything else moves when a preset changes. Wander
(`web/src/wander.ts`, the Wander button and its two dials) keeps the preset's 46 sound parameters moving so every
bound object stays alive:

- **floats and ints** (drive, drawbars, levels, times): an Ornstein-Uhlenbeck walk in the parameter's 0..1 range,
  pulled back towards the preset's value; ints step when the walk crosses a whole number. Exact for any time step,
  so a throttled tab takes bigger steps instead of stalling.
- **bools and choices** (percussion, vibrato, rotor speed): now and then switch to another setting and tend to come
  back to the preset's.
- **speed** sets the time scale geometrically, a 40 s drift at 0, about 6 s at the middle, 1 s at 1. **amount** sets
  the spread (a standard deviation of up to 0.4 of each range) and how often switches flip; at 0 nothing moves.
- **Held**: `voice.manuals` (it changes which keys play which manual, not the sound). **Gentler**: `out.level` at a
  quarter and `tg.master` at 0.15 of the amount (about ±1 Hz: a tape-like drift, not out of tune). Both lists are
  constants at the top of the file.
- Loading a preset re-centres every walk on it; setting a parameter yourself (dragging its object, MIDI) re-centres
  that walk on your value. Stopping reloads the preset if nothing was changed by hand (clearing the edited mark),
  otherwise returns each parameter to its centre, keeping your changes.

## 5.2 Shuffle

The **Shuffle** button deals the parameters onto other objects (`web/src/shuffle.ts`). It picks a seed and
writes it into the address (`?seed=4821`), so a shuffle can be shared and reopened; shift-click (or
`&notes=shuffle`) also re-deals the 88 notes over the same note shapes; the × next to it returns to the curated
mapping. Rules:

- Bindings with `"locked": true` stay (the pyramid keeps Drive). Every other parameter gets an object from the
  pool: every named object in objects.json not held by a locked binding (56 objects for 46 parameters, so 10 are
  left out of each deal). Same seed, same deal.
- The look follows the parameter: Drive still heats, a drawbar still fills, wherever it lands. What adapts is the
  shape: drags run along the new object's long side, fills rise from the bottom of tall objects and from the
  left of wide ones, and role-specific effects (`parts`) cover the whole new object.
- The handover is animated: old objects fade their effect out while the new ones fade in, over 1.2 s.

## 6. Authoring workflow (what Matt does to assign parameters)

The current mapping is a proposal (`docs/mapping-proposal.md` lists it: all 47 parameters on 47 named objects,
88 notes on single shapes, 9 spare objects). To change it:

1. `pnpm dev`, open `http://localhost:5173/?debug`, press **Bind…** in the HUD. Parts mode turns on.
2. Click a shape of the painting to select it, shift+click to add or remove shapes. The editor says which
   object the shapes belong to and shows what that object is bound to.
3. **Object**: keep the one it found, pick another, take *the selected shape on its own* (a `part` binding), or
   *new object from the selection*: give it a name (`lower-case-with-dashes`) and a few words of label.
4. **Bind to**: a parameter (the list shows where each one is now) or *a note…* with its MIDI number. The form
   fills in from the existing binding for that parameter or note, or from defaults by type (drawbars fill and
   drag up and down, switches glow and blink on tap, choices turn hue on tap, the rest glow on a sideways drag).
5. Adjust gesture (*display only* = no touch), range and curve, glide, label, locked, and the effects with their
   amounts and options.
6. **Preview** applies it live without saving. **Save** writes `objects.json` and `mapping.json` through the dev
   server; the page reloads with the editor still open on the same shapes. **Remove binding** unbinds the
   parameter or note. **Copy JSON** puts the binding on the clipboard (Save does that too when there is no dev
   server, on a built site).
7. Afterwards: `python3 -I tools/mapping_report.py` refreshes `docs/mapping-proposal.md`.

Saving replaces the binding for the same parameter (or the same note), so a parameter is never bound twice; the
editor does not stop two bindings sharing an object, which is allowed (effects add up). It edits the curated
mapping whatever shuffle is showing.

Hand-drawn regions (v1) still work for anything that is not a shape of the painting: in `?debug`, shift+click
around it, Enter prints a `regions` entry for `mapping.json`.

From the console in debug mode, `thingsynth.params()` lists the ids with ranges and units,
`thingsynth.set('amp.drive', 0.5)` / `thingsynth.get(id)` poke the engine, `thingsynth.shuffle(seed, notes)`
deals, and `thingsynth.host` is the full runtime host.

Tools for starting over with a different painting: `tools/extract_psd.py` (layers and parts),
`tools/propose_objects.py` (which shapes are details of which, from how they enclose each other across the ink:
a starting point for naming objects).

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
own something visible. Milestones 1 to 4 are done: the painting is drawn from its PSD layers, nine effects
show the bound values, wander keeps the parameters moving (5.1), all 47 parameters and 88 notes are bound in a
proposal (`docs/mapping-proposal.md`) that the bind editor changes (section 6), and shuffle re-deals it (5.2).
Milestone 5 (polish) is done too: boil redraws lines, scribbles match the painting's own, phones get lighter
layers and a lite mode, the output has a safety knee, and `docs/demo/thingsynth-demo.mp4` shows it all with
sound. What is left is Matt's: reviewing the names and pairings in `docs/mapping-proposal.md`.
