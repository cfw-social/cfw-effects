import textwrap
import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..compose import rounded_rect_mask, shadow as mk_shadow
from ..palette import color, colorf
from .. import text as T

@register("glass_card", defaults=dict(title="Try this", body="", pos=(0.07, 0.66), width=0.62, radius=40, blur=24,
                                      tint="text", tint_alpha=0.2, border_alpha=0.6, shadow=0.4, accent="accent",
                                      text_color="text", text_outline="outline", title_font="nunito", body_font="nunito-bold",
                                      title_size=76, body_size=54, wrap=22, padding=40, slide_from="left", slide=0.45,
                                      slide_out=0.3, layer="front", grain=0.02))
def glass_card(ctx, p):
    """Frosted-glass rounded note card (blurred backdrop, tint, bright rim, soft shadow, accent bar) with title + body text.
    Slides in from slide_from (left|right|bottom) with overshoot, slides out over the last slide_out s.
    layer front = over the subject; behind = subject passes in front of the card."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    if "_card" not in st:
        cw = int(W * p["width"]); pad = p["padding"]
        tc, oc = color(pal, p["text_color"]), color(pal, p["text_outline"])
        title = np.array(T.render(p["title"], p["title_font"], p["title_size"], color(pal, p["accent"]), 3, oc, align="left")) if p["title"] else None
        body = None
        if p["body"]:
            wrapped = "\n".join(textwrap.wrap(p["body"], p["wrap"]))
            body = np.array(T.render(wrapped, p["body_font"], p["body_size"], tc, 2, oc, align="left", spacing=0.12))
        h = pad * 2 + (title.shape[0] if title is not None else 0) + (body.shape[0] + 6 if body is not None else 0)
        rr = rounded_rect_mask(cw, h, p["radius"])
        rim = np.clip(rr - cv2.erode(rr, np.ones((5, 5), np.uint8)), 0, 1)
        st["_card"] = dict(w=cw, h=h, rr=rr, rim=rim, title=title, body=body)
    c = st["_card"]; cw, ch = c["w"], c["h"]
    tx, ty = int(p["pos"][0] * W), int(p["pos"][1] * H)
    uin = ease("out_back", ctx.t / p["slide"]) if p["slide"] > 0 else 1.0
    uout = ease("in_cubic", (ctx.t - (ctx.dur - p["slide_out"])) / p["slide_out"]) if p["slide_out"] > 0 and ctx.t > ctx.dur - p["slide_out"] else 0.0
    sf = p["slide_from"]
    off = {"left": (-(tx + cw + 40), 0), "right": (W - tx + 40, 0), "bottom": (0, H - ty + 40)}[sf]
    x = int(tx + off[0] * (1 - uin) + off[0] * uout); y = int(ty + off[1] * (1 - uin) + off[1] * uout)
    out = F.copy()
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + cw), min(H, y + ch)
    if x1 <= x0 or y1 <= y0: return F
    sx0, sy0 = x0 - x, y0 - y; sx1, sy1 = sx0 + (x1 - x0), sy0 + (y1 - y0)
    rr = c["rr"][sy0:sy1, sx0:sx1][..., None]
    # shadow under the card
    if p["shadow"] > 0:
        full = np.zeros((H, W), np.float32); full[y0:y1, x0:x1] = rr[..., 0]
        sa = mk_shadow(full, 0, 26, 28, p["shadow"])[..., None]
        out = out * (1 - sa) + colorf(pal, "outline") * 0.5 * sa
    # frosted backdrop
    mg = int(p["blur"] * 3)
    bx0, by0, bx1, by1 = max(0, x0 - mg), max(0, y0 - mg), min(W, x1 + mg), min(H, y1 + mg)
    blur = cv2.GaussianBlur(out[by0:by1, bx0:bx1], (0, 0), p["blur"])[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]
    tint = colorf(pal, p["tint"])
    g = np.linspace(1.0, 0.65, ch, dtype=np.float32)[sy0:sy1, None, None]
    glass = blur * (1 - p["tint_alpha"] * g) + tint * p["tint_alpha"] * g
    if p["grain"]: glass = glass + np.random.default_rng(ctx.i).normal(0, p["grain"], glass.shape[:2])[..., None].astype(np.float32)
    rim = c["rim"][sy0:sy1, sx0:sx1][..., None] * p["border_alpha"]
    glass = glass * (1 - rim) + tint * rim
    # accent bar
    ab = np.zeros((ch, cw), np.float32); cv2.rectangle(ab, (p["padding"] // 2 - 4, p["padding"]), (p["padding"] // 2 + 4, ch - p["padding"]), 1.0, -1)
    abm = ab[sy0:sy1, sx0:sx1][..., None]
    glass = glass * (1 - abm) + colorf(pal, p["accent"]) * abm
    reg = out[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = reg * (1 - rr) + np.clip(glass, 0, 1) * rr
    # text
    yy = y + p["padding"]
    for spr in (c["title"], c["body"]):
        if spr is None: continue
        from ..compose import over
        over(out, spr, x + p["padding"] + 6, yy - 8); yy += spr.shape[0] + 6
    if p["layer"] == "behind":
        mm = m[..., None]; out = out * (1 - mm) + F * mm
    return out
