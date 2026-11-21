# SKYHAVEN: the series blueprint (handoff for the Blender session)

You are building an original 3D animated family series for **Skytrade Aviation** (private charter, www.skytradeaviation.com), made in **Blender 5.3** on the client's PC through the Blender MCP add-on. Read this whole file before building anything. It is the source of truth for story, cast, look and rules.

---

## 1. What the series is about

**Skyhaven** follows **Ace Sterling** from an ordinary young dad with a big dream to the founder of a successful company, and eventually to a family who flies private with Skytrade.

- **One episode = one year of their life.** Never put "Year 1", "Year 2" on screen. The audience works out that time has passed from clues: baby Max grows, the car gets older or replaced, the calendar on the wall, the company gets bigger, the flat becomes a house.
- **Every episode ends with that year's win**, a real step forward in building the company.
- **The message:** how many millionaires are made today. It isn't luck. It's ownership (building or investing in a company), risk, patience, a supportive family, and a plan once success arrives. Keep it honest and warm, never "get rich quick".
- **Skytrade's role:** it grows over the seasons. First a jet flying over the city that Ace looks up at, then a dream, then the family's first charter, and later the hangar, crew and fleet as regular settings. It should never feel like an advert.
- **Audience:** global families on YouTube (16:9), with 9:16 clips for TikTok and Reels. English only.

## 2. Episode 1: "The Dream" (the first year, about 3–4 min). START HERE

One ordinary day in the life of the young Sterling family, ending with their first win.

| # | Scene | What happens |
|---|---|---|
| 1 | **6:00, a small flat** | Alarm. Baby Max cries. Ace stumbles out of bed; Tori is already up making tea. Small, cosy, slightly cramped. |
| 2 | **Breakfast** | A tight budget: one egg split two ways, a bill stuck on the fridge. Ace sketches a delivery drone on a napkin. Tori smiles: "Still dreaming?" Ace: "Still planning." |
| 3 | **Going to work** | Ace's old hatchback won't start on the first try. Second try works. He drives through Skyhaven's morning traffic. A Skytrade jet passes overhead and he watches it through the windscreen. |
| 4 | **The day job** | An open-plan office, a stack of paperwork, a strict boss. At lunch Ace calls his friend **Leo**: "Tonight. The garage." |
| 5 | **Evening, the garage** | Ace and Leo build a drone prototype; Tori watches with Max in her arms. First test flight: the drone wobbles and crashes into a paint tin. |
| 6 | **Late night** | Ace sits alone, tired, ready to quit. Tori brings two mugs of tea: "Again. Tomorrow." |
| 7 | **The win** | A new morning. The drone lifts off and carries a tiny parcel across the yard and lands at Tori's feet. Baby Max claps. Ace and Leo hug. On the garage wall, a hand-painted sign goes up for their new company. |
| 8 | **Hook** | Fade on the drone flying over Skyhaven at sunrise, with a Skytrade jet far behind it in the sky. |

The start-up name is still open. Pick a made-up name and check that it isn't a real company. Voices come later from ElevenLabs, generated in the cloud session; you build picture and timing.

**First milestone:** get Ace, Tori and baby Max finished as master characters, plus the flat (bedroom and kitchen). A test scene already exists: `skyhaven_kitchen_test.blend` (kitchen, Ace with rig, 72-frame walk). Improve it rather than starting over.

## 3. The cast (fixed looks; reuse exactly)

### The Sterlings ("before" years: ordinary clothes)
| Character | Look | Colours |
|---|---|---|
| **Ace Sterling**, dad, about 30, dreamer and builder | broad build, warm brown skin, short dark side-parted hair, big friendly eyes, about 1.80 m | skin #c68a5e, sweater #5b7a99, khaki trousers #8f7f62, brown shoes #3a2418, hair #2a1a12 |
| **Victoria "Tori" Sterling**, mum, practical and keeps the budget | slim, long wavy brown hair, about 1.68 m | skin #f0c6a0, cardigan #c96f53, trousers #3d4a63, shoes #d8bf94, hair #7a4a24 |
| **Max Sterling**, baby in Ep 1, grows each episode | curious, messy dark hair | skin #dba67c, babygrow #a7c7e7, hair #3b2416 |
| **Leo**, Ace's best friend and co-founder | slim, glasses, messy light-brown hair, green hoodie | skin #e3ad84, hoodie #6d8a4e, glasses #1c1c1c |
| **The boss**, Ep 1 only | grey suit, stern | your choice, keep muted |

### Later seasons (do not build yet)
- **Rich-years Sterlings:** Ace in a navy suit with a red tie, Tori with a pearl necklace, Lily (daughter, born later), Grandma Rose, Duke the fluffy dog.
- **Household staff:** nannies Martha, Chloe and Grace; drivers Henry and Jake.
- **The Carters** (middle-class neighbours): Daniel, Emma, Noah (wants to be a pilot), Ollie, Grandpa Joe.
- **The Skytrade team:** Captain James, Officer Sophie, Ryan (helicopter pilot), Sam (engineer), Olivia (trip planner), Ethan (cabin host), Tom and Ben (ground crew).
- **The fleet:** Skye (light jet), Atlas (long-range jet), Hummingbird (helicopter), Ranger (turboprop). Navy and white livery with a thin red pinstripe, **no registrations**.

The 2D model sheet for the rich-years Sterlings (reference for later) is in the repo at `skytrade/cartoon/characters/sterlings-lineup.png`.

## 4. Look and style

- **Stylised 3D toon, warm and friendly.** Rounded shapes, slightly big heads and eyes, simple clean materials. Use toon or stylised shading in EEVEE, soft shadows and a light outline (Freestyle or Line Art).
- **Original design only.** It must not look like any existing cartoon or studio: no copying characters, art style, settings or music from existing shows or games.
- **Colour script:** warm golden mornings, cool blue nights, a warm tungsten garage. The palette leans navy, cream and terracotta, with a red accent that echoes Skytrade's colours.
- **Camera:** 16:9 at 1920×1080 and 24 fps for the episode. Keep important action in the centre third so 9:16 TikTok crops work.

## 5. It must feel alive (the most important note)

Static scenes are the main thing to avoid. Every shot needs life:
- **Characters never fully freeze:** idle breathing, blinks every 2–5 s, small weight shifts, eye darts, head tilts while listening.
- **Overlapping and secondary motion:** hair and clothing follow through, the coffee cup sways, keys jingle, the baby wiggles.
- **Acting:** clear poses and anticipation before big moves. Hold expressions long enough to read, then react.
- **Lip-sync:** mouth shapes (A/E/O/M/F) on the face rig, timed to the voice files once delivered.
- **The world moves:** steam from tea, curtains in the breeze, dust in sunbeams, a ticking clock, a flickering garage bulb, birds outside, clouds drifting, the sun shifting across the day.
- **Background life in the city:** cars driving, traffic lights changing, pedestrians walking, a dog on a lead, buses at stops, a plane crossing the sky. Use particles or geometry-node crowds and cars on simple paths.
- **Camera life:** gentle handheld drift on dialogue, slow push-ins on emotional beats, a smooth follow-cam on the car drive, and one hero aerial over Skyhaven.

## 6. Building the city of Skyhaven

**Skyhaven is a fictional city.** It should feel like a believable modern city (not a copy of a recognisable real one), with:
- downtown towers
- the Maple Grove suburbs
- Crestview Heights (hill houses, for later)
- Skyhaven Airport with the Skytrade private terminal and hangar
- a school, a hospital, a park and a river

**Options, best first:**
1. **Procedural city with Geometry Nodes:** road grid, blocks, buildings by height zone, street lights, trees. This is fully original and easiest to restyle as the toon look evolves.
2. **City and building add-ons:** for example free or pay-what-you-want building generators, plus asset libraries like Poly Haven (CC0 textures, HDRIs, models) and BlenderKit (check each asset's licence).
3. **Real map data as a layout base only:** e.g. the Blosm (blender-osm) add-on importing OpenStreetMap streets and buildings, then heavily restyled and renamed so no real place is recognisable. **Licensing:**
   - OpenStreetMap data is ODbL and needs an "© OpenStreetMap contributors" credit.
   - Mapbox and Google 3D tiles have terms that restrict use in videos. Read them before using either; avoid Google photorealistic tiles for the series.

**Whatever the method:**
- Keep the city modular: one `skyhaven_city.blend`, linked into episodes.
- Use low-detail versions for wide shots.
- No real logos, shop brands, number plates, aircraft registrations or recognisable landmarks.

## 7. File structure and workflow

```
skyhaven-Private-/                     (GitHub: 75647737/skyhaven-Private-)
  blender/characters/  ace_v001.blend, tori_v001.blend, max_baby_v001.blend, leo_v001.blend  (master files)
  blender/sets/        flat.blend, garage.blend, office.blend, skyhaven_city.blend, airport.blend
  blender/props/       hatchback.blend, drone.blend, mugs, napkin, parcel...
  blender/episodes/ep01/  ep01_s01_bedroom.blend ... (LINK characters and sets, never copy)
  renders/ep01/s01/####.png   (local only, ignored by Git)
```
- **Link, don't append**, characters and sets into episode files (File → Link), using library overrides for animation. Fixing Ace once then fixes him everywhere.
- **Version as you go:** `ace_v001.blend`, `ace_v002.blend`. Keep a short `CHANGELOG.txt`.
- Render on the PC's GPU (EEVEE for the series). Do a preview pass at 50% resolution first.
- Send finished renders and master files to the cloud session, which keeps them in the GitHub repo `75647737/skyhaven-Private-` and handles voices, music, sound effects and the final edit.

## 8. Rules

- **Everything original:** fictional characters and companies, no real people, no real brands or logos, no registrations on aircraft or plates on cars.
- **No AI image or video generation** in the pipeline unless the client says so. ElevenLabs is approved for voices only, generated in the cloud session.
- **Keep it family-friendly:** no gambling or "jackpot luck" framing; success comes from work, ownership and a plan.
- **End card** (added in the edit): Skyhaven logo, "A Skytrade Aviation original series", www.skytradeaviation.com, and "A fictional story. Not financial advice."

## 9. Your first tasks, in order

1. Open `skyhaven_kitchen_test.blend`. Review Ace against section 3 and give him a face rig (blinks, brows, mouth shapes) and idle breathing.
2. Build **Tori** and **baby Max** to the same quality, saved as master files.
3. Build the **flat** (bedroom and kitchen) and **scene 1–2 blocking** with simple animation and full "life" (section 5).
4. Render a 10-second preview of scene 2 (breakfast) and share it for review.
5. Then the **garage**, the **hatchback**, and the **Skyhaven city** block-out for the drive (scene 3).
