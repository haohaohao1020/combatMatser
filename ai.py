#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - AI逻辑模块
实现智能的AI对战逻辑，支持简单和困难两种难度
"""

import random
from typing import Optional

from config import (
    CharacterState, WALK_SPEED,
    clamp
)
from character import Character
from attack import (
    get_light_attack, get_heavy_attack, get_low_attack
)


# =============================================================================
# AI控制器类
# =============================================================================
class AIController:
    """AI控制器，控制角色的AI行为"""
    
    def __init__(self, character: Character, difficulty: str = "easy"):
        """
        初始化AI控制器
        
        Args:
            character: 要控制的角色
            difficulty: 难度 ("easy" 或 "hard")
        """
        self.character = character
        self.difficulty = difficulty
        self.ai_timer = 0
        
        # 设置角色为AI
        self.character.is_ai = True
        self.character.difficulty = difficulty
    
    # =========================================================================
    # 难度参数
    # =========================================================================
    def _get_difficulty_params(self) -> dict:
        """根据难度获取AI参数"""
        if self.difficulty == "easy":
            return {
                "reaction_time": 30,           # 反应时间（帧数）- 较慢
                "block_chance": 0.2,           # 格挡概率
                "dodge_chance": 0.1,           # 闪避概率
                "attack_chance": 0.02,         # 攻击概率
                "combo_chance": 0.3,           # 连招概率
                "crouch_chance": 0.2,          # 下蹲躲避概率
                "move_smartness": 0.5,         # 移动智能程度
            }
        else:  # hard
            return {
                "reaction_time": 8,            # 反应时间 - 很快
                "block_chance": 0.6,           # 高格挡概率
                "dodge_chance": 0.3,           # 高闪避概率
                "attack_chance": 0.05,         # 高频攻击
                "combo_chance": 0.7,           # 高连招概率
                "crouch_chance": 0.4,          # 高中段躲避
                "move_smartness": 0.9,         # 高移动智能
            }
    
    # =========================================================================
    # 主更新函数
    # =========================================================================
    def update(self, opponent: Character):
        """
        更新AI逻辑
        
        Args:
            opponent: 对手角色
        """
        char = self.character
        
        # 检查是否可以操作
        if char.hitstun > 0 or char.grounded_timer > 0:
            return
        if char.dodge_timer > 0:
            return
        if char.is_attacking:
            return
        if char.is_ultimate:
            return
        
        self.ai_timer += 1
        params = self._get_difficulty_params()
        
        # 计算距离和方向
        dist_x = opponent.x - char.x
        abs_dist_x = abs(dist_x)
        target_facing = 1 if dist_x > 0 else -1
        
        # 设置朝向（始终面对对手）
        char.facing = target_facing
        
        # ========================================
        # 1. 怒气满必放必杀
        # ========================================
        if char.rage >= char.max_rage and self.ai_timer % 10 == 0:
            char.start_ultimate()
            return
        
        # ========================================
        # 2. 对手攻击时的反应
        # ========================================
        if opponent.is_attacking and opponent.current_attack:
            attack = opponent.current_attack
            in_range = abs_dist_x < (attack.hitbox_w + char.width)
            
            if in_range and self.ai_timer % params["reaction_time"] == 0:
                # 上段攻击可以下蹲躲避
                if attack.is_high and random.random() < params["crouch_chance"]:
                    char.state = CharacterState.CROUCH
                    char.block_high = False
                    return
                
                # 尝试格挡
                if random.random() < params["block_chance"] and char.is_grounded:
                    char.is_blocking = True
                    char.state = CharacterState.BLOCK
                    # 困难AI更容易完美格挡
                    if self.difficulty == "hard":
                        char.perfect_block_window = 12
                    return
                
                # 尝试闪避
                if random.random() < params["dodge_chance"] and char.dodge_cooldown <= 0:
                    # 闪避方向：远离对手
                    dodge_dir = -target_facing
                    char.start_dodge(dodge_dir)
                    return
        
        # ========================================
        # 3. 移动逻辑 - 保持最佳攻击距离
        # ========================================
        ideal_range = 80  # 理想攻击距离
        move_toward = False
        move_away = False
        
        if abs_dist_x < ideal_range - 20:
            move_away = True
        elif abs_dist_x > ideal_range + 40:
            move_toward = True
        
        # 根据智能程度决定
        if random.random() < params["move_smartness"]:
            if move_toward:
                char.vel_x = target_facing * WALK_SPEED
                if char.is_grounded:
                    char.state = CharacterState.WALK
            elif move_away:
                char.vel_x = target_facing * -WALK_SPEED * 0.7
                if char.is_grounded:
                    char.state = CharacterState.WALK
            else:
                if char.is_grounded and char.state == CharacterState.WALK:
                    char.state = CharacterState.IDLE
        else:
            # 简单AI偶尔随机移动
            if random.random() < 0.02:
                if char.is_grounded:
                    char.vel_x = random.choice([-WALK_SPEED, 0, WALK_SPEED])
                    if char.vel_x != 0:
                        char.state = CharacterState.WALK
        
        # ========================================
        # 4. 攻击逻辑
        # ========================================
        attack_range = 100
        if abs_dist_x < attack_range and char.is_grounded:
            char.ai_attack_cooldown = max(0, char.ai_attack_cooldown - 1)
            
            if char.ai_attack_cooldown <= 0:
                roll = random.random()
                
                if roll < params["attack_chance"] * 0.6:
                    # 轻攻击
                    char.start_attack(get_light_attack())
                    # 简单AI冷却更长
                    char.ai_attack_cooldown = 60 if self.difficulty == "easy" else 40
                    
                elif roll < params["attack_chance"] * 0.85:
                    # 重攻击
                    char.start_attack(get_heavy_attack())
                    char.ai_attack_cooldown = 80 if self.difficulty == "easy" else 60
                    
                elif roll < params["attack_chance"]:
                    # 下段攻击
                    char.start_attack(get_low_attack())
                    char.ai_attack_cooldown = 70 if self.difficulty == "easy" else 50
        
        # ========================================
        # 5. 困难AI额外行为
        # ========================================
        if self.difficulty == "hard":
            # 跳跃压制
            if char.is_grounded and abs_dist_x < 200 and random.random() < 0.005:
                char.jump()
            
            # 绕后走位
            if char.is_grounded and abs_dist_x < 150 and random.random() < 0.01:
                # 尝试绕到对手后方
                if opponent.vel_x > 0:
                    char.vel_x = -WALK_SPEED
                else:
                    char.vel_x = WALK_SPEED


# =============================================================================
# 便捷函数：为角色添加AI控制
# =============================================================================
def add_ai_to_character(character: Character, difficulty: str = "easy") -> AIController:
    """
    为角色添加AI控制
    
    Args:
        character: 要控制的角色
        difficulty: 难度 ("easy" 或 "hard")
    
    Returns:
        AIController: AI控制器实例
    """
    return AIController(character, difficulty)
