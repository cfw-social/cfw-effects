import textwrap
import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..palette import colorf, color
from ..compose import rounded_rect_mask
from ..sprites import window, paste, cover, solid
from .. import text as T

def _bubble(txt, pal, mine, maxw, size=40):
    tc = color(pal, "text") if mine else color(pal, "outline")
    t = np.array(T.render("\n".join(textwrap.wrap(txt, 22)), "nunito-bold", size, tc, 0, align="left", spacing=0.1))
    pad = 26; w, h = min(maxw, t.shape[1] + 2 * pad), t.shape[0] + 2 * pad
    b = solid(h, w, colorf(pal, "secondary") if mine else np.clip(colorf(pal, "text") * 0.88, 0, 1))
    b[..., 3] = rounded_rect_mask(w, h, 30); paste(b, t, pad, pad); return b

@register("chat_window", defaults=dict(title="Chat", messages=[{"text": "look at this!", "at": 0.4, "mine": True},
                                                                       {"text": "love it", "at": 1.6, "mine": False}],
                                       bg="bg", width=0.86, height=0.78, video_h=0.5, intro=0.45, typing=True))
def chat_window(ctx, p):
    """The clip plays inside a generic chat window (no real app chrome): header with avatar + title, the video as a
    sent media bubble, then text bubbles pop in at their times with a typing indicator before each."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    ww, wh = int(W * p["width"]), int(H * p["height"])
    if "_win" not in st: st["_win"] = window(ww, wh, pal, p["title"])
    win, hd = st["_win"]; canvas = win.copy()
    vw = int(ww * 0.72); vh = int(wh * p["video_h"]); vx, vy = ww - vw - 30, hd + 30
    vid = solid(vh, vw, (0, 0, 0)); vid[..., :3] = cover(F, vw, vh); vid[..., 3] = rounded_rect_mask(vw, vh, 30)
    paste(canvas, vid, vx, vy); y = vy + vh + 24
    for k, msg in enumerate(p["messages"]):
        if ctx.t < msg["at"] - 0.6: break
        if ctx.t < msg["at"]:
            if p["typing"] and not msg.get("mine"):
                dots = solid(70, 150, np.clip(colorf(pal, "text") * 0.88, 0, 1)); dots[..., 3] = rounded_rect_mask(150, 70, 35)
                for d in range(3):
                    r = 9 + 4 * max(0, np.sin(ctx.t * 9 - d))
                    cv2.circle(dots, (40 + d * 35, 35), int(r), tuple(float(v) for v in colorf(pal, "outline")) + (1.0,), -1, cv2.LINE_AA)
                paste(canvas, dots, 30, y)
            break
        key = ("_b", k)
        if key not in st: st[key] = _bubble(msg["text"], pal, msg.get("mine", False), int(ww * 0.75))
        b = st[key]; pop = ease("out_back", (ctx.t - msg["at"]) / 0.3)
        bh, bw = b.shape[:2]; sb = cv2.resize(b, (max(2, int(bw * pop)), max(2, int(bh * pop))))
        x = ww - 30 - sb.shape[1] if msg.get("mine") else 30
        if y + bh < wh - 20: paste(canvas, sb, x, y)
        y += bh + 18
    k = lerp(1.25, 1.0, ease("out_cubic", ctx.t / p["intro"])); a = clamp(ctx.t / (p["intro"] * 0.6))
    out = np.empty_like(F); out[:] = colorf(pal, p["bg"])
    blur = cv2.GaussianBlur(cv2.resize(F, (W // 8, H // 8)), (0, 0), 3); out = out * 0.75 + cv2.resize(blur, (W, H)) * 0.25
    from ._util import place
    lay = place(canvas, W, H, W / 2, H / 2, k)
    al = lay[..., 3:4] * a
    out = out * (1 - al) + lay[..., :3] * al
    return F * (1 - a) + out * a if a < 1 else out
