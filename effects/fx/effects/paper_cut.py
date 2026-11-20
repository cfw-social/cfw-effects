import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..compose import feather, shadow, value_noise, desaturate
from ..palette import colorf
from ._util import subject

def paper_texture(H, W, rgb, seed=3, fibers=900):
    """Procedural paper: soft blotches + fibres + grain, tinted to rgb (float 0..1)."""
    h, w = H // 4, W // 4
    n = value_noise(h, w, 60, seed, 4)
    rng = np.random.default_rng(seed)
    fib = np.zeros((h, w), np.float32)
    for _ in range(fibers):
        x, y = rng.integers(0, w), rng.integers(0, h); a = rng.uniform(0, np.pi); L = rng.uniform(4, 18)
        cv2.line(fib, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(0.3, 1)), 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.6)
    base = (0.9 + 0.1 * n - 0.05 * fib)
    base = cv2.resize(base, (W, H), interpolation=cv2.INTER_CUBIC)
    grain = np.random.default_rng(seed + 1).normal(0, 0.018, (H, W)).astype(np.float32)
    return np.clip(base[..., None] * rgb[None, None] + grain[..., None], 0, 1)

@register("paper_cut", defaults=dict(border=26, rough=12, rough_scale=34, paper="paper", bg="texture", bg_color="secondary",
                                     shadow=0.5, shadow_dx=14, shadow_dy=22, pop=0.4, angle=-2.0, seed=3, layers=1))
def paper_cut(ctx, p):
    """Subject cut out like a paper sticker: torn white border, drop shadow, on a procedural paper background.
    bg: texture (paper tinted bg_color) | dim (darkened original) | original. layers=2 adds a second offset colour border."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    if "_paper" not in st:
        st["_paper"] = paper_texture(H, W, colorf(ctx.palette, p["bg_color"]), p["seed"])
        st["_noise"] = (value_noise(H // 2, W // 2, p["rough_scale"], p["seed"] + 9, 3) * 2 - 1)
        st["_ptex"] = paper_texture(H, W, colorf(ctx.palette, p["paper"]), p["seed"] + 5, 400)
    if p["bg"] == "texture": bg = st["_paper"]
    elif p["bg"] == "dim": bg = desaturate(F, 0.5) * 0.45
    else: bg = F
    # torn border alpha from distance-to-subject + static noise (half res for speed)
    hs = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    dist = cv2.distanceTransform((hs < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    def edge(bpx):
        b = bpx / 2 + p["rough"] / 2 * st["_noise"]
        return cv2.resize(np.clip((b - dist) / 1.2, 0, 1), (W, H), interpolation=cv2.INTER_LINEAR)
    A = np.maximum(edge(p["border"]), m)
    rgb = st["_ptex"] * (1 - m[..., None]) + F * m[..., None]
    if p["layers"] >= 2:
        A2 = edge(p["border"] * 1.9)
        c2 = colorf(ctx.palette, "accent")
        rgb = rgb * A[..., None] + c2 * (1 - A[..., None]); A = np.maximum(A, A2)
    # pop-in
    cx, cy, _ = subject(ctx)
    k = lerp(0.82, 1.0, ease("out_back", ctx.t / p["pop"])) if p["pop"] > 0 else 1.0
    ang = p["angle"] * ease("out_cubic", ctx.t / max(1e-3, p["pop"]))
    if k != 1.0 or ang:
        M = cv2.getRotationMatrix2D((cx, cy), ang, k)
        layer = cv2.warpAffine(np.dstack([rgb, A]).astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        rgb, A = layer[..., :3], layer[..., 3]
    sh = shadow(A, p["shadow_dx"], p["shadow_dy"], 16, p["shadow"])[..., None]
    out = bg * (1 - sh) + colorf(ctx.palette, "outline") * 0.6 * sh
    return out * (1 - A[..., None]) + rgb * A[..., None]
