"""Bake the voxel zombie FBX into the ZVOX table in index.html.

Input: zombie.json, the mesh's world-space triangle positions and U
coordinates exported with three.js FBXLoader (cm, model facing +X), and
palette.png, the pack's 256x1 colour strip (VoxelApocalypse_Character.png).

Unlike the hero, the zombie is baked back into *voxels*, not triangles: the
mesh is a clean 5 cm voxel surface, so each face is mapped onto its lattice
cell and the solid is recovered by parity along z. That keeps it editable —
the game recolours it per outfit and adds voxels (boils, hair, a throat sac)
before meshing it at load time.

It is cut into the game's eight zombie parts, each stored as a small box of
voxels relative to its joint (one byte per voxel: 0 empty, else 1 + palette
index). The source is in a T-pose; the arms are swung down to hang at the
sides, which on a voxel lattice is an exact quarter turn.
"""
import numpy as np, base64, json, re, sys
from PIL import Image

S = 0.05
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'zombie.json'))
P = np.array(d['pos']).reshape(-1, 3, 3); U = np.array(d['u']).reshape(-1, 3)
Q = np.stack([-P[..., 2], P[..., 1], P[..., 0]], -1) / 100.0      # face +Z; cm -> m
ci = np.clip((U.mean(1) * 256).astype(int), 0, 255)
pal = np.array(Image.open(sys.argv[2] if len(sys.argv) > 2 else 'palette.png').convert('RGB'))[0]

G = np.round((Q + [0, 0, 0.025]) / S).astype(int)                  # lattice units
lo = G.reshape(-1, 3).min(0); G -= lo; N = G.reshape(-1, 3).max(0)
Z0 = lo[2] * S - 0.025                                              # z of cell 0's back face
X0 = lo[0] * S

def inside(p, A):
    s = lambda a, b, c: (a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1])
    d1, d2, d3 = s(p, A[0], A[1]), s(p, A[1], A[2]), s(p, A[2], A[0])
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

face = {}                          # (cell, axis, sign) -> palette index
for t, c in zip(G, ci):
    n = np.cross(t[1] - t[0], t[2] - t[0]); ax = int(np.argmax(np.abs(n))); sg = 1 if n[ax] > 0 else -1
    a = [i for i in range(3) if i != ax]; mn, mx = t.min(0), t.max(0)
    for u in range(mn[a[0]], mx[a[0]]):
        for v in range(mn[a[1]], mx[a[1]]):
            if not inside((u + 0.5, v + 0.5), t[:, a].astype(float)): continue
            cell = [0, 0, 0]; cell[a[0]] = u; cell[a[1]] = v
            cell[ax] = t[0][ax] - 1 if sg > 0 else t[0][ax]
            face[(tuple(cell), ax, sg)] = int(c)
occ = np.zeros(N, bool)
runs = {}
for (cell, ax, sg) in face:
    if ax == 2: runs.setdefault(cell[:2], []).append((cell[2], sg))
for (i, j), L in runs.items():
    L.sort(); start = None
    for k, sg in L:
        if sg < 0: start = k
        elif start is not None: occ[i, j, start:k + 1] = True; start = None
col = np.zeros(N, int) - 1
for (cell, ax, sg), c in face.items(): col[cell] = c
# interior voxels never show; give them their nearest surface colour anyway,
# so a cut (at a joint) shows a sensible colour rather than black
for _ in range(4):
    for i, j, k in zip(*np.nonzero(occ & (col < 0))):
        for di, dj, dk in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            n = (i + di, j + dj, k + dk)
            if all(0 <= n[q] < N[q] for q in range(3)) and col[n] >= 0: col[i, j, k] = col[n]; break
used = sorted(set(col[occ].tolist()))
remap = {c: i + 1 for i, c in enumerate(used)}
vox = np.zeros(N, np.uint8)
for i, j, k in zip(*np.nonzero(occ)): vox[i, j, k] = remap[col[i, j, k]]
print('voxels', occ.sum(), 'grid', N.tolist(), 'colours', used)

# The model's joints, in lattice cells: body columns 13..18 (x -0.15..0.15),
# legs in columns 13-14 and 17-18, hips at row 14 (0.70 m), knees at row 7,
# arms in rows 23-24 out past the body, neck from row 26.
xc = lambda m: int(round((m - X0) / S))
BX0, BX1 = xc(-0.15), xc(0.15)
HIP, KNEE, ARM0, ARM1, NECK = 14, 7, 23, 25, 26
parts = {}
def box(a, origin):                # origin: metres of the box's min corner, relative to the joint
    return {'d': list(a.shape), 'o': [round(float(v), 3) for v in origin],
            'v': base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()}
zmin = Z0
parts['torso'] = box(vox[BX0:BX1, HIP:NECK], [-0.15, HIP * S - 1.00, zmin])
parts['head'] = box(vox[BX0:BX1, NECK:], [-0.15, 0.0, zmin])
for side, (a, b) in (('R', (xc(-0.15), xc(-0.05))), ('L', (xc(0.05), xc(0.15)))):   # character's right is -x
    parts['thigh' + side] = box(vox[a:b, KNEE:HIP], [-0.05, -(HIP - KNEE) * S, zmin])
    parts['shin' + side] = box(vox[a:b, 0:KNEE], [-0.05, -KNEE * S, zmin])
# arms: T-pose along x -> hanging along -y. The upper face of the T-pose arm
# ends up facing outward.
for side, sl, sgn in (('R', slice(0, BX0), -1), ('L', slice(BX1, N[0]), 1)):
    a = vox[sl, ARM0:ARM1]                     # (along x, 2 rows, z)
    if sgn < 0: a = a[::-1]                    # index 0 at the shoulder
    L = a.shape[0]
    h = np.zeros((2, L, N[2]), np.uint8)       # (x, y, z) with y index 0 at the hand
    for u in range(L):
        for r in range(2):                     # r=1 is the top row -> outer column
            xi = r if sgn > 0 else 1 - r
            h[xi, L - 1 - u] = a[u, r]
    parts['arm' + side] = box(h, [-0.05, 0.05 - L * S, zmin])
# the game's slots: armL/thighL sit at -x, armR/thighR at +x
slot = {'torso': 'torso', 'head': 'head', 'armL': 'armR', 'armR': 'armL',
        'thighL': 'thighR', 'thighR': 'thighL', 'shinL': 'shinR', 'shinR': 'shinL'}
out = {'pal': ['%02x%02x%02x' % tuple(pal[c]) for c in used],
       'parts': {k: parts[v] for k, v in slot.items()}}
for k, v in out['parts'].items(): print(k, v['d'], v['o'])
js = json.dumps(out, separators=(',', ':'))
print('bytes', len(js))
if len(sys.argv) > 3:
    p = sys.argv[3]; s = open(p, encoding='utf-8').read()
    s, n = re.subn(r'var ZVOX = \{.*?\};\n', lambda m: 'var ZVOX = ' + js + ';\n', s, count=1, flags=re.S)
    assert n == 1, 'ZVOX table not found'
    open(p, 'w', encoding='utf-8').write(s)
else:
    open('zvox_baked.json', 'w').write(js)
