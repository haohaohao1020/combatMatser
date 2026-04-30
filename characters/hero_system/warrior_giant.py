import math
from typing import Optional, Tuple
import pygame

from config import (
    CharacterState, AttackType,
    PLAYER_WIDTH, PLAYER_HEIGHT,
    WALK_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    MAX_HEALTH, MAX_RAGE,
    WHITE, BLACK, ORANGE, YELLOW, RED, DARK_RED,
    clamp_color, with_alpha, clamp, SCREEN_WIDTH, BOUNDARY_MARGIN
)
from attacks import (
    AttackData, get_light_attack, get_heavy_attack, get_low_attack
)
from characters.hero_system.character_types import HeroType, SkillType
from characters.hero_system.hero_base import HeroCharacter, HeroStats, SkillData


class WarriorGiant(HeroCharacter):
    def __init__(self, x: float, y: float, is_player1: bool):
        super().__init__(x, y, is_player1, HeroType.WARRIOR_GIANT)
        self.width = int(PLAYER_WIDTH * 1.3)
        self.height = int(PLAYER_HEIGHT * 1.15)
        self._charge_timer = 0
        self._is_charging = False
        self._charge_level = 0

    def _get_default_stats(self) -> HeroStats:
        return HeroStats(
            max_health=int(MAX_HEALTH * 1.5),
            max_rage=int(MAX_RAGE * 0.9),
            walk_speed=WALK_SPEED * 0.7,
            attack_multiplier=1.4,
            defense_multiplier=1.6,
            jump_force=JUMP_FORCE * 0.85,
            double_jump_force=DOUBLE_JUMP_FORCE * 0.85
        )

    def get_special_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.SPECIAL_SKILL,
            name="野蛮冲撞",
            description="向前冲刺，对敌人造成伤害并击退",
            damage=180,
            cooldown=180,
            startup_frames=8,
            active_frames=30,
            recovery_frames=25,
            hitstun=40,
            knockback_x=12.0,
            knockback_y=-4.0,
            is_high=True,
            can_block=False,
            guard_break=True,
            special_effects={
                "dash_speed": 18.0,
                "dash_frames": 25,
                "invincible_during_dash": True
            }
        )

    def get_ultimate_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.ULTIMATE,
            name="撼地重击",
            description="蓄力砸地，触发范围冲击波，震飞周围对手",
            damage=420,
            startup_frames=30,
            active_frames=50,
            recovery_frames=60,
            hitstun=70,
            knockback_x=20.0,
            knockback_y=-25.0,
            can_block=False,
            guard_break=True,
            special_effects={
                "charge_time": 25,
                "shockwave_radius": 150,
                "aoe_damage": True
            }
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
        attack_data.hitbox_x = 0
        attack_data.hitbox_y = -10
        attack_data.hitbox_w = 100
        attack_data.hitbox_h = 100
        self.current_attack = attack_data
        self.attack_timer = skill.total_frames

        special_effects = skill.special_effects
        self.vel_x = self.facing * special_effects.get("dash_speed", 15.0)
        if special_effects.get("invincible_during_dash", False):
            self.invincible_timer = special_effects.get("dash_frames", 20)

    def start_ultimate(self):
        if self.rage < self.max_rage or self.is_ultimate:
            return

        self.rage = 0
        self.is_ultimate = True
        self.is_attacking = True
        self._is_charging = True
        self._charge_level = 0

        ultimate_skill = self.get_ultimate_skill()
        self.ultimate_timer = ultimate_skill.total_frames + 40
        self.state = CharacterState.ULTIMATE

        attack_data = ultimate_skill.to_attack_data()
        attack_data.hitbox_x = -100
        attack_data.hitbox_y = -80
        attack_data.hitbox_w = 280
        attack_data.hitbox_h = 200
        self.current_attack = attack_data
        self.attack_timer = attack_data.total_frames
        self.has_hit = False

    def update(self, opponent: 'HeroCharacter'):
        if self.is_using_special and self.current_special_skill:
            special_effects = self.current_special_skill.special_effects
            dash_frames = special_effects.get("dash_frames", 20)
            current_frame = self.current_special_skill.total_frames - self.special_skill_timer
            if current_frame < dash_frames:
                self.vel_x = self.facing * special_effects.get("dash_speed", 15.0)
                self.state = CharacterState.ATTACK_HEAVY
            elif current_frame < dash_frames + 5:
                self.vel_x *= 0.8

        if self._is_charging:
            self._charge_level += 1
            if self._charge_level >= 25:
                self._is_charging = False
                self._charge_level = 25

        super().update(opponent)

    def _render_special_skill(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        import pygame.time as pg_time
        current_frame = self.current_special_skill.total_frames - self.special_skill_timer if self.current_special_skill else 0

        if 0 <= current_frame < 25:
            trail_surface = pygame.Surface((120, render_h + 20), pygame.SRCALPHA)
            for i in range(5):
                trail_alpha = clamp_color(100 - i * 20)
                trail_color = with_alpha(ORANGE, trail_alpha)
                trail_offset_x = -i * 20 * self.facing
                if self.facing > 0:
                    trail_rect = pygame.Rect(0 + trail_offset_x, 10, 30 - i * 5, render_h)
                else:
                    trail_rect = pygame.Rect(120 + trail_offset_x - 30 + i * 5, 10, 30 - i * 5, render_h)
                pygame.draw.rect(trail_surface, trail_color, trail_rect, border_radius=5)

            if self.facing > 0:
                surface.blit(trail_surface, (x - 80, render_y - 10))
            else:
                surface.blit(trail_surface, (x + self.width - 40, render_y - 10))

        pygame.draw.rect(surface, ORANGE, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, YELLOW, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)

        fist_x = x + self.width // 2 + self.facing * (self.width // 2 + 20)
        pygame.draw.circle(surface, RED, (int(fist_x), render_y + render_h // 2), 20)
        pygame.draw.circle(surface, ORANGE, (int(fist_x), render_y + render_h // 2), 15)

    def _render_ultimate(
        self, surface, x: int, render_h: int, render_y: int,
        body_color
    ):
        import pygame.time as pg_time
        from config import GROUND_Y

        current_frame = self.ultimate_timer

        if self._is_charging or current_frame > 80:
            charge_pulse = math.sin(pg_time.get_ticks() * 0.01) * 0.3 + 0.7
            charge_size = 40 + self._charge_level * 2
            charge_surface = pygame.Surface((charge_size * 2 + 40, charge_size * 2 + 40), pygame.SRCALPHA)

            for i in range(4):
                layer_alpha = clamp_color(int(200 - i * 40 * charge_pulse))
                layer_color = with_alpha(ORANGE, layer_alpha)
                layer_radius = int(charge_size - i * 10 + math.sin(pg_time.get_ticks() * 0.005 + i) * 5)
                pygame.draw.circle(charge_surface, layer_color,
                                 (charge_size + 20, charge_size + 20), layer_radius,
                                 width=max(1, 8 - i * 2))

            center_color = with_alpha(YELLOW, 200)
            pygame.draw.circle(charge_surface, center_color,
                             (charge_size + 20, charge_size + 20),
                             int(15 + self._charge_level * 0.3))

            surface.blit(charge_surface,
                        (x + self.width // 2 - charge_size - 20,
                         render_y + render_h // 2 - charge_size - 20))

        if not self._is_charging and current_frame <= 80:
            shockwave_radius = 150 - current_frame
            if shockwave_radius > 0:
                shockwave_surface = pygame.Surface((400, 200), pygame.SRCALPHA)

                wave_alpha = clamp_color(int(current_frame / 80 * 200))
                wave_color = with_alpha(ORANGE, wave_alpha)
                edge_color = with_alpha(YELLOW, int(wave_alpha * 1.5))

                ground_y_shock = 160
                for i in range(3):
                    radius = int(shockwave_radius - i * 20)
                    if radius > 0:
                        pygame.draw.ellipse(
                            shockwave_surface,
                            with_alpha(wave_color, max(0, 180 - i * 50)),
                            (200 - radius, ground_y_shock - 15, radius * 2, 30),
                            width=max(1, 8 - i * 2)
                        )

                crack_count = min(8, int((150 - shockwave_radius) / 10))
                for i in range(crack_count):
                    angle = (i / crack_count) * math.pi * 2
                    crack_length = 30 + math.sin(pg_time.get_ticks() * 0.01 + i) * 10
                    crack_start_x = 200 + math.cos(angle) * 20
                    crack_start_y = ground_y_shock
                    crack_end_x = 200 + math.cos(angle) * (20 + crack_length)
                    crack_end_y = ground_y_shock + math.sin(angle) * 5
                    crack_color = with_alpha(DARK_RED, 150)
                    pygame.draw.line(shockwave_surface, crack_color,
                                   (int(crack_start_x), int(crack_start_y)),
                                   (int(crack_end_x), int(crack_end_y)), 3)

                surface.blit(shockwave_surface, (x + self.width // 2 - 200, render_y + render_h - 80))

        pygame.draw.rect(surface, ORANGE, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, RED, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)

        if not self._is_charging:
            arm_down_y = render_y + render_h - 20
            pygame.draw.rect(surface, body_color,
                           (x + self.width // 2 - 15, render_y + render_h // 2, 30, render_h // 2),
                           border_radius=5)
            fist_y = render_y + render_h + 10
            pygame.draw.circle(surface, YELLOW, (int(x + self.width // 2), min(fist_y, GROUND_Y - 10)), 25)
            pygame.draw.circle(surface, ORANGE, (int(x + self.width // 2), min(fist_y, GROUND_Y - 10)), 18)
