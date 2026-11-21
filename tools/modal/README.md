# Rendering Skyhaven on Modal

`skyhaven_render.py` is a small render farm: headless Blender on Modal renders a scene's frames in parallel chunks, and the frames come back through a Modal volume.

## Workers
| Worker | Hardware | Engine | Best for |
|---|---|---|---|
| `render_cpu` (default) | 8 CPU cores, 16 GB RAM, up to **2** at once | Cycles on CPU | Previews, test frames, light scenes, anything the GPU worker can't run |
| `render_gpu` (`--gpu`) | 1 × L4 (or T4), never more than 1 | EEVEE (default), or Cycles on GPU with `--engine cycles` (OptiX, falling back to CUDA) | Final episode renders; usually far cheaper per frame |

**Note:** EEVEE needs a GPU. CPU workers render with **Cycles** only, so a scene built for EEVEE will look slightly different on the CPU worker. For the final look, render with `--gpu`.

**Chunks:** CPU workers render 24 frames per chunk; the GPU worker renders 120, because its chunks run one after another and each chunk restarts Blender. Change it with `--chunk`.

**Fails loudly:** if the settings script can't apply (wrong engine name, no GPU found for Cycles), the chunk stops with an error instead of rendering with the file's own settings. Each chunk's log prints the engine, file format and size it used.

## Cost guard
- `MAX_WORKERS = 2` (CPU) and `max_containers=1` (GPU) cap how many containers can run at once. Change them only on purpose.
- Every chunk stops after 2 hours.
- Set a **spending limit** in the Modal dashboard (Settings → Usage and billing) before the first big render.
- Always run a `--preview` of a few frames first, look at the time per frame, then estimate the full render (frames × seconds per frame ÷ workers).

## Rough costs (check current Modal prices)
- **CPU:** about $0.05 per core-hour plus memory, so one 8-core worker is roughly $0.45 an hour. A stylised Cycles frame at 1080p might take 20–60 s on 8 cores, so a 3-minute episode (about 4,300 frames) is roughly 24–70 worker-hours, or **$10–30**.
- **GPU (L4):** roughly $0.80 an hour. EEVEE at 1080p is often 1–4 s per frame, so the same episode is roughly 2–5 hours, or **$2–4**.

These are estimates; the preview run gives the real numbers.

## Steps
Run these on the machine that has the Modal login (`modal token` lives there). Never paste Modal tokens into code or chat.
1. `pip install modal` (once)
2. `modal volume create skyhaven-files` and `modal volume create skyhaven-renders` (once)
3. Upload the Blender files, keeping the repo layout so linked files resolve:
   `modal volume put skyhaven-files blender/ /blender/`
4. Preview: `modal run tools/modal/skyhaven_render.py --blend blender/episodes/ep01/ep01_s02_breakfast.blend --start 1 --end 24 --preview`
5. First GPU run: try `--start 1 --end 2 --preview --gpu` and check the log and the two frames. EEVEE without a screen on Modal hasn't been tested yet.
6. Full scene: same command without `--preview`, with the full frame range (add `--gpu` for EEVEE, `--gpu --engine cycles` for Cycles on the GPU).
7. Download: `modal volume get skyhaven-renders /ep01_s02_breakfast/ renders/ep01/s02/`

## Before uploading
- In Blender: **File → External Data → Make Paths Relative**, and keep characters, sets and props linked with relative paths.
- Set the frame range, camera and output size in the scene. The script only overrides the engine, PNG output, and preview size and samples.
- Blender versions must match (`BLENDER_VERSION` in the script = the version on the PC).
