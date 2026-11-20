import numpy as np, cv2
from ..core import register
from ..anim import ease, envelope, clamp
from ..compose import rounded_rect_mask, over, desaturate
from ..palette import color, colorf
from .. import text as T

@register("label", defaults=dict(text="EFFECT", index=None, y=0.07, size=46, bg="bg", bg_alpha=0.82, color="text", accent="accent",
                                 fade=0.25, font="nunito", out=0.25))
def label(ctx, p):
    """Small pill chip naming what's on screen, e.g. '03  SPOTLIGHT'. Drops in, fades out at the end."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    if "_lab" not in st:
        oc = color(pal, "outline")
        parts = []
        if p["index"] is not None: parts.append(np.array(T.render(f"{int(p['index']):02d}", p["font"], p["size"], color(pal, p["accent"]), 0, oc)))
        parts.append(np.array(T.render(p["text"], p["font"], p["size"], color(pal, p["color"]), 0, oc)))
        gap = int(p["size"] * 0.45); padx, pady = int(p["size"] * 0.7), int(p["size"] * 0.3)
        w = sum(x.shape[1] for x in parts) + gap * (len(parts) - 1) + 2 * padx; h = max(x.shape[0] for x in parts) + 2 * pady
        chip = np.zeros((h, w, 4), np.float32); chip[..., :3] = colorf(pal, p["bg"]); chip[..., 3] = rounded_rect_mask(w, h, h // 2) * p["bg_alpha"]
        x = padx
        for part in parts:
            sub = chip[pady:pady + part.shape[0], x:x + part.shape[1]]; a = part[..., 3:]
            sub[..., :3] = sub[..., :3] * (1 - a) + part[..., :3] * a; sub[..., 3:] = np.maximum(sub[..., 3:], a); x += part.shape[1] + gap
        st["_lab"] = chip
    chip = st["_lab"]
    a = envelope(ctx.t, 0, ctx.dur, p["fade"], p["out"])
    dy = int((1 - ease("out_back", ctx.t / max(1e-3, p["fade"] * 1.6))) * -40)
    out = F.copy(); over(out, chip, (W - chip.shape[1]) // 2, int(p["y"] * H) + dy, a)
    return out

@register("redact", defaults=dict(rects=[], mode="blur", color="bg", strength=28))
def redact(ctx, p):
    """Hide regions (signage, names, screens). rects: [[x,y,w,h], ...] as frame fractions. mode blur|pixelate|fill."""
    out = ctx.frame.copy(); H, W = ctx.H, ctx.W
    for (x, y, w, h) in p["rects"]:
        x0, y0, x1, y1 = int(x * W), int(y * H), int((x + w) * W), int((y + h) * H)
        r = out[y0:y1, x0:x1]
        if not r.size: continue
        if p["mode"] == "fill": out[y0:y1, x0:x1] = colorf(ctx.palette, p["color"])
        elif p["mode"] == "pixelate":
            s = cv2.resize(r, (max(1, r.shape[1] // p["strength"]), max(1, r.shape[0] // p["strength"])), interpolation=cv2.INTER_AREA)
            out[y0:y1, x0:x1] = cv2.resize(s, (r.shape[1], r.shape[0]), interpolation=cv2.INTER_NEAREST)
        else: out[y0:y1, x0:x1] = cv2.GaussianBlur(r, (0, 0), p["strength"])
    return out

@register("grade", defaults=dict(contrast=1.06, saturation=1.08, warmth=0.02, lift=0.0))
def grade(ctx, p):
    """Simple global grade: contrast around mid-grey, saturation, warmth (+R -B), lift."""
    f = (ctx.frame - 0.5) * p["contrast"] + 0.5 + p["lift"]
    f = desaturate(f, 1 - p["saturation"])
    f[..., 0] += p["warmth"]; f[..., 2] -= p["warmth"]
    return np.clip(f, 0, 1)
