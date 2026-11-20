import math
import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..compose import behind_only, rounded_rect_mask, shadow as mk_shadow
from ..palette import color, colorf
from .. import text as T
from ._util import place

def _fmt(v, f):
    if f == "mm:ss": return f"{v // 60:02d}:{v % 60:02d}"
    if f == "ss": return f"{v:02d}"
    return str(v)

def _tiles(s, pal, p, H):
    """Flip-clock style: each digit on a rounded tile with a split line. -> RGBA sprite."""
    th = int(H * 0.2); tw = int(th * 0.74); gap = int(th * 0.07); colon_w = int(th * 0.28)
    fs = int(th * 0.78)
    tile_c = colorf(pal, p["tile_color"]); txt_c = color(pal, p["text_color"]); line_c = colorf(pal, p["line_color"])
    widths = [colon_w if ch == ":" else tw for ch in s]
    Wt = sum(widths) + gap * (len(s) - 1); spr = np.zeros((th, Wt, 4), np.float32); x = 0
    rr = rounded_rect_mask(tw, th, int(th * 0.12))
    for ch, w in zip(s, widths):
        if ch == ":":
            for cy in (0.36, 0.64):
                cv2.circle(spr, (x + w // 2, int(th * cy)), int(th * 0.055), tuple(float(v) for v in colorf(pal, p["text_color"])) + (1.0,), -1, cv2.LINE_AA)
        else:
            tile = np.zeros((th, tw, 4), np.float32)
            grad = np.linspace(1.12, 0.9, th, dtype=np.float32)[:, None, None]
            tile[..., :3] = np.clip(tile_c * grad, 0, 1); tile[..., 3] = rr * p["tile_alpha"]
            g = np.array(T.render(ch, p["font"], fs, txt_c, 0))
            gy, gx = (th - g.shape[0]) // 2, (tw - g.shape[1]) // 2
            sub = tile[max(0, gy):gy + g.shape[0], max(0, gx):gx + g.shape[1]]; gg = g[:sub.shape[0], :sub.shape[1]]
            sub[..., :3] = sub[..., :3] * (1 - gg[..., 3:]) + gg[..., :3] * gg[..., 3:]; sub[..., 3] = np.maximum(sub[..., 3], gg[..., 3])
            yl = th // 2; tile[yl - 2:yl + 2, :, :3] = line_c; tile[yl - 2:yl + 2, :, 3] *= 1.0
            spr[:, x:x + tw] = tile
        x += w + gap
    return spr

@register("countdown_behind", defaults=dict(start_value=3, end_value=0, per_tick=None, format="mm:ss", style="tiles",
                                            font="antonio", color="accent", outline="outline", outline_px=10, y=0.34, width=0.86,
                                            tick_punch=0.2, flip=0.22, tile_color="bg", tile_alpha=0.92, text_color="text",
                                            line_color="hot", shadow=0.4, final_color="hot"))
def countdown_behind(ctx, p):
    """Big timer digits BEHIND the subject counting start_value -> end_value (one tick per `per_tick` s, default spreads
    across the effect). style tiles = flip-clock tiles with a flip on each tick; plain = big outlined digits with a punch."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    n = abs(p["start_value"] - p["end_value"]) + 1; step = -1 if p["start_value"] > p["end_value"] else 1
    per = p["per_tick"] or ctx.dur / n
    k = min(n - 1, int(ctx.t / per)); v = p["start_value"] + step * k; dt = ctx.t - k * per
    sy, scale = 1.0, 1.0
    if p["style"] == "tiles":
        x = dt / p["flip"] if k > 0 else 1.0
        if x < 1:
            sy = max(0.02, abs(math.cos(math.pi * x)))
            if x < 0.5: v -= step
    else:
        scale = lerp(1.18, 1.0, ease("out_cubic", dt / p["tick_punch"]))
    s = _fmt(v, p["format"])
    key = ("_cd", s, p["style"])
    if key not in st:
        if p["style"] == "tiles":
            spr = _tiles(s, ctx.palette, p, H)
        else:
            c = p["final_color"] if v == p["end_value"] else p["color"]
            size = T.fit_size(s, p["font"], W * p["width"], H * 0.4, start=900)
            spr = np.array(T.render(s, p["font"], size, color(ctx.palette, c), p["outline_px"], color(ctx.palette, p["outline"])))
        f = W * p["width"] / spr.shape[1]
        st[key] = cv2.resize(spr, (int(spr.shape[1] * f), int(spr.shape[0] * f)), interpolation=cv2.INTER_AREA)
    lay = place(st[key], W, H, W / 2, p["y"] * H, scale, 0.0, sy)
    a_in = clamp(ctx.t / 0.15)
    out = F
    if p["shadow"] > 0:
        sa = mk_shadow(lay[..., 3], 8, 18, 16, p["shadow"])
        out = behind_only(out, np.dstack([np.broadcast_to(colorf(ctx.palette, "outline"), (H, W, 3)), sa]).astype(np.float32), m, a_in)
    return behind_only(out, lay, m, a_in)
