# /// script
# requires-python = ">=3.11"
# dependencies = ["psd-tools>=1.10", "pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Take the painting apart: read the Adobe Fresco PSD and write the layers thingsynth rebuilds it from.

    uv run tools/extract_psd.py "<path to .psd>" art/<slug> --reference art/<slug>/<image>.jpg [--scale 0.5]

Writes art/<slug>/layers/:
  layers.json     canvas size, painted area (the frame's hole), stack order, raster scale, source name and hash
                  (the PSD itself is not copied)
  wash.webp       the soft colour-wash pixel layer, on the full canvas, at --scale (default 0.5: 2475 px)
  scribbles.webp  the pencil-scribble pixel layer, same, with alpha
  *.small.webp    both again at half that size (1238 px), for phones, where the painting is ~1100 px across
  fills.svg       every coloured vector fill as <path id="fNNN" fill=... fill-opacity=...>, canvas coordinates
  ink.svg         every black vector ink shape as <path id="iNNNN">, canvas coordinates
  caption.webp    the white margin below the painted area with the hand-lettered title and signature, cropped
                  from --reference (the published image), because the PSD's own title and signature layers are
                  an older lettering
  parts.json      the fills and ink strokes with bbox, centroid, area, colour, and which ink overlaps each fill
  check.jpg       the rebuilt composite next to --reference, with the mean difference printed

The PSD's vector layers are Fresco exports: paths of absolute M/C/Z commands, ink stored as black-filled
outline shapes, fills as coloured shapes, each smart object placed at an integer offset on the canvas.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from psd_tools import PSDImage

NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")
PATH = re.compile(r"<path([^>]*)>")


def read_vector_layer(layer) -> tuple[list[dict], tuple[float, float, float, float]]:
    """Paths of a Fresco vector smart object and its placement (offset and scale from the transform box)."""
    svg = bytes(layer.smart_object.data).decode("utf-8")
    tb = layer.smart_object.transform_box  # x0 y0 x1 y0 x1 y1 x0 y1, unrotated in Fresco exports
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    sx = (tb[2] - tb[0]) / vb[2]
    sy = (tb[5] - tb[1]) / vb[3]
    place = (tb[0] - vb[0] * sx, tb[1] - vb[1] * sy, sx, sy)
    out = []
    for m in PATH.finditer(svg):
        attrs = m.group(1)
        d = re.search(r' d="([^"]*)"', attrs)
        fill = re.search(r"fill:(#[0-9A-Fa-f]{6}|none)", attrs)
        op = re.search(r"fill-opacity:([0-9.]+)", attrs)
        if not d or not fill:
            continue
        out.append({"d": d.group(1), "fill": fill.group(1).upper(), "opacity": float(op.group(1)) if op else 1.0})
    return out, place


def translate(d: str, place: tuple[float, float, float, float], decimals: int = 1) -> tuple[str, list[tuple[float, float]]]:
    """Place an absolute M/C/Z path onto the canvas; also return flattened canvas points for geometry."""
    ox, oy, sx, sy = place
    tokens = re.findall(r"[MCZmcz]|" + NUM.pattern, d)
    out: list[str] = []
    pts: list[tuple[float, float]] = []
    cmd = ""
    nums: list[float] = []
    cur = (0.0, 0.0)

    def flush() -> None:
        nonlocal cur
        if cmd == "M" and len(nums) >= 2:
            cur = (nums[0] * sx + ox, nums[1] * sy + oy)
            pts.append(cur)
            out.append("M" + fmt(nums))
        elif cmd == "C":
            for i in range(0, len(nums) - 5, 6):
                p0 = cur
                p1, p2, p3 = ((nums[i + k] * sx + ox, nums[i + k + 1] * sy + oy) for k in (0, 2, 4))
                for t in (0.25, 0.5, 0.75, 1.0):
                    u = 1 - t
                    pts.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
                cur = p3
            out.append("C" + fmt(nums))
        elif cmd == "Z":
            out.append("Z")

    def fmt(ns: list[float]) -> str:
        s = []
        for i, n in enumerate(ns):
            v = round(n * sx + ox if i % 2 == 0 else n * sy + oy, decimals)
            s.append(f"{v:.{decimals}f}".rstrip("0").rstrip("."))
        return " ".join(s)

    for t in tokens:
        if t in "MCZmcz":
            if t.islower():
                raise ValueError(f"relative command {t!r} not supported")
            if cmd:
                flush()
            cmd, nums = t, []
        else:
            nums.append(float(t))
    if cmd:
        flush()
    return "".join(out), pts


def geometry(pts: list[tuple[float, float]]) -> dict:
    a = np.array(pts)
    x, y = a[:, 0], a[:, 1]
    # shoelace on the flattened outline (subpaths concatenated; good enough for area ranking and centroids)
    area = float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)
    return {
        "bbox": [round(float(x.min()), 1), round(float(y.min()), 1), round(float(x.max() - x.min()), 1), round(float(y.max() - y.min()), 1)],
        "centroid": [round(float(x.mean()), 1), round(float(y.mean()), 1)],
        "area": round(area),
    }


def raster(layer, canvas: int, scale: float) -> Image.Image:
    im = layer.composite()
    full = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    full.paste(im, (layer.bbox[0], layer.bbox[1]))
    size = round(canvas * scale)
    return full.resize((size, size), Image.LANCZOS)


def frame_hole(layer) -> list[int]:
    """The transparent hole of the white border frame, measured along its centre row and column."""
    a = np.asarray(layer.composite())[..., 3]
    h, w = a.shape
    row, col = a[h // 2] < 128, a[:, w // 2] < 128
    def run(v: np.ndarray, mid: int) -> tuple[int, int]:
        lo = mid
        while lo > 0 and v[lo - 1]:
            lo -= 1
        hi = mid
        while hi < len(v) - 1 and v[hi + 1]:
            hi += 1
        return lo, hi
    x0, x1 = run(row, w // 2)
    y0, y1 = run(col, h // 2)
    return [x0 + layer.bbox[0], y0 + layer.bbox[1], x1 - x0 + 1, y1 - y0 + 1]


def save_webp(im: Image.Image, path: Path, quality: int) -> None:
    im.save(path, "WEBP", quality=quality, alpha_quality=100, method=6)


def svg_doc(canvas: int, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas} {canvas}">\n{body}</svg>\n'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psd")
    ap.add_argument("art_dir")
    ap.add_argument("--scale", type=float, default=0.5, help="raster layers scale relative to the PSD (default 0.5)")
    ap.add_argument("--reference", required=True, help="the published image: caption source and check target")
    ap.add_argument("--quality", type=int, default=90, help="WebP quality for the raster layers (default 90)")
    args = ap.parse_args()

    psd_path = Path(args.psd)
    out = Path(args.art_dir) / "layers"
    out.mkdir(parents=True, exist_ok=True)
    psd = PSDImage.open(psd_path)
    canvas = psd.width
    assert psd.width == psd.height, "expected a square canvas"
    print(f"{psd_path.name}: {psd.width}x{psd.height}, {len(list(psd))} layers")

    by_id = {l.layer_id: l for l in psd}
    stack = [(l.layer_id, l.name, l.kind) for l in psd]
    fills: list[dict] = []
    inks: list[dict] = []
    for l in psd:
        if l.kind != "smartobject" or l.smart_object.filetype.strip().lower() != "svg":
            continue
        paths, place = read_vector_layer(l)
        for n, p in enumerate(paths):
            d, pts = translate(p["d"], place)
            rec = {"layer": l.layer_id, "n": n, "d": d, **geometry(pts), "_pts": np.array(pts, dtype=np.float32)}
            if p["fill"] == "#000000":
                inks.append(rec)
            else:
                rec["fill"] = p["fill"]
                rec["opacity"] = p["opacity"]
                fills.append(rec)
        print(f"  vector layer {l.layer_id} {l.name!r}: {len(paths)} paths at ({place[0]:.1f}, {place[1]:.1f}) scale {place[2]:.5f}")
    for i, f in enumerate(fills):
        f["id"] = f"f{i + 1:03d}"
    for i, s in enumerate(inks):
        s["id"] = f"i{i + 1:04d}"
    print(f"  {len(fills)} fills, {len(inks)} ink strokes")

    # Ink that outlines each fill: a stroke belongs to a fill when enough of its outline runs along the fill's
    # edge. Ink strokes are filled outline shapes about 40 px wide here, so both sides of a stroke that traces a
    # fill's edge lie within ~25 px of it; NEAR allows for that plus the fill sitting under the line.
    NEAR, SHARE = 40.0, 0.3
    ib = np.array([s_["bbox"] for s_ in inks])
    for f in fills:
        x, y, w, h = f["bbox"]
        cand = np.flatnonzero((ib[:, 0] < x + w + NEAR) & (ib[:, 0] + ib[:, 2] > x - NEAR)
                              & (ib[:, 1] < y + h + NEAR) & (ib[:, 1] + ib[:, 3] > y - NEAR))
        edge = f["_pts"]
        near: list[tuple[float, str]] = []
        for k in cand:
            ip = inks[k]["_pts"]
            # nearest edge point for every ink point, in chunks to bound memory
            best = np.empty(len(ip), dtype=np.float32)
            for c in range(0, len(ip), 512):
                d2 = ((ip[c:c + 512, None, :] - edge[None, :, :]) ** 2).sum(-1)
                best[c:c + 512] = np.sqrt(d2.min(1))
            share = float((best < NEAR).mean())
            if share >= SHARE:
                near.append((share, inks[k]["id"]))
        near.sort(reverse=True)
        f["ink"] = [i for _, i in near]
    for r in fills + inks:
        r.pop("_pts", None)
    print(f"  ink per fill (outline adjacency): median {int(np.median([len(f['ink']) for f in fills]))}, max {max(len(f['ink']) for f in fills)}")

    body = "".join(
        f'<path id="{f["id"]}" fill="{f["fill"]}"' + (f' fill-opacity="{f["opacity"]:.3f}"' if f["opacity"] < 1 else "") + f' d="{f["d"]}"/>\n'
        for f in fills)
    (out / "fills.svg").write_text(svg_doc(canvas, body))
    body = '<g fill="#000">\n' + "".join(f'<path id="{s["id"]}" d="{s["d"]}"/>\n' for s in inks) + "</g>\n"
    (out / "ink.svg").write_text(svg_doc(canvas, body))

    # How much of each fill is visible: later fills paint over earlier ones (a tree's body under its trunk
    # details), so a shape's own area says little about what a viewer sees. Render every fill in paint order in an
    # id-encoded colour, unblended and without anti-aliasing, and count the pixels each keeps; then subtract what the
    # ink covers. `visible` is the share of the fill's area left showing, `visibleArea` that area in canvas px.
    import resvg_py
    VS = canvas // 2
    ids_svg = "".join(f'<path fill="#{i + 1:06x}" d="{f["d"]}"/>' for i, f in enumerate(fills))
    ink_svg = "".join(f'<path d="{s_["d"]}"/>' for s_ in inks)
    vis_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas} {canvas}" width="{VS}" height="{VS}" '
               f'shape-rendering="crispEdges"><rect width="{canvas}" height="{canvas}" fill="#000"/>{ids_svg}'
               f'<g fill="#000">{ink_svg}</g></svg>')
    px = np.asarray(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=vis_svg)))).convert("RGB")).astype(np.int64)
    idx = (px[..., 0] << 16) | (px[..., 1] << 8) | px[..., 2]
    counts = np.bincount(idx.ravel(), minlength=len(fills) + 1)
    k2 = (canvas / VS) ** 2
    # Each fill's own pixel area, rendered alone over its box at the same scale (the shoelace `area` is only a
    # ranking hint: it is wrong for shapes with holes or several sub-shapes).
    for i, f in enumerate(fills):
        x, y, w, h = f["bbox"]
        W, H = max(1, round(w / 2)), max(1, round(h / 2))
        solo = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {W * 2} {H * 2}" width="{W}" height="{H}" '
                f'shape-rendering="crispEdges"><path fill="#fff" d="{f["d"]}"/></svg>')
        a_ = np.asarray(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=solo)))).convert("RGBA"))[..., 3]
        own = float((a_ > 127).sum()) * k2
        va = float(counts[i + 1]) * k2
        f["pixelArea"] = round(own)
        f["visibleArea"] = round(va)
        f["visible"] = round(min(1.0, va / own) if own > 0 else 0.0, 3)
    print(f"  visibility: median {np.median([f['visible'] for f in fills]):.2f}, "
          f"{sum(f['visible'] >= 0.5 for f in fills)} fills at least half visible")

    # The painted area is the hole in the white border frame (a shape layer); everything is clipped to it.
    frame = next((l for l in psd if l.kind == "shape"), None)
    painted = frame_hole(frame) if frame else [0, 0, canvas, canvas]
    print(f"  painted area (frame hole): {painted}")

    # Raster layers by role: the two big pixel layers in stack order are the wash (below the fills) and the
    # scribbles (above them). The PSD's small title and signature layers are not used (see the docstring).
    pixel = [l for l in psd if l.kind == "pixel" or (l.kind == "smartobject" and l.smart_object.filetype.strip().lower() != "svg")]
    big = [l for l in pixel if l.bbox[2] - l.bbox[0] > canvas / 2 and l.bbox[3] - l.bbox[1] > canvas / 2]
    rasters = {}
    for role, l in zip(("wash", "scribbles"), big):
        full = raster(l, canvas, args.scale)
        save_webp(full, out / f"{role}.webp", args.quality)
        save_webp(full.resize((full.width // 2, full.height // 2), Image.LANCZOS), out / f"{role}.small.webp", args.quality)
        rasters[role] = {"layer": l.layer_id, "name": l.name, "file": f"{role}.webp", "small": f"{role}.small.webp"}
        print(f"  {role}: layer {l.layer_id} {l.name!r} -> {role}.webp")

    # Caption: the reference image's margin below the painted area, mapped to canvas coordinates.
    ref = Image.open(args.reference).convert("RGB")
    k = ref.width / canvas
    cap_y = painted[1] + painted[3] + 8
    cap = ref.crop((0, round(cap_y * k), ref.width, ref.height))
    save_webp(cap, out / "caption.webp", args.quality)
    caption = {"file": "caption.webp", "box": [0, cap_y, canvas, canvas - cap_y], "source": Path(args.reference).name}
    print(f"  caption: {cap.size[0]}x{cap.size[1]} from {Path(args.reference).name} -> caption.webp")

    info = {
        "schema": "thingsynth.layers/1",
        "source": {"file": psd_path.name, "sha256": hashlib.sha256(psd_path.read_bytes()).hexdigest(), "width": psd.width, "height": psd.height},
        "canvas": [canvas, canvas],
        "painted": painted,
        "rasterScale": args.scale,
        "stack": [{"layer": i, "name": n, "kind": k_} for i, n, k_ in stack],
        "order": ["background", "wash", "fills", "scribbles", "ink", "caption"],
        "rasters": rasters,
        "caption": caption,
        "files": {"fills": "fills.svg", "ink": "ink.svg"},
        "counts": {"fills": len(fills), "ink": len(inks)},
    }
    (out / "layers.json").write_text(json.dumps(info, indent=2) + "\n")
    parts = {"schema": "thingsynth.parts/1", "canvas": [canvas, canvas],
             "fills": [{k_: v for k_, v in f.items() if k_ != "d"} for f in fills],
             "ink": [{k_: v for k_, v in s_.items() if k_ != "d"} for s_ in inks]}
    (out / "parts.json").write_text(json.dumps(parts, separators=(",", ":")) + "\n")
    for stale in ("wash.png", "scribbles.png", "sig.png", "title.png"):
        (out / stale).unlink(missing_ok=True)

    # Check: rebuild the stack exactly as the page does and compare with the reference.
    import resvg_py
    S = 1200
    sk = S / canvas
    def svg_png(p: Path) -> Image.Image:
        png = resvg_py.svg_to_bytes(svg_string=p.read_text(), width=S, height=S)
        return Image.open(io.BytesIO(bytes(png))).convert("RGBA")
    art = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    art.alpha_composite(Image.open(out / "wash.webp").convert("RGBA").resize((S, S), Image.LANCZOS))
    art.alpha_composite(svg_png(out / "fills.svg"))
    art.alpha_composite(Image.open(out / "scribbles.webp").convert("RGBA").resize((S, S), Image.LANCZOS))
    art.alpha_composite(svg_png(out / "ink.svg"))
    x, y, w, h = (round(v * sk) for v in painted)
    comp = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    comp.alpha_composite(art.crop((x, y, x + w, y + h)), (x, y))
    cb = caption["box"]
    comp.paste(Image.open(out / "caption.webp").convert("RGB").resize((S, S - round(cb[1] * sk)), Image.LANCZOS), (0, round(cb[1] * sk)))
    refS = ref.resize((S, S), Image.LANCZOS)
    diff = np.abs(np.asarray(comp.convert("RGB")).astype(int) - np.asarray(refS).astype(int))
    inner = diff[y:y + h, x:x + w]
    print(f"  check, painted area: mean abs difference {inner.mean():.2f}/255, pixels off by more than 40: {(inner.max(axis=2) > 40).mean() * 100:.2f}%")
    side = Image.new("RGB", (S * 2, S), "white"); side.paste(comp.convert("RGB"), (0, 0)); side.paste(refS, (S, 0))
    side.save(out / "check.jpg", quality=85)
    for f in sorted(out.iterdir()):
        print(f"  {f.name:16} {f.stat().st_size // 1024:6} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
