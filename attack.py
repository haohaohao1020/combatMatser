#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 攻击数据模块
定义所有攻击类型的数据结构和属性
"""

from dataclasses import dataclass
from typing import Optional
import pygame

from config import (
    AttackType,
    LIGHT_ATTACK_DAMAGE,
    HEAVY_ATTACK_DAMAGE,
    LOW_ATTACK_DAMAGE,
    ULTIMATE_DAMAGE
)


@dataclass
class AttackData:
    """攻击数据类，包含所有攻击相关的参数"""
    # 攻击标识
    attack_type: AttackType
    
    # 伤害
    damage: int
    
    # 碰撞盒（相对于角色中心的偏移）
    hitbox_x: int      # X偏移
    hitbox_y: int      # Y偏移
    hitbox_w: int      # 宽度
    hitbox_h: int      # 高度
    
    # 帧数据
    startup_frames: int     # 前摇帧数
    active_frames: int      # 活跃帧数
    recovery_frames: int    # 后摇帧数
    
    # 受击效果
    hitstun: int            # 硬直帧数
    knockback_x: float      # X方向击退
    knockback_y: float      # Y方向击退（负值为向上）
    
    # 特殊属性
    is_high: bool = True            # 是否为上段攻击
    can_block: bool = True          # 是否可被格挡
    guard_break: bool = False       # 是否破防
    
    @property
    def total_frames(self) -> int:
        """获取攻击总帧数"""
        return self.startup_frames + self.active_frames + self.recovery_frames
    
    def is_active_frame(self, current_frame: int) -> bool:
        """检查当前帧是否为攻击活跃帧"""
        return self.startup_frames <= current_frame < self.startup_frames + self.active_frames
    
    def is_startup_frame(self, current_frame: int) -> bool:
        """检查当前帧是否为前摇帧"""
        return current_frame < self.startup_frames
    
    def is_recovery_frame(self, current_frame: int) -> bool:
        """检查当前帧是否为后摇帧"""
        return current_frame >= self.startup_frames + self.active_frames


# =============================================================================
# 预定义的攻击数据
# =============================================================================

def get_light_attack() -> AttackData:
    """
    轻攻击
    - 快速出招、小伤害
    - 短前摇短后摇
    - 可衔接连招
    """
    return AttackData(
        attack_type=AttackType.LIGHT,
        damage=LIGHT_ATTACK_DAMAGE,
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


def get_heavy_attack() -> AttackData:
    """
    重攻击
    - 高伤害
    - 长前摇
    - 击飞效果
    - 可破防
    """
    return AttackData(
        attack_type=AttackType.HEAVY,
        damage=HEAVY_ATTACK_DAMAGE,
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


def get_low_attack() -> AttackData:
    """
    下段攻击
    - 只能击中下蹲或站立敌人
    - 无法格挡
    """
    return AttackData(
        attack_type=AttackType.LOW,
        damage=LOW_ATTACK_DAMAGE,
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


def get_ultimate_attack() -> AttackData:
    """
    必杀技
    - 大范围伤害
    - 高伤害
    - 强制击飞
    - 无法格挡
    - 全屏特效
    """
    return AttackData(
        attack_type=AttackType.ULTIMATE,
        damage=ULTIMATE_DAMAGE,
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


# =============================================================================
# 攻击碰撞盒计算
# =============================================================================

def calculate_hitbox(
    attack: AttackData,
    player_x: float,
    player_y: float,
    player_width: float,
    player_height: float,
    facing: int
) -> Optional[pygame.Rect]:
    """
    根据攻击数据和角色位置计算实际的碰撞盒
    
    Args:
        attack: 攻击数据
        player_x: 角色X坐标
        player_y: 角色Y坐标
        player_width: 角色宽度
        player_height: 角色高度
        facing: 朝向 (1为右, -1为左)
    
    Returns:
        pygame.Rect: 碰撞盒，如果方向不对则返回None
    """
    # 计算角色中心
    center_x = player_x + player_width / 2
    center_y = player_y + player_height / 2
    
    # 根据朝向计算X偏移
    if facing > 0:
        # 朝右
        hb_x = center_x + attack.hitbox_x
    else:
        # 朝左 - 碰撞盒需要镜像
        hb_x = center_x - attack.hitbox_x - attack.hitbox_w
    
    hb_y = player_y + attack.hitbox_y
    
    return pygame.Rect(hb_x, hb_y, attack.hitbox_w, attack.hitbox_h)


def get_defense_hitbox(
    player_x: float,
    player_y: float,
    player_width: float,
    player_height: float,
    is_crouching: bool
) -> pygame.Rect:
    """
    获取角色的防御碰撞盒
    
    Args:
        player_x: 角色X坐标
        player_y: 角色Y坐标
        player_width: 角色宽度
        player_height: 角色高度
        is_crouching: 是否下蹲
    
    Returns:
        pygame.Rect: 防御碰撞盒
    """
    if is_crouching:
        # 下蹲时碰撞盒高度降低
        return pygame.Rect(
            player_x, 
            player_y + player_height * 0.4,  # 从40%高度开始
            player_width, 
            player_height * 0.6  # 只有60%高度
        )
    
    return pygame.Rect(player_x, player_y, player_width, player_height)
