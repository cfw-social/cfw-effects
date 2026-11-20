"""Generate a brand-free synthetic test clip (no real people): a magenta 'mannequin' doing a crawl/stand loop in a
procedural room. Segment it with the colour-key backend: seg = {"backend": "chroma", "chroma_hue": 292, "chroma_subject": "key"}.
Usage: python examples/make_synthetic_clip.py [out.mp4] [seconds]"""
import math, os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fx.vio import Writer

W, H, FPS = 540, 960, 30
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "synthetic_mannequin.mp4")
T = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0

def room():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    wall = np.stack([40 + 30 * yy / H, 90 + 40 * yy / H, 120 + 30 * xx / W], -1)
    floor_y = int(H * 0.62); img = wall.copy()
    fl = ((((xx // 60) + ((yy - floor_y) // 40)) % 2) * 25 + 150)
    img[floor_y:] = np.stack([fl * 0.35, fl * 0.55, fl * 0.95], -1)[floor_y:]
    img = img.astype(np.uint8).copy()
    for cx, cy, r, c in ((110, 220, 60, (230, 180, 60)), (430, 260, 45, (240, 240, 240)), (300, 160, 25, (200, 90, 60))):
        cv2.circle(img, (cx, cy), r, c, -1, cv2.LINE_AA)
    cv2.rectangle(img, (360, 380), (500, 560), (60, 60, 70), -1); cv2.rectangle(img, (40, 400), (150, 590), (180, 60, 50), -1)
    return img

def limb(img, a, b, th, col): cv2.line(img, tuple(map(int, a)), tuple(map(int, b)), col, th, cv2.LINE_AA)

def figure(img, t):
    col = (224, 64, 251); dark = (170, 40, 200)
    ph = 2 * math.pi * t / 1.6; stand = 0.5 + 0.5 * math.sin(2 * math.pi * t / T - math.pi / 2)  # 0 crawl -> 1 stand
    x = W * (0.3 + 0.4 * (t / T)); ground = H * 0.8
    hip = np.array([x, ground - 150 - 150 * stand]); sh = hip + np.array([60 * (1 - stand), -170 + 40 * (1 - stand)])
    head = sh + np.array([30 * (1 - stand), -70])
    for s, c in ((1, dark), (-1, col)):
        k = hip + np.array([25 * s * math.sin(ph), 85]); f = np.array([k[0] + 20 * s * math.sin(ph), ground])
        limb(img, hip, k, 34, c); limb(img, k, f, 30, c)
        e = sh + np.array([40 * s * math.sin(ph + 1) + 30 * (1 - stand), 90 * (1 - stand) + 70 * stand])
        hnd = np.array([e[0] + 25 * (1 - stand), ground if stand < 0.5 else e[1] + 80])
        limb(img, sh, e, 26, c); limb(img, e, hnd, 22, c)
    limb(img, hip, sh, 70, col); cv2.circle(img, tuple(map(int, head)), 46, col, -1, cv2.LINE_AA)

bg = room(); w = Writer(out, W, H, FPS, crf=24)
for i in range(int(T * FPS)):
    f = bg.copy(); figure(f, i / FPS); w.write(f)
w.close(); print("wrote", out)
