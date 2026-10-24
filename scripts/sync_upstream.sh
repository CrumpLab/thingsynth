#!/usr/bin/env bash
# Re-copy the Tonewheel pieces thingsynth needs from a SynthLand checkout. Copies, never symlinks.
# Usage: scripts/sync_upstream.sh [path-to-SynthLandExplorer]
# Afterwards: review `git diff`, update UPSTREAM.md (this script rewrites the commit line), commit.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-${SYNTHLAND_DIR:-$HERE/../SynthLandExplorer}}"
[ -f "$SRC/plugins/tonewheel/manifest.json" ] || { echo "not a SynthLand checkout: $SRC" >&2; exit 1; }

# The browser build of the additive engine (worklet instantiates the .wasm; the .js glue is kept for reference).
for f in additive.wasm additive.js; do
  [ -f "$SRC/web/public/wasm/$f" ] || { echo "missing $SRC/web/public/wasm/$f (run pnpm -C web wasm upstream)" >&2; exit 1; }
  cp "$SRC/web/public/wasm/$f" "$HERE/web/public/wasm/$f"
done

# The web runtime (AudioWorklet host, Web MIDI, computer keyboard), source files verbatim.
rm -rf "$HERE/web/runtime"; mkdir -p "$HERE/web/runtime"
cp "$SRC"/web/packages/runtime/src/*.ts "$HERE/web/runtime/"

# Plugin manifest and engine parameter table (reference copies, see PLAN.md) and the generated plugin.json the
# runtime loads (upstream it is a codegen output: run `python3 tools/codegen/codegen.py` there if it is missing).
mkdir -p "$HERE/upstream/tonewheel" "$HERE/upstream/additive" "$HERE/web/public/tonewheel/presets"
cp "$SRC/plugins/tonewheel/manifest.json" "$HERE/upstream/tonewheel/manifest.json"
cp "$SRC/engines/additive/params.json" "$HERE/upstream/additive/params.json"
[ -f "$SRC/plugins/tonewheel/gen/plugin.json" ] || { echo "missing gen/plugin.json upstream: run python3 tools/codegen/codegen.py there" >&2; exit 1; }
cp "$SRC/plugins/tonewheel/gen/plugin.json" "$HERE/web/public/tonewheel/plugin.json"

# Presets: every preset file plus bank.json (the bank order); index.json is rebuilt from them.
rm -f "$HERE"/web/public/tonewheel/presets/*.json
cp "$SRC"/plugins/tonewheel/presets/*.json "$HERE/web/public/tonewheel/presets/"
node "$HERE/scripts/build_preset_index.mjs"

COMMIT="$(git -C "$SRC" rev-parse HEAD)"
DATE="$(git -C "$SRC" log -1 --format=%cs)"
sed -i '' -E "s|^- Commit: .*|- Commit: \`$COMMIT\` ($DATE)|" "$HERE/UPSTREAM.md" 2>/dev/null || true
echo "synced from $SRC @ $COMMIT"
