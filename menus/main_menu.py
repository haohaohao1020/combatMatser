import math
import pygame
from typing import Optional

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY,
    CYAN, YELLOW, LIGHT_GRAY,
    clamp_color, safe_color, lerp, with_alpha
)


class MainMenu:
    def __init__(self):
        self.font_title: Optional[pygame.font.Font] = None
        self.font_option: Optional[pygame.font.Font] = None
        self.font_hint: Optional[pygame.font.Font] = None

        self.selected_index = 0
        self.options = []
        self.menu_type = "main"
        self.animation_offset = 0

    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 100)
        self.font_option = pygame.font.Font(None, 48)
        self.font_hint = pygame.font.Font(None, 28)

    def set_menu(self, menu_type: str):
        self.menu_type = menu_type
        self.selected_index = 0

        if menu_type == "main":
            self.options = ["START GAME", "ENDLESS SURVIVAL", "QUIT"]
        elif menu_type == "mode":
            self.options = ["PLAYER VS PLAYER", "PLAYER VS CPU", "BACK"]
        elif menu_type == "difficulty":
            self.options = ["EASY", "HARD", "BACK"]

    def update(self):
        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.003) * 10

    def handle_input(self, keys, events) -> Optional[int]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.selected_index

        return None

    def render(self, surface: pygame.Surface):
        self._render_background(surface)

        self._render_decorations(surface)

        if self.menu_type == "main" and self.font_title:
            self._render_main_title(surface)
        elif self.menu_type == "mode" and self.font_title:
            title_text = self.font_title.render("SELECT MODE", True, WHITE)
            surface.blit(title_text, (
                SCREEN_WIDTH // 2 - title_text.get_width() // 2,
                120
            ))
        elif self.menu_type == "difficulty" and self.font_title:
            title_text = self.font_title.render("SELECT DIFFICULTY", True, WHITE)
            surface.blit(title_text, (
                SCREEN_WIDTH // 2 - title_text.get_width() // 2,
                120
            ))

        if self.font_option:
            self._render_options(surface)

        if self.font_hint:
            hint_text = self.font_hint.render(
                "UP/DOWN or W/S to select, ENTER to confirm",
                True, GRAY
            )
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                SCREEN_HEIGHT - 60
            ))

    def _render_background(self, surface: pygame.Surface):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = clamp_color(int(lerp(10, 40, t)))
            g = clamp_color(int(lerp(20, 60, t)))
            b = clamp_color(int(lerp(40, 100, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _render_decorations(self, surface: pygame.Surface):
        decor_color = safe_color((30, 60, 120))

        for i in range(8):
            x = int(math.sin(pygame.time.get_ticks() * 0.001 + i) * 200 + SCREEN_WIDTH // 2)
            pygame.draw.circle(
                surface, decor_color,
                (x, 300 + i * 50),
                50 + i * 10
            )

    def _render_main_title(self, surface: pygame.Surface):
        if not self.font_title:
            return

        title_text = self.font_title.render("COMBAT MASTER", True, CYAN)
        title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
        title_y = 100 + self.animation_offset

        glow_surface = pygame.Surface(
            (title_text.get_width() + 40, title_text.get_height() + 40),
            pygame.SRCALPHA
        )

        for i in range(5):
            alpha = clamp_color(50 - i * 10)
            glow_color = with_alpha(CYAN, alpha)
            size = clamp_color(10 + i * 2)

            pygame.draw.rect(
                glow_surface, glow_color,
                (
                    20 - size // 2,
                    20 - size // 2,
                    title_text.get_width() + size,
                    title_text.get_height() + size
                ),
                width=size // 2,
                border_radius=10
            )

        surface.blit(glow_surface, (title_x - 20, title_y - 20))
        surface.blit(title_text, (title_x, title_y))

    def _render_options(self, surface: pygame.Surface):
        start_y = 280
        spacing = 70

        for i, option in enumerate(self.options):
            is_selected = i == self.selected_index
            color = YELLOW if is_selected else LIGHT_GRAY

            text = self.font_option.render(option, True, color)
            text_x = SCREEN_WIDTH // 2 - text.get_width() // 2
            text_y = start_y + i * spacing

            if is_selected:
                indicator_x = text_x - 50
                pygame.draw.polygon(surface, YELLOW, [
                    (indicator_x, text_y + 15),
                    (indicator_x + 20, text_y + 5),
                    (indicator_x + 20, text_y + 25)
                ])
                pygame.draw.polygon(surface, YELLOW, [
                    (text_x + text.get_width() + 30, text_y + 15),
                    (text_x + text.get_width() + 10, text_y + 5),
                    (text_x + text.get_width() + 10, text_y + 25)
                ])

            surface.blit(text, (text_x, text_y))
