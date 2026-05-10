import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from config import (
    SCREEN_WIDTH, GROUND_Y, PLAYER_HEIGHT, PLAYER_WIDTH, BOUNDARY_MARGIN,
    MAX_HEALTH, MAX_RAGE, FPS,
    ENDLESS_BASE_SCORE, ENDLESS_COMBO_BONUS_MULTIPLIER,
    ENDLESS_WAVE_BONUS_MULTIPLIER, ENDLESS_SURVIVAL_BONUS_PER_SECOND,
    ENDLESS_WAVE_TRANSITION_FRAMES, ENDLESS_WAVE_HEAL_AMOUNT,
    ENDLESS_WAVE_ENERGY_RESTORE,
    EndlessDifficulty, GameState, CharacterState,
    RED, DARK_RED, PINK, ORANGE, YELLOW, WHITE
)
from characters import Character, AIController, add_ai_to_character


@dataclass
class EndlessEnemy:
    character: Character
    ai_controller: AIController
    difficulty_multiplier: float = 1.0
    spawn_index: int = 0
    is_active: bool = True


@dataclass
class EndlessStats:
    current_wave: int = 1
    total_kills: int = 0
    current_combo_kills: int = 0
    max_combo_kills: int = 0
    max_combo: int = 0
    combo_timer: int = 0
    score: int = 0
    survival_frames: int = 0
    wave_kills: int = 0
    wave_enemies_total: int = 0

    gold_reward: int = 0
    exp_reward: int = 0
    talent_points_reward: int = 0


class EndlessModeManager:
    def __init__(self):
        self.difficulty = EndlessDifficulty()
        self.stats = EndlessStats()
        self.enemies: List[EndlessEnemy] = []
        self.player: Optional[Character] = None

        self.transition_timer = 0
        self.is_transitioning = False
        self.transition_message = ""

        self.frame_count = 0
        self.is_running = False

    def reset(self):
        self.difficulty.reset()
        self.stats = EndlessStats()
        self.enemies.clear()
        self.player = None
        self.transition_timer = 0
        self.is_transitioning = False
        self.frame_count = 0
        self.is_running = False

    def start(self, player: Character):
        self.reset()
        self.player = player
        self.is_running = True
        self._spawn_wave_enemies()
        self.is_transitioning = True
        self.transition_timer = ENDLESS_WAVE_TRANSITION_FRAMES
        self.transition_message = f"WAVE {self.stats.current_wave}"

    def _spawn_wave_enemies(self):
        enemy_count = self.difficulty.get_enemy_count()
        self.stats.wave_enemies_total = enemy_count
        self.stats.wave_kills = 0

        spawn_positions = self._get_spawn_positions(enemy_count)

        for i, pos in enumerate(spawn_positions):
            enemy = self._create_enemy(pos, i)
            self.enemies.append(enemy)

    def _get_spawn_positions(self, count: int) -> List[float]:
        positions = []
        margin = BOUNDARY_MARGIN + PLAYER_WIDTH

        if count == 1:
            positions.append(SCREEN_WIDTH - margin - PLAYER_WIDTH)
        elif count == 2:
            positions.append(SCREEN_WIDTH - margin - PLAYER_WIDTH)
            positions.append(margin)
        elif count >= 3:
            spacing = (SCREEN_WIDTH - 2 * margin - PLAYER_WIDTH) // (count - 1)
            for i in range(count):
                pos = margin + i * spacing
                positions.append(pos)

        random.shuffle(positions)
        return positions

    def _create_enemy(self, x: float, index: int) -> EndlessEnemy:
        ground_y = GROUND_Y - PLAYER_HEIGHT
        character = Character(x, ground_y, is_player1=False)

        ai_params = self.difficulty.get_ai_params()
        health_mult = self.difficulty.get_health_multiplier()

        character.max_health = int(MAX_HEALTH * health_mult)
        character.health = character.max_health

        character.is_ai = True
        character.ai_difficulty_params = ai_params

        ai_controller = add_ai_to_character(character, "easy")
        ai_controller._dynamic_params = ai_params

        return EndlessEnemy(
            character=character,
            ai_controller=ai_controller,
            difficulty_multiplier=health_mult,
            spawn_index=index
        )

    def update(self, player: Character) -> Optional[str]:
        if not self.is_running:
            return None

        self.frame_count += 1
        self.stats.survival_frames += 1

        if self.frame_count % FPS == 0:
            self.difficulty.add_survival_time(1)
            self.stats.score += ENDLESS_SURVIVAL_BONUS_PER_SECOND

        if self.stats.combo_timer > 0:
            self.stats.combo_timer -= 1
            if self.stats.combo_timer <= 0:
                self.stats.current_combo_kills = 0

        if self.is_transitioning:
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.is_transitioning = False
            return "transition"

        self._update_enemies(player)

        dead_enemies = [e for e in self.enemies if e.character.health <= 0 and e.is_active]
        for enemy in dead_enemies:
            self._on_enemy_death(enemy)

        self.enemies = [e for e in self.enemies if e.is_active]

        if self._is_wave_clear():
            self._start_next_wave(player)
            return "wave_complete"

        if player.health <= 0:
            self.is_running = False
            self._calculate_final_rewards()
            return "game_over"

        return None

    def _update_enemies(self, player: Character):
        for enemy in self.enemies:
            if not enemy.is_active:
                continue

            char = enemy.character

            other_targets = [e.character for e in self.enemies if e != enemy and e.is_active]
            all_targets = [player] + other_targets

            nearest_target = self._find_nearest_target(char, all_targets)

            if nearest_target:
                if enemy.ai_controller and nearest_target == player:
                    enemy.ai_controller.update(player)
                else:
                    self._simple_ai_update(char, nearest_target)

            char.update(nearest_target if nearest_target else player)

    def _find_nearest_target(self, enemy: Character, targets: List[Character]) -> Optional[Character]:
        if not targets:
            return None

        nearest = None
        min_dist = float('inf')

        for target in targets:
            if target.health <= 0:
                continue
            dist = abs(target.x - enemy.x)
            if dist < min_dist:
                min_dist = dist
                nearest = target

        return nearest

    def _simple_ai_update(self, char: Character, target: Character):
        from attacks import get_light_attack, get_heavy_attack, get_low_attack
        from config import WALK_SPEED, clamp

        if char.hitstun > 0 or char.grounded_timer > 0:
            return
        if char.dodge_timer > 0 or char.is_attacking or char.is_ultimate:
            return

        dist_x = target.x - char.x
        abs_dist_x = abs(dist_x)
        target_facing = 1 if dist_x > 0 else -1

        char.facing = target_facing

        ideal_range = 80
        if abs_dist_x < ideal_range - 20:
            char.vel_x = target_facing * -WALK_SPEED * 0.7
            if char.is_grounded:
                char.state = CharacterState.WALK
        elif abs_dist_x > ideal_range + 40:
            char.vel_x = target_facing * WALK_SPEED
            if char.is_grounded:
                char.state = CharacterState.WALK
        else:
            if char.is_grounded and char.state == CharacterState.WALK:
                char.state = CharacterState.IDLE

        attack_range = 100
        if abs_dist_x < attack_range and char.is_grounded:
            char.ai_attack_cooldown = max(0, char.ai_attack_cooldown - 1)

            if char.ai_attack_cooldown <= 0:
                params = getattr(char, 'ai_difficulty_params', {
                    "attack_chance": 0.02,
                    "combo_chance": 0.3
                })

                roll = random.random()
                attack_chance = params.get("attack_chance", 0.02)

                if roll < attack_chance * 0.6:
                    char.start_attack(get_light_attack())
                    char.ai_attack_cooldown = 50
                elif roll < attack_chance * 0.85:
                    char.start_attack(get_heavy_attack())
                    char.ai_attack_cooldown = 70
                elif roll < attack_chance:
                    char.start_attack(get_low_attack())
                    char.ai_attack_cooldown = 60

    def _on_enemy_death(self, enemy: EndlessEnemy):
        enemy.is_active = False
        self.stats.total_kills += 1
        self.stats.wave_kills += 1
        self.stats.current_combo_kills += 1
        self.stats.combo_timer = 180

        if self.stats.current_combo_kills > self.stats.max_combo_kills:
            self.stats.max_combo_kills = self.stats.current_combo_kills

        if self.player:
            if self.player.hit_combo > self.stats.max_combo:
                self.stats.max_combo = self.player.hit_combo

        base_score = ENDLESS_BASE_SCORE
        combo_bonus = int(base_score * self.stats.current_combo_kills * ENDLESS_COMBO_BONUS_MULTIPLIER)
        wave_bonus = int(base_score * self.stats.current_wave * ENDLESS_WAVE_BONUS_MULTIPLIER)

        self.stats.score += base_score + combo_bonus + wave_bonus

    def _is_wave_clear(self) -> bool:
        alive_enemies = [e for e in self.enemies if e.is_active and e.character.health > 0]
        return len(alive_enemies) == 0 and self.stats.wave_kills >= self.stats.wave_enemies_total > 0

    def _start_next_wave(self, player: Character):
        self.stats.current_wave += 1
        self.difficulty.next_wave()

        player.health = min(player.max_health, player.health + ENDLESS_WAVE_HEAL_AMOUNT)
        player.rage = min(player.max_rage, player.rage + ENDLESS_WAVE_ENERGY_RESTORE)

        self.is_transitioning = True
        self.transition_timer = ENDLESS_WAVE_TRANSITION_FRAMES
        self.transition_message = f"WAVE {self.stats.current_wave}"

        self._spawn_wave_enemies()

    def _calculate_final_rewards(self):
        score = self.stats.score
        waves = self.stats.current_wave
        kills = self.stats.total_kills

        self.stats.gold_reward = int(score * 0.1 + waves * 50 + kills * 10)
        self.stats.exp_reward = int(score * 0.05 + waves * 30 + kills * 5)
        self.stats.talent_points_reward = max(1, waves // 5)

    def get_active_enemies(self) -> List[Character]:
        return [e.character for e in self.enemies if e.is_active and e.character.health > 0]

    def get_all_enemies(self) -> List[Character]:
        return [e.character for e in self.enemies]

    def get_survival_time_seconds(self) -> int:
        return self.stats.survival_frames // FPS

    def get_survival_time_formatted(self) -> str:
        seconds = self.get_survival_time_seconds()
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def get_combo_multiplier(self) -> float:
        if self.stats.current_combo_kills < 2:
            return 1.0
        return 1.0 + (self.stats.current_combo_kills - 1) * 0.5

    def check_attacks(self, player: Character, effects_list: list, screen_shake):
        enemies = self.get_active_enemies()

        for enemy in enemies:
            if enemy.is_attacking and player.health > 0:
                enemy.check_attack_hit(player, effects_list, screen_shake)

            if player.is_attacking and enemy.health > 0:
                player.check_attack_hit(enemy, effects_list, screen_shake)

        for i, enemy1 in enumerate(enemies):
            for j, enemy2 in enumerate(enemies):
                if i >= j:
                    continue
                if enemy1.is_attacking and enemy2.health > 0:
                    enemy1.check_attack_hit(enemy2, effects_list, screen_shake)
                if enemy2.is_attacking and enemy1.health > 0:
                    enemy2.check_attack_hit(enemy1, effects_list, screen_shake)
