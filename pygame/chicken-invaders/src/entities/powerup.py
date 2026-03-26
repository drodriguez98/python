# powerup.py
# Power-up que cae verticalmente; al ser recogido aplica efecto sobre el jugador.

import pygame
from src.utils import load_image
from src import settings

class PowerUp:
    """
    PowerUp simple con tipo (life|gun|laser|ray) que cae hacia abajo y aplica efecto al jugador.
    """

    def __init__(self, x, y, type_):
        self.type = type_
        # tamaño pequeño
        self.image = load_image(f'powerup_{type_}.png', scale=(40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.vy = 2.5
        self.x = x
        self.y = y

    def update(self, dt):
        self.y += self.vy
        self.rect.centery = int(self.y)

    def off_screen(self, screen_h):
        return self.y > screen_h + 50

    def apply(self, player):
        """Aplica el efecto al jugador: vida o mejora/cambio de arma."""
        if self.type == 'life':
            if player.lives < settings.PLAYER_MAX_LIVES:
                player.lives += 1
        else:
            # Si es el mismo tipo: subir nivel (hasta 4)
            if player.weapon_type == self.type:
                player.weapon_level = min(4, player.weapon_level + 1)
            else:
                # cambiar arma (mantener su nivel)
                player.weapon_type = self.type

    def draw(self, screen):
        screen.blit(self.image, self.rect)
