# Graveyard Shift

A top-down 3D zombie survival shooter, played **in landscape** on desktop or a
sideways phone. The game itself is one HTML file with no build step and no
dependencies to install.

Open `index.html` in a browser, or serve the directory with any static host.

## Installing it

Pushes to `main` build an installable version to GitHub Pages via
`.github/workflows/pages.yml`. On a phone, open the Pages URL and use **Add to
Home Screen** — it launches fullscreen in landscape with no browser chrome, and
works offline once cached.

`index.html` is authored as a Claude artifact fragment, with no doctype, `html`,
`head` or `body` tags of its own, because the artifact host supplies those. A
PWA needs a real document with a manifest link, so rather than keep a second
copy of the game in sync the workflow wraps the same file at deploy time. One
source of truth, still no build step for development.

**Pages must be enabled once by hand:** repository Settings → Pages → Source →
*GitHub Actions*. The workflow cannot enable it itself.

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

- **Eleven stacking upgrades**: damage, fire rate, pierce, crit, armour, regen,
  pickup magnet, and more.
- **Twin-stick by default.** The left half of the screen is a floating movement
  stick, the right half aims and fires. **Auto-aim is off by default** and can be
  switched on from the menu or pause screen — with it on, the weapon tracks the
  nearest walker and one thumb is enough. Manual aim always overrides it.

  The default is deliberate: auto-aim plus auto-fire leaves the player with only
  one verb ("don't die"), which rewards standing still in a corner. Giving the
  right thumb a job keeps both hands in the fight.
- **Synthesised audio** — gunfire, groans, impacts — generated with WebAudio.
  No audio files.

## The district

The map is a 140×140 city district generated from a **seeded** layout — stable
run to run, because a level you cannot design or test against is not a level.
Streets sit on a 28-unit pitch; blocks are split into building footprints with
alleys between them, and a few blocks are reserved as set pieces: an open lot,
a fuel forecourt, cleared rubble fields.

It holds 45 buildings, 42 light anchors, 26 wrecked cars, and several hundred
pieces of street furniture and debris — skips, jersey barriers, hydrants,
benches, cones, pallets, sacks, rubble, roof vents, traffic signals and burn
barrels. Everything is instanced, and per-instance scale carries each building's
footprint so all 45 share one geometry.

Burn barrels are reused as light anchors alongside the streetlights, so they
flicker orange on the same pooled point lights rather than needing their own.

### Collision needed a broad phase

`resolveProps` scanned every prop for every body, every step. At 22 props that
was free; at 205 colliders and 40 bodies it is roughly 8,000 distance checks per
step. A uniform grid, built once because nothing in the district moves, narrows
it to the handful in the 3×3 cells around each body — **measured 5.3× faster**
than the brute-force scan over the same set.

Buildings are AABB colliders rather than circles, pushed out along the shallower
axis, and the same broad phase stops bullets, so walls are real cover.

### The city is cheaper than the lot was

Frame time went **down**: 65ms against the small arena's 81ms under identical
conditions. Buildings occlude the ground, and the ground is the expensive
surface — it is per-fragment lit with several lights. Blocking the view of it
saves more than the extra geometry costs.

## Landscape

Landscape is the design target, and the camera frames by **width** there — about
36 world units across on a desktop window and a sideways phone alike, so the
play area is the same shape on both.

That number is why. Portrait shows roughly 14 units across, which is enough to
see your own feet and not enough to see a horde coming down a street. Sightlines,
chokepoints and leading the player with light all need the wider frame.

Portrait still works and still frames by height so the player isn't a speck, but
it is a fallback rather than the target: a phone held upright gets a rotate
prompt, while a narrow *desktop* window is left alone, since that is a legitimate
way to play.

## Darkness and the flashlight

The lot is dark, and light comes from actual light sources. Streetlamps
illuminate the ground and everything standing near them; the **flashlight** is a
found item, guaranteed to drop from wave 2, and it is a real spotlight that
lights the ground, the props and the bodies it falls on. It is not a toggle —
lose the run and you start blind again.

An earlier version faked this in screen space, darkening by distance from the
player. It looked like a filter because it was one: a lamp twenty units away sat
in shadow under that model, which is backwards. The lamp *is* the light.

## Lighting

Ambient is deliberately near-useless — enough to read a silhouette and no more.
Everything else comes from real lights, on a fixed budget:

- **Streetlamps.** Only the nearest few can ever be on screen, so a small pool
  of point lights is reassigned to the closest posts each frame rather than
  lighting all seven at once. The pool size is a quality tier: 1 light on
  battery, 2 on balanced, 3 on high.
- **The flashlight** is a `SpotLight` whose height is a balance rather than a
  preference. Too low and the beam meets the floor at grazing incidence
  (`N·L ≈ 0.1`) and lights nothing; too high and the cone touches down several
  units ahead, so it reads as a projector rather than something the player is
  carrying. Just above head height, aimed a short way ahead, puts the near edge
  of the cone about two units from the feet. It is emitted from the weapon —
  forward and slightly to the gun side — rather than from the player's centre.
- **Muzzle flash and explosions** are point lights created at startup at zero
  intensity, because adding a light later changes the scene's light count and
  forces every material to recompile.

Two costs are worth knowing. The ground uses `MeshPhongMaterial` for
**per-fragment** lighting — it is one object covering most of the screen, so
paying per-fragment there buys smooth pools and spot cones for a single
material's worth of cost, while everything else stays on cheap vertex-lit
Lambert. And changing the lamp-pool size adds or removes lights from the scene
rather than zeroing their intensity, since the shader loops over every light
present regardless; that costs one recompile on a settings change, which is
acceptable there and would not be per frame.

The ground texture carries no baked light any more. It is pure surface.

## Minimap

A 34-unit-radius radar sits under the HUD buttons: arena bounds, zombies
coloured by type, weapon crates, health drops, and your own facing. When you
carry the flashlight it also draws the cone, so the map shows what you can
actually see rather than what exists.

It is a 2D canvas redrawn each frame — a few dozen `arc` calls, far cheaper than
DOM nodes, and it became necessary the moment darkness landed.

## Cheats

Turn **Cheats: On** in the menu or pause screen and a slider button appears in the
HUD beside pause. It opens a panel with every weapon (tap to equip) and every
upgrade (tap to add a level, up to its normal cap). The world freezes while the
panel is open, so you can build a loadout without being eaten.

Touching anything in the panel marks the run: it will not write a best wave or
best score, and the game-over screen says so. Testing a wave-12 Howler pack
shouldn't quietly overwrite a real record.

## Controls

| | Touch | Desktop |
|---|---|---|
| Move | Drag on the left half | `WASD` / arrow keys |
| Aim | Drag on the right half | Mouse |
| Fire | While aiming | Hold mouse button |
| Fire (auto-aim on) | Automatic | Automatic |
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
- **The ground** is a 2D canvas painted at startup: asphalt grain, cracks and
  faded parking bays. Surface only — the light on it is real, not painted.
- **Audio** is synthesised from oscillators and noise buffers.

This was originally a constraint — the page is published as a sandboxed artifact
that cannot fetch external media — but it keeps the whole game in one file with
zero network requests after the engine loads.

### Difficulty scales on three axes, damage included

Enemy health, speed **and damage** all scale with wave number:

```js
hpScale  = 1 + 0.135 * (wave - 1)
spScale  = min(1.42, 1 + 0.022 * (wave - 1))
dmgScale = 1 + 0.12  * (wave - 1)
```

Damage scaling is load-bearing, not decoration. Without it, flat damage
reduction eventually zeroes every hit: a −10 flat armour bonus against an
unscaled 9-damage Shambler floors at 1, the global 0.42s hit cooldown caps
incoming damage at ~2.4/sec regardless of how many bodies are on you, and 3.5
HP/sec of regen then exceeds that ceiling. The result was a player who could
not be killed by anything except Brutes and Bloaters.

The fix is three-part: damage scales, armour is a **percentage** (7%/level to a
35% cap) so it can never trivialise a hit, and regen only ticks **2.2 seconds
after you were last hit**, making it a between-fights recovery tool rather than
a combat one. A fully-maxed defensive build standing still in nine wave-7
zombies now loses ~19 HP/sec.

### Post-processing: bloom and FXAA

Written by hand rather than with three.js `EffectComposer` + `UnrealBloomPass`,
which live in the examples bundle and would mean a second CDN fetch this page
can't guarantee. Four passes: scene into a render target, a bright-pass that
downsamples, a separable blur in two directions, then a composite.

- The bright-pass keys on **max channel, not luma**. This palette's highlights
  are saturated amber, which luma weighting under-reads and refuses to bloom.
- The composite also runs **FXAA**, which is load-bearing: rendering into a
  render target bypasses the canvas's MSAA entirely, so without it turning
  effects on would make edges *worse*.
- Bloom buffers run at 20–40% resolution depending on quality tier. FXAA is the
  only full-resolution pass, and it is skipped on the battery tier.
- Render targets tolerate a 6% size drift before reallocating, because the
  adaptive quality system nudges pixel ratio continuously and would otherwise
  reallocate every buffer every few frames.
- If frame time still misses 30fps with pixel ratio already at its floor,
  effects switch themselves off after ~6 sustained seconds. That is not
  persisted, so the player's own setting survives a reload.

### Lighting

Two `PointLight`s — muzzle flash and explosion — are added at startup at zero
intensity and driven by their timers. Adding a light later changes the scene's
light count and forces every material to recompile, which shows up as a hitch
at exactly the wrong moment.

The ground plane is subdivided 64×64 for their benefit: `MeshLambertMaterial`
lights per-vertex, so on the original two triangles a muzzle flash had nowhere
to land.

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

### Desktop

Keyboard and mouse are first-class, not an afterthought: WASD/arrows move, the
mouse aims, holding the button fires, `Esc` pauses. The camera has a separate
landscape branch so a wide window shows a wide view rather than a stretched
portrait one, and the on-screen hints reword themselves for keyboard and mouse
when no touch support is detected.

A `blur` handler clears held keys. `visibilitychange` catches tab switches but
not application switches, so alt-tabbing while holding a movement key used to
swallow the keyup and leave the player walking on return.

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
