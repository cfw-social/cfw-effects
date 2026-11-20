import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..compose import feather, grow, desaturate
from ..palette import colorf
from ._util import subject

@register("spotlight", defaults=dict(dim=0.3, desat=0.55, radius=1.15, glow="glow", glow_strength=0.85, glow_size=34,
                                     beam=True, beam_strength=0.35, sparkles=40, sparkle_color="text", sparkle_size=30,
                                     ramp=0.35, lift=1.06, seed=7))
def spotlight(ctx, p):
    """Dims + desaturates the background, pools light on the subject, adds a coloured rim glow, an optional overhead
    beam and twinkling sparkle particles in front."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    a = ease("out_cubic", ctx.t / p["ramp"]) if p["ramp"] > 0 else 1.0
    cx, cy, (x0, y0, x1, y1) = subject(ctx)
    h, w = H // 8, W // 8
    if "_grid" not in st: st["_grid"] = np.mgrid[0:h, 0:w].astype(np.float32)
    yy, xx = st["_grid"]
    R = max(x1 - x0, y1 - y0) / 2 * p["radius"] + 40
    pool = np.exp(-(((xx * 8 - cx) ** 2 + ((yy * 8 - cy) * 0.8) ** 2) / (2 * R * R)))
    if p["beam"]:
        top_w, bot_w = W * 0.10, (x1 - x0) * 0.75 + 60
        frac = np.clip(yy * 8 / max(1, cy), 0, 1)
        half = top_w / 2 + (bot_w / 2 - top_w / 2) * frac
        beam = np.clip(1 - np.abs(xx * 8 - cx) / half, 0, 1) ** 0.7 * (yy * 8 < cy + R * 0.3)
        pool = np.maximum(pool, cv2.GaussianBlur(beam.astype(np.float32), (0, 0), 3) * p["beam_strength"])
    light = cv2.resize(pool.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    lvl = p["dim"] + (1 - p["dim"]) * np.clip(light, 0, 1)
    bg = desaturate(F, p["desat"] * a) * (1 - a + a * lvl)
    if p["glow_strength"] > 0:
        g = feather(grow(m, p["glow_size"] // 2), p["glow_size"]) * a * p["glow_strength"]
        c = colorf(ctx.palette, p["glow"])
        bg = 1 - (1 - bg) * (1 - g[..., None] * c)
    mm = m[..., None]
    out = bg * (1 - mm) + np.clip(F * (1 + (p["lift"] - 1) * a), 0, 1) * mm
    n = int(p["sparkles"])
    if n > 0 and a > 0:
        if "_sp" not in st:
            rng = np.random.default_rng(p["seed"])
            st["_sp"] = dict(rx=rng.uniform(-0.75, 0.75, n), ry=rng.uniform(-0.7, 0.6, n), ph=rng.random(n),
                             fr=rng.uniform(0.7, 1.6, n), sz=rng.uniform(0.4, 1.0, n), vy=rng.uniform(20, 70, n))
        sp = st["_sp"]; lay = np.zeros((H // 2, W // 2), np.float32)
        bw, bh = (x1 - x0) / 2 + 80, (y1 - y0) / 2 + 80
        for j in range(n):
            b = max(0.0, np.sin(2 * np.pi * (ctx.t * sp["fr"][j] + sp["ph"][j]))) ** 3 * a
            if b < 0.05: continue
            x = (cx + sp["rx"][j] * bw * 1.4) / 2; y = (cy + sp["ry"][j] * bh * 1.2 - sp["vy"][j] * ctx.t) / 2
            s = p["sparkle_size"] * sp["sz"][j] * (0.6 + 0.4 * b)
            for (dx, dy, L) in ((1, 0, s), (0, 1, s), (0.7, 0.7, s * 0.45), (0.7, -0.7, s * 0.45)):
                cv2.line(lay, (int(x - dx * L), int(y - dy * L)), (int(x + dx * L), int(y + dy * L)), float(b), 3, cv2.LINE_AA)
            cv2.circle(lay, (int(x), int(y)), max(1, int(s * 0.18)), float(b), -1, cv2.LINE_AA)
        lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
        halo = cv2.GaussianBlur(lay, (0, 0), 6) * 0.8
        c = colorf(ctx.palette, p["sparkle_color"]); gc = colorf(ctx.palette, p["glow"])
        out = 1 - (1 - out) * (1 - np.clip(halo, 0, 1)[..., None] * gc)
        out = out * (1 - np.clip(lay, 0, 1)[..., None]) + c * np.clip(lay, 0, 1)[..., None]
    return out
