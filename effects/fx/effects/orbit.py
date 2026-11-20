import math
import numpy as np, cv2
from ..core import register
from ..anim import ease, clamp
from ..compose import behind_only
from ..sprites import ClipBank, card, with_shadow
from ._util import subject, place

@register("orbit", defaults=dict(clips=None, count=5, card_w=0.3, aspect=1.6, radius_x=0.42, radius_y=0.07, y=0.45,
                                 speed=0.35, tilt=8.0, min_scale=0.55, border="text", radius=26, intro=0.5, self_delay=12))
def orbit(ctx, p):
    """Cards playing clips orbit the subject on a tilted 3D ellipse; depth-sorted so the far half passes BEHIND the
    subject and the near half in FRONT. clips: list of paths/{src,in} (none = delayed copies of this clip).
    speed = turns per second; y = orbit centre (fraction of height)."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    if "_bank" not in st:
        cw = int(W * p["card_w"]); st["_bank"] = ClipBank(p["clips"], (cw, int(cw * p["aspect"])), int(round(ctx.fps)))
    bank = st["_bank"]; cw, chh = bank.size
    cx, _, _ = subject(ctx)
    cy = p["y"] * H; grow = ease("out_back", ctx.t / p["intro"]) if p["intro"] > 0 else 1
    from ..palette import colorf
    cards = []
    for k in range(p["count"]):
        th = 2 * math.pi * (p["speed"] * ctx.t + k / p["count"])
        z = math.sin(th)                       # +1 = nearest
        x = cx + math.cos(th) * W * p["radius_x"] * grow; y = cy + z * H * p["radius_y"] * grow
        sc = (p["min_scale"] + (1 - p["min_scale"]) * (z + 1) / 2) * grow
        cards.append((z, x, y, sc, k, math.cos(th)))
    out = F
    for z, x, y, sc, k, c in sorted(cards):
        img = bank.frame(k, ctx.i + k * 7, ctx, delay=p["self_delay"] * (k + 1))
        spr = card(img, cw, chh, p["radius"], 8, colorf(ctx.palette, p["border"]))
        spr = spr * np.float32(0.55 + 0.45 * (z + 1) / 2) if False else spr
        if z < 0: spr = spr.copy(); spr[..., :3] *= 0.6 + 0.4 * (z + 1)       # far cards darker
        lay = place(spr, W, H, x, y, max(0.05, sc), p["tilt"] * c)
        if z < 0: out = behind_only(out, lay, m)
        else:
            a = lay[..., 3:4]; out = out * (1 - a) + lay[..., :3] * a
    return out
