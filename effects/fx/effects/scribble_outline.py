import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..compose import grow
from ..palette import colorf

def _resample(c, step):
    c = c[:, 0, :].astype(np.float32)
    d = np.sqrt(((np.roll(c, -1, 0) - c) ** 2).sum(1)); L = d.sum()
    if L < step * 4: return None
    s = np.concatenate([[0], np.cumsum(d)])[:-1]
    q = np.arange(0, L, step)
    x = np.interp(q, s, c[:, 0], period=L); y = np.interp(q, s, c[:, 1], period=L)
    pts = np.stack([x, y], 1)
    k = 3; pad = np.concatenate([pts[-k:], pts, pts[:k]])
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    return np.stack([np.convolve(pad[:, 0], ker, "valid"), np.convolve(pad[:, 1], ker, "valid")], 1)

@register("scribble_outline", defaults=dict(color="accent", color2="text", thickness=7, offset=16, jitter=5.0, boil=3, passes=2,
                                            step=16, draw_on=0.5, min_area=0.004, glow=0.5, seed=11, max_shapes=4))
def scribble_outline(ctx, p):
    """Hand-drawn contour that 'boils' (re-jitters every `boil` frames) around the subject, drawn on over `draw_on` s.
    passes=2 gives a sketchy double line (second pass in color2, thinner)."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W
    hs = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    b = (grow(hs, max(1, int(p["offset"] / 2))) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cs = sorted([c for c in cs if cv2.contourArea(c) > p["min_area"] * b.size], key=cv2.contourArea, reverse=True)[:p["max_shapes"]]
    reveal = ease("out_cubic", ctx.t / p["draw_on"]) if p["draw_on"] > 0 else 1.0
    lay = np.zeros((H, W), np.float32); lay2 = np.zeros((H, W), np.float32)
    boil = ctx.i // max(1, p["boil"])
    for ci, c in enumerate(cs):
        pts = _resample(c, p["step"] / 2)
        if pts is None: continue
        pts = pts * 2
        for ps in range(p["passes"]):
            rng = np.random.default_rng(p["seed"] + boil * 131 + ps * 17 + ci * 7)
            j = rng.normal(0, p["jitter"], pts.shape)
            j = (j + np.roll(j, 1, 0) + np.roll(j, -1, 0)) / 3
            q = pts + j + (ps * p["jitter"] * 0.8)
            n = max(2, int(len(q) * reveal) + (2 if reveal >= 1 else 0))
            seg = np.concatenate([q, q[:2]])[:n] if reveal >= 1 else q[:n]
            th = p["thickness"] if ps == 0 else max(2, int(p["thickness"] * 0.55))
            cv2.polylines(lay if ps == 0 else lay2, [np.round(seg).astype(np.int32)], False, 1.0, th, cv2.LINE_AA)
    out = F
    if p["glow"] > 0:
        g = cv2.GaussianBlur(lay, (0, 0), 9) * p["glow"]
        out = 1 - (1 - out) * (1 - np.clip(g, 0, 1)[..., None] * colorf(ctx.palette, p["color"]))
    a2 = lay2[..., None]; out = out * (1 - a2) + colorf(ctx.palette, p["color2"]) * a2
    a = lay[..., None]
    return out * (1 - a) + colorf(ctx.palette, p["color"]) * a
