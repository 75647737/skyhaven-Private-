# Test scenes

## `ace_sit_mug_test.blend` — Ace sits down and drinks tea

An 8-second (192 frames, 24 fps) action test for the breakfast scene: Ace stands at a table, sits down, looks at his mug, picks it up, drinks, lowers it and smiles.

| | |
|---|---|
| Ace | **linked** from `../../characters/ace_v007.blend` (collection `Ace`) with an editable library override. Fixes to the master file show up here on reload. |
| Action | `Ace_sit_mug` on `Ace.rig`. Arms are in IK for this shot (`IK_FK` = 0) so the right hand can be placed exactly on the mug; legs stay IK so the feet stay planted while he sits |
| Mug | `PROP_mug` has a Child Of constraint ("Held by Ace") to `ORG-hand.R`; its influence switches from 0 to 1 at frame 102, the moment his hand closes on it |
| Face | blinks (frames 16, 74, 178), eyes half-closed while drinking (134–146), smile from frame 150 using the lip corner controls (`lip_end.*.001`) |
| Set | `Set_breakfast_test`: placeholder table, chair, mug of tea, floor and two walls built from simple shapes, warm morning sun and a cool fill light, camera `CAM_test` |

Timeline: 1–12 stand · 12–60 sit down · 60–84 settle and look at the mug · 84–104 reach and grab · 104–140 lift and drink · 140–166 lower the mug · 166–192 hold, smile, look up.

### Things this test found
- **Finger curl axis:** on this rig the finger master controls (`f_*.01_master`) curl toward the palm on their **Z** axis, and the thumb on **X**.
- **Face shape keys can't be animated in a scene that links Ace**, because the mesh and its shape keys stay linked. Use the rig's face controls in scenes, or (next step for the master file) add rig custom properties that drive the ARKit shape keys so they become animatable through the override.
- The grip is first-pass: from the shot camera it reads as holding the mug, but close up the hand sits a little high on the mug.

The set pieces are placeholders; swap them for BlenderKit or Poly Haven furniture when the real flat is built.
