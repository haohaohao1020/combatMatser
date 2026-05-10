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
from progression import ProgressionManager, TalentBranch


class HeroSelectMenu:
    def __init__(self, progression_manager=None):
        self.font_title: Optional[pygame.font.Font] = None
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.font_hint: Optional[pygame.font.Font] = None
        self.font_tiny: Optional[pygame.font.Font] = None

        self.hero_types: List[HeroType] = get_all_hero_types()
        self.selected_index = 0
        self.player1_hero: Optional[HeroType] = None
        self.player2_hero: Optional[HeroType] = None
        self.selecting_player = 1
        self.animation_offset = 0
        self.preview_animation_time = 0

        self.single_player_mode = False

        self.current_view = "select"
        self.progression = progression_manager if progression_manager else ProgressionManager()

        self.selected_talent_branch: str = "attack"
        self.selected_talent_index: int = 0
        self.talent_highlighted: Optional[str] = None

        self.menu_buttons: List[Dict[str, Any]] = []
        self._init_buttons()

    def set_progression_manager(self, progression_manager):
        self.progression = progression_manager

    def _init_buttons(self):
        button_width = 200
        button_height = 50
        start_x = SCREEN_WIDTH // 2 - button_width - 50
        start_y = SCREEN_HEIGHT - 180

        self.menu_buttons = [
            {
                "id": "select",
                "label": "选择英雄",
                "x": start_x,
                "y": start_y,
                "w": button_width,
                "h": button_height,
                "color": CYAN,
                "active_color": (100, 255, 255),
                "view": "select"
            },
            {
                "id": "talents",
                "label": "天赋加点",
                "x": start_x + button_width + 100,
                "y": start_y,
                "w": button_width,
                "h": button_height,
                "color": ORANGE,
                "active_color": (255, 180, 100),
                "view": "talents"
            }
        ]

    def init_fonts(self):
        chinese_font_names = [
            "microsoftyahei",
            "msyh",
            "simhei",
            "simsun",
            "microsoftyaheiui",
            "fangsong",
            "kaiti",
            "youyuan",
        ]

        chinese_font_files = [
            "msyh.ttc",
            "simhei.ttf",
            "simsun.ttc",
            "msyhl.ttc",
            "msyhbd.ttc",
        ]

        self.font_title = self._load_chinese_font(80, chinese_font_names, chinese_font_files)
        self.font_large = self._load_chinese_font(56, chinese_font_names, chinese_font_files)
        self.font_medium = self._load_chinese_font(42, chinese_font_names, chinese_font_files)
        self.font_small = self._load_chinese_font(32, chinese_font_names, chinese_font_files)
        self.font_hint = self._load_chinese_font(26, chinese_font_names, chinese_font_files)
        self.font_tiny = self._load_chinese_font(20, chinese_font_names, chinese_font_files)

    def _load_chinese_font(self, size: int, font_names: List[str], font_files: List[str]) -> pygame.font.Font:
        import os

        test_text = "测试中文"

        for font_name in font_names:
            try:
                font = pygame.font.SysFont(font_name, size)
                if font:
                    try:
                        rendered = font.render(test_text, True, (255, 255, 255))
                        if rendered and rendered.get_width() > 0:
                            return font
                    except:
                        continue
            except:
                continue

        windows_fonts_path = "C:\\Windows\\Fonts"
        for font_file in font_files:
            try:
                font_path = os.path.join(windows_fonts_path, font_file)
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                    if font:
                        try:
                            rendered = font.render(test_text, True, (255, 255, 255))
                            if rendered and rendered.get_width() > 0:
                                return font
                        except:
                            continue
            except:
                continue

        for font_name in ["arial", "courier", "times"]:
            try:
                font = pygame.font.SysFont(font_name, size)
                if font:
                    return font
            except:
                continue

        return pygame.font.Font(None, size)

    def reset_selection(self):
        self.selected_index = 0
        self.player1_hero = None
        self.player2_hero = None
        self.selecting_player = 1
        self.single_player_mode = False
        self.current_view = "select"

    def get_hero_at_index(self, index: int) -> HeroType:
        return self.hero_types[index % len(self.hero_types)]

    def get_current_hero_info(self) -> Dict[str, Any]:
        hero_type = self.get_hero_at_index(self.selected_index)
        return get_hero_info(hero_type)

    def update(self):
        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.003) * 8
        self.preview_animation_time = pygame.time.get_ticks()

    def handle_input(self, keys, events) -> Optional[Tuple[int, Optional[HeroType], Optional[HeroType]]]:
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.current_view == "select":
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.selected_index = (self.selected_index - 1) % len(self.hero_types)
                        self.talent_highlighted = None
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.selected_index = (self.selected_index + 1) % len(self.hero_types)
                        self.talent_highlighted = None
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.selecting_player == 1:
                            self.player1_hero = self.get_hero_at_index(self.selected_index)
                            if self.single_player_mode:
                                return (0, self.player1_hero, None)
                            self.selecting_player = 2
                        else:
                            self.player2_hero = self.get_hero_at_index(self.selected_index)
                            return (0, self.player1_hero, self.player2_hero)
                    elif event.key == pygame.K_t:
                        self.current_view = "talents"
                        self.talent_highlighted = None
                    elif event.key == pygame.K_ESCAPE:
                        return (1, None, None)

                elif self.current_view == "talents":
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        branches = ["attack", "defense", "technique"]
                        current_idx = branches.index(self.selected_talent_branch)
                        self.selected_talent_branch = branches[(current_idx - 1) % 3]
                        self.selected_talent_index = 0
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        branches = ["attack", "defense", "technique"]
                        current_idx = branches.index(self.selected_talent_branch)
                        self.selected_talent_branch = branches[(current_idx + 1) % 3]
                        self.selected_talent_index = 0
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.selected_talent_index = max(0, self.selected_talent_index - 1)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        hero_type = self.get_hero_at_index(self.selected_index)
                        talent_tree = self.progression.get_talent_tree_for_character(hero_type.name)
                        talents_in_branch = [t for t in talent_tree.values() if t.branch.value == self.selected_talent_branch]
                        self.selected_talent_index = min(len(talents_in_branch) - 1, self.selected_talent_index + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        hero_type = self.get_hero_at_index(self.selected_index)
                        talent_tree = self.progression.get_talent_tree_for_character(hero_type.name)
                        talents_in_branch = [t for t in talent_tree.values() if t.branch.value == self.selected_talent_branch]
                        if 0 <= self.selected_talent_index < len(talents_in_branch):
                            talent = talents_in_branch[self.selected_talent_index]
                            if talent.unlocked and talent.points_spent < talent.max_points:
                                self.progression.spend_talent_point(hero_type.name, talent.talent_id)
                    elif event.key == pygame.K_r:
                        hero_type = self.get_hero_at_index(self.selected_index)
                        current_gold = self.progression.get_total_gold()
                        if current_gold >= 500:
                            self.progression.reset_talents(hero_type.name, 500)
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_t:
                        self.current_view = "select"
                        self.talent_highlighted = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in self.menu_buttons:
                    if btn["x"] <= mouse_pos[0] <= btn["x"] + btn["w"] and \
                       btn["y"] <= mouse_pos[1] <= btn["y"] + btn["h"]:
                        self.current_view = btn["view"]
                        self.talent_highlighted = None
                        break

        return None

    def render(self, surface: pygame.Surface):
        if self.current_view == "select":
            self._render_select_view(surface)
        elif self.current_view == "talents":
            self._render_talents_view(surface)

        self._render_menu_buttons(surface)

    def _render_select_view(self, surface: pygame.Surface):
        self._render_background(surface)
        self._render_decorations(surface)
        self._render_title(surface)
        self._render_hero_preview(surface)
        self._render_hero_info(surface)
        self._render_character_progression_panel(surface)
        self._render_selection_indicators(surface)
        self._render_hints(surface)

    def _render_talents_view(self, surface: pygame.Surface):
        self._render_background(surface)
        self._render_talents_background(surface)
        self._render_talent_branch_selector(surface)
        self._render_talent_tree(surface)
        self._render_talent_info_panel(surface)
        self._render_character_stats_panel(surface)
        self._render_talents_hints(surface)

    def _render_background(self, surface: pygame.Surface):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = clamp_color(int(lerp(15, 50, t)))
            g = clamp_color(int(lerp(25, 70, t)))
            b = clamp_color(int(lerp(50, 120, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _render_talents_background(self, surface: pygame.Surface):
        hero_type = self.get_hero_at_index(self.selected_index)
        hero_info = get_hero_info(hero_type)
        colors = hero_info.get("colors", {})
        accent = colors.get("accent", CYAN)

        title = f"{hero_info.get('name', 'Unknown')} - 天赋树"
        if self.font_title:
            title_text = self.font_title.render(title, True, accent)
            title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
            surface.blit(title_text, (title_x, 40))

        prog = self.progression.get_character_progression(hero_type.name)
        if self.font_medium:
            level_text = self.font_medium.render(f"等级: {prog.level}  天赋点: {prog.available_talent_points}", True, ORANGE)
            surface.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 110))

        if self.font_small:
            gold_text = self.font_small.render(f"金币: {self.progression.get_total_gold()}", True, YELLOW)
            surface.blit(gold_text, (SCREEN_WIDTH - 200, 15))

    def _render_talent_branch_selector(self, surface: pygame.Surface):
        branches = [
            ("attack", "攻击系", RED),
            ("defense", "防御系", CYAN),
            ("technique", "技巧系", PURPLE)
        ]

        total_width = 600
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        y = 160
        btn_width = 180
        btn_height = 45

        for i, (branch_id, name, color) in enumerate(branches):
            x = start_x + i * (btn_width + 30)

            is_selected = branch_id == self.selected_talent_branch

            if is_selected:
                pygame.draw.rect(surface, color, (x, y, btn_width, btn_height), border_radius=10)
                border_color = WHITE
            else:
                panel_surface = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
                panel_color = with_alpha(DARK_GRAY, 200)
                pygame.draw.rect(panel_surface, panel_color, (0, 0, btn_width, btn_height), border_radius=10)
                surface.blit(panel_surface, (x, y))
                border_color = color

            pygame.draw.rect(surface, border_color, (x, y, btn_width, btn_height), 3, border_radius=10)

            if self.font_small:
                text = self.font_small.render(name, True, WHITE if is_selected else LIGHT_GRAY)
                text_x = x + btn_width // 2 - text.get_width() // 2
                text_y = y + btn_height // 2 - text.get_height() // 2
                surface.blit(text, (text_x, text_y))

    def _render_talent_tree(self, surface: pygame.Surface):
        hero_type = self.get_hero_at_index(self.selected_index)
        talent_tree = self.progression.get_talent_tree_for_character(hero_type.name)

        talents_in_branch = [t for t in talent_tree.values() if t.branch.value == self.selected_talent_branch]
        talents_in_branch.sort(key=lambda t: t.tier)

        start_y = 230
        row_height = 90
        node_width = 180
        node_height = 50

        self.talent_highlighted = None

        for idx, talent in enumerate(talents_in_branch):
            row = idx
            center_x = SCREEN_WIDTH // 2
            x = center_x - node_width // 2
            y = start_y + row * row_height

            is_selected = idx == self.selected_talent_index
            is_maxed = talent.points_spent >= talent.max_points
            is_unlocked = talent.unlocked

            if is_unlocked:
                if is_maxed:
                    panel_color = GREEN
                    border_color = YELLOW
                elif is_selected:
                    panel_color = ORANGE
                    border_color = WHITE
                else:
                    panel_color = with_alpha(DARK_GRAY, 220)
                    border_color = LIGHT_GRAY
            else:
                panel_color = with_alpha((60, 60, 80), 150)
                border_color = GRAY

            panel_surface = pygame.Surface((node_width, node_height), pygame.SRCALPHA)
            if isinstance(panel_color, tuple) and len(panel_color) == 4:
                pygame.draw.rect(panel_surface, panel_color, (0, 0, node_width, node_height), border_radius=8)
            else:
                pygame.draw.rect(panel_surface, panel_color, (0, 0, node_width, node_height), border_radius=8)
            surface.blit(panel_surface, (x, y))
            pygame.draw.rect(surface, border_color, (x, y, node_width, node_height), 3 if is_selected else 2, border_radius=8)

            if self.font_small:
                name_color = WHITE if is_unlocked else (100, 100, 100)
                name_text = self.font_small.render(talent.name, True, name_color)
                surface.blit(name_text, (x + 10, y + 8))

            if self.font_tiny:
                progress_text = self.font_tiny.render(
                    f"{talent.points_spent}/{talent.max_points}",
                    True, YELLOW if is_maxed else LIGHT_GRAY
                )
                surface.blit(progress_text, (x + node_width - progress_text.get_width() - 10, y + 25))

            if self.font_tiny:
                req_text = self.font_tiny.render(
                    f"解锁" if is_unlocked else f"需要前置",
                    True, GREEN if is_unlocked else RED
                )
                surface.blit(req_text, (x + 10, y + 28))

            if is_selected:
                self.talent_highlighted = talent.talent_id

    def _render_talent_info_panel(self, surface: pygame.Surface):
        hero_type = self.get_hero_at_index(self.selected_index)
        talent_tree = self.progression.get_talent_tree_for_character(hero_type.name)

        selected_talent = None
        if self.talent_highlighted:
            selected_talent = talent_tree.get(self.talent_highlighted)

        panel_x = 30
        panel_y = 220
        panel_width = 280
        panel_height = 400

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_color = with_alpha(DARK_GRAY, 200)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(panel_surface, CYAN, (0, 0, panel_width, panel_height), 2, border_radius=15)

        if self.font_medium:
            title = self.font_medium.render("天赋详情", True, CYAN)
            panel_surface.blit(title, (10, 10))

        if selected_talent:
            if self.font_small:
                name_text = self.font_small.render(selected_talent.name, True, WHITE)
                panel_surface.blit(name_text, (20, 60))

                desc_text = self.font_small.render(selected_talent.description, True, LIGHT_GRAY)
                panel_surface.blit(desc_text, (20, 100))

                tier_color = {1: GREEN, 2: YELLOW, 3: ORANGE}.get(selected_talent.tier, GRAY)
                tier_text = self.font_small.render(f"阶层: {selected_talent.tier}", True, tier_color)
                panel_surface.blit(tier_text, (20, 150))

                points_text = self.font_small.render(
                    f"点数: {selected_talent.points_spent}/{selected_talent.max_points}",
                    True, ORANGE
                )
                panel_surface.blit(points_text, (20, 190))

                can_upgrade = selected_talent.unlocked and selected_talent.points_spent < selected_talent.max_points
                status = "可加点" if can_upgrade else "已满级" if selected_talent.points_spent >= selected_talent.max_points else "未解锁"
                status_color = GREEN if can_upgrade else YELLOW if selected_talent.points_spent >= selected_talent.max_points else RED
                status_text = self.font_small.render(status, True, status_color)
                panel_surface.blit(status_text, (20, 230))
        else:
            if self.font_small:
                hint_text = self.font_small.render("选择一个天赋", True, GRAY)
                panel_surface.blit(hint_text, (20, 100))

        surface.blit(panel_surface, (panel_x, panel_y))

    def _render_character_stats_panel(self, surface: pygame.Surface):
        hero_type = self.get_hero_at_index(self.selected_index)
        hero_info = get_hero_info(hero_type)

        base_stats = {
            "max_health": hero_info.get("base_stats", {}).get("max_health", 1000),
            "attack_multiplier": hero_info.get("base_stats", {}).get("attack_multiplier", 1.0),
            "walk_speed": hero_info.get("base_stats", {}).get("walk_speed", 5.0),
        }

        bonuses = self.progression.get_merged_bonuses(hero_type.name)

        panel_x = SCREEN_WIDTH - 310
        panel_y = 220
        panel_width = 280
        panel_height = 400

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_color = with_alpha(DARK_GRAY, 200)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(panel_surface, ORANGE, (0, 0, panel_width, panel_height), 2, border_radius=15)

        if self.font_medium:
            title = self.font_medium.render("角色属性", True, ORANGE)
            panel_surface.blit(title, (10, 10))

        if self.font_small:
            name_text = self.font_small.render(hero_info.get('name', 'Unknown'), True, WHITE)
            panel_surface.blit(name_text, (20, 55))

            y_offset = 100
            line_spacing = 35

            health_base = base_stats["max_health"]
            health_bonus = bonuses.get("max_health_bonus", 0.0)
            health_total = int(health_base + health_bonus)
            health_color = GREEN if health_bonus > 0 else WHITE
            self._render_stat_line(panel_surface, "生命值", f"{health_total}", f"(+{int(health_bonus)})", 20, y_offset, health_color)
            y_offset += line_spacing

            atk_base = base_stats["attack_multiplier"]
            atk_bonus = bonuses.get("attack_power_percent", 0.0)
            atk_total = f"{(atk_base + atk_bonus) * 100:.0f}%"
            atk_color = ORANGE if atk_bonus > 0 else WHITE
            self._render_stat_line(panel_surface, "攻击力", atk_total, f"(+{atk_bonus * 100:.1f}%)", 20, y_offset, atk_color)
            y_offset += line_spacing

            spd_base = base_stats["walk_speed"]
            spd_bonus = bonuses.get("move_speed_bonus", 0.0)
            spd_total = f"{spd_base * (1 + spd_bonus):.1f}"
            spd_color = CYAN if spd_bonus > 0 else WHITE
            self._render_stat_line(panel_surface, "移动速度", spd_total, f"(+{spd_bonus * 100:.0f}%)", 20, y_offset, spd_color)
            y_offset += line_spacing + 15

            active_bonuses = []
            if bonuses.get("combo_damage_bonus", 0) > 0:
                active_bonuses.append(f"连击伤害 +{bonuses['combo_damage_bonus'] * 100:.0f}%")
            if bonuses.get("ultimate_damage_bonus", 0) > 0:
                active_bonuses.append(f"必杀伤害 +{bonuses['ultimate_damage_bonus'] * 100:.0f}%")
            if bonuses.get("damage_reduction", 0) > 0:
                active_bonuses.append(f"受伤减免 {bonuses['damage_reduction'] * 100:.0f}%")
            if bonuses.get("dodge_cooldown_reduction", 0) > 0:
                active_bonuses.append(f"闪避冷却 -{bonuses['dodge_cooldown_reduction'] * 100:.0f}%")

            if active_bonuses:
                active_title = self.font_small.render("天赋加成:", True, YELLOW)
                panel_surface.blit(active_title, (20, y_offset))
                y_offset += line_spacing

                for bonus in active_bonuses:
                    if y_offset + 30 > panel_height - 20:
                        break
                    bonus_text = self.font_tiny.render(f"  {bonus}", True, LIGHT_GRAY)
                    panel_surface.blit(bonus_text, (20, y_offset))
                    y_offset += 28

        surface.blit(panel_surface, (panel_x, panel_y))

    def _render_stat_line(self, surface: pygame.Surface, label: str, value: str, bonus: str, x: int, y: int, color: Tuple[int, int, int]):
        if not self.font_small or not self.font_tiny:
            return

        label_text = self.font_small.render(label, True, LIGHT_GRAY)
        value_text = self.font_small.render(value, True, color)
        bonus_text = self.font_tiny.render(bonus, True, color)

        surface.blit(label_text, (x, y))
        surface.blit(value_text, (x + 120, y))
        if bonus != "(+0)" and bonus != "(+0.0%)":
            surface.blit(bonus_text, (x + 120 + value_text.get_width() + 5, y + 5))

    def _render_menu_buttons(self, surface: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()

        for btn in self.menu_buttons:
            is_hover = btn["x"] <= mouse_pos[0] <= btn["x"] + btn["w"] and \
                       btn["y"] <= mouse_pos[1] <= btn["y"] + btn["h"]

            is_active = btn["view"] == self.current_view

            if is_active:
                color = btn["active_color"]
            elif is_hover:
                color = with_alpha(btn["color"], 220)
            else:
                color = with_alpha(DARK_GRAY, 200)

            panel_surface = pygame.Surface((btn["w"], btn["h"]), pygame.SRCALPHA)
            pygame.draw.rect(panel_surface, color, (0, 0, btn["w"], btn["h"]), border_radius=10)
            surface.blit(panel_surface, (btn["x"], btn["y"]))

            border_color = WHITE if is_active else btn["color"]
            pygame.draw.rect(surface, border_color, (btn["x"], btn["y"], btn["w"], btn["h"]), 3 if is_active else 2, border_radius=10)

            if self.font_small:
                text = self.font_small.render(btn["label"], True, WHITE)
                text_x = btn["x"] + btn["w"] // 2 - text.get_width() // 2
                text_y = btn["y"] + btn["h"] // 2 - text.get_height() // 2
                surface.blit(text, (text_x, text_y))

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
        info_panel_h = 280

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
            panel_surface.blit(special_label, (20, 160))
            panel_surface.blit(special_text, (100, 160))

            ultimate_label = self.font_small.render("必杀技:", True, ORANGE)
            ultimate_text = self.font_small.render(ultimate_name, True, WHITE)
            panel_surface.blit(ultimate_label, (20, 195))
            panel_surface.blit(ultimate_text, (100, 195))

        surface.blit(panel_surface, (info_panel_x, info_panel_y))

    def _render_character_progression_panel(self, surface: pygame.Surface):
        hero_type = self.get_hero_at_index(self.selected_index)
        prog = self.progression.get_character_progression(hero_type.name)

        panel_x = SCREEN_WIDTH - 400
        panel_y = 180
        panel_width = 320
        panel_height = 280

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_color = with_alpha(DARK_GRAY, 200)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(panel_surface, ORANGE, (0, 0, panel_width, panel_height), 2, border_radius=15)

        if self.font_medium:
            title = self.font_medium.render("角色养成", True, ORANGE)
            panel_surface.blit(title, (10, 10))

        if self.font_small:
            level_text = self.font_small.render(f"等级: {prog.level}", True, WHITE)
            panel_surface.blit(level_text, (20, 60))

            exp_text = self.font_small.render(f"经验: {prog.current_experience}/{prog.experience_to_next}", True, CYAN)
            panel_surface.blit(exp_text, (20, 95))

            tp_text = self.font_small.render(f"天赋点: {prog.available_talent_points}/{prog.total_talent_points_earned}", True, YELLOW)
            panel_surface.blit(tp_text, (20, 130))

            wins_text = self.font_small.render(f"总胜场: {prog.total_wins}", True, LIGHT_GRAY)
            panel_surface.blit(wins_text, (20, 165))

            if prog.highest_wave_reached > 0:
                wave_text = self.font_small.render(f"最高波数: {prog.highest_wave_reached}", True, PURPLE)
                panel_surface.blit(wave_text, (20, 200))

        bar_x = 20
        bar_y = 230
        bar_width = panel_width - 40
        bar_height = 20

        if prog.experience_to_next > 0:
            exp_ratio = min(1.0, prog.current_experience / prog.experience_to_next)
            fill_width = int(bar_width * exp_ratio)
            pygame.draw.rect(panel_surface, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=5)
            pygame.draw.rect(panel_surface, ORANGE, (bar_x, bar_y, fill_width, bar_height), border_radius=5)

        surface.blit(panel_surface, (panel_x, panel_y))

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
            "T: Open Talent Tree",
            "ENTER or SPACE: Confirm Selection",
            "ESCAPE: Go Back"
        ]

        start_y = SCREEN_HEIGHT - 100
        spacing = 25

        for i, hint in enumerate(hints):
            hint_text = self.font_hint.render(hint, True, GRAY)
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                start_y + i * spacing
            ))

    def _render_talents_hints(self, surface: pygame.Surface):
        if not self.font_hint:
            return

        hints = [
            "LEFT/RIGHT: Switch Branch",
            "UP/DOWN: Select Talent",
            "ENTER: Spend Talent Point",
            "R: Reset Talents (500 Gold)",
            "T or ESC: Return to Selection"
        ]

        start_y = SCREEN_HEIGHT - 100
        spacing = 25

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
