import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..compose import behind_only
from ..sprites import ClipBank, phone, with_shadow
from ._util import subject, place

@register("phone_fan", defaults=dict(clips=None, count=5, spread=95.0, phone_w=0.34, pivot_y=0.95, lift=0.18, intro=0.6,
                                     stagger=0.06, self_delay=10, y=0.5))
def phone_fan(ctx, p):
    """Generic phones fan out from behind the subject like a hand of cards (rotating about a low pivot), each screen
    playing a clip (or a delayed copy of this one). Phones stay BEHIND the subject."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state
    pw = int(W * p["phone_w"]); ph = int(pw * 2.05)
    if "_bank" not in st: st["_bank"] = ClipBank(p["clips"], (pw, ph), int(round(ctx.fps)))
    bank = st["_bank"]; cx, _, _ = subject(ctx)
    lay = np.zeros((H, W, 4), np.float32); n = p["count"]
    for k in range(n):
        u = ease("out_back", (ctx.t - k * p["stagger"]) / p["intro"]) if p["intro"] > 0 else 1
        if u <= 0: continue
        frac = 0 if n == 1 else k / (n - 1) - 0.5
        ang = -frac * p["spread"] * u
        spr, _ = phone(pw, ph, bank.frame(k, ctx.i + 9 * k, ctx, delay=p["self_delay"] * (k + 1)))
        spr, pad = with_shadow(spr, 0, 16, 16, 0.4)
        # rotate about a pivot below the phone: offset centre along the rotated up-vector
        d = ph * p["pivot_y"] * 0.6; th = np.radians(ang)
        px, py = cx, p["y"] * H + d - p["lift"] * H * u          # pivot below the hand of phones
        x = px - np.sin(th) * d; y = py - np.cos(th) * d
        L = place(spr, W, H, x, y, lerp(0.6, 1.0, u), ang)
        a = L[..., 3:4]; lay[..., :3] = lay[..., :3] * (1 - a) + L[..., :3] * a; lay[..., 3:4] = np.maximum(lay[..., 3:4], a)
    return behind_only(F, lay, m)
