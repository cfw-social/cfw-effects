import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..palette import colorf, color
from ..sprites import ClipBank, card
from ..compose import over
from .. import text as T

@register("grid_collage", defaults=dict(clips=None, cols=4, rows=6, gap=10, bg="bg", labels=None, intro=0.6, title=None,
                                        include_self=False, radius=12))
def grid_collage(ctx, p):
    """All-in-one grid: cols x rows tiles each playing a clip (e.g. every effect's render), cascading in, with optional
    small labels per tile and a title. include_self puts the live clip in the first tile."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    c, r, g = p["cols"], p["rows"], p["gap"]
    top = int(H * 0.07) if p["title"] else 0
    tw = (W - g * (c + 1)) // c; th = (H - top - g * (r + 1)) // r
    if "_bank" not in st: st["_bank"] = ClipBank(p["clips"], (tw, th), int(round(ctx.fps)))
    bank = st["_bank"]; out = np.empty_like(F); out[:] = colorf(pal, p["bg"])
    if p["title"]:
        t = np.array(T.render(p["title"], "nunito", int(top * 0.55), color(pal, "text"), 0)); over(out, t, (W - t.shape[1]) // 2, (top - t.shape[0]) // 2 + g)
    for k in range(c * r):
        rr, cc = divmod(k, c); u = ease("out_cubic", (ctx.t - (rr * c + cc) * 0.02) / p["intro"]) if p["intro"] > 0 else 1
        if u <= 0: continue
        if p["include_self"] and k == 0: img = F
        elif bank.items or not p["clips"]:
            idx = k - (1 if p["include_self"] else 0)
            if p["clips"] and idx >= len(bank.items): continue
            img = bank.frame(idx, ctx.i, ctx, delay=k * 3)
        spr = card(img, tw, th, p["radius"], 0)
        if p["labels"] and k < len(p["labels"]) and p["labels"][k]:
            lab = np.array(T.render(p["labels"][k], "nunito", max(14, th // 12), color(pal, "text"), 3, color(pal, "outline")))
            over(spr, lab[..., :4], 8, th - lab.shape[0] - 6) if False else None
            from ..sprites import paste; paste(spr, lab, 8, th - lab.shape[0] - 6)
        spr = spr.copy(); spr[..., 3] *= u
        over(out, spr, g + cc * (tw + g), top + g + rr * (th + g) + int((1 - u) * 40))
    return out
