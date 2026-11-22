# Master characters

## Ace Sterling, rigged with idle (`ace_v007.blend`) — use this one

v006 plus a looping idle action, so he never stands frozen.

| | |
|---|---|
| Action | `Ace_idle_loop` on `Ace.rig` (fake user, so it is kept even when unassigned). 240 frames = 10 s at 24 fps, frames 1 and 241 match, every curve has a Cycles modifier so it loops forever |
| Base pose | arms down and relaxed (arms in FK, `IK_FK` keyed to 1), soft elbows, hands turned slightly in. Legs stay IK so the feet stay planted |
| Breathing | 3 breaths per loop (every 80 frames): chest lifts about 1°, shoulders rise about 1.6° |
| Weight shift | one slow hip-to-hip shift per loop: torso slides ±9 mm, hips tilt about 1.8°, chest counter-tilts |
| Head | small turns and tilts at frames 60, 130, 190 (up to 7°), neck takes about a third |
| Eyes | quick glances (3-frame moves, then holds) just before each head turn, via `eye_common` |
| Blinks | at frames 34, 98 + 105 (double blink), 168, 222: close in 2 frames, hold 1, open in 4. Done with the lid controls, so the lashes follow |

In an episode file, link Ace, make a library override, and add `Ace_idle_loop` as an NLA strip under any acting; key acting on top in a new layer.

Preview: `ace_v007_idle_preview.mp4` (viewport render, 960×540) was made from this file; it is not stored in the repo.

## Ace Sterling, rigged (`ace_v006.blend`)

**Fixed 2026-11-22:** the first v006 had all body shape keys set to 0, which removed Ace's body shape (MPFB keeps his build and face proportions as shape keys), so the body under the clothes was the plain MakeHuman base and didn't match the clothes. The 21 shape key values are now copied back from v005.

v005 below with a **Rigify control rig** in place of the plain MPFB skeleton, so he can be animated.

| | |
|---|---|
| Rig | `Ace.rig`: Rigify human rig made with MPFB (*Add rigify rig*, no toe bones), 930 bones, 181 deform bones |
| Body | IK/FK arms and legs (IK by default; `IK_FK` slider on `upper_arm_parent` / `thigh_parent`), torso, neck, head, fingers |
| Face | Rigify face controls: brows, lids (blinks move the lashes too), cheeks, nose, lips, jaw, tongue, eyes and eye target |
| Shape keys | the same 96 on `Ace.body` (ARKit face units + visemes), still usable on top of the rig |
| Attached | body, sweater, trousers, shoes, hair, brows, lashes, eyes, teeth, tongue — all parented to `Ace.rig` with an Armature modifier |
| Rest pose | MPFB A-pose; nothing is keyed |

How the pieces were weighted: the body uses MPFB's Rigify weights. Clothes, hair, brows, lashes and tongue got their weights from the body (nearest surface, including MPFB's hidden helper geometry). Each eyeball follows only its own `DEF-eye` bone. The teeth keep v005's upper/lower split: upper on `DEF-teeth.T`, lower on `DEF-teeth.B`. The hidden `Ace.body.metarig` is kept so the rig can be regenerated.

Checked in Blender: arms, elbows and head posed without tearing; jaw opens with the lower teeth; the top lid control closes the eye and the lashes follow.

Known look issues carried over from v005: a few stray hair strands at the right temple; hair is slicked back rather than side-parted.

## Ace Sterling (`ace_v005.blend`)

Realistic human avatar (not toon), built with **MPFB2** (MakeHuman for Blender) in Blender 5.3. One base body; clothes, body size, eyes and hair change per season by editing the settings block in `tools/blender/build_ace.py` and rebuilding.

| | |
|---|---|
| Height / build | 1.80 m, ~30 years, broad build |
| Skin | warm brown; renders at ~#b28362 (blueprint #c68a5e read orange on realistic skin, same hue kept) |
| Hair | MakeHuman `short04` (side-parted), #2a1a12 |
| Eyes | brown, slightly enlarged |
| Clothes | fisherman sweater #5b7a99, wool trousers #8f7f62, shoes #3a2418 |
| Rig | MPFB `default` skeleton |
| Face | 93 shape keys: 52 ARKit-style face units (`eyeBlinkLeft`, `browInnerUp`, `mouthSmileLeft` ...) + Microsoft visemes for lip-sync |

Textures are packed into the .blend, so it opens anywhere.

### Rebuild or change him
1. Install the MPFB extension (Blender: Edit > Preferences > Get Extensions > "MPFB").
2. Install these MakeHuman asset packs (all **CC0**): makehuman_system_assets, skins01-03, eyebrows01, eyelashes01, hair01, shirts01, pants01, shoes01, suits01, suits02, underwear01, system_clothes_materials01, system_hair_materials01, glasses01, visemes01, faceunits01. Downloads: https://static.makehumancommunity.org/assets/assetpacks.html
3. Edit `ACE` / `PALETTE` in `tools/blender/build_ace.py`, then:
   `blender -b --python tools/blender/build_ace.py -- blender/characters/ace_v007.blend` (use the next free version number; the rebuilt file has the plain MPFB skeleton, so redo the Rigify step above)
4. Pack textures (File > External Data > Pack Resources) before committing.

### Licences
- MakeHuman base mesh, targets and the asset packs above: **CC0** (no credit required). Only CC0 packs are used.
- MPFB2 is a GPL-3.0 tool; it is not shipped in this repo, and characters made with it are not covered by the GPL.

## Victoria "Tori" Sterling (`tori_v001.blend`) — work in progress

Ace's wife. Look direction from the client: beautiful and feminine, curvy hourglass figure (narrow waist, fuller hips), long wavy brown hair, a fitted dress and heels. Reference photos were used for style only; the face is original.

| | |
|---|---|
| Body | MPFB2 (no MakeHuman asset packs on this PC): female, height macro 0.572 → 1.69 m; waist, hip, bust and buttock targets; face targets for an oval face, slimmer nose, cheekbones, almond eyes, gentle smile, slender neck. All values are shape keys on `Tori.body` |
| Skin | `Tori_skin`: procedural (noise-varied #dca07a–#eab690, subsurface, fine bump), lips coloured from MPFB's `lips` vertex group (`lip_mask` attribute) |
| Eyes | `Tori.eye.L/R`: spheres on MPFB's eye helpers, procedural brown iris, glossy coat |
| Hair | `Tori.hair`: 13,200 Blender hair curves grown by script from the `scalp` group — side part on her left, soft waves, collision with head/neck/shoulders, chestnut gradient (`Tori_hair`). `Tori.brows`, `Tori.lashes`: short curves on the skin surface |
| Dress | `Tori.dress`: original terracotta (#b85a44 / blueprint #c96f53) fitted bodice with V-neck and gathered bust, flared knee-length skirt; `Tori.dress_straps`; navy `Tori.belt` (#3d4a63) |
| Not done | heels, rig, face controls; straps don't quite meet the bodice; hairline sits a little high |

**Why not the MakeHuman packs:** their server in Sweden ran at 5–10 KB/s from this connection (1.1 GB ≈ two days) and BlenderKit's free library has no long hair, dresses or heels, so hair, brows, lashes, skin, eyes and dress were built in Blender.

**Store-Blender path limit:** MPFB fails on this PC with "target … does not exist" because the Microsoft Store Blender path is over 260 characters. Before using MPFB in a new Blender session run:
```python
from bl_ext.blender_org.mpfb.services.locationservice import LocationService as ls
r = r"C:\Users\DELL\AppData\Roaming\Blender Foundation\Blender\5.3\extensions\blender_org\mpfb"
ls._mpfb_data = r + r"\data"; ls._mpfb_root = r
```
