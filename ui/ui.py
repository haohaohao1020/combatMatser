import math
import pygame
from typing import Optional, Tuple

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAX_ROUNDS,
    DARK_BLUE, DARK_RED, BLUE, RED,
    DARK_GRAY, GRAY, LIGHT_GRAY, WHITE, GREEN,
    PURPLE, ORANGE, YELLOW, BLACK, CYAN,
    clamp_color, lerp_color, with_alpha,
    lerp, clamp
)
from characters import Character


class UI:
    def __init__(self):
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.font_tiny: Optional[pygame.font.Font] = None

        self.round_transition_alpha = 0
        self.round_transition_text = ""

    def init_fonts(self):
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 20)

    def render_health_bar(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        width: int, height: int,
        current: int, maximum: int,
        is_player1: bool,
        rage: float, max_rage: float,
        player_name: str,
        is_flashing: bool = False
    ):
        border_color = DARK_BLUE if is_player1 else DARK_RED
        fill_color = BLUE if is_player1 else RED

        pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height), border_radius=5)
        pygame.draw.rect(surface, border_color, (x, y, width, height), 3, border_radius=5)

        health_ratio = current / maximum
        fill_width = max(0, int(width * health_ratio))

        if fill_width > 0:
            self._render_gradient_bar(
                surface,
                x + 3, y + 3,
                fill_width, height - 6,
                fill_color,
                is_player1
            )

        if health_ratio < 0.25:
            flash_alpha = clamp_color(int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 50))
            if flash_alpha > 0 and fill_width > 0:
                flash_surface = pygame.Surface((fill_width, height - 6), pygame.SRCALPHA)
                flash_color = with_alpha(RED, flash_alpha)
                pygame.draw.rect(flash_surface, flash_color, (0, 0, fill_width, height - 6))
                surface.blit(flash_surface, (x + 3, y + 3))

        self._render_rage_bar(
            surface,
            x, y + height + 8,
            width, 12,
            rage, max_rage
        )

        if self.font_small:
            name_text = self.font_small.render(player_name, True, WHITE)
            if is_player1:
                surface.blit(name_text, (x, y - 30))
            else:
                surface.blit(name_text, (x + width - name_text.get_width(), y - 30))

        if self.font_medium:
            health_text = self.font_medium.render(f"{current}", True, WHITE)
            if is_player1:
                surface.blit(health_text, (x + width + 10, y))
            else:
                text_width = health_text.get_width()
                surface.blit(health_text, (x - text_width - 10, y))

    def _render_gradient_bar(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        width: int, height: int,
        base_color: Tuple[int, ...],
        is_player1: bool
    ):
        gradient_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        color_light = lerp_color(base_color, WHITE, 0.3)
        color_dark = lerp_color(base_color, (0, 0, 0), 0.3)

        for i in range(width):
            t = i / width
            current_color = lerp_color(color_light, color_dark, t)
            pygame.draw.line(gradient_surface, current_color, (i, 0), (i, height))

        highlight_height = height // 3
        highlight = pygame.Surface((width, highlight_height), pygame.SRCALPHA)
        highlight_alpha = clamp_color(80)

        for i in range(width):
            pygame.draw.line(highlight, (255, 255, 255, highlight_alpha), (i, 0), (i, highlight_height))

        gradient_surface.blit(highlight, (0, 0))
        surface.blit(gradient_surface, (x, y))

    def _render_rage_bar(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        width: int, height: int,
        rage: float, max_rage: float
    ):
        rage_width = int(width * 0.8)
        rage_height = height
        rage_x = x + (width - rage_width) // 2
        rage_y = y

        pygame.draw.rect(surface, DARK_GRAY, (rage_x, rage_y, rage_width, rage_height), border_radius=3)

        if rage > 0:
            rage_ratio = rage / max_rage
            rage_fill = max(0, int(rage_width * rage_ratio))

            rage_surface = pygame.Surface((rage_fill, rage_height - 4), pygame.SRCALPHA)

            flow_offset = pygame.time.get_ticks() * 0.01

            for i in range(rage_fill):
                flow = (math.sin((i + flow_offset) * 0.1) + 1) * 0.5
                pixel_color = lerp_color(PURPLE, ORANGE, flow)
                pixel_color = lerp_color(pixel_color, WHITE, 0.2)
                pygame.draw.line(rage_surface, pixel_color, (i, 0), (i, rage_height - 4))

            if rage_ratio >= 1.0:
                flash = clamp_color(int((math.sin(pygame.time.get_ticks() * 0.02) + 1) * 50))
                if flash > 0:
                    flash_color = with_alpha(WHITE, flash)
                    pygame.draw.rect(rage_surface, flash_color, (0, 0, rage_fill, rage_height - 4))

            surface.blit(rage_surface, (rage_x + 2, rage_y + 2))

        border_color = PURPLE if rage < max_rage else YELLOW
        pygame.draw.rect(surface, border_color, (rage_x, rage_y, rage_width, rage_height), 2, border_radius=3)

    def render_timer(self, surface: pygame.Surface, time_remaining: int):
        if self.font_large:
            timer_x = SCREEN_WIDTH // 2 - 50

            pygame.draw.rect(surface, DARK_GRAY, (timer_x, 10, 100, 50), border_radius=10)
            pygame.draw.rect(surface, GRAY, (timer_x + 3, 13, 94, 44), 2, border_radius=8)

            color = RED if time_remaining <= 10 else WHITE
            timer_text = self.font_large.render(f"{time_remaining}", True, color)
            surface.blit(timer_text, (
                SCREEN_WIDTH // 2 - timer_text.get_width() // 2,
                15
            ))

    def render_round_score(self, surface: pygame.Surface, p1_wins: int, p2_wins: int):
        if self.font_small:
            for i in range(MAX_ROUNDS):
                x1 = 20 + i * 30
                color1 = GREEN if i < p1_wins else DARK_GRAY
                pygame.draw.circle(surface, color1, (x1 + 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x1 + 10, 85), 10, 2)

                x2 = SCREEN_WIDTH - 20 - (MAX_ROUNDS - 1 - i) * 30
                color2 = GREEN if i < p2_wins else DARK_GRAY
                pygame.draw.circle(surface, color2, (x2 - 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x2 - 10, 85), 10, 2)

    def render_combo(self, surface: pygame.Surface, player1: Character, player2: Character):
        if self.font_medium:
            if player2.hit_combo >= 2:
                combo_text = self.font_medium.render(
                    f"COMBO x{player2.hit_combo}",
                    True, ORANGE
                )
                surface.blit(combo_text, (20, 120))

            if player1.hit_combo >= 2:
                combo_text = self.font_medium.render(
                    f"COMBO x{player1.hit_combo}",
                    True, ORANGE
                )
                surface.blit(combo_text, (
                    SCREEN_WIDTH - combo_text.get_width() - 20,
                    120
                ))

    def render_round_transition(self, surface: pygame.Surface, text: str, alpha: int):
        if self.font_large and alpha > 0:
            safe_alpha = clamp_color(alpha)

            transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

            overlay_alpha = clamp_color(min(safe_alpha, 180))
            overlay_color = with_alpha(BLACK, overlay_alpha)
            transition_surface.fill(overlay_color)

            text_surface = self.font_large.render(text, True, WHITE)
            text_surface.set_alpha(safe_alpha)

            transition_surface.blit(
                text_surface,
                (
                    SCREEN_WIDTH // 2 - text_surface.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text_surface.get_height() // 2
                )
            )

            surface.blit(transition_surface, (0, 0))

    def render_endless_hud(
        self,
        surface: pygame.Surface,
        wave: int,
        survival_time: str,
        combo_kills: int,
        score: int,
        difficulty_color: tuple,
        difficulty_desc: str
    ):
        panel_width = 200
        panel_height = 120
        panel_x = 10
        panel_y = 80

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_alpha = clamp_color(200)
        panel_color = with_alpha(DARK_GRAY, panel_alpha)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(panel_surface, GRAY, (0, 0, panel_width, panel_height), 2, border_radius=10)

        surface.blit(panel_surface, (panel_x, panel_y))

        if self.font_small:
            wave_text = self.font_small.render(f"WAVE: {wave}", True, WHITE)
            surface.blit(wave_text, (panel_x + 15, panel_y + 10))

            time_text = self.font_small.render(f"TIME: {survival_time}", True, WHITE)
            surface.blit(time_text, (panel_x + 15, panel_y + 35))

            combo_color = ORANGE if combo_kills >= 5 else YELLOW if combo_kills >= 3 else WHITE
            combo_text = self.font_small.render(f"COMBO: {combo_kills}x", True, combo_color)
            surface.blit(combo_text, (panel_x + 15, panel_y + 60))

            score_text = self.font_small.render(f"SCORE: {score:,}", True, GREEN)
            surface.blit(score_text, (panel_x + 15, panel_y + 85))

        diff_panel_width = 200
        diff_panel_height = 40
        diff_panel_x = SCREEN_WIDTH - diff_panel_width - 10
        diff_panel_y = 80

        diff_surface = pygame.Surface((diff_panel_width, diff_panel_height), pygame.SRCALPHA)
        pygame.draw.rect(diff_surface, panel_color, (0, 0, diff_panel_width, diff_panel_height), border_radius=8)
        pygame.draw.rect(diff_surface, difficulty_color, (0, 0, diff_panel_width, diff_panel_height), 2, border_radius=8)

        surface.blit(diff_surface, (diff_panel_x, diff_panel_y))

        if self.font_small:
            diff_text = self.font_small.render(difficulty_desc, True, difficulty_color)
            text_rect = diff_text.get_rect(center=(diff_panel_width // 2, diff_panel_height // 2))
            surface.blit(diff_text, (diff_panel_x + text_rect.x, diff_panel_y + text_rect.y))

    def render_endless_wave_transition(
        self,
        surface: pygame.Surface,
        wave: int,
        alpha: int,
        heal_amount: int = 0
    ):
        if self.font_large and alpha > 0:
            safe_alpha = clamp_color(alpha)

            transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

            overlay_alpha = clamp_color(min(safe_alpha, 150))
            overlay_color = with_alpha(BLACK, overlay_alpha)
            transition_surface.fill(overlay_color)

            wave_text = self.font_large.render(f"WAVE {wave}", True, ORANGE)
            wave_text.set_alpha(safe_alpha)

            transition_surface.blit(
                wave_text,
                (
                    SCREEN_WIDTH // 2 - wave_text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - wave_text.get_height() // 2 - 30
                )
            )

            if self.font_medium and heal_amount > 0:
                heal_text = self.font_medium.render(f"+{heal_amount} HP RESTORED", True, GREEN)
                heal_text.set_alpha(safe_alpha)
                transition_surface.blit(
                    heal_text,
                    (
                        SCREEN_WIDTH // 2 - heal_text.get_width() // 2,
                        SCREEN_HEIGHT // 2 + 30
                    )
                )

            surface.blit(transition_surface, (0, 0))

    def render_gold_display(
        self,
        surface: pygame.Surface,
        gold: int,
        x: int = 10,
        y: int = 10
    ):
        if not self.font_small:
            return

        panel_width = 150
        panel_height = 40

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_alpha = clamp_color(200)
        panel_color = with_alpha(DARK_GRAY, panel_alpha)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(panel_surface, YELLOW, (0, 0, panel_width, panel_height), 2, border_radius=8)

        surface.blit(panel_surface, (x, y))

        coin_text = self.font_small.render(f"GOLD: {gold}", True, YELLOW)
        surface.blit(coin_text, (x + 15, y + 8))

    def render_experience_bar(
        self,
        surface: pygame.Surface,
        level: int,
        current_exp: int,
        exp_to_next: int,
        x: int,
        y: int,
        width: int = 200,
        height: int = 12,
        is_player1: bool = True
    ):
        if not self.font_small:
            return

        bar_color = ORANGE if is_player1 else PURPLE
        border_color = DARK_GRAY

        pygame.draw.rect(surface, border_color, (x, y, width, height), border_radius=4)

        if exp_to_next > 0:
            exp_ratio = max(0.0, min(1.0, current_exp / exp_to_next))
            fill_width = int(width * exp_ratio)
            if fill_width > 0:
                exp_surface = pygame.Surface((fill_width, height - 4), pygame.SRCALPHA)
                for i in range(fill_width):
                    t = i / fill_width
                    color = lerp_color(YELLOW, bar_color, t)
                    pygame.draw.line(exp_surface, color, (i, 0), (i, height - 4))
                surface.blit(exp_surface, (x + 2, y + 2))

        pygame.draw.rect(surface, bar_color, (x, y, width, height), 2, border_radius=4)

        level_text = self.font_small.render(f"Lv.{level}", True, WHITE)
        if is_player1:
            surface.blit(level_text, (x - 50, y - 2))
        else:
            surface.blit(level_text, (x + width + 10, y - 2))

    def render_hero_level_info(
        self,
        surface: pygame.Surface,
        level: int,
        current_exp: int,
        exp_to_next: int,
        talent_points: int,
        x: int = 10,
        y: int = 60
    ):
        if not self.font_small:
            return

        panel_width = 280
        panel_height = 55

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_alpha = clamp_color(200)
        panel_color = with_alpha(DARK_GRAY, panel_alpha)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(panel_surface, CYAN, (0, 0, panel_width, panel_height), 2, border_radius=8)

        surface.blit(panel_surface, (x, y))

        level_text = self.font_small.render(f"LEVEL: {level}", True, CYAN)
        surface.blit(level_text, (x + 15, y + 8))

        if talent_points > 0:
            talent_text = self.font_small.render(f"TP: {talent_points}", True, ORANGE)
            surface.blit(talent_text, (x + 150, y + 8))

        bar_x = x + 15
        bar_y = y + 32
        bar_width = panel_width - 30
        bar_height = 10

        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=3)

        if exp_to_next > 0:
            exp_ratio = max(0.0, min(1.0, current_exp / exp_to_next))
            fill_width = int(bar_width * exp_ratio)
            if fill_width > 0:
                for i in range(fill_width):
                    t = i / bar_width
                    color = lerp_color(YELLOW, ORANGE, t)
                    pygame.draw.line(surface, color, (bar_x + i, bar_y + 2), (bar_x + i, bar_y + bar_height - 2))

        pygame.draw.rect(surface, ORANGE, (bar_x, bar_y, bar_width, bar_height), 1, border_radius=3)

        if self.font_tiny:
            exp_text = self.font_tiny.render(f"{current_exp}/{exp_to_next}", True, WHITE)
            surface.blit(exp_text, (bar_x + bar_width // 2 - exp_text.get_width() // 2, bar_y - 20))
