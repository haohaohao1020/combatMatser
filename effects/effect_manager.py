from typing import List
import pygame

from effects.base_effect import Effect


class EffectManager:
    def __init__(self):
        self.effects: List[Effect] = []

    def add(self, effect: Effect):
        self.effects.append(effect)

    def update(self):
        for effect in self.effects:
            effect.update()
        self.effects = [e for e in self.effects if e.alive]

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        for effect in self.effects:
            effect.render(surface, offset_x, offset_y)

    def clear(self):
        self.effects.clear()
