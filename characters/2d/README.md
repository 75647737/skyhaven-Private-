# Skyhaven characters (2D puppet rig)

- `rig.js`: one shared drawing rig. Every character is built from the same parts (head, eyes, brows, mouth, hair, torso, arms, legs, props), so a character looks identical in every episode. There is no AI and no Modal.
- `sterlings.js`: the Sterling household model sheet (fixed colours, heights, hair, outfits). If you change a value here, it changes in every scene.
- `lineup.html` renders to `sterlings-lineup.png` (3000×1500).
- Animation hooks: `draw(spec, {mouth:'smile'|'open'|'o'|'grin', blink:0..1, armL, armR, look})`. Lip-sync swaps the mouths, blinks use `blink`, and gestures rotate the arms at the shoulder.

Original designs for Skytrade Aviation. Not based on any existing cartoon.
