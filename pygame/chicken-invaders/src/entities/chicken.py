# chicken.py
# Entidad pollo con vida, movimiento lateral y posibilidad de soltar huevos/powerups.

import pygame
from src.utils import load_image
import random
from src import settings

class Chicken:
    """
    Pollo enemigo:
    - x,y: posición
    - speed: velocidad lateral base
    - hp: vida total
    - level: nivel de juego (para puntajes)
    - drop_prob: probabilidad de soltar huevo por segundo aproximada
    """

    def __init__(self, x, y, speed, hp, level, drop_prob=None):
        # Escalar pollos en función del ancho de la pantalla
        chick_w = int(settings.WIDTH * 0.05)  # 5% del ancho
        self.image = load_image('chicken.png', scale=(chick_w, chick_w))
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y
        self.speed = speed
        self.hp = hp
        self.level = level
        # Movimiento: alternar sentido cada cierto tiempo
        self.direction = 1 if random.random() < 0.5 else -1
        self._move_timer = random.uniform(0.5, 2.0)
        self._time_acc = 0.0
        self.drop_prob = drop_prob if drop_prob is not None else settings.BASE_CHICKEN_EGG_PROB

    def update(self, dt):
        # Movimiento lateral simple y cambiar dirección aleatoriamente
        self.x += self.direction * self.speed
        self.rect.centerx = int(self.x)
        self._time_acc += dt
        if self._time_acc >= self._move_timer:
            self.direction *= -1
            self._time_acc = 0.0
            self._move_timer = random.uniform(0.7, 2.5)

    def try_drop_egg(self):
        # Probabilidad por frame (aprox): drop_prob is interpreted as prob per second
        if random.random() < self.drop_prob:
            return True
        return False

    def hit(self, damage=1):
        """Aplica daño; devuelve True si el pollo muere."""
        self.hp -= damage
        return self.hp <= 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)
