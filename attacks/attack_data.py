from dataclasses import dataclass
from typing import Optional
import pygame

from config import AttackType


@dataclass
class AttackData:
    attack_type: AttackType
    damage: int
    hitbox_x: int
    hitbox_y: int
    hitbox_w: int
    hitbox_h: int
    startup_frames: int
    active_frames: int
    recovery_frames: int
    hitstun: int
    knockback_x: float
    knockback_y: float
    is_high: bool = True
    can_block: bool = True
    guard_break: bool = False

    @property
    def total_frames(self) -> int:
        return self.startup_frames + self.active_frames + self.recovery_frames

    def is_active_frame(self, current_frame: int) -> bool:
        return self.startup_frames <= current_frame < self.startup_frames + self.active_frames

    def is_startup_frame(self, current_frame: int) -> bool:
        return current_frame < self.startup_frames

    def is_recovery_frame(self, current_frame: int) -> bool:
        return current_frame >= self.startup_frames + self.active_frames
