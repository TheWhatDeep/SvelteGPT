"""Bake a voxel character FBX into the HERO table in index.html.

Input: hero.json with the mesh's world-space triangle positions and U
coordinates, exported from three.js FBXLoader (positions in cm, model facing
+X), and palette.png, the pack's 256x1 colour strip.

The mesh is cut at the hips, knees, shoulders and elbows (triangles crossing a
cut are split), the arms are swung from the T-pose onto the gun with a two-bone
reach, and each part is written as millimetre int16 positions relative to its
joint plus one palette index per triangle.
"""
import numpy as np, base64, json, sys
from PIL import Image
d = json.load(open('hero.json'))
P = np.array(d['pos']).reshape(-1, 3, 3); U = np.array(d['u']).reshape(-1, 3)
Q = np.stack([-P[..., 2], P[..., 1], P[..., 0]], -1) / 100.0   # turn to face +Z; cm to m
ci = np.clip((U.mean(1) * 256).astype(int), 0, 255)
pal=np.array(Image.open('palette.png').convert('RGB'))[0]
Q=Q.copy(); Q[...,2]-=0.05                       # centre the body on z = 0

def clip(tris, cols, axis, v):
    """Split triangles by the plane coord[axis] = v. Returns (below, above) lists."""
    lo, hi = ([], []), ([], [])
    for t, c in zip(tris, cols):
        s = t[:, axis] - v
        if (np.abs(s) < 1e-6).all():
            # lying on the cut: it belongs to the side its solid is on, behind it
            n = np.cross(t[1] - t[0], t[2] - t[0])[axis]
            side = hi if n < 0 else lo
            side[0].append(t); side[1].append(c); continue
        if (s <= 1e-9).all(): lo[0].append(t); lo[1].append(c); continue
        if (s >= -1e-9).all(): hi[0].append(t); hi[1].append(c); continue
        for side, keep in ((lo, lambda x: x <= 0), (hi, lambda x: x >= 0)):
            poly = []
            for i in range(3):
                a, b = t[i], t[(i + 1) % 3]; sa, sb = s[i], s[(i + 1) % 3]
                if keep(sa): poly.append(a)
                if (sa < 0 < sb) or (sb < 0 < sa):
                    poly.append(a + (b - a) * (sa / (sa - sb)))
            for k in range(1, len(poly) - 1):
                side[0].append(np.array([poly[0], poly[k], poly[k + 1]])); side[1].append(c)
    return lo, hi

T = list(Q); C = list(ci)
legs, upper = clip(T, C, 1, 0.62)
legR, legL = clip(*legs, 0, 0.0)                       # character's right is -x
parts = {}
for name, part in (('L', legL), ('R', legR)):
    shin, thigh = clip(*part, 1, 0.32)
    parts['thigh' + name] = thigh; parts['shin' + name] = shin

# arms: everything above the waist band that sits outboard of the shoulders
band_lo, band_hi = ([], []), ([], [])
for t, c in zip(*upper):
    (band_hi if t[:, 1].mean() > 1.05 else band_lo)[0].append(t)
    (band_hi if t[:, 1].mean() > 1.05 else band_lo)[1].append(c)
torso = [list(band_lo[0]), list(band_lo[1])]
mid, armP = clip(*band_hi, 0, 0.15)
armN, mid = clip(*mid, 0, -0.15)
torso[0] += mid[0]; torso[1] += mid[1]

def rot_frame(u0, d1):
    """Rotation taking direction u0 to d1 while keeping 'up' as close to +y as it can."""
    def frame(d):
        up = np.array([0., 1., 0.]) - d * d[1]
        if np.linalg.norm(up) < 1e-3: up = np.array([0., 0., 1.]) - d * d[2]
        up /= np.linalg.norm(up); return np.stack([d, up, np.cross(d, up)], 1)
    return frame(d1) @ frame(u0).T

def pose_arm(tris, cols, sgn, S, H, pole, a=0.30, b=0.28):
    # two-bone reach: where must the elbow go for the hand to land on H?
    S, H, pole = map(np.array, (S, H, pole))
    D = H - S; d = min(np.linalg.norm(D), a + b - 1e-3); dirv = D / np.linalg.norm(D)
    ca = (a * a + d * d - b * b) / (2 * a * d); sa = np.sqrt(max(0, 1 - ca * ca))
    perp = pole - dirv * pole.dot(dirv); perp /= np.linalg.norm(perp)
    E = S + a * (ca * dirv + sa * perp)
    Hh = S + dirv * d
    u0 = np.array([sgn, 0., 0.])
    R1 = rot_frame(u0, (E - S) / a); R2 = rot_frame(u0, (Hh - E) / np.linalg.norm(Hh - E))
    S0 = np.array([0.15 * sgn, 1.2, 0.0]); E0 = np.array([0.45 * sgn, 1.2, 0.0])
    upperA, fore = clip(tris, cols, 0, 0.45 * sgn) if sgn > 0 else clip(tris, cols, 0, 0.45 * sgn)[::-1]
    out_t, out_c = [], []
    for t, c in zip(*upperA): out_t.append((R1 @ (t - S0).T).T + S); out_c.append(c)
    for t, c in zip(*fore):   out_t.append((R2 @ (t - E0).T).T + E); out_c.append(c)
    return out_t, out_c, E

# Gun sits on the +x side at chest height, stock at the shoulder. Hands on the
# grip and the foregrip; elbows pushed out and down like someone holding a rifle.
GY = 1.03
tP, cP, eP = pose_arm(*armP, 1, [0.15, 1.2, 0.0], [0.17, GY - 0.02, 0.24], [1.0, -0.6, -0.4])
tN, cN, eN = pose_arm(*armN, -1, [-0.15, 1.2, 0.0], [0.13, GY + 0.01, 0.52], [-0.6, -1.0, 0.1])
torso[0] += tP + tN; torso[1] += cP + cN
parts['upper'] = torso
print('elbows', np.round(eP, 3), np.round(eN, 3))

# pivots: thighs hang from the hip, shins from the knee
PIV = {'thighL': [0.10, 0.62, 0], 'thighR': [-0.10, 0.62, 0], 'shinL': [0.10, 0.32, 0], 'shinR': [-0.10, 0.32, 0], 'upper': [0, 0, 0]}
used = sorted(set(int(c) for p in parts.values() for c in p[1]))
remap = {c: i for i, c in enumerate(used)}
out = {'pal': ['%02x%02x%02x' % tuple(pal[c]) for c in used], 'gunY': GY, 'parts': {}}
total = 0
for k, (tris, cols) in parts.items():
    P = np.array(tris) - np.array(PIV[k])
    q = np.round(P * 1000).astype('<i2')
    out['parts'][k] = {'n': len(tris), 'p': base64.b64encode(q.tobytes()).decode(),
                       'c': base64.b64encode(bytes(remap[int(c)] for c in cols)).decode()}
    total += len(tris)
json.dump(out, open('hero_baked.json', 'w'))
print('parts', {k: v['n'] for k, v in out['parts'].items()}, 'total tris', total,
      'colours', len(used), 'bytes', len(json.dumps(out)))
