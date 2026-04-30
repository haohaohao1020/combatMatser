from typing import Dict, Any
from config import (
    ENDLESS_DIFFICULTY_INCREASE_WAVE,
    ENDLESS_FIRST_MULTI_ENEMY_WAVE,
    ENDLESS_MAX_ENEMIES_AT_ONCE,
    MAX_HEALTH, LIGHT_ATTACK_DAMAGE, HEAVY_ATTACK_DAMAGE, LOW_ATTACK_DAMAGE
)


class EndlessDifficulty:
    def __init__(self):
        self.current_wave = 1
        self.survival_seconds = 0

    def reset(self):
        self.current_wave = 1
        self.survival_seconds = 0

    def next_wave(self):
        self.current_wave += 1

    def add_survival_time(self, seconds: float):
        self.survival_seconds += seconds

    def get_difficulty_level(self) -> int:
        return (self.current_wave - 1) // ENDLESS_DIFFICULTY_INCREASE_WAVE

    def get_ai_params(self) -> Dict[str, Any]:
        level = self.get_difficulty_level()

        base_easy = {
            "reaction_time": 30,
            "block_chance": 0.2,
            "dodge_chance": 0.1,
            "attack_chance": 0.02,
            "combo_chance": 0.3,
            "crouch_chance": 0.2,
            "move_smartness": 0.5,
            "ultimate_chance": 0.0,
            "prediction_chance": 0.0,
        }

        base_hard = {
            "reaction_time": 8,
            "block_chance": 0.6,
            "dodge_chance": 0.3,
            "attack_chance": 0.05,
            "combo_chance": 0.7,
            "crouch_chance": 0.4,
            "move_smartness": 0.9,
            "ultimate_chance": 0.3,
            "prediction_chance": 0.2,
        }

        t = min(level / 10, 1.0)

        return {
            "reaction_time": int(self._lerp(base_easy["reaction_time"], base_hard["reaction_time"], t)),
            "block_chance": self._lerp(base_easy["block_chance"], base_hard["block_chance"], t),
            "dodge_chance": self._lerp(base_easy["dodge_chance"], base_hard["dodge_chance"], t),
            "attack_chance": self._lerp(base_easy["attack_chance"], base_hard["attack_chance"], t),
            "combo_chance": self._lerp(base_easy["combo_chance"], base_hard["combo_chance"], t),
            "crouch_chance": self._lerp(base_easy["crouch_chance"], base_hard["crouch_chance"], t),
            "move_smartness": self._lerp(base_easy["move_smartness"], base_hard["move_smartness"], t),
            "ultimate_chance": self._lerp(base_easy["ultimate_chance"], base_hard["ultimate_chance"], t),
            "prediction_chance": self._lerp(base_easy["prediction_chance"], base_hard["prediction_chance"], t),
        }

    def get_enemy_count(self) -> int:
        if self.current_wave < ENDLESS_FIRST_MULTI_ENEMY_WAVE:
            return 1

        extra_waves = self.current_wave - ENDLESS_FIRST_MULTI_ENEMY_WAVE
        count = 2 + (extra_waves // 2)
        return min(count, ENDLESS_MAX_ENEMIES_AT_ONCE)

    def get_health_multiplier(self) -> float:
        level = self.get_difficulty_level()
        return 1.0 + level * 0.15

    def get_damage_multiplier(self) -> float:
        level = self.get_difficulty_level()
        return 1.0 + level * 0.1

    def get_hitstun_reduction(self) -> float:
        level = self.get_difficulty_level()
        return min(level * 0.05, 0.5)

    def get_scaled_health(self, base_health: int = MAX_HEALTH) -> int:
        return int(base_health * self.get_health_multiplier())

    def get_scaled_damage(self, base_damage: int, attack_type: str = "light") -> int:
        multiplier = self.get_damage_multiplier()
        return int(base_damage * multiplier)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def get_difficulty_description(self) -> str:
        level = self.get_difficulty_level()
        if level == 0:
            return "NOVICE - 新手难度"
        elif level <= 2:
            return "APPRENTICE - 学徒难度"
        elif level <= 4:
            return "ADEPT - 熟练难度"
        elif level <= 6:
            return "EXPERT - 专家难度"
        elif level <= 8:
            return "MASTER - 大师难度"
        else:
            return "LEGEND - 传奇难度"

    def get_color_for_difficulty(self) -> tuple:
        from config import GREEN, YELLOW, ORANGE, RED, PURPLE, CYAN
        level = self.get_difficulty_level()
        if level == 0:
            return GREEN
        elif level <= 2:
            return YELLOW
        elif level <= 4:
            return ORANGE
        elif level <= 6:
            return RED
        elif level <= 8:
            return PURPLE
        else:
            return CYAN
