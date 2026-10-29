# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10", "numpy>=1.26", "resvg-py>=0.1"]
# ///
"""Batch b10 of the note animations: notes 34, 48, 64, 76, 90, 104 (see scripts/note_kit.py).

    uv run scripts/notes_b10.py            # strips and end frames
    uv run scripts/notes_b10.py 64         # one note
    uv run scripts/notes_b10.py export     # build.json for each
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ks = importlib.util.spec_from_file_location('note_kit', ROOT / 'scripts/note_kit.py')
k = importlib.util.module_from_spec(ks); ks.loader.exec_module(k)

m, g, p, tube, bez = k.m, k.g, k.p, k.tube, k.bez
smooth, rot_path, crescent = m.smooth, g.rot_path, g.crescent


# ---- helpers ---------------------------------------------------------------------------------------------------------

def R(v):
    return round(float(v), 4)


def it(d, fill, edge, at, start, end, grow='scale', out=None):
    """One sprite item; `out` = (outStart, outEnd) to shrink it away again."""
    x = {'d': d, 'fill': fill, 'edge': edge, 'at': [round(at[0], 1), round(at[1], 1)], 'start': R(start), 'end': R(end),
         'grow': grow}
    if out:
        x['outStart'], x['outEnd'] = R(out[0]), R(out[1])
    return x


def lump(cx, cy, rx, ry, rot=0.0, seed=0, amt=0.06, n=12) -> str:
    """A lumpy hand-drawn ellipse, rotated by rot degrees."""
    rnd = random.Random(seed)
    a = math.radians(rot)
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        q = 1 + amt * (rnd.random() * 2 - 1)
        x, y = math.cos(t) * rx * q, math.sin(t) * ry * q
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return smooth(pts)


def star(cx, cy, r_out, r_in, n, seed=0, rot=0.0) -> str:
    """A lumpy, round-tipped star: alternate long and short spokes through a smooth curve."""
    rnd = random.Random(seed)
    pts = []
    for i in range(2 * n):
        a = math.radians(rot) + i * math.pi / n
        r = (r_out if i % 2 == 0 else r_in) * (1 + 0.12 * (rnd.random() * 2 - 1))
        pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r))
    return smooth(pts)


def pointed(base, ang, length, w, bend=0.0, seed=0) -> str:
    """A fat pointed shape (a thorn, a spark, a pincer finger) from a round base at `base` out to a sharp tip along
    angle `ang` (degrees, counter-clockwise, y up), `w` half-width at the base, `bend` curling the tip sideways."""
    rnd = random.Random(seed)
    a = math.radians(ang)
    d = (math.cos(a), -math.sin(a))
    n = (-d[1], d[0])
    bx, by = base
    jit = lambda: 1 + 0.08 * (rnd.random() * 2 - 1)
    tip = (bx + d[0] * length + n[0] * bend, by + d[1] * length + n[1] * bend)
    s1 = (bx + n[0] * w * jit(), by + n[1] * w * jit())
    s2 = (bx - n[0] * w * jit(), by - n[1] * w * jit())
    back = (bx - d[0] * w * 0.7, by - d[1] * w * 0.7)
    L = length

    def P(q, u, v):  # q + u along d + v along n
        return p(q[0] + d[0] * u + n[0] * v, q[1] + d[1] * u + n[1] * v)
    return (f'M{p(*tip)}C{P(tip, -L * 0.45, w * 0.35 - bend * 0.4)} {P(s1, w * 0.6, 0)} {p(*s1)}'
            f'C{P(s1, -w * 0.5, 0)} {P(back, 0, w * 0.6)} {p(*back)}'
            f'C{P(back, 0, -w * 0.6)} {P(s2, -w * 0.5, 0)} {p(*s2)}'
            f'C{P(s2, w * 0.6, 0)} {P(tip, -L * 0.45, -w * 0.35 - bend * 0.4)} {p(*tip)}Z')


def stalk_copy(fid, colour, edge, start=0.0):
    """The painted shape laid again (fill and outline), so it can stay in front of something drawn behind it."""
    return it(m.FILLS[fid], colour, edge, m.FP[fid]['centroid'], start, start + 0.001)


# ---- note-34 A#1: the neighbour peeks in ---------------------------------------------------------------------------
# The see-through strip at the painting's left edge. Something big lives just past the edge: its fat lilac fingers
# curl in one by one over the orange cap's rim, its head slides in over the strip behind the red blade's tip, a big
# eye arrives sleepy and rolls round to the pink figure, then the lid lifts, the brow goes up and a cheek bunches.

def design_34():
    E = 14
    LIL, LID, BROW, CHEEK = '#C49CF2', '#A47BE4', '#6F3CC0', '#F59BD8'
    EDGE = 378.0
    items = []
    # the head: a lumpy dome coming in from the edge, as far as the pink figure
    head = smooth([(EDGE, 3112), (398, 3086), (432, 3080), (466, 3096), (498, 3128), (512, 3166), (498, 3214), (497, 3272),
                   (493, 3332), (484, 3380), (466, 3414), (436, 3432), (404, 3438), (EDGE, 3432)])
    items.append(it(head, LIL, E, (EDGE, 3272), 0.38, 0.58, 'x'))
    # the eye: white, iris and pupil looking down, then round to the pink figure
    ex, ey = 446, 3300
    items.append(it(lump(ex, ey, 40, 52, 0, 3, 0.04), '#ffffff', E, (ex, ey), 0.5, 0.6))
    items.append(it(lump(ex - 4, ey + 16, 25, 25, 0, 4, 0.04), '#4CF6BE', 11, (ex, ey), 0.56, 0.64, out=(0.7, 0.76)))
    items.append(it(lump(ex - 4, ey + 18, 12, 12, 0, 5), '#000000', 0, (ex, ey), 0.56, 0.64, out=(0.7, 0.76)))
    items.append(it(lump(ex + 12, ey + 4, 25, 25, 0, 6, 0.04), '#4CF6BE', 11, (ex + 12, ey + 4), 0.72, 0.82))
    items.append(it(lump(ex + 17, ey + 5, 12, 12, 0, 7), '#000000', 0, (ex + 12, ey + 4), 0.72, 0.82))
    items.append(it(lump(ex + 22, ey - 5, 6, 6, 0, 8), '#ffffff', 0, (ex + 12, ey + 4), 0.76, 0.86))
    # the sleepy lid over its top, lifting off at the end
    lid = smooth([(400, 3306), (403, 3268), (421, 3242), (447, 3234), (474, 3242), (492, 3268), (495, 3306), (472, 3318),
                  (446, 3322), (420, 3318)])
    items.append(it(lid, LID, E, (446, 3236), 0.5, 0.6, out=(0.84, 0.93)))
    # the brow arches up and the cheek bunches
    items.append(it(tube(bez((404, 3226), (424, 3196), (458, 3188), (484, 3204), 14), 10, 7), BROW, 10, (444, 3220), 0.85, 0.94))
    items.append(it(lump(452, 3384, 34, 20, -8, 9), CHEEK, 11, (452, 3384), 0.9, 1.0))
    # the hand: the back of it along the edge, four fat fingers curling over the cap's rim one by one from the top
    fingers = []
    for kk, (y, L) in enumerate([(3448, 112), (3504, 126), (3560, 120), (3614, 102)]):
        P = bez((EDGE + 10, y), (420, y - 8), (EDGE + L - 24, y - 6), (EDGE + L, y + 8), 18)
        s = [0.0, 0.1, 0.2, 0.3][kk]
        e = s + (0.07 if kk == 0 else 0.12)
        tx, ty = P[-1]
        fingers.append([it(tube(P, 30, 27), LIL, E, (EDGE, y), s, e, 'x'),
                        it(lump(tx - 6, ty - 4, 15, 12, 20, 60 + kk, 0.08), '#FF89C8', 10, (EDGE, y), s, e, 'x')])
    back = smooth([(EDGE, 3418), (404, 3424), (424, 3470), (428, 3530), (424, 3590), (412, 3640), (EDGE, 3648)])
    items += [x for f in fingers[::-1] for x in f] + [it(back, LIL, E, (EDGE, 3530), 0.0, 0.07, 'x')]
    return {
        'note': 34,
        'label': 'The see-through strip at the painting\'s left edge: hold A#1 to play; a big lilac neighbour from past '
                 'the edge curls its fingers round, leans in, and its sleepy eye opens wide',
        'crop': (300, 3020, 700, 700),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-48 C3: koala hug -------------------------------------------------------------------------------------------
# The splash bush's magenta stalk. A koala climbs it from behind: its ears pop out first, then its body behind the
# stalk and its head beside it, then its arms and a leg wrap round the front; at the end it squeezes, eyes closing
# happily, a blush on its cheek.

def design_48():
    E = 13
    GREY, DARK, EAR, CHEST, NOSE = '#ABA5BC', '#8E87A3', '#F7C3DE', '#E4DFEC', '#2E2A35'
    items = []
    # ears first (the 0.2 s beat), the left one then the right, half behind the stalk
    for (cx, cy, r, s) in [(574, 2798, 46, 0.0), (690, 2788, 42, 0.04)]:
        items.append(it(lump(cx, cy, r, r * 0.92, 0, int(cx), 0.1, 11), GREY, E, (cx, cy + 30), s, s + 0.06))
        items.append(it(lump(cx + 3, cy + 4, r * 0.55, r * 0.5, 0, int(cx) + 1, 0.08), EAR, 0, (cx, cy + 30), s, s + 0.06))
    # the body behind the stalk, with its pale chest
    items.append(it(lump(652, 2990, 80, 104, 8, 21, 0.06), GREY, E, (660, 3090), 0.1, 0.3))
    items.append(it(lump(640, 3010, 40, 62, 8, 22, 0.08), CHEST, 0, (660, 3090), 0.16, 0.32))
    # the head beside the stalk, its right cheek tucked behind it
    items.append(it(lump(626, 2858, 76, 66, -6, 23, 0.05), GREY, E, (640, 2930), 0.25, 0.42))
    items.append(it(smooth([(596, 2874), (618, 2866), (640, 2874), (642, 2896), (630, 2912), (606, 2912), (594, 2896)]), NOSE, 11,
                    (618, 2888), 0.36, 0.48))
    for j, (x, y) in enumerate([(585, 2846), (648, 2842)]):
        items.append(it(lump(x, y, 9, 11, 0, 30 + j), '#000000', 0, (x, y), 0.42, 0.5, out=(0.84, 0.9)))
        items.append(it(lump(x + 3, y - 4, 3.5, 3.5, 0, 34 + j), '#ffffff', 0, (x, y), 0.44, 0.52, out=(0.84, 0.9)))
    # the stalk laid again in front of the body and the head's cheek (fill and outline), from the first moment
    items.append(stalk_copy('f113', '#F434E6', 13))
    # arms wrap round the front of the stalk: first pose, then a tighter squeeze
    arms = [((690, 2952), (792, 2946), (812, 2954)), ((696, 3026), (800, 3026), (820, 3036))]
    for j, (sh, pw, pw2) in enumerate(arms):
        s = 0.45 + 0.1 * j
        P = bez(sh, (sh[0] + 30, sh[1] - 18), (pw[0] - 34, pw[1] - 16), pw, 16)
        items.append(it(tube(P, 24, 21), GREY, E, sh, s, s + 0.14, out=(0.84, 0.9)))
        items.append(it(lump(pw[0] + 4, pw[1] + 4, 27, 22, 30, 40 + j), DARK, E, sh, s, s + 0.14, out=(0.84, 0.9)))
        Q = bez(sh, (sh[0] + 34, sh[1] - 22), (pw2[0] - 30, pw2[1] - 22), pw2, 16)
        items.append(it(tube(Q, 25, 22), GREY, E, sh, 0.84, 0.93))
        items.append(it(lump(pw2[0] + 2, pw2[1] + 6, 29, 23, 45, 50 + j), DARK, E, sh, 0.84, 0.93))
        # a fill-only shoulder over the arm's root, so it comes out of the body with no seam
        items.append(it(lump(sh[0] - 4, sh[1] + 2, 27, 30, 0, 55 + j), GREY, 0, sh, s, s + 0.06))
    # a leg hooks round the stalk's foot
    L = bez((676, 3070), (708, 3090), (748, 3118), (788, 3136), 14)
    items.append(it(tube(L, 26, 22), GREY, E, (676, 3070), 0.66, 0.8))
    items.append(it(lump(796, 3142, 28, 20, 25, 60), DARK, E, (676, 3070), 0.66, 0.8))
    items.append(it(lump(672, 3068, 26, 28, 0, 61), GREY, 0, (676, 3070), 0.66, 0.72))
    # the squeeze: eyes close into happy arcs, a blush
    for j, (x, y) in enumerate([(585, 2848), (648, 2844)]):
        items.append(it(crescent(x, y + 12, 16, 30, 150, 9), '#000000', 0, (x, y), 0.86, 0.95))
    items.append(it(lump(574, 2884, 15, 10, 0, 70), '#FF9EC9', 0, (574, 2884), 0.9, 1.0))
    return {
        'note': 48,
        'label': 'The magenta stalk in the splash bush: hold C3 to play; a koala climbs it, wraps its arms round and '
                 'gives it a big happy squeeze',
        'crop': (430, 2640, 600, 600),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-64 E4: rubber duck --------------------------------------------------------------------------------------
# The butter-yellow almond in the orange cap is a rubber duck's back afloat in a tub: its tail flicks up, its head
# rises out behind its back, the orange bill and a round eye arrive, then a wing; suds puff up along the waterline,
# and at the end its bill opens and it squeaks.

def design_64():
    E = 12
    YEL, WING, BILL, BILL_D, SUDS = '#FFF789', '#FFE24A', '#FF8A2A', '#E8641A', '#ffffff'
    items = []
    # tail flicks up from the almond's point (the 0.2 s beat), behind the body
    items.append(it(pointed((794, 3436), 122, 100, 28, -14, 1), YEL, E, (794, 3436), 0.0, 0.06))
    # the head rises out behind the body
    items.append(it(lump(894, 3374, 68, 62, -8, 2, 0.05), YEL, E, (890, 3450), 0.1, 0.3))
    # the body laid again in front, so the neck tucks behind its back (fill and outline, from the first moment)
    items.append(stalk_copy('f102', YEL, E))
    # the bill and the eye
    upper = smooth([(948, 3356), (982, 3348), (1022, 3352), (1040, 3366), (1022, 3378), (982, 3382), (950, 3384)])
    items.append(it(upper, BILL, E, (950, 3368), 0.3, 0.42))
    items.append(it(lump(905, 3348, 11, 13, 0, 3), '#000000', 0, (905, 3348), 0.4, 0.48))
    items.append(it(lump(909, 3343, 4, 4, 0, 4), '#ffffff', 0, (905, 3348), 0.42, 0.5))
    # a wing on its back
    items.append(it(smooth([(818, 3470), (842, 3452), (880, 3456), (902, 3478), (888, 3506), (850, 3512), (826, 3498)]),
                    WING, 11, (870, 3480), 0.45, 0.6))
    # suds puff up along the waterline, one after another
    # (an outlined layer under a fill-only layer, so the puffs melt into one foam)
    puffs = [(800, 3480, 28), (826, 3522, 34), (866, 3556, 32), (908, 3580, 36), (950, 3562, 28), (978, 3536, 22)]
    for layer in (2 * 11, 0):
        for j, (x, y, r) in enumerate(puffs):
            s = 0.55 + 0.045 * j
            items.append(it(lump(x, y, r, r * 0.86, 0, 10 + j, 0.12, 10), SUDS, layer, (x, y + r), s, s + 0.1))
    # the squeak: the bill drops open, two fat sound crescents
    lower = smooth([(950, 3384), (984, 3386), (1014, 3398), (1018, 3416), (990, 3418), (956, 3404)])
    items.append(it(lower, BILL_D, E, (952, 3386), 0.84, 0.92))
    items.append(it(crescent(1024, 3388, 54, -58, 58, 30), '#7FFFF6', 11, (1024, 3388), 0.88, 0.95))
    items.append(it(crescent(1024, 3388, 96, -50, 50, 34), '#FF7FD8', 11, (1024, 3388), 0.92, 1.0))
    return {
        'note': 64,
        'label': 'The yellow almond in the orange cap: hold E4 to play; it is a rubber duck afloat, its head bobs up, '
                 'suds puff round it, and it squeaks',
        'crop': (660, 3200, 500, 500),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-76 E5: claws from the crack ----------------------------------------------------------------------------
# The mauve sliver between the two orange caps is a crack, and something lives in it: a coral claw pokes up, then a
# second; each opens its pincer, pale knobs come up on them, and at the end they clack shut together.

def claw(base, wrist, ang, start, opens, seed, E, big=1.0):
    """One claw rising out of the crack at `base`: a dark hole, the arm, the palm with its fixed finger, and the
    movable finger closed, opening, opening wider, then clacking shut. `ang` is the claw's axis (degrees, ccw)."""
    CORAL, CORAL_D, HOLE = '#FF6F61', '#E8524E', '#4A2350'
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def W(q):  # claw-local (x along the claw, y below it) to canvas
        x, y = q[0] * big, q[1] * big
        return (wrist[0] + x * ca + y * sa, wrist[1] - x * sa + y * ca)

    def turn(pts, deg):  # turn claw-local points round the hinge (negative opens)
        hx, hy = 104, -22
        r = math.radians(deg)
        return [(hx + (x - hx) * math.cos(r) - (y - hy) * math.sin(r), hy + (x - hx) * math.sin(r) + (y - hy) * math.cos(r))
                for x, y in pts]

    body = [(0, -24), (30, -38), (70, -42), (100, -32), (110, -8), (140, 2), (170, 8), (188, 22), (166, 34), (130, 44),
            (90, 50), (50, 48), (16, 38), (0, 24)]
    dact = [(94, -36), (130, -40), (166, -28), (190, 0), (170, -6), (140, -8), (112, -10), (94, -18)]
    o1, o2 = opens
    out = []
    P = bez(base, (base[0] + 4, base[1] - 50), W((-50, 0)), W((6, 0)), 16)
    out.append(it(tube(P, 23 * big, 21 * big), CORAL, E, base, start, start + 0.2))
    # the movable finger's poses: closed (rising with the claw), open, wide open, closed again (the clack)
    poses = [(0, start, start + 0.2, (o1, o1 + 0.04)), (-24, o1, o1 + 0.08, (o2, o2 + 0.04)),
             (-44, o2, o2 + 0.08, (0.86, 0.9)), (0, 0.86, 0.91, None)]
    hinge = W((104, -22))
    for j, (deg, s0, s1, gone) in enumerate(poses):
        at = base if j == 0 else hinge
        out.append(it(smooth([W(q) for q in turn(dact, deg)]), CORAL_D, E, at, s0, s1, out=gone))
    out.append(it(smooth([W(q) for q in body]), CORAL, E, base, start, start + 0.2))
    # the dark hole in the crack it comes out of, laid over the arm's root
    out.append(it(lump(base[0], base[1] + 2, 32 * big, 12, -8, seed, 0.1), HOLE, 0, base, start, start + 0.04))
    return out, W((190, 0))


def design_76():
    E = 12
    c1, tip1 = claw((990, 3646), (1026, 3546), 58, 0.0, (0.38, 0.6), 10, E)
    c2, tip2 = claw((1080, 3658), (1134, 3572), 38, 0.18, (0.5, 0.64), 20, E, 0.9)
    flicks = []
    for j, (tip, a0) in enumerate([(tip1, 30), (tip2, 0)]):
        flicks.append(it(crescent(tip[0], tip[1], 40, a0, a0 + 80, 18), '#FFE65B', 10, tip, 0.9 + 0.03 * j, 0.97 + 0.03 * j))
        flicks.append(it(crescent(tip[0], tip[1], 68, a0 + 5, a0 + 75, 22), '#FFE65B', 10, tip, 0.92 + 0.03 * j, 0.98 + 0.02 * j))
    return {
        'note': 76,
        'label': 'The mauve crack between the two orange caps: hold E5 to play; two coral claws poke up out of it, '
                 'open wide, and clack',
        'crop': (860, 3300, 500, 500),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': c1 + c2 + flicks}],
    }


# ---- note-90 F#6: sharp ---------------------------------------------------------------------------------------------
# The eye bush's short magenta trunk. F# is a sharp, so it gets sharp: fat candy thorns pop out up both sides, a
# green shoot grows off it with a leaf and a bud, and the bud opens into a lumpy red rose.

def design_90():
    E = 11
    items = []
    thorns = [  # (base, angle, length, colour) in popping order
        ((1080, 3254), 158, 80, '#FF7FD8'),
        ((1104, 3222), 30, 74, '#FF4F9A'),
        ((1082, 3200), 148, 66, '#FF4F9A'),
        ((1098, 3276), 20, 78, '#FF7FD8'),
        ((1076, 3302), 170, 72, '#FF4F9A'),
        ((1090, 3180), 48, 58, '#FF7FD8'),
    ]
    for j, (b, a, L, col) in enumerate(thorns):
        s = 0.0 if j == 0 else 0.06 * j
        e = 0.05 if j == 0 else s + 0.08
        side = 1 if 90 < a < 270 else -1
        items.append(it(pointed(b, a, L, 13, 10 * side, 100 + j), col, E, b, s, e))
    # a shoot with a leaf
    sh = bez((1098, 3292), (1140, 3300), (1190, 3290), (1236, 3262), 16)
    items.append(it(tube(sh, 10, 8), '#4FC65A', E, (1098, 3292), 0.38, 0.52))
    items.append(it(pointed((1160, 3302), -30, 54, 15, 6, 120), '#7BE07F', E, (1160, 3298), 0.46, 0.58))
    # the bud swells at its tip, then gives way to the rose
    items.append(it(pointed((1244, 3262), 70, 64, 26, 0, 121), '#FF4F7A', E, (1240, 3266), 0.56, 0.7, out=(0.8, 0.86)))
    items.append(it(lump(1240, 3268, 24, 18, 0, 122, 0.1), '#4FC65A', E, (1240, 3270), 0.56, 0.68, out=(0.8, 0.86)))
    # the rose: an outer ring of lumpy petals, a middle cup, a curled heart
    rx, ry = 1256, 3238
    for j in range(5):
        a = math.radians(90 + j * 72)
        items.append(it(lump(rx + math.cos(a) * 40, ry - math.sin(a) * 36, 38, 32, -math.degrees(a), 130 + j, 0.1), '#FF3B6B', E,
                        (rx, ry), 0.8 + 0.012 * j, 0.88 + 0.012 * j))
    items.append(it(lump(rx, ry, 44, 38, 10, 140, 0.1), '#FF6F8F', E, (rx, ry), 0.87, 0.95))
    items.append(it(lump(rx - 6, ry - 4, 24, 20, -20, 141, 0.12), '#E0245A', E, (rx, ry), 0.92, 1.0))
    items.append(it(crescent(rx - 2, ry + 4, 16, 200, 340, 9), '#FF9AB0', 9, (rx, ry), 0.94, 1.0))
    return {
        'note': 90,
        'label': 'The eye bush\'s magenta trunk: hold F#6 to play; it gets sharp, candy thorns popping out up both '
                 'sides, then a shoot grows and a red rose opens',
        'crop': (930, 3030, 420, 420),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


# ---- note-104 G#7: sparkler ---------------------------------------------------------------------------------------
# The lilac bud on the mint finger is a sparkler's head: it flashes white-hot, then fat lumpy candy sparks burst out
# round it in rings, more each second, and at the end a big fizzing yellow starburst blazes behind them.

def design_104():
    E = 9
    C = (1606, 3050)
    items = []
    # the finale burst behind everything
    items.append(it(star(C[0], C[1], 102, 64, 8, 1, 22), '#FFE65B', E, C, 0.82, 0.96))
    rings = [  # (angles, length, half-width, colour, start)
        ([90, 210, 330], 64, 19, '#FFE65B', 0.04),
        ([30, 150, 270], 70, 19, '#FF7FD8', 0.2),
        ([60, 180, 300], 74, 18, '#7FFFF6', 0.4),
        ([0, 120, 240], 78, 18, '#FF9F43', 0.6),
    ]
    for ri, (angs, L, w, col, s0) in enumerate(rings):
        for j, a in enumerate(angs):
            rad = math.radians(a)
            b = (C[0] + math.cos(rad) * 30, C[1] - math.sin(rad) * 30)
            s = s0 + 0.04 * j
            items.append(it(pointed(b, a, L, w, 0, 200 + ri * 10 + j), col, E, C, s, s + 0.12))
    # fat round sparks flung out between the rays
    for j, (a, r, col) in enumerate([(15, 104, '#ffffff'), (105, 100, '#FF7FD8'), (195, 106, '#7FFFF6'), (285, 98, '#ffffff')]):
        rad = math.radians(a)
        x, y = C[0] + math.cos(rad) * r, C[1] - math.sin(rad) * r
        s = 0.5 + 0.08 * j
        items.append(it(star(x, y, 20, 12, 4, 300 + j, a), col, E, C, s, s + 0.12))
    # the white-hot core on the bud's tip: the first flash
    items.append(it(star(C[0], C[1], 36, 22, 6, 2), '#ffffff', E, C, 0.0, 0.05))
    items.append(it(lump(C[0], C[1], 14, 14, 0, 3), '#FFE65B', 0, C, 0.02, 0.06))
    return {
        'note': 104,
        'label': 'The lilac bud on the mint finger: hold G#7 to play; it lights like a sparkler, fat candy sparks '
                 'fizzing out round it in a growing starburst',
        'crop': (1440, 2890, 340, 340),
        'effects': [{'effect': 'sprites', 'place': 'over', 'items': items}],
    }


DESIGNS = [design_34(), design_48(), design_64(), design_76(), design_90(), design_104()]

if __name__ == '__main__':
    for dsn in DESIGNS:
        n_items = sum(len(e.get('items', [])) for e in dsn['effects'])
        print(f"note-{dsn['note']}: {n_items} sprite items")
    k.run(DESIGNS)
