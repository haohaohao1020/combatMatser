import math
import pygame
from typing import Optional, Dict, Any, List, Tuple

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY, LIGHT_GRAY,
    CYAN, YELLOW, ORANGE, PURPLE, GREEN, RED, BLUE,
    clamp_color, safe_color, lerp, with_alpha
)
from characters.hero_system.character_types import HeroType, HeroArchetype, HERO_INFO
from characters.hero_system.hero_factory import get_hero_info, get_all_hero_types


class HeroSelectMenu:
    def __init__(self):
        self.font_title: Optional[pygame.font.Font] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.font_hint: Optional[pygame.font.Font] = None

        self.hero_types: List[HeroType] = get_all_hero_types()
        self.selected_index = 0
        self.player1_hero: Optional[HeroType] = None
        self.player2_hero: Optional[HeroType] = None
        self.selecting_player = 1
        self.animation_offset = 0
        self.preview_animation_time = 0

    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 80)
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 32)
        self.font_hint = pygame.font.Font(None, 26)

    def reset_selection(self):
        self.selected_index = 0
        self.player1_hero = None
        self.player2_hero = None
        self.selecting_player = 1

    def get_hero_at_index(self, index: int) -> HeroType:
        return self.hero_types[index % len(self.hero_types)]

    def get_current_hero_info(self) -> Dict[str, Any]:
        hero_type = self.get_hero_at_index(self.selected_index)
        return get_hero_info(hero_type)

    def update(self):
        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.003) * 8
        self.preview_animation_time = pygame.time.get_ticks()

    def handle_input(self, keys, events) -> Optional[Tuple[int, Optional[HeroType], Optional[HeroType]]]:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.selected_index = (self.selected_index - 1) % len(self.hero_types)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.selected_index = (self.selected_index + 1) % len(self.hero_types)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.selecting_player == 1:
                        self.player1_hero = self.get_hero_at_index(self.selected_index)
                        self.selecting_player = 2
                    else:
                        self.player2_hero = self.get_hero_at_index(self.selected_index)
                        return (0, self.player1_hero, self.player2_hero)
                elif event.key == pygame.K_ESCAPE:
                    return (1, None, None)

        return None

    def render(self, surface: pygame.Surface):
        self._render_background(surface)

        self._render_decorations(surface)

        self._render_title(surface)

        self._render_hero_preview(surface)

        self._render_hero_info(surface)

        self._render_selection_indicators(surface)

        self._render_hints(surface)

    def _render_background(self, surface: pygame.Surface):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = clamp_color(int(lerp(15, 50, t)))
            g = clamp_color(int(lerp(25, 70, t)))
            b = clamp_color(int(lerp(50, 120, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _render_decorations(self, surface: pygame.Surface):
        hero_info = self.get_current_hero_info()
        colors = hero_info.get("colors", {})
        accent = colors.get("accent", CYAN)

        decor_color = safe_color((
            clamp_color(accent[0] // 3),
            clamp_color(accent[1] // 3),
            clamp_color(accent[2] // 3)
        ))

        for i in range(6):
            x = int(math.sin(self.preview_animation_time * 0.001 + i) * 150 + SCREEN_WIDTH // 2)
            y = 350 + i * 40
            size = 40 + i * 8
            alpha = clamp_color(60 + int(math.sin(self.preview_animation_time * 0.002 + i) * 20))
            color = with_alpha(decor_color, alpha)
            pygame.draw.circle(surface, color, (x, y), size)

    def _render_title(self, surface: pygame.Surface):
        if not self.font_title:
            return

        if self.selecting_player == 1:
            title_text = "PLAYER 1 - SELECT YOUR HERO"
            title_color = CYAN
        else:
            title_text = "PLAYER 2 - SELECT YOUR HERO"
            title_color = RED

        rendered = self.font_title.render(title_text, True, title_color)
        title_x = SCREEN_WIDTH // 2 - rendered.get_width() // 2
        title_y = 60 + self.animation_offset

        glow_surface = pygame.Surface(
            (rendered.get_width() + 40, rendered.get_height() + 40),
            pygame.SRCALPHA
        )

        for i in range(4):
            alpha = clamp_color(40 - i * 8)
            glow_color = with_alpha(title_color, alpha)
            size = clamp_color(8 + i * 2)

            pygame.draw.rect(
                glow_surface, glow_color,
                (
                    20 - size // 2,
                    20 - size // 2,
                    rendered.get_width() + size,
                    rendered.get_height() + size
                ),
                width=size // 2,
                border_radius=10
            )

        surface.blit(glow_surface, (title_x - 20, title_y - 20))
        surface.blit(rendered, (title_x, title_y))

    def _render_hero_preview(self, surface: pygame.Surface):
        hero_info = self.get_current_hero_info()
        colors = hero_info.get("colors", {})
        primary = colors.get("primary", BLUE)
        secondary = colors.get("secondary", DARK_GRAY)
        accent = colors.get("accent", CYAN)

        preview_center_x = SCREEN_WIDTH // 2
        preview_center_y = 380
        preview_width = 100
        preview_height = 150

        pulse_size = 15 + math.sin(self.preview_animation_time * 0.005) * 5
        glow_surface = pygame.Surface((preview_width + 80, preview_height + 80), pygame.SRCALPHA)
        for i in range(5):
            glow_alpha = clamp_color(120 - i * 20)
            glow_color = with_alpha(accent, glow_alpha)
            glow_radius = int((preview_width // 2 + 30) + i * 15 + pulse_size)
            pygame.draw.ellipse(
                glow_surface, glow_color,
                (
                    (preview_width + 80) // 2 - glow_radius,
                    (preview_height + 80) // 2 - glow_radius + 20,
                    glow_radius * 2,
                    glow_radius
                ),
                width=max(1, 8 - i * 2)
            )

        surface.blit(glow_surface,
                    (preview_center_x - (preview_width + 80) // 2,
                     preview_center_y - (preview_height + 80) // 2))

        preview_x = preview_center_x - preview_width // 2
        preview_y = preview_center_y - preview_height // 2

        bounce_offset = math.sin(self.preview_animation_time * 0.004) * 8

        pygame.draw.rect(surface, primary,
                        (preview_x, preview_y + bounce_offset, preview_width, preview_height),
                        border_radius=15)
        pygame.draw.rect(surface, secondary,
                        (preview_x + 8, preview_y + 8 + bounce_offset,
                         preview_width - 16, preview_height - 16),
                        border_radius=10)

        head_x = preview_x + preview_width // 2
        head_y = preview_y + 25 + bounce_offset
        head_radius = 25

        pygame.draw.circle(surface, primary, (head_x, head_y), head_radius)
        pygame.draw.circle(surface, secondary, (head_x, head_y), head_radius - 4)

        eye_offset_x = 8
        eye_y = head_y - 3
        pygame.draw.circle(surface, WHITE, (head_x - eye_offset_x, eye_y), 5)
        pygame.draw.circle(surface, WHITE, (head_x + eye_offset_x, eye_y), 5)
        pygame.draw.circle(surface, BLACK, (head_x - eye_offset_x + 2, eye_y), 2)
        pygame.draw.circle(surface, BLACK, (head_x + eye_offset_x + 2, eye_y), 2)

        pygame.draw.line(
            surface, accent,
            (preview_x + preview_width // 2, preview_y + 60 + bounce_offset),
            (preview_x + preview_width // 2, preview_y + preview_height - 20 + bounce_offset),
            3
        )

    def _render_hero_info(self, surface: pygame.Surface):
        hero_info = self.get_current_hero_info()
        colors = hero_info.get("colors", {})
        accent = colors.get("accent", CYAN)

        info_panel_x = 80
        info_panel_y = 180
        info_panel_w = 320
        info_panel_h = 320

        panel_surface = pygame.Surface((info_panel_w, info_panel_h), pygame.SRCALPHA)
        panel_color = with_alpha(DARK_GRAY, 200)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, info_panel_w, info_panel_h), border_radius=15)

        name = hero_info.get("name", "Unknown")
        if self.font_medium:
            name_text = self.font_medium.render(name, True, accent)
            panel_surface.blit(name_text, (info_panel_w // 2 - name_text.get_width() // 2, 20))

        archetype = hero_info.get("archetype")
        archetype_name = {
            HeroArchetype.BALANCED: "平衡型",
            HeroArchetype.POWER: "力量型",
            HeroArchetype.SPEED: "速度型",
            HeroArchetype.CONTROL: "控制型"
        }.get(archetype, "未知类型")

        if self.font_small:
            arch_text = self.font_small.render(f"类型: {archetype_name}", True, LIGHT_GRAY)
            panel_surface.blit(arch_text, (20, 60))

        desc = hero_info.get("description", "")
        if self.font_small:
            max_width = info_panel_w - 40
            lines = self._wrap_text(desc, self.font_small, max_width)
            for i, line in enumerate(lines):
                desc_text = self.font_small.render(line, True, GRAY)
                panel_surface.blit(desc_text, (20, 90 + i * 25))

        special_name = hero_info.get("special_skill_name", "")
        ultimate_name = hero_info.get("ultimate_name", "")

        if self.font_small:
            special_label = self.font_small.render("小技能:", True, accent)
            special_text = self.font_small.render(special_name, True, WHITE)
            panel_surface.blit(special_label, (20, 180))
            panel_surface.blit(special_text, (100, 180))

            ultimate_label = self.font_small.render("必杀技:", True, ORANGE)
            ultimate_text = self.font_small.render(ultimate_name, True, WHITE)
            panel_surface.blit(ultimate_label, (20, 215))
            panel_surface.blit(ultimate_text, (100, 215))

        surface.blit(panel_surface, (info_panel_x, info_panel_y))

    def _render_selection_indicators(self, surface: pygame.Surface):
        hero_info = self.get_current_hero_info()
        colors = hero_info.get("colors", {})
        accent = colors.get("accent", CYAN)

        preview_center_x = SCREEN_WIDTH // 2
        arrow_y = 380

        left_arrow_x = preview_center_x - 180
        right_arrow_x = preview_center_x + 160

        arrow_pulse = 1 + math.sin(self.preview_animation_time * 0.005) * 0.2

        pygame.draw.polygon(surface, accent, [
            (left_arrow_x, arrow_y),
            (left_arrow_x + 30 * arrow_pulse, arrow_y - 25 * arrow_pulse),
            (left_arrow_x + 30 * arrow_pulse, arrow_y + 25 * arrow_pulse)
        ])

        pygame.draw.polygon(surface, accent, [
            (right_arrow_x + 30 * arrow_pulse, arrow_y),
            (right_arrow_x, arrow_y - 25 * arrow_pulse),
            (right_arrow_x, arrow_y + 25 * arrow_pulse)
        ])

        if self.player1_hero:
            p1_info = get_hero_info(self.player1_hero)
            p1_accent = p1_info.get("colors", {}).get("accent", CYAN)
            p1_name = p1_info.get("name", "")

            if self.font_medium:
                p1_text = self.font_medium.render(f"P1: {p1_name}", True, p1_accent)
                surface.blit(p1_text, (50, 520))

                if self.selecting_player == 2:
                    check_text = self.font_medium.render("✓", True, GREEN)
                    surface.blit(check_text, (20, 520))

        if self.player2_hero:
            p2_info = get_hero_info(self.player2_hero)
            p2_accent = p2_info.get("colors", {}).get("accent", RED)
            p2_name = p2_info.get("name", "")

            if self.font_medium:
                p2_text = self.font_medium.render(f"P2: {p2_name}", True, p2_accent)
                surface.blit(p2_text, (SCREEN_WIDTH - 200, 520))

    def _render_hints(self, surface: pygame.Surface):
        if not self.font_hint:
            return

        hints = [
            "LEFT/RIGHT or A/D: Select Hero",
            "ENTER or SPACE: Confirm Selection",
            "ESCAPE: Go Back"
        ]

        start_y = SCREEN_HEIGHT - 100
        spacing = 30

        for i, hint in enumerate(hints):
            hint_text = self.font_hint.render(hint, True, GRAY)
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                start_y + i * spacing
            ))

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            test_width = font.size(test_line)[0]

            if test_width <= max_width or not current_line:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines
