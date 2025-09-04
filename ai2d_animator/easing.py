from __future__ import annotations

from typing import Callable, Dict


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def linear(t: float) -> float:
    return clamp(t, 0.0, 1.0)


def ease_in_quad(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t


def ease_out_quad(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def ease_in_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return t * t * t


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    t -= 1
    return t * t * t + 1


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    if t < 0.5:
        return 4 * t * t * t
    t -= 1
    return 4 * t * t * t + 1


EASING_FUNCTIONS: Dict[str, Callable[[float], float]] = {
    "linear": linear,
    "easeInQuad": ease_in_quad,
    "easeOutQuad": ease_out_quad,
    "easeInOutQuad": ease_in_out_quad,
    "easeInCubic": ease_in_cubic,
    "easeOutCubic": ease_out_cubic,
    "easeInOutCubic": ease_in_out_cubic,
}

