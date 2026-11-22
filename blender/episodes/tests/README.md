# Test scenes

## `ace_sit_mug_test.blend` — Ace sits down and drinks tea

An 8-second (192 frames, 24 fps) action test for the breakfast scene: Ace stands at a table, sits down, looks at his mug, picks it up, drinks, lowers it and smiles.

| | |
|---|---|
| Ace | **linked** from `../../characters/ace_v007.blend` (collection `Ace`) with an editable library override. Fixes to the master file show up here on reload. |
| Action | `Ace_sit_mug` on `Ace.rig`. Arms are in IK for this shot (`IK_FK` = 0) so the right hand can be placed exactly on the mug; legs stay IK so the feet stay planted while he sits |
| Mug | handle turned toward his right hand (mug rotated −96°). `PROP_mug` has a Child Of constraint ("Held by Ace") to `ORG-hand.R`; its influence switches from 0 to 1 at frame 106, when his fingers have closed on the handle |
| Grip | a real mug hold: index and middle fingers hooked through the handle, thumb resting on top of the handle, ring and little fingers tucked under. The hand pose is stored relative to the mug, so every hand key after the grab is "mug pose × grip" and the grip never slips |
| Drink | matched to a reference photo of a relaxed sip. The cup is brought to the mouth: the rim rests on the lower lip (`lip.B`) and the cup follows the direction his face points. While drinking, the handle faces forward and to his right (62° off his face direction), so his hand is in front and to the side of the cup with the knuckles out. His wrist sits just below the rim, the forearm rises diagonally, and the elbow is out to the side, in front of and below the shoulder. Gentle tilt: 6° → 16° → 26° → 31° → 16°. He settles back into the chair, keeps his head nearly upright (up to 5°) and turns it to his left (up to 15°), eyes open and gazing out. Jaw opens 2° |
| Face | blinks (frames 16, 74, 148, 178), eyes open while drinking, smile from frame 150 using the lip corner controls (`lip_end.*.001`) |
| Set | `Set_breakfast_test`: placeholder table, chair, mug of tea, floor and two walls built from simple shapes, warm morning sun and a cool fill light, camera `CAM_test` |

Timeline: 1–12 stand · 12–60 sit down · 60–84 settle and look at the mug · 84–104 reach and grab · 104–140 lift and drink · 140–166 lower the mug · 166–192 hold, smile, look up.

### Things this test found
- **Hand axes on Ace's rig** (important for any hand pose): fingers point along the hand's local **Y**; the knuckles run along **Z** (index side +Z); the palm faces **−X on the right hand** and **+X on the left**. Finger master controls (`f_*.01_master`) curl toward the palm with **+X** rotation.
- The first mug prop had its body 4.75 cm lower than its handle and tea (origin in the middle of the cup); fixed so the origin is at the base.
- **Face shape keys can't be animated in a scene that links Ace**, because the mesh and its shape keys stay linked. Use the rig's face controls in scenes, or (next step for the master file) add rig custom properties that drive the ARKit shape keys so they become animatable through the override.
- **Elbow placement:** with IK arms the elbow sits wherever the shoulder–wrist geometry allows, so put the *hand* where a person would (beside and slightly under the cup) and the elbow follows. Rotating `upper_arm_ik.R` on its Y axis swings the elbow around that line for fine-tuning.
- **Lifting to the mouth:** with only a few keys, the IK elbow tucked back against the ribs and then jumped up (seconds 4–5 of the first version). The lift is now keyed every 2 frames (106–128): the cup follows one curved path that rises close to the body and then comes in to the lips, it turns gradually from the table grip to the drinking angle, and the elbow swing (`upper_arm_ik.R` Y) is solved per frame so the elbow travels smoothly forward and up. Keep big lean changes slow; leaning back fast while lifting looked like a jolt.
- The tea surface tilts with the mug instead of staying level; it's hidden at the lips in this shot, but a close-up would need the liquid kept level.

The set pieces are placeholders; swap them for BlenderKit or Poly Haven furniture when the real flat is built.
