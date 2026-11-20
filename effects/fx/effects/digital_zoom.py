import numpy as np, cv2
from ..core import register
from ..anim import ease, lerp
from ..palette import colorf, color
from .. import text as T
from ..compose import over
from ._util import subject

@register("digital_zoom", defaults=dict(steps=[[0.0, 1.0], [1.0, 2.0], [2.2, 3.5]], punch=0.12, pixelate=0.55, anchor="subject",
                                        ui=True, rec_color="hot", ui_color="text", timecode_start=0, scanlines=0.08))
def digital_zoom(ctx, p):
    """Camcorder-style digital zoom: snaps between zoom levels (steps: [[time, zoom], ...]) with a short punch,
    real pixelation that grows with zoom, scanlines and a generic camera UI (blinking REC dot, timecode, zoom x, corner frame)."""
    F = ctx.frame; H, W = ctx.H, ctx.W
    z, zprev, tstep = 1.0, 1.0, 0.0
    for t0, zz in p["steps"]:
        if ctx.t >= t0: zprev, z, tstep = z, zz, t0
    zc = lerp(zprev, z, ease("out_cubic", (ctx.t - tstep) / p["punch"]))
    if p["anchor"] == "subject": cx, cy, _ = subject(ctx)
    else: cx, cy = p["anchor"][0] * W, p["anchor"][1] * H
    cx = min(max(cx, W / 2 / zc), W - W / 2 / zc); cy = min(max(cy, H / 2 / zc), H - H / 2 / zc)
    M = np.float32([[zc, 0, W / 2 - zc * cx], [0, zc, H / 2 - zc * cy]])
    if zc > 1.01 and p["pixelate"] > 0:
        f = max(1.0, (zc - 1) * p["pixelate"] * 6)
        small = cv2.warpAffine(F, M, (W, H), flags=cv2.INTER_LINEAR)
        s = cv2.resize(small, (int(W / f), int(H / f)), interpolation=cv2.INTER_AREA)
        out = cv2.resize(s, (W, H), interpolation=cv2.INTER_NEAREST)
    else:
        out = cv2.warpAffine(F, M, (W, H), flags=cv2.INTER_LINEAR)
    if p["scanlines"]:
        out = out.copy(); out[::4] *= (1 - p["scanlines"])
    if p["ui"]:
        uc = colorf(ctx.palette, p["ui_color"]); lay = np.zeros((H, W), np.float32); mg, L = 60, 90
        for (x, y, sx, sy) in ((mg, mg * 2, 1, 1), (W - mg, mg * 2, -1, 1), (mg, H - mg * 2, 1, -1), (W - mg, H - mg * 2, -1, -1)):
            cv2.line(lay, (x, y), (x + sx * L, y), 1.0, 5, cv2.LINE_AA); cv2.line(lay, (x, y), (x, y + sy * L), 1.0, 5, cv2.LINE_AA)
        out = out * (1 - lay[..., None]) + uc * lay[..., None]
        if int(ctx.t * 2) % 2 == 0:
            cv2.circle(out, (mg + 40, mg * 2 + 70), 16, tuple(float(v) for v in colorf(ctx.palette, p["rec_color"])), -1, cv2.LINE_AA)
        tc = p["timecode_start"] + ctx.t
        for txt, x, y in (("REC", mg + 70, mg * 2 + 46), (f"{int(tc // 3600):02d}:{int(tc // 60) % 60:02d}:{int(tc) % 60:02d}:{int(tc * 30) % 30:02d}", W - mg - 330, mg * 2 + 46),
                          (f"{zc:.1f}x", W // 2 - 50, H - mg * 2 - 100)):
            over(out, np.array(T.render(txt, "mono", 44, color(ctx.palette, p["ui_color"]), 2, color(ctx.palette, "outline"))), x, y)
    return out
