#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 配置模块
包含所有游戏常量、颜色定义和工具函数
"""

import math
from enum import Enum, auto
from typing import Tuple

# =============================================================================
# 游戏核心常量
# =============================================================================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 650
FPS = 60
GROUND_Y = 520
ROUND_TIME = 99
MAX_ROUNDS = 3

# 角色物理参数
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 100
WALK_SPEED = 5
RUN_SPEED = 9
FRICTION = 0.85
GRAVITY = 0.8
MAX_FALL_SPEED = 18
JUMP_FORCE = -15
DOUBLE_JUMP_FORCE = -12
BOUNDARY_MARGIN = 30

# 角色属性
MAX_HEALTH = 1000
MAX_RAGE = 100

# 伤害值
LIGHT_ATTACK_DAMAGE = 80
HEAVY_ATTACK_DAMAGE = 180
LOW_ATTACK_DAMAGE = 100
ULTIMATE_DAMAGE = 350

# 怒气获取
RAGE_ON_HIT = 10
RAGE_ON_GUARD = 5
RAGE_ON_HIT_BY = 8
RAGE_PERFECT_BLOCK = 15

# 连击保护
COMBO_PROTECTION_START = 0.4
COMBO_PROTECTION_PER_HIT = 0.05

# =============================================================================
# 颜色定义 (所有值严格限制在 0-255 范围内)
# =============================================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
DARK_RED = (180, 30, 30)
BLUE = (50, 100, 255)
DARK_BLUE = (30, 60, 180)
GREEN = (50, 255, 80)
YELLOW = (255, 220, 0)
ORANGE = (255, 140, 0)
PURPLE = (180, 50, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (180, 180, 180)
CYAN = (0, 200, 255)
PINK = (255, 100, 180)

# 玩家颜色
PLAYER1_COLOR = BLUE
PLAYER1_COLOR_DARK = DARK_BLUE
PLAYER1_ACCENT = CYAN

PLAYER2_COLOR = RED
PLAYER2_COLOR_DARK = DARK_RED
PLAYER2_ACCENT = PINK

# =============================================================================
# 枚举定义
# =============================================================================
class GameState(Enum):
    MENU = auto()
    MODE_SELECT = auto()
    DIFFICULTY_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    ROUND_END = auto()
    GAME_OVER = auto()

class CharacterState(Enum):
    IDLE = auto()
    WALK = auto()
    RUN = auto()
    JUMP = auto()
    CROUCH = auto()
    ATTACK_LIGHT = auto()
    ATTACK_HEAVY = auto()
    ATTACK_LOW = auto()
    BLOCK = auto()
    HIT = auto()
    LAUNCHED = auto()
    GROUNDED = auto()
    DODGE = auto()
    ULTIMATE = auto()

class AttackType(Enum):
    LIGHT = auto()
    HEAVY = auto()
    LOW = auto()
    ULTIMATE = auto()

# =============================================================================
# 安全的颜色处理工具函数
# =============================================================================
def clamp_color(value: int) -> int:
    """将颜色值限制在 0-255 范围内"""
    return max(0, min(255, int(value)))

def safe_color(color: Tuple[int, ...]) -> Tuple[int, ...]:
    """确保颜色值的每个分量都在 0-255 范围内"""
    return tuple(clamp_color(c) for c in color)

def lerp_color(color1: Tuple[int, ...], color2: Tuple[int, ...], t: float) -> Tuple[int, ...]:
    """安全的颜色插值，确保结果在 0-255 范围内"""
    t = max(0.0, min(1.0, t))
    return tuple(clamp_color(color1[i] + (color2[i] - color1[i]) * t) for i in range(len(color1)))

def scale_color(color: Tuple[int, ...], scale: float) -> Tuple[int, ...]:
    """安全的颜色缩放，确保结果在 0-255 范围内"""
    return tuple(clamp_color(c * scale) for c in color)

def add_color(color1: Tuple[int, ...], color2: Tuple[int, ...]) -> Tuple[int, ...]:
    """安全的颜色相加，确保结果在 0-255 范围内"""
    return tuple(clamp_color(color1[i] + color2[i]) for i in range(len(color1)))

def with_alpha(color: Tuple[int, ...], alpha: int) -> Tuple[int, ...]:
    """为颜色添加alpha通道，确保alpha在 0-255 范围内"""
    alpha = clamp_color(alpha)
    if len(color) == 3:
        return (color[0], color[1], color[2], alpha)
    elif len(color) == 4:
        return (color[0], color[1], color[2], alpha)
    return color

# =============================================================================
# 通用工具函数
# =============================================================================
def lerp(a: float, b: float, t: float) -> float:
    """线性插值"""
    return a + (b - a) * t

def clamp(value: float, min_value: float, max_value: float) -> float:
    """将值限制在范围内"""
    return max(min_value, min(max_value, value))

def get_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """计算两点距离"""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
