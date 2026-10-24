# thingsynth

One painting by Matt Crump, *Golden Pyramid With Tunnel Celebration* (Colorlands, 2022), as the interface to
[SynthLand](https://github.com/CrumpLabSandbox/SynthLandExplorer)'s **Tonewheel** organ. The painting fills the
browser window; regions of it, described in `mapping.json`, control Tonewheel parameters; the computer keyboard
and Web MIDI play notes. Everything runs in the browser (WebAssembly in an AudioWorklet).

See [PLAN.md](PLAN.md) for the architecture, the mapping schema and the parameter list.

## Run

Needs Node 22 and pnpm (`corepack enable` gives you the pinned pnpm).

```bash
pnpm install
pnpm dev
```

Open the printed URL (http://localhost:5173). Click or press a key to start audio.

- Notes: A W S E D F T G Y H U J K O L P ; on the computer keyboard, Z / X shift the octave. Any Web MIDI input
  plays too (Chrome, Edge; Safari needs Web MIDI enabled).
- Preset: the select in the bottom bar, or `?preset=<slug>` (slugs are the file names in
  `web/public/tonewheel/presets/`).
- `?debug` draws the mapped regions, shows pointer coordinates in image pixels and the mapped parameter values,
  logs image coordinates on every click, and has a small polygon editor (shift+click points, Enter prints a
  `mapping.json` entry). `?mute=1` keeps the engine running silently (for automated checks).

Other scripts: `pnpm build` (typecheck + production build into `dist/`), `pnpm preview`, `pnpm typecheck`,
`pnpm presets` (rebuild the preset index), `pnpm sync` (re-copy from SynthLand, see [UPSTREAM.md](UPSTREAM.md)).

## Layout

```
art/<slug>/             the painting (full resolution) and meta.json
mapping.json            regions of the painting -> Tonewheel parameters (the thing Matt edits)
web/                    Vite app, plain TypeScript, no framework
  src/main.ts           boots the runtime, presets, start overlay
  src/painting.ts       image + SVG hit layer in image-pixel coordinates, gesture handling
  src/mapping.ts        mapping.json schema, validation, value curves
  src/debug.ts          ?debug overlay, HUD and region editor
  runtime/              copy of SynthLand's web runtime (do not edit here)
  public/wasm/          additive.wasm (Tonewheel's engine)
  public/tonewheel/     plugin.json and presets
upstream/               reference copies of the Tonewheel manifest and engine params.json
scripts/                sync_upstream.sh, build_preset_index.mjs, build_worklet.mjs
```

## Licence

Code: GPLv3 (see [LICENSE](LICENSE)), the same licence as SynthLand, whose runtime and engine this repo copies.
The artwork in `art/` is copyright Matt Crump, all rights reserved; it is included here for this project only
and is not covered by the GPL.
