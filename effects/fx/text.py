"""Text rendering to RGBA float arrays (PIL), with outline, cached."""
import functools, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import glob as _glob

def _font_dirs():
    env = os.environ.get("FX_FONT_DIR")
    ds = [env] if env else []
    ds += [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts"),
           os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/.fonts"), "/usr/share/fonts", "/usr/local/share/fonts",
           "/Library/Fonts", os.path.expanduser("~/Library/Fonts"), "C:/Windows/Fonts"]
    return [d for d in ds if d and os.path.isdir(d)]

@functools.lru_cache(maxsize=64)
def find_font(filename):
    """Locate a font file by name in FX_FONT_DIR, ./fonts, or the usual system font folders."""
    for d in _font_dirs():
        hits = _glob.glob(os.path.join(d, "**", filename), recursive=True)
        if hits: return hits[0]
    return None

FONTS = {  # name -> (font filename, variable-weight instance name or None). All are SIL OFL Google Fonts (not bundled).
    "nunito": ("Nunito-VariableFont_wght.ttf", "Black"),
    "nunito-bold": ("Nunito-VariableFont_wght.ttf", "ExtraBold"),
    "fraunces": ("Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf", "Black"),
    "antonio": ("Antonio-VariableFont_wght.ttf", "Bold"),
    "caveat": ("Caveat-VariableFont_wght.ttf", "Bold"),
    "mono": ("GeistMono-VariableFont_wght.ttf", "Bold"),
}
FALLBACKS = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]

@functools.lru_cache(maxsize=128)
def font(name="nunito", size=100):
    fn, var = FONTS.get(name, (name, None))
    path = fn if os.path.exists(fn) else find_font(os.path.basename(fn))
    if not path and name == "mono": path, var = find_font("DejaVuSansMono-Bold.ttf") or find_font("DejaVuSansMono.ttf"), None
    if not path:
        var = None; path = next((p for p in map(find_font, FALLBACKS) if p), None)
    f = ImageFont.truetype(path, int(size)) if path else ImageFont.load_default(int(size))
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

def measure(text, fname="nunito", size=100, stroke=0):
    f = font(fname, size); bb = ImageDraw.Draw(Image.new("L", (1, 1))).multiline_textbbox((0, 0), text, font=f, stroke_width=stroke, align="center")
    return bb[2] - bb[0], bb[3] - bb[1]

def fit_size(text, fname, max_w, max_h=10 ** 6, start=400, stroke_frac=0.0):
    s = start
    while s > 10:
        w, h = measure(text, fname, s, int(s * stroke_frac))
        if w <= max_w and h <= max_h: return s
        s = int(s * 0.93)
    return s

@functools.lru_cache(maxsize=256)
def render(text, fname="nunito", size=100, fill=(255, 255, 255), stroke=0, stroke_fill=(0, 0, 0), align="center", spacing=0.0, pad=None):
    """-> float32 RGBA (h,w,4). Cached; treat as read-only."""
    f = font(fname, size); pad = pad if pad is not None else stroke + 8
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.multiline_textbbox((0, 0), text, font=f, stroke_width=stroke, align=align, spacing=int(size * spacing))
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((pad - bb[0], pad - bb[1]), text, font=f, fill=tuple(fill) + (255,), stroke_width=stroke,
                                      stroke_fill=tuple(stroke_fill) + (255,), align=align, spacing=int(size * spacing))
    a = np.asarray(im).astype(np.float32) / 255.0
    a.setflags(write=False)
    return a
