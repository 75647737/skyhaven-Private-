# Test scenes

## `ace_sit_mug_test.blend` — Ace sits down and drinks tea

An 8-second (192 frames, 24 fps) action test for the breakfast scene: Ace stands at a table, sits down, looks at his mug, picks it up, drinks, lowers it and smiles.

| | |
|---|---|
| Ace | **linked** from `../../characters/ace_v007.blend` (collection `Ace`) with an editable library override. Fixes to the master file show up here on reload. |
| Action | `Ace_sit_mug` on `Ace.rig`. Arms are in IK for this shot (`IK_FK` = 0) so the right hand can be placed exactly on the mug; legs stay IK so the feet stay planted while he sits |
| Mug | handle turned toward his right hand (mug rotated −96°). `PROP_mug` has a Child Of constraint ("Held by Ace") to `ORG-hand.R`; its influence switches from 0 to 1 at frame 106, when his fingers have closed on the handle |
| Grip | a real mug hold: index and middle fingers hooked through the handle, thumb resting on top of the handle, ring and little fingers tucked under. The hand pose is stored relative to the mug, so every hand key after the grab is "mug pose × grip" and the grip never slips |
| Drink | the mug is brought to the mouth, not the mouth to the mug: the rim rests on the lower lip (`lip.B`), the mug tips toward his face from 10° to 28°, 48° and 56° for the sip, then back. His head tilts back up to 15°, his jaw opens 4°, and his eyes half close. Then he lowers it upright to chest height |
| Face | blinks (frames 16, 74, 178), eyes half-closed while drinking (134–146), smile from frame 150 using the lip corner controls (`lip_end.*.001`) |
| Set | `Set_breakfast_test`: placeholder table, chair, mug of tea, floor and two walls built from simple shapes, warm morning sun and a cool fill light, camera `CAM_test` |

Timeline: 1–12 stand · 12–60 sit down · 60–84 settle and look at the mug · 84–104 reach and grab · 104–140 lift and drink · 140–166 lower the mug · 166–192 hold, smile, look up.

### Things this test found
- **Hand axes on Ace's rig** (important for any hand pose): fingers point along the hand's local **Y**; the knuckles run along **Z** (index side +Z); the palm faces **−X on the right hand** and **+X on the left**. Finger master controls (`f_*.01_master`) curl toward the palm with **+X** rotation.
- The first mug prop had its body 4.75 cm lower than its handle and tea (origin in the middle of the cup); fixed so the origin is at the base.
- **Face shape keys can't be animated in a scene that links Ace**, because the mesh and its shape keys stay linked. Use the rig's face controls in scenes, or (next step for the master file) add rig custom properties that drive the ARKit shape keys so they become animatable through the override.
- The tea surface tilts with the mug instead of staying level; it's hidden at the lips in this shot, but a close-up would need the liquid kept level.

The set pieces are placeholders; swap them for BlenderKit or Poly Haven furniture when the real flat is built.
