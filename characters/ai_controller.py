import random
from typing import Optional

from config import (
    CharacterState, WALK_SPEED,
    clamp
)
from characters.character import Character
from attacks import (
    get_light_attack, get_heavy_attack, get_low_attack
)


class AIController:
    def __init__(self, character: Character, difficulty: str = "easy"):
        self.character = character
        self.difficulty = difficulty
        self.ai_timer = 0

        self.character.is_ai = True
        self.character.difficulty = difficulty

    def _get_difficulty_params(self) -> dict:
        if self.difficulty == "easy":
            return {
                "reaction_time": 30,
                "block_chance": 0.2,
                "dodge_chance": 0.1,
                "attack_chance": 0.02,
                "combo_chance": 0.3,
                "crouch_chance": 0.2,
                "move_smartness": 0.5,
            }
        else:
            return {
                "reaction_time": 8,
                "block_chance": 0.6,
                "dodge_chance": 0.3,
                "attack_chance": 0.05,
                "combo_chance": 0.7,
                "crouch_chance": 0.4,
                "move_smartness": 0.9,
            }

    def update(self, opponent: Character):
        char = self.character

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

        dist_x = opponent.x - char.x
        abs_dist_x = abs(dist_x)
        target_facing = 1 if dist_x > 0 else -1

        char.facing = target_facing

        if char.rage >= char.max_rage and self.ai_timer % 10 == 0:
            char.start_ultimate()
            return

        if opponent.is_attacking and opponent.current_attack:
            attack = opponent.current_attack
            in_range = abs_dist_x < (attack.hitbox_w + char.width)

            if in_range and self.ai_timer % params["reaction_time"] == 0:
                if attack.is_high and random.random() < params["crouch_chance"]:
                    char.state = CharacterState.CROUCH
                    char.block_high = False
                    return

                if random.random() < params["block_chance"] and char.is_grounded:
                    char.is_blocking = True
                    char.state = CharacterState.BLOCK
                    if self.difficulty == "hard":
                        char.perfect_block_window = 12
                    return

                if random.random() < params["dodge_chance"] and char.dodge_cooldown <= 0:
                    dodge_dir = -target_facing
                    char.start_dodge(dodge_dir)
                    return

        ideal_range = 80
        move_toward = False
        move_away = False

        if abs_dist_x < ideal_range - 20:
            move_away = True
        elif abs_dist_x > ideal_range + 40:
            move_toward = True

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
            if random.random() < 0.02:
                if char.is_grounded:
                    char.vel_x = random.choice([-WALK_SPEED, 0, WALK_SPEED])
                    if char.vel_x != 0:
                        char.state = CharacterState.WALK

        attack_range = 100
        if abs_dist_x < attack_range and char.is_grounded:
            char.ai_attack_cooldown = max(0, char.ai_attack_cooldown - 1)

            if char.ai_attack_cooldown <= 0:
                roll = random.random()

                if roll < params["attack_chance"] * 0.6:
                    char.start_attack(get_light_attack())
                    char.ai_attack_cooldown = 60 if self.difficulty == "easy" else 40

                elif roll < params["attack_chance"] * 0.85:
                    char.start_attack(get_heavy_attack())
                    char.ai_attack_cooldown = 80 if self.difficulty == "easy" else 60

                elif roll < params["attack_chance"]:
                    char.start_attack(get_low_attack())
                    char.ai_attack_cooldown = 70 if self.difficulty == "easy" else 50

        if self.difficulty == "hard":
            if char.is_grounded and abs_dist_x < 200 and random.random() < 0.005:
                char.jump()

            if char.is_grounded and abs_dist_x < 150 and random.random() < 0.01:
                if opponent.vel_x > 0:
                    char.vel_x = -WALK_SPEED
                else:
                    char.vel_x = WALK_SPEED


def add_ai_to_character(character: Character, difficulty: str = "easy") -> AIController:
    return AIController(character, difficulty)
