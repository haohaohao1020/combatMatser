from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    MODE_SELECT = auto()
    DIFFICULTY_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    ROUND_END = auto()
    GAME_OVER = auto()


class CharacterState(Enum):
    IDLE = auto()
    WALK = auto()
    RUN = auto()
    JUMP = auto()
    CROUCH = auto()
    ATTACK_LIGHT = auto()
    ATTACK_HEAVY = auto()
    ATTACK_LOW = auto()
    BLOCK = auto()
    HIT = auto()
    LAUNCHED = auto()
    GROUNDED = auto()
    DODGE = auto()
    ULTIMATE = auto()


class AttackType(Enum):
    LIGHT = auto()
    HEAVY = auto()
    LOW = auto()
    ULTIMATE = auto()
