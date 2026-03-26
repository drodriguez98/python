# utils.py
# Utilidades generales: carga de assets, dibujado de texto, estrellas de fondo, colisiones sencillas.
# Añadido: load_image con parámetro `scale` para redimensionar las imágenes de forma consistente.

import pygame
from src import settings
import random
import os

# Cargar imagen con fallback y posibilidad de escalado.
# scale: None (sin escalar), float (>0) escala multiplicadora, or (w,h) exact size
def load_image(name, scale=None):
    path = os.path.join(settings.ASSETS_IMG, name)
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        print(f"Warning: imagen no encontrada: {path}")
        # superficie placeholder
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 128))
        img = surf

    if scale is None:
        return img
    try:
        if isinstance(scale, tuple) and len(scale) == 2:
            w, h = int(scale[0]), int(scale[1])
            return pygame.transform.smoothscale(img, (w, h))
        elif isinstance(scale, (int, float)):
            if scale <= 0:
                return img
            w = max(1, int(img.get_width() * scale))
            h = max(1, int(img.get_height() * scale))
            return pygame.transform.smoothscale(img, (w, h))
    except Exception as e:
        print("Warning: error al escalar imagen:", e)
    return img

# Cargar sonido con fallback
def load_sound(name):
    path = os.path.join(settings.ASSETS_SND, name)
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        # no abortar si sonido no encontrado
        # print(f"Warning: sonido no encontrado: {path}")
        return None

# Dibuja texto centrado
def draw_text_center(surface, text, font, color, pos):
    img = font.render(text, True, color)
    rect = img.get_rect(center=pos)
    surface.blit(img, rect)

# Generar lista de estrellas (x,y,brightness)
def gen_stars(n, w, h):
    stars = []
    for _ in range(n):
        stars.append([random.randrange(0, w), random.randrange(0, h), random.randint(100, 255)])
    return stars

# Actualizar/ dibujar estrellas (muy simple, no animación por ahora)
def draw_stars(screen, stars):
    for s in stars:
        x, y, b = s
        # dibujar pixel por pixel
        if 0 <= x < screen.get_width() and 0 <= y < screen.get_height():
            screen.set_at((x, y), (b, b, b))
