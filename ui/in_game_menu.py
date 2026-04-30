import pygame
from typing import Optional

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY,
    YELLOW, LIGHT_GRAY, BLUE, RED, CYAN, PINK,
    clamp_color, with_alpha
)


class InGameMenu:
    def __init__(self):
        self.font_title: Optional[pygame.font.Font] = None
        self.font_option: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.selected_index = 0
        self.options = ["RESUME", "RESTART", "BACK TO MENU"]

    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 72)
        self.font_option = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 28)

    def handle_input(self, keys, events) -> Optional[int]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0

        return None

    def render_pause(self, surface: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_alpha = clamp_color(180)
        overlay.fill(with_alpha(BLACK, overlay_alpha))
        surface.blit(overlay, (0, 0))

        if self.font_title:
            title_text = self.font_title.render("PAUSED", True, WHITE)
            surface.blit(title_text, (
                SCREEN_WIDTH // 2 - title_text.get_width() // 2,
                150
            ))

        if self.font_option:
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

    def render_game_over(
        self,
        surface: pygame.Surface,
        winner_name: str,
        p1_max_combo: int,
        p2_max_combo: int,
        p1_total_damage: int,
        p2_total_damage: int,
        winner_is_p1: bool
    ):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_alpha = clamp_color(200)
        overlay.fill(with_alpha(BLACK, overlay_alpha))
        surface.blit(overlay, (0, 0))

        if self.font_title:
            winner_color = BLUE if winner_is_p1 else RED
            win_text = self.font_title.render("WINNER!", True, winner_color)
            surface.blit(win_text, (
                SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                120
            ))

            if self.font_option:
                name_text = self.font_option.render(winner_name, True, WHITE)
                surface.blit(name_text, (
                    SCREEN_WIDTH // 2 - name_text.get_width() // 2,
                    200
                ))

        if self.font_small:
            start_y = 300
            spacing = 40

            p1_header = self.font_small.render("PLAYER 1", True, CYAN)
            surface.blit(p1_header, (200, start_y))

            p1_combo = self.font_small.render(
                f"Max Combo: {p1_max_combo}",
                True, WHITE
            )
            surface.blit(p1_combo, (200, start_y + spacing))

            p1_dmg = self.font_small.render(
                f"Total Damage: {p1_total_damage}",
                True, WHITE
            )
            surface.blit(p1_dmg, (200, start_y + spacing * 2))

            p2_header = self.font_small.render("PLAYER 2", True, PINK)
            surface.blit(p2_header, (SCREEN_WIDTH - 400, start_y))

            p2_combo = self.font_small.render(
                f"Max Combo: {p2_max_combo}",
                True, WHITE
            )
            surface.blit(p2_combo, (SCREEN_WIDTH - 400, start_y + spacing))

            p2_dmg = self.font_small.render(
                f"Total Damage: {p2_total_damage}",
                True, WHITE
            )
            surface.blit(p2_dmg, (SCREEN_WIDTH - 400, start_y + spacing * 2))

        if self.font_small:
            hint_text = self.font_small.render(
                "Press ENTER to return to menu",
                True, GRAY
            )
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                SCREEN_HEIGHT - 80
            ))
