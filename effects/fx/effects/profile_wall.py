import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..palette import colorf, color
from ..compose import over
from ..sprites import ClipBank, card
from .. import text as T

@register("profile_wall", defaults=dict(clips=None, cols=3, rows=4, gap=14, count_from=0, count_to=17355, count_label="views",
                                        count_dur=None, highlight="accent", bg="bg", intro=0.4, font="antonio", self_delay=6, header=0.24))
def profile_wall(ctx, p):
    """Profile-grid wall: cols x rows tiles all playing (clips or delayed copies of this clip), the centre tile is the
    live clip with an accent frame, tiles cascade in, and a big number counts up (ease-out) with a label."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    c, r, g = p["cols"], p["rows"], p["gap"]; tw = (W - g * (c + 1)) // c; th = int(tw * 16 / 9)
    top = int(H * p["header"])
    if th * r + g * (r + 1) > H - top: th = (H - top - g * (r + 1)) // r
    if "_bank" not in st: st["_bank"] = ClipBank(p["clips"], (tw, th), int(round(ctx.fps)))
    bank = st["_bank"]
    out = np.empty_like(F); out[:] = colorf(pal, p["bg"])
    y0 = top + (H - top - (th * r + g * (r - 1))) // 2; mid = (r // 2) * c + c // 2
    for k in range(c * r):
        rr, cc = divmod(k, c); delay = (rr + cc) * 0.05
        u = ease("out_back", (ctx.t - delay) / p["intro"]) if p["intro"] > 0 else 1
        if u <= 0: continue
        img = F if k == mid else bank.frame(k, ctx.i + k * 5, ctx, delay=p["self_delay"] * (k % 7 + 1))
        spr = card(img, tw, th, 16, 6 if k == mid else 0, colorf(pal, p["highlight"]))
        if u < 0.999:
            spr = cv2.resize(spr, (max(2, int(tw * u)), max(2, int(th * u))))
        x = g + cc * (tw + g) + (tw - spr.shape[1]) // 2; y = y0 + rr * (th + g) + (th - spr.shape[0]) // 2
        over(out, spr, x, y)
    cd = p["count_dur"] or ctx.dur * 0.8
    v = int(lerp(p["count_from"], p["count_to"], ease("out_expo", ctx.t / cd)))
    num = np.array(T.render(f"{v:,}", p["font"], int(H * p["header"] * 0.45), color(pal, "text"), 12, color(pal, "outline")))
    lab = np.array(T.render(p["count_label"], "nunito", int(H * p["header"] * 0.18), color(pal, p["highlight"]), 6, color(pal, "outline")))
    over(out, num, (W - num.shape[1]) // 2, int(H * 0.075)); over(out, lab, (W - lab.shape[1]) // 2, int(H * 0.075) + num.shape[0] - 20)
    return out
