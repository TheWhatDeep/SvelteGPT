# Graveyard Shift

An endless top-down 3D zombie survival shooter, built for portrait-mode mobile
Safari. One HTML file, no build step, no dependencies to install.

Open `index.html` in a browser, or serve the directory with any static host.

## What it is

You hold a lamp-lit parking lot against escalating waves of the dead. Clear a
wave, take one of three permanent upgrades, repeat until you're overrun. Score
and best wave persist locally.

- **Endless waves** with four enemy types — Shamblers, Runners, Brutes, and
  ranged Spitters — that enter the mix as waves progress.
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
  — with per-limb walk animation driven by a phase offset per body.
- **The ground** is a 2D canvas painted at startup: asphalt grain, cracks, faded
  parking bays, and the warm pools beneath each streetlight, baked in at the
  lamps' own coordinates.
- **Audio** is synthesised from oscillators and noise buffers.

This was originally a constraint — the page is published as a sandboxed artifact
that cannot fetch external media — but it keeps the whole game in one file with
zero network requests after the engine loads.

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
