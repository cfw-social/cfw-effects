import numpy as np, cv2
from ..core import register
from ..palette import colorf
from ..compose import behind_only
from ..sprites import keycap
from ._util import place

@register("key_rain", defaults=dict(letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ", count=26, size=150, gravity=2600, spawn=1.6,
                                    floor=0.93, bounce=0.35, behind_ratio=0.5, cap="text", side="secondary", legend="outline",
                                    accent_every=5, accent="accent", seed=5))
def key_rain(ctx, p):
    """Keyboard keycaps rain down with gravity, spin and a small bounce on a floor line; about `behind_ratio` of them
    fall behind the subject, the rest in front. Every Nth cap is accent-coloured."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    if "_keys" not in st:
        rng = np.random.default_rng(p["seed"]); L = p["letters"]; ks = []
        for k in range(p["count"]):
            acc = p["accent_every"] and k % p["accent_every"] == 0
            spr = keycap(L[k % len(L)], int(p["size"] * rng.uniform(0.75, 1.15)), colorf(pal, p["accent"] if acc else p["cap"]),
                         colorf(pal, p["side"]), colorf(pal, p["legend"]))
            ks.append(dict(spr=spr, x=rng.uniform(0.08, 0.92) * W, t0=rng.uniform(0, p["spawn"]), vy=rng.uniform(0, 400),
                           rot=rng.uniform(-30, 30), w=rng.uniform(-260, 260), behind=rng.random() < p["behind_ratio"],
                           floor=p["floor"] * H - rng.uniform(0, 0.05) * H))
        st["_keys"] = ks
    back = np.zeros((H, W, 4), np.float32); front = np.zeros((H, W, 4), np.float32)
    for k in st["_keys"]:
        t = ctx.t - k["t0"]
        if t < 0: continue
        y = -k["spr"].shape[0] + k["vy"] * t + 0.5 * p["gravity"] * t * t; ang = k["rot"] + k["w"] * t
        if y > k["floor"]:          # one damped bounce, then rest
            tf = (np.sqrt(k["vy"] ** 2 + 2 * p["gravity"] * (k["floor"] + k["spr"].shape[0])) - k["vy"]) / p["gravity"]
            v = (k["vy"] + p["gravity"] * tf) * p["bounce"]; tb = t - tf
            y = k["floor"] - max(0.0, v * tb - 0.5 * p["gravity"] * tb * tb); ang = k["rot"] + k["w"] * tf
        lay = place(k["spr"], W, H, k["x"], y, 1.0, ang)
        tgt = back if k["behind"] else front
        a = lay[..., 3:4]; tgt[..., :3] = tgt[..., :3] * (1 - a) + lay[..., :3] * a; tgt[..., 3:4] = np.maximum(tgt[..., 3:4], a)
    out = behind_only(F, back, m)
    a = front[..., 3:4]
    return out * (1 - a) + front[..., :3] * a
