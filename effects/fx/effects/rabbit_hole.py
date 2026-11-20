import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..palette import colorf

@register("rabbit_hole", defaults=dict(depth=7, scale=0.78, spin=8.0, spin_speed=20.0, border=10, border_color="accent",
                                       alt_color="secondary", subject_front=True, intro=0.6))
def rabbit_hole(ctx, p):
    """Recursive frame tunnel: the frame contains a smaller, rotated copy of itself, repeated `depth` times, with
    alternating coloured borders; the twist animates (spin deg per level, spin_speed deg/s). Subject stays in front."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W
    a = ease("out_cubic", ctx.t / p["intro"]) if p["intro"] > 0 else 1
    ang = (p["spin"] + p["spin_speed"] * ctx.t) * a; s = 1 - (1 - p["scale"]) * a
    b = p["border"]; c1, c2 = colorf(ctx.palette, p["border_color"]), colorf(ctx.palette, p["alt_color"])
    # small working res for speed
    w, h = W // 2, H // 2
    base = cv2.resize(F, (w, h), interpolation=cv2.INTER_AREA)
    img = base.copy()
    for k in range(p["depth"]):
        framed = img.copy()
        cv2.rectangle(framed, (0, 0), (w - 1, h - 1), tuple(float(v) for v in (c1 if k % 2 == 0 else c2)), b)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, s)
        warped = cv2.warpAffine(framed, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        msk = cv2.warpAffine(np.ones((h, w), np.float32), M, (w, h), flags=cv2.INTER_LINEAR)[..., None]
        img = base * (1 - msk) + warped * msk
    out = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    if p["subject_front"]:
        mm = m[..., None]; out = out * (1 - mm) + F * mm
    return out
