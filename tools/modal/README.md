# GPU rendering on Modal

`render_service.py` is a small web service in your Modal account. It takes a `.blend`, splits the frames across up to 10 GPUs, and returns an MP4. Deploy it once from your PC; after that the cloud Claude session can send renders to it over HTTPS.

## One-time setup (on your PC)

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

## Notes
- GPU: `L40S` by default. For cheaper renders deploy with `SKYHAVEN_GPU=L4 modal deploy ...`.
- Engine: EEVEE first. If EEVEE cannot get a GPU context inside Modal's containers, each chunk falls back to Cycles on the GPU automatically (slower per frame, still fast in parallel). The job status reports which engine was used.
- Textures must be packed into the `.blend` (File > External Data > Pack Resources).
- Rendered frames and videos stay in the Modal volume `skyhaven-render-jobs`; clear it now and then with `modal volume rm skyhaven-render-jobs /<job_id> -r`.
- Cost: you pay Modal per GPU-second only while frames render.
