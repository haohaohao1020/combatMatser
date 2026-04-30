import math
from typing import Optional, Tuple, Dict, Any
import pygame

from config import (
    CharacterState, AttackType,
    PLAYER_WIDTH, PLAYER_HEIGHT,
    WALK_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    MAX_HEALTH, MAX_RAGE,
    WHITE, BLACK, GREEN, YELLOW, ORANGE, CYAN, BLUE, DARK_GRAY,
    clamp_color, with_alpha, clamp, SCREEN_WIDTH, BOUNDARY_MARGIN, GROUND_Y
)
from attacks import (
    AttackData, get_light_attack, get_heavy_attack, get_low_attack
)
from effects import DamageNumber, ScreenShake
from characters.hero_system.character_types import HeroType, SkillType
from characters.hero_system.hero_base import HeroCharacter, HeroStats, SkillData


class MysticMage(HeroCharacter):
    def __init__(self, x: float, y: float, is_player1: bool):
        super().__init__(x, y, is_player1, HeroType.MYSTIC_MAGE)
        self.width = int(PLAYER_WIDTH * 0.9)
        self.height = int(PLAYER_HEIGHT * 1.0)
        self._orb_projectiles: list = []
        self._lightning_strikes: list = []
        self._barrier_active = False
        self._barrier_timer = 0
        self._root_target_timer = 0
        self._spell_charge_level = 0

    def _get_default_stats(self) -> HeroStats:
        return HeroStats(
            max_health=int(MAX_HEALTH * 0.85),
            max_rage=int(MAX_RAGE * 1.3),
            walk_speed=WALK_SPEED * 0.9,
            attack_multiplier=1.15,
            defense_multiplier=0.85,
            jump_force=JUMP_FORCE * 1.0,
            double_jump_force=DOUBLE_JUMP_FORCE * 1.0
        )

    def get_special_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.SPECIAL_SKILL,
            name="元气禁锢",
            description="释放光波法阵，命中后定住对手几秒",
            damage=100,
            cooldown=200,
            startup_frames=10,
            active_frames=40,
            recovery_frames=25,
            hitstun=20,
            knockback_x=0.0,
            knockback_y=0.0,
            is_high=True,
            can_block=True,
            is_ranged=True,
            projectile_speed=8.0,
            special_effects={
                "root_duration": 120,
                "projectile_range": 400,
                "slow_effect": True
            }
        )

    def get_ultimate_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.ULTIMATE,
            name="雷霆结界",
            description="召唤大范围雷电法阵，持续造成多段伤害",
            damage=60,
            startup_frames=20,
            active_frames=120,
            recovery_frames=50,
            hitstun=15,
            knockback_x=3.0,
            knockback_y=-5.0,
            can_block=False,
            guard_break=True,
            special_effects={
                "barrier_radius": 180,
                "tick_interval": 15,
                "total_ticks": 8,
                "stun_on_last_tick": True
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
        self._spell_charge_level = 0

        special_effects = skill.special_effects
        projectile_speed = special_effects.get("projectile_speed", 8.0)
        projectile_range = special_effects.get("projectile_range", 400)

        self._orb_projectiles.append({
            "x": self.x + self.width // 2,
            "y": self.y + self.height // 2,
            "vel_x": self.facing * projectile_speed,
            "vel_y": 0,
            "damage": skill.damage,
            "range": projectile_range,
            "start_x": self.x + self.width // 2,
            "active": True,
            "root_duration": special_effects.get("root_duration", 120)
        })

        attack_data = skill.to_attack_data()
        attack_data.hitbox_x = -50
        attack_data.hitbox_y = -50
        attack_data.hitbox_w = 160
        attack_data.hitbox_h = 160
        self.current_attack = attack_data
        self.attack_timer = skill.total_frames

    def start_ultimate(self):
        if self.rage < self.max_rage or self.is_ultimate:
            return

        self.rage = 0
        self.is_ultimate = True
        self.is_attacking = True
        self._barrier_active = True
        self._barrier_timer = 0
        self._lightning_strikes = []

        ultimate_skill = self.get_ultimate_skill()
        self.ultimate_timer = ultimate_skill.total_frames + 30
        self.state = CharacterState.ULTIMATE

        attack_data = ultimate_skill.to_attack_data()
        attack_data.hitbox_x = -120
        attack_data.hitbox_y = -100
        attack_data.hitbox_w = 300
        attack_data.hitbox_h = 220
        self.current_attack = attack_data
        self.attack_timer = attack_data.total_frames
        self.has_hit = False

    def check_attack_hit(
        self,
        opponent: 'HeroCharacter',
        effects_list: list,
        screen_shake: 'ScreenShake'
    ):
        super().check_attack_hit(opponent, effects_list, screen_shake)

        for orb in self._orb_projectiles:
            if not orb["active"]:
                continue

            orb_rect = pygame.Rect(orb["x"] - 25, orb["y"] - 25, 50, 50)
            opp_rect = opponent.get_defense_hitbox()

            if orb_rect.colliderect(opp_rect) and opponent.invincible_timer <= 0:
                if opponent.is_blocking and self.current_special_skill:
                    if not self.current_special_skill.can_block:
                        pass
                    else:
                        opponent.apply_damage(int(orb["damage"] * 0.3), self.current_attack)
                        orb["active"] = False
                        continue

                actual_damage = opponent.apply_damage(orb["damage"], self.current_attack)
                opponent.hitstun = 15
                opponent.rooted_timer = orb.get("root_duration", 120)
                opponent.vel_x = 0
                opponent.vel_y = 0

                effects_list.append(DamageNumber(
                    opponent.x + opponent.width / 2,
                    opponent.y,
                    actual_damage
                ))

                screen_shake.trigger(6, 10)
                orb["active"] = False

    def update(self, opponent: 'HeroCharacter'):
        new_orbs = []
        for orb in self._orb_projectiles:
            if not orb["active"]:
                continue

            orb["x"] += orb["vel_x"]
            orb["y"] += orb["vel_y"]

            if abs(orb["x"] - orb["start_x"]) > orb["range"]:
                orb["active"] = False

            if orb["active"]:
                new_orbs.append(orb)

        self._orb_projectiles = new_orbs

        if self.is_using_special:
            self._spell_charge_level += 1
            if self._spell_charge_level > 30:
                self._spell_charge_level = 30

        if self._barrier_active:
            self._barrier_timer += 1
            ultimate_skill = self.get_ultimate_skill()
            special_effects = ultimate_skill.special_effects
            tick_interval = special_effects.get("tick_interval", 15)

            if self._barrier_timer % tick_interval == 0:
                self.has_hit = False
                for _ in range(3):
                    strike_angle = self._barrier_timer * 0.1 + math.pi * 2 * (_ / 3)
                    barrier_radius = special_effects.get("barrier_radius", 180)
                    strike_x = self.x + self.width // 2 + math.cos(strike_angle) * (barrier_radius * 0.6)
                    strike_y = self.y + self.height // 2
                    self._lightning_strikes.append({
                        "x": strike_x,
                        "y": strike_y,
                        "timer": 20,
                        "branch": _
                    })

        new_strikes = []
        for strike in self._lightning_strikes:
            strike["timer"] -= 1
            if strike["timer"] > 0:
                new_strikes.append(strike)
        self._lightning_strikes = new_strikes

        if self._barrier_timer > 120:
            self._barrier_active = False

        super().update(opponent)

    def _render_special_skill(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        import pygame.time as pg_time

        for orb in self._orb_projectiles:
            if not orb["active"]:
                continue

            orb_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
            pulse_size = 25 + math.sin(pg_time.get_ticks() * 0.02) * 5

            for i in range(4):
                orb_alpha = clamp_color(200 - i * 40)
                orb_color = with_alpha(GREEN, orb_alpha)
                orb_radius = int(pulse_size + i * 8)
                pygame.draw.circle(orb_surface, orb_color, (40, 40), orb_radius,
                                 width=max(1, 8 - i * 2))

            core_color = with_alpha(YELLOW, 200)
            pygame.draw.circle(orb_surface, core_color, (40, 40), 15)

            surface.blit(orb_surface, (int(orb["x"] - 40), int(orb["y"] - 40)))

            rune_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            rune_alpha = clamp_color(150)
            rune_color = with_alpha(self.accent_color, rune_alpha)
            for rune_i in range(6):
                rune_angle = rune_i * (math.pi / 3) + pg_time.get_ticks() * 0.002
                rune_x = 30 + math.cos(rune_angle) * 22
                rune_y = 30 + math.sin(rune_angle) * 22
                pygame.draw.circle(rune_surface, rune_color, (int(rune_x), int(rune_y)), 4)

            surface.blit(rune_surface, (int(orb["x"] - 30), int(orb["y"] - 30)))

        if self.is_using_special:
            charge_pulse = self._spell_charge_level / 30
            hand_x = x + self.width // 2 + self.facing * (self.width // 2)
            hand_y = render_y + render_h // 2

            charge_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            for i in range(3):
                charge_alpha = clamp_color(int(180 * charge_pulse - i * 40))
                if charge_alpha > 0:
                    charge_color = with_alpha(GREEN, charge_alpha)
                    charge_radius = int(10 + charge_pulse * 15 + i * 5)
                    pygame.draw.circle(charge_surface, charge_color, (30, 30), charge_radius,
                                     width=max(1, 6 - i))

            surface.blit(charge_surface, (int(hand_x + self.facing * 10 - 30), int(hand_y - 30)))

        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

        pygame.draw.line(
            surface, self.accent_color,
            (x + self.width // 2, render_y + 15),
            (x + self.width // 2, render_y + render_h - 15),
            3
        )

    def _render_ultimate(
        self, surface, x: int, render_h: int, render_y: int,
        body_color
    ):
        import pygame.time as pg_time
        from config import GROUND_Y

        ultimate_skill = self.get_ultimate_skill()
        special_effects = ultimate_skill.special_effects
        barrier_radius = special_effects.get("barrier_radius", 180)

        center_x = x + self.width // 2
        center_y = render_y + render_h // 2

        if self._barrier_active:
            barrier_surface = pygame.Surface((barrier_radius * 2 + 100, barrier_radius * 2 + 100), pygame.SRCALPHA)
            barrier_center_x = barrier_radius + 50
            barrier_center_y = barrier_radius + 50

            pulse_size = barrier_radius + math.sin(pg_time.get_ticks() * 0.015) * 15

            for i in range(5):
                barrier_alpha = clamp_color(180 - i * 30)
                barrier_color = with_alpha(GREEN, barrier_alpha)
                edge_color = with_alpha(self.accent_color, int(barrier_alpha * 1.2))

                wave_radius = int(pulse_size - i * 25)
                if wave_radius > 0:
                    pygame.draw.ellipse(
                        barrier_surface,
                        barrier_color,
                        (barrier_center_x - wave_radius, barrier_center_y + 50,
                         wave_radius * 2, 60),
                        width=max(1, 8 - i * 2)
                    )
                    pygame.draw.ellipse(
                        barrier_surface,
                        edge_color,
                        (barrier_center_x - wave_radius, barrier_center_y + 50,
                         wave_radius * 2, 60),
                        width=max(1, 3 - i)
                    )

            rune_count = 12
            for rune_i in range(rune_count):
                rune_angle = rune_i * (math.pi * 2 / rune_count) + pg_time.get_ticks() * 0.001
                rune_x = barrier_center_x + math.cos(rune_angle) * (barrier_radius - 20)
                rune_y = barrier_center_y + 50 + math.sin(rune_angle) * 20
                rune_alpha = clamp_color(200)
                rune_color = with_alpha(YELLOW, rune_alpha)
                pygame.draw.circle(barrier_surface, rune_color, (int(rune_x), int(rune_y)), 6)
                pygame.draw.circle(barrier_surface, with_alpha(WHITE, 150), (int(rune_x), int(rune_y)), 3)

            surface.blit(barrier_surface,
                        (int(center_x - barrier_radius - 50),
                         int(center_y - barrier_radius - 50)))

        for strike in self._lightning_strikes:
            lightning_surface = pygame.Surface((100, 300), pygame.SRCALPHA)
            strike_alpha = clamp_color(int(strike["timer"] / 20 * 255))
            lightning_color = with_alpha(YELLOW, strike_alpha)
            lightning_core = with_alpha(WHITE, strike_alpha)

            start_x = 50
            start_y = 0
            end_x = 50 + math.sin(strike["timer"] * 0.5 + strike["branch"]) * 20
            end_y = 300

            points = [(start_x, start_y)]
            segments = 8
            for seg in range(1, segments):
                seg_y = start_y + (end_y - start_y) * (seg / segments)
                seg_x = start_x + (end_x - start_x) * (seg / segments)
                seg_x += math.sin(seg * 1.5 + strike["branch"]) * 15
                points.append((seg_x, seg_y))
            points.append((end_x, end_y))

            pygame.draw.lines(lightning_surface, lightning_color, False,
                            [(int(p[0]), int(p[1])) for p in points], 6)
            pygame.draw.lines(lightning_surface, lightning_core, False,
                            [(int(p[0]), int(p[1])) for p in points], 2)

            surface.blit(lightning_surface, (int(strike["x"] - 50), int(render_y - 200)))

            ground_hit_surface = pygame.Surface((60, 30), pygame.SRCALPHA)
            hit_color = with_alpha(YELLOW, strike_alpha)
            pygame.draw.ellipse(ground_hit_surface, hit_color, (5, 5, 50, 20))
            surface.blit(ground_hit_surface, (int(strike["x"] - 30), int(GROUND_Y - 20)))

        pygame.draw.rect(surface, GREEN, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, self.accent_color, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)

        hand_offsets = [-25, 25]
        for offset in hand_offsets:
            hand_x = x + self.width // 2 + offset
            hand_y = render_y + render_h // 2 - 30

            orb_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            orb_alpha = clamp_color(200)
            orb_color = with_alpha(GREEN, orb_alpha)
            core_color = with_alpha(YELLOW, 200)

            pygame.draw.circle(orb_surface, orb_color, (20, 20), 15)
            pygame.draw.circle(orb_surface, core_color, (20, 20), 8)

            surface.blit(orb_surface, (int(hand_x - 20), int(hand_y - 20)))
