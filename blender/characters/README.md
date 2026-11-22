# Master characters

## Ace Sterling, rigged (`ace_v006.blend`) — use this one

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
