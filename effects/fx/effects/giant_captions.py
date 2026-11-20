import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..palette import color
from ..compose import behind_only
from .. import text as T
from ._util import place

@register("giant_captions", defaults=dict(text="MAKE IT BIG AND BOLD", words=None, per_word=None, lines=3, font="antonio",
                                          colors=["text", "accent", "secondary"], outline="outline", outline_px=8, top=0.12,
                                          bottom=0.62, layer="behind", pop=0.18, keep=True))
def giant_captions(ctx, p):
    """Screen-filling stacked caption: words appear one at a time (per_word s or spread over the effect), each set as
    its own full-width line so the type is enormous; colours cycle through `colors`. keep=False shows only the
    latest `lines` words. layer behind|front."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    words = p["words"] or [{"text": w} for w in p["text"].split()]
    per = p["per_word"] or ctx.dur / max(1, len(words)) * 0.85
    for k, w in enumerate(words): w.setdefault("at", k * per)
    shown = [k for k, w in enumerate(words) if ctx.t >= w["at"]]
    if not shown: return F
    vis = shown[-p["lines"]:] if not p["keep"] else shown[max(0, len(shown) - p["lines"]):]
    slot_h = (p["bottom"] - p["top"]) * H / p["lines"]
    lay = np.zeros((H, W, 4), np.float32)
    for j, k in enumerate(vis):
        w = words[k]; c = color(pal, w.get("color", p["colors"][k % len(p["colors"])]))
        key = ("_gc", k)
        if key not in st:
            size = T.fit_size(w["text"], p["font"], W * 0.94, slot_h * 1.05, start=900)
            st[key] = np.array(T.render(w["text"], p["font"], size, c, p["outline_px"], color(pal, p["outline"])))
        s = lerp(1.35, 1.0, ease("out_back", (ctx.t - w["at"]) / p["pop"]))
        L = place(st[key], W, H, W / 2, p["top"] * H + slot_h * (j + 0.5), s)
        a = L[..., 3:4]; lay[..., :3] = lay[..., :3] * (1 - a) + L[..., :3] * a; lay[..., 3:4] = np.maximum(lay[..., 3:4], a)
    if p["layer"] == "behind": return behind_only(F, lay, m)
    a = lay[..., 3:4]; return F * (1 - a) + lay[..., :3] * a
