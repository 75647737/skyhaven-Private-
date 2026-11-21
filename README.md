# Skyhaven

An original 3D animated family series by **Skytrade Aviation**. Ace Sterling goes from an ordinary young dad with a big dream to a company founder, one year per episode. The full story, cast, look, rules and first tasks are in **[SKYHAVEN-BLUEPRINT.md](SKYHAVEN-BLUEPRINT.md)**. Read it before building anything.

## Layout
| Folder | What lives there |
|---|---|
| `blender/characters/` | Master character files (`ace_v001.blend` ...), rigged, with face shape keys. **Link** them into episodes, never copy. |
| `blender/sets/` | Flat, garage, office, Skyhaven city, airport. |
| `blender/props/` | Hatchback, drone, mugs, parcel ... |
| `blender/episodes/epNN/` | One file per scene, linking characters, sets and props. |
| `renders/` | Notes and links only. Rendered frames and finished episodes are too big for Git (see `renders/README.md`). |
| `characters/2d/` | The original 2D model sheet and rig (reference for looks and colours). |
| `characters/3d-web/` | The first three.js 3D test (superseded by Blender, kept for reference). |
| `episodes/pilot-2d-the-call/` | The early 2D pilot "The Call" with its ElevenLabs voice lines, mix and render. The story has since been re-planned: Episode 1 is now "The Dream" (see the blueprint). |
| `tools/` | Small helpers (audio synthesis for sound effects). |
| `fonts/` | Montserrat and Cormorant Garamond (SIL Open Font License). |

## Workflow
- **Building:** a local Claude chat on the client's PC with the Blender MCP add-on builds in Blender 5.3.
- **Cloud session:** handles voices (ElevenLabs), sound, the edit and reviews.
- `.blend` files go through **Git LFS** (see `.gitattributes`). Install Git LFS before your first commit (`git lfs install`).
- Version files (`_v001`, `_v002` ...) and note changes in `CHANGELOG.md`.

Everything here is original and fictional: no real people, brands, logos, registrations or number plates.
