import sys
from psd_tools import PSDImage
psd = PSDImage.open(sys.argv[1])
print('size', psd.width, psd.height, 'mode', psd.color_mode, 'depth', psd.depth, 'channels', psd.channels)
def walk(layers, depth=0):
    for l in layers:
        kind = l.kind
        extra = ''
        if hasattr(l, 'blend_mode'): extra += f' blend={l.blend_mode.name}'
        if l.mask: extra += ' +mask'
        print('  '*depth + f'[{l.layer_id}] {l.name!r} kind={kind} visible={l.visible} opacity={l.opacity} bbox={l.bbox}{extra}')
        if l.is_group(): walk(l, depth+1)
walk(psd)
