"""Video / image-sequence IO via ffmpeg pipes, plus framing (crop+zoom to a target size)."""
import glob, json, os, subprocess
import numpy as np, cv2

def probe(path):
    """-> dict(w, h, fps, n, dur). Works for video files and image-sequence dirs (assumes 30 fps unless told)."""
    if os.path.isdir(path):
        fs = seq_files(path); h, w = cv2.imread(fs[0]).shape[:2]
        return dict(w=w, h=h, fps=30.0, n=len(fs), dur=len(fs) / 30.0)
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate,nb_frames:stream_side_data=rotation:format=duration", "-of", "json", path],
                                  capture_output=True, text=True, check=True).stdout)
    s = j["streams"][0]; a, b = s["r_frame_rate"].split("/"); fps = float(a) / float(b)
    dur = float(j["format"]["duration"])
    rot = 0
    for sd in s.get("side_data_list", []) or []:
        if "rotation" in sd: rot = int(float(sd["rotation"]))
    w, h = (s["height"], s["width"]) if abs(rot) % 180 == 90 else (s["width"], s["height"])   # ffmpeg autorotates on decode
    return dict(w=w, h=h, fps=fps, rot=rot, n=int(s.get("nb_frames") or round(dur * fps)), dur=dur)

def seq_files(d):
    fs = sorted(sum((glob.glob(os.path.join(d, e)) for e in ("*.jpg", "*.jpeg", "*.png")), []))
    if not fs: raise FileNotFoundError(f"no frames in {d}")
    return fs

def read_frames(path, start=0.0, dur=None, fps=30.0, speed=1.0, src_fps=None):
    """Yield RGB uint8 frames sampled at `fps` output rate starting at `start` s of the source, for `dur` s.
    `speed` <1 = slow motion (frames repeat / nearest). Image-seq dirs use src_fps (default 30)."""
    if os.path.isdir(path):
        fs = seq_files(path); sf = src_fps or 30.0
        n = int(round((dur if dur is not None else (len(fs) / sf - start) / speed) * fps))
        last = None; cache = None
        for i in range(n):
            k = min(len(fs) - 1, int(round((start + i / fps * speed) * sf)))
            if k != last: cache = cv2.cvtColor(cv2.imread(fs[k]), cv2.COLOR_BGR2RGB); last = k
            yield cache
        return
    info = probe(path); w, h = info["w"], info["h"]
    if dur is None: dur = (info["dur"] - start) / speed
    vf = f"setpts={1/speed:.6f}*PTS,fps={fps}" if speed != 1 else f"fps={fps}"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur*speed + 0.5:.3f}", "-i", path,
           "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = int(round(dur * fps)); sz = w * h * 3; got = 0; last = None
    try:
        while got < n:
            b = p.stdout.read(sz)
            if len(b) < sz: break
            last = np.frombuffer(b, np.uint8).reshape(h, w, 3); got += 1; yield last
        while got < n and last is not None: got += 1; yield last   # pad short tails
    finally:
        p.stdout.close(); p.kill(); p.wait()

def fit(img, W, H, center=(0.5, 0.5), zoom=1.0, redact=None):
    """Cover-crop img to WxH. center = focus point (fractions of the source), zoom>=1 crops tighter.
    redact = list of [x,y,w,h] fractions of the SOURCE to heavy-blur before cropping (signage, names)."""
    if redact:
        img = img.copy(); sh, sw = img.shape[:2]
        for (x, y, w, h) in redact:
            x0, y0 = int(x * sw), int(y * sh); x1, y1 = int((x + w) * sw), int((y + h) * sh)
            roi = img[y0:y1, x0:x1]
            if roi.size:
                small = cv2.resize(roi, (max(1, roi.shape[1] // 60), max(1, roi.shape[0] // 60)), interpolation=cv2.INTER_AREA)
                img[y0:y1, x0:x1] = cv2.GaussianBlur(cv2.resize(small, (roi.shape[1], roi.shape[0])), (0, 0), 18)
    sh, sw = img.shape[:2]
    s = max(W / sw, H / sh) * zoom
    cw, ch = W / s, H / s
    cx = min(max(center[0] * sw, cw / 2), sw - cw / 2); cy = min(max(center[1] * sh, ch / 2), sh - ch / 2)
    M = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)

class Writer:
    """Raw RGB frames -> H.264 mp4 (yuv420p). w.write(frame_uint8); w.close()."""
    def __init__(self, path, W, H, fps=30, crf=19, preset="medium"):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                                   "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
                                   "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        self.n = 0
    def write(self, f):
        if f.dtype != np.uint8: f = np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)
        self.p.stdin.write(np.ascontiguousarray(f).tobytes()); self.n += 1
    def close(self):
        self.p.stdin.close(); self.p.wait()
        if self.p.returncode: raise RuntimeError("ffmpeg writer failed")

def mux(video, audio, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)

def copy_audio(src_video, video, out, start=0.0):
    """Mux the source's audio (if any) onto a processed video."""
    has = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", src_video],
                         capture_output=True, text=True).stdout.strip()
    if not has: os.replace(video, out); return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", f"{start:.3f}", "-i", src_video, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(video)
