import pygame


class Effect:
    def __init__(self, x: float, y: float, duration: int):
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.alive = True

    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False

    def render(self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0):
        pass
