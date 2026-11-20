import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..palette import colorf

@register("dot_mosaic", defaults=dict(cell=26, target="background", dot="secondary", dot2="accent", bg="bg", reveal=0.5,
                                      colour_mode="duotone", gamma=0.9))
def dot_mosaic(ctx, p):
    """Halftone dot mosaic: the frame is re-drawn as a grid of dots sized by brightness (duotone palette dots or
    'source' colours) on the bg colour. target background (subject stays real) | all. Dots grow in over `reveal` s."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; c = p["cell"]
    gh, gw = H // c + 1, W // c + 1
    small = cv2.resize(F, (gw, gh), interpolation=cv2.INTER_AREA)
    lum = (small @ np.array([0.299, 0.587, 0.114], np.float32)) ** p["gamma"]
    g = ease("out_cubic", ctx.t / p["reveal"]) if p["reveal"] > 0 else 1
    if "_dots" not in st:   # pre-render dot sprites by radius level
        st["_dots"] = []
        for lv in range(17):
            r = (lv / 16) * c * 0.62; d = np.zeros((c, c), np.float32)
            if r > 0.3: cv2.circle(d, (c * 4 // 2, c * 4 // 2), int(r * 4), 1.0, -1, cv2.LINE_AA, 2)
            st["_dots"].append(d)
    lvl = np.clip((lum * g * 16).round().astype(int), 0, 16)
    alpha = np.zeros((gh * c, gw * c), np.float32)
    for lv in range(1, 17):
        ys, xs = np.nonzero(lvl == lv)
        d = st["_dots"][lv]
        for y, x in zip(ys, xs): alpha[y * c:(y + 1) * c, x * c:(x + 1) * c] = d
    alpha = alpha[:H, :W, None]
    out = np.empty_like(F); out[:] = colorf(ctx.palette, p["bg"])
    if p["colour_mode"] == "source":
        col = cv2.resize(small, (gw * c, gh * c), interpolation=cv2.INTER_NEAREST)[:H, :W]
    else:
        t = cv2.resize(lum, (gw * c, gh * c), interpolation=cv2.INTER_NEAREST)[:H, :W, None]
        col = colorf(ctx.palette, p["dot"]) * (1 - t) + colorf(ctx.palette, p["dot2"]) * t
    out = out * (1 - alpha) + col * alpha
    if p["target"] == "background":
        mm = m[..., None]; out = out * (1 - mm) + F * mm
    return out
