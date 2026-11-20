"""Layer compositing on float32 RGB frames in [0,1].

Stack order used by every effect:  background -> behind-subject graphics -> subject (mask) -> foreground graphics.
RGBA layers are float32 HxWx4 with straight (non-premultiplied) alpha.
"""
import numpy as np, cv2

def f32(img): return img.astype(np.float32) / 255.0 if img.dtype == np.uint8 else img
def u8(img): return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)

def over(dst, rgba, x=0, y=0, opacity=1.0):
    """Alpha-composite rgba (h,w,4 float) onto dst (H,W,3 float) at (x,y), clipped to bounds. In place; returns dst."""
    H, W = dst.shape[:2]; h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return dst
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * opacity
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a
    return dst

def layer_full(H, W): return np.zeros((H, W, 4), np.float32)

def stack(bg, subject, mask, behind=(), front=()):
    """bg, subject: HxWx3; mask HxW; behind/front: iterables of full-frame RGBA layers."""
    out = bg.copy()
    for L in behind: out = out * (1 - L[..., 3:4]) + L[..., :3] * L[..., 3:4]
    m = mask[..., None]
    out = out * (1 - m) + subject * m
    for L in front: out = out * (1 - L[..., 3:4]) + L[..., :3] * L[..., 3:4]
    return out

def behind_only(frame, layer, mask, opacity=1.0):
    """Put an RGBA layer between background and subject in one step."""
    a = layer[..., 3:4] * opacity * (1 - mask[..., None])
    return frame * (1 - a) + layer[..., :3] * a

def transform(rgba, scale=1.0, angle=0.0, center=None, dx=0.0, dy=0.0, out_size=None):
    """Scale/rotate an image about `center` (px) then translate. out_size=(W,H) default same."""
    h, w = rgba.shape[:2]; W, H = out_size or (w, h)
    cx, cy = center or (w / 2, h / 2)
    M = cv2.getRotationMatrix2D((cx, cy), angle, scale); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def grow(mask, px):
    """Dilate (px>0) or erode (px<0) a soft mask."""
    if px == 0: return mask
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * abs(px) + 1, 2 * abs(px) + 1))
    return cv2.dilate(mask, k) if px > 0 else cv2.erode(mask, k)

def feather(mask, sigma):
    return cv2.GaussianBlur(mask, (0, 0), sigma) if sigma > 0 else mask

def shadow(alpha, dx=12, dy=18, blur=18, strength=0.5):
    """Offset blurred copy of an alpha matte -> shadow alpha."""
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    s = cv2.warpAffine(alpha, M, (alpha.shape[1], alpha.shape[0]))
    return np.clip(feather(s, blur) * strength, 0, 1)

def centroid(mask, default=None):
    """(x, y, bbox) of the subject mask, or default when empty. bbox = (x0,y0,x1,y1)."""
    b = mask > 0.5
    if b.sum() < 50: return default
    ys, xs = np.nonzero(b)
    return float(xs.mean()), float(ys.mean()), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

def inpaint_bg(frame, mask, grow_px=18, scale=0.25):
    """Approximate clean plate: remove the subject by low-res inpainting. Good enough under motion/zoom."""
    H, W = frame.shape[:2]; sw, sh = int(W * scale), int(H * scale)
    small = cv2.resize(u8(frame), (sw, sh), interpolation=cv2.INTER_AREA)
    m = cv2.resize(grow(mask, grow_px), (sw, sh)) > 0.2
    m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
    fill = cv2.inpaint(small, m, 6, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(fill, (0, 0), 2)
    up = f32(cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC))
    a = feather(grow(mask, grow_px), 6)[..., None]
    return frame * (1 - a) + up * a

def zoom_about(img, k, cx, cy):
    M = np.float32([[k, 0, cx - k * cx], [0, k, cy - k * cy]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def desaturate(img, amount):
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    return img + (lum[..., None] - img) * amount

def rounded_rect_mask(w, h, r, ss=2):
    m = np.zeros((h * ss, w * ss), np.uint8); r = int(r * ss)
    cv2.rectangle(m, (r, 0), (w * ss - r, h * ss), 255, -1); cv2.rectangle(m, (0, r), (w * ss, h * ss - r), 255, -1)
    for cx, cy in ((r, r), (w * ss - r - 1, r), (r, h * ss - r - 1), (w * ss - r - 1, h * ss - r - 1)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0

def value_noise(h, w, scale, seed=0, octaves=3):
    """Smooth procedural noise in [0,1] (sum of upsampled random grids)."""
    rng = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        acc += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp
        amp *= 0.5; scale /= 2.2
    return np.clip(acc / tot, 0, 1)
