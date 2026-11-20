# Scripts

This effect runs through the shared `fx` package:

```bash
python -m fx apply --effect vertigo --in "$CLIP" --out "$OUT"
```

`SKILL.md` has the full command, including the synthetic chroma-key path. There is no private script in this folder.

Shared files, relative to `effects/`:

- `scripts/download_models.sh` — optional segmentation weights into `models/` (not committed)
- `examples/make_samples.py` — re-render the synthetic sample
- `fx/effects/vertigo.py` — implementation

Keep credentials, private footage, and downloaded model binaries out of this folder.
