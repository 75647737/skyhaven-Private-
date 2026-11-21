"""Skyhaven render farm on Modal: headless Blender renders a scene's frames in parallel chunks.

CPU workers are the default (Cycles on CPU). A GPU worker (EEVEE or Cycles on an L4) is included for final
renders because it's usually much cheaper per frame; it's only used when you pass --gpu.

One-time setup (run on the machine that holds the Modal login, never paste tokens into code or chat):
  modal volume create skyhaven-files
  modal volume create skyhaven-renders

Upload a scene (and everything it links: characters, sets, props, keeping the same folder layout):
  modal volume put skyhaven-files blender/ /blender/

Render (frames 1-240 of scene 1, 24 frames per worker, at most 2 workers at once):
  modal run tools/modal/skyhaven_render.py --blend blender/episodes/ep01/ep01_s01_bedroom.blend --start 1 --end 240
  modal run tools/modal/skyhaven_render.py --blend ... --start 1 --end 48 --preview      # 50% size, low samples
  modal run tools/modal/skyhaven_render.py --blend ... --start 1 --end 240 --gpu         # L4, EEVEE
  modal run tools/modal/skyhaven_render.py --blend ... --start 1 --end 240 --gpu --engine cycles   # L4, Cycles (OptiX)

Download the frames:
  modal volume get skyhaven-renders /ep01_s01_bedroom/ renders/ep01/s01/
"""
import os, subprocess
import modal

BLENDER_VERSION = "5.3.0"            # match the version used on the PC
BLENDER_SERIES = "5.3"
CPU_CORES = 8.0                      # per CPU worker
CPU_MEMORY_MB = 16384
MAX_WORKERS = 2                      # cost guard: never more than this many containers at once
CHUNK_TIMEOUT_S = 2 * 60 * 60        # a chunk that runs longer than 2 h is stopped

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("wget", "xz-utils", "libxi6", "libxxf86vm1", "libxfixes3", "libxrender1", "libxkbcommon0",
                 "libsm6", "libice6", "libgl1", "libegl1", "libglu1-mesa", "libx11-6")
    .run_commands(
        f"wget -q https://download.blender.org/release/Blender{BLENDER_SERIES}/blender-{BLENDER_VERSION}-linux-x64.tar.xz -O /tmp/b.tar.xz",
        "mkdir -p /opt/blender && tar -xJf /tmp/b.tar.xz -C /opt/blender --strip-components=1 && rm /tmp/b.tar.xz",
        "ln -s /opt/blender/blender /usr/local/bin/blender",
    )
)
files = modal.Volume.from_name("skyhaven-files")
renders = modal.Volume.from_name("skyhaven-renders")
app = modal.App("skyhaven-render", image=image)

def _render(blend, start, end, engine, preview, device):
    files.reload()
    src = os.path.join("/files", blend)
    if not os.path.exists(src):
        raise SystemExit(f"{blend} is not on the skyhaven-files volume (upload it with `modal volume put`)")
    shot = os.path.splitext(os.path.basename(blend))[0]
    out_dir = f"/renders/{shot}/"
    os.makedirs(out_dir, exist_ok=True)
    # settings applied inside Blender before rendering (no change to the saved file)
    py = f"""
import bpy
s = bpy.context.scene
s.render.engine = {engine!r}
s.render.image_settings.file_format = 'PNG'
if {preview}:
    s.render.resolution_percentage = 50
if s.render.engine == 'CYCLES':
    s.cycles.device = {device!r}
    if {preview}: s.cycles.samples = 32
    if {device!r} == 'GPU':
        # OptiX is fastest on L4/T4; fall back to CUDA. Without a GPU, Cycles would quietly render on the CPU.
        p = bpy.context.preferences.addons['cycles'].preferences
        used = None
        for kind in ('OPTIX', 'CUDA'):
            try:
                p.compute_device_type = kind
            except TypeError:
                continue
            p.get_devices()
            if any(d.type == kind for d in p.devices):
                for d in p.devices:
                    d.use = d.type == kind
                used = kind
                break
        if used is None:
            raise RuntimeError('Cycles found no NVIDIA GPU (OptiX or CUDA)')
        print('Cycles GPU:', used, [d.name for d in p.devices if d.use], flush=True)
print('Render engine:', s.render.engine, '| format:', s.render.image_settings.file_format,
      '| size:', s.render.resolution_x, 'x', s.render.resolution_y, '@', s.render.resolution_percentage, '%', flush=True)
"""
    with open("/tmp/setup.py", "w") as f:
        f.write(py)
    # --python-exit-code makes Blender stop if the setup script fails, instead of rendering with the file's own settings
    cmd = ["blender", "-b", src, "--python-exit-code", "1", "--python", "/tmp/setup.py",
           "-o", out_dir + "####", "-s", str(start), "-e", str(end), "-a"]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    renders.commit()
    return f"{shot}: frames {start}-{end} done"

@app.function(volumes={"/files": files, "/renders": renders}, cpu=CPU_CORES, memory=CPU_MEMORY_MB,
              timeout=CHUNK_TIMEOUT_S, max_containers=MAX_WORKERS)
def render_cpu(blend: str, start: int, end: int, preview: bool = False):
    return _render(blend, start, end, "CYCLES", preview, "CPU")

@app.function(volumes={"/files": files, "/renders": renders}, gpu=["L4", "T4"], cpu=4.0, memory=16384,
              timeout=CHUNK_TIMEOUT_S, max_containers=1)
def render_gpu(blend: str, start: int, end: int, preview: bool = False, engine: str = "BLENDER_EEVEE"):
    return _render(blend, start, end, engine, preview, "GPU")

ENGINES = {"EEVEE": "BLENDER_EEVEE", "BLENDER_EEVEE": "BLENDER_EEVEE", "CYCLES": "CYCLES"}

@app.local_entrypoint()
def main(blend: str, start: int = 1, end: int = 24, chunk: int = 0, preview: bool = False, gpu: bool = False,
         engine: str = ""):
    # engine: "eevee" or "cycles". GPU default is EEVEE; CPU workers can only run Cycles.
    eng = ENGINES.get(engine.upper()) if engine else ("BLENDER_EEVEE" if gpu else "CYCLES")
    if eng is None:
        raise SystemExit(f"--engine must be eevee or cycles, not {engine!r}")
    if eng == "BLENDER_EEVEE" and not gpu:
        raise SystemExit("EEVEE needs a GPU: add --gpu, or use --engine cycles")
    # one GPU worker runs chunks one after another, so bigger chunks save Blender start-up and file loading
    chunk = chunk or (120 if gpu else 24)
    frames = end - start + 1
    chunks = [(blend, a, min(a + chunk - 1, end)) for a in range(start, end + 1, chunk)]
    workers = 1 if gpu else min(MAX_WORKERS, len(chunks))
    print(f"{frames} frames in {len(chunks)} chunks, {eng}, on "
          f"{'1 GPU worker' if gpu else f'{workers} CPU worker(s) x {CPU_CORES:g} cores'}")
    if gpu:
        calls = render_gpu.starmap([(b, a, e, preview, eng) for b, a, e in chunks])
    else:
        calls = render_cpu.starmap([(b, a, e, preview) for b, a, e in chunks])
    for msg in calls:
        print(msg)
    print("Download: modal volume get skyhaven-renders /%s/ renders/" % os.path.splitext(os.path.basename(blend))[0])
