# Upstream: SynthLand

thingsynth plays Tonewheel, a plugin from SynthLand (https://github.com/CrumpLabSandbox/SynthLandExplorer).
The files below are copies, not symlinks, so this repo builds on its own. SynthLand stays the source of truth;
never edit the copies here, change them upstream and re-run the sync.

- Repository: https://github.com/CrumpLabSandbox/SynthLandExplorer
- Commit: `4f74aaf22f4755d06a171b8546bf6db9a933f68d` (2026-10-23)
- Synced: 2026-10-23

## What is copied, and where

| Upstream (SynthLandExplorer) | Here | Why |
| --- | --- | --- |
| `web/public/wasm/additive.wasm`, `additive.js` | `web/public/wasm/` | The additive engine (Tonewheel's core) built for the browser. The worklet instantiates the `.wasm` directly; the `.js` glue is kept for reference. Upstream these are build outputs (`pnpm -C web wasm`, needs emcc) and git-ignored; here they are committed. |
| `web/packages/runtime/src/*.ts` | `web/runtime/` | The web runtime: `host.ts` (AudioWorklet host, presets, parameters), `worklet.ts` (the processor), `midi.ts` (Web MIDI), `keyboard.ts` (computer keyboard), `loop.ts`, `bridge.ts`, `messages.ts`, `types.ts`, `index.ts`. Verbatim. `web/packages/ui` is not needed: the runtime does not import it. |
| `plugins/tonewheel/gen/plugin.json` | `web/public/tonewheel/plugin.json` | The generated plugin description (manifest merged with the engine's parameter table) the runtime loads. Upstream it is codegen output (`python3 tools/codegen/codegen.py`). |
| `plugins/tonewheel/presets/*.json` | `web/public/tonewheel/presets/` | All 110 presets plus `bank.json` (order) and `anchors.json`. `index.json` is rebuilt here by `scripts/build_preset_index.mjs`, the same way SynthLand's `web/scripts/sync-assets.mjs` does it. |
| `plugins/tonewheel/manifest.json` | `upstream/tonewheel/manifest.json` | Reference: which engine parameters Tonewheel hides, its macros, preset categories, skin theme. |
| `engines/additive/params.json` | `upstream/additive/params.json` | Reference: the engine's full parameter table (261 entries) with descriptions. |

Not copied: `engines/additive/gen/Params.h` and `plugins/tonewheel/gen/PluginParams.h` (C++ only, the runtime
does not load them), the Tonewheel skin (thingsynth replaces it with the painting), `@synthland/ui`.

## Re-syncing

```bash
scripts/sync_upstream.sh /path/to/SynthLandExplorer
```

The script copies everything in the table, rebuilds `presets/index.json`, and rewrites the commit line above.
Then `pnpm typecheck && pnpm build`, check `git diff`, and commit with the new upstream commit in the message.
If the runtime's `HostOptions` or the worklet message protocol changed upstream, `web/src/main.ts` may need
the matching change; `scripts/build_worklet.mjs` mirrors upstream's `packages/runtime/build.mjs`.
