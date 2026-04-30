from typing import Optional
import pygame

from config import (
    AttackType,
    LIGHT_ATTACK_DAMAGE,
    HEAVY_ATTACK_DAMAGE,
    LOW_ATTACK_DAMAGE,
    ULTIMATE_DAMAGE
)
from attacks.attack_data import AttackData


def get_light_attack() -> AttackData:
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
        knockback_x=4,
        knockback_y=-5,
        is_high=True,
        can_block=True,
        guard_break=True
    )


def get_low_attack() -> AttackData:
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


def calculate_hitbox(
    attack: AttackData,
    player_x: float,
    player_y: float,
    player_width: float,
    player_height: float,
    facing: int
) -> Optional[pygame.Rect]:
    center_x = player_x + player_width / 2
    center_y = player_y + player_height / 2

    if facing > 0:
        hb_x = center_x + attack.hitbox_x
    else:
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
    if is_crouching:
        return pygame.Rect(
            player_x,
            player_y + player_height * 0.4,
            player_width,
            player_height * 0.6
        )

    return pygame.Rect(player_x, player_y, player_width, player_height)
