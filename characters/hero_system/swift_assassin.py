import math
from typing import Optional, Tuple, List
import pygame

from config import (
    CharacterState, AttackType,
    PLAYER_WIDTH, PLAYER_HEIGHT,
    WALK_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    MAX_HEALTH, MAX_RAGE,
    WHITE, BLACK, PURPLE, DARK_GRAY, GRAY, YELLOW, ORANGE,
    clamp_color, with_alpha, clamp, SCREEN_WIDTH, BOUNDARY_MARGIN
)
from attacks import (
    AttackData, get_light_attack, get_heavy_attack, get_low_attack
)
from characters.hero_system.character_types import HeroType, SkillType
from characters.hero_system.hero_base import HeroCharacter, HeroStats, SkillData


class SwiftAssassin(HeroCharacter):
    def __init__(self, x: float, y: float, is_player1: bool):
        super().__init__(x, y, is_player1, HeroType.SWIFT_ASSASSIN)
        self.width = int(PLAYER_WIDTH * 0.85)
        self.height = int(PLAYER_HEIGHT * 1.05)
        self._blink_positions: List[Tuple[float, float, int]] = []
        self._slash_count = 0
        self._slash_timer = 0
        self._is_blinking = False
        self._blink_target_x = 0.0

    def _get_default_stats(self) -> HeroStats:
        return HeroStats(
            max_health=int(MAX_HEALTH * 0.75),
            max_rage=int(MAX_RAGE * 1.2),
            walk_speed=WALK_SPEED * 1.5,
            attack_multiplier=1.2,
            defense_multiplier=0.75,
            jump_force=JUMP_FORCE * 1.15,
            double_jump_force=DOUBLE_JUMP_FORCE * 1.15
        )

    def get_special_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.SPECIAL_SKILL,
            name="瞬身闪袭",
            description="瞬间向前无敌位移，并对路径上的敌人造成伤害",
            damage=160,
            cooldown=120,
            startup_frames=5,
            active_frames=15,
            recovery_frames=15,
            hitstun=30,
            knockback_x=8.0,
            knockback_y=-2.0,
            is_high=True,
            can_block=True,
            special_effects={
                "blink_distance": 200,
                "invincible_duration": 25,
                "path_damage": True
            }
        )

    def get_ultimate_skill(self) -> SkillData:
        return SkillData(
            skill_type=SkillType.ULTIMATE,
            name="暗影连斩",
            description="身形化作残影，连续多段斩击飞敌人",
            damage=320,
            startup_frames=15,
            active_frames=60,
            recovery_frames=40,
            hitstun=80,
            knockback_x=12.0,
            knockback_y=-22.0,
            can_block=False,
            guard_break=True,
            special_effects={
                "slash_count": 6,
                "slash_interval": 8,
                "teleport_between_slashes": True
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
        self._is_blinking = True

        special_effects = skill.special_effects
        blink_distance = special_effects.get("blink_distance", 180)
        self._blink_target_x = self.x + self.facing * blink_distance
        self._blink_target_x = clamp(self._blink_target_x, BOUNDARY_MARGIN,
                                      SCREEN_WIDTH - self.width - BOUNDARY_MARGIN)

        self._blink_positions = [(self.x, self.y, 10)]

        invincible_duration = special_effects.get("invincible_duration", 25)
        self.invincible_timer = invincible_duration

        attack_data = skill.to_attack_data()
        attack_data.hitbox_x = 0
        attack_data.hitbox_y = -20
        attack_data.hitbox_w = 120
        attack_data.hitbox_h = 120
        self.current_attack = attack_data
        self.attack_timer = skill.total_frames

    def start_ultimate(self):
        if self.rage < self.max_rage or self.is_ultimate:
            return

        self.rage = 0
        self.is_ultimate = True
        self.is_attacking = True
        self._slash_count = 0
        self._slash_timer = 0
        self._blink_positions = []

        ultimate_skill = self.get_ultimate_skill()
        self.ultimate_timer = ultimate_skill.total_frames + 30
        self.state = CharacterState.ULTIMATE

        attack_data = ultimate_skill.to_attack_data()
        attack_data.hitbox_x = -30
        attack_data.hitbox_y = -30
        attack_data.hitbox_w = 120
        attack_data.hitbox_h = 140
        self.current_attack = attack_data
        self.attack_timer = attack_data.total_frames
        self.has_hit = False

        self.invincible_timer = ultimate_skill.total_frames + 30

    def update(self, opponent: 'HeroCharacter'):
        if self._blink_positions:
            new_positions = []
            for pos in self._blink_positions:
                x, y, timer = pos
                if timer > 0:
                    new_positions.append((x, y, timer - 1))
            self._blink_positions = new_positions

        if self._is_blinking and self.current_special_skill:
            current_frame = self.current_special_skill.total_frames - self.special_skill_timer
            if current_frame < 8:
                progress = current_frame / 8
                start_x = self._blink_positions[0][0] if self._blink_positions else self.x
                self.x = start_x + (self._blink_target_x - start_x) * progress
                if current_frame % 2 == 0:
                    self._blink_positions.append((self.x, self.y, 12))
            elif current_frame == 8:
                self.x = self._blink_target_x
                self._is_blinking = False

        if self.is_ultimate:
            ultimate_skill = self.get_ultimate_skill()
            special_effects = ultimate_skill.special_effects
            slash_interval = special_effects.get("slash_interval", 8)
            max_slashes = special_effects.get("slash_count", 6)

            self._slash_timer += 1
            if self._slash_timer >= slash_interval and self._slash_count < max_slashes:
                self._slash_count += 1
                self._slash_timer = 0
                self.has_hit = False

                if special_effects.get("teleport_between_slashes", True):
                    if opponent:
                        teleport_offset = (150 if self._slash_count % 2 == 0 else -80)
                        new_x = opponent.x + self.facing * teleport_offset
                        new_x = clamp(new_x, BOUNDARY_MARGIN, SCREEN_WIDTH - self.width - BOUNDARY_MARGIN)
                        self._blink_positions.append((self.x, self.y, 15))
                        self.x = new_x

                        if opponent.x > self.x:
                            self.facing = 1
                        else:
                            self.facing = -1

        super().update(opponent)

    def _render_special_skill(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        import pygame.time as pg_time

        for i, (pos_x, pos_y, timer) in enumerate(self._blink_positions):
            if timer > 0:
                alpha = clamp_color(int(timer / 12 * 150))
                after_image_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                after_image_color = with_alpha(PURPLE, alpha)
                pygame.draw.rect(after_image_surface, after_image_color,
                               (0, 0, self.width, render_h), border_radius=8)
                surface.blit(after_image_surface, (int(pos_x), int(pos_y)))

        if self._is_blinking:
            current_frame = self.current_special_skill.total_frames - self.special_skill_timer if self.current_special_skill else 0
            if current_frame < 8:
                motion_lines_surface = pygame.Surface((250, render_h), pygame.SRCALPHA)
                for i in range(5):
                    line_alpha = clamp_color(180 - i * 30)
                    line_color = with_alpha(PURPLE, line_alpha)
                    line_y = render_h // 2 - 40 + i * 20
                    line_length = 80 - i * 12
                    if self.facing > 0:
                        pygame.draw.line(motion_lines_surface, line_color,
                                       (0, line_y), (line_length, line_y), 4 - i)
                    else:
                        pygame.draw.line(motion_lines_surface, line_color,
                                       (250, line_y), (250 - line_length, line_y), 4 - i)

                if self.facing > 0:
                    surface.blit(motion_lines_surface, (x - 100, render_y))
                else:
                    surface.blit(motion_lines_surface, (x - 150 + self.width, render_y))

        pygame.draw.rect(surface, PURPLE, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, self.accent_color, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

        hand_x = x + self.width // 2 + self.facing * (self.width // 2 + 15)
        pygame.draw.line(surface, YELLOW,
                        (int(hand_x), int(render_y + render_h // 2 - 20)),
                        (int(hand_x + self.facing * 35), int(render_y + render_h // 2 + 10)), 4)

    def _render_ultimate(
        self, surface, x: int, render_h: int, render_y: int,
        body_color
    ):
        import pygame.time as pg_time
        from config import GROUND_Y

        for i, (pos_x, pos_y, timer) in enumerate(self._blink_positions):
            if timer > 0:
                alpha = clamp_color(int(timer / 15 * 180))
                after_image_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                after_image_color = with_alpha(PURPLE, alpha)
                pygame.draw.rect(after_image_surface, after_image_color,
                               (0, 0, self.width, render_h), border_radius=8)
                surface.blit(after_image_surface, (int(pos_x), int(pos_y)))

        if self._slash_count > 0:
            slash_surface = pygame.Surface((200, 150), pygame.SRCALPHA)
            for slash in range(min(self._slash_count, 6)):
                slash_angle = slash * (math.pi / 3)
                slash_alpha = clamp_color(200 - slash * 20)
                slash_color = with_alpha(PURPLE, slash_alpha)
                edge_color = with_alpha(self.accent_color, int(slash_alpha * 1.2))

                slash_length = 70
                start_x = 100
                start_y = 75
                end_x = start_x + math.cos(slash_angle) * slash_length
                end_y = start_y + math.sin(slash_angle) * slash_length

                pygame.draw.line(slash_surface, slash_color,
                               (int(start_x), int(start_y)),
                               (int(end_x), int(end_y)), 6)
                pygame.draw.line(slash_surface, edge_color,
                               (int(start_x), int(start_y)),
                               (int(end_x), int(end_y)), 2)

            surface.blit(slash_surface, (x + self.width // 2 - 100, render_y + render_h // 2 - 75))

        ultimate_surface = pygame.Surface((220, 220), pygame.SRCALPHA)
        pulse_size = 60 + math.sin(pg_time.get_ticks() * 0.025) * 15
        for i in range(4):
            wave_alpha = clamp_color(180 - i * 35)
            wave_color = with_alpha(PURPLE, wave_alpha)
            wave_radius = int(pulse_size + i * 18)
            pygame.draw.circle(ultimate_surface, wave_color,
                             (110, 110), wave_radius, width=max(1, 8 - i * 2))

        surface.blit(ultimate_surface, (x + self.width // 2 - 110, render_y + render_h // 2 - 110))

        pygame.draw.rect(surface, PURPLE, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, self.accent_color, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)

        for hand_offset in [-20, 20]:
            hand_x = x + self.width // 2 + hand_offset
            pygame.draw.line(surface, YELLOW,
                            (int(hand_x), int(render_y + render_h // 2 - 30)),
                            (int(hand_x + hand_offset * 2), int(render_y + render_h // 2 + 20)), 5)
