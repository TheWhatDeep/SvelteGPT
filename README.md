# Graveyard Shift

An endless top-down 3D zombie survival shooter, built for portrait-mode mobile
Safari. One HTML file, no build step, no dependencies to install.

Open `index.html` in a browser, or serve the directory with any static host.

## What it is

You hold a lamp-lit parking lot against escalating waves of the dead. Clear a
wave, take one of three permanent upgrades, repeat until you're overrun. Score
and best wave persist locally.

- **Endless waves** with seven enemy types, each entering a few waves apart so
  you meet one new threat at a time:

  | Type | From wave | Behaviour |
  |---|---|---|
  | Shambler | 1 | Slow, weak, arrives in numbers |
  | Runner | 2 | Fast, fragile, closes before you notice |
  | Crawler | 3 | Scuttles on all fours — low silhouette, easy to lose in a crowd |
  | Brute | 4 | Huge and slow, soaks a magazine |
  | Spitter | 6 | Holds at range and lobs acid |
  | Bloater | 7 | Detonates on death, damaging you *and* its neighbours |
  | Howler | 9 | Shrieks and every walker nearby surges to 1.5× speed |

  Bloaters and Howlers exist to break the "hold the trigger" reflex: one
  punishes killing at arm's length, the other makes target priority matter.
- **Five weapons**, found in crates that drop in the lot each wave rather than
  chosen from a menu — walking out to get one mid-fight is the decision:

  | Weapon | Shape of it |
  |---|---|
  | Field Rifle | Balanced starter. Nothing it does badly. |
  | Scattergun | Seven pellets, short reach. Deletes a crowd at contact range. |
  | Stutter SMG | 13 rounds/sec, sprays wide, runs out of reach early. |
  | Marksman | Slow and heavy, pierces 3 bodies, drops Brutes. |
  | Thumper | Lobs a grenade. Huge against a pack, wasteful on one body. |

- **Twelve stacking upgrades**: damage, fire rate, pierce, multishot, crit,
  armour, regen, pickup magnet, and more.
- **One-thumb play.** The left half of the screen is a floating movement stick;
  the weapon auto-targets the nearest threat. The right half overrides aim when
  you need to pick something specific out of the horde.
- **Synthesised audio** — gunfire, groans, impacts — generated with WebAudio.
  No audio files.

## Controls

| | Touch | Desktop |
|---|---|---|
| Move | Drag on the left half | `WASD` / arrow keys |
| Aim | Drag on the right half (optional) | Mouse |
| Fire | Automatic | Automatic |
| Pause | Button, top right | `Esc` |

## How it's built

Vanilla JavaScript and [three.js](https://threejs.org) r128, loaded from a CDN
with a fallback source. Everything else is in `index.html`.

### Assets are generated, not loaded

There are no model or texture files. Every asset is authored in code at runtime:

- **Zombies** are six-part articulated figures — torso, head, two arms, two legs
  — with per-limb walk animation driven by a phase offset per body. Crawlers
  reuse the same six parts in a different pose: torso near-horizontal, front
  limbs pawing at the ground, hind legs kicking out behind.
- **The ground** is a 2D canvas painted at startup: asphalt grain, cracks, faded
  parking bays, and the warm pools beneath each streetlight, baked in at the
  lamps' own coordinates.
- **Audio** is synthesised from oscillators and noise buffers.

This was originally a constraint — the page is published as a sandboxed artifact
that cannot fetch external media — but it keeps the whole game in one file with
zero network requests after the engine loads.

### Weapons are base stats; upgrades are multipliers

Upgrades used to mutate `player.damage` directly. That works until weapons can
swap, at which point "+25% damage" earned on a rifle silently becomes a flat
number on a shotgun and your build evaporates.

So weapons hold base stats, upgrades write only to `player.mul` (damage, fire
rate, bullet speed, range) and `player.add` (pierce, shots, crit, spread), and
a single `recalc()` derives the effective stats into a reused `eff` object
whenever either side changes. The hot loop never re-derives or allocates, and a
build carries across every weapon swap.

### Gait is derived, not tuned

Walk cycles are driven by **distance travelled**, never by a fixed tempo. A leg
of length `L` swinging `±θ` advances the body `4·L·sin(θ)` per cycle, so each
body type's stride is computed from its own leg geometry at startup:

```js
t.stride = 4 * LEG_LEN * t.scale * Math.sin(t.legSwing);
```

The phase then advances by `(speed / stride) × 2π` per second. Feet cannot
slide, because the animation rate is a function of the movement rate rather
than a constant someone guessed. A Brute at 1.8 u/s and a Runner at 5.05 u/s
plant their feet at visibly different rates without either being hand-tuned,
and changing a type's speed needs no animation change at all.

### Performance notes

The interesting problem is drawing a horde of articulated figures on a phone.
Six separate meshes per zombie times forty zombies is ~240 draw calls, which a
mobile GPU will not enjoy.

Instead there is one `InstancedMesh` per **body part per zombie type**, and limb
world matrices are composed manually on the CPU each frame. That is 24 draw
calls for the entire horde regardless of its size, with every limb still
animating independently.

A per-instance colour approach (`setColorAt`) would cut that to 6, but it
depends on the renderer recompiling its shader when `instanceColor` first
appears — behaviour that varies across three.js versions, and when it silently
fails every zombie renders pure white. Solid materials per type are boring and
correct.

Other deliberate choices:

- **No dynamic lights for the streetlamps.** Light pools are painted into the
  ground texture, so they cost nothing per frame.
- **No shadow maps.** Expensive on mobile GPUs for very little here.
- **`MeshLambertMaterial` over `MeshStandardMaterial`** — much cheaper, and the
  art direction is flat enough not to miss PBR.
- **Device pixel ratio is capped** and adapts downward when frame time slips.
  Retina fill rate is the usual reason a WebGL page feels slow on an iPhone.
- **Fixed 1/60 timestep** with an accumulator, so physics stays stable when the
  frame rate does not.
- **`outputEncoding` is `LinearEncoding`, not sRGB.** Every colour here is
  hand-authored for display; the sRGB pass would apply a gamma curve a second
  time and wash the palette out.

### Safari specifics

- Auto-pauses on `visibilitychange`, since Safari suspends `requestAnimationFrame`
  in background tabs.
- `AudioContext` is only resumed inside a user gesture, as iOS requires.
- `touch-action: none` and `preventDefault` on touch events to suppress scroll,
  rubber-banding, and double-tap zoom.
- Handles `webglcontextlost`, which Safari fires under memory pressure, with a
  recoverable message rather than a frozen canvas.
- Sizes to `height: 100%` rather than `100vh`, which is unreliable while the
  Safari URL bar animates.

## Swapping in external 3D models

If you host this yourself, the sandbox restriction goes away and you can load
real GLTF assets. Add `GLTFLoader`, then replace the per-part `InstancedMesh`
groups with `SkinnedMesh` clones, or keep instancing and swap `zGeo`'s box
geometries for meshes extracted from a loaded model. The animation code drives
limb transforms by name, so it maps onto a real rig without restructuring the
game loop.

## Licence

MIT — see `LICENSE`.
