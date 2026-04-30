import random
from typing import Tuple


class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.duration = 0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def trigger(self, intensity: float, duration: int):
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)

    def update(self):
        if self.duration > 0:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)

            self.duration -= 1
            self.intensity *= 0.9
        else:
            self.offset_x = 0.0
            self.offset_y = 0.0

    def get_offset(self) -> Tuple[float, float]:
        return (self.offset_x, self.offset_y)
