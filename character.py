#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 角色模块
包含角色的物理系统、动作系统、攻击判定
所有颜色值严格限制在 0-255 范围内
"""

import math
from typing import Optional, Tuple
import pygame

from config import (
    CharacterState, AttackType,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_WIDTH, PLAYER_HEIGHT,
    WALK_SPEED, FRICTION, GRAVITY, MAX_FALL_SPEED,
    JUMP_FORCE, DOUBLE_JUMP_FORCE, BOUNDARY_MARGIN,
    MAX_HEALTH, MAX_RAGE,
    PLAYER1_COLOR, PLAYER1_COLOR_DARK, PLAYER1_ACCENT,
    PLAYER2_COLOR, PLAYER2_COLOR_DARK, PLAYER2_ACCENT,
    WHITE, BLACK, ORANGE, YELLOW, CYAN, LIGHT_GRAY,
    GROUND_Y,
    clamp_color, safe_color, lerp_color, scale_color, with_alpha,
    clamp, lerp,
    COMBO_PROTECTION_START, COMBO_PROTECTION_PER_HIT,
    RAGE_ON_HIT, RAGE_ON_GUARD, RAGE_ON_HIT_BY, RAGE_PERFECT_BLOCK
)
from attack import (
    AttackData, 
    get_light_attack, get_heavy_attack, get_low_attack, get_ultimate_attack,
    calculate_hitbox, get_defense_hitbox
)
from effects import Effect, DamageNumber, HitSpark, UltimateWave, ScreenShake


# =============================================================================
# 角色类
# =============================================================================
class Character:
    """游戏角色类"""
    
    def __init__(self, x: float, y: float, is_player1: bool):
        # ========================================
        # 位置和物理
        # ========================================
        self.x = x
        self.y = y
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        # ========================================
        # 玩家标识
        # ========================================
        self.is_player1 = is_player1
        self.facing = 1 if is_player1 else -1
        
        # ========================================
        # 状态
        # ========================================
        self.state = CharacterState.IDLE
        
        # ========================================
        # 属性
        # ========================================
        self.max_health = MAX_HEALTH
        self.health = self.max_health
        self.max_rage = MAX_RAGE
        self.rage = 0
        
        # ========================================
        # 跳跃
        # ========================================
        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = True
        
        # ========================================
        # 攻击
        # ========================================
        self.current_attack: Optional[AttackData] = None
        self.attack_timer = 0
        self.has_hit = False
        self.is_attacking = False
        
        # ========================================
        # 受击
        # ========================================
        self.hitstun = 0
        self.is_launched = False
        self.is_grounded_hit = False
        self.grounded_timer = 0
        self.invincible_timer = 0
        
        # ========================================
        # 格挡
        # ========================================
        self.is_blocking = False
        self.block_high = True
        self.perfect_block_window = 0
        
        # ========================================
        # 闪避
        # ========================================
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.dodge_direction = 0
        
        # ========================================
        # 必杀
        # ========================================
        self.ultimate_timer = 0
        self.is_ultimate = False
        
        # ========================================
        # 动画帧
        # ========================================
        self.anim_frame = 0
        self.anim_timer = 0
        
        # ========================================
        # 连击统计
        # ========================================
        self.hit_combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.total_damage_dealt = 0
        
        # ========================================
        # 受击闪烁
        # ========================================
        self.hit_flash_timer = 0
        self.hit_flash_color: Optional[Tuple[int, ...]] = None
        
        # ========================================
        # 渲染颜色（使用安全的预定义颜色）
        # ========================================
        if is_player1:
            self.body_color = PLAYER1_COLOR
            self.body_color_dark = PLAYER1_COLOR_DARK
            self.accent_color = PLAYER1_ACCENT
        else:
            self.body_color = PLAYER2_COLOR
            self.body_color_dark = PLAYER2_COLOR_DARK
            self.accent_color = PLAYER2_ACCENT
        
        # ========================================
        # AI相关（在ai.py中实现）
        # ========================================
        self.is_ai = False
        self.difficulty = "easy"
        self.ai_timer = 0
        self.ai_attack_cooldown = 0
    
    # =========================================================================
    # 输入处理
    # =========================================================================
    def handle_input(self, keys, opponent: 'Character'):
        """
        处理玩家输入
        
        Args:
            keys: pygame.key.get_pressed() 的结果
            opponent: 对手角色
        """
        # AI角色不处理键盘输入
        if self.is_ai:
            return
        
        # ========================================
        # 检查是否可以操作
        # ========================================
        if self.hitstun > 0 or self.grounded_timer > 0:
            return
        if self.dodge_timer > 0:
            return
        if self.is_attacking and self.attack_timer > 0:
            return
        if self.is_ultimate:
            return
        
        # ========================================
        # 重置状态
        # ========================================
        move_input = 0
        self.is_blocking = False
        
        # ========================================
        # 根据玩家1或玩家2处理不同按键
        # ========================================
        if self.is_player1:
            # 玩家1按键
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
                self.start_attack(get_light_attack())
            if keys[pygame.K_k]:
                self.start_attack(get_heavy_attack())
            
            # 格挡
            if keys[pygame.K_l]:
                if self.is_grounded:
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
        
        else:
            # 玩家2按键（只在PVP模式下使用）
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
                self.start_attack(get_light_attack())
            if keys[pygame.K_KP2] or keys[pygame.K_2]:
                self.start_attack(get_heavy_attack())
            
            # 格挡
            if keys[pygame.K_KP3] or keys[pygame.K_3]:
                if self.is_grounded:
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
        
        # ========================================
        # 应用移动
        # ========================================
        if not self.is_blocking and not self.is_attacking:
            if move_input != 0:
                self.vel_x = move_input * WALK_SPEED
                if self.state != CharacterState.JUMP and self.is_grounded:
                    self.state = CharacterState.WALK
            else:
                if self.is_grounded and self.state == CharacterState.WALK:
                    self.state = CharacterState.IDLE
    
    # =========================================================================
    # 跳跃动作
    # =========================================================================
    def jump(self):
        """执行跳跃动作"""
        if self.jump_count >= self.max_jumps:
            return
        
        # 根据跳跃次数选择不同的跳跃力度
        jump_force = JUMP_FORCE if self.jump_count == 0 else DOUBLE_JUMP_FORCE
        
        self.vel_y = jump_force
        self.jump_count += 1
        self.is_grounded = False
        self.state = CharacterState.JUMP
    
    # =========================================================================
    # 开始攻击
    # =========================================================================
    def start_attack(self, attack_data: AttackData):
        """开始攻击
        
        Args:
            attack_data: 攻击数据
        """
        if self.is_attacking or self.hitstun > 0:
            return
        
        self.current_attack = attack_data
        self.attack_timer = attack_data.total_frames
        self.is_attacking = True
        self.has_hit = False
        
        # 设置状态
        if attack_data.attack_type == AttackType.LIGHT:
            self.state = CharacterState.ATTACK_LIGHT
        elif attack_data.attack_type == AttackType.HEAVY:
            self.state = CharacterState.ATTACK_HEAVY
        elif attack_data.attack_type == AttackType.LOW:
            self.state = CharacterState.ATTACK_LOW
        
        # 攻击时减速
        self.vel_x *= 0.3
    
    # =========================================================================
    # 开始闪避
    # =========================================================================
    def start_dodge(self, direction: int):
        """开始闪避
        
        Args:
            direction: 闪避方向 (1为右, -1为左)
        """
        if self.dodge_cooldown > 0 or not self.is_grounded:
            return
        
        self.dodge_timer = 25
        self.dodge_cooldown = 60
        self.dodge_direction = direction
        self.state = CharacterState.DODGE
        self.invincible_timer = 25  # 全程无敌
        self.vel_x = direction * 12
    
    # =========================================================================
    # 开始必杀
    # =========================================================================
    def start_ultimate(self):
        """开始必杀技"""
        if self.rage < self.max_rage or self.is_ultimate:
            return
        
        self.rage = 0
        self.is_ultimate = True
        self.ultimate_timer = 90
        self.state = CharacterState.ULTIMATE
        self.current_attack = get_ultimate_attack()
        self.attack_timer = self.ultimate_timer
        self.has_hit = False
    
    # =========================================================================
    # 获取攻击碰撞盒
    # =========================================================================
    def get_attack_hitbox(self) -> Optional[pygame.Rect]:
        """获取当前攻击的碰撞盒
        
        Returns:
            pygame.Rect 或 None（如果不在攻击活跃帧）
        """
        if not self.current_attack or not self.is_attacking:
            return None
        
        attack = self.current_attack
        current_frame = attack.total_frames - self.attack_timer
        
        # 检查是否在活跃帧
        if not attack.is_active_frame(current_frame):
            return None
        
        # 计算碰撞盒
        return calculate_hitbox(
            attack,
            self.x, self.y,
            self.width, self.height,
            self.facing
        )
    
    # =========================================================================
    # 获取防御碰撞盒
    # =========================================================================
    def get_defense_hitbox(self) -> pygame.Rect:
        """获取防御碰撞盒
        
        Returns:
            pygame.Rect
        """
        is_crouching = self.state == CharacterState.CROUCH
        return get_defense_hitbox(
            self.x, self.y,
            self.width, self.height,
            is_crouching
        )
    
    # =========================================================================
    # 检查攻击命中
    # =========================================================================
    def check_attack_hit(
        self, 
        opponent: 'Character', 
        effects_list: list,
        screen_shake: ScreenShake
    ):
        """检查攻击是否命中对手
        
        Args:
            opponent: 对手角色
            effects_list: 特效列表（用于添加命中特效）
            screen_shake: 屏幕震动管理器
        """
        if not self.current_attack or self.has_hit or not self.is_attacking:
            return
        
        attack_hitbox = self.get_attack_hitbox()
        if not attack_hitbox:
            return
        
        defense_hitbox = opponent.get_defense_hitbox()
        
        # 碰撞检测
        if not attack_hitbox.colliderect(defense_hitbox):
            return
        
        attack = self.current_attack
        
        # 检查对手是否无敌
        if opponent.invincible_timer > 0:
            return
        
        # ========================================
        # 检查格挡
        # ========================================
        is_blocked = False
        is_perfect_block = False
        
        if opponent.is_blocking and attack.can_block:
            # 下段攻击无法被站立格挡
            if not attack.is_high and opponent.block_high:
                pass  # 攻击命中
            # 检查格挡方向（必须面对攻击者）
            elif (opponent.facing * -1) == self.facing:
                # 完美格挡判定（在短时间内按下格挡）
                if opponent.perfect_block_window > 0:
                    is_perfect_block = True
                is_blocked = True
        
        # ========================================
        # 格挡处理
        # ========================================
        if is_blocked:
            if is_perfect_block:
                # 完美格挡 - 弹反
                opponent.hitstun = 20
                opponent.vel_x = self.facing * -2
                opponent.perfect_block_window = 0
                opponent.is_blocking = False
                
                # 特效
                effects_list.append(HitSpark(
                    opponent.x + opponent.width / 2, 
                    opponent.y + opponent.height / 2, 
                    1.5
                ))
                screen_shake.trigger(8, 10)
                
                # 怒气
                opponent.rage = min(opponent.max_rage, opponent.rage + RAGE_PERFECT_BLOCK)
            else:
                # 普通格挡
                if opponent.block_high:
                    # 站立格挡 - 减伤80%
                    reduced_damage = int(attack.damage * 0.2)
                    opponent.health = max(0, opponent.health - reduced_damage)
                    opponent.hitstun = 5
                    effects_list.append(DamageNumber(
                        opponent.x + opponent.width / 2, 
                        opponent.y, 
                        reduced_damage, 
                        is_blocked=True
                    ))
                else:
                    # 下蹲格挡 - 减伤100%
                    effects_list.append(DamageNumber(
                        opponent.x + opponent.width / 2, 
                        opponent.y, 
                        0, 
                        is_blocked=True
                    ))
                
                # 格挡特效
                effects_list.append(HitSpark(
                    attack_hitbox.centerx, 
                    attack_hitbox.centery, 
                    0.5
                ))
                
                # 怒气
                self.rage = min(self.max_rage, self.rage + RAGE_ON_GUARD)
                opponent.rage = min(opponent.max_rage, opponent.rage + 8)
            
            # 破防检查
            if attack.guard_break and not is_perfect_block:
                is_blocked = False
        
        # ========================================
        # 命中处理
        # ========================================
        if not is_blocked:
            # 连击保护（连击数越高，伤害越低）
            combo_multiplier = max(
                COMBO_PROTECTION_START, 
                1.0 - opponent.hit_combo * COMBO_PROTECTION_PER_HIT
            )
            final_damage = int(attack.damage * combo_multiplier)
            
            # 应用伤害
            opponent.health = max(0, opponent.health - final_damage)
            opponent.hit_combo += 1
            opponent.combo_timer = 120
            
            # 更新最大连击
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
            
            # 特效
            opponent.hit_flash_timer = 8
            opponent.hit_flash_color = WHITE
            
            effects_list.append(DamageNumber(
                opponent.x + opponent.width / 2, 
                opponent.y, 
                final_damage, 
                is_crit=(attack.attack_type == AttackType.HEAVY)
            ))
            
            spark_intensity = 1.0 if attack.attack_type == AttackType.LIGHT else 2.0
            effects_list.append(HitSpark(
                attack_hitbox.centerx, 
                attack_hitbox.centery, 
                spark_intensity
            ))
            
            # 屏幕震动
            if attack.attack_type == AttackType.LIGHT:
                shake_intensity = 5
                shake_duration = 8
            elif attack.attack_type == AttackType.ULTIMATE:
                shake_intensity = 12
                shake_duration = 20
            else:
                shake_intensity = 10
                shake_duration = 15
            
            screen_shake.trigger(shake_intensity, shake_duration)
            
            # 怒气获取
            self.rage = min(self.max_rage, self.rage + RAGE_ON_HIT)
            opponent.rage = min(opponent.max_rage, opponent.rage + RAGE_ON_HIT_BY)
            
            # 状态
            opponent.state = CharacterState.HIT
            opponent.is_blocking = False
            
            # 必杀特效
            if attack.attack_type == AttackType.ULTIMATE:
                effects_list.append(UltimateWave(
                    self.x + self.width / 2, 
                    self.y + self.height / 2
                ))
        
        self.has_hit = True
    
    # =========================================================================
    # 更新逻辑
    # =========================================================================
    def update(self, opponent: 'Character'):
        """更新角色状态
        
        Args:
            opponent: 对手角色（用于朝向判断）
        """
        # ========================================
        # 朝向对手
        # ========================================
        if not self.is_attacking and self.hitstun <= 0 and self.dodge_timer <= 0:
            if opponent.x > self.x:
                self.facing = 1
            else:
                self.facing = -1
        
        # ========================================
        # 连击计时器
        # ========================================
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.hit_combo = 0
        
        # ========================================
        # 计时器更新
        # ========================================
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
        
        # ========================================
        # 攻击结束
        # ========================================
        if self.is_attacking and self.attack_timer <= 0:
            self.is_attacking = False
            self.current_attack = None
            if self.is_grounded and self.hitstun <= 0:
                self.state = CharacterState.IDLE
        
        # ========================================
        # 受击结束
        # ========================================
        if self.hitstun <= 0 and self.state == CharacterState.HIT:
            if not self.is_grounded:
                self.state = CharacterState.JUMP
            else:
                self.state = CharacterState.IDLE
        
        # ========================================
        # 闪避结束
        # ========================================
        if self.dodge_timer <= 0 and self.state == CharacterState.DODGE:
            if self.is_grounded:
                self.state = CharacterState.IDLE
        
        # ========================================
        # 物理更新
        # ========================================
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
        
        # 边界限制（安全的clamp）
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
        """渲染角色
        
        Args:
            surface: 渲染目标表面
            offset_x: X偏移（用于屏幕震动）
            offset_y: Y偏移（用于屏幕震动）
        """
        # 安全计算坐标
        x = int(clamp(self.x + offset_x, -100, 1300))
        y = int(clamp(self.y + offset_y, -100, 750))
        w = self.width
        h = self.height
        
        # ========================================
        # 受击闪烁
        # ========================================
        if self.hit_flash_timer > 0 and self.hit_flash_timer % 2 == 0:
            flash_color = self.hit_flash_color
        else:
            flash_color = None
        
        # ========================================
        # 无敌闪烁
        # ========================================
        is_invincible = self.invincible_timer > 0
        if is_invincible and self.invincible_timer % 6 < 3:
            temp_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            temp_surface.set_alpha(clamp_color(120))
            # 使用安全的颜色
            safe_white_alpha = with_alpha(WHITE, 100)
            pygame.draw.rect(temp_surface, safe_white_alpha, (0, 0, w, h))
            surface.blit(temp_surface, (x, y))
        
        # ========================================
        # 下蹲时的高度调整
        # ========================================
        render_h = h
        render_y = y
        if self.state == CharacterState.CROUCH:
            render_h = int(h * 0.6)
            render_y = y + h - render_h
        
        # ========================================
        # 选择身体颜色
        # ========================================
        if flash_color:
            body_color = flash_color
            body_color_dark = flash_color
        else:
            body_color = self.body_color
            body_color_dark = self.body_color_dark
        
        # ========================================
        # 身体阴影（安全的颜色）
        # ========================================
        shadow_surface = pygame.Surface((w + 20, 20), pygame.SRCALPHA)
        shadow_color = with_alpha(BLACK, 80)
        pygame.draw.ellipse(shadow_surface, shadow_color, (10, 5, w, 10))
        shadow_x = int(clamp(x - 10, -100, 1300))
        shadow_y = int(clamp(GROUND_Y - 10 + offset_y, 0, 700))
        surface.blit(shadow_surface, (shadow_x, shadow_y))
        
        # ========================================
        # 根据状态渲染不同姿态
        # ========================================
        self._render_by_state(surface, x, y, w, render_h, render_y, body_color, body_color_dark)
        
        # ========================================
        # 头部（使用安全的颜色）
        # ========================================
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
    
    # =========================================================================
    # 根据状态渲染
    # =========================================================================
    def _render_by_state(
        self, 
        surface: pygame.Surface,
        x: int, y: int, w: int, 
        render_h: int, render_y: int,
        body_color: Tuple[int, ...], 
        body_color_dark: Tuple[int, ...]
    ):
        """根据角色状态渲染不同姿态"""
        
        if self.state == CharacterState.DODGE:
            self._render_dodge(surface, x, render_h, render_y, body_color, body_color_dark)
        elif self.state == CharacterState.GROUNDED:
            self._render_grounded(surface, x, render_h, render_y, body_color, body_color_dark)
        elif self.state == CharacterState.ATTACK_LIGHT:
            self._render_attack_light(surface, x, render_h, render_y, body_color, body_color_dark)
        elif self.state == CharacterState.ATTACK_HEAVY:
            self._render_attack_heavy(surface, x, render_h, render_y, body_color, body_color_dark)
        elif self.state == CharacterState.ATTACK_LOW:
            self._render_attack_low(surface, x, render_h, render_y, body_color, body_color_dark)
        elif self.is_ultimate:
            self._render_ultimate(surface, x, render_h, render_y, body_color)
        elif self.state == CharacterState.BLOCK:
            self._render_block(surface, x, render_h, render_y, body_color, body_color_dark)
        else:
            self._render_idle(surface, x, render_h, render_y, body_color, body_color_dark)
    
    # =========================================================================
    # 各种姿态的具体渲染
    # =========================================================================
    def _render_idle(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """站立/行走姿态"""
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=10)
        pygame.draw.rect(surface, body_color_dark, (x + 6, render_y + 6, self.width - 12, render_h - 12), border_radius=8)
        
        # 装饰线
        pygame.draw.line(
            surface, self.accent_color,
            (x + self.width // 2, render_y + 10),
            (x + self.width // 2, render_y + render_h - 10),
            2
        )
    
    def _render_dodge(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """闪避姿态 - 横向压缩"""
        stretch_x = 0.7
        stretch_y = 1.2
        temp_width = max(1, int(self.width * stretch_x))
        temp_height = max(1, int(render_h * stretch_y))
        
        temp_surface = pygame.Surface((temp_width, temp_height), pygame.SRCALPHA)
        pygame.draw.rect(temp_surface, body_color, (0, 0, temp_width, temp_height), border_radius=8)
        pygame.draw.rect(temp_surface, body_color_dark, (2, 2, temp_width - 4, temp_height - 4), border_radius=6)
        
        draw_x = x + self.width // 2 - temp_width // 2
        draw_y = render_y + render_h - temp_height
        surface.blit(temp_surface, (draw_x, draw_y))
    
    def _render_grounded(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """倒地姿态"""
        pygame.draw.rect(surface, body_color, (x, render_y + render_h - 30, self.width, 30), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 3, render_y + render_h - 27, self.width - 6, 24), border_radius=6)
    
    def _render_attack_light(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """轻攻击姿态"""
        arm_extend = 30
        
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)
        
        # 拳头
        fist_x = x + self.width // 2 + self.facing * (self.width // 2 + arm_extend)
        pygame.draw.circle(surface, self.accent_color, (int(fist_x), render_y + render_h // 2), 12)
        pygame.draw.circle(surface, WHITE, (int(fist_x), render_y + render_h // 2), 8)
    
    def _render_attack_heavy(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """重攻击姿态"""
        arm_extend = 50
        
        # 蓄力效果
        if self.attack_timer > 20:
            charge_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            for i in range(3):
                # 安全的颜色和alpha
                charge_alpha = clamp_color(150 - i * 50)
                charge_color = with_alpha(ORANGE, charge_alpha)
                charge_radius = clamp_color(25 - i * 6)
                pygame.draw.circle(charge_surface, charge_color, (30, 30), charge_radius)
            
            surface.blit(charge_surface, (x + self.width // 2 - 30, render_y + render_h // 2 - 30))
        
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)
        
        # 重拳
        fist_x = x + self.width // 2 + self.facing * (self.width // 2 + arm_extend)
        pygame.draw.circle(surface, ORANGE, (int(fist_x), render_y + render_h // 2 - 10), 18)
        pygame.draw.circle(surface, YELLOW, (int(fist_x), render_y + render_h // 2 - 10), 12)
    
    def _render_attack_low(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """下段攻击姿态"""
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)
        
        # 下段攻击特效
        leg_x = x + self.width // 2 + self.facing * (self.width // 2 + 25)
        pygame.draw.rect(
            surface, self.accent_color,
            (int(leg_x - 15), int(render_y + render_h - 20), 40, 15),
            border_radius=5
        )
    
    def _render_ultimate(
        self, surface, x: int, render_h: int, render_y: int,
        body_color
    ):
        """必杀姿态"""
        import pygame.time as pg_time
        pulse_size = 30 + math.sin(pg_time.get_ticks() * 0.02) * 10
        
        # 能量场（安全的颜色）
        ultimate_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        for i in range(4):
            wave_alpha = clamp_color(200 - i * 40)
            wave_color = with_alpha(CYAN, wave_alpha)
            wave_radius = int(pulse_size + i * 15)
            wave_width = clamp_color(8 - i * 2)
            pygame.draw.circle(
                ultimate_surface, wave_color,
                (100, 100), wave_radius, width=wave_width
            )
        
        surface.blit(ultimate_surface, (x + self.width // 2 - 100, render_y + render_h // 2 - 100))
        
        # 身体（发光效果）
        pygame.draw.rect(surface, CYAN, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, WHITE, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)
    
    def _render_block(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        """格挡姿态"""
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)
        
        # 格挡护盾（安全的颜色）
        shield_surface = pygame.Surface((40, render_h + 20), pygame.SRCALPHA)
        shield_color = with_alpha(LIGHT_GRAY, 180)
        shield_highlight = with_alpha(WHITE, 150)
        
        pygame.draw.rect(shield_surface, shield_color, (5, 10, 30, render_h), border_radius=5)
        pygame.draw.rect(shield_surface, shield_highlight, (10, 15, 20, render_h - 10), border_radius=3)
        
        if self.facing > 0:
            surface.blit(shield_surface, (x + self.width, render_y - 10))
        else:
            surface.blit(shield_surface, (x - 40, render_y - 10))
