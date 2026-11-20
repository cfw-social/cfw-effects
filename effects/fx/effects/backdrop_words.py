import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..compose import behind_only, shadow as mk_shadow
from ..palette import color, colorf
from .. import text as T
from ._util import place

@register("backdrop_words", defaults=dict(words=None, text="BACKDROP", font="antonio", color="accent", outline="outline",
                                          outline_px=0, y=0.36, width=0.96, max_h=0.42, punch=0.3, punch_from=1.8, drift=0.06,
                                          angle=0.0, shadow=0.45, opacity=1.0, shake=6))
def backdrop_words(ctx, p):
    """Giant words BEHIND the subject with a punch-in (overshoot scale) and slow drift.
    words: [{"text": "BALANCE", "at": 0.0, "color": "accent"}, ...] (times relative to effect start) or text: "ONE WORD".
    Use "\\n" for stacked lines."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W
    words = p["words"] or [{"text": p["text"], "at": 0.0}]
    cur = None
    for w in words:
        if ctx.t >= w.get("at", 0.0): cur = w
    if cur is None: return F
    tw = ctx.t - cur.get("at", 0.0); txt = cur["text"]
    fname = cur.get("font", p["font"]); col = color(ctx.palette, cur.get("color", p["color"]))
    key = ("_bw", txt, fname, col)
    st = ctx.state
    if key not in st:
        size = T.fit_size(txt, fname, W * p["width"], H * p["max_h"], start=900)
        st[key] = np.array(T.render(txt, fname, size, col, p["outline_px"], color(ctx.palette, p["outline"]), spacing=-0.12))
    spr = st[key]
    k = lerp(p["punch_from"], 1.0, ease("out_back", tw / p["punch"])) * (1 + p["drift"] * clamp(tw / 3.0))
    jit = p["shake"] * max(0.0, 1 - tw / 0.25)
    rng = np.random.default_rng(int(tw * 60))
    lay = place(spr, W, H, W / 2 + rng.uniform(-jit, jit), p["y"] * H + rng.uniform(-jit, jit), k, cur.get("angle", p["angle"]))
    a_in = clamp(tw / 0.06) * p["opacity"]
    out = F
    if p["shadow"] > 0:
        sa = mk_shadow(lay[..., 3], 10, 16, 14, p["shadow"])
        sh = np.dstack([np.broadcast_to(colorf(ctx.palette, "outline"), (H, W, 3)), sa]).astype(np.float32)
        out = behind_only(out, sh, m, a_in)
    return behind_only(out, lay, m, a_in)
