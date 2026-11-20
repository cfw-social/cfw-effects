import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..palette import colorf, color
from .. import text as T
from ..compose import over
from ._util import subject

@register("locked_on", defaults=dict(target="centre", zoom=1.35, ramp=0.5, color="hot", thickness=6, bracket=0.22,
                                     reticle=True, label_text="LOCKED", follow=0.85, pad=40))
def locked_on(ctx, p):
    """Tracks a point on the subject (target: head | centre | [x,y] fraction), recentres + zooms the frame on it, and
    draws corner brackets around the subject plus a crosshair reticle and a small label."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    cx, cy, (x0, y0, x1, y1) = subject(ctx, smooth=p["follow"])
    if isinstance(p["target"], (list, tuple)): tx, ty = p["target"][0] * W, p["target"][1] * H
    elif p["target"] == "head": tx, ty = cx, y0 + (y1 - y0) * 0.15
    else: tx, ty = cx, cy
    a = ease("in_out_cubic", ctx.t / p["ramp"]) if p["ramp"] > 0 else 1
    k = lerp(1.0, p["zoom"], a)
    ox, oy = lerp(W / 2, tx, a), lerp(H / 2, ty, a)          # point that ends up at frame centre
    M = np.float32([[k, 0, W / 2 - k * ox], [0, k, H / 2 - k * oy]])
    out = cv2.warpAffine(F, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # bbox in output coords
    bx0, by0 = M @ np.array([x0 - p["pad"], y0 - p["pad"], 1]); bx1, by1 = M @ np.array([x1 + p["pad"], y1 + p["pad"], 1])
    hx, hy = M @ np.array([tx, ty, 1])
    mg = 50; bx0, by0 = max(mg, bx0), max(mg * 3, by0); bx1, by1 = min(W - mg, bx1), min(H - mg * 3, by1)
    lay = np.zeros((H, W), np.float32); th = p["thickness"]
    L = int(min(bx1 - bx0, by1 - by0) * p["bracket"])
    snap = 1 + 0.25 * (1 - ease("out_cubic", ctx.t / 0.35))   # brackets snap inward
    mx, my = (bx0 + bx1) / 2, (by0 + by1) / 2
    bx0, bx1 = mx + (bx0 - mx) * snap, mx + (bx1 - mx) * snap; by0, by1 = my + (by0 - my) * snap, my + (by1 - my) * snap
    for (px, py, sx, sy) in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        px, py = int(px), int(py)
        cv2.line(lay, (px, py), (px + sx * L, py), 1.0, th, cv2.LINE_AA); cv2.line(lay, (px, py), (px, py + sy * L), 1.0, th, cv2.LINE_AA)
    if p["reticle"]:
        r = int(36 + 10 * np.sin(ctx.t * 6)); hx, hy = int(hx), int(hy)
        cv2.circle(lay, (hx, hy), r, 1.0, max(2, th // 2), cv2.LINE_AA)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv2.line(lay, (hx + dx * (r - 14), hy + dy * (r - 14)), (hx + dx * (r + 22), hy + dy * (r + 22)), 1.0, max(2, th // 2), cv2.LINE_AA)
    c = colorf(ctx.palette, p["color"]); al = lay[..., None]
    out = out * (1 - al) + c * al
    if p["label_text"] and (int(ctx.t * 4) % 2 == 0 or ctx.t > 1.0):
        spr = np.array(T.render(p["label_text"], "mono", 40, color(ctx.palette, p["color"]), 3, color(ctx.palette, "outline")))
        over(out, spr, int(bx0), int(by0) - spr.shape[0] - 8)
    return out
