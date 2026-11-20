"""CLI:
  python -m fx list
  python -m fx apply --effect NAME --in clip.mp4 --out out.mp4 [--start s --end s] [--params JSON|file] [--palette JSON|file]
                     [--size 1080x1920] [--backend ensemble|mediapipe|u2net|chroma] [--seg JSON]
  python -m fx recipe recipe.json [--out out.mp4] [--only 0,2] [--stills 1.5,6.2]
  python -m fx masks --in clip.mp4 --out preview.mp4 [--start s --end s] [--size 1080x1920]   (segmentation check)
"""
import argparse, json, os, sys

def _js(x):
    if x is None: return None
    return json.load(open(x)) if os.path.exists(x) else json.loads(x)

def main(argv=None):
    import fx
    ap = argparse.ArgumentParser(prog="fx"); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("apply")
    a.add_argument("--effect", required=True); a.add_argument("--in", dest="inp", required=True); a.add_argument("--out", required=True)
    a.add_argument("--start", type=float, default=0.0); a.add_argument("--end", type=float); a.add_argument("--params")
    a.add_argument("--palette"); a.add_argument("--size"); a.add_argument("--backend", default="ensemble"); a.add_argument("--fps", type=float)
    a.add_argument("--seg", help='extra Segmenter options as JSON, e.g. {"chroma_hue": 290, "chroma_subject": "key"}')
    rc = sub.add_parser("recipe"); rc.add_argument("recipe"); rc.add_argument("--out"); rc.add_argument("--only"); rc.add_argument("--stills")
    mk = sub.add_parser("masks"); mk.add_argument("--in", dest="inp", required=True); mk.add_argument("--out", required=True)
    mk.add_argument("--start", type=float, default=0.0); mk.add_argument("--end", type=float); mk.add_argument("--size"); mk.add_argument("--backend", default="ensemble")
    o = ap.parse_args(argv)
    size = lambda s: tuple(int(v) for v in s.lower().split("x")) if s else None
    if o.cmd == "list":
        for k, v in fx.list_effects().items():
            print(f"{k}\n  {v['doc']}\n  defaults: {json.dumps(v['defaults'])}\n")
    elif o.cmd == "apply":
        fx.apply_effect(o.effect, o.inp, o.out, o.start, o.end, _js(o.params), _js(o.palette) if o.palette and (o.palette.startswith("{") or os.path.exists(o.palette)) else o.palette,
                        o.backend, size(o.size), o.fps, seg_opts=_js(o.seg))
    elif o.cmd == "recipe":
        fx.run_recipe(o.recipe, o.out, [int(x) for x in o.only.split(",")] if o.only else None,
                      [float(x) for x in o.stills.split(",")] if o.stills else None)
    elif o.cmd == "masks":
        from fx.vio import probe, read_frames, fit, Writer
        from fx.seg import Segmenter, preview
        info = probe(o.inp); W, H = size(o.size) or (info["w"], info["h"]); end = o.end or info["dur"]
        fr = [fit(f, W, H) for f in read_frames(o.inp, o.start, end - o.start, info["fps"] or 30)]
        sg = Segmenter(o.backend); ms = sg.sequence(fr); w = Writer(o.out, W, H, int(round(info["fps"] or 30)))
        for f, m in zip(fr, ms): w.write(preview(f, sg.upscale(m, f)))
        w.close(); print("wrote", o.out)

if __name__ == "__main__":
    main()
