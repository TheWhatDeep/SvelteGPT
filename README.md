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

You hold Oakhaven — a small town at night — against the dead, paced by an
**AI Director**. Survive a horde, take one of three
permanent upgrades, repeat until you're overrun. Score and best time persist
locally.

- **Seven enemy types**, each entering at a higher level so you meet one new
  threat at a time. Level grows with hordes survived and time (see
  [The Director](#the-director)):

  | Type | From level | Behaviour |
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
- **Five weapons**, found in crates the Director leaves after each horde rather than
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
  switched on in Settings (the cog on the menu) or on the pause screen — with it on, the weapon tracks the
  nearest walker and one thumb is enough. Manual aim always overrides it.

  The default is deliberate: auto-aim plus auto-fire leaves the player with only
  one verb ("don't die"), which rewards standing still in a corner. Giving the
  right thumb a job keeps both hands in the fight.
- **A quiet menu.** The logo — traced from the artwork into a vector path, so
  it is sharp at any size on a transparent background — a Start button and your
  best run. Settings (auto-aim, cheats, quality, effects, sound) sit behind the
  **cog** in the bottom-right corner, in a pop-up over the menu; the **i** beside
  it opens How to Play. Escape closes either.
- **Synthesised audio** — gunfire, groans, impacts — generated with WebAudio.
  No audio files.

## The Director

An AI Director, after Left 4 Dead's, paces the run from one
number — **intensity**, how hard the player is being pushed right now:

```
target = 0.55 · proximity      bodies within 14 m, weighted by closeness
       + 0.30 · recent damage  HP lost, decaying over a few seconds
       + 0.15 · kill rate      fighting hard even when unhurt
```

Intensity rises fast (1.5/s) and falls slowly (0.25/s), so a scare lingers after
the last body drops. The Director cycles through four states:

| State | Spawns | Leaves when |
|---|---|---|
| **Build** | A rising trickle of the common dead | intensity > 0.55, or 35 s |
| **Peak** | The horde: a budget of bodies from one direction, or two from level 6 | budget spent and ≥ 8 s, or 45 s |
| **Relax** | Nothing | intensity < 0.15 for 4 s (40 s cap) |
| **Respite** | Nothing; an upgrade, and supplies | 12–20 s, or you push on 50 m |

**Relax is gated on the player, not a clock.** Hurt and cornered, it waits;
that is the thing a fixed spawn schedule can never do. A horde is announced with its
own low swell before it arrives.

- **Out of sight.** Every spawn is off screen, outdoors, and reachable by path
  (18–38 m by path, never under 14 m in a straight line), preferring behind
  the player — or ahead of where they are heading, for an ambush.
- **Specials** run on their own timer and caps — one Howler, two Bloaters, two
  Spitters, one Brute at a time and at most one every 40 s — so a run never
  dies to a dice roll of three Brutes. They never spawn in the lulls.
- **Supplies go where you are heading.** After each horde: a weapon crate
  (two from level 8), health if you are under half, and a flashlight if you
  have none — placed ahead along your direction of travel.
- **Stragglers are recycled.** A body more than 42 m away and out of sight for
  4 s is quietly removed, so outrunning the dead does not fill the alive cap
  with a trail nobody will meet.
- **Difficulty is separate from rhythm.** `level = 1 + hordes survived + time /
  150 s` scales the horde budget, the enemies and which types appear, so the
  shape of a fight stays the same while the peaks grow.

## Oakhaven

The map is **transcribed from a blueprint**, not generated: Oakhaven Village, a
176 × 104 m town — a department store and gas-station diner on the central
block, a ring of Main Street, Oak Avenue and Church Road around it, twelve
houses, a café, a church, three school buildings, a park and a forest edge.

Every coordinate in the `OAK` table is kept in **blueprint pixels** (10 px =
1 m), so any wall, door or tree can be checked against the drawing directly;
`wx()` / `wz()` convert to world metres. The table holds:

- **Buildings** as closed outlines, with doors cut from whichever wall they sit
  on, interior partitions, and the furniture drawn in each room — beds, sofas,
  kitchens, tubs, toilets, stairs, store shelving, checkout counters, pews, an
  altar. Furniture is sized to real objects inside the rectangle the blueprint
  gives it and pushed against the side it backs onto.
- **Ground**: roads, centre dashes, crosswalks, sidewalks, the store plaza, the
  gas forecourt, driveways and paths.
- **Everything else drawn**: 71 trees, 5 shrubs, 38 fence runs, 16 vehicles,
  30 lights, signs, debris, the barricade, the playground and the park.

Nothing is added that the blueprint does not show. Two readings are judgement
calls: the fuel pumps sit on the forecourt just outside the shop's thin west
wall (they are drawn right against it), and a few pieces of furniture that
landed in a doorway were nudged aside so every room can be reached.

The trees were located with a Hough-circle pass over the drawing's green
outlines and then corrected by hand; the overgrown ground is the drawing's own
stipple, extracted as a density mask and run-length encoded into the page.

### How it is built: voxels

The world is **voxel**, to match the hero model. The voxel is **10 cm — one
blueprint pixel** — so every wall, window and roof step lands exactly on the
drawing's grid; small props and furniture sit on a 5 cm grid, the hero's own
voxel size.

- **Voxel palette textures.** One texel is one voxel face (10 cm on
  architecture, 5 cm on furniture and props), aligned to the world grid, and
  shaded in a handful of flat levels rather than noise: lap siding in 20 cm
  boards, bricks one voxel high and two long, shingles, planks, dressed stone,
  leaves in clumps of three or four greens. The ground is one 1759×1038 texture
  at a texel per voxel, in the same flat levels.
- **Buildings.** Walls sit on the grid with real window openings — a frame and
  sill standing 5 cm proud, glass set back mid-wall, a cross of glazing bars,
  shutters on the homes — trimmed doorways with the door swung open against
  the inner face, corner boards and a darker footing course. Interior walls stop
  inside the outer wall, so no two colours ever share a plane (which flickers).
- **Roofs are a height map.** Every 10 cm cell over a building and its eaves
  gets the height of the highest wing gable that covers it — which is exactly
  how intersecting roofs meet, so L-shaped houses get a real valley — then
  quantised to 10 cm steps and meshed: flat runs merge into single faces, the
  steps become risers, and the gable-end walls and fascia boards fall out of
  the same pass. Homes get a chimney on their main ridge.
- **Props.** Trees are block clusters in five species; fences are built from
  posts, rails and a picket every 20 cm (iron bars every 25 cm round the church
  and park); cars have bodies cut round their wheel arches, block wheels with
  hubs, a glasshouse on four pillars with a stepped windscreen, bumpers,
  lights and mirrors. Anything that was round is square.
- **Merged, indexed geometry.** Every static object is baked into one mesh per
  material per 32 m chunk, indexed so a face shares its corners — about 222k
  vertices in all, drawn in **30–70 calls and 21–31k triangles a frame** because
  chunks off screen are culled with their real bounding spheres.
- **Roofs lift off** the building you walk into, so its rooms read from above.
- **See-through.** Walls, roofs and canopies between the camera and the player
  dither away in a small screen-space circle around the player instead of hiding them.

### Zombie brains

Three layers, after how Left 4 Dead's infected behave.

**Senses.** A zombie is *wandering*, *hunting* or *searching*. About half the
Director's build-up trickle arrives wandering and has to notice you; hordes and
specials arrive hunting.

| Sense | Rule |
|---|---|
| Sight | A forward cone, blocked by walls: 10 m in the dark, 16 m under a lamp, 22 m if you carry a torch |
| Hearing | Gunfire, measured by **path distance along the streets** — it carries round corners, not through buildings. 26 m (SMG) to 38 m (marksman); blasts 32 m |
| Pain | Being shot |
| Each other | A hunter wakes wanderers within 7 m; a Howler's shriek wakes the street |

A hunter that has sensed nothing for 14 s searches for 8 s, then loses interest.

**Pathing.** Far off, hunters walk the **flow field**: a breadth-first
distance map from the player over a 0.5 m grid, rebuilt when the player changes
cell (0.8 ms), looked a few cells ahead so paths are straight rather than
stair-stepped.

- **Flanking.** Runners (70%), crawlers (40%) and shamblers (25%) follow a second
  field to a point behind the player, routed round a 7 m no-go half-disc over the
  player's front, and turn in at the end — unless the detour is far longer than
  the direct route, which is not a flank. Measured on Main Street, direct runners
  arrive at 0–19° off the aim; flankers at 85–97°.
- **Surround.** Within 7.5 m every melee hunter takes a slot on a ring, spread
  evenly and weighted behind the player, in the order they already stand so
  nobody crosses. A pack of ten from one direction ended up in all eight
  directions around the player, half of them behind.
- **Unsticking.** A body that makes no progress for 1.5 s sidesteps.

**Attacks you can read.** Every melee hit has a wind-up — arms rise, then
slam — and lands only if you are still in reach when it does, so stepping away
dodges it. Only 3 zombies may be mid-swing at once (rising to 6 with level);
the rest hold their slots just outside reach.

| Type | Attack |
|---|---|
| Shambler, Bloater | Wind-up and slam |
| Runner | A quick wind-up (0.22 s) |
| Crawler | Pounces from 2–5 m: crouch, then a leading leap |
| Brute | Charges from 5–13 m with a clear line: plants and rears for 0.8 s, then runs straight at 12 m/s. A hit does 1.6× and knocks you back; a miss into a wall **stuns it for 1.8 s, taking 1.6× damage** |
| Spitter | Holds 6.5–12 m with a clear line, strafes and relocates after each shot, backs off when rushed, leads its shots; claws if cornered |
| Howler | Shelters 9–13 m back, flees a rush, shrieks when there is a pack to send |

The brains cost about 0.1 ms per simulation step for 26 zombies.

Zombies spawn **outdoors, 18–38 m away by path**, so nothing materialises beside
you or inside a room it cannot leave. From the spawn, 99.9% of walkable ground
is reachable; the unreachable remainder is a couple of closets behind stairs.

### Collision

A uniform grid broad phase keeps several hundred colliders cheap. Walls and
furniture are AABBs, trees, cars and posts are circles. Low things — beds,
counters, pews, fences — block bodies but not bullets. Bullets are sub-stepped,
because a fast round covers more than a wall's thickness in one physics step
and would otherwise tunnel through it.

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

The town is dark, and light comes from actual light sources. Streetlamps
illuminate the ground and everything standing near them; the **flashlight** is a
found item, left for you after your first horde if you don't have one, and a real spotlight that
lights the ground, the props and the bodies it falls on. It is not a toggle —
lose the run and you start blind again.

An earlier version faked this in screen space, darkening by distance from the
player. It looked like a filter because it was one: a lamp twenty units away sat
in shadow under that model, which is backwards. The lamp *is* the light.

## Lighting

The baseline is moonlight — enough to read the streets and rooftops, not enough
to see into a dark room. Everything else comes from real lights, on a fixed
budget:

- **Streetlamps.** Only the nearest few can ever be on screen, so a small pool
  of point lights is reassigned to the closest of the town's thirty posts. The
  pool size is a quality tier: 2 lights on battery, 3 on balanced, 4 on high. A
  light keeps its post while that post is still wanted, and a light that has to
  move fades out, moves while dark, and fades back in — so walking a street
  hands light from post to post instead of snapping it.
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

A 34-unit-radius radar sits under the HUD buttons: the town's streets and
rooftops, drawn from the ground texture, then zombies
coloured by type, weapon crates, health drops, and your own facing. When you
carry the flashlight it also draws the cone, so the map shows what you can
actually see rather than what exists.

It is a 2D canvas redrawn each frame — a few dozen `arc` calls, far cheaper than
DOM nodes, and it became necessary the moment darkness landed.

## Cheats

Turn **Cheats: On** in Settings (the cog on the menu) or on the pause screen and a slider button appears in the
HUD beside pause. It opens a panel with every weapon (tap to equip) and every
upgrade (tap to add a level, up to its normal cap). The world freezes while the
panel is open, so you can build a loadout without being eaten.

Touching anything in the panel marks the run: it will not write a best time or
best score, and the game-over screen says so. Testing a level-12 Howler pack
shouldn't quietly overwrite a real record.

With cheats on, a readout along the bottom edge also shows what the Director is
thinking: its state and time in it, intensity and where it is heading, the horde
budget spent, bodies alive, level, and time to the next special.

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

- **Characters** are built from tapered segments — a box stretched between two
  joints and narrowing along its length — so a chest is wider than a waist and
  a forearm tapers to the wrist. Skin, clothes, blood and eyes are vertex
  colours baked into each part, over a pixel cloth texture.
- **Zombies** are one voxel model — `Character_Zombie.fbx`, from the same
  pack as the hero — baked offline by `tools/bake-zombie.py`. Unlike the hero
  it is baked back into **voxels**, not triangles: the mesh is a clean 5 cm
  voxel surface, so each face is mapped onto its lattice cell and the solid is
  recovered, 600 voxels in all. It is cut into eight parts — torso, head, two
  arms, two thighs, two shins — each a small box of voxels stored relative to
  its joint (about 2 KB for the lot), with the T-pose arms swung down to hang,
  an exact quarter turn on the lattice. Knees fold while a leg swings forward
  and straighten to take the weight, which is what stops a walk reading as
  stilts. Crawlers reuse the same parts on all fours.
- **Each type and outfit is that body, edited voxel by voxel** at load time,
  then greedy-meshed (each face merged with its same-coloured neighbours into
  the biggest rectangles it can), about 1,000 triangles a body. Skin, shirt,
  trousers and shoes are recoloured by role, keeping the model's own shading
  within each; features are painted or added voxels. There are three shamblers
  (the model's own colours, red flannel, office shirt and tie with hair), two
  runners (tank top, hoodie with the hood up), two crawlers with exposed ribs, a
  brute in a hi-vis vest, a spitter in a hospital gown with acid for blood and a
  swollen throat, a bloater covered in boils, and a howler with lank hair and
  its jaw hanging open. Skin keeps each type's signature colour so they still
  read apart at a glance.
- **A glowing outline** picks the dead out at night: a thin, very faint red
  line round each zombie's silhouette. It is the classic inverted hull — each
  body part meshed again ignoring colour (so it merges into far fewer faces,
  about 380 triangles a body), inflated 1.5 screen pixels along smoothed
  normals, back faces only, blended additively — with two refinements: the
  shell's *depth* is pushed 60 cm back, so any zombie body in front covers it
  (only the *outer* silhouette glows, not where an arm crosses the chest), and a
  stencil lets each pixel glow once (so overlapping limbs do not stack into hot
  spots). Only its depth moves: pushing the point itself back would slide the
  outline towards the centre of the view, off the body. It is depth-tested like
  any geometry, so a wall hides the outline with the body: no seeing through
  buildings. It adds a few points of red (out of 255) to a body in a dark yard;
  **lurkers** — crawlers, spitters and howlers — get almost none (under 1):
  they are found with the flashlight. A worst-case horde with every outfit on
  screen costs 88 more draw calls.
- **The survivor** is a voxel model — `Character_Hero.fbx` from a voxel
  apocalypse asset pack — baked offline by `tools/bake-hero.py` into a small
  table in the page (about 35 KB): 5 cm voxels, one palette colour per face,
  1,352 triangles. The source is one unrigged mesh in a T-pose, so the bake cuts
  it at the hips, knees, shoulders and elbows, splitting triangles that cross a
  cut, and swings the arms onto the gun with a two-bone reach so both hands land
  on the grip and foregrip. The legs animate with the same knee rule as the
  horde. Each of the five guns is its own model — rifle, pump shotgun, stubby
  SMG, scoped marksman rifle, drum-fed launcher — with the muzzle flash and
  light at that gun's muzzle.
- **The ground** is a painted canvas texture — see [Oakhaven](#oakhaven).
- **Audio** is synthesised from oscillators and noise buffers.

This was originally a constraint — the page is published as a sandboxed artifact
that cannot fetch external media — but it keeps the whole game in one file with
zero network requests after the engine loads.

### Difficulty scales on three axes, damage included

Enemy health, speed **and damage** all scale with the Director's level:

```js
hpScale  = 1 + 0.135 * (level - 1)
spScale  = min(1.42, 1 + 0.022 * (level - 1))
dmgScale = 1 + 0.12  * (level - 1)
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
a combat one. A fully-maxed defensive build standing still in nine level-7
zombies now loses ~19 HP/sec.

### Post-processing: bloom, FXAA and the grade

Written by hand rather than with three.js `EffectComposer` + `UnrealBloomPass`,
which live in the examples bundle and would mean a second CDN fetch this page
can't guarantee. Four passes: scene into a render target, a bright-pass that
downsamples, a separable blur in two directions, then a composite.

- The bright-pass keys on **max channel, not luma**. This palette's highlights
  are saturated amber, which luma weighting under-reads and refuses to bloom.
- The composite also runs **FXAA**, which is load-bearing: rendering into a
  render target bypasses the canvas's MSAA entirely, so without it turning
  effects on would make edges *worse*.
- The composite ends with the **grade** that gives the night its grit: colour
  pulled 20% towards grey, the shadows crushed a touch and cooled, and a fine
  film grain that changes every frame. The grain is strongest in the midtones,
  so black stays black and the lamp pools stay clean. It runs on every quality
  tier; it is one hash per pixel.
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

### Recoil

Every shot kicks three things, each tuned per weapon in its `recoil` entry:

- **The model.** The gun pivots about the grip, so the muzzle climbs while the
  stock drives back, and the torso rocks back from the waist. It springs home
  in about 0.3 s.
- **The camera** is shoved back against the shot and springs home, instead of
  a random shake — the view jolts the way the gun does.
- **Accuracy.** Each shot adds a little spread (`bloom`) that bleeds off at the
  weapon's `recover` rate. Tapping stays accurate; holding the trigger on the
  SMG builds to about 2° extra and is gone within half a second of letting go.
  The shotgun and launcher kick hardest but have no bloom — their spread is
  already their character.

### Walking

The player's legs walk where the body is **going**, while the torso faces where
it **aims** — so strafing and backpedalling while shooting no longer moonwalk:

- Up to about 100° off the aim, the hips turn toward the movement (capped at
  ~50°, since nobody strafes with hips square to their direction). Past that it
  is a backpedal: the hips face the aim and the stride runs in reverse, a bit
  shorter.
- **Feet are planted.** The body's height each frame is whatever puts the lower
  foot on the ground, computed from the hip and knee angles. That produces a
  walk's natural bob — highest as the legs pass, lowest at full stride — with
  feet staying within 2 cm of the ground; a run adds a short flight.
- Walk and run blend by speed: a run folds the knee further through the swing,
  carries the thighs forward, counter-rotates the shoulders and leans in. Weight
  shifts over the stance leg; standing still, the body breathes and settles.

Zombies walk the same way with more character. Some shamblers and bloaters drag
a bad leg — it barely swings or bends, the body drops onto it each step, and the
cadence is uneven, hurrying off it. Most carry one arm lower; heads loll, each
at its own pace; brutes and bloaters stomp with a heavy roll; runners run.

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
Eight separate meshes per zombie times forty zombies is ~320 draw calls, which a
mobile GPU will not enjoy.

Instead there is one `InstancedMesh` per **body part per outfit**, and limb
world matrices are composed manually on the CPU each frame — the shin's is the
thigh's times its knee. Draw calls depend on which outfits are on screen, never
on how many bodies wear them, and outfits with nobody on screen are hidden. A
26-strong horde with every type and outfit on screen measures 160 scene draw
calls and 59k triangles (248 and 68k with the outlines).

A per-instance colour approach (`setColorAt`) would cut the calls further, but
it depends on the renderer recompiling its shader when `instanceColor` first
appears — behaviour that varies across three.js versions, and when it silently
fails every zombie renders pure white. Colour baked into each outfit's geometry
is boring and correct.

Other deliberate choices:

- **A fixed light count.** Four lamp lights, the torch, the muzzle flash and
  the blast light exist from the first frame, so nothing recompiles mid-fight.
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
groups with `SkinnedMesh` clones, or keep instancing and swap the per-outfit
part geometries (`zTorso`, `zHead`, `zArm`, `zThigh`, `zShin`) for meshes
extracted from a loaded model. The animation code drives
limb transforms by name, so it maps onto a real rig without restructuring the
game loop.

## Licence

MIT — see `LICENSE`.
