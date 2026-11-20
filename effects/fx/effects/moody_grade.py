import numpy as np
from ..core import register
from ..anim import ease
from ..compose import desaturate
from ..palette import colorf

@register("moody_grade", defaults=dict(desat=0.7, vignette=0.55, crush=0.06, contrast=1.12, shadows="bg", tint=0.12, grain=0.035,
                                       ramp=0.4, subject_pop=0.25))
def moody_grade(ctx, p):
    """Moody look: heavy desaturation, contrast + crushed blacks, shadows tinted toward a palette colour, strong oval
    vignette, film grain. subject_pop keeps some original colour on the subject."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    a = ease("out_cubic", ctx.t / p["ramp"]) if p["ramp"] > 0 else 1
    if "_vig" not in st:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
        st["_vig"] = np.clip(1 - r ** 2.2, 0, 1)[..., None]
    g = desaturate(F, p["desat"])
    g = np.clip((g - 0.5) * p["contrast"] + 0.5 - p["crush"], 0, 1)
    lum = g.mean(2, keepdims=True)
    g = g + (colorf(ctx.palette, p["shadows"]) - g) * p["tint"] * (1 - lum)
    g = g * (1 - p["vignette"] * (1 - st["_vig"]))
    if p["subject_pop"]:
        mm = m[..., None] * p["subject_pop"]; g = g * (1 - mm) + np.clip(F * p["contrast"], 0, 1) * mm
    if p["grain"]: g = g + np.random.default_rng(ctx.i).normal(0, p["grain"], (H, W, 1)).astype(np.float32)
    return np.clip(F * (1 - a) + g * a, 0, 1)
