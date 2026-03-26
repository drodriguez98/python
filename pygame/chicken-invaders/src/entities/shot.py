# shot.py
# Implementación genérica de proyectil usado por el jugador.

import pygame
from src.utils import load_image
from src import settings

class Shot:
    """
    Proyectil simple hacia arriba (para el jugador).
    Tiene posición (x,y) y velocidad vertical.
    """

    def __init__(self, x, y, vy):
        # Escalar bala a un tamaño coherente
        bullet_w = max(8, int(settings.WIDTH * 0.01))  # ~1% del ancho
        self.image = load_image('bullet.png', scale=(bullet_w, bullet_w))
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = vy
        self.x = x
        self.y = y

    def update(self, dt):
        self.y += self.vy
        self.rect.centery = int(self.y)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
