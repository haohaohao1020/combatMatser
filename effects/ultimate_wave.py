import pygame

from config import (
    CYAN, SCREEN_WIDTH, SCREEN_HEIGHT,
    clamp_color, with_alpha, lerp
)
from effects.base_effect import Effect


class UltimateWave(Effect):
    def __init__(self, x: float, y: float, max_radius: float = 400):
        super().__init__(x, y, 60)
        self.radius = 0
        self.max_radius = max_radius
        self.alpha = 200

    def update(self):
        super().update()
        self.radius = lerp(self.radius, self.max_radius, 0.15)
        self.alpha = clamp_color(int(self.duration / 60 * 200))

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return

        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        center_x = int(self.x + offset_x)
        center_y = int(self.y + offset_y)

        for i in range(3):
            r = int(self.radius - i * 30)
            if r > 0:
                wave_alpha = clamp_color(int(self.alpha * (1 - i * 0.3)))
                wave_color = with_alpha(CYAN, wave_alpha)
                line_width = clamp_color(8 - i * 2)

                pygame.draw.circle(
                    temp_surface,
                    wave_color,
                    (center_x, center_y),
                    r,
                    width=line_width
                )

        surface.blit(temp_surface, (0, 0))
