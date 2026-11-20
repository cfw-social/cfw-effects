import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..palette import colorf
from ..compose import feather, grow

@register("shadow_puppet", defaults=dict(bg="accent", silhouette="outline", rim="text", rim_px=4, cast=True, cast_dx=40, cast_dy=10,
                                         cast_alpha=0.25, gradient=0.25, intro=0.25, grain=0.02, harden=(0.35, 0.6)))
def shadow_puppet(ctx, p):
    """Subject becomes a flat silhouette on a solid palette colour (with a soft radial gradient), optional thin rim
    light and a faint offset cast shadow. Wipes in from the original over `intro` s."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    m = np.clip((m - p["harden"][0]) / (p["harden"][1] - p["harden"][0]), 0, 1)   # crisp silhouette edge
    if "_bg" not in st:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
        st["_bg"] = (colorf(ctx.palette, p["bg"]) * (1 - p["gradient"] * np.clip(r * 1.6, 0, 1))[..., None]).astype(np.float32)
    out = st["_bg"].copy()
    if p["cast"]:
        M = np.float32([[1, -0.15, p["cast_dx"]], [0, 1, p["cast_dy"]]])
        c = feather(cv2.warpAffine(m, M, (W, H)), 6)[..., None] * p["cast_alpha"]
        out = out * (1 - c)
    if p["rim_px"]:
        rim = np.clip(grow(m, p["rim_px"]) - m, 0, 1)[..., None]
        out = out * (1 - rim) + colorf(ctx.palette, p["rim"]) * rim
    mm = m[..., None]; out = out * (1 - mm) + colorf(ctx.palette, p["silhouette"]) * mm
    if p["grain"]: out = out + np.random.default_rng(ctx.i).normal(0, p["grain"], (H, W, 1)).astype(np.float32)
    a = ease("out_cubic", ctx.t / p["intro"]) if p["intro"] > 0 else 1
    if a < 1:
        edge = int(a * H); out = np.concatenate([out[:edge], F[edge:]], 0)
    return np.clip(out, 0, 1)
