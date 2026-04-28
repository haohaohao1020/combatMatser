#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - UI系统模块
包含血条、怒气条、计时器、连击计数等UI元素
所有颜色值严格限制在 0-255 范围内
"""

import math
import pygame
from typing import Optional, Tuple

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAX_ROUNDS,
    DARK_BLUE, DARK_RED, BLUE, RED,
    DARK_GRAY, GRAY, LIGHT_GRAY, WHITE, RED, GREEN,
    PURPLE, ORANGE, YELLOW, BLACK, CYAN, PINK,
    clamp_color, safe_color, lerp_color, scale_color, with_alpha,
    lerp, clamp
)
from character import Character


# =============================================================================
# UI类
# =============================================================================
class UI:
    """UI系统管理器"""
    
    def __init__(self):
        # 字体（延迟初始化，需要pygame先初始化）
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        
        # 回合过渡效果
        self.round_transition_alpha = 0
        self.round_transition_text = ""
    
    def init_fonts(self):
        """初始化字体（必须在pygame.init()之后调用）"""
        # 使用系统默认字体，避免中文乱码问题
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
    
    # =========================================================================
    # 血条和怒气条渲染
    # =========================================================================
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
        """
        渲染血条和怒气条
        
        Args:
            surface: 渲染目标表面
            x, y: 位置
            width, height: 尺寸
            current: 当前血量
            maximum: 最大血量
            is_player1: 是否为玩家1（决定颜色）
            rage: 当前怒气
            max_rage: 最大怒气
            player_name: 玩家名字
            is_flashing: 是否闪烁（残血状态）
        """
        # ========================================
        # 血条背景和边框
        # ========================================
        border_color = DARK_BLUE if is_player1 else DARK_RED
        fill_color = BLUE if is_player1 else RED
        
        # 背景
        pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height), border_radius=5)
        # 边框
        pygame.draw.rect(surface, border_color, (x, y, width, height), 3, border_radius=5)
        
        # ========================================
        # 血条填充（带安全的渐变效果）
        # ========================================
        health_ratio = current / maximum
        fill_width = max(0, int(width * health_ratio))
        
        if fill_width > 0:
            # 使用安全的颜色渲染渐变
            self._render_gradient_bar(
                surface,
                x + 3, y + 3,
                fill_width, height - 6,
                fill_color,
                is_player1
            )
        
        # ========================================
        # 残血闪烁（安全的alpha值）
        # ========================================
        if health_ratio < 0.25:
            # 安全计算闪烁alpha
            flash_alpha = clamp_color(int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 50))
            if flash_alpha > 0 and fill_width > 0:
                flash_surface = pygame.Surface((fill_width, height - 6), pygame.SRCALPHA)
                flash_color = with_alpha(RED, flash_alpha)
                pygame.draw.rect(flash_surface, flash_color, (0, 0, fill_width, height - 6))
                surface.blit(flash_surface, (x + 3, y + 3))
        
        # ========================================
        # 怒气条
        # ========================================
        self._render_rage_bar(
            surface,
            x, y + height + 8,
            width, 12,
            rage, max_rage
        )
        
        # ========================================
        # 玩家名字
        # ========================================
        if self.font_small:
            name_text = self.font_small.render(player_name, True, WHITE)
            if is_player1:
                surface.blit(name_text, (x, y - 30))
            else:
                surface.blit(name_text, (x + width - name_text.get_width(), y - 30))
        
        # ========================================
        # 血量数字
        # ========================================
        if self.font_medium:
            health_text = self.font_medium.render(f"{current}", True, WHITE)
            if is_player1:
                surface.blit(health_text, (x + width + 10, y))
            else:
                text_width = health_text.get_width()
                surface.blit(health_text, (x - text_width - 10, y))
    
    # =========================================================================
    # 安全的渐变条渲染
    # =========================================================================
    def _render_gradient_bar(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        width: int, height: int,
        base_color: Tuple[int, ...],
        is_player1: bool
    ):
        """
        安全地渲染渐变血条
        使用安全的颜色处理，确保所有值在 0-255 范围内
        """
        # 创建渐变表面
        gradient_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 定义渐变的颜色范围（使用安全的颜色缩放）
        # 左亮右暗，而非直接乘以1.3可能超出范围
        color_light = lerp_color(base_color, WHITE, 0.3)
        color_dark = lerp_color(base_color, (0, 0, 0), 0.3)
        
        # 逐像素渲染渐变
        for i in range(width):
            t = i / width
            # 安全插值
            current_color = lerp_color(color_light, color_dark, t)
            pygame.draw.line(gradient_surface, current_color, (i, 0), (i, height))
        
        # 添加高光效果（安全的alpha）
        highlight_height = height // 3
        highlight = pygame.Surface((width, highlight_height), pygame.SRCALPHA)
        highlight_alpha = clamp_color(80)
        
        for i in range(width):
            # 安全的alpha值
            pygame.draw.line(highlight, (255, 255, 255, highlight_alpha), (i, 0), (i, highlight_height))
        
        gradient_surface.blit(highlight, (0, 0))
        
        # 绘制到目标表面
        surface.blit(gradient_surface, (x, y))
    
    # =========================================================================
    # 怒气条渲染
    # =========================================================================
    def _render_rage_bar(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        width: int, height: int,
        rage: float, max_rage: float
    ):
        """
        安全地渲染怒气条
        包含流光效果和满怒闪烁
        """
        rage_width = int(width * 0.8)
        rage_height = height
        rage_x = x + (width - rage_width) // 2
        rage_y = y
        
        # 背景
        pygame.draw.rect(surface, DARK_GRAY, (rage_x, rage_y, rage_width, rage_height), border_radius=3)
        
        # 填充
        if rage > 0:
            rage_ratio = rage / max_rage
            rage_fill = max(0, int(rage_width * rage_ratio))
            
            # 创建流光效果表面
            rage_surface = pygame.Surface((rage_fill, rage_height - 4), pygame.SRCALPHA)
            
            # 使用安全的颜色渐变（紫色到橙色）
            flow_offset = pygame.time.get_ticks() * 0.01
            
            for i in range(rage_fill):
                # 安全的流光效果
                flow = (math.sin((i + flow_offset) * 0.1) + 1) * 0.5
                # 安全插值颜色
                pixel_color = lerp_color(PURPLE, ORANGE, flow)
                # 安全提亮
                pixel_color = lerp_color(pixel_color, WHITE, 0.2)
                pygame.draw.line(rage_surface, pixel_color, (i, 0), (i, rage_height - 4))
            
            # 满怒闪烁（安全的alpha）
            if rage_ratio >= 1.0:
                flash = clamp_color(int((math.sin(pygame.time.get_ticks() * 0.02) + 1) * 50))
                if flash > 0:
                    flash_color = with_alpha(WHITE, flash)
                    pygame.draw.rect(rage_surface, flash_color, (0, 0, rage_fill, rage_height - 4))
            
            surface.blit(rage_surface, (rage_x + 2, rage_y + 2))
        
        # 边框（根据怒气状态变色）
        border_color = PURPLE if rage < max_rage else YELLOW
        pygame.draw.rect(surface, border_color, (rage_x, rage_y, rage_width, rage_height), 2, border_radius=3)
    
    # =========================================================================
    # 计时器渲染
    # =========================================================================
    def render_timer(self, surface: pygame.Surface, time_remaining: int):
        """渲染回合计时器"""
        if self.font_large:
            timer_x = SCREEN_WIDTH // 2 - 50
            
            # 背景
            pygame.draw.rect(surface, DARK_GRAY, (timer_x, 10, 100, 50), border_radius=10)
            pygame.draw.rect(surface, GRAY, (timer_x + 3, 13, 94, 44), 2, border_radius=8)
            
            # 时间文字（最后10秒变红）
            color = RED if time_remaining <= 10 else WHITE
            timer_text = self.font_large.render(f"{time_remaining}", True, color)
            surface.blit(timer_text, (
                SCREEN_WIDTH // 2 - timer_text.get_width() // 2,
                15
            ))
    
    # =========================================================================
    # 回合分数渲染
    # =========================================================================
    def render_round_score(self, surface: pygame.Surface, p1_wins: int, p2_wins: int):
        """渲染回合获胜计数（圆形指示器）"""
        if self.font_small:
            for i in range(MAX_ROUNDS):
                # 玩家1的回合指示
                x1 = 20 + i * 30
                color1 = GREEN if i < p1_wins else DARK_GRAY
                pygame.draw.circle(surface, color1, (x1 + 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x1 + 10, 85), 10, 2)
                
                # 玩家2的回合指示
                x2 = SCREEN_WIDTH - 20 - (MAX_ROUNDS - 1 - i) * 30
                color2 = GREEN if i < p2_wins else DARK_GRAY
                pygame.draw.circle(surface, color2, (x2 - 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x2 - 10, 85), 10, 2)
    
    # =========================================================================
    # 连击计数渲染
    # =========================================================================
    def render_combo(self, surface: pygame.Surface, player1: Character, player2: Character):
        """渲染连击计数"""
        if self.font_medium:
            # 玩家1的连击（显示在左侧，是玩家2造成的）
            if player2.hit_combo >= 2:
                combo_text = self.font_medium.render(
                    f"COMBO x{player2.hit_combo}", 
                    True, ORANGE
                )
                surface.blit(combo_text, (20, 120))
            
            # 玩家2的连击（显示在右侧，是玩家1造成的）
            if player1.hit_combo >= 2:
                combo_text = self.font_medium.render(
                    f"COMBO x{player1.hit_combo}", 
                    True, ORANGE
                )
                surface.blit(combo_text, (
                    SCREEN_WIDTH - combo_text.get_width() - 20, 
                    120
                ))
    
    # =========================================================================
    # 回合过渡效果
    # =========================================================================
    def render_round_transition(self, surface: pygame.Surface, text: str, alpha: int):
        """
        渲染回合过渡效果（如 "ROUND 1"、"PLAYER 1 WINS!"）
        
        Args:
            surface: 渲染目标
            text: 显示的文字
            alpha: 透明度 (0-255，安全限制)
        """
        if self.font_large and alpha > 0:
            # 安全的alpha值
            safe_alpha = clamp_color(alpha)
            
            # 创建过渡表面
            transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # 背景遮罩（安全的alpha）
            overlay_alpha = clamp_color(min(safe_alpha, 180))
            overlay_color = with_alpha(BLACK, overlay_alpha)
            transition_surface.fill(overlay_color)
            
            # 文字
            text_surface = self.font_large.render(text, True, WHITE)
            text_surface.set_alpha(safe_alpha)
            
            # 居中绘制
            transition_surface.blit(
                text_surface,
                (
                    SCREEN_WIDTH // 2 - text_surface.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text_surface.get_height() // 2
                )
            )
            
            surface.blit(transition_surface, (0, 0))


# =============================================================================
# 游戏内菜单（暂停、结算）
# =============================================================================
class InGameMenu:
    """游戏内菜单系统"""
    
    def __init__(self):
        self.font_title: Optional[pygame.font.Font] = None
        self.font_option: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None
        self.selected_index = 0
        self.options = ["RESUME", "RESTART", "BACK TO MENU"]
    
    def init_fonts(self):
        """初始化字体"""
        self.font_title = pygame.font.Font(None, 72)
        self.font_option = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 28)
    
    def handle_input(self, keys, events) -> Optional[int]:
        """
        处理菜单输入
        
        Returns:
            选中的选项索引，或None（无选择）
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0  # ESC恢复游戏
        
        return None
    
    def render_pause(self, surface: pygame.Surface):
        """渲染暂停菜单"""
        # 半透明背景（安全的alpha）
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_alpha = clamp_color(180)
        overlay.fill(with_alpha(BLACK, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        # 标题
        if self.font_title:
            title_text = self.font_title.render("PAUSED", True, WHITE)
            surface.blit(title_text, (
                SCREEN_WIDTH // 2 - title_text.get_width() // 2,
                150
            ))
        
        # 选项
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
                    # 选中指示器（三角形）
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
        """
        渲染游戏结束/结算界面
        
        Args:
            winner_name: 胜利者名字
            p1_max_combo: 玩家1最高连击
            p2_max_combo: 玩家2最高连击
            p1_total_damage: 玩家1总伤害
            p2_total_damage: 玩家2总伤害
            winner_is_p1: 胜利者是否为玩家1
        """
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_alpha = clamp_color(200)
        overlay.fill(with_alpha(BLACK, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        if self.font_title:
            # 胜利文字
            winner_color = BLUE if winner_is_p1 else RED
            win_text = self.font_title.render("WINNER!", True, winner_color)
            surface.blit(win_text, (
                SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                120
            ))
            
            # 胜利者名字
            if self.font_option:
                name_text = self.font_option.render(winner_name, True, WHITE)
                surface.blit(name_text, (
                    SCREEN_WIDTH // 2 - name_text.get_width() // 2,
                    200
                ))
        
        # 统计数据
        if self.font_small:
            start_y = 300
            spacing = 40
            
            # 玩家1数据
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
            
            # 玩家2数据
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
        
        # 提示文字
        if self.font_small:
            hint_text = self.font_small.render(
                "Press ENTER to return to menu", 
                True, GRAY
            )
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                SCREEN_HEIGHT - 80
            ))
