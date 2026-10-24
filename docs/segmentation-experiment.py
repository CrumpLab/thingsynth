import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src = sys.argv[1]
im = Image.open(src).convert('RGB')
a = np.asarray(im).astype(np.int16)
H, W, _ = a.shape
# crop to the painted area (inside the white border): find rows/cols that are not near-white
nonwhite = (a.min(axis=2) < 235)
rows = np.where(nonwhite.mean(axis=1) > 0.5)[0]; cols = np.where(nonwhite.mean(axis=0) > 0.5)[0]
y0, y1, x0, x1 = rows[0], rows[-1], cols[0], cols[-1]
print('painted area', x0, y0, x1, y1, 'size', x1-x0, y1-y0)
crop = a[y0:y1, x0:x1]
lum = crop.mean(axis=2); sat = crop.max(axis=2) - crop.min(axis=2)
for thr in (70, 90, 110):
    ink = (lum < thr) & (sat < 60)
    # thicken lines slightly so cells separate cleanly at anti-aliased gaps
    ink2 = ndi.binary_dilation(ink, iterations=2)
    lab, n = ndi.label(~ink2)
    areas = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n+1))
    print(f'thr {thr}: ink {ink.mean()*100:.1f}%  cells {n}  >500px {int((areas>500).sum())}  >2000px {int((areas>2000).sum())}  >10000px {int((areas>10000).sum())}  >50000px {int((areas>50000).sum())}')
    if thr == 90:
        keep = np.where(areas > 2000)[0] + 1
        rng = np.random.default_rng(1)
        colors = rng.integers(40, 255, size=(n+1, 3)); colors[0] = 0
        out = colors[lab]; out[ink2] = 0
        small = ~np.isin(lab, keep) & ~ink2; out[small] = 255
        Image.fromarray(out.astype(np.uint8)).resize((1000, 1000)).save('cells_preview.png')
        # also the ink mask
        Image.fromarray((~ink2*255).astype(np.uint8)).resize((1000,1000)).save('ink_preview.png')
        big = sorted(areas, reverse=True)[:5]; print('largest cells', [int(b) for b in big], 'of', crop.shape[0]*crop.shape[1])
