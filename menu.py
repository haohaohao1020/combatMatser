#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 主菜单模块
包含主菜单、模式选择、难度选择
所有颜色值严格限制在 0-255 范围内
"""

import math
import pygame
from typing import Optional

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BLACK, WHITE, GRAY, DARK_GRAY,
    CYAN, YELLOW, LIGHT_GRAY,
    clamp_color, safe_color, lerp_color, with_alpha,
    lerp
)


# =============================================================================
# 主菜单类
# =============================================================================
class MainMenu:
    """主菜单系统"""
    
    def __init__(self):
        # 字体（延迟初始化）
        self.font_title: Optional[pygame.font.Font] = None
        self.font_option: Optional[pygame.font.Font] = None
        self.font_hint: Optional[pygame.font.Font] = None
        
        # 菜单状态
        self.selected_index = 0
        self.options = []
        self.menu_type = "main"
        self.animation_offset = 0
    
    def init_fonts(self):
        """初始化字体"""
        self.font_title = pygame.font.Font(None, 100)
        self.font_option = pygame.font.Font(None, 48)
        self.font_hint = pygame.font.Font(None, 28)
    
    def set_menu(self, menu_type: str):
        """
        设置菜单类型
        
        Args:
            menu_type: "main", "mode", 或 "difficulty"
        """
        self.menu_type = menu_type
        self.selected_index = 0
        
        if menu_type == "main":
            self.options = ["START GAME", "QUIT"]
        elif menu_type == "mode":
            self.options = ["PLAYER VS PLAYER", "PLAYER VS CPU", "BACK"]
        elif menu_type == "difficulty":
            self.options = ["EASY", "HARD", "BACK"]
    
    def update(self):
        """更新菜单动画"""
        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.003) * 10
    
    def handle_input(self, keys, events) -> Optional[int]:
        """
        处理菜单输入
        
        Returns:
            选中的选项索引，或None
        """
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
        """渲染菜单"""
        # ========================================
        # 背景 - 渐变色（安全的颜色处理）
        # ========================================
        self._render_background(surface)
        
        # ========================================
        # 装饰动画
        # ========================================
        self._render_decorations(surface)
        
        # ========================================
        # 标题
        # ========================================
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
        
        # ========================================
        # 选项
        # ========================================
        if self.font_option:
            self._render_options(surface)
        
        # ========================================
        # 操作提示
        # ========================================
        if self.font_hint:
            hint_text = self.font_hint.render(
                "UP/DOWN or W/S to select, ENTER to confirm",
                True, GRAY
            )
            surface.blit(hint_text, (
                SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                SCREEN_HEIGHT - 60
            ))
    
    # =========================================================================
    # 背景渲染
    # =========================================================================
    def _render_background(self, surface: pygame.Surface):
        """安全地渲染渐变背景"""
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            # 安全的颜色插值
            r = clamp_color(int(lerp(10, 40, t)))
            g = clamp_color(int(lerp(20, 60, t)))
            b = clamp_color(int(lerp(40, 100, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # =========================================================================
    # 装饰动画
    # =========================================================================
    def _render_decorations(self, surface: pygame.Surface):
        """安全地渲染装饰动画"""
        for i in range(8):
            x = int(math.sin(pygame.time.get_ticks() * 0.001 + i) * 200 + SCREEN_WIDTH // 2)
            # 安全的颜色
            decor_color = safe_color((30, 60, 120))
            pygame.draw.circle(
                surface, decor_color,
                (x, 300 + i * 50),
                50 + i * 10
            )
    
    # =========================================================================
    # 主标题渲染（带动画光晕）
    # =========================================================================
    def _render_main_title(self, surface: pygame.Surface):
        """渲染主标题 - "COMBAT MASTER" 带光晕效果"""
        if not self.font_title:
            return
        
        title_text = self.font_title.render("COMBAT MASTER", True, CYAN)
        title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
        title_y = 100 + self.animation_offset
        
        # 标题光晕（安全的颜色和alpha）
        glow_surface = pygame.Surface(
            (title_text.get_width() + 40, title_text.get_height() + 40),
            pygame.SRCALPHA
        )
        
        for i in range(5):
            # 安全的alpha值
            alpha = clamp_color(50 - i * 10)
            # 安全的颜色
            glow_color = with_alpha(CYAN, alpha)
            # 安全的尺寸
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
    
    # =========================================================================
    # 选项渲染
    # =========================================================================
    def _render_options(self, surface: pygame.Surface):
        """渲染菜单选项"""
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
