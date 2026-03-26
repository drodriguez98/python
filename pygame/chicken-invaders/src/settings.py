# settings.py
# Configuración global y constantes del juego.

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_IMG = os.path.join(BASE_DIR, 'assets', 'img')
ASSETS_SND = os.path.join(BASE_DIR, 'assets', 'sounds')

# Pantalla (si quieres forzar fullscreen, usa get_desktop_size en runtime)
FPS = 60
WIDTH = None  # cambiar a resolución de pantalla o calcular en runtime
HEIGHT = None

# Colores (R,G,B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Jugador
PLAYER_SPEED = 6
PLAYER_LIVES = 3
PLAYER_MAX_LIVES = 5

# Disparos
BASE_SHOT_SPEED = 10  # velocidad base para todas las armas

# Huevo roto
EGG_CRACK_DURATION = 3.0  # segundos que permanece el huevo roto

# Probabilidades
CHICKEN_DROP_POWERUP_PROB = 0.08  # probabilidad de soltar powerup al morir
ASTEROID_DROP_POWERUP_PROB = 0.05

# Valores base primera oleada de pollos
BASE_CHICKEN_ROWS = 3
BASE_CHICKEN_COLS = 6
BASE_CHICKEN_SPEED = 1.0
BASE_CHICKEN_HP = 1
BASE_CHICKEN_EGG_PROB = 0.001
BASE_EGG_FALL_SPEED = 3.0

# Valores base primera oleada de asteroides
BASE_ASTEROID_COUNT = 3
BASE_ASTEROID_SPEED = 2.0
BASE_ASTEROID_HP = 1

# Multiplicadores por nivel (scaling)
MULT_CHICKEN_ROWS = 1.05
MULT_CHICKEN_COLS = 1.03
MULT_CHICKEN_SPEED = 1.02
MULT_CHICKEN_HP = 1.1
MULT_CHICKEN_EGG_PROB = 1.02
MULT_EGG_FALL_SPEED = 1.01

MULT_ASTEROID_COUNT = 1.05
MULT_ASTEROID_SPEED = 1.03
MULT_ASTEROID_HP = 1.1

# Valores máximos
MAX_CHICKEN_COLS = 12
MAX_CHICKEN_ROWS = 8
MAX_CHICKEN_SPEED = 5.0
MAX_CHICKEN_EGG_PROB = 0.25
MAX_CHICKEN_POWERUP_PROB = 0.2
MAX_ASTEROID_POWERUP_PROB = 0.15

MAX_ASTEROID_COUNT = 12
MAX_ASTEROID_SPEED = 6.0

# Puntuaciones
SCORE_PER_CHICKEN = 10
SCORE_PER_ASTEROID = 15

# Misc
STAR_COUNT = 80  # estrellas dibujadas cada frame

# Mapear tipos de powerup
POWERUP_TYPES = ('life', 'gun', 'laser', 'ray')
