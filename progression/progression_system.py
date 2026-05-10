import json
import os
import math
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from copy import deepcopy


class TalentBranch(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    TECHNIQUE = "technique"


@dataclass
class TalentData:
    talent_id: str
    branch: TalentBranch
    name: str
    description: str
    tier: int
    requires: List[str] = field(default_factory=list)
    effect_type: str = ""
    effect_value: float = 0.0
    max_points: int = 1
    points_spent: int = 0
    unlocked: bool = False

    @property
    def is_maxed(self) -> bool:
        return self.points_spent >= self.max_points

    @property
    def can_upgrade(self) -> bool:
        return not self.is_maxed and self.unlocked


@dataclass
class TalentNode:
    talent: TalentData
    position: Tuple[float, float] = (0.5, 0.5)


@dataclass
class CharacterProgressionData:
    hero_type_name: str = "BASIC_FIGHTER"
    level: int = 1
    current_experience: int = 0
    experience_to_next: int = 100
    total_talent_points_earned: int = 0
    available_talent_points: int = 0
    unlocked_skins: List[str] = field(default_factory=list)
    active_skin: str = "default"
    talents_spent: Dict[str, int] = field(default_factory=dict)
    highest_wave_reached: int = 0
    fastest_win_time: float = float('inf')
    total_wins: int = 0

    @property
    def max_level(self) -> int:
        return 30

    @property
    def is_max_level(self) -> bool:
        return self.level >= self.max_level

    def get_experience_for_level(self, level: int) -> int:
        if level <= 1:
            return 0
        return int(100 * math.pow(1.2, level - 2) + 50 * (level - 2))

    def add_experience(self, amount: int) -> Tuple[int, int]:
        if self.is_max_level:
            return 0, 0

        total_levels_gained = 0
        exp_overflow = 0
        self.current_experience += amount

        while self.current_experience >= self.experience_to_next and not self.is_max_level:
            self.current_experience -= self.experience_to_next
            self.level += 1
            total_levels_gained += 1

            self.total_talent_points_earned += 2
            self.available_talent_points += 2

            if not self.is_max_level:
                self.experience_to_next = self.get_experience_for_level(self.level + 1)

        if self.is_max_level:
            exp_overflow = self.current_experience
            self.current_experience = 0
            self.experience_to_next = 0

        return total_levels_gained, exp_overflow

    def get_level_bonuses(self) -> Dict[str, float]:
        levels_above_1 = self.level - 1
        return {
            "max_health_bonus": 25.0 * levels_above_1,
            "attack_power_percent": 0.015 * levels_above_1,
            "move_speed_bonus": 0.05 * levels_above_1,
            "attack_startup_reduction": 0.003 * levels_above_1,
            "hitstun_reduction": 0.004 * levels_above_1,
        }

    def spend_talent_point(self, talent_id: str, talent_tree: Dict[str, TalentData]) -> bool:
        if self.available_talent_points <= 0:
            return False

        talent = talent_tree.get(talent_id)
        if not talent:
            return False

        if talent.points_spent >= talent.max_points:
            return False

        for req_id in talent.requires:
            req_talent = talent_tree.get(req_id)
            if not req_talent or req_talent.points_spent < req_talent.max_points:
                return False

        self.available_talent_points -= 1
        self.talents_spent[talent_id] = self.talents_spent.get(talent_id, 0) + 1
        talent.points_spent = self.talents_spent[talent_id]
        talent.unlocked = True
        return True

    def reset_talents(self, talent_tree: Dict[str, TalentData]):
        self.available_talent_points = self.total_talent_points_earned
        self.talents_spent = {}
        for talent in talent_tree.values():
            talent.points_spent = 0
            talent.unlocked = talent.tier == 1

    def get_active_talent_effects(self, talent_tree: Dict[str, TalentData]) -> Dict[str, float]:
        effects: Dict[str, float] = {}
        for talent_id, points in self.talents_spent.items():
            talent = talent_tree.get(talent_id)
            if talent and points > 0:
                total_effect = 0.0
                for i in range(1, points + 1):
                    multiplier = 1.0 + (i - 1) * 0.5
                    total_effect += talent.effect_value * multiplier
                current_val = effects.get(talent.effect_type, 0.0)
                effects[talent.effect_type] = current_val + total_effect
        return effects

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hero_type_name": self.hero_type_name,
            "level": self.level,
            "current_experience": self.current_experience,
            "experience_to_next": self.experience_to_next,
            "total_talent_points_earned": self.total_talent_points_earned,
            "available_talent_points": self.available_talent_points,
            "unlocked_skins": self.unlocked_skins,
            "active_skin": self.active_skin,
            "talents_spent": self.talents_spent,
            "highest_wave_reached": self.highest_wave_reached,
            "fastest_win_time": float('inf') if self.fastest_win_time == float('inf') else self.fastest_win_time,
            "total_wins": self.total_wins,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterProgressionData':
        return cls(
            hero_type_name=data.get("hero_type_name", "BASIC_FIGHTER"),
            level=data.get("level", 1),
            current_experience=data.get("current_experience", 0),
            experience_to_next=data.get("experience_to_next", 100),
            total_talent_points_earned=data.get("total_talent_points_earned", 0),
            available_talent_points=data.get("available_talent_points", 0),
            unlocked_skins=data.get("unlocked_skins", []),
            active_skin=data.get("active_skin", "default"),
            talents_spent=data.get("talents_spent", {}),
            highest_wave_reached=data.get("highest_wave_reached", 0),
            fastest_win_time=float('inf') if data.get("fastest_win_time", float('inf')) == float('inf') else data.get("fastest_win_time", float('inf')),
            total_wins=data.get("total_wins", 0),
        )


@dataclass
class GameSaveData:
    version: int = 1
    total_gold: int = 0
    character_progressions: Dict[str, CharacterProgressionData] = field(default_factory=dict)
    completed_challenges: List[str] = field(default_factory=list)
    highest_ever_wave: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "total_gold": self.total_gold,
            "character_progressions": {
                k: v.to_dict() for k, v in self.character_progressions.items()
            },
            "completed_challenges": self.completed_challenges,
            "highest_ever_wave": self.highest_ever_wave,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSaveData':
        char_progs = {}
        for k, v in data.get("character_progressions", {}).items():
            char_progs[k] = CharacterProgressionData.from_dict(v)
        return cls(
            version=data.get("version", 1),
            total_gold=data.get("total_gold", 0),
            character_progressions=char_progs,
            completed_challenges=data.get("completed_challenges", []),
            highest_ever_wave=data.get("highest_ever_wave", 0),
        )


class SaveManager:
    SAVE_FILE_NAME = "combat_master_save.json"

    @classmethod
    def get_save_path(cls) -> str:
        app_data = os.environ.get('APPDATA')
        if app_data:
            save_dir = os.path.join(app_data, "CombatMaster")
        else:
            save_dir = os.path.join(os.path.expanduser("~"), ".combat_master")

        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, cls.SAVE_FILE_NAME)

    @classmethod
    def save_game(cls, save_data: GameSaveData) -> bool:
        try:
            save_path = cls.get_save_path()
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data.to_dict(), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False

    @classmethod
    def load_game(cls) -> GameSaveData:
        try:
            save_path = cls.get_save_path()
            if not os.path.exists(save_path):
                return GameSaveData()
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return GameSaveData.from_dict(data)
        except Exception as e:
            print(f"Load failed: {e}")
            return GameSaveData()

    @classmethod
    def reset_save(cls) -> bool:
        try:
            save_path = cls.get_save_path()
            if os.path.exists(save_path):
                os.remove(save_path)
            return True
        except Exception:
            return False


def create_default_talent_tree() -> Dict[str, TalentData]:
    talents = {}

    attack_talents = [
        TalentData(
            talent_id="atk_combo_damage",
            branch=TalentBranch.ATTACK,
            name="连击精通",
            description="连招伤害 +8%/12%/15%",
            tier=1,
            effect_type="combo_damage_bonus",
            effect_value=0.08,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="atk_ultimate_damage",
            branch=TalentBranch.ATTACK,
            name="必杀强化",
            description="必杀技能伤害 +10%/15%/20%",
            tier=1,
            effect_type="ultimate_damage_bonus",
            effect_value=0.10,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="atk_knockback",
            branch=TalentBranch.ATTACK,
            name="重击击退",
            description="普通攻击击退距离 +15%/25%/35%",
            tier=2,
            requires=["atk_combo_damage"],
            effect_type="knockback_bonus",
            effect_value=0.15,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="atk_rage_gen",
            branch=TalentBranch.ATTACK,
            name="怒气爆发",
            description="攻击命中额外攒能量 +5/10/15",
            tier=2,
            requires=["atk_ultimate_damage"],
            effect_type="rage_on_hit_bonus",
            effect_value=5.0,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="atk_crit_chance",
            branch=TalentBranch.ATTACK,
            name="致命打击",
            description="暴击概率 +6%/12%/20%",
            tier=3,
            requires=["atk_knockback", "atk_rage_gen"],
            effect_type="crit_chance",
            effect_value=0.06,
            max_points=3,
            unlocked=False
        ),
    ]

    defense_talents = [
        TalentData(
            talent_id="def_global_reduction",
            branch=TalentBranch.DEFENSE,
            name="钢筋铁骨",
            description="受到所有伤害 -5%/10%/15%",
            tier=1,
            effect_type="damage_reduction",
            effect_value=0.05,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="def_block_effectiveness",
            branch=TalentBranch.DEFENSE,
            name="格挡大师",
            description="格挡减伤比例 +10%/20%/30%",
            tier=1,
            effect_type="block_reduction_bonus",
            effect_value=0.10,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="def_perfect_block_window",
            branch=TalentBranch.DEFENSE,
            name="精准防御",
            description="完美格挡判定窗口 +4/8/12 帧",
            tier=2,
            requires=["def_global_reduction"],
            effect_type="perfect_block_frames",
            effect_value=4.0,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="def_getup_speed",
            branch=TalentBranch.DEFENSE,
            name="快速起身",
            description="倒地起身速度 +20%/35%/50%",
            tier=2,
            requires=["def_block_effectiveness"],
            effect_type="getup_speed_bonus",
            effect_value=0.20,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="def_health_regen",
            branch=TalentBranch.DEFENSE,
            name="生命回复",
            description="额外生命 +80/150/250",
            tier=3,
            requires=["def_perfect_block_window", "def_getup_speed"],
            effect_type="health_regen_bonus",
            effect_value=80.0,
            max_points=3,
            unlocked=False
        ),
    ]

    technique_talents = [
        TalentData(
            talent_id="tech_dodge_cdr",
            branch=TalentBranch.TECHNIQUE,
            name="闪避精通",
            description="闪避冷却时间 -12%/25%/40%",
            tier=1,
            effect_type="dodge_cooldown_reduction",
            effect_value=0.12,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="tech_throw_range",
            branch=TalentBranch.TECHNIQUE,
            name="投技延展",
            description="投技范围 +15%/30%/50%",
            tier=1,
            effect_type="throw_range_bonus",
            effect_value=0.15,
            max_points=3,
            unlocked=True
        ),
        TalentData(
            talent_id="tech_combo_decay",
            branch=TalentBranch.TECHNIQUE,
            name="连击延续",
            description="连击伤害衰减 -1.5%/3%/5%",
            tier=2,
            requires=["tech_dodge_cdr"],
            effect_type="combo_decay_reduction",
            effect_value=0.015,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="tech_starting_rage",
            branch=TalentBranch.TECHNIQUE,
            name="先发制人",
            description="对局初始能量 +15/30/50",
            tier=2,
            requires=["tech_throw_range"],
            effect_type="starting_rage_bonus",
            effect_value=15.0,
            max_points=3,
            unlocked=False
        ),
        TalentData(
            talent_id="tech_ultimate_cdr",
            branch=TalentBranch.TECHNIQUE,
            name="能量涌动",
            description="攻击命中额外回复怒气 +2/5/10",
            tier=3,
            requires=["tech_combo_decay", "tech_starting_rage"],
            effect_type="rage_gen_passive",
            effect_value=2.0,
            max_points=3,
            unlocked=False
        ),
    ]

    for t in attack_talents + defense_talents + technique_talents:
        talents[t.talent_id] = t

    return talents


class ProgressionManager:
    def __init__(self):
        self.save_data = SaveManager.load_game()
        self.talent_tree_template = create_default_talent_tree()
        self._ensure_all_characters_exist()

    def _ensure_all_characters_exist(self):
        from characters.hero_system.character_types import HeroType
        for hero_type in HeroType:
            name = hero_type.name
            if name not in self.save_data.character_progressions:
                self.save_data.character_progressions[name] = CharacterProgressionData(
                    hero_type_name=name
                )

    def get_character_progression(self, hero_type_name: str) -> CharacterProgressionData:
        if hero_type_name not in self.save_data.character_progressions:
            self.save_data.character_progressions[hero_type_name] = CharacterProgressionData(
                hero_type_name=hero_type_name
            )
        return self.save_data.character_progressions[hero_type_name]

    def get_talent_tree_for_character(self, hero_type_name: str) -> Dict[str, TalentData]:
        tree = deepcopy(self.talent_tree_template)
        prog = self.get_character_progression(hero_type_name)
        for talent_id, points in prog.talents_spent.items():
            if talent_id in tree:
                tree[talent_id].points_spent = points
                tree[talent_id].unlocked = True
        for talent in tree.values():
            if talent.tier == 1:
                talent.unlocked = True
            else:
                all_reqs_satisfied = True
                for req_id in talent.requires:
                    if req_id not in tree:
                        all_reqs_satisfied = False
                        break
                    req_talent = tree[req_id]
                    if req_talent.points_spent < req_talent.max_points:
                        all_reqs_satisfied = False
                        break
                talent.unlocked = all_reqs_satisfied
        return tree

    def add_experience(self, hero_type_name: str, amount: int) -> Tuple[int, int]:
        prog = self.get_character_progression(hero_type_name)
        levels_gained, overflow = prog.add_experience(amount)
        self.save()
        return levels_gained, overflow

    def add_gold(self, amount: int) -> int:
        self.save_data.total_gold += amount
        self.save()
        return self.save_data.total_gold

    def spend_gold(self, amount: int) -> bool:
        if self.save_data.total_gold >= amount:
            self.save_data.total_gold -= amount
            self.save()
            return True
        return False

    def spend_talent_point(self, hero_type_name: str, talent_id: str) -> bool:
        prog = self.get_character_progression(hero_type_name)
        tree = self.get_talent_tree_for_character(hero_type_name)
        success = prog.spend_talent_point(talent_id, tree)
        if success:
            self.save()
        return success

    def reset_talents(self, hero_type_name: str, cost: int = 500) -> bool:
        if not self.spend_gold(cost):
            return False
        prog = self.get_character_progression(hero_type_name)
        tree = self.get_talent_tree_for_character(hero_type_name)
        prog.reset_talents(tree)
        self.save()
        return True

    def get_total_gold(self) -> int:
        return self.save_data.total_gold

    def record_win(self, hero_type_name: str, duration_seconds: float):
        prog = self.get_character_progression(hero_type_name)
        prog.total_wins += 1
        if duration_seconds < prog.fastest_win_time:
            prog.fastest_win_time = duration_seconds
        self.save()

    def record_wave(self, hero_type_name: str, wave: int):
        prog = self.get_character_progression(hero_type_name)
        if wave > prog.highest_wave_reached:
            prog.highest_wave_reached = wave
        if wave > self.save_data.highest_ever_wave:
            self.save_data.highest_ever_wave = wave
        self.save()

    def get_merged_bonuses(self, hero_type_name: str) -> Dict[str, float]:
        prog = self.get_character_progression(hero_type_name)
        level_bonuses = prog.get_level_bonuses()
        tree = self.get_talent_tree_for_character(hero_type_name)
        talent_effects = prog.get_active_talent_effects(tree)
        merged = dict(level_bonuses)
        for key, val in talent_effects.items():
            merged[key] = merged.get(key, 0.0) + val
        return merged

    def save(self) -> bool:
        return SaveManager.save_game(self.save_data)

    def reload(self):
        self.save_data = SaveManager.load_game()
        self._ensure_all_characters_exist()
