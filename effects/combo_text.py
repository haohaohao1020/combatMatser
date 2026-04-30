import pygame

from config import (
    ORANGE,
    clamp_color, lerp
)
from effects.base_effect import Effect


class ComboText(Effect):
    def __init__(self, x: float, y: float, combo: int):
        super().__init__(x, y, 60)
        self.combo = combo
        self.scale = 2.0
        self.alpha = 255

    def update(self):
        super().update()
        self.scale = lerp(self.scale, 1.0, 0.1)
        if self.duration < 20:
            self.alpha = clamp_color(int(self.duration / 20 * 255))

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive or self.combo < 3:
            return

        font = pygame.font.Font(None, 60)
        text = font.render(f"{self.combo} HIT!", True, ORANGE)

        scaled_width = max(1, int(text.get_width() * self.scale))
        scaled_height = max(1, int(text.get_height() * self.scale))
        scaled_text = pygame.transform.scale(text, (scaled_width, scaled_height))

        temp_surface = pygame.Surface((200, 80), pygame.SRCALPHA)
        text_x = 100 - scaled_width // 2
        text_y = 40 - scaled_height // 2
        temp_surface.blit(scaled_text, (text_x, text_y))

        temp_surface.set_alpha(clamp_color(self.alpha))

        draw_x = int(self.x + offset_x - 100)
        draw_y = int(self.y + offset_y - 40)
        surface.blit(temp_surface, (draw_x, draw_y))
