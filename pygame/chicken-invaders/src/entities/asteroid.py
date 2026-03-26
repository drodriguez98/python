# asteroid.py
# Asteroide con tamaño variable, rotación y movimiento hacia abajo.

import pygame
from src.utils import load_image
import random
from src import settings

class Asteroid:
    """
    Asteroide que cae verticalmente, rota, y puede tener tamaño escalado entre 50% y 100%.
    """

    def __init__(self, x, y, speed, hp):
        base = load_image('asteroid.png')
        scale = random.uniform(0.5, 1)
        # limitar tamaño máximo
        maxw = int(settings.WIDTH * 0.25)
        w = max(8, min(maxw, int(base.get_width() * scale)))
        h = int(base.get_height() * (w / base.get_width()))
        self.image = pygame.transform.smoothscale(base, (w, h))
        self.orig_image = self.image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y
        self.vy = speed
        self.hp = hp
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-90, 90)  # grados por segundo

    def update(self, dt):
        self.y += self.vy
        self.rect.centery = int(self.y)
        # rotación
        self.angle = (self.angle + self.spin * dt) % 360
        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def off_screen(self, screen_h):
        return self.y > screen_h + 200

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)
