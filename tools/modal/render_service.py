"""Skyhaven GPU render service on Modal.

Deploy once from your PC (see tools/modal/README.md):
    modal deploy tools/modal/render_service.py

Then any client (e.g. the cloud Claude session) can submit a .blend over HTTPS:
    POST /jobs          multipart: blend=<file>, start, end, fps, engine, resolution_pct, samples
    GET  /jobs/{id}     -> {"status": "running" | "done" | "failed", ...}
    GET  /jobs/{id}/video -> the MP4
All requests need:  Authorization: Bearer <SKYHAVEN_RENDER_TOKEN>
"""
import os
import subprocess
import uuid
from pathlib import Path

import modal

BLENDER_URL = "https://download.blender.org/release/Blender5.3/blender-5.3.0-linux-x64.tar.xz"
GPU = os.environ.get("SKYHAVEN_GPU", "L40S")      # L4 is cheaper, L40S is faster
MAX_GPUS = 10                                      # frames are split across up to this many GPUs

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "wget", "xz-utils", "ffmpeg",
        # libraries Blender needs to start headless (OpenGL/EGL for EEVEE)
        "libxi6", "libxkbcommon0", "libsm6", "libgl1", "libegl1", "libxrender1",
        "libxfixes3", "libxxf86vm1", "libglvnd0",
    )
    .run_commands(
        f"wget -q {BLENDER_URL} -O /tmp/blender.tar.xz",
        "tar xf /tmp/blender.tar.xz -C /opt && mv /opt/blender-5.3.0-linux-x64 /opt/blender && rm /tmp/blender.tar.xz",
    )
    .pip_install("fastapi[standard]")
    # expose the NVIDIA graphics driver (EGL) as well as CUDA, so EEVEE can use the GPU
    .env({"NVIDIA_DRIVER_CAPABILITIES": "all"})
)

app = modal.App("skyhaven-render")
jobs = modal.Volume.from_name("skyhaven-render-jobs", create_if_missing=True)
secret = modal.Secret.from_name("skyhaven-render")      # holds SKYHAVEN_RENDER_TOKEN

SETUP = r'''
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
engine, pct, samples = a[0], int(a[1]), int(a[2])
sc = bpy.context.scene
sc.render.resolution_percentage = pct
if engine == "CYCLES":
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            if any(d.type == dev_type for d in prefs.devices):
                break
        except Exception:
            pass
    for d in prefs.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
else:
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = samples
sc.render.image_settings.file_format = "PNG"
'''


@app.function(image=image, gpu=GPU, timeout=3600, volumes={"/jobs": jobs}, max_containers=MAX_GPUS)
def render_frames(job_id: str, frames: list[int], engine: str, pct: int, samples: int) -> dict:
    jobs.reload()
    job = Path("/jobs") / job_id
    (job / "frames").mkdir(exist_ok=True)
    (job / "setup.py").write_text(SETUP)
    log = []
    for engine_try in ([engine, "CYCLES"] if engine != "CYCLES" else ["CYCLES"]):
        ok = True
        for f in frames:
            out = job / "frames" / f"f_{f:04d}.png"
            cmd = ["/opt/blender/blender", "-b", str(job / "scene.blend"), "--python", str(job / "setup.py"),
                   "-o", str(job / "frames" / "f_####"), "-f", str(f), "--", engine_try, str(pct), str(samples)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if not out.exists():
                ok = False
                log.append(f"{engine_try} frame {f} failed: {r.stdout[-800:]} {r.stderr[-800:]}")
                break
        if ok:
            jobs.commit()
            return {"engine": engine_try, "frames": len(frames), "log": log}
    jobs.commit()
    raise RuntimeError("\n".join(log))


@app.function(image=image, timeout=7200, volumes={"/jobs": jobs})
def run_job(job_id: str, start: int, end: int, fps: int, engine: str, pct: int, samples: int) -> dict:
    frames = list(range(start, end + 1))
    n = min(MAX_GPUS, len(frames))
    chunks = [frames[i::n] for i in range(n)]
    results = list(render_frames.starmap([(job_id, c, engine, pct, samples) for c in chunks]))
    jobs.reload()
    job = Path("/jobs") / job_id
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(start),
                    "-i", str(job / "frames" / "f_%04d.png"),
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-movflags", "+faststart", str(job / "out.mp4")], check=True)
    jobs.commit()
    return {"engines": sorted({r["engine"] for r in results}), "frames": len(frames)}


@app.function(image=image, volumes={"/jobs": jobs}, secrets=[secret], timeout=600)
@modal.asgi_app()
def web():
    from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
    from fastapi.responses import FileResponse

    api = FastAPI(title="Skyhaven render")

    def auth(authorization: str = Header(default="")):
        if authorization != f"Bearer {os.environ['SKYHAVEN_RENDER_TOKEN']}":
            raise HTTPException(status_code=401, detail="bad token")

    @api.post("/jobs", dependencies=[Depends(auth)])
    async def submit(blend: UploadFile = File(...), start: int = Form(1), end: int = Form(120),
                     fps: int = Form(24), engine: str = Form("BLENDER_EEVEE"),
                     resolution_pct: int = Form(100), samples: int = Form(64)):
        job_id = uuid.uuid4().hex[:12]
        job = Path("/jobs") / job_id
        job.mkdir(parents=True)
        with open(job / "scene.blend", "wb") as f:
            while chunk := await blend.read(1 << 20):
                f.write(chunk)
        jobs.commit()
        call = run_job.spawn(job_id, start, end, fps, engine, resolution_pct, samples)
        (job / "call_id").write_text(call.object_id)
        jobs.commit()
        return {"job_id": job_id}

    @api.get("/jobs/{job_id}", dependencies=[Depends(auth)])
    def status(job_id: str):
        jobs.reload()
        job = Path("/jobs") / job_id
        if not (job / "call_id").exists():
            raise HTTPException(404, "no such job")
        call = modal.FunctionCall.from_id((job / "call_id").read_text())
        frames_done = len(list((job / "frames").glob("*.png"))) if (job / "frames").exists() else 0
        try:
            result = call.get(timeout=0)
            return {"status": "done", "frames_done": frames_done, **result}
        except TimeoutError:
            return {"status": "running", "frames_done": frames_done}
        except Exception as e:  # render failed
            return {"status": "failed", "error": str(e)[-3000:]}

    @api.get("/jobs/{job_id}/video", dependencies=[Depends(auth)])
    def video(job_id: str):
        jobs.reload()
        path = Path("/jobs") / job_id / "out.mp4"
        if not path.exists():
            raise HTTPException(404, "not ready")
        return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")

    return api
