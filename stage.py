#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 场景渲染模块
纯代码绘制场景背景和地面
所有颜色值严格限制在 0-255 范围内
"""

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y,
    DARK_GRAY, GRAY, LIGHT_GRAY,
    clamp_color, lerp, safe_color, clamp
)


# =============================================================================
# 场景类
# =============================================================================
class Stage:
    """游戏场景 - 纯代码绘制"""
    
    def __init__(self):
        self.grid_offset = 0.0
    
    def update(self):
        """更新场景动画"""
        self.grid_offset += 0.5
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        """
        渲染场景
        
        Args:
            surface: 渲染目标表面
            offset_x: X偏移（用于屏幕震动）
            offset_y: Y偏移（用于屏幕震动）
        """
        # ========================================
        # 背景渐变（安全的颜色处理）
        # ========================================
        self._render_background(surface)
        
        # ========================================
        # 远景装饰
        # ========================================
        self._render_background_decorations(surface)
        
        # ========================================
        # 地面
        # ========================================
        self._render_ground(surface, offset_x, offset_y)
    
    # =========================================================================
    # 背景渐变
    # =========================================================================
    def _render_background(self, surface: pygame.Surface):
        """安全地渲染背景渐变"""
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            # 安全的颜色计算，确保在 0-255 范围内
            r = clamp_color(int(lerp(20, 60, t)))
            g = clamp_color(int(lerp(30, 80, t)))
            b = clamp_color(int(lerp(50, 120, t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # =========================================================================
    # 远景装饰
    # =========================================================================
    def _render_background_decorations(self, surface: pygame.Surface):
        """安全地渲染远景装饰"""
        # 装饰颜色（安全）
        decor_color = safe_color((40, 70, 100))
        
        for i in range(5):
            # 滚动动画
            x = (i * 300 + self.grid_offset * 0.3) % (SCREEN_WIDTH + 200) - 100
            # 安全的坐标
            draw_x = clamp_color(int(x))
            pygame.draw.circle(surface, decor_color, (draw_x, 200), 80)
    
    # =========================================================================
    # 地面渲染
    # =========================================================================
    def _render_ground(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        """
        安全地渲染地面
        
        Args:
            surface: 渲染目标
            offset_x: X偏移
            offset_y: Y偏移
        """
        # 安全计算地面位置
        ground_y = int(clamp(GROUND_Y + offset_y, 0, SCREEN_HEIGHT))
        
        # 地面主体
        pygame.draw.rect(
            surface, DARK_GRAY,
            (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y)
        )
        
        # 地面网格（垂直）
        for i in range(int(SCREEN_WIDTH / 40) + 2):
            x = int((i * 40 - self.grid_offset + offset_x) % (SCREEN_WIDTH + 40))
            pygame.draw.line(surface, GRAY, (x, ground_y), (x, SCREEN_HEIGHT), 1)
        
        # 地面网格（水平）
        for i in range(int((SCREEN_HEIGHT - GROUND_Y) / 30) + 2):
            y = int(ground_y + i * 30)
            if y < SCREEN_HEIGHT:
                pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y), 1)
        
        # 地面高亮线
        pygame.draw.line(surface, LIGHT_GRAY, (0, ground_y), (SCREEN_WIDTH, ground_y), 3)
