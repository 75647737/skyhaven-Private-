# Rendering Skyhaven on Modal

There are two Modal tools here:

- **`skyhaven_render.py`**, a command-line render farm: you run it from your PC and it renders a scene's frames in parallel chunks (CPU or one GPU). See *Part 1*.
- **`render_service.py`**, a web service you deploy once: it takes a `.blend`, splits the frames across up to 10 GPUs and returns an MP4, so a cloud Claude session can send renders to it. See *Part 2*.

## Part 1: command-line render farm (`skyhaven_render.py`)

`skyhaven_render.py` is a small render farm: headless Blender on Modal renders a scene's frames in parallel chunks, and the frames come back through a Modal volume.

### Workers
| Worker | Hardware | Engine | Best for |
|---|---|---|---|
| `render_cpu` (default) | 8 CPU cores, 16 GB RAM, up to **2** at once | Cycles on CPU | Previews, test frames, light scenes, anything the GPU worker can't run |
| `render_gpu` (`--gpu`) | 1 × L4 (or T4), never more than 1 | EEVEE, or Cycles on GPU | Final episode renders; usually far cheaper per frame |

**Note:** EEVEE needs a GPU. CPU workers render with **Cycles** only, so a scene built for EEVEE will look slightly different on the CPU worker. For the final look, render with `--gpu`.

### Cost guard
- `MAX_WORKERS = 2` (CPU) and `max_containers=1` (GPU) cap how many containers can run at once. Change them only on purpose.
- Every chunk stops after 2 hours.
- Set a **spending limit** in the Modal dashboard (Settings → Usage and billing) before the first big render.
- Always run a `--preview` of a few frames first, look at the time per frame, then estimate the full render (frames × seconds per frame ÷ workers).

### Rough costs (check current Modal prices)
- **CPU:** about $0.05 per core-hour plus memory, so one 8-core worker is roughly $0.45 an hour. A stylised Cycles frame at 1080p might take 20–60 s on 8 cores, so a 3-minute episode (about 4,300 frames) is roughly 24–70 worker-hours, or **$10–30**.
- **GPU (L4):** roughly $0.80 an hour. EEVEE at 1080p is often 1–4 s per frame, so the same episode is roughly 2–5 hours, or **$2–4**.

These are estimates; the preview run gives the real numbers.

### Steps
Run these on the machine that has the Modal login (`modal token` lives there). Never paste Modal tokens into code or chat.
1. `pip install modal` (once)
2. `modal volume create skyhaven-files` and `modal volume create skyhaven-renders` (once)
3. Upload the Blender files, keeping the repo layout so linked files resolve:
   `modal volume put skyhaven-files blender/ /blender/`
4. Preview: `modal run tools/modal/skyhaven_render.py --blend blender/episodes/ep01/ep01_s02_breakfast.blend --start 1 --end 24 --preview`
5. Full scene: same command without `--preview`, with the full frame range (add `--gpu` for EEVEE).
6. Download: `modal volume get skyhaven-renders /ep01_s02_breakfast/ renders/ep01/s02/`

### Before uploading
- In Blender: **File → External Data → Make Paths Relative**, and keep characters, sets and props linked with relative paths.
- Set the frame range, camera and output size in the scene. The script only overrides the engine, PNG output, and preview size and samples.
- Blender versions must match (`BLENDER_VERSION` in the script = the version on the PC).

## Part 2: GPU render web service (`render_service.py`)

`render_service.py` is a small web service in your Modal account. It takes a `.blend`, splits the frames across up to 10 GPUs, and returns an MP4. Deploy it once from your PC; after that the cloud Claude session can send renders to it over HTTPS.

### One-time setup (on your PC)

1. Install and log in to Modal:
   ```bash
   pip install modal
   ```
   ```bash
   modal setup
   ```
2. Make a private access token for the service (any long random string) and store it in Modal:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   ```bash
   modal secret create skyhaven-render SKYHAVEN_RENDER_TOKEN=<paste the string here>
   ```
3. Deploy from the repo folder:
   ```bash
   modal deploy tools/modal/render_service.py
   ```
   Modal prints the web URL, like `https://<your-workspace>--skyhaven-render-web.modal.run`.
4. Give the cloud session the **URL** (in chat is fine) and the **token** (only through the secure credential form it opens, never in chat).

### Notes
- GPU: `L40S` by default. For cheaper renders deploy with `SKYHAVEN_GPU=L4 modal deploy ...`.
- Engine: EEVEE first. If EEVEE cannot get a GPU context inside Modal's containers, each chunk falls back to Cycles on the GPU automatically (slower per frame, still fast in parallel). The job status reports which engine was used.
- Textures must be packed into the `.blend` (File > External Data > Pack Resources).
- Rendered frames and videos stay in the Modal volume `skyhaven-render-jobs`; clear it now and then with `modal volume rm skyhaven-render-jobs /<job_id> -r`.
- Cost: you pay Modal per GPU-second only while frames render.
