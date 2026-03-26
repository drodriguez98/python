import pygame
from src import settings
from src.utils import load_image, load_sound
from src.entities.shot import Shot
import time

class Player:
    def __init__(self, x, y):
        ship_width = int(settings.WIDTH * 0.08)
        self.image = load_image('spaceship.png', scale=(ship_width, ship_width))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = settings.PLAYER_SPEED
        self.lives = settings.PLAYER_LIVES
        self.weapon_type = 'gun'
        self.weapon_level = 1
        self.shots = []
        self.fire_cooldown = 0.18
        self._last_shot_time = 0.0

        # Cargar sonidos de disparo
        self.sounds = {
            'gun': load_sound('gun.mp3'),
            'laser': load_sound('laser.mp3'),
            'ray': load_sound('ray.mp3')
        }

        # Sprites de disparo
        bullet_size = int(settings.WIDTH * 0.02)
        self.bullet_images = {
            'gun': load_image('bullet.png', scale=(bullet_size, bullet_size)),
            'laser': load_image('laser.png', scale=(bullet_size, bullet_size*2)),
            'ray': load_image('ray.png', scale=(bullet_size*2, bullet_size*2))
        }

    def reset(self):
        self.lives = settings.PLAYER_LIVES
        self.weapon_type = 'gun'
        self.weapon_level = 1
        self.shots.clear()
        self._last_shot_time = 0.0

    def reset_weapons(self):
        self.weapon_type = 'gun'
        self.weapon_level = 1
        self.shots.clear()
        self._last_shot_time = 0.0

    def can_shoot(self):
        return time.time() - self._last_shot_time >= self.fire_cooldown

    def update(self, keys, dt):
        # Movimiento horizontal
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= int(self.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += int(self.speed)
        # Movimiento vertical
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= int(self.speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += int(self.speed)

        # Limitar dentro de pantalla
        self.rect.x = max(0, min(self.rect.x, settings.WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, settings.HEIGHT - self.rect.height))

        # Disparo
        if keys[pygame.K_SPACE] and self.can_shoot():
            self.shoot()
            self._last_shot_time = time.time()

    def shoot(self):
        x = self.rect.centerx
        y = self.rect.top
        level = min(4, max(1, self.weapon_level))

        # reproducir sonido
        if self.sounds.get(self.weapon_type):
            try:
                self.sounds[self.weapon_type].play()
            except Exception:
                pass

        # disparo
        patterns = {
            'gun': {1:[0],2:[-6,6],3:[-10,0,10],4:[-20,-8,0,8,20]},
            'laser': {1:[0],2:[-8,8],3:[-12,0,12],4:[-25,-10,0,10,25]},
            'ray': {1:[0],2:[-12,12],3:[-18,0,18],4:[-30,-15,0,15,30]}
        }

        for off in patterns[self.weapon_type][level]:
            s = Shot(x+off, y, -settings.BASE_SHOT_SPEED)
            # asignar imagen de bala
            s.image = self.bullet_images[self.weapon_type]
            # ajustes visuales opcionales
            if self.weapon_type == 'laser':
                s.width = 4
            elif self.weapon_type == 'ray':
                s.width = 6
            self.shots.append(s)

    def apply_powerup(self, powerup_type):
        if powerup_type == 'life':
            self.lives += 1
        elif powerup_type in ['gun','laser','ray']:
            if self.weapon_type == powerup_type:
                self.weapon_level = min(4, self.weapon_level + 1)
            else:
                self.weapon_type = powerup_type
                # Mantener nivel actual al cambiar de tipo

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        for shot in list(self.shots):
            shot.draw(screen)
