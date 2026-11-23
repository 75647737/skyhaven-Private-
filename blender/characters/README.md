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

## Victoria "Tori" Sterling (`tori_v004.blend`) — use this one

v004: refined to read as a warm wife and mum rather than a glamour look.
- **Softer lips:** natural rose (#b4645e) kept inside the lip line (`lip_tighten` map range on the lip mask), slightly thinner lips; gentle resting smile (`mouth-angles-up` 0.55); softer brown brows.
- **Modest neckline:** dress rebuilt with the V bottom at 1.26 m (was 1.195); weights redone (body transfer + hip/thigh skirt blend).
- **Hair:** soft waves restored (v003's smoothing had flattened them).
- **Postures** (actions with fake users; all keep the heels stance and use IK arms): `Tori_pose_relaxed` (hands softly clasped in front, weight on one leg, head tilt, smile), `Tori_pose_hand_on_hip` (left hand on the waist under the belt, hip shift), `Tori_pose_wave` (right hand raised in greeting, big smile). Assign one to `Tori.rig` (or as an NLA strip) to use it; `Tori_heels_stance` is the neutral default.

### v003

v003 adds to v002:
- **Face controls:** the 52 ARKit face units (`eyeBlinkLeft`, `mouthSmileLeft`, `browInnerUp` …) and 22 Microsoft visemes (`aa_ah_ax_01`, `f_v_18` …) from the CC0 MakeHuman packs `faceunits01` and `visemes01`, as shape keys on `Tori.body`. Each is driven by a slider on the rig, `Tori.rig["face_<name>"]` (0–1, library-overridable), so scenes that link Tori can animate them. If a driver ever shows as invalid, set `driver.is_valid = True` and change frame.
- **Hairline:** 1,400 strands added along a smooth line up to 1.2 cm below the old hairline; each copies the sweep of its nearest strand.
- **Shoes:** rebuilt with a 6.2 cm heel counter and 4 cm sides; opening edge smoothed along itself. Sides under the arch are still low.
- **Hair back:** strands smoothed below the top 30 %, removing the band at shoulder height.

### v002

v002 adds to v001 below: Rigify rig `Tori.rig` (MPFB, 930 bones); dress, straps and belt weighted from the body, the skirt blended between `DEF-spine` and both thighs so it stays one piece; eyes on `DEF-eye.*`, lashes split per side on `DEF-lid.T.*.002` (they close with blinks), hair and brows on the head bone. Nude pumps (#d8bf94, `Tori.shoe.*` + heel posts) bone-parented to the feet. Action `Tori_heels_stance` (feet rolled 38° on `foot_heel_ik`, torso up 6 cm) is her default stance — keep it in every scene so the heels touch the floor. Everything is in the `Tori` collection for linking.

### v001 notes

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

## Ace cartoon versions (style test)

- **2D:** `characters/2d/ace_cartoon.html` (renders to `ace_cartoon_sheet.png`): original cartoon model sheet — front view, four expressions (easy smile, still planning, surprised, tired), palette from the blueprint, 5-heads-tall proportions vs the realistic 8.
- **3D toon:** `ace_toon_v001.blend` — a copy of `ace_v007.blend` with flat 3-tone cel materials (emission through Shader to RGB + constant ramp), an inverted-hull outline (Solidify, flipped normals, `TOON_outline` material) and bigger eyes. Rig, idle and face controls are unchanged. Proportions are still realistic: scaling the head by pose bones or a shape key tore the Rigify face, so a true big-head 3D cartoon Ace needs a new head mesh built from the 2D sheet.

### Cartoon Ace, face that turns (`ace_cartoon_v005.blend`) — face test, Ace only

Built from v004 by `tools/blender/build_ace_face.py`; review sheets by `tools/blender/face_views.py` (`blender -b <file> --python tools/blender/face_views.py -- AC <out_dir> [tag]`).

| | |
|---|---|
| Head | `AC.head` re-sampled from v004's head (same skull and hairline) at high resolution, then given a continuous profile: forehead, soft brow ridge, a nose sculpted into the head (bridge from between the eyes, rounded tip, nostril wings, turned-under base), philtrum, upper lip, mouth line, lower lip, chin, and a jaw brought forward of the old egg shape. The old `AC.nose` blob is hidden. |
| Ears | `AC.ear.L/R` rebuilt: outer rim (helix) from above the tragus round to the lobe, a Y-shaped inner fold (antihelix), a darker bowl (concha, `AC_skin_fold`), tragus, fleshy lobe; outlined so the folds draw; splayed forward a little so they read from the front. |
| Nose | modelled after the reference faces: a soft, wide, low bridge, a big round bulb tip that turns under, wide full wings level with the inner eye corners. `AC.nostrils` (two dark openings under the bulb, seen from the front and three-quarter) and `AC.nose_fold` (a curved crease round each wing, the lines a cartoon nose is drawn with). |
| Attached features | eye whites, irises, pupils, highlights, brows, nostrils, nose fold and every mouth piece have an `OnFace` Shrinkwrap (mouth lines, nostrils and nose creases are projected straight along the face's forward axis, so thin lines stay clean on the lips) onto `AC.head_surface` (a twin of the head that shares its mesh and shape keys but is invisible to camera and shadows), so they lie on the curve of the face and stay on it through turns, blinks and jaw moves. The eye parts are single front sheets now, each eye white has a dark rim (`AC.eye_rim.L/R`) on the same eye bone, so blinks still work. |
| Mouth rig | the face itself moves with the `mouth` slider (0 smile, 1 rest, 2 A, 3 E, 4 O, 5 U/W, 6 M/B/P, 7 F/V, 8 frown): head shape keys `jaw_open`, `lips_round`, `lips_press`, `lip_tuck`, `smile`, `frown` are driven from it, on top of the existing mouth shapes. `blink`, `look_x/y`, `brows`, `brow_tilt` unchanged (same names and ranges, so the breakfast lip-sync keys should drive it; not yet re-run on v005). |

Sheets: `characters/3d/ace_v005_turn.png` (front, three-quarter, side), `ace_v005_turn_close.png` (the same, face filling the frame), `ace_v005_mouth.png` (nine mouth shapes, front, three-quarter and side), `ace_v005_expr.png` (happy, talking, surprised, cross, worried, blink in front and three-quarter); `ace_v004_turn.png` is the before.

### Cartoon Ace, short version (`ace_cartoon_v001.blend`) — the chosen cartoon style

Short and chunky, about 2½ heads tall (1.04 m), built in Blender straight from the 2D sheet's measurements (1 sheet unit = 2.5 mm). Simple rounded shapes: big head with large eyes (white, iris, pupil, highlight), curve brows and smile, hair cap with a front hairline, sweater with collar, hem and cable lines, mitt hands, short legs, rounded shoes. Flat 3-tone cel materials (`AC_*`) and an inverted-hull outline (`AC_outline`).
Rig `AC.rig`: root, hips, chest, head, arm/hand and leg/foot per side; every part is bone-parented (rigid), so posing is quick. Polished: rounded tapered sleeves with cuffs; mitt hands with a thumb on the same bone as the sleeve, so they never separate; a fringe showing his side part; face features, brows and sweater cables snapped onto the real surfaces; full hair at the back. Turnaround (front, three-quarter, side, back): `characters/2d/ace_cartoon_turnaround.png`.

#### Cartoon Ace rig and controls

Bones (`AC.rig`): root, hips, chest, head; per side `upper_arm`, `forearm`, `hand`, `thumb`, `leg`, `foot`; face bones `eye`, `pupil`, `brow` per side and `mouth`. The sweater sleeve is one mesh skinned to upper arm + forearm (smooth bend at the elbow); cuff, mitt hand and thumb ride on forearm / hand / thumb.

Face sliders are custom properties on `AC.rig` (keyframe them like any value):

| Slider | Range | Does |
|---|---|---|
| `mouth` | 0–8 | 0 smile, 1 rest, 2 A (ah, ai, i), 3 E (ee), 4 O, 5 U/W, 6 M/B/P, 7 F/V, 8 frown. Key with **Constant** interpolation for lip-sync |
| `blink`, `blink_L`, `blink_R` | 0–1 | both eyes / wink |
| `look_x`, `look_y` | −1–1 | pupils right/left, up/down (screen directions when he faces camera) |
| `brows` | −1–1 | brows down / up |
| `brow_tilt` | −1–1 | angry (−) / worried (+) |

The drivers use no Python expressions (only `max`/`min` for blink, otherwise a plain slider input mapped through an F-curve), so they work even with "Auto Run Python Scripts" off. Don't hide `AC.rig` from renders: that also stops the face bones from updating in the render.

Test action `AC_wave_talk` (96 frames): right-arm wave with elbow and wrist, head tilt, brows up, two blinks, talking mouth.

### Cartoon Tori (`tori_cartoon_v001.blend`) — matches cartoon Ace

Built from `characters/2d/tori_cartoon.html` (2D model sheet: front view, four expressions, palette, proportions, turnaround) and from a copy of `ace_cartoon_v001.blend`, so she has the **same rig and the same face sliders** (`mouth` 0–8, `blink`, `blink_L/R`, `look_x/y`, `brows`, `brow_tilt` on `TC.rig`). About 2½ heads tall and 5 % shorter than cartoon Ace (rig scaled 0.95).

Her look: rounder jaw, long chestnut hair (one shell behind the head with a wavy hem at the shoulders) plus the side-swept fringe, three lash flicks per eye (on the eye bones, so they close with blinks), blush, lip-coloured mouth lines, bare slim arms with mitt hands, terracotta dress (#c96f53) with puff sleeves, V neckline and a navy belt (#3d4a63), legs and nude low heels (#d8bf94). Test action `TC_wave_talk` (left-hand wave, talk, blinks). Turnaround: `characters/2d/tori_cartoon_turnaround.png`.

Known rough spots: the nose sticks out a little in profile, and her hair is one smooth shape (no individual waves yet).

### Eyes seated (`ace_cartoon_v003.blend`, `tori_cartoon_v003.blend`) — use these

v002 with the eyes, irises, pupils, highlights, brows and lashes pulled back onto the face (`tools/blender/fix_eyes.py`), so they no longer stick out in profile. Everything else is the same as v002. Baby Max is now `max_cartoon_v002.blend` (see below; built from Ace v003 by `build_max.py`, which also runs the eye fix).

### Fingers (`ace_cartoon_v002.blend`, `tori_cartoon_v002.blend`)

v001 plus real hands: a rounded palm (`*.hand.L/R`), four fingers (`*.finger_index/middle/ring/pinky.L/R`) and a rebuilt thumb, all bone-parented. Each finger has its own bone under `hand.*` (Euler XYZ): **curl = negative X** (about −0.4 relaxed, −1.4 fist), spread = Z. Built by `tools/blender/add_fingers.py` (re-runnable; `HAND_SCALE`, `FINGER_LEN`, `FINGER_FAT`, `PALM_START` overrides).

### Baby Max (`max_cartoon_v001.blend`) — Episode 1 age

Ace and Tori's son, about 1 year old, built from cartoon Ace by `tools/blender/build_max.py` (`blender -b blender/characters/ace_cartoon_v002.blend --python tools/blender/build_max.py -- <out.blend> [preview_dir]`). Same rig and face sliders (`MX.rig`, object scale 0.72, about 0.62 m tall); Ace's head and face parts moved down onto a baby body, nose 72 %, thinner brows, default `brows` 0.35 / `brow_tilt` 0.3 for a softer look.

Look (blueprint palette): skin #dba67c, light-blue babygrow #a7c7e7 with footies and white soles, white round collar, chubby sleeve "sausages" on the arm bones, short chubby fingers, messy dark hair #3b2416 (cap plus nine flicks), blush, small navy aeroplane patch on the chest (no logo). Everything is in the `MaxCartoon` collection for linking; `MX_wave_talk` is kept as a test action.

To grow him for later episodes, change `RIG_SCALE`, `DZ` and the bone positions in the script and save the next version.
