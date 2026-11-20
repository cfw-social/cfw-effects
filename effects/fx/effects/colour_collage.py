import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..palette import colorf, color
from ..compose import rounded_rect_mask
from ..sprites import solid, paste
from .. import text as T
from ._util import place

@register("colour_collage", defaults=dict(bg="secondary", blocks=[{"text": "BIG", "color": "accent", "pos": [0.32, 0.2], "angle": -6},
                                                                   {"text": "BOLD", "color": "hot", "pos": [0.66, 0.36], "angle": 5},
                                                                   {"text": "BLOCKS", "color": "bg", "pos": [0.4, 0.78], "angle": -3}],
                                          text_color="text", font="antonio", block_h=0.13, stagger=0.25, slide=0.35, keep_bg=False))
def colour_collage(ctx, p):
    """Poster collage: solid palette background, big rotated colour blocks with words slide in (staggered) BEHIND the
    cut-out subject. keep_bg=True keeps the original background under the blocks instead of a solid fill."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    out = F.copy() if p["keep_bg"] else np.broadcast_to(colorf(pal, p["bg"]), F.shape).astype(np.float32).copy()
    bh = int(H * p["block_h"])
    for k, b in enumerate(p["blocks"]):
        key = ("_cb", k)
        if key not in st:
            size = int(bh * 0.78); t = np.array(T.render(b["text"], p["font"], size, color(pal, b.get("text_color", p["text_color"])), 0))
            w = t.shape[1] + int(bh * 0.6); s = solid(bh, w, colorf(pal, b["color"])); s[..., 3] = rounded_rect_mask(w, bh, 12)
            paste(s, t, (w - t.shape[1]) // 2, (bh - t.shape[0]) // 2); st[key] = s
        u = ease("out_back", (ctx.t - k * p["stagger"]) / p["slide"])
        if u <= 0: continue
        side = -1 if k % 2 == 0 else 1
        x = lerp(W / 2 + side * W, b["pos"][0] * W, u); L = place(st[key], W, H, x, b["pos"][1] * H, 1.0, b.get("angle", 0))
        a = L[..., 3:4]; out = out * (1 - a) + L[..., :3] * a
    mm = m[..., None]
    return out * (1 - mm) + F * mm
