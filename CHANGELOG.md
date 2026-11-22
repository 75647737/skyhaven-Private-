# Changelog

## 2026-11-22
- Ace idle: `blender/characters/ace_v007.blend` adds `Ace_idle_loop`, a 10 s looping action (relaxed arms, breathing, weight shift, head turns, eye glances, blinks incl. a double blink). Stills in `characters/3d/ace_v007_idle_*.png`.
- Fix v006: his body shape keys had been reset to 0, losing his build under the clothes; values restored from v005. Removed the v006 pose test image, which showed that bug.
- Ace rigged for animation: `blender/characters/ace_v006.blend` replaces v005's plain MPFB skeleton with a Rigify control rig (`Ace.rig`: IK/FK limbs, fingers, full face controls). Clothes, hair, brows, lashes, eyes, teeth and tongue all follow it; teeth split upper/lower, each eyeball on its own eye bone. Face test screenshot `characters/3d/ace_v006_rig_test_face.png`. Details in `blender/characters/README.md`.

## 2026-11-21 (cloud session)
- Ace Sterling rebuilt as a realistic human avatar with MPFB2 and CC0 MakeHuman assets: `blender/characters/ace_v005.blend` (rigged, 93 face shape keys incl. blinks, brows and visemes; textures packed). Build script `tools/blender/build_ace.py`, model sheet `characters/3d/ace_v005_model_sheet.jpg`. Notes and licences in `blender/characters/README.md`.

## 2026-11-21
- Repository created: blueprint, folder layout, Git LFS for .blend, 2D model sheet and rig, three.js 3D test, 2D pilot "The Call" with voices.
