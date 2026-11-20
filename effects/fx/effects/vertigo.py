import numpy as np
from ..core import register
from ..anim import ease
from ..compose import inpaint_bg, zoom_about
from ._util import anchor

@register("vertigo", defaults=dict(amount=0.35, direction="in", ease="in_out_sine", anchor="subject", streak=0.7,
                                   vignette=0.3, inpaint=True))
def vertigo(ctx, p):
    """Dolly-zoom feel: the background zooms (in or out) around the subject while the subject stays locked.
    amount: extra bg scale (0.35 = +35%); direction in|out; streak: radial motion-blur strength; vignette darkens bg edges."""
    F, m = ctx.frame, ctx.mask
    cx, cy = anchor(ctx, p)
    bg = inpaint_bg(F, m) if p["inpaint"] else F
    u = ease(p["ease"], ctx.u)
    k = 1 + p["amount"] * (u if p["direction"] == "in" else 1 - u)
    zb = zoom_about(bg, k, cx, cy)
    if p["streak"] > 0:
        du = abs(ease(p["ease"], min(1, ctx.u + 0.02)) - ease(p["ease"], max(0, ctx.u - 0.02))) / 0.04   # speed of the zoom
        s = p["streak"] * p["amount"] * du * 0.06
        if s > 0.002:
            zb = (zb + zoom_about(bg, k * (1 + s), cx, cy) + zoom_about(bg, k * (1 + 2 * s), cx, cy)) / 3
    if p["vignette"] > 0:
        st = ctx.state
        if "_vig" not in st:
            yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
            r = np.sqrt(((xx - ctx.W / 2) / ctx.W) ** 2 + ((yy - ctx.H / 2) / ctx.H) ** 2) * 1.6
            st["_vig"] = np.clip(1 - r ** 2, 0, 1)[..., None]
        v = 1 - p["vignette"] * u * (1 - st["_vig"])
        zb = zb * v
    mm = m[..., None]
    return zb * (1 - mm) + F * mm
