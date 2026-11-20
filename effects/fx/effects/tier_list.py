import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..palette import colorf, color
from ..compose import rounded_rect_mask
from ..sprites import paste, solid, card, cover
from .. import text as T
from ._util import place

@register("tier_list", defaults=dict(tiers=["S", "A", "B", "C"], colors=["hot", "accent", "secondary", "text"],
                                     items=[{"label": "idea one", "tier": 0}, {"label": "idea two", "tier": 2}],
                                     drop_tier=0, drop_at=1.2, video_h=0.46, board_bg="bg", fly=0.45))
def tier_list(ctx, p):
    """Generic tier board in the lower part of the frame (coloured tier labels + rows with text chips) under the live
    clip; at drop_at a snapshot card of the clip flies into tier `drop_tier`."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    vh = int(H * p["video_h"]); bh = H - vh; n = len(p["tiers"]); rh = bh // n; lw = int(rh * 1.0)
    out = np.empty_like(F); out[:] = colorf(pal, p["board_bg"])
    out[:vh] = cover(F, W, vh)
    if "_board" not in st:
        b = np.zeros((bh, W, 4), np.float32)
        for k, (tname, cn) in enumerate(zip(p["tiers"], p["colors"])):
            y = k * rh
            b[y:y + rh - 6, :lw, :3] = colorf(pal, cn); b[y:y + rh - 6, :lw, 3] = 1
            b[y:y + rh - 6, lw + 6:, :3] = colorf(pal, "outline") * 1.6; b[y:y + rh - 6, lw + 6:, 3] = 1
            t = np.array(T.render(tname, "nunito", int(rh * 0.5), color(pal, "outline"), 0)); paste(b, t, (lw - t.shape[1]) // 2, y + (rh - t.shape[0]) // 2)
        slots = [0] * n
        for it in p["items"]:
            k = it["tier"]; chip_h = int(rh * 0.62)
            t = np.array(T.render(it["label"], "nunito-bold", int(chip_h * 0.45), color(pal, "outline"), 0))
            cw = t.shape[1] + 50; c = solid(chip_h, cw, colorf(pal, "text")); c[..., 3] = rounded_rect_mask(cw, chip_h, 18)
            paste(c, t, 25, (chip_h - t.shape[0]) // 2)
            x = lw + 30 + slots[k]; paste(b, c, x, k * rh + (rh - 6 - chip_h) // 2); slots[k] += cw + 20
        st["_board"] = b; st["_slots"] = slots
    b = st["_board"]; a = b[..., 3:4]; out[vh:] = out[vh:] * (1 - a) + b[..., :3] * a
    if ctx.t >= p["drop_at"]:
        if "_snap" not in st: st["_snap"] = card(F, int(rh * 0.9 * 0.75), int(rh * 0.9), 14, 5, colorf(pal, "accent"))
        u = ease("in_out_cubic", (ctx.t - p["drop_at"]) / p["fly"]); k = p["drop_tier"]
        x1 = lw + 30 + st["_slots"][k] + st["_snap"].shape[1] / 2; y1 = vh + k * rh + (rh - 6) / 2
        x = lerp(W / 2, x1, u); y = lerp(vh * 0.5, y1, u) - np.sin(u * np.pi) * 160
        L = place(st["_snap"], W, H, x, y, lerp(2.2, 1.0, u), lerp(-10, 0, u))
        al = L[..., 3:4]; out = out * (1 - al) + L[..., :3] * al
    return out
