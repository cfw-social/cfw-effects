"""Keyframe + easing helpers. Times are seconds; u is 0..1 progress."""
import math

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, u): return a + (b - a) * u

_E = {
    "linear": lambda u: u,
    "in_quad": lambda u: u * u, "out_quad": lambda u: 1 - (1 - u) ** 2,
    "in_out_quad": lambda u: 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2,
    "in_cubic": lambda u: u ** 3, "out_cubic": lambda u: 1 - (1 - u) ** 3,
    "in_out_cubic": lambda u: 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2,
    "out_expo": lambda u: 1 if u >= 1 else 1 - 2 ** (-10 * u),
    "in_out_sine": lambda u: -(math.cos(math.pi * u) - 1) / 2,
    "out_back": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
    "out_elastic": lambda u: 0 if u <= 0 else 1 if u >= 1 else 2 ** (-10 * u) * math.sin((u * 10 - .75) * 2 * math.pi / 3) + 1,
}
EASINGS = sorted(_E)

def ease(name, u):
    return _E[name or "linear"](clamp(u))

def envelope(t, t0, t1, fade_in=0.2, fade_out=0.2, curve="out_cubic"):
    """0 before t0, ramps to 1 over fade_in, holds, ramps to 0 over fade_out ending at t1."""
    if t < t0 or t > t1: return 0.0
    a = 1.0
    if fade_in > 0: a = min(a, ease(curve, (t - t0) / fade_in))
    if fade_out > 0: a = min(a, ease(curve, (t1 - t) / fade_out))
    return a

class Keyframes:
    """Keyframes([(t, value), ...], ease="in_out_cubic"); value may be number or tuple. kf(t) -> value."""
    def __init__(self, keys, ease="in_out_cubic"):
        self.k = sorted(keys, key=lambda x: x[0]); self.e = ease
    def __call__(self, t):
        k = self.k
        if t <= k[0][0]: return k[0][1]
        if t >= k[-1][0]: return k[-1][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t0 <= t <= t1:
                u = ease(self.e, (t - t0) / max(1e-9, t1 - t0))
                if isinstance(v0, (tuple, list)): return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
                return lerp(v0, v1, u)
