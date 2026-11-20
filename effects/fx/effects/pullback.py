import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..palette import colorf, color
from ..compose import rounded_rect_mask
from ..sprites import phone, paste, solid, with_shadow, cover
from .. import text as T
from ._util import place

def _feed_ui(sw, sh, pal, handle, caption):
    """Generic short-video feed overlay (no real app marks): handle, caption, follow pill, round action buttons."""
    ui = np.zeros((sh, sw, 4), np.float32); s = sw / 500
    g = np.linspace(0, 0.55, sh // 3, dtype=np.float32)[:, None]; ui[sh - sh // 3:, :, 3] = g; ui[..., :3] = 0
    tc = color(pal, "text")
    h = np.array(T.render(handle, "nunito", int(30 * s), tc, 0)); paste(ui, h, int(24 * s), sh - int(150 * s))
    c = np.array(T.render(caption, "nunito-bold", int(24 * s), tc, 0)); paste(ui, c, int(24 * s), sh - int(105 * s))
    pill = solid(int(40 * s), int(110 * s), colorf(pal, "accent")); pill[..., 3] = rounded_rect_mask(pill.shape[1], pill.shape[0], int(20 * s))
    paste(ui, pill, int(30 * s) + h.shape[1], sh - int(150 * s))
    for k in range(4):
        cy = sh - int((380 - k * 75) * s); cx = sw - int(45 * s)
        cv2.circle(ui, (cx, cy), int(24 * s), (*[v / 255 for v in tc], 0.9), max(2, int(4 * s)), cv2.LINE_AA)
    return ui

@register("pullback", defaults=dict(at=0.3, dur=0.7, phone_w=0.62, bg="secondary", handle="@yourhandle", caption="your caption here",
                                    scroll_at=None, ui=True))
def pullback(ctx, p):
    """Camera pulls back: the full-frame clip shrinks into a generic phone showing a short-video feed UI, on a
    palette background. Optional scroll_at: the feed swipes up to the next (blurred) post."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    pw = int(W * p["phone_w"]); ph = int(pw * 2.05)
    u = ease("in_out_cubic", (ctx.t - p["at"]) / p["dur"])
    if u <= 0: return F
    spr, (bx, by, sw, sh) = phone(pw, ph, None)
    scr = cover(F, sw, sh).copy()
    if p["scroll_at"] is not None and ctx.t > p["scroll_at"]:
        v = ease("in_out_cubic", (ctx.t - p["scroll_at"]) / 0.45); off = int(v * sh)
        nxt = cv2.GaussianBlur(scr, (0, 0), 12) * 0.7
        scr = np.concatenate([scr[off:], nxt[:off]], 0)
    if p["ui"]:
        if "_ui" not in st: st["_ui"] = _feed_ui(sw, sh, pal, p["handle"], p["caption"])
        a = st["_ui"][..., 3:4]; scr = scr * (1 - a) + st["_ui"][..., :3] * a
    m = rounded_rect_mask(sw, sh, max(2, int(pw * 0.16) - bx))[..., None]
    spr[by:by + sh, bx:bx + sw, :3] = spr[by:by + sh, bx:bx + sw, :3] * (1 - m) + scr * m
    spr, pad = with_shadow(spr, 0, 30, 30, 0.5)
    k = lerp(W / sw * 1.02, 1.0, u)                    # start: screen fills the frame
    out = np.broadcast_to(colorf(pal, p["bg"]), F.shape).astype(np.float32).copy()
    L = place(spr, W, H, W / 2, H / 2, k)
    a = L[..., 3:4]; out = out * (1 - a) + L[..., :3] * a
    return out
