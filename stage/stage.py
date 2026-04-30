import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y,
    DARK_GRAY, GRAY, LIGHT_GRAY,
    clamp_color, lerp, safe_color, clamp
)


class Stage:
    def __init__(self):
        self.grid_offset = 0.0

    def update(self):
        self.grid_offset += 0.5

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        self._render_background(surface)

        self._render_background_decorations(surface)

        self._render_ground(surface, offset_x, offset_y)

    def _render_background(self, surface: pygame.Surface):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = clamp_color(int(lerp(20, 60, t)))
            g = clamp_color(int(lerp(30, 80, t)))
            b = clamp_color(int(lerp(50, 120, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _render_background_decorations(self, surface: pygame.Surface):
        decor_color = safe_color((40, 70, 100))

        for i in range(5):
            x = (i * 300 + self.grid_offset * 0.3) % (SCREEN_WIDTH + 200) - 100
            draw_x = clamp_color(int(x))
            pygame.draw.circle(surface, decor_color, (draw_x, 200), 80)

    def _render_ground(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        ground_y = int(clamp(GROUND_Y + offset_y, 0, SCREEN_HEIGHT))

        pygame.draw.rect(
            surface, DARK_GRAY,
            (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y)
        )

        for i in range(int(SCREEN_WIDTH / 40) + 2):
            x = int((i * 40 - self.grid_offset + offset_x) % (SCREEN_WIDTH + 40))
            pygame.draw.line(surface, GRAY, (x, ground_y), (x, SCREEN_HEIGHT), 1)

        for i in range(int((SCREEN_HEIGHT - GROUND_Y) / 30) + 2):
            y = int(ground_y + i * 30)
            if y < SCREEN_HEIGHT:
                pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y), 1)

        pygame.draw.line(surface, LIGHT_GRAY, (0, ground_y), (SCREEN_WIDTH, ground_y), 3)
