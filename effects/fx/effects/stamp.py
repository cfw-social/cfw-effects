import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp, clamp
from ..palette import colorf
from ..compose import value_noise, rounded_rect_mask
from .. import text as T
from ._util import place

@register("stamp", defaults=dict(text="NAILED IT", at=0.3, color="hot", pos=(0.5, 0.3), angle=-12.0, width=0.78, border=14,
                                 from_scale=3.2, slam=0.14, shake=26, grunge=0.45, seed=2, font="nunito"))
def stamp(ctx, p):
    """Rubber-stamp slam: bordered text drops from big+transparent to full size at `at` s, the whole frame shakes
    on impact, ink has procedural grunge (patchy coverage + speckle)."""
    F = ctx.frame; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    if "_st" not in st:
        c = colorf(pal, p["color"]); t = np.array(T.render(p["text"], p["font"], 200, tuple(int(v * 255) for v in c), 0))
        pad = 50; w, h = t.shape[1] + 2 * pad, t.shape[0] + 2 * pad
        ring = rounded_rect_mask(w, h, 30); inner = np.zeros_like(ring); b = p["border"]
        inner[b:h - b, b:w - b] = rounded_rect_mask(w - 2 * b, h - 2 * b, 22); ring = np.clip(ring - inner, 0, 1)
        alpha = np.maximum(ring, 0); alpha[pad:pad + t.shape[0], pad:pad + t.shape[1]] = np.maximum(alpha[pad:pad + t.shape[0], pad:pad + t.shape[1]], t[..., 3])
        n = value_noise(h, w, 18, p["seed"], 3); speck = np.random.default_rng(p["seed"]).random((h, w)) > 0.06
        alpha = alpha * np.clip((n - p["grunge"] * 0.6) / 0.25, 0.15, 1) * speck
        spr = np.zeros((h, w, 4), np.float32); spr[..., :3] = c; spr[..., 3] = alpha * 0.92
        f = W * p["width"] / w; st["_st"] = cv2.resize(spr, (int(w * f), int(h * f)), interpolation=cv2.INTER_AREA)
    if ctx.t < p["at"] - p["slam"]: return F
    u = clamp((ctx.t - (p["at"] - p["slam"])) / p["slam"]); k = lerp(p["from_scale"], 1.0, ease("in_cubic", u)); a = u ** 0.5
    out = F
    after = ctx.t - p["at"]
    if 0 <= after < 0.3:
        s = p["shake"] * (1 - after / 0.3); rng = np.random.default_rng(int(after * 100))
        M = np.float32([[1, 0, rng.uniform(-s, s)], [0, 1, rng.uniform(-s, s)]])
        out = cv2.warpAffine(F, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if after < 0.05: out = out + (1 - out) * 0.25
    lay = place(st["_st"], W, H, p["pos"][0] * W, p["pos"][1] * H, k, p["angle"])
    al = lay[..., 3:4] * a
    return out * (1 - al) + lay[..., :3] * al
