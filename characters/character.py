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
from attacks import (
    AttackData,
    get_light_attack, get_heavy_attack, get_low_attack, get_ultimate_attack,
    calculate_hitbox, get_defense_hitbox
)
from effects import Effect, DamageNumber, HitSpark, UltimateWave, ScreenShake


class Character:
    def __init__(self, x: float, y: float, is_player1: bool):
        self.x = x
        self.y = y
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT

        self.is_player1 = is_player1
        self.facing = 1 if is_player1 else -1

        self.state = CharacterState.IDLE

        self.max_health = MAX_HEALTH
        self.health = self.max_health
        self.max_rage = MAX_RAGE
        self.rage = 0

        self.jump_count = 0
        self.max_jumps = 2
        self.is_grounded = True

        self.current_attack: Optional[AttackData] = None
        self.attack_timer = 0
        self.has_hit = False
        self.is_attacking = False

        self.hitstun = 0
        self.is_launched = False
        self.is_grounded_hit = False
        self.grounded_timer = 0
        self.invincible_timer = 0

        self.is_blocking = False
        self.block_high = True
        self.perfect_block_window = 0

        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.dodge_direction = 0

        self.ultimate_timer = 0
        self.is_ultimate = False

        self.anim_frame = 0
        self.anim_timer = 0

        self.hit_combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.total_damage_dealt = 0

        self.hit_flash_timer = 0
        self.hit_flash_color: Optional[Tuple[int, ...]] = None

        if is_player1:
            self.body_color = PLAYER1_COLOR
            self.body_color_dark = PLAYER1_COLOR_DARK
            self.accent_color = PLAYER1_ACCENT
        else:
            self.body_color = PLAYER2_COLOR
            self.body_color_dark = PLAYER2_COLOR_DARK
            self.accent_color = PLAYER2_ACCENT

        self.is_ai = False
        self.difficulty = "easy"
        self.ai_timer = 0
        self.ai_attack_cooldown = 0

    def handle_input(self, keys, opponent: 'Character'):
        if self.is_ai:
            return

        move_input = 0
        self.is_blocking = False

        can_attack = (self.hitstun <= 0 and self.dodge_timer <= 0 and
                       self.grounded_timer <= 0 and not self.is_ultimate)

        if self.is_player1:
            if keys[pygame.K_a]:
                move_input = -1
            if keys[pygame.K_d]:
                move_input = 1

            if keys[pygame.K_w] and self.jump_count < self.max_jumps and can_attack:
                self.jump()

            if keys[pygame.K_s] and not self.is_attacking:
                self.state = CharacterState.CROUCH
                self.block_high = False

            if keys[pygame.K_j] and can_attack:
                self.start_attack(get_light_attack())
            if keys[pygame.K_k] and can_attack:
                self.start_attack(get_heavy_attack())

            if keys[pygame.K_l] and can_attack:
                if self.is_grounded:
                    self.is_blocking = True
                    self.state = CharacterState.BLOCK
                    self.block_high = not keys[pygame.K_s]

            if keys[pygame.K_SPACE] and self.rage >= self.max_rage and can_attack:
                self.start_ultimate()

            if keys[pygame.K_LSHIFT] and self.dodge_cooldown <= 0 and can_attack:
                dodge_dir = -self.facing if move_input == 0 else move_input
                self.start_dodge(dodge_dir)

        else:
            if keys[pygame.K_LEFT]:
                move_input = -1
            if keys[pygame.K_RIGHT]:
                move_input = 1

            if keys[pygame.K_UP] and self.jump_count < self.max_jumps and can_attack:
                self.jump()

            if keys[pygame.K_DOWN] and not self.is_attacking:
                self.state = CharacterState.CROUCH
                self.block_high = False

            if (keys[pygame.K_KP1] or keys[pygame.K_1]) and can_attack:
                self.start_attack(get_light_attack())
            if (keys[pygame.K_KP2] or keys[pygame.K_2]) and can_attack:
                self.start_attack(get_heavy_attack())

            if (keys[pygame.K_KP3] or keys[pygame.K_3]) and can_attack:
                if self.is_grounded:
                    self.is_blocking = True
                    self.state = CharacterState.BLOCK
                    self.block_high = not keys[pygame.K_DOWN]

            if keys[pygame.K_RETURN] and self.rage >= self.max_rage and can_attack:
                self.start_ultimate()

            if keys[pygame.K_RSHIFT] and self.dodge_cooldown <= 0 and can_attack:
                dodge_dir = -self.facing if move_input == 0 else move_input
                self.start_dodge(dodge_dir)

        if not self.is_blocking and not self.is_attacking:
            if self.dodge_timer <= 0:
                if move_input != 0:
                    self.vel_x = move_input * WALK_SPEED
                    if self.state != CharacterState.JUMP and self.is_grounded:
                        self.state = CharacterState.WALK
                else:
                    if self.is_grounded and self.state in [CharacterState.WALK, CharacterState.IDLE]:
                        self.state = CharacterState.IDLE

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
        self.attack_timer = attack_data.total_frames
        self.is_attacking = True
        self.has_hit = False

        if attack_data.attack_type == AttackType.LIGHT:
            self.state = CharacterState.ATTACK_LIGHT
        elif attack_data.attack_type == AttackType.HEAVY:
            self.state = CharacterState.ATTACK_HEAVY
        elif attack_data.attack_type == AttackType.LOW:
            self.state = CharacterState.ATTACK_LOW

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
        self.is_attacking = True
        self.ultimate_timer = 90
        self.state = CharacterState.ULTIMATE
        self.current_attack = get_ultimate_attack()
        self.attack_timer = self.current_attack.total_frames
        self.has_hit = False

    def get_attack_hitbox(self) -> Optional[pygame.Rect]:
        if not self.current_attack or not self.is_attacking:
            return None

        attack = self.current_attack
        current_frame = attack.total_frames - self.attack_timer

        if not attack.is_active_frame(current_frame):
            return None

        return calculate_hitbox(
            attack,
            self.x, self.y,
            self.width, self.height,
            self.facing
        )

    def get_defense_hitbox(self) -> pygame.Rect:
        is_crouching = self.state == CharacterState.CROUCH
        return get_defense_hitbox(
            self.x, self.y,
            self.width, self.height,
            is_crouching
        )

    def apply_damage(self, damage: int, attack: AttackData) -> int:
        self.health = max(0, self.health - damage)
        return damage

    def check_attack_hit(
        self,
        opponent: 'Character',
        effects_list: list,
        screen_shake: ScreenShake
    ):
        if not self.current_attack or self.has_hit or not self.is_attacking:
            return

        attack_hitbox = self.get_attack_hitbox()
        if not attack_hitbox:
            return

        defense_hitbox = opponent.get_defense_hitbox()

        if not attack_hitbox.colliderect(defense_hitbox):
            return

        attack = self.current_attack

        if opponent.invincible_timer > 0:
            return

        is_blocked = False
        is_perfect_block = False

        if opponent.is_blocking and attack.can_block:
            if not attack.is_high and opponent.block_high:
                pass
            elif (opponent.facing * -1) == self.facing:
                if opponent.perfect_block_window > 0:
                    is_perfect_block = True
                is_blocked = True

        if is_blocked:
            if is_perfect_block:
                opponent.hitstun = 20
                opponent.vel_x = self.facing * -2
                opponent.perfect_block_window = 0
                opponent.is_blocking = False

                effects_list.append(HitSpark(
                    opponent.x + opponent.width / 2,
                    opponent.y + opponent.height / 2,
                    1.5
                ))
                screen_shake.trigger(8, 10)

                opponent.rage = min(opponent.max_rage, opponent.rage + RAGE_PERFECT_BLOCK)
            else:
                if opponent.block_high:
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
                    effects_list.append(DamageNumber(
                        opponent.x + opponent.width / 2,
                        opponent.y,
                        0,
                        is_blocked=True
                    ))

                effects_list.append(HitSpark(
                    attack_hitbox.centerx,
                    attack_hitbox.centery,
                    0.5
                ))

                self.rage = min(self.max_rage, self.rage + RAGE_ON_GUARD)
                opponent.rage = min(opponent.max_rage, opponent.rage + 8)

            if attack.guard_break and not is_perfect_block:
                is_blocked = False

        if not is_blocked:
            combo_multiplier = max(
                COMBO_PROTECTION_START,
                1.0 - opponent.hit_combo * COMBO_PROTECTION_PER_HIT
            )
            final_damage = int(attack.damage * combo_multiplier)

            opponent.health = max(0, opponent.health - final_damage)
            opponent.hit_combo += 1
            opponent.combo_timer = 120

            if opponent.hit_combo > opponent.max_combo:
                opponent.max_combo = opponent.hit_combo

            self.total_damage_dealt += final_damage

            opponent.hitstun = attack.hitstun
            opponent.vel_x = self.facing * attack.knockback_x
            opponent.vel_y = attack.knockback_y
            opponent.is_grounded = False

            if attack.knockback_y < -5:
                opponent.is_launched = True
                opponent.jump_count = opponent.max_jumps

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

            self.rage = min(self.max_rage, self.rage + RAGE_ON_HIT)
            opponent.rage = min(opponent.max_rage, opponent.rage + RAGE_ON_HIT_BY)

            opponent.state = CharacterState.HIT
            opponent.is_blocking = False

            if attack.attack_type == AttackType.ULTIMATE:
                effects_list.append(UltimateWave(
                    self.x + self.width / 2,
                    self.y + self.height / 2
                ))

        self.has_hit = True

    def update(self, opponent: 'Character'):
        if not self.is_attacking and self.hitstun <= 0 and self.dodge_timer <= 0:
            if opponent.x > self.x:
                self.facing = 1
            else:
                self.facing = -1

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.hit_combo = 0

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

        if self.is_attacking and self.attack_timer <= 0:
            self.is_attacking = False
            self.current_attack = None
            if self.is_grounded and self.hitstun <= 0:
                self.state = CharacterState.IDLE

        if self.hitstun <= 0 and self.state == CharacterState.HIT:
            if not self.is_grounded:
                self.state = CharacterState.JUMP
            else:
                self.state = CharacterState.IDLE

        if self.dodge_timer <= 0 and self.state == CharacterState.DODGE:
            if self.is_grounded:
                self.state = CharacterState.IDLE

        if not self.is_grounded:
            self.vel_y += GRAVITY
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED

        self.x += self.vel_x
        self.y += self.vel_y

        ground_level = GROUND_Y - self.height
        if self.y >= ground_level:
            self.y = ground_level

            if not self.is_grounded:
                self.is_grounded = True
                self.jump_count = 0

                if self.is_launched or self.vel_y > 10:
                    self.is_launched = False
                    self.is_grounded_hit = True
                    self.grounded_timer = 40
                    self.invincible_timer = 30
                    self.state = CharacterState.GROUNDED

            if self.state == CharacterState.JUMP:
                self.state = CharacterState.IDLE
        else:
            self.is_grounded = False

        if not self.is_grounded:
            self.state = CharacterState.JUMP

        if self.hitstun > 0:
            self.vel_x *= 0.9
        elif self.dodge_timer > 0:
            self.vel_x *= 0.95
        elif not self.is_attacking:
            if abs(self.vel_x) > 0.5:
                self.vel_x *= FRICTION
            else:
                self.vel_x = 0

        self.x = clamp(self.x, BOUNDARY_MARGIN, SCREEN_WIDTH - self.width - BOUNDARY_MARGIN)

        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        x = int(clamp(self.x + offset_x, -100, 1300))
        y = int(clamp(self.y + offset_y, -100, 750))
        w = self.width
        h = self.height

        if self.hit_flash_timer > 0 and self.hit_flash_timer % 2 == 0:
            flash_color = self.hit_flash_color
        else:
            flash_color = None

        is_invincible = self.invincible_timer > 0
        if is_invincible and self.invincible_timer % 6 < 3:
            temp_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            temp_surface.set_alpha(clamp_color(120))
            safe_white_alpha = with_alpha(WHITE, 100)
            pygame.draw.rect(temp_surface, safe_white_alpha, (0, 0, w, h))
            surface.blit(temp_surface, (x, y))

        render_h = h
        render_y = y
        if self.state == CharacterState.CROUCH:
            render_h = int(h * 0.6)
            render_y = y + h - render_h

        if flash_color:
            body_color = flash_color
            body_color_dark = flash_color
        else:
            body_color = self.body_color
            body_color_dark = self.body_color_dark

        shadow_surface = pygame.Surface((w + 20, 20), pygame.SRCALPHA)
        shadow_color = with_alpha(BLACK, 80)
        pygame.draw.ellipse(shadow_surface, shadow_color, (10, 5, w, 10))
        shadow_x = int(clamp(x - 10, -100, 1300))
        shadow_y = int(clamp(GROUND_Y - 10 + offset_y, 0, 700))
        surface.blit(shadow_surface, (shadow_x, shadow_y))

        self._render_by_state(surface, x, y, w, render_h, render_y, body_color, body_color_dark)

        head_x = x + w // 2
        head_y = render_y + 15
        head_radius = 18

        pygame.draw.circle(surface, body_color, (head_x, head_y), head_radius)
        pygame.draw.circle(surface, body_color_dark, (head_x, head_y), head_radius - 3)

        eye_offset_x = 5 * self.facing
        eye_y = head_y - 2
        pygame.draw.circle(surface, WHITE, (head_x + eye_offset_x, eye_y), 4)
        pygame.draw.circle(surface, BLACK, (head_x + eye_offset_x + self.facing, eye_y), 2)

    def _render_by_state(
        self,
        surface: pygame.Surface,
        x: int, y: int, w: int,
        render_h: int, render_y: int,
        body_color: Tuple[int, ...],
        body_color_dark: Tuple[int, ...]
    ):
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

    def _render_idle(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=10)
        pygame.draw.rect(surface, body_color_dark, (x + 6, render_y + 6, self.width - 12, render_h - 12), border_radius=8)

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
        pygame.draw.rect(surface, body_color, (x, render_y + render_h - 30, self.width, 30), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 3, render_y + render_h - 27, self.width - 6, 24), border_radius=6)

    def _render_attack_light(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        arm_extend = 30

        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

        fist_x = x + self.width // 2 + self.facing * (self.width // 2 + arm_extend)
        pygame.draw.circle(surface, self.accent_color, (int(fist_x), render_y + render_h // 2), 12)
        pygame.draw.circle(surface, WHITE, (int(fist_x), render_y + render_h // 2), 8)

    def _render_attack_heavy(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        arm_extend = 50

        if self.attack_timer > 20:
            charge_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            for i in range(3):
                charge_alpha = clamp_color(150 - i * 50)
                charge_color = with_alpha(ORANGE, charge_alpha)
                charge_radius = clamp_color(25 - i * 6)
                pygame.draw.circle(charge_surface, charge_color, (30, 30), charge_radius)

            surface.blit(charge_surface, (x + self.width // 2 - 30, render_y + render_h // 2 - 30))

        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

        fist_x = x + self.width // 2 + self.facing * (self.width // 2 + arm_extend)
        pygame.draw.circle(surface, ORANGE, (int(fist_x), render_y + render_h // 2 - 10), 18)
        pygame.draw.circle(surface, YELLOW, (int(fist_x), render_y + render_h // 2 - 10), 12)

    def _render_attack_low(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

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
        import pygame.time as pg_time
        pulse_size = 30 + math.sin(pg_time.get_ticks() * 0.02) * 10

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

        pygame.draw.rect(surface, CYAN, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, WHITE, (x + 8, render_y + 8, self.width - 16, render_h - 16), border_radius=6)

    def _render_block(
        self, surface, x: int, render_h: int, render_y: int,
        body_color, body_color_dark
    ):
        pygame.draw.rect(surface, body_color, (x, render_y, self.width, render_h), border_radius=8)
        pygame.draw.rect(surface, body_color_dark, (x + 5, render_y + 5, self.width - 10, render_h - 10), border_radius=6)

        shield_surface = pygame.Surface((40, render_h + 20), pygame.SRCALPHA)
        shield_color = with_alpha(LIGHT_GRAY, 180)
        shield_highlight = with_alpha(WHITE, 150)

        pygame.draw.rect(shield_surface, shield_color, (5, 10, 30, render_h), border_radius=5)
        pygame.draw.rect(shield_surface, shield_highlight, (10, 15, 20, render_h - 10), border_radius=3)

        if self.facing > 0:
            surface.blit(shield_surface, (x + self.width, render_y - 10))
        else:
            surface.blit(shield_surface, (x - 40, render_y - 10))
