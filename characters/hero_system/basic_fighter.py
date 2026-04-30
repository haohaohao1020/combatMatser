import math
from typing import Optional, Tuple
import pygame

from config import (
    CharacterState, AttackType,
    PLAYER_WIDTH, PLAYER_HEIGHT,
    WALK_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    MAX_HEALTH, MAX_RAGE,
    WHITE, BLACK, ORANGE, YELLOW, CYAN,
    clamp_color, with_alpha
)
from attacks import (
    AttackData, get_light_attack, get_heavy_attack, get_low_attack
)
from characters.hero_system.character_types import HeroType, SkillType
from characters.hero_system.hero_base import HeroCharacter, HeroStats, SkillData


class BasicFighter(HeroCharacter):
    def __init__(self, x: float, y: float, is_player1: bool):
        super().__init__(x, y, is_player1, HeroType.BASIC_FIGHTER)

    def _get_default_stats(self) -> HeroStats:
        return HeroStats(
            max_health=MAX_HEALTH,
            max_rage=MAX_RAGE,
            walk_speed=WALK_SPEED,
            attack_multiplier=1.0,
            defense_multiplier=1.0,
            jump_force=JUMP_FORCE,
            double_jump_force=DOUBLE_JUMP_FORCE
        )

    def get_special_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.SPECIAL_SKILL,
            name="旋风斩",
            description="原地旋转攻击，对周围敌人造成伤害",
            damage=150,
            cooldown=150,
            startup_frames=12,
            active_frames=25,
            recovery_frames=20,
            hitstun=35,
            knockback_x=6.0,
            knockback_y=-3.0,
            is_high=True,
            can_block=True
        )

    def get_ultimate_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.ULTIMATE,
            name="极限爆发",
            description="释放全身力量，造成大范围爆发伤害",
            damage=380,
            startup_frames=20,
            active_frames=40,
            recovery_frames=50,
            hitstun=60,
            knockback_x=18.0,
            knockback_y=-20.0,
            can_block=False,
            guard_break=True
        )

    def start_special_skill(self):
        if self.special_skill_cooldown > 0:
            return

        skill = self.get_special_skill()
        self.current_special_skill = skill
        self.special_skill_max_cooldown = skill.cooldown
        self.special_skill_cooldown = skill.cooldown
        self.is_using_special = True
        self.special_skill_timer = skill.total_frames
        self.is_attacking = True
        self.has_hit = False

        attack_data = skill.to_attack_data()
        attack_data.hitbox_x = -40
        attack_data.hitbox_y = -20
        attack_data.hitbox_w = 140
        attack_data.hitbox_h = 120
        self.current_attack = attack_data
        self.attack_timer = skill.total_frames

    def start_ultimate(self):
        if self.rage < self.max_rage or self.is_ultimate:
            return

        self.rage = 0
        self.is_ultimate = True
        self.is_attacking = True

        ultimate_skill = self.get_ultimate_skill()
        self.ultimate_timer = ultimate_skill.total_frames + 30
        self.state = CharacterState.ULTIMATE

        attack_data = ultimate_skill.to_attack_data()
        attack_data.hitbox_x = -80
        attack_data.hitbox_y = -50
        attack_data.hitbox_w = 220
        attack_data.hitbox_h = 160
        self.current_attack = attack_data
        self.attack_timer = attack_data.total_frames
        self.has_hit = False

    def _render_special_skill(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        import pygame.time as pg_time
        current_frame = self.current_special_skill.total_frames - self.special_skill_timer if self.current_special_skill else 0

        if 5 <= current_frame < 25:
            spin_surface = pygame.Surface((160, 160), pygame.SRCALPHA)
            spin_angle = pg_time.get_ticks() * 0.015
            for i in range(6):
                angle = spin_angle + i * (math.pi / 3)
                radius = 40 + math.sin(current_frame * 0.3) * 10
                slice_x = 80 + math.cos(angle) * radius
                slice_y = 80 + math.sin(angle) * radius
                slice_alpha = clamp_color(180)
                slice_color = with_alpha(self.accent_color, slice_alpha)
                pygame.draw.circle(spin_surface, slice_color, (int(slice_x), int(slice_y)), 15)
            surface.blit(spin_surface, (x + self.width // 2 - 80, render_y + render_h // 2 - 80))

        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

    def _render_ultimate(
        self, surface, x: int, render_h: int, render_y: int,
        body_color
    ):
        import pygame.time as pg_time
        current_frame = self.ultimate_timer
        pulse_size = 50 + math.sin(pg_time.get_ticks() * 0.02) * 15

        ultimate_surface = pygame.Surface((280, 280), pygame.SRCALPHA)
        for i in range(5):
            wave_alpha = clamp_color(220 - i * 40)
            wave_color = with_alpha(self.accent_color, wave_alpha)
            wave_radius = int(pulse_size + i * 20)
            wave_width = clamp_color(10 - i * 2)
            pygame.draw.circle(
                ultimate_surface, wave_color,
                (140, 140), wave_radius, width=wave_width
            )

        for i in range(8):
            ray_angle = pg_time.get_ticks() * 0.005 + i * (math.pi / 4)
            ray_length = 80 + math.sin(pg_time.get_ticks() * 0.01 + i) * 20
            ray_start_x = 140
            ray_start_y = 140
            ray_end_x = 140 + math.cos(ray_angle) * ray_length
            ray_end_y = 140 + math.sin(ray_angle) * ray_length
            ray_color = with_alpha(YELLOW, 150)
            pygame.draw.line(ultimate_surface, ray_color, (int(ray_start_x), int(ray_start_y)),
                           (int(ray_end_x), int(ray_end_y)), 4)

        surface.blit(ultimate_surface, (x + self.width // 2 - 140, render_y + render_h // 2 - 140))

        pygame.draw.rect(surface, self.accent_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, WHITE, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)
