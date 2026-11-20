"""Effect registry + per-frame context + the single-clip driver used by the CLI."""
import os, tempfile, time
import numpy as np
from .anim import envelope
from .compose import f32, u8
from .palette import load_palette

_REG = {}

def register(name, defaults=None, doc=None):
    """@register("spotlight", defaults={...}) on fn(ctx, params) -> float frame."""
    def deco(fn):
        _REG[name] = dict(fn=fn, defaults=dict(defaults or {}), doc=(doc or fn.__doc__ or "").strip())
        return fn
    return deco

def get_effect(name):
    if name not in _REG: raise KeyError(f"unknown effect {name!r}; have {sorted(_REG)}")
    return _REG[name]

def list_effects(): return {k: dict(defaults=v["defaults"], doc=v["doc"]) for k, v in sorted(_REG.items())}

class Ctx:
    """What an effect sees for one frame.
    frame: float32 HxWx3 [0,1] (already includes earlier effects); src: the untouched frame
    mask: float32 HxW subject matte; t: seconds since effect start; dur: effect length; u = t/dur;
    i: frame index inside the effect; fps; palette; state: dict persisted across frames of this effect instance."""
    __slots__ = ("frame", "src", "mask", "t", "dur", "u", "i", "fps", "palette", "state", "W", "H")
    def __init__(self, frame, src, mask, t, dur, i, fps, palette, state):
        self.frame, self.src, self.mask, self.t, self.dur, self.i, self.fps, self.palette, self.state = frame, src, mask, t, dur, i, fps, palette, state
        self.u = 0.0 if dur <= 0 else min(1.0, max(0.0, t / dur)); self.H, self.W = frame.shape[:2]

def apply_frame(name, frame, src, mask, t, dur, i, fps, palette, params, state):
    """Run one effect on one frame, with the generic in/out crossfade (params mix_in / mix_out seconds)."""
    e = get_effect(name); p = {**e["defaults"], **(params or {})}
    ctx = Ctx(frame, src, mask, t, dur, i, fps, palette, state)
    out = e["fn"](ctx, p)
    a = envelope(t, 0, dur, p.get("mix_in", 0.0), p.get("mix_out", 0.0)) if (p.get("mix_in") or p.get("mix_out")) else 1.0
    return out if a >= 1 else frame * (1 - a) + out * a

def apply_effect(name, inp, out, start=0.0, end=None, params=None, palette=None, backend="ensemble",
                 size=None, fps=None, keep_audio=True, log=print, seg_opts=None):
    """Apply one effect to [start,end] of a clip; frames outside the range pass through.
    size=(W,H) cover-crops to that size first (e.g. 1080x1920); default = source size."""
    from .vio import probe, read_frames, fit, Writer, copy_audio
    from .seg import Segmenter
    info = probe(inp); fps = fps or info["fps"] or 30.0
    W, H = size or (info["w"], info["h"])
    end = info["dur"] if end is None else min(end, info["dur"])
    pal = load_palette(palette); seg = Segmenter(backend, **(seg_opts or {}))
    prep = (lambda f: fit(f, W, H)) if size else (lambda f: f)
    t0 = time.time()
    rng = [prep(f) for f in read_frames(inp, start, end - start, fps)]          # effect range only (masks need neighbours)
    small = seg.sequence(rng, progress=lambda i, n: log(f"  masks {i}/{n}"))
    tmp = tempfile.mktemp(suffix=".mp4", dir=os.path.dirname(os.path.abspath(out)))
    w = Writer(tmp, W, H, int(round(fps)))
    def passthru(a, b):
        if b > a:
            for f in read_frames(inp, a, b - a, fps): w.write(prep(f))
    passthru(0.0, start)
    state = {}
    for i, fr in enumerate(rng):
        F = f32(fr); m = seg.upscale(small[i], fr)
        w.write(u8(apply_frame(name, F, F, m, i / fps, end - start, i, fps, pal, params, state)))
        if i % 30 == 0: log(f"  fx {i}/{len(rng)}")
    passthru(end, info["dur"])
    w.close()
    if keep_audio and not os.path.isdir(inp): copy_audio(inp, tmp, out)
    else: os.replace(tmp, out)
    log(f"wrote {out} in {time.time()-t0:.1f}s")
    return out
