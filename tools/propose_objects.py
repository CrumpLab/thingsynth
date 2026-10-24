# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "pillow>=10", "resvg-py>=0.1"]
# ///
"""Propose objects (named groups of fills) and their structure from the exported layers.

    uv run tools/propose_objects.py art/<slug> > proposal.json

Reads art/<slug>/layers/{fills.svg,ink.svg,parts.json}. Renders every fill in an id-encoded colour with the ink on
top at half scale, then for each fill looks across its ink outline: the share of the surrounding pixels that
belong to each neighbouring fill. A fill mostly surrounded (>= 70%) by one larger fill is a *detail* of it (an eye
in a face, a stripe on a horn); a fill with no such parent is a *top-level* shape. Very large shapes (the sky, the
ground) never adopt details. Writes JSON to stdout:

  { "fills": { "f012": { "parent": "f010" | null, "neighbours": { "f013": 0.42, ... }, "kind": "detail" | "top" |
                "background" | "hidden" } },
    "objects": [ { "root": "f010", "details": ["f012", ...], "pixelArea": ..., "bbox": [...] } ] }

The output is a starting point: objects.json is written by hand (or with the bind editor) from it.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import resvg_py
from PIL import Image
from scipy import ndimage as ndi

ENCLOSED = 0.70
BACKGROUND_AREA = 300_000  # canvas px^2: larger shapes do not adopt details
REACH = 24  # px at half scale: far enough to cross an ink line (~20 px wide here)


def main() -> int:
    art = Path(sys.argv[1])
    L = art / "layers"
    parts = json.loads((L / "parts.json").read_text())
    fills = {f["id"]: f for f in parts["fills"]}
    fsvg = (L / "fills.svg").read_text()
    isvg = (L / "ink.svg").read_text()
    order = re.findall(r'<path id="(f\d+)"[^>]* d="([^"]*)"', fsvg)
    canvas = parts["canvas"][0]
    S = canvas // 2
    body = "".join(f'<path fill="#{i + 1:06x}" d="{d}"/>' for i, (_, d) in enumerate(order))
    ink = "".join(f'<path d="{d}"/>' for d in re.findall(r' d="([^"]*)"', isvg))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas} {canvas}" width="{S}" height="{S}" '
           f'shape-rendering="crispEdges"><rect width="{canvas}" height="{canvas}" fill="#000"/>{body}'
           f'<g fill="#000">{ink}</g></svg>')
    px = np.asarray(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert("RGB")).astype(np.int64)
    idmap = (px[..., 0] << 16) | (px[..., 1] << 8) | px[..., 2]
    ids = [fid for fid, _ in order]
    disk = ndi.generate_binary_structure(2, 1)

    info: dict[str, dict] = {}
    for k, fid in enumerate(ids):
        f = fills[fid]
        if f.get("visible", 1) < 0.05:
            info[fid] = {"parent": None, "neighbours": {}, "kind": "hidden"}
            continue
        x, y, w, h = (v / 2 for v in f["bbox"])
        x0, y0 = max(0, int(x) - REACH - 2), max(0, int(y) - REACH - 2)
        x1, y1 = min(S, int(x + w) + REACH + 2), min(S, int(y + h) + REACH + 2)
        crop = idmap[y0:y1, x0:x1]
        mask = crop == k + 1
        if not mask.any():
            info[fid] = {"parent": None, "neighbours": {}, "kind": "hidden"}
            continue
        far = ndi.binary_dilation(mask, structure=disk, iterations=REACH)
        near = ndi.binary_dilation(mask, structure=disk, iterations=3)
        ring = far & ~near
        around = crop[ring]
        around = around[(around > 0) & (around != k + 1)]
        total = int(around.size)  # shape pixels only: the ring mostly crosses ink, which says nothing
        if total == 0:
            info[fid] = {"parent": None, "neighbours": {}, "kind": "top"}
            continue
        counts = np.bincount(around, minlength=len(ids) + 1) if around.size else np.zeros(len(ids) + 1, dtype=np.int64)
        nb = {ids[j - 1]: round(int(c) / total, 3) for j, c in enumerate(counts) if j > 0 and c > 0 and int(c) / total >= 0.05}
        info[fid] = {"parent": None, "neighbours": dict(sorted(nb.items(), key=lambda kv: -kv[1])), "kind": "top"}

    def big(fid: str) -> bool:
        return fills[fid].get("pixelArea", fills[fid]["area"]) >= BACKGROUND_AREA

    for fid, d in info.items():
        if d["kind"] == "hidden":
            continue
        if big(fid):
            d["kind"] = "background"
            continue
        for nb, share in d["neighbours"].items():
            if share >= ENCLOSED and fills[nb].get("pixelArea", 0) > fills[fid].get("pixelArea", 0) and not big(nb):
                d["parent"] = nb
                d["kind"] = "detail"
            break

    def root(fid: str) -> str:
        seen = set()
        while info[fid]["parent"] and fid not in seen:
            seen.add(fid)
            fid = info[fid]["parent"]
        return fid

    groups: dict[str, list[str]] = {}
    for fid, d in info.items():
        if d["kind"] in ("hidden", "background"):
            continue
        groups.setdefault(root(fid), []).append(fid)
    objects = []
    for r, members in groups.items():
        details = [m for m in members if m != r]
        x0 = min(fills[m]["bbox"][0] for m in members); y0 = min(fills[m]["bbox"][1] for m in members)
        x1 = max(fills[m]["bbox"][0] + fills[m]["bbox"][2] for m in members)
        y1 = max(fills[m]["bbox"][1] + fills[m]["bbox"][3] for m in members)
        objects.append({"root": r, "details": details, "pixelArea": sum(fills[m].get("pixelArea", 0) for m in members),
                        "bbox": [round(x0), round(y0), round(x1 - x0), round(y1 - y0)]})
    objects.sort(key=lambda o: -o["pixelArea"])
    kinds = {}
    for d in info.values():
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    print(f"fills: {kinds}; objects: {len(objects)} (with details: {sum(1 for o in objects if o['details'])})", file=sys.stderr)
    json.dump({"fills": info, "objects": objects}, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
