#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 特效系统模块
包含所有视觉特效：伤害飘字、火花、连击文字、必杀波纹、屏幕震动
所有颜色值严格限制在 0-255 范围内
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from config import (
    YELLOW, ORANGE, WHITE, RED, GREEN, CYAN,
    clamp_color, safe_color, lerp_color, with_alpha,
    lerp, SCREEN_WIDTH, SCREEN_HEIGHT
)


# =============================================================================
# 特效基类
# =============================================================================
class Effect:
    """特效基类"""
    
    def __init__(self, x: float, y: float, duration: int):
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.alive = True
    
    def update(self):
        """更新特效状态"""
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        """渲染特效"""
        pass


# =============================================================================
# 伤害数字飘字
# =============================================================================
class DamageNumber(Effect):
    """伤害数字飘字特效"""
    
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
            # 安全地计算alpha，确保在 0-255 范围内
            self.alpha = clamp_color(int(self.duration / 30 * 255))
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        
        # 选择颜色（使用安全的颜色值）
        if self.is_blocked:
            color = GREEN
        elif self.is_crit:
            color = RED
        else:
            color = WHITE
        
        # 字体大小
        size = 40 if self.is_crit else 28
        font = pygame.font.Font(None, size)
        
        # 渲染文字
        if self.is_blocked:
            text = font.render("BLOCK!", True, color)
        else:
            text = font.render(str(self.damage), True, color)
        
        # 创建透明表面进行alpha混合（安全的alpha值）
        temp_surface = pygame.Surface((100, 50), pygame.SRCALPHA)
        text_rect = text.get_rect(center=(50, 25))
        temp_surface.blit(text, text_rect)
        
        # 安全设置alpha
        temp_surface.set_alpha(clamp_color(self.alpha))
        
        # 绘制
        draw_x = int(self.x + offset_x - 25)
        draw_y = int(self.y + offset_y)
        surface.blit(temp_surface, (draw_x, draw_y))


# =============================================================================
# 攻击火花特效
# =============================================================================
class HitSpark(Effect):
    """攻击命中时的火花粒子特效"""
    
    def __init__(self, x: float, y: float, intensity: float = 1.0):
        super().__init__(x, y, int(25 * intensity))
        self.particles: List[dict] = []
        
        # 创建粒子（使用安全的颜色值）
        num_particles = int(12 * intensity)
        available_colors = [YELLOW, ORANGE, WHITE, RED]
        
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8) * intensity
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': clamp_color(int(random.uniform(3, 8) * intensity)),
                'color': random.choice(available_colors)
            })
    
    def update(self):
        super().update()
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3
            # 安全地缩小粒子
            p['size'] = max(1, int(p['size'] * 0.92))
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        
        for p in self.particles:
            size = p['size']
            if size > 0:
                # 安全的颜色和坐标
                draw_x = clamp_color(int(p['x'] + offset_x))
                draw_y = clamp_color(int(p['y'] + offset_y))
                pygame.draw.circle(surface, p['color'], (draw_x, draw_y), size)


# =============================================================================
# 连击爆炸文字
# =============================================================================
class ComboText(Effect):
    """连击计数的爆炸文字特效"""
    
    def __init__(self, x: float, y: float, combo: int):
        super().__init__(x, y, 60)
        self.combo = combo
        self.scale = 2.0
        self.alpha = 255
    
    def update(self):
        super().update()
        self.scale = lerp(self.scale, 1.0, 0.1)
        if self.duration < 20:
            # 安全的alpha计算
            self.alpha = clamp_color(int(self.duration / 20 * 255))
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive or self.combo < 3:
            return
        
        font = pygame.font.Font(None, 60)
        text = font.render(f"{self.combo} HIT!", True, ORANGE)
        
        # 安全缩放
        scaled_width = max(1, int(text.get_width() * self.scale))
        scaled_height = max(1, int(text.get_height() * self.scale))
        scaled_text = pygame.transform.scale(text, (scaled_width, scaled_height))
        
        # 使用SRCALPHA表面进行alpha混合
        temp_surface = pygame.Surface((200, 80), pygame.SRCALPHA)
        text_x = 100 - scaled_width // 2
        text_y = 40 - scaled_height // 2
        temp_surface.blit(scaled_text, (text_x, text_y))
        
        # 安全alpha
        temp_surface.set_alpha(clamp_color(self.alpha))
        
        draw_x = int(self.x + offset_x - 100)
        draw_y = int(self.y + offset_y - 40)
        surface.blit(temp_surface, (draw_x, draw_y))


# =============================================================================
# 必杀技能量波纹
# =============================================================================
class UltimateWave(Effect):
    """必杀技的全屏能量波纹特效"""
    
    def __init__(self, x: float, y: float, max_radius: float = 400):
        super().__init__(x, y, 60)
        self.radius = 0
        self.max_radius = max_radius
        self.alpha = 200
    
    def update(self):
        super().update()
        self.radius = lerp(self.radius, self.max_radius, 0.15)
        # 安全的alpha计算
        self.alpha = clamp_color(int(self.duration / 60 * 200))
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        
        # 创建全屏透明表面
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # 绘制多层波纹（使用安全的颜色和alpha）
        center_x = int(self.x + offset_x)
        center_y = int(self.y + offset_y)
        
        for i in range(3):
            r = int(self.radius - i * 30)
            if r > 0:
                # 安全的alpha值
                wave_alpha = clamp_color(int(self.alpha * (1 - i * 0.3)))
                # 安全的颜色（带alpha）
                wave_color = with_alpha(CYAN, wave_alpha)
                # 安全的线宽
                line_width = clamp_color(8 - i * 2)
                
                pygame.draw.circle(
                    temp_surface, 
                    wave_color,
                    (center_x, center_y), 
                    r, 
                    width=line_width
                )
        
        surface.blit(temp_surface, (0, 0))


# =============================================================================
# 屏幕震动管理
# =============================================================================
class ScreenShake:
    """屏幕震动管理器"""
    
    def __init__(self):
        self.intensity = 0.0
        self.duration = 0
        self.offset_x = 0.0
        self.offset_y = 0.0
    
    def trigger(self, intensity: float, duration: int):
        """触发屏幕震动
        
        Args:
            intensity: 震动强度（像素）
            duration: 持续帧数
        """
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)
    
    def update(self):
        """更新震动状态"""
        if self.duration > 0:
            # 生成随机偏移
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            
            self.duration -= 1
            # 震动强度衰减
            self.intensity *= 0.9
        else:
            self.offset_x = 0.0
            self.offset_y = 0.0
    
    def get_offset(self) -> Tuple[float, float]:
        """获取当前震动偏移
        
        Returns:
            (x偏移, y偏移)
        """
        return (self.offset_x, self.offset_y)


# =============================================================================
# 特效管理器
# =============================================================================
class EffectManager:
    """特效管理器，统一管理所有特效"""
    
    def __init__(self):
        self.effects: List[Effect] = []
    
    def add(self, effect: Effect):
        """添加特效"""
        self.effects.append(effect)
    
    def update(self):
        """更新所有特效"""
        for effect in self.effects:
            effect.update()
        # 移除已结束的特效
        self.effects = [e for e in self.effects if e.alive]
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        """渲染所有特效"""
        for effect in self.effects:
            effect.render(surface, offset_x, offset_y)
    
    def clear(self):
        """清除所有特效"""
        self.effects.clear()
