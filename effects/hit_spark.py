import math
import random
from typing import List
import pygame

from config import (
    YELLOW, ORANGE, WHITE, RED,
    clamp_color, safe_color
)
from effects.base_effect import Effect


class HitSpark(Effect):
    def __init__(self, x: float, y: float, intensity: float = 1.0):
        super().__init__(x, y, int(25 * intensity))
        self.particles: List[dict] = []

        num_particles = int(12 * intensity)
        available_colors = [YELLOW, ORANGE, WHITE, RED]

        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8) * intensity
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': clamp_color(int(random.uniform(3, 8) * intensity)),
                'color': random.choice(available_colors)
            })

    def update(self):
        super().update()

        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3
            p['size'] = max(1, int(p['size'] * 0.92))

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return

        for p in self.particles:
            size = p['size']
            if size > 0:
                draw_x = clamp_color(int(p['x'] + offset_x))
                draw_y = clamp_color(int(p['y'] + offset_y))
                pygame.draw.circle(surface, p['color'], (draw_x, draw_y), size)
