# Breakfast test (Episode 1, scene 2 sketch)

A 33-second test of the cartoon family with dialogue, lip-sync and expressions.
Scene file: `blender/episodes/tests/breakfast_v001.blend`.

| Shot | Frames | What happens |
|---|---|---|
| 1 Kitchen, stove | 1–239 | Tori cooks one egg with Max on her hip. "One egg, two plates... We'll make it work. Won't we, Max?" Max giggles. She puts the spatula down, goes to the doorway: "Ace! Breakfast is ready!" |
| 2 Living room | 240–399 | Ace sketches a drone on a napkin. "Coming, love! Just... one more line." He walks off to the kitchen. |
| 3 Kitchen, table | 400–792 | Tori at the table with Max on her lap. Ace: "Good morning, my little pilot!" Max: "Da-da!" Ace sits, puts the napkin down. Tori: "Still dreaming?" Ace: "Still planning." (wink) Tori: "Eat, before it gets cold." Max claps. |

## Voices (ElevenLabs, `eleven_multilingual_v2`)

| Character | Voice | voice_id |
|---|---|---|
| Ace | Will (relaxed optimist) | `bIHbv24MWmeRgasZH58o` |
| Tori | Sarah (mature, reassuring) | `EXAVITQu4vr4xnSDxMaL` |
| Max | Piku (expressive kid) | `EeQEodFZVtBkjtgK3HBc` |

Lines and voice settings: `dialogue.json`. Regenerate with
`python tools/audio/elevenlabs_tts.py episodes/breakfast-test/dialogue.json --force`
(the key comes from `ELEVENLABS_API_KEY` or `~/.skyhaven/elevenlabs_key.txt`; never commit it).
Each line gives `voices/<id>.mp3` and `voices/<id>.json` with per-character start/end times, which
`tools/blender/anim_breakfast.py` turns into mouth-shape keys.

## Rebuild the animation

Open the scene in Blender, run `tools/blender/dress_breakfast.py` (set dressing) and then
`tools/blender/anim_breakfast.py` (all acting, lip-sync, cameras, sound strips). Line start
frames are in `LINES` at the top of the animation script.
