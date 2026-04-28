#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 横版双人格斗游戏
支持双人对战和AI对战（简单/困难难度）
"""

import pygame
import sys
import math
import random
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Tuple

# =============================================================================
# 游戏常量配置
# =============================================================================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 650
FPS = 60
GROUND_Y = 520
ROUND_TIME = 99
MAX_ROUNDS = 3

# 颜色定义
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

# 游戏状态
class GameState(Enum):
    MENU = auto()
    MODE_SELECT = auto()
    DIFFICULTY_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    ROUND_END = auto()
    GAME_OVER = auto()

# 角色状态
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

# 攻击类型
class AttackType(Enum):
    LIGHT = auto()
    HEAVY = auto()
    LOW = auto()
    ULTIMATE = auto()

# =============================================================================
# 工具函数
# =============================================================================
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))

def get_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

# =============================================================================
# 攻击数据类
# =============================================================================
@dataclass
class AttackData:
    attack_type: AttackType
    damage: int
    hitbox_x: int
    hitbox_y: int
    hitbox_w: int
    hitbox_h: int
    startup_frames: int
    active_frames: int
    recovery_frames: int
    hitstun: int
    knockback_x: float
    knockback_y: float
    is_high: bool = True
    can_block: bool = True
    guard_break: bool = False

# =============================================================================
# 特效基类
# =============================================================================
class Effect:
    def __init__(self, x: float, y: float, duration: int):
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.alive = True
    
    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        pass

# 伤害数字飘字
class DamageNumber(Effect):
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
            self.alpha = int(self.duration / 30 * 255)
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        temp_surface = pygame.Surface((100, 50), pygame.SRCALPHA)
        color = GREEN if self.is_blocked else (RED if self.is_crit else WHITE)
        size = 40 if self.is_crit else 28
        font = pygame.font.Font(None, size)
        text = font.render(str(self.damage), True, color)
        if self.is_blocked:
            text = font.render("BLOCK!", True, color)
        temp_surface.blit(text, (0, 0))
        temp_surface.set_alpha(self.alpha)
        surface.blit(temp_surface, (self.x + offset_x - 25, self.y + offset_y))

# 攻击火花特效
class HitSpark(Effect):
    def __init__(self, x: float, y: float, intensity: float = 1.0):
        super().__init__(x, y, int(25 * intensity))
        self.particles = []
        num_particles = int(12 * intensity)
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8) * intensity
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(3, 8) * intensity,
                'color': random.choice([YELLOW, ORANGE, WHITE, RED])
            })
    
    def update(self):
        super().update()
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.3
            p['size'] *= 0.92
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        for p in self.particles:
            size = int(p['size'])
            if size > 0:
                pygame.draw.circle(surface, p['color'], 
                    (int(p['x'] + offset_x), int(p['y'] + offset_y)), size)

# 连击爆炸文字
class ComboText(Effect):
    def __init__(self, x: float, y: float, combo: int):
        super().__init__(x, y, 60)
        self.combo = combo
        self.scale = 2.0
        self.alpha = 255
    
    def update(self):
        super().update()
        self.scale = lerp(self.scale, 1.0, 0.1)
        if self.duration < 20:
            self.alpha = int(self.duration / 20 * 255)
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive or self.combo < 3:
            return
        temp_surface = pygame.Surface((200, 80), pygame.SRCALPHA)
        font = pygame.font.Font(None, 60)
        text = font.render(f"{self.combo} HIT!", True, ORANGE)
        scaled_size = (int(text.get_width() * self.scale), int(text.get_height() * self.scale))
        scaled_text = pygame.transform.scale(text, scaled_size)
        temp_surface.blit(scaled_text, (100 - scaled_size[0] // 2, 40 - scaled_size[1] // 2))
        temp_surface.set_alpha(self.alpha)
        surface.blit(temp_surface, (self.x + offset_x - 100, self.y + offset_y - 40))

# 必杀技能量波纹
class UltimateWave(Effect):
    def __init__(self, x: float, y: float, max_radius: float = 400):
        super().__init__(x, y, 60)
        self.radius = 0
        self.max_radius = max_radius
        self.alpha = 200
    
    def update(self):
        super().update()
        self.radius = lerp(self.radius, self.max_radius, 0.15)
        self.alpha = int(self.duration / 60 * 200)
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        if not self.alive:
            return
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(3):
            r = int(self.radius - i * 30)
            if r > 0:
                pygame.draw.circle(temp_surface, (*CYAN, int(self.alpha * (1 - i * 0.3))),
                    (int(self.x + offset_x), int(self.y + offset_y)), r, width=8 - i * 2)
        surface.blit(temp_surface, (0, 0))

# =============================================================================
# 屏幕震动管理
# =============================================================================
class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0
    
    def trigger(self, intensity: float, duration: int):
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)
    
    def update(self):
        if self.duration > 0:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.duration -= 1
            self.intensity *= 0.9
        else:
            self.offset_x = 0
            self.offset_y = 0
    
    def get_offset(self) -> Tuple[float, float]:
        return (self.offset_x, self.offset_y)

# =============================================================================
# 角色类
# =============================================================================
class Character:
    def __init__(self, x: float, y: float, is_player1: bool, is_ai: bool = False, difficulty: str = "normal"):
        # 位置和物理
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        # 玩家标识
        self.is_player1 = is_player1
        self.is_ai = is_ai
        self.difficulty = difficulty
        self.facing = 1 if is_player1 else -1
        
        # 状态
        self.state = CharacterState.IDLE
        self.previous_state = CharacterState.IDLE
        
        # 属性
        self.max_health = 1000
        self.health = self.max_health
        self.max_rage = 100
        self.rage = 0
        
        # 跳跃
        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = True
        
        # 攻击
        self.current_attack: Optional[AttackData] = None
        self.attack_timer = 0
        self.has_hit = False
        self.is_attacking = False
        
        # 受击
        self.hitstun = 0
        self.is_launched = False
        self.is_grounded_hit = False
        self.grounded_timer = 0
        self.invincible_timer = 0
        
        # 格挡
        self.is_blocking = False
        self.block_high = True
        self.perfect_block_window = 0
        
        # 闪避
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.dodge_direction = 0
        
        # 必杀
        self.ultimate_timer = 0
        self.is_ultimate = False
        
        # 动画帧
        self.anim_frame = 0
        self.anim_timer = 0
        
        # 连击
        self.hit_combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.total_damage_dealt = 0
        
        # 受击闪烁
        self.hit_flash_timer = 0
        self.hit_flash_color = None
        
        # 渲染颜色
        self.body_color = BLUE if is_player1 else RED
        self.body_color_dark = DARK_BLUE if is_player1 else DARK_RED
        self.accent_color = CYAN if is_player1 else PINK
        
        # AI参数
        self.ai_timer = 0
        self.ai_action = "idle"
        self.ai_action_timer = 0
        self.ai_attack_cooldown = 0
        
        # 怒气获取加速
        self.rage_multiplier = 1.0
    
    # =========================================================================
    # 攻击数据定义
    # =========================================================================
    def get_light_attack(self) -> AttackData:
        return AttackData(
            attack_type=AttackType.LIGHT,
            damage=80,
            hitbox_x=20,
            hitbox_y=10,
            hitbox_w=60,
            hitbox_h=70,
            startup_frames=8,
            active_frames=6,
            recovery_frames=12,
            hitstun=20,
            knockback_x=3,
            knockback_y=0,
            is_high=True,
            can_block=True
        )
    
    def get_heavy_attack(self) -> AttackData:
        return AttackData(
            attack_type=AttackType.HEAVY,
            damage=180,
            hitbox_x=10,
            hitbox_y=0,
            hitbox_w=80,
            hitbox_h=90,
            startup_frames=20,
            active_frames=10,
            recovery_frames=25,
            hitstun=35,
            knockback_x=8,
            knockback_y=-12,
            is_high=True,
            can_block=True,
            guard_break=True
        )
    
    def get_low_attack(self) -> AttackData:
        return AttackData(
            attack_type=AttackType.LOW,
            damage=100,
            hitbox_x=15,
            hitbox_y=50,
            hitbox_w=70,
            hitbox_h=40,
            startup_frames=12,
            active_frames=8,
            recovery_frames=18,
            hitstun=25,
            knockback_x=5,
            knockback_y=-2,
            is_high=False,
            can_block=False
        )
    
    def get_ultimate_attack(self) -> AttackData:
        return AttackData(
            attack_type=AttackType.ULTIMATE,
            damage=350,
            hitbox_x=-50,
            hitbox_y=-50,
            hitbox_w=200,
            hitbox_h=150,
            startup_frames=15,
            active_frames=30,
            recovery_frames=40,
            hitstun=50,
            knockback_x=15,
            knockback_y=-18,
            is_high=True,
            can_block=False
        )
    
    # =========================================================================
    # 输入处理
    # =========================================================================
    def handle_input(self, keys, opponent):
        if self.is_ai:
            self.handle_ai(opponent)
            return
        
        # 受击硬直中无法操作
        if self.hitstun > 0 or self.grounded_timer > 0:
            return
        
        # 闪避中无法操作
        if self.dodge_timer > 0:
            return
        
        # 攻击中部分状态可取消
        if self.is_attacking and self.attack_timer > 0:
            return
        
        # 必杀中
        if self.is_ultimate:
            return
        
        # 重置移动输入
        move_input = 0
        self.is_blocking = False
        
        # 玩家1按键
        if self.is_player1:
            # 移动
            if keys[pygame.K_a]:
                move_input = -1
            if keys[pygame.K_d]:
                move_input = 1
            # 跳跃
            if keys[pygame.K_w] and self.jump_count < self.max_jumps:
                self.jump()
            # 下蹲
            if keys[pygame.K_s]:
                self.state = CharacterState.CROUCH
                self.block_high = False
            # 攻击
            if keys[pygame.K_j]:
                self.start_attack(self.get_light_attack())
            if keys[pygame.K_k]:
                self.start_attack(self.get_heavy_attack())
            if keys[pygame.K_l]:
                if not self.is_grounded:
                    pass  # 空中不能格挡
                else:
                    self.is_blocking = True
                    self.state = CharacterState.BLOCK
                    if keys[pygame.K_s]:
                        self.block_high = False
                    else:
                        self.block_high = True
            # 必杀
            if keys[pygame.K_SPACE] and self.rage >= self.max_rage:
                self.start_ultimate()
            # 闪避
            if keys[pygame.K_LSHIFT] and self.dodge_cooldown <= 0:
                dodge_dir = -self.facing if move_input == 0 else move_input
                self.start_dodge(dodge_dir)
        # 玩家2按键
        else:
            # 移动
            if keys[pygame.K_LEFT]:
                move_input = -1
            if keys[pygame.K_RIGHT]:
                move_input = 1
            # 跳跃
            if keys[pygame.K_UP] and self.jump_count < self.max_jumps:
                self.jump()
            # 下蹲
            if keys[pygame.K_DOWN]:
                self.state = CharacterState.CROUCH
                self.block_high = False
            # 攻击
            if keys[pygame.K_KP1] or keys[pygame.K_1]:
                self.start_attack(self.get_light_attack())
            if keys[pygame.K_KP2] or keys[pygame.K_2]:
                self.start_attack(self.get_heavy_attack())
            if keys[pygame.K_KP3] or keys[pygame.K_3]:
                if not self.is_grounded:
                    pass
                else:
                    self.is_blocking = True
                    self.state = CharacterState.BLOCK
                    if keys[pygame.K_DOWN]:
                        self.block_high = False
                    else:
                        self.block_high = True
            # 必杀
            if keys[pygame.K_RETURN] and self.rage >= self.max_rage:
                self.start_ultimate()
            # 闪避
            if keys[pygame.K_RSHIFT] and self.dodge_cooldown <= 0:
                dodge_dir = -self.facing if move_input == 0 else move_input
                self.start_dodge(dodge_dir)
        
        # 处理移动
        if not self.is_blocking and not self.is_attacking:
            if move_input != 0:
                self.vel_x = move_input * WALK_SPEED
                if self.state != CharacterState.JUMP and self.is_grounded:
                    self.state = CharacterState.WALK
            else:
                if self.is_grounded and self.state == CharacterState.WALK:
                    self.state = CharacterState.IDLE
    
    # =========================================================================
    # AI逻辑
    # =========================================================================
    def handle_ai(self, opponent):
        if self.hitstun > 0 or self.grounded_timer > 0:
            return
        if self.dodge_timer > 0:
            return
        if self.is_attacking:
            return
        if self.is_ultimate:
            return
        
        self.ai_timer += 1
        dist_x = opponent.x - self.x
        abs_dist_x = abs(dist_x)
        target_facing = 1 if dist_x > 0 else -1
        self.facing = target_facing
        
        # 难度参数
        if self.difficulty == "easy":
            reaction_time = 30
            block_chance = 0.2
            dodge_chance = 0.1
            attack_chance = 0.02
            combo_chance = 0.3
        else:  # hard
            reaction_time = 8
            block_chance = 0.6
            dodge_chance = 0.3
            attack_chance = 0.05
            combo_chance = 0.7
        
        # 怒气满必放必杀
        if self.rage >= self.max_rage and self.ai_timer % 10 == 0:
            self.start_ultimate()
            return
        
        # 对手攻击时的反应
        if opponent.is_attacking and opponent.current_attack:
            attack = opponent.current_attack
            in_range = abs_dist_x < (attack.hitbox_w + self.width)
            
            if in_range and self.ai_timer % reaction_time == 0:
                # 上段攻击可以下蹲躲避
                if attack.is_high and random.random() < 0.3:
                    self.state = CharacterState.CROUCH
                    self.block_high = False
                    return
                # 格挡
                if random.random() < block_chance and self.is_grounded:
                    self.is_blocking = True
                    self.state = CharacterState.BLOCK
                    self.perfect_block_window = 12  # 困难AI更容易完美格挡
                    return
                # 闪避
                if random.random() < dodge_chance and self.dodge_cooldown <= 0:
                    self.start_dodge(self.facing * -1)
                    return
        
        # 移动逻辑 - 保持最佳攻击距离
        ideal_range = 80
        move_toward = False
        move_away = False
        
        if abs_dist_x < ideal_range - 20:
            move_away = True
        elif abs_dist_x > ideal_range + 40:
            move_toward = True
        
        if move_toward:
            self.vel_x = target_facing * WALK_SPEED
            if self.is_grounded:
                self.state = CharacterState.WALK
        elif move_away:
            self.vel_x = target_facing * -WALK_SPEED * 0.7
            if self.is_grounded:
                self.state = CharacterState.WALK
        else:
            if self.is_grounded and self.state == CharacterState.WALK:
                self.state = CharacterState.IDLE
        
        # 攻击逻辑
        attack_range = 100
        if abs_dist_x < attack_range and self.is_grounded:
            self.ai_attack_cooldown -= 1
            
            if self.ai_attack_cooldown <= 0:
                roll = random.random()
                
                if roll < attack_chance * 0.6:
                    # 轻攻击连段
                    self.start_attack(self.get_light_attack())
                    self.ai_attack_cooldown = 40
                    
                    # 可能接连招
                    if random.random() < combo_chance:
                        pass  # 下帧检测继续
                elif roll < attack_chance * 0.85:
                    # 重攻击
                    self.start_attack(self.get_heavy_attack())
                    self.ai_attack_cooldown = 60
                elif roll < attack_chance:
                    # 下段攻击
                    self.start_attack(self.get_low_attack())
                    self.ai_attack_cooldown = 50
        
        # 跳跃压制
        if self.difficulty == "hard":
            if self.is_grounded and abs_dist_x < 200 and random.random() < 0.005:
                self.jump()
    
    # =========================================================================
    # 动作方法
    # =========================================================================
    def jump(self):
        if self.jump_count >= self.max_jumps:
            return
        
        jump_force = JUMP_FORCE if self.jump_count == 0 else DOUBLE_JUMP_FORCE
        self.vel_y = jump_force
        self.jump_count += 1
        self.is_grounded = False
        self.state = CharacterState.JUMP
    
    def start_attack(self, attack_data: AttackData):
        if self.is_attacking or self.hitstun > 0:
            return
        
        self.current_attack = attack_data
        self.attack_timer = attack_data.startup_frames + attack_data.active_frames + attack_data.recovery_frames
        self.is_attacking = True
        self.has_hit = False
        
        if attack_data.attack_type == AttackType.LIGHT:
            self.state = CharacterState.ATTACK_LIGHT
        elif attack_data.attack_type == AttackType.HEAVY:
            self.state = CharacterState.ATTACK_HEAVY
        elif attack_data.attack_type == AttackType.LOW:
            self.state = CharacterState.ATTACK_LOW
        
        # 停止移动
        self.vel_x *= 0.3
    
    def start_dodge(self, direction: int):
        if self.dodge_cooldown > 0 or not self.is_grounded:
            return
        
        self.dodge_timer = 25
        self.dodge_cooldown = 60
        self.dodge_direction = direction
        self.state = CharacterState.DODGE
        self.invincible_timer = 25
        self.vel_x = direction * 12
    
    def start_ultimate(self):
        if self.rage < self.max_rage or self.is_ultimate:
            return
        
        self.rage = 0
        self.is_ultimate = True
        self.ultimate_timer = 90
        self.state = CharacterState.ULTIMATE
        self.current_attack = self.get_ultimate_attack()
        self.attack_timer = self.ultimate_timer
        self.has_hit = False
    
    # =========================================================================
    # 攻击判定
    # =========================================================================
    def get_attack_hitbox(self) -> Optional[pygame.Rect]:
        if not self.current_attack or not self.is_attacking:
            return None
        
        attack = self.current_attack
        total_frames = attack.startup_frames + attack.active_frames + attack.recovery_frames
        current_frame = total_frames - self.attack_timer
        
        # 检查是否在活跃帧
        if current_frame < attack.startup_frames or current_frame >= attack.startup_frames + attack.active_frames:
            return None
        
        # 计算碰撞盒
        if self.facing > 0:
            hb_x = self.x + self.width / 2 + attack.hitbox_x
        else:
            hb_x = self.x + self.width / 2 - attack.hitbox_x - attack.hitbox_w
        
        hb_y = self.y + attack.hitbox_y
        return pygame.Rect(hb_x, hb_y, attack.hitbox_w, attack.hitbox_h)
    
    def get_defense_hitbox(self) -> pygame.Rect:
        if self.state == CharacterState.CROUCH:
            return pygame.Rect(self.x, self.y + 40, self.width, self.height - 40)
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_attack_hit(self, opponent, effects_list: List[Effect], screen_shake: ScreenShake):
        if not self.current_attack or self.has_hit or not self.is_attacking:
            return
        
        attack_hitbox = self.get_attack_hitbox()
        if not attack_hitbox:
            return
        
        defense_hitbox = opponent.get_defense_hitbox()
        
        if not attack_hitbox.colliderect(defense_hitbox):
            return
        
        attack = self.current_attack
        
        # 检查对手无敌
        if opponent.invincible_timer > 0:
            return
        
        # 检查攻击类型与防守姿态
        is_blocked = False
        is_perfect_block = False
        
        if opponent.is_blocking and attack.can_block:
            # 下段攻击无法被站立格挡
            if not attack.is_high and opponent.block_high:
                pass  # 攻击命中
            # 检查格挡方向
            elif (opponent.facing * -1) == self.facing:
                # 完美格挡判定
                if opponent.perfect_block_window > 0:
                    is_perfect_block = True
                is_blocked = True
        
        # 命中处理
        if is_blocked:
            # 格挡减伤
            if is_perfect_block:
                # 完美格挡 - 弹反
                opponent.hitstun = 20
                opponent.vel_x = self.facing * -2
                opponent.perfect_block_window = 0
                opponent.is_blocking = False
                
                # 特效
                effects_list.append(HitSpark(opponent.x + opponent.width / 2, opponent.y + opponent.height / 2, 1.5))
                screen_shake.trigger(8, 10)
                
                # 怒气
                opponent.rage = min(opponent.max_rage, opponent.rage + 15)
            else:
                # 普通格挡
                if opponent.block_high:
                    # 站立格挡 - 减伤80%
                    reduced_damage = int(attack.damage * 0.2)
                    opponent.health = max(0, opponent.health - reduced_damage)
                    opponent.hitstun = 5
                    effects_list.append(DamageNumber(opponent.x + opponent.width / 2, opponent.y, reduced_damage, is_blocked=True))
                else:
                    # 下蹲格挡 - 减伤100%
                    effects_list.append(DamageNumber(opponent.x + opponent.width / 2, opponent.y, 0, is_blocked=True))
                
                # 格挡特效
                effects_list.append(HitSpark(attack_hitbox.centerx, attack_hitbox.centery, 0.5))
                
                # 怒气
                self.rage = min(self.max_rage, self.rage + 5)
                opponent.rage = min(opponent.max_rage, opponent.rage + 8)
            
            # 破防检查
            if attack.guard_break and not is_perfect_block:
                is_blocked = False
        
        if not is_blocked:
            # 计算连击保护
            combo_multiplier = max(0.4, 1.0 - opponent.hit_combo * 0.05)
            final_damage = int(attack.damage * combo_multiplier)
            
            # 应用伤害
            opponent.health = max(0, opponent.health - final_damage)
            opponent.hit_combo += 1
            opponent.combo_timer = 120
            if opponent.hit_combo > opponent.max_combo:
                opponent.max_combo = opponent.hit_combo
            
            # 统计伤害
            self.total_damage_dealt += final_damage
            
            # 受击状态
            opponent.hitstun = attack.hitstun
            opponent.vel_x = self.facing * attack.knockback_x
            opponent.vel_y = attack.knockback_y
            
            # 浮空
            if attack.knockback_y < -5:
                opponent.is_launched = True
                opponent.jump_count = opponent.max_jumps
            
            # 受击特效
            opponent.hit_flash_timer = 8
            opponent.hit_flash_color = WHITE
            effects_list.append(DamageNumber(opponent.x + opponent.width / 2, opponent.y, final_damage, is_crit=(attack.attack_type == AttackType.HEAVY)))
            effects_list.append(HitSpark(attack_hitbox.centerx, attack_hitbox.centery, 1.0 if attack.attack_type == AttackType.LIGHT else 2.0))
            
            # 连击显示
            if opponent.hit_combo == 3 or opponent.hit_combo == 5 or opponent.hit_combo == 10:
                effects_list.append(ComboText(opponent.x + opponent.width / 2, opponent.y - 30, opponent.hit_combo))
            
            # 屏幕震动
            shake_intensity = 5 if attack.attack_type == AttackType.LIGHT else 12 if attack.attack_type == AttackType.ULTIMATE else 10
            shake_duration = 8 if attack.attack_type == AttackType.LIGHT else 20 if attack.attack_type == AttackType.ULTIMATE else 15
            screen_shake.trigger(shake_intensity, shake_duration)
            
            # 怒气获取
            self.rage = min(self.max_rage, self.rage + 10)
            opponent.rage = min(self.max_rage, opponent.rage + 8)
            
            # 状态
            opponent.state = CharacterState.HIT
            opponent.is_blocking = False
            
            # 必杀特效
            if attack.attack_type == AttackType.ULTIMATE:
                effects_list.append(UltimateWave(self.x + self.width / 2, self.y + self.height / 2))
        
        self.has_hit = True
    
    # =========================================================================
    # 更新逻辑
    # =========================================================================
    def update(self, opponent):
        # 朝向对手
        if not self.is_attacking and self.hitstun <= 0 and self.dodge_timer <= 0:
            if opponent.x > self.x:
                self.facing = 1
            else:
                self.facing = -1
        
        # 连击计时器
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.hit_combo = 0
        
        # 计时器更新
        if self.attack_timer > 0:
            self.attack_timer -= 1
        
        if self.hitstun > 0:
            self.hitstun -= 1
        
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        if self.grounded_timer > 0:
            self.grounded_timer -= 1
            if self.grounded_timer <= 0:
                self.invincible_timer = 0
                self.is_grounded_hit = False
        
        if self.ultimate_timer > 0:
            self.ultimate_timer -= 1
            if self.ultimate_timer <= 0:
                self.is_ultimate = False
                self.current_attack = None
                self.is_attacking = False
        
        if self.perfect_block_window > 0:
            self.perfect_block_window -= 1
        
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
        
        # 攻击结束
        if self.is_attacking and self.attack_timer <= 0:
            self.is_attacking = False
            self.current_attack = None
            if self.is_grounded and self.hitstun <= 0:
                self.state = CharacterState.IDLE
        
        # 受击结束
        if self.hitstun <= 0 and self.state == CharacterState.HIT:
            if not self.is_grounded:
                self.state = CharacterState.JUMP
            else:
                self.state = CharacterState.IDLE
        
        # 闪避结束
        if self.dodge_timer <= 0 and self.state == CharacterState.DODGE:
            if self.is_grounded:
                self.state = CharacterState.IDLE
        
        # 物理更新
        # 重力
        if not self.is_grounded:
            self.vel_y += GRAVITY
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED
        
        # 应用速度
        self.x += self.vel_x
        self.y += self.vel_y
        
        # 地面检测
        ground_level = GROUND_Y - self.height
        if self.y >= ground_level:
            self.y = ground_level
            
            if not self.is_grounded:
                # 落地
                self.is_grounded = True
                self.jump_count = 0
                
                # 浮空落地
                if self.is_launched or self.vel_y > 10:
                    self.is_launched = False
                    self.is_grounded_hit = True
                    self.grounded_timer = 40
                    self.invincible_timer = 30  # 起身无敌
                    self.state = CharacterState.GROUNDED
            
            if self.state == CharacterState.JUMP:
                self.state = CharacterState.IDLE
        
        # 空中状态
        if not self.is_grounded:
            self.state = CharacterState.JUMP
        
        # 摩擦
        if self.hitstun > 0:
            self.vel_x *= 0.9
        elif self.dodge_timer > 0:
            self.vel_x *= 0.95
        elif not self.is_attacking:
            # 正常摩擦
            if abs(self.vel_x) > 0.5:
                self.vel_x *= FRICTION
            else:
                self.vel_x = 0
        
        # 边界限制
        self.x = clamp(self.x, BOUNDARY_MARGIN, SCREEN_WIDTH - self.width - BOUNDARY_MARGIN)
        
        # 动画帧
        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4
    
    # =========================================================================
    # 渲染
    # =========================================================================
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        x = int(self.x + offset_x)
        y = int(self.y + offset_y)
        w = self.width
        h = self.height
        
        # 受击闪烁
        if self.hit_flash_timer > 0 and self.hit_flash_timer % 2 == 0:
            flash_color = self.hit_flash_color
        else:
            flash_color = None
        
        # 无敌闪烁
        is_invincible = self.invincible_timer > 0
        if is_invincible and self.invincible_timer % 6 < 3:
            temp_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            temp_surface.set_alpha(120)
            pygame.draw.rect(temp_surface, (*WHITE, 100), (0, 0, w, h))
            surface.blit(temp_surface, (x, y))
        
        # 下蹲时的高度调整
        render_h = h
        render_y = y
        if self.state == CharacterState.CROUCH:
            render_h = int(h * 0.6)
            render_y = y + h - render_h
        
        # 身体主体
        body_color = flash_color if flash_color else self.body_color
        body_color_dark = flash_color if flash_color else self.body_color_dark
        
        # 身体阴影
        shadow_surface = pygame.Surface((w + 20, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (*BLACK, 80), (10, 5, w, 10))
        surface.blit(shadow_surface, (x - 10 + offset_x, GROUND_Y - 10 + offset_y))
        
        # 绘制角色
        if self.state == CharacterState.DODGE:
            # 闪避姿态 - 横向压缩
            stretch_x = 0.7
            stretch_y = 1.2
            temp_surface = pygame.Surface((int(w * stretch_x), int(render_h * stretch_y)), pygame.SRCALPHA)
            pygame.draw.rect(temp_surface, body_color, (0, 0, temp_surface.get_width(), temp_surface.get_height()), border_radius=8)
            pygame.draw.rect(temp_surface, body_color_dark, (2, 2, temp_surface.get_width() - 4, temp_surface.get_height() - 4), border_radius=6)
            surface.blit(temp_surface, (x + w // 2 - temp_surface.get_width() // 2, render_y + render_h - temp_surface.get_height()))
        elif self.state == CharacterState.GROUNDED:
            # 倒地姿态
            pygame.draw.rect(surface, body_color, (x, render_y + render_h - 30, w, 30), border_radius=8)
            pygame.draw.rect(surface, body_color_dark, (x + 3, render_y + render_h - 27, w - 6, 24), border_radius=6)
        elif self.state == CharacterState.ATTACK_LIGHT:
            # 轻攻击
            arm_extend = 30
            pygame.draw.rect(surface, body_color, (x, render_y, w, render_h), border_radius=8)
            pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, w - 10, render_h - 10), border_radius=6)
            
            # 拳头
            fist_x = x + w // 2 + self.facing * (w // 2 + arm_extend)
            pygame.draw.circle(surface, self.accent_color, (int(fist_x), render_y + render_h // 2), 12)
            pygame.draw.circle(surface, WHITE, (int(fist_x), render_y + render_h // 2), 8)
        elif self.state == CharacterState.ATTACK_HEAVY:
            # 重攻击 - 蓄力/挥出
            arm_extend = 50
            # 蓄力效果
            if self.attack_timer > 20:
                charge_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
                for i in range(3):
                    pygame.draw.circle(charge_surface, (*ORANGE, 150 - i * 50), (30, 30), 25 - i * 6)
                surface.blit(charge_surface, (x + w // 2 - 30, render_y + render_h // 2 - 30))
            
            pygame.draw.rect(surface, body_color, (x, render_y, w, render_h), border_radius=8)
            pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, w - 10, render_h - 10), border_radius=6)
            
            # 重拳
            fist_x = x + w // 2 + self.facing * (w // 2 + arm_extend)
            pygame.draw.circle(surface, ORANGE, (int(fist_x), render_y + render_h // 2 - 10), 18)
            pygame.draw.circle(surface, YELLOW, (int(fist_x), render_y + render_h // 2 - 10), 12)
        elif self.state == CharacterState.ATTACK_LOW:
            # 下段攻击
            pygame.draw.rect(surface, body_color, (x, render_y, w, render_h), border_radius=8)
            pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, w - 10, render_h - 10), border_radius=6)
            
            # 下段攻击特效
            leg_x = x + w // 2 + self.facing * (w // 2 + 25)
            pygame.draw.rect(surface, self.accent_color, 
                (leg_x - 15, render_y + render_h - 20, 40, 15), border_radius=5)
        elif self.is_ultimate:
            # 必杀姿态
            pulse_size = 30 + math.sin(pygame.time.get_ticks() * 0.02) * 10
            
            # 能量场
            ultimate_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
            for i in range(4):
                pygame.draw.circle(ultimate_surface, (*CYAN, 200 - i * 40), 
                    (100, 100), int(pulse_size + i * 15), width=8 - i * 2)
            surface.blit(ultimate_surface, (x + w // 2 - 100, render_y + render_h // 2 - 100))
            
            # 身体
            pygame.draw.rect(surface, CYAN, (x, render_y, w, render_h), border_radius=8)
            pygame.draw.rect(surface, WHITE, (x + 8, render_y + 8, w - 16, render_h - 16), border_radius=6)
        elif self.state == CharacterState.BLOCK:
            # 格挡姿态
            pygame.draw.rect(surface, body_color, (x, render_y, w, render_h), border_radius=8)
            pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, w - 10, render_h - 10), border_radius=6)
            
            # 格挡护盾
            shield_surface = pygame.Surface((40, render_h + 20), pygame.SRCALPHA)
            pygame.draw.rect(shield_surface, (*LIGHT_GRAY, 180), 
                (5, 10, 30, render_h), border_radius=5)
            pygame.draw.rect(shield_surface, (*WHITE, 150), 
                (10, 15, 20, render_h - 10), border_radius=3)
            if self.facing > 0:
                surface.blit(shield_surface, (x + w, render_y - 10))
            else:
                surface.blit(shield_surface, (x - 40, render_y - 10))
        else:
            # 正常姿态
            pygame.draw.rect(surface, body_color, (x, render_y, w, render_h), border_radius=10)
            pygame.draw.rect(surface, body_color_dark, (x + 6, render_y + 6, w - 12, render_h - 12), border_radius=8)
            
            # 装饰线
            pygame.draw.line(surface, self.accent_color, 
                (x + w // 2, render_y + 10), (x + w // 2, render_y + render_h - 10), 2)
        
        # 头部
        head_x = x + w // 2
        head_y = render_y + 15
        head_radius = 18
        pygame.draw.circle(surface, body_color, (head_x, head_y), head_radius)
        pygame.draw.circle(surface, body_color_dark, (head_x, head_y), head_radius - 3)
        
        # 眼睛
        eye_offset_x = 5 * self.facing
        eye_y = head_y - 2
        pygame.draw.circle(surface, WHITE, (head_x + eye_offset_x, eye_y), 4)
        pygame.draw.circle(surface, BLACK, (head_x + eye_offset_x + self.facing, eye_y), 2)

# =============================================================================
# 场景渲染
# =============================================================================
class Stage:
    def __init__(self):
        self.grid_offset = 0
    
    def update(self):
        self.grid_offset += 0.5
    
    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        # 背景渐变
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(lerp(20, 60, t))
            g = int(lerp(30, 80, t))
            b = int(lerp(50, 120, t))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 远景装饰
        for i in range(5):
            x = (i * 300 + self.grid_offset * 0.3) % (SCREEN_WIDTH + 200) - 100
            pygame.draw.circle(surface, (40, 70, 100), (int(x), 200), 80)
        
        # 地面
        pygame.draw.rect(surface, DARK_GRAY, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        
        # 地面网格
        for i in range(int(SCREEN_WIDTH / 40) + 2):
            x = int((i * 40 - self.grid_offset) % (SCREEN_WIDTH + 40))
            pygame.draw.line(surface, GRAY, (x, GROUND_Y), (x, SCREEN_HEIGHT), 1)
        
        for i in range(int((SCREEN_HEIGHT - GROUND_Y) / 30) + 2):
            y = GROUND_Y + i * 30
            pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y), 1)
        
        # 地面高亮线
        pygame.draw.line(surface, LIGHT_GRAY, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 3)

# =============================================================================
# UI系统
# =============================================================================
class UI:
    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.round_transition_alpha = 0
        self.round_transition_text = ""
    
    def init_fonts(self):
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
    
    def render_health_bar(self, surface: pygame.Surface, x: int, y: int, width: int, height: int, 
                           current: int, maximum: int, is_player1: bool, rage: float, max_rage: float,
                           player_name: str, is_flashing: bool = False):
        # 血条背景
        border_color = DARK_BLUE if is_player1 else DARK_RED
        fill_color = BLUE if is_player1 else RED
        
        pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height), border_radius=5)
        pygame.draw.rect(surface, border_color, (x, y, width, height), 3, border_radius=5)
        
        # 血条填充（带渐变效果）
        health_ratio = current / maximum
        fill_width = int(width * health_ratio)
        
        if fill_width > 0:
            # 主血条
            health_surface = pygame.Surface((fill_width, height - 6), pygame.SRCALPHA)
            for i in range(fill_width):
                t = i / fill_width
                r = int(lerp(fill_color[0] * 1.3, fill_color[0] * 0.7, t))
                g = int(lerp(fill_color[1] * 1.3, fill_color[1] * 0.7, t))
                b = int(lerp(fill_color[2] * 1.3, fill_color[2] * 0.7, t))
                pygame.draw.line(health_surface, (r, g, b), (i, 0), (i, height - 6))
            
            # 高光
            highlight = pygame.Surface((fill_width, (height - 6) // 3), pygame.SRCALPHA)
            for i in range(fill_width):
                pygame.draw.line(highlight, (255, 255, 255, 80), (i, 0), (i, highlight.get_height()))
            health_surface.blit(highlight, (0, 0))
            
            surface.blit(health_surface, (x + 3, y + 3))
        
        # 残血闪烁
        if health_ratio < 0.25:
            flash_alpha = int((math.sin(pygame.time.get_ticks() * 0.01) + 1) * 50)
            flash_surface = pygame.Surface((fill_width, height - 6), pygame.SRCALPHA)
            pygame.draw.rect(flash_surface, (255, 0, 0, flash_alpha), (0, 0, fill_width, height - 6))
            surface.blit(flash_surface, (x + 3, y + 3))
        
        # 怒气条
        rage_width = int(width * 0.8)
        rage_height = 12
        rage_x = x + (width - rage_width) // 2
        rage_y = y + height + 8
        
        pygame.draw.rect(surface, DARK_GRAY, (rage_x, rage_y, rage_width, rage_height), border_radius=3)
        
        # 怒气填充（流光效果）
        if rage > 0:
            rage_ratio = rage / max_rage
            rage_fill = int(rage_width * rage_ratio)
            
            rage_surface = pygame.Surface((rage_fill, rage_height - 4), pygame.SRCALPHA)
            
            # 流光
            flow_offset = pygame.time.get_ticks() * 0.01
            for i in range(rage_fill):
                flow = (math.sin((i + flow_offset) * 0.1) + 1) * 0.5
                r = int(lerp(PURPLE[0], ORANGE[0], flow) * 0.8 + 50)
                g = int(lerp(PURPLE[1], ORANGE[1], flow) * 0.8 + 50)
                b = int(lerp(PURPLE[2], ORANGE[2], flow) * 0.8 + 50)
                pygame.draw.line(rage_surface, (r, g, b), (i, 0), (i, rage_height - 4))
            
            # 满怒闪烁
            if rage_ratio >= 1.0:
                flash = int((math.sin(pygame.time.get_ticks() * 0.02) + 1) * 50)
                pygame.draw.rect(rage_surface, (255, 255, 255, flash), (0, 0, rage_fill, rage_height - 4))
            
            surface.blit(rage_surface, (rage_x + 2, rage_y + 2))
        
        # 怒气条边框
        border_rage = PURPLE if rage < max_rage else YELLOW
        pygame.draw.rect(surface, border_rage, (rage_x, rage_y, rage_width, rage_height), 2, border_radius=3)
        
        # 玩家名字
        if self.font_small:
            name_text = self.font_small.render(player_name, True, WHITE)
            if is_player1:
                surface.blit(name_text, (x, y - 30))
            else:
                surface.blit(name_text, (x + width - name_text.get_width(), y - 30))
        
        # 血量数字
        if self.font_medium:
            health_text = self.font_medium.render(f"{current}", True, WHITE)
            if is_player1:
                surface.blit(health_text, (x + width + 10, y))
            else:
                text_width = health_text.get_width()
                surface.blit(health_text, (x - text_width - 10, y))
    
    def render_timer(self, surface: pygame.Surface, time_remaining: int):
        if self.font_large:
            # 时间背景
            timer_x = SCREEN_WIDTH // 2 - 50
            pygame.draw.rect(surface, DARK_GRAY, (timer_x, 10, 100, 50), border_radius=10)
            pygame.draw.rect(surface, GRAY, (timer_x + 3, 13, 94, 44), 2, border_radius=8)
            
            # 时间文字
            color = RED if time_remaining <= 10 else WHITE
            timer_text = self.font_large.render(f"{time_remaining}", True, color)
            surface.blit(timer_text, (SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 15))
    
    def render_round_score(self, surface: pygame.Surface, p1_wins: int, p2_wins: int):
        if self.font_small:
            # 回合指示器
            for i in range(MAX_ROUNDS):
                # 玩家1
                x1 = 20 + i * 30
                color1 = GREEN if i < p1_wins else DARK_GRAY
                pygame.draw.circle(surface, color1, (x1 + 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x1 + 10, 85), 10, 2)
                
                # 玩家2
                x2 = SCREEN_WIDTH - 20 - (MAX_ROUNDS - 1 - i) * 30
                color2 = GREEN if i < p2_wins else DARK_GRAY
                pygame.draw.circle(surface, color2, (x2 - 10, 85), 10)
                pygame.draw.circle(surface, WHITE, (x2 - 10, 85), 10, 2)
    
    def render_combo(self, surface: pygame.Surface, player1: Character, player2: Character):
        if self.font_medium:
            # 玩家1连击
            if player2.hit_combo >= 2:
                combo_text = self.font_medium.render(f"COMBO x{player2.hit_combo}", True, ORANGE)
                surface.blit(combo_text, (20, 120))
            
            # 玩家2连击
            if player1.hit_combo >= 2:
                combo_text = self.font_medium.render(f"COMBO x{player1.hit_combo}", True, ORANGE)
                surface.blit(combo_text, (SCREEN_WIDTH - combo_text.get_width() - 20, 120))
    
    def render_round_transition(self, surface: pygame.Surface, text: str, alpha: int):
        if self.font_large and alpha > 0:
            transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            transition_surface.fill((0, 0, 0, min(alpha, 180)))
            
            text_surface = self.font_large.render(text, True, WHITE)
            text_surface.set_alpha(alpha)
            transition_surface.blit(text_surface, 
                (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, 
                 SCREEN_HEIGHT // 2 - text_surface.get_height() // 2))
            
            surface.blit(transition_surface, (0, 0))

# =============================================================================
# 菜单系统
# =============================================================================
class Menu:
    def __init__(self):
        self.font_title = None
        self.font_option = None
        self.font_hint = None
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
            self.options = ["START GAME", "QUIT"]
        elif menu_type == "mode":
            self.options = ["PLAYER VS PLAYER", "PLAYER VS CPU", "BACK"]
        elif menu_type == "difficulty":
            self.options = ["EASY", "HARD", "BACK"]
    
    def update(self):
        self.animation_offset = math.sin(pygame.time.get_ticks() * 0.003) * 10
    
    def handle_input(self, keys, events):
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
        # 背景
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(lerp(10, 40, t))
            g = int(lerp(20, 60, t))
            b = int(lerp(40, 100, t))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 装饰线
        for i in range(8):
            x = int(math.sin(pygame.time.get_ticks() * 0.001 + i) * 200 + SCREEN_WIDTH // 2)
            pygame.draw.circle(surface, (30, 60, 120), (x, 300 + i * 50), 50 + i * 10)
        
        # 标题
        if self.menu_type == "main" and self.font_title:
            title_text = self.font_title.render("COMBAT MASTER", True, CYAN)
            title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
            title_y = 100 + self.animation_offset
            surface.blit(title_text, (title_x, title_y))
            
            # 标题光晕
            glow_surface = pygame.Surface((title_text.get_width() + 40, title_text.get_height() + 40), pygame.SRCALPHA)
            for i in range(5):
                alpha = int(50 - i * 10)
                size = 10 + i * 2
                pygame.draw.rect(glow_surface, (*CYAN, alpha), 
                    (20 - size // 2, 20 - size // 2, 
                     title_text.get_width() + size, title_text.get_height() + size), 
                    width=size // 2, border_radius=10)
            surface.blit(glow_surface, (title_x - 20, title_y - 20))
        
        # 副标题
        if self.menu_type == "mode" and self.font_title:
            title_text = self.font_title.render("SELECT MODE", True, WHITE)
            surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 120))
        elif self.menu_type == "difficulty" and self.font_title:
            title_text = self.font_title.render("SELECT DIFFICULTY", True, WHITE)
            surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 120))
        
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
                    # 选中指示器
                    indicator_x = text_x - 50
                    pygame.draw.polygon(surface, YELLOW, 
                        [(indicator_x, text_y + 15), 
                         (indicator_x + 20, text_y + 5),
                         (indicator_x + 20, text_y + 25)])
                    
                    pygame.draw.polygon(surface, YELLOW, 
                        [(text_x + text.get_width() + 30, text_y + 15), 
                         (text_x + text.get_width() + 10, text_y + 5),
                         (text_x + text.get_width() + 10, text_y + 25)])
                
                surface.blit(text, (text_x, text_y))
        
        # 操作提示
        if self.font_hint:
            hint_text = self.font_hint.render("UP/DOWN or W/S to select, ENTER to confirm", True, GRAY)
            surface.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 60))

# =============================================================================
# 暂停/结算菜单
# =============================================================================
class InGameMenu:
    def __init__(self):
        self.font_title = None
        self.font_option = None
        self.font_small = None
        self.selected_index = 0
        self.options = ["RESUME", "RESTART", "BACK TO MENU"]
    
    def init_fonts(self):
        self.font_title = pygame.font.Font(None, 72)
        self.font_option = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 28)
    
    def handle_input(self, keys, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0  # 按ESC恢复
        
        return None
    
    def render_pause(self, surface: pygame.Surface):
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # 标题
        if self.font_title:
            title_text = self.font_title.render("PAUSED", True, WHITE)
            surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
        
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
                    # 选中指示器
                    indicator_x = text_x - 50
                    pygame.draw.polygon(surface, YELLOW, 
                        [(indicator_x, text_y + 15), 
                         (indicator_x + 20, text_y + 5),
                         (indicator_x + 20, text_y + 25)])
                    
                    pygame.draw.polygon(surface, YELLOW, 
                        [(text_x + text.get_width() + 30, text_y + 15), 
                         (text_x + text.get_width() + 10, text_y + 5),
                         (text_x + text.get_width() + 10, text_y + 25)])
                
                surface.blit(text, (text_x, text_y))
    
    def render_game_over(self, surface: pygame.Surface, winner_name: str, 
                         p1_max_combo: int, p2_max_combo: int,
                         p1_total_damage: int, p2_total_damage: int,
                         winner_is_p1: bool):
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        if self.font_title:
            # 胜利文字
            winner_color = BLUE if winner_is_p1 else RED
            win_text = self.font_title.render("WINNER!", True, winner_color)
            surface.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, 120))
            
            # 获胜者名字
            if self.font_option:
                name_text = self.font_option.render(winner_name, True, WHITE)
                surface.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 200))
        
        # 统计数据
        if self.font_small:
            start_y = 300
            spacing = 40
            
            # 玩家1数据
            p1_header = self.font_small.render("PLAYER 1", True, CYAN)
            surface.blit(p1_header, (200, start_y))
            
            p1_combo = self.font_small.render(f"Max Combo: {p1_max_combo}", True, WHITE)
            surface.blit(p1_combo, (200, start_y + spacing))
            
            p1_dmg = self.font_small.render(f"Total Damage: {p1_total_damage}", True, WHITE)
            surface.blit(p1_dmg, (200, start_y + spacing * 2))
            
            # 玩家2数据
            p2_header = self.font_small.render("PLAYER 2", True, PINK)
            surface.blit(p2_header, (SCREEN_WIDTH - 400, start_y))
            
            p2_combo = self.font_small.render(f"Max Combo: {p2_max_combo}", True, WHITE)
            surface.blit(p2_combo, (SCREEN_WIDTH - 400, start_y + spacing))
            
            p2_dmg = self.font_small.render(f"Total Damage: {p2_total_damage}", True, WHITE)
            surface.blit(p2_dmg, (SCREEN_WIDTH - 400, start_y + spacing * 2))
        
        # 提示
        if self.font_small:
            hint_text = self.font_small.render("Press ENTER to return to menu", True, GRAY)
            surface.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 80))

# =============================================================================
# 游戏主类
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        # 窗口设置
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Combat Master - 格斗大师")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 游戏状态
        self.state = GameState.MENU
        self.game_mode = "pvp"  # "pvp" or "pvc"
        self.difficulty = "easy"
        
        # 回合数据
        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.p1_wins = 0
        self.p2_wins = 0
        self.current_round = 1
        
        # 回合过渡
        self.round_transition = False
        self.round_transition_timer = 0
        self.round_transition_text = ""
        
        # 游戏对象
        self.player1: Optional[Character] = None
        self.player2: Optional[Character] = None
        self.stage = Stage()
        self.effects: List[Effect] = []
        self.screen_shake = ScreenShake()
        
        # UI和菜单
        self.ui = UI()
        self.main_menu = Menu()
        self.ingame_menu = InGameMenu()
        
        # 初始化字体
        self.ui.init_fonts()
        self.main_menu.init_fonts()
        self.ingame_menu.init_fonts()
        
        self.main_menu.set_menu("main")
    
    def start_new_round(self):
        ground_y = GROUND_Y - PLAYER_HEIGHT
        self.player1 = Character(200, ground_y, is_player1=True, is_ai=False)
        self.player2 = Character(SCREEN_WIDTH - 260, ground_y, is_player1=False, 
                                 is_ai=(self.game_mode == "pvc"), difficulty=self.difficulty)
        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.effects = []
        self.screen_shake = ScreenShake()
        
        # 回合开始过渡
        self.round_transition = True
        self.round_transition_timer = 120
        self.round_transition_text = f"ROUND {self.current_round}"
    
    def start_game(self):
        self.current_round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.start_new_round()
        self.state = GameState.PLAYING
    
    def check_round_end(self) -> bool:
        p1_dead = self.player1.health <= 0
        p2_dead = self.player2.health <= 0
        time_up = self.round_timer <= 0
        
        if p1_dead or p2_dead or time_up:
            # 决定胜利者
            if p1_dead and not p2_dead:
                winner = 2
            elif p2_dead and not p1_dead:
                winner = 1
            else:
                # 时间结束比较血量
                if self.player1.health > self.player2.health:
                    winner = 1
                elif self.player2.health > self.player1.health:
                    winner = 2
                else:
                    winner = 0  # 平局
            
            # 显示回合结果
            if winner == 1:
                self.p1_wins += 1
                self.round_transition_text = "PLAYER 1 WINS!"
            elif winner == 2:
                self.p2_wins += 1
                self.round_transition_text = "PLAYER 2 WINS!"
            else:
                self.round_transition_text = "DRAW!"
            
            self.round_transition = True
            self.round_transition_timer = 180
            self.state = GameState.ROUND_END
            return True
        
        return False
    
    def check_game_over(self) -> bool:
        if self.p1_wins >= 2:
            # 玩家1获胜
            self.state = GameState.GAME_OVER
            return True
        elif self.p2_wins >= 2:
            # 玩家2/CPU获胜
            self.state = GameState.GAME_OVER
            return True
        return False
    
    def handle_events(self):
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        
        if self.state == GameState.MENU:
            self.main_menu.update()
            selection = self.main_menu.handle_input(keys, events)
            if selection is not None:
                if self.main_menu.menu_type == "main":
                    if selection == 0:
                        self.main_menu.set_menu("mode")
                    elif selection == 1:
                        self.running = False
                elif self.main_menu.menu_type == "mode":
                    if selection == 0:
                        self.game_mode = "pvp"
                        self.start_game()
                    elif selection == 1:
                        self.game_mode = "pvc"
                        self.main_menu.set_menu("difficulty")
                    elif selection == 2:
                        self.main_menu.set_menu("main")
                elif self.main_menu.menu_type == "difficulty":
                    if selection == 0:
                        self.difficulty = "easy"
                        self.start_game()
                    elif selection == 1:
                        self.difficulty = "hard"
                        self.start_game()
                    elif selection == 2:
                        self.main_menu.set_menu("mode")
        
        elif self.state == GameState.PLAYING:
            # ESC暂停
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                        self.ingame_menu.selected_index = 0
            
            # 游戏输入
            if self.player1 and self.player2:
                self.player1.handle_input(keys, self.player2)
                self.player2.handle_input(keys, self.player1)
        
        elif self.state == GameState.PAUSED:
            selection = self.ingame_menu.handle_input(keys, events)
            if selection is not None:
                if selection == 0:
                    self.state = GameState.PLAYING
                elif selection == 1:
                    self.start_game()
                elif selection == 2:
                    self.state = GameState.MENU
                    self.main_menu.set_menu("main")
        
        elif self.state == GameState.GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                        self.main_menu.set_menu("main")
    
    def update(self):
        if self.state == GameState.PLAYING:
            # 回合计时器
            self.round_timer_frames += 1
            if self.round_timer_frames >= FPS:
                self.round_timer_frames = 0
                if self.round_timer > 0:
                    self.round_timer -= 1
            
            # 回合过渡
            if self.round_transition:
                self.round_transition_timer -= 1
                if self.round_transition_timer <= 0:
                    self.round_transition = False
            else:
                # 更新玩家
                if self.player1 and self.player2:
                    self.player1.update(self.player2)
                    self.player2.update(self.player2)
                    
                    # 攻击判定
                    self.player1.check_attack_hit(self.player2, self.effects, self.screen_shake)
                    self.player2.check_attack_hit(self.player1, self.effects, self.screen_shake)
                
                # 更新特效
                for effect in self.effects:
                    effect.update()
                self.effects = [e for e in self.effects if e.alive]
                
                # 更新屏幕震动
                self.screen_shake.update()
                
                # 更新场景
                self.stage.update()
                
                # 检查回合结束
                if not self.check_round_end():
                    pass
        
        elif self.state == GameState.ROUND_END:
            self.round_transition_timer -= 1
            if self.round_transition_timer <= 0:
                if not self.check_game_over():
                    # 进入下一回合
                    self.current_round += 1
                    self.start_new_round()
                    self.state = GameState.PLAYING
        
        elif self.state == GameState.MENU:
            self.main_menu.update()
            self.stage.update()
    
    def render(self):
        self.screen.fill(BLACK)
        
        shake_x, shake_y = self.screen_shake.get_offset()
        
        if self.state == GameState.MENU:
            # 渲染菜单背景
            self.stage.render(self.screen)
            self.main_menu.render(self.screen)
        
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.ROUND_END]:
            # 渲染场景
            self.stage.render(self.screen, shake_x, shake_y)
            
            # 渲染玩家
            if self.player1 and self.player2:
                self.player1.render(self.screen, shake_x, shake_y)
                self.player2.render(self.screen, shake_x, shake_y)
            
            # 渲染特效
            for effect in self.effects:
                effect.render(self.screen, shake_x, shake_y)
            
            # 渲染UI（不受屏幕震动影响）
            if self.player1 and self.player2:
                # 玩家1血条（左侧）
                self.ui.render_health_bar(
                    self.screen, 50, 30, 280, 30,
                    self.player1.health, self.player1.max_health,
                    True, self.player1.rage, self.player1.max_rage,
                    "PLAYER 1"
                )
                
                # 玩家2血条（右侧）
                self.ui.render_health_bar(
                    self.screen, SCREEN_WIDTH - 330, 30, 280, 30,
                    self.player2.health, self.player2.max_health,
                    False, self.player2.rage, self.player2.max_rage,
                    "PLAYER 2" if self.game_mode == "pvp" else "CPU"
                )
                
                # 计时器
                self.ui.render_timer(self.screen, self.round_timer)
                
                # 回合分数
                self.ui.render_round_score(self.screen, self.p1_wins, self.p2_wins)
                
                # 连击
                self.ui.render_combo(self.screen, self.player1, self.player2)
            
            # 回合过渡
            if self.round_transition:
                alpha = 0
                if self.round_transition_timer > 100:
                    alpha = int((120 - self.round_transition_timer) / 20 * 255)
                elif self.round_transition_timer > 30:
                    alpha = 255
                else:
                    alpha = int(self.round_transition_timer / 30 * 255)
                self.ui.render_round_transition(self.screen, self.round_transition_text, alpha)
        
        # 暂停菜单
        if self.state == GameState.PAUSED:
            self.ingame_menu.render_pause(self.screen)
        
        # 结算界面
        if self.state == GameState.GAME_OVER and self.player1 and self.player2:
            winner_is_p1 = self.p1_wins >= 2
            winner_name = "PLAYER 1" if winner_is_p1 else ("PLAYER 2" if self.game_mode == "pvp" else "CPU")
            self.ingame_menu.render_game_over(
                self.screen, winner_name,
                self.player1.max_combo, self.player2.max_combo,
                self.player1.total_damage_dealt, self.player2.total_damage_dealt,
                winner_is_p1
            )
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# =============================================================================
# 主函数
# =============================================================================
def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()