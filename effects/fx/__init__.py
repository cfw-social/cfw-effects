"""fx: brand-agnostic subject-aware video effects (segmentation + layered compositing).

Quick use:
    from fx import apply_effect, run_recipe, load_palette
    apply_effect("spotlight", "in.mp4", "out.mp4", start=1.0, end=4.0, params={"sparkles": 40})
"""
__version__ = "0.1.0"
from .palette import load_palette, DEFAULT_PALETTE, color          # noqa: F401
from .anim import ease, Keyframes, envelope, lerp, clamp           # noqa: F401
from .seg import Segmenter                                          # noqa: F401
from .core import Ctx, register, get_effect, list_effects, apply_effect, apply_frame  # noqa: F401
from . import effects                                               # noqa: F401  (registers effects)
from .recipe import run_recipe                                      # noqa: F401
