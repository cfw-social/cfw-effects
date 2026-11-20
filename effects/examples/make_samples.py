"""Render a short sample of every effect on the synthetic mannequin clip (safe to commit: no real people).
Writes examples/samples/<effect>.mp4 (360x640) and examples/samples/_grid.mp4.
Usage: python examples/make_samples.py [effect ...]"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import fx

CLIP = os.path.join(HERE, "assets", "synthetic_mannequin.mp4"); OUT = os.path.join(HERE, "samples")
if not os.path.exists(CLIP): subprocess.run([sys.executable, os.path.join(HERE, "make_synthetic_clip.py")], check=True)
P = {  # sample params per effect (defaults otherwise)
    "backdrop_words": {"words": [{"text": "FOCUS", "at": 0.1}, {"text": "REPEAT", "at": 1.2, "color": "secondary"}], "y": 0.45},
    "glass_card": {"title": "One tip", "body": "Keep one idea per card."},
    "countdown_behind": {"start_value": 3, "end_value": 0, "y": 0.3},
    "stamp": {"text": "DONE", "at": 0.5},
    "giant_captions": {"text": "SAY IT BIG"},
    "chat_window": {"title": "Group chat", "messages": [{"text": "check this out", "at": 0.5, "mine": True}, {"text": "nice!", "at": 1.4}]},
    "tier_list": {"items": [{"label": "idea one", "tier": 1}, {"label": "idea two", "tier": 2}], "drop_at": 0.8},
    "profile_wall": {"count_to": 12500, "count_label": "views"},
    "receipt_scroll": {"title": "TODAY", "items": [["warm-up", "5 min"], ["drills", "10 min"], ["cool-down", "3 min"]], "total": ["TOTAL", "18 min"], "speed": 900},
    "colour_collage": {"blocks": [{"text": "PLAN", "color": "accent", "pos": [0.32, 0.2], "angle": -6}, {"text": "DO", "color": "hot", "pos": [0.68, 0.35], "angle": 5}, {"text": "REVIEW", "color": "bg", "pos": [0.42, 0.8], "angle": -3}]},
    "key_rain": {"letters": "SAMPLE", "count": 18, "spawn": 1.0},
    "digital_zoom": {"steps": [[0, 1.0], [0.8, 1.8], [1.6, 2.6]]},
    "pullback": {"at": 0.2, "dur": 0.7, "caption": "your caption here"},
    "redact": {"rects": [[0.6, 0.12, 0.35, 0.12]], "mode": "pixelate"},
    "label": {"text": "LABEL", "index": 1},
}
SKIP = {"grid_collage"}
names = sys.argv[1:] or [n for n in fx.list_effects() if n not in SKIP]
seg = {"backend": "chroma", "chroma_hue": 290, "chroma_tol": 22, "chroma_subject": "key", "temporal_sigma": 0.8}
os.makedirs(OUT, exist_ok=True); tmpd = tempfile.mkdtemp()
for n in names:
    r = {"out": os.path.join(tmpd, n + ".mp4"), "size": [1080, 1920], "fps": 30, "palette": "neutral-mono", "seg": seg,
         "segments": [{"src": CLIP, "in": 0.5, "dur": 2.5, "effects": [{"name": n, "params": P.get(n, {})}]}]}
    fx.run_recipe(r, log=lambda *a, **k: None)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", r["out"], "-vf", "scale=360:640", "-c:v", "libx264", "-crf", "30",
                    "-preset", "slow", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", os.path.join(OUT, n + ".mp4")], check=True)
    print("sample", n)
if not sys.argv[1:]:
    allc = [{"src": os.path.join(OUT, n + ".mp4"), "dur": 2.5} for n in names]
    r = {"out": os.path.join(tmpd, "_grid.mp4"), "size": [1080, 1920], "fps": 30, "palette": "neutral-mono", "seg": seg,
         "segments": [{"src": CLIP, "dur": 3.0, "effects": [{"name": "grid_collage", "params": {"clips": allc, "cols": 5, "rows": 6, "title": "fx samples", "labels": names}}]}]}
    fx.run_recipe(r, log=lambda *a, **k: None)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", r["out"], "-vf", "scale=540:960", "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
                    "-an", "-movflags", "+faststart", os.path.join(OUT, "_grid.mp4")], check=True)
    print("sample grid")
