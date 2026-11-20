"""Reusable generic, brand-neutral sprites (cards, device frames, keycaps, windows) and a clip bank for
effects that show other footage (orbit, phone_fan, profile_wall, ...). All sprites are float32 RGBA."""
import os
import numpy as np, cv2
from .compose import rounded_rect_mask, f32, shadow as mk_shadow
from .palette import colorf, color
from . import text as T

def solid(h, w, rgb, a=1.0):
    s = np.zeros((h, w, 4), np.float32); s[..., :3] = rgb; s[..., 3] = a; return s

def paste(dst, src, x, y):
    """Alpha-over an RGBA sprite onto an RGBA canvas (both float32), in place."""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; d = dst[y0:y1, x0:x1]
    a = s[..., 3:4]; da = d[..., 3:4]
    oa = a + da * (1 - a)
    d[..., :3] = np.where(oa > 0, (s[..., :3] * a + d[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6), 0)
    d[..., 3:4] = oa
    return dst

def cover(img, w, h):
    """Cover-resize an RGB image to w x h."""
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih)
    r = cv2.resize(img, (max(w, int(iw * s + 0.5)), max(h, int(ih * s + 0.5))), interpolation=cv2.INTER_AREA)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]

def card(img, w, h, radius=24, border=8, border_rgb=(1, 1, 1)):
    """Photo card: rounded image with a solid border."""
    s = solid(h, w, border_rgb, 1.0); s[..., 3] = rounded_rect_mask(w, h, radius)
    iw, ih = w - 2 * border, h - 2 * border
    if iw > 4 and ih > 4:
        im = f32(cover(img, iw, ih)) if img.dtype == np.uint8 else cover(img, iw, ih)
        m = rounded_rect_mask(iw, ih, max(1, radius - border))[..., None]
        s[border:border + ih, border:border + iw, :3] = s[border:border + ih, border:border + iw, :3] * (1 - m) + im * m
    return s

def with_shadow(spr, dx=0, dy=14, blur=14, strength=0.45, rgb=(0, 0, 0)):
    pad = blur * 3 + max(abs(dx), abs(dy))
    h, w = spr.shape[:2]; c = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
    c[pad:pad + h, pad:pad + w] = spr
    sa = mk_shadow(c[..., 3], dx, dy, blur, strength)
    out = np.zeros_like(c); out[..., :3] = rgb; out[..., 3] = sa
    return paste(out, c, 0, 0), pad

def phone(w, h, screen_img=None, body_rgb=(0.06, 0.06, 0.08), bezel=None):
    """Generic slab phone: rounded body, thin bezel, pill speaker slot. Returns (rgba, screen_rect)."""
    bz = bezel or max(6, int(w * 0.045)); r = int(w * 0.16)
    s = solid(h, w, body_rgb); s[..., 3] = rounded_rect_mask(w, h, r)
    sw, sh = w - 2 * bz, h - 2 * bz
    if screen_img is not None:
        im = f32(cover(screen_img, sw, sh)) if screen_img.dtype == np.uint8 else cover(screen_img, sw, sh)
        m = rounded_rect_mask(sw, sh, max(2, r - bz))[..., None]
        s[bz:bz + sh, bz:bz + sw, :3] = s[bz:bz + sh, bz:bz + sw, :3] * (1 - m) + im * m
    pw, ph = int(w * 0.22), max(4, int(w * 0.035))
    cv2.rectangle(s, (w // 2 - pw // 2, bz + ph), (w // 2 + pw // 2, bz + 2 * ph), (*body_rgb, 1.0), -1, cv2.LINE_AA)
    return s, (bz, bz, sw, sh)

def keycap(ch, size, cap_rgb, side_rgb, text_rgb, font="nunito"):
    """Chunky keycap: top face + darker side band + legend."""
    h = int(size * 1.12); s = np.zeros((h, size, 4), np.float32)
    base = rounded_rect_mask(size, h, int(size * 0.2)); s[..., :3] = side_rgb; s[..., 3] = base
    top = rounded_rect_mask(int(size * 0.84), int(size * 0.8), int(size * 0.16))
    ox, oy = int(size * 0.08), int(size * 0.05)
    th, tw = top.shape
    grad = np.linspace(1.08, 0.94, th, dtype=np.float32)[:, None, None]
    face = np.clip(np.asarray(cap_rgb, np.float32) * grad, 0, 1) * np.ones((th, tw, 1), np.float32)
    s[oy:oy + th, ox:ox + tw, :3] = s[oy:oy + th, ox:ox + tw, :3] * (1 - top[..., None]) + face * top[..., None]
    g = np.array(T.render(ch, font, int(size * 0.42), tuple(int(v * 255) for v in text_rgb), 0))
    gx, gy = ox + (tw - g.shape[1]) // 2, oy + (th - g.shape[0]) // 2
    paste(s, g, gx, gy)
    return s

def window(w, h, pal, title="Chat", header=None, radius=28, body_rgb=None):
    """Generic app window: rounded panel, header bar with a simple round avatar + title, no OS chrome."""
    hd = header or max(60, int(h * 0.085))
    body = body_rgb if body_rgb is not None else np.clip(colorf(pal, "text") * 0.97, 0, 1)
    s = solid(h, w, body); s[..., 3] = rounded_rect_mask(w, h, radius)
    s[:hd, :, :3] = colorf(pal, "bg")
    cv2.circle(s, (int(hd * 0.6), hd // 2), int(hd * 0.28), (*map(float, colorf(pal, "accent")), 1.0), -1, cv2.LINE_AA)
    t = np.array(T.render(title, "nunito", int(hd * 0.38), color(pal, "text"), 0))
    paste(s, t, int(hd * 1.05), (hd - t.shape[0]) // 2)
    return s, hd

class ClipBank:
    """Frames from other clips (paths/dirs) at a thumbnail size, or a rolling buffer of the current source ("self")."""
    _cache = {}
    def __init__(self, clips, size=(360, 640), fps=30, dur=6.0):
        self.size, self.fps = size, fps; self.items = []
        for c in clips or []:
            if isinstance(c, str): c = {"src": c}
            key = (c["src"], c.get("in", 0.0), size, dur)
            if key not in ClipBank._cache:
                from .vio import read_frames
                fr = [cover(f, *size) for f in read_frames(c["src"], c.get("in", 0.0), c.get("dur", dur), fps, c.get("speed", 1.0), c.get("src_fps"))]
                ClipBank._cache[key] = fr
            self.items.append(ClipBank._cache[key])
    def frame(self, k, i, ctx=None, delay=0):
        """k-th clip at frame i (loops). With no clips, returns the current source delayed by `delay` frames."""
        if self.items:
            fr = self.items[k % len(self.items)]; return f32(fr[i % len(fr)])
        buf = ctx.state.setdefault("_selfbuf", [])
        if not buf or buf[-1][0] != ctx.i:
            buf.append((ctx.i, cv2.resize(ctx.src, self.size, interpolation=cv2.INTER_AREA)))
            if len(buf) > 90: buf.pop(0)
        j = max(0, len(buf) - 1 - delay)
        return buf[j][1]
