import numpy as np, cv2
from ..compose import centroid

def subject(ctx, smooth=0.8):
    """Smoothed subject centre + bbox (frame px). Falls back to last known / frame centre."""
    m = ctx.mask[::4, ::4]
    c = centroid(m)
    prev = ctx.state.get("_subj")
    if c is None:
        return prev or (ctx.W / 2, ctx.H / 2, (ctx.W // 4, ctx.H // 4, 3 * ctx.W // 4, 3 * ctx.H // 4))
    x, y, (x0, y0, x1, y1) = c[0] * 4, c[1] * 4, tuple(v * 4 for v in c[2])
    if prev:
        a = smooth; px, py, pb = prev
        x, y = px * a + x * (1 - a), py * a + y * (1 - a)
        x0, y0, x1, y1 = (pb[k] * a + v * (1 - a) for k, v in enumerate((x0, y0, x1, y1)))
    ctx.state["_subj"] = (x, y, (x0, y0, x1, y1))
    return ctx.state["_subj"]

def anchor(ctx, p, key="anchor"):
    a = p.get(key, "subject")
    if isinstance(a, (list, tuple)): return a[0] * ctx.W, a[1] * ctx.H
    x, y, _ = subject(ctx); return x, y

def place(rgba, W, H, cx, cy, scale=1.0, angle=0.0, sy=1.0):
    """Paste an RGBA sprite into a full WxH RGBA layer with its centre at (cx,cy)."""
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[1, :] *= sy
    # translate sprite centre to target
    c = M @ np.array([w / 2, h / 2, 1.0])
    M[0, 2] += cx - c[0]; M[1, 2] += cy - c[1]
    return cv2.warpAffine(np.ascontiguousarray(rgba), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
