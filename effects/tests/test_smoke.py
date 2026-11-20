"""Fast tests with synthetic frames + a synthetic mask (no models needed)."""
import numpy as np, cv2, pytest
import fx
from fx.compose import f32

def synth(W=270, H=480):
    yy, xx = np.mgrid[0:H, 0:W]
    frame = np.dstack([(xx / W * 255), (yy / H * 255), np.full_like(xx, 120)]).astype(np.uint8)
    mask = np.zeros((H, W), np.float32); cv2.ellipse(mask, (W // 2, H // 2), (60, 130), 0, 0, 360, 1.0, -1)
    return f32(frame), cv2.GaussianBlur(mask, (0, 0), 2)

@pytest.mark.parametrize("name", sorted(fx.list_effects()))
def test_effect_runs(name):
    F, M = synth(); pal = fx.load_palette(); st = {}
    params = {"rects": [[0, 0, 0.5, 0.2]]} if name == "redact" else {}
    for i in range(4):
        out = fx.apply_frame(name, F, F, M, t=i / 30 + 0.5, dur=2.0, i=i, fps=30, palette=pal, params=params, state=st)
        assert out.shape == F.shape and np.isfinite(out).all()

def test_palette_presets():
    assert fx.color(fx.load_palette(), "accent") == (253, 161, 7)
    assert fx.color(fx.load_palette("neutral-mono"), "text") == (255, 255, 255)
    assert fx.color(fx.load_palette({"roles": {"accent": "#112233"}}), "accent") == (17, 34, 51)

def test_easing():
    assert fx.ease("out_cubic", 0) == 0 and fx.ease("out_cubic", 1) == 1
    k = fx.Keyframes([(0, 0.0), (1, 10.0)], "linear"); assert abs(k(0.5) - 5) < 1e-6

def test_recipe_mask_src(tmp_path):
    """mask_src: segment on one copy of the source, render another (e.g. a privacy-blurred copy)."""
    import json, os, shutil
    if not shutil.which("ffmpeg"): pytest.skip("ffmpeg not on PATH")
    clip = os.path.join(os.path.dirname(__file__), "..", "examples", "assets", "synthetic_mannequin.mp4")
    clip = os.path.abspath(clip)
    out = tmp_path / "out.mp4"
    r = {"out": str(out), "size": [180, 320], "fps": 30, "seg": {"backend": "chroma", "chroma_hue": 290, "chroma_tol": 22, "chroma_subject": "key"},
         "segments": [{"src": clip, "mask_src": clip, "in": 0.0, "dur": 0.3,
                       "effects": [{"name": "spotlight", "params": {"sparkles": 5}}]}]}
    p = tmp_path / "r.json"; p.write_text(json.dumps(r))
    fx.run_recipe(str(p), log=lambda *a: None)
    assert out.exists() and out.stat().st_size > 0
