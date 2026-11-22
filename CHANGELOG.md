# Changelog

## 2026-11-22
- Breakfast test made to feel directed and lived in: window with sunrise and skyline, floor lamp, picture, ticking clock, bookshelf, plant, rug; teapot, toast, saucer and the napkin drone sketch on the table. Soft warm window key, low sun, dim cool fill, lamp practical and rim light. Slow push-in on the wide camera with a cut to a close-up for the sip. Face acting: smiles, brow lifts, extra blinks, and an end turn back to the cup and sketch.
- Mug test: fixed the awkward lift at seconds 4–5 (elbow tucked back then jumped up, body jolted back). The cup now follows one smooth curved path close to the body, keyed every 2 frames, with the elbow swing solved per frame and the lean back spread over a second.
- Sip matched to a reference photo: cup follows his face, handle forward-right so the hand sits in front of and beside the cup with the knuckles out, elbow out to the side and below the shoulder, gentle tilt (max 31°), relaxed lean back, head nearly upright and turned to look out, eyes open.
- Mug test reworked for a human grip and drink: handle turned to his right hand, index and middle fingers through the handle with the thumb on top, hand keyed relative to the mug so it never slips; rim placed on the lower lip, mug tipped 10° → 56° for the sip, head tilts back, jaw opens, eyes close; arms hang naturally when standing. Fixed the hand axes used for all hand poses, and the mug prop (body was 4.75 cm too low). Close-ups in `characters/3d/tests/`.
- First action test: `blender/episodes/tests/ace_sit_mug_test.blend` links Ace v007 (library override) and animates him sitting down at a table, picking up a mug and drinking (8 s). Notes in `blender/episodes/tests/README.md`. Ace's master collection renamed to `Ace` (widgets in `WGTS_Ace.rig`) so it can be linked.
- Ace idle: `blender/characters/ace_v007.blend` adds `Ace_idle_loop`, a 10 s looping action (relaxed arms, breathing, weight shift, head turns, eye glances, blinks incl. a double blink). Stills in `characters/3d/ace_v007_idle_*.png`.
- Fix v006: his body shape keys had been reset to 0, losing his build under the clothes; values restored from v005. Removed the v006 pose test image, which showed that bug.
- Ace rigged for animation: `blender/characters/ace_v006.blend` replaces v005's plain MPFB skeleton with a Rigify control rig (`Ace.rig`: IK/FK limbs, fingers, full face controls). Clothes, hair, brows, lashes, eyes, teeth and tongue all follow it; teeth split upper/lower, each eyeball on its own eye bone. Face test screenshot `characters/3d/ace_v006_rig_test_face.png`. Details in `blender/characters/README.md`.

## 2026-11-21 (cloud session)
- Ace Sterling rebuilt as a realistic human avatar with MPFB2 and CC0 MakeHuman assets: `blender/characters/ace_v005.blend` (rigged, 93 face shape keys incl. blinks, brows and visemes; textures packed). Build script `tools/blender/build_ace.py`, model sheet `characters/3d/ace_v005_model_sheet.jpg`. Notes and licences in `blender/characters/README.md`.

## 2026-11-21
- Repository created: blueprint, folder layout, Git LFS for .blend, 2D model sheet and rig, three.js 3D test, 2D pilot "The Call" with voices.
