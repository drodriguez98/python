# egg.py
# Huevo lanzado por pollos; cuando choca contra el suelo se convierte en huevo roto.

import pygame
from src import settings
from src.utils import load_image, load_sound

class Egg:
    """
    Huevo que cae verticalmente. Puede chocar con jugador o con el suelo.
    Si choca con el suelo se transforma en objeto inerte (egg_crack) durante EGG_CRACK_DURATION.
    """

    def __init__(self, x, y, vy=None):
        self.image = load_image('egg.png', scale=(24, 24))
        self.crack_image = load_image('egg_crack.png', scale=(28, 18))
        self.egg_sound = load_sound('egg_crack.mp3')
        self.x = x
        self.y = y
        self.vy = vy if vy is not None else settings.BASE_EGG_FALL_SPEED
        self.rect = self.image.get_rect(center=(x, y))
        self.cracked = False
        self.crack_timer = 0.0

    def update(self, dt):
        if not self.cracked:
            self.y += self.vy
            self.rect.centery = int(self.y)
            if self.y >= settings.HEIGHT - 20:
                self.crack()
        else:
            self.crack_timer -= dt

    def crack(self):
        self.cracked = True
        self.crack_timer = settings.EGG_CRACK_DURATION
        if self.egg_sound:
            try:
                self.egg_sound.play()
            except Exception:
                pass

    def off_screen(self, screen_h):
        if self.cracked:
            return self.crack_timer <= 0
        return self.y > screen_h + 50

    def draw(self, screen):
        if self.cracked:
            img = self.crack_image
        else:
            img = self.image
        screen.blit(img, self.rect)
