import numpy as np, cv2
from ..core import register
from ..anim import ease
from ..palette import colorf, color
from ..compose import behind_only, value_noise
from ..sprites import paste, solid
from .. import text as T
from ._util import place

@register("receipt_scroll", defaults=dict(title="RECEIPT", items=[["item one", "1.00"], ["item two", "2.50"],
                                                                        ["item three", "x3"], ["extra", "free"]],
                                          total=["TOTAL", "6.50"], width=0.62, x=0.5, angle=-4.0, speed=520, layer="behind",
                                          paper="paper", ink="outline", accent="hot", font="mono", size=46))
def receipt_scroll(ctx, p):
    """A printed paper receipt (procedural paper, zig-zag torn edges, mono font, dotted rules) scrolls up through the
    frame behind (or in front of) the subject. items: [[left, right], ...]; total: [label, value]."""
    F, m = ctx.frame, ctx.mask; H, W = ctx.H, ctx.W; st = ctx.state; pal = ctx.palette
    if "_rc" not in st:
        w = int(W * p["width"]); ink = color(pal, p["ink"]); s = p["size"]; lines = []
        lines.append(("c", p["title"], ink)); lines.append(("rule",)); 
        for l, r in p["items"]: lines.append(("lr", l, r, ink))
        lines.append(("rule",)); lines.append(("lr", p["total"][0], p["total"][1], color(pal, p["accent"]))); lines.append(("rule",))
        lines.append(("c", "THANK YOU", ink)); lines.append(("bar",))
        h = int(s * 1.6 * (len(lines) + 2)) + 120
        paper = colorf(pal, p["paper"]) * (0.94 + 0.06 * value_noise(h, w, 50, 4))[..., None]
        rc = np.dstack([paper, np.ones((h, w), np.float32)]).astype(np.float32)
        z = 22   # zig-zag torn edges
        al = np.ones((h, w), np.float32)
        for x in range(0, w, z):
            for yb, sgn in ((0, 1), (h - 1, -1)):
                cv2.fillPoly(al, [np.array([[x, yb], [x + z, yb], [x + z // 2, yb + sgn * (z // 2)]], np.int32)], 0.0)
        rc[..., 3] = al
        y = 70; pad = 44
        for ln in lines:
            if ln[0] == "c":
                t = np.array(T.render(ln[1], p["font"], s, ln[2], 0)); paste(rc, t, (w - t.shape[1]) // 2, y)
            elif ln[0] == "lr":
                a = np.array(T.render(ln[1], p["font"], int(s * 0.8), ln[3], 0)); b = np.array(T.render(ln[2], p["font"], int(s * 0.8), ln[3], 0))
                paste(rc, a, pad, y); paste(rc, b, w - pad - b.shape[1], y)
            elif ln[0] == "rule":
                for x in range(pad, w - pad, 18): cv2.circle(rc, (x, y + s // 2), 3, (*[c / 255 for c in ink], 1.0), -1)
            elif ln[0] == "bar":
                rng = np.random.default_rng(1); x = pad
                while x < w - pad:
                    bw = int(rng.integers(3, 12)); cv2.rectangle(rc, (x, y), (x + bw, y + s * 2), (*[c / 255 for c in ink], 1.0), -1); x += bw + int(rng.integers(3, 9))
            y += int(s * 1.6)
        st["_rc"] = rc
    rc = st["_rc"]; h = rc.shape[0]
    y = H + h / 2 - p["speed"] * ctx.t
    lay = place(rc, W, H, p["x"] * W, y, 1.0, p["angle"])
    if p["layer"] == "behind": return behind_only(F, lay, m)
    a = lay[..., 3:4]; return F * (1 - a) + lay[..., :3] * a
