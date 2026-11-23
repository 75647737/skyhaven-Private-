"""Generate voice lines with ElevenLabs, plus per-character timing for lip-sync.

    python tools/audio/elevenlabs_tts.py episodes/breakfast-test/dialogue.json [--force]

Reads the API key from the ELEVENLABS_API_KEY environment variable or from
~/.skyhaven/elevenlabs_key.txt (never from the repo). For each line writes
voices/<id>.mp3 and voices/<id>.json (text, characters, start/end times in
seconds, duration) next to the dialogue file. Existing lines are skipped
unless --force. ElevenLabs is approved for voices only (see the blueprint).
"""
import base64, json, os, sys, urllib.request, urllib.error

MODEL = "eleven_multilingual_v2"


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k:
        p = os.path.join(os.path.expanduser("~"), ".skyhaven", "elevenlabs_key.txt")
        if os.path.exists(p):
            k = open(p, encoding="utf-8-sig").read().strip()
    if not k:
        sys.exit("No ElevenLabs key: set ELEVENLABS_API_KEY or ~/.skyhaven/elevenlabs_key.txt")
    return k


def tts(key, voice_id, text, stability, style):
    body = json.dumps({
        "text": text, "model_id": MODEL,
        "voice_settings": {"stability": stability, "similarity_boost": 0.8, "style": style, "use_speaker_boost": True},
    }).encode()
    url = "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % voice_id
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "xi-api-key": key, "Content-Type": "application/json", "User-Agent": "skyhaven-tools"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    path = sys.argv[1]
    force = "--force" in sys.argv
    d = json.load(open(path, encoding="utf-8"))
    out = os.path.join(os.path.dirname(path), "voices")
    os.makedirs(out, exist_ok=True)
    key = api_key()
    for ln in d["lines"]:
        mp3 = os.path.join(out, ln["id"] + ".mp3")
        js = os.path.join(out, ln["id"] + ".json")
        if os.path.exists(mp3) and os.path.exists(js) and not force:
            print("skip", ln["id"])
            continue
        v = d["voices"][ln["who"]]
        try:
            r = tts(key, v["voice_id"], ln["text"], v.get("stability", 0.5), v.get("style", 0.3))
        except urllib.error.HTTPError as e:
            sys.exit("ElevenLabs error %s on %s: %s" % (e.code, ln["id"], e.read().decode("utf-8", "replace")[:300]))
        open(mp3, "wb").write(base64.b64decode(r["audio_base64"]))
        al = r.get("normalized_alignment") or r.get("alignment") or {}
        ends = al.get("character_end_times_seconds", [0])
        json.dump({"id": ln["id"], "who": ln["who"], "text": ln["text"], "mood": ln.get("mood"),
                   "voice": v["voice"], "chars": al.get("characters", []),
                   "starts": al.get("character_start_times_seconds", []), "ends": ends,
                   "duration": max(ends) if ends else 0}, open(js, "w", encoding="utf-8"), indent=1)
        print("ok", ln["id"], ln["who"], "%.2fs" % (max(ends) if ends else 0))


if __name__ == "__main__":
    main()
