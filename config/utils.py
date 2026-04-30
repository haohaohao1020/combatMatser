import math
from typing import Tuple


def clamp_color(value: int) -> int:
    return max(0, min(255, int(value)))


def safe_color(color: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(clamp_color(c) for c in color)


def lerp_color(color1: Tuple[int, ...], color2: Tuple[int, ...], t: float) -> Tuple[int, ...]:
    t = max(0.0, min(1.0, t))
    return tuple(clamp_color(color1[i] + (color2[i] - color1[i]) * t) for i in range(len(color1)))


def scale_color(color: Tuple[int, ...], scale: float) -> Tuple[int, ...]:
    return tuple(clamp_color(c * scale) for c in color)


def add_color(color1: Tuple[int, ...], color2: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(clamp_color(color1[i] + color2[i]) for i in range(len(color1)))


def with_alpha(color: Tuple[int, ...], alpha: int) -> Tuple[int, ...]:
    alpha = clamp_color(alpha)
    if len(color) == 3:
        return (color[0], color[1], color[2], alpha)
    elif len(color) == 4:
        return (color[0], color[1], color[2], alpha)
    return color


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def get_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
