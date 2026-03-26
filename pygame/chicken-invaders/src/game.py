# game.py
# Contiene la lógica principal del juego: bucle, estados (menu, jugando, game over), gestión de fases y HUD.
# Añadido: actualización y dibujado de todas las entidades, colisiones básicas y drops de powerups/eggs.

import pygame
import sys
from src import settings
from src.utils import load_image, load_sound, draw_text_center, gen_stars, draw_stars
from src.entities.player import Player
from src.entities.chicken import Chicken
from src.entities.asteroid import Asteroid
from src.entities.powerup import PowerUp
from src.entities.egg import Egg
import random
import time

# Función wrapper simple: inicializa pygame y ejecuta el bucle principal.

def run_game():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    # Detectar resolución del monitor y actualizar settings
    info = pygame.display.Info()
    settings.WIDTH, settings.HEIGHT = info.current_w, info.current_h

    # Crear ventana fullscreen con la resolución detectada
    screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption('Chicken Invaders)')
    clock = pygame.time.Clock()

    # Fuentes
    font_big = pygame.font.SysFont('Arial', 64)
    font_med = pygame.font.SysFont('Arial', 28)

    # Generar estrellas
    stars = gen_stars(settings.STAR_COUNT, settings.WIDTH, settings.HEIGHT)

    # Estado
    state = 'menu'
    level = 1
    score = 0

    # Instancia jugador
    player = Player(x=settings.WIDTH // 2, y=settings.HEIGHT - 80)

    # Contenedores
    chickens = []
    eggs = []
    asteroids = []
    powerups = []

    # temporizadores/flags
    show_phase_timer = 0
    phase_text = ''

    # Sonidos (opcional)
    s_chicken = load_sound('chicken.mp3')
    s_gun = load_sound('gun.mp3')
    s_egg_crack = load_sound('egg_crack.mp3')

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if state == 'menu' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # iniciar nivel 1
                    level = 1
                    score = 0
                    player.reset()
                    chickens = spawn_chicken_wave(level)
                    asteroids = []
                    eggs = []
                    powerups = []
                    state = 'phase'  # mostrar pantalla de fase
                    phase_text = 'Fase de pollos' if not is_asteroid_phase(level) else 'Fase de asteroides'
                    show_phase_timer = 2.0
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif state == 'gameover' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    state = 'menu'
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if state == 'playing':
            # actualizar jugador
            player.update(keys, dt)

            # actualizar disparos y colisiones con enemigos
            for shot in list(player.shots):
                shot.update(dt)
                # fuera de pantalla
                if shot.y < -50:
                    try:
                        player.shots.remove(shot)
                    except ValueError:
                        pass
                    continue
                # colisión con pollos
                for ch in list(chickens):
                    if ch.rect.colliderect(shot.rect):
                        try:
                            player.shots.remove(shot)
                        except ValueError:
                            pass
                        died = ch.hit(1)
                        if died:
                            try:
                                chickens.remove(ch)
                            except ValueError:
                                pass
                            score += settings.SCORE_PER_CHICKEN * level
                            # chance powerup drop
                            if random.random() < settings.CHICKEN_DROP_POWERUP_PROB:
                                pu_type = random.choice(settings.POWERUP_TYPES)
                                powerups.append(PowerUp(ch.x, ch.y, pu_type))
                            if s_chicken:
                                try:
                                    s_chicken.play()
                                except Exception:
                                    pass
                        break
                # colisión con asteroides
                for a in list(asteroids):
                    if a.rect.colliderect(shot.rect):
                        try:
                            player.shots.remove(shot)
                        except ValueError:
                            pass
                        died = a.hit()
                        if died:
                            try:
                                asteroids.remove(a)
                            except ValueError:
                                pass
                            score += settings.SCORE_PER_ASTEROID * level
                        break

            # actualizar pollos (movimiento, posibilidad de soltar huevo)
            for ch in list(chickens):
                ch.update(dt)
                # intentar soltar huevo
                if ch.try_drop_egg():
                    eggs.append(Egg(ch.x, ch.y + 10, vy=settings.BASE_EGG_FALL_SPEED))
                # si llegan al suelo -> penalizar (simplemente quitar vida)
                if ch.y >= settings.HEIGHT - 60:
                    try:
                        chickens.remove(ch)
                    except ValueError:
                        pass
                    player.lives -= 1
                    if player.lives <= 0:
                        state = 'gameover'

            # actualizar huevos
            for egg in list(eggs):
                egg.update(dt)
                # colisión con jugador
                if not egg.cracked and egg.rect.colliderect(player.rect):
                    eggs.remove(egg)
                    player.lives -= 1
                    player.reset_weapons()  # reiniciar armas (no tocar vidas)
                    if player.lives <= 0:
                        state = 'gameover'
                elif egg.off_screen(settings.HEIGHT):
                    try:
                        eggs.remove(egg)
                    except ValueError:
                        pass

            # actualizar asteroides
            for a in list(asteroids):
                a.update(dt)
                if a.off_screen(settings.HEIGHT):
                    try:
                        asteroids.remove(a)
                    except ValueError:
                        pass
                # colisión con jugador
                if a.rect.colliderect(player.rect):
                    try:
                        asteroids.remove(a)
                    except ValueError:
                        pass
                    player.lives -= 1
                    player.reset_weapons()
                    if player.lives <= 0:
                        state = 'gameover'

            # actualizar powerups (caída y recogida)
            for pu in list(powerups):
                pu.update(dt)
                if pu.off_screen(settings.HEIGHT):
                    try:
                        powerups.remove(pu)
                    except ValueError:
                        pass
                elif pu.rect.colliderect(player.rect):
                    pu.apply(player)
                    try:
                        powerups.remove(pu)
                    except ValueError:
                        pass

            # si ya no quedan enemigos -> siguiente nivel
            if not chickens and not asteroids:
                level += 1
                if is_asteroid_phase(level):
                    asteroids = spawn_asteroid_wave(level)
                    phase_text = 'Fase de asteroides'
                else:
                    chickens = spawn_chicken_wave(level)
                    phase_text = 'Fase de pollos'
                state = 'phase'
                show_phase_timer = 2.0

        # Phase timer
        if state == 'phase':
            show_phase_timer -= dt
            if show_phase_timer <= 0:
                state = 'playing'

        # Dibujado
        screen.fill(settings.BLACK)
        draw_stars(screen, stars)

        # Dibujar entidades
        for ch in chickens:
            ch.draw(screen)
        for egg in eggs:
            egg.draw(screen)
        for a in asteroids:
            a.draw(screen)
        for pu in powerups:
            pu.draw(screen)

        # Dibujar HUD y jugador
        player.draw(screen)

        # HUD
        hud_text = f'Vidas: {player.lives}    Puntos: {score}    Arma: {player.weapon_type} (lvl {player.weapon_level})    Nivel: {level}'
        hud_img = font_med.render(hud_text, True, settings.WHITE)
        screen.blit(hud_img, (10, 10))

        if state == 'menu':
            draw_text_center(screen, 'CHICKEN INVADERS', font_big, settings.WHITE, (settings.WIDTH//2, settings.HEIGHT//2 - 80))
            draw_text_center(screen, 'ENTER = Jugar   ESC = Salir', font_med, settings.WHITE, (settings.WIDTH//2, settings.HEIGHT//2 + 10))
        elif state == 'phase':
            draw_text_center(screen, phase_text, font_big, settings.YELLOW, (settings.WIDTH//2, settings.HEIGHT//2))
        elif state == 'gameover':
            draw_text_center(screen, 'GAME OVER', font_big, settings.RED, (settings.WIDTH//2, settings.HEIGHT//2 - 80))
            draw_text_center(screen, f'Puntuación: {score}', font_med, settings.WHITE, (settings.WIDTH//2, settings.HEIGHT//2))
            draw_text_center(screen, 'R = Volver al menú   ESC = Salir', font_med, settings.WHITE, (settings.WIDTH//2, settings.HEIGHT//2 + 60))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# Helpers

def is_asteroid_phase(level):
    # Niveles 5,10,15... -> asteroides
    return level % 5 == 0


def spawn_chicken_wave(level):
    # Genera una lista de entidades Chicken aplicando multiplicadores y límites.
    rows = min(settings.MAX_CHICKEN_ROWS, int(settings.BASE_CHICKEN_ROWS * (settings.MULT_CHICKEN_ROWS ** (level-1))))
    cols = min(settings.MAX_CHICKEN_COLS, int(settings.BASE_CHICKEN_COLS * (settings.MULT_CHICKEN_COLS ** (level-1))))
    speed = min(settings.MAX_CHICKEN_SPEED, settings.BASE_CHICKEN_SPEED * (settings.MULT_CHICKEN_SPEED ** (level-1)))
    hp = int(max(1, settings.BASE_CHICKEN_HP * (settings.MULT_CHICKEN_HP ** (level-1))))
    chickens = []
    spacing_x = settings.WIDTH // (cols + 1) if cols > 0 else settings.WIDTH // 6
    spacing_y = 50
    # drop probability escalado
    drop_prob = min(settings.MAX_CHICKEN_EGG_PROB, settings.BASE_CHICKEN_EGG_PROB * (settings.MULT_CHICKEN_EGG_PROB ** (level-1)))
    for r in range(rows):
        for c in range(cols):
            x = (c + 1) * spacing_x
            y = 50 + r * spacing_y
            chickens.append(Chicken(x, y, speed, hp, level, drop_prob=drop_prob))
    return chickens

def spawn_asteroid_wave(level):
    count = min(settings.MAX_ASTEROID_COUNT, int(settings.BASE_ASTEROID_COUNT * (settings.MULT_ASTEROID_COUNT ** (level-1))))
    speed = min(settings.MAX_ASTEROID_SPEED, settings.BASE_ASTEROID_SPEED * (settings.MULT_ASTEROID_SPEED ** (level-1)))
    asts = []
    for _ in range(count):
        x = random.randint(50, settings.WIDTH - 50)
        y = random.randint(-300, -50)
        asts.append(Asteroid(x, y, speed, int(settings.BASE_ASTEROID_HP * (settings.MULT_ASTEROID_HP ** (level-1)))))
    return asts
