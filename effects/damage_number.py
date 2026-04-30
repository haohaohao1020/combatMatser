import pygame

from config import (
    WHITE, RED, GREEN,
    clamp_color, with_alpha
)
from effects.base_effect import Effect


class DamageNumber(Effect):
    def __init__(self, x: float, y: float, damage: int, is_crit: bool = False, is_blocked: bool = False):
        super().__init__(x, y, 90)
        self.damage = damage
        self.is_crit = is_crit
        self.is_blocked = is_blocked
        self.vel_y = -3
        self.alpha = 255

    def update(self):
        super().update()
        self.y += self.vel_y
        self.vel_y *= 0.95
        if self.duration < 30:
            self.alpha = clamp_color(int(self.duration / 30 * 255))

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return

        if self.is_blocked:
            color = GREEN
        elif self.is_crit:
            color = RED
        else:
            color = WHITE

        size = 40 if self.is_crit else 28
        font = pygame.font.Font(None, size)

        if self.is_blocked:
            text = font.render("BLOCK!", True, color)
        else:
            text = font.render(str(self.damage), True, color)

        temp_surface = pygame.Surface((100, 50), pygame.SRCALPHA)
        text_rect = text.get_rect(center=(50, 25))
        temp_surface.blit(text, text_rect)

        temp_surface.set_alpha(clamp_color(self.alpha))

        draw_x = int(self.x + offset_x - 25)
        draw_y = int(self.y + offset_y)
        surface.blit(temp_surface, (draw_x, draw_y))
