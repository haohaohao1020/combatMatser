from enum import Enum, auto


class HeroType(Enum):
    BASIC_FIGHTER = auto()
    WARRIOR_GIANT = auto()
    SWIFT_ASSASSIN = auto()
    MYSTIC_MAGE = auto()


class HeroArchetype(Enum):
    BALANCED = auto()
    POWER = auto()
    SPEED = auto()
    CONTROL = auto()


class SkillType(Enum):
    LIGHT_ATTACK = auto()
    HEAVY_ATTACK = auto()
    SPECIAL_SKILL = auto()
    ULTIMATE = auto()


HERO_INFO = {
    HeroType.BASIC_FIGHTER: {
        "name": "基础战斗者",
        "archetype": HeroArchetype.BALANCED,
        "description": "平衡型角色，适合新手入门",
        "special_skill_name": "旋风斩",
        "ultimate_name": "极限爆发",
        "colors": {
            "primary": (50, 100, 255),
            "secondary": (30, 60, 180),
            "accent": (0, 200, 255)
        }
    },
    HeroType.WARRIOR_GIANT: {
        "name": "狂武壮汉",
        "archetype": HeroArchetype.POWER,
        "description": "高血量、高攻击、高防御，移速偏慢",
        "special_skill_name": "野蛮冲撞",
        "ultimate_name": "撼地重击",
        "colors": {
            "primary": (180, 50, 30),
            "secondary": (120, 30, 20),
            "accent": (255, 140, 0)
        }
    },
    HeroType.SWIFT_ASSASSIN: {
        "name": "疾风刺客",
        "archetype": HeroArchetype.SPEED,
        "description": "高移速、高暴击，血量和防御较低",
        "special_skill_name": "瞬身闪袭",
        "ultimate_name": "暗影连斩",
        "colors": {
            "primary": (80, 30, 120),
            "secondary": (50, 20, 80),
            "accent": (180, 50, 255)
        }
    },
    HeroType.MYSTIC_MAGE: {
        "name": "玄术法师",
        "archetype": HeroArchetype.CONTROL,
        "description": "远程控制型，技能带有控制效果",
        "special_skill_name": "元气禁锢",
        "ultimate_name": "雷霆结界",
        "colors": {
            "primary": (30, 150, 100),
            "secondary": (20, 100, 70),
            "accent": (50, 255, 150)
        }
    }
}
