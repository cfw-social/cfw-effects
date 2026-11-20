"""Person segmentation with on-disk mask cache and temporal smoothing.

Backends:
  "mediapipe"  MediaPipe selfie_multiclass_256x256 (1 - background). Fast; best at small/far people.
  "u2net"      U^2-Net human-seg (ONNX, the rembg model). Cleaner edges on medium/close people.
  "ensemble"   (default) mean of both, re-ramped: keeps people either model finds, drops single-model junk.
  "chroma"     colour key (no model): green-screen (chroma_subject="rest") or a uniquely coloured subject
               (chroma_subject="key"). chroma_hue = key hue in degrees, chroma_tol = hue tolerance, chroma_sat = min saturation.
Masks are float32 HxW in [0,1] at the frame's size. Raw masks are cached as PNG (540px wide) keyed by a hash
of the frame content + backend, so re-renders and other effects reuse them.
"""
import hashlib, os, threading
import numpy as np, cv2

LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("FX_MASK_CACHE", os.path.join(LIB, "cache", "masks"))
MP_MODEL = os.environ.get("FX_MP_MODEL", os.path.join(LIB, "models", "selfie_multiclass_256x256.tflite"))
U2_MODEL = os.environ.get("FX_U2_MODEL", next((p for p in [os.path.join(LIB, "models", "u2net_human_seg.onnx"),
                                                          os.path.expanduser("~/.rembg/models/u2net_human_seg/u2net_human_seg.onnx"),
                                                          os.path.expanduser("~/.u2net/u2net_human_seg.onnx")] if os.path.exists(p)),
                                                    os.path.join(LIB, "models", "u2net_human_seg.onnx")))
SEG_W = 540   # analysis width (9:16 -> 540x960)
_lock = threading.Lock(); _models = {}

def _mp():
    if "mp" not in _models:
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        opts = vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=MP_MODEL), output_confidence_masks=True)
        _models["mp"] = (mp, vision.ImageSegmenter.create_from_options(opts))
    return _models["mp"]

def _u2():
    if "u2" not in _models:
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 4
        _models["u2"] = ort.InferenceSession(U2_MODEL, so, providers=["CPUExecutionProvider"])
    return _models["u2"]

def _run_mp(img):
    mp, seg = _mp()
    r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img)))
    return 1.0 - np.squeeze(r.confidence_masks[0].numpy_view()).astype(np.float32)

def _run_u2(img):
    s = _u2()
    x = cv2.resize(img, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = ((x - (0.485, 0.456, 0.406)) / (0.229, 0.224, 0.225)).transpose(2, 0, 1)[None].astype(np.float32)
    o = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
    o = (o - o.min()) / (o.max() - o.min() + 1e-6)
    return cv2.resize(o, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)

def _run_chroma(img, hue, tol, sat, subject):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h = hsv[..., 0] * 360 / 256; s = hsv[..., 1] / 255
    d = np.abs((h - hue + 180) % 360 - 180)
    key = np.clip((tol - d) / 6, 0, 1) * np.clip((s - sat) / 0.1, 0, 1)
    key = cv2.GaussianBlur(key.astype(np.float32), (0, 0), 0.8)
    return key if subject == "key" else 1 - key

def ramp(m, lo, hi): return np.clip((m - lo) / (hi - lo), 0, 1).astype(np.float32)

class Segmenter:
    def __init__(self, backend="ensemble", cache_dir=CACHE, temporal_sigma=1.2, cut_threshold=28.0,
                 refine=True, min_area=0.0015, chroma_hue=120.0, chroma_tol=28.0, chroma_sat=0.35, chroma_subject="rest"):
        self.chroma = (chroma_hue, chroma_tol, chroma_sat, chroma_subject)
        self.backend, self.cache, self.sigma, self.cut, self.refine, self.min_area = backend, cache_dir, temporal_sigma, cut_threshold, refine, min_area
        os.makedirs(self.cache, exist_ok=True)

    def _small(self, frame):
        h, w = frame.shape[:2]; return cv2.resize(frame, (SEG_W, int(round(h * SEG_W / w))), interpolation=cv2.INTER_AREA)

    def raw(self, frame):
        """Raw (unsmoothed) mask at analysis size, cached. -> float32 [0,1]."""
        small = self._small(frame)
        if self.backend == "chroma":
            return self._clean(_run_chroma(small, *self.chroma))
        key = hashlib.blake2b(small[::2, ::2].tobytes() + self.backend.encode(), digest_size=16).hexdigest()
        p = os.path.join(self.cache, key[:2], key + ".png")
        if os.path.exists(p):
            m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
            if m is not None: return m.astype(np.float32) / 255.0
        with _lock:
            if self.backend == "mediapipe": m = _run_mp(small)
            elif self.backend == "u2net": m = ramp(_run_u2(small), 0.15, 0.6)
            elif self.backend == "ensemble":
                m = ramp(0.5 * (_run_mp(small) + ramp(_run_u2(small), 0.15, 0.6)), 0.22, 0.55)
            else: raise ValueError(f"unknown backend {self.backend}")
        m = self._clean(m)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        cv2.imwrite(p, np.clip(m * 255 + .5, 0, 255).astype(np.uint8))
        return m

    def _clean(self, m):
        """Drop tiny islands (< min_area of frame) and fill pinholes."""
        b = (m > 0.5).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
        keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= self.min_area * m.size
        drop = (~keep[lab]) & (b > 0)
        m = m.copy(); m[drop] = 0
        return cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    def sequence(self, frames, progress=None):
        """Masks for a list of frames: raw (cached) -> temporal gaussian (resets at scene cuts) -> edge refine.
        Returns list of float32 masks at analysis size (use .upscale(mask, frame) for full res)."""
        raws, smalls = [], []
        for i, f in enumerate(frames):
            raws.append(self.raw(f)); smalls.append(cv2.resize(f, (96, 170), interpolation=cv2.INTER_AREA).astype(np.float32))
            if progress and i % 30 == 0: progress(i, len(frames))
        seg_id = [0]
        for i in range(1, len(frames)):
            seg_id.append(seg_id[-1] + (np.abs(smalls[i] - smalls[i - 1]).mean() > self.cut))
        out = []
        r = int(np.ceil(self.sigma * 2.5)) if self.sigma > 0 else 0
        for i in range(len(raws)):
            acc, wsum = 0, 0
            for j in range(max(0, i - r), min(len(raws), i + r + 1)):
                if seg_id[j] != seg_id[i]: continue
                w = np.exp(-0.5 * ((j - i) / self.sigma) ** 2) if self.sigma > 0 else 1.0
                acc = acc + w * raws[j]; wsum += w
            m = (acc / wsum).astype(np.float32)
            out.append(m)
        return out

    def upscale(self, m, frame):
        """Analysis-size mask -> frame-size mask, edge-refined with a guided filter on the frame."""
        h, w = frame.shape[:2]
        M = cv2.resize(m.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        if self.refine and hasattr(cv2, "ximgproc"):
            g = cv2.resize(frame, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
            mm = cv2.resize(M, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
            mm = cv2.ximgproc.guidedFilter(guide=g, src=mm, radius=6, eps=1e-3 * 255 * 255)
            M = cv2.resize(np.clip(mm, 0, 1), (w, h), interpolation=cv2.INTER_LINEAR)
        return np.clip(M, 0, 1).astype(np.float32)

def preview(frame, mask, color=(253, 161, 7)):
    """Debug overlay: subject tinted, background dimmed."""
    m = mask[..., None]
    return (frame * (0.35 + 0.65 * m) * (1 - 0.45 * m) + np.array(color) * 0.45 * m).clip(0, 255).astype(np.uint8)
