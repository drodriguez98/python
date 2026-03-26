# Imports.

import random, pygame, sys
from pygame.locals import *

# Constantes.

FPS = 15

WIDTH = 640
HEIGHT = 480

SIZE_CELL = 20
WIDTH_CELL = int(WIDTH / SIZE_CELL)
HEIGHT_CELL = int(HEIGHT / SIZE_CELL)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 155, 0)
DARK_GREY  = (40, 40, 40)

BACKGROUND_COLOR = BLACK

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0 

# Comprobar si el ancho y el alto de la ventana son múltiplos del tamaño de las celdas. 

assert WIDTH % SIZE_CELL == 0, "Window width must be a multiple of the cell size."
assert HEIGHT % SIZE_CELL == 0, " Window height must be a multiple of the cell size."


# Main.

def main():

    global CLOCK, WINDOW, FONT

    pygame.init()

    CLOCK = pygame.time.Clock()
    WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    FONT = pygame.font.Font('freesansbold.ttf', 18)

    pygame.display.set_caption('Snake!')

    showHomeScreen()

    while True:

        start()
        game_over()

# Start      

def start():

    # Posiciones y dirección iniciales del gusano y la manzana.
    
    x = random.randint(5, WIDTH_CELL - 6)
    y = random.randint(5, HEIGHT_CELL - 6)

    coordinates = [{'x': x, 'y': y},
                  {'x': x - 1, 'y': y},
                  {'x': x - 2, 'y': y}]

    direction = RIGHT

    apple = randomPosition()

    # Bucle infinito.
    
    while True:     

        for event in pygame.event.get(): 

            # Salir del juego.

            if event.type == QUIT:

                exit()

            # Cambiar de dirección.

            if event.type == KEYDOWN:

                if (event.key == K_LEFT or event.key == K_a) and direction != RIGHT:

                    direction = LEFT

                elif (event.key == K_RIGHT or event.key == K_d) and direction != LEFT:

                    direction = RIGHT

                elif (event.key == K_UP or event.key == K_w) and direction != DOWN:

                    direction = UP

                elif (event.key == K_DOWN or event.key == K_s) and direction != UP:

                    direction = DOWN

                elif event.key == K_ESCAPE:

                    exit()

        # Finalizar el juego si hay una colisión con los bordes.

        if coordinates[HEAD]['x'] == -1 or coordinates[HEAD]['x'] == WIDTH_CELL or coordinates[HEAD]['y'] == -1 or coordinates[HEAD]['y'] == HEIGHT_CELL:

            return 

        # Finalizar el juego si hay una colisión con la cola.

        for body in coordinates[1:]:

            if body['x'] == coordinates[HEAD]['x'] and body['y'] == coordinates[HEAD]['y']:

                return 
        
        # Reubicar la manzana si la cabeza del gusano toca la manzana. Si no, borrar el último segmento de la cola para dar efecto de movimiento.

        if coordinates[HEAD]['x'] == apple['x'] and coordinates[HEAD]['y'] == apple['y']:

            apple = randomPosition() 

        else:

            del coordinates[-1]     

        # Crear nueva cabeza en función de la dirección del gusano.

        if direction == UP:

            newHead = {'x': coordinates[HEAD]['x'], 'y': coordinates[HEAD]['y'] - 1}

        elif direction == DOWN:

            newHead = {'x': coordinates[HEAD]['x'], 'y': coordinates[HEAD]['y'] + 1}

        elif direction == LEFT:

            newHead = {'x': coordinates[HEAD]['x'] - 1, 'y': coordinates[HEAD]['y']}

        elif direction == RIGHT:

            newHead = {'x': coordinates[HEAD]['x'] + 1, 'y': coordinates[HEAD]['y']}

        coordinates.insert(0, newHead)

        # Mostrar los elementos actualizados en pantalla. Se actualizan continuamente según el valor de la constante FPS.

        WINDOW.fill(BACKGROUND_COLOR)
        showGrid()
        showWorm(coordinates)
        showAppel(apple)
        showPunctuation(len(coordinates) - 3)

        pygame.display.update()

        CLOCK.tick(FPS)

# Función para mostrar el texto de la pantalla inicial y game over.

def showPressKey():

    keyPressAnimation = FONT.render('Press any key to play', True, WHITE)
    straight_press_key = keyPressAnimation.get_rect()
    straight_press_key.topleft = (WIDTH - 300, HEIGHT - 30)

    WINDOW.blit(keyPressAnimation, straight_press_key)

# Función para comprobar si el usuario pulsa alguna de las teclas asociadas para salir.

def exitKeys():

    if len(pygame.event.get(QUIT)) > 0:

        exit()

    exitEvent = pygame.event.get(KEYUP)

    if len(exitEvent) == 0:

        return None

    if exitEvent[0].key == K_ESCAPE:

        exit()

    return exitEvent[0].key

# Función para mostrar la pantalla inicial y la animación.

def showHomeScreen():

    font = pygame.font.Font('freesansbold.ttf', 100)
    text1 = font.render('Snake!', True, WHITE, DARK_GREEN)
    text2 = font.render('Snake!', True, GREEN)

    degreesText1 = 0
    degreesText2 = 0

    # Bucle infinito que rota las animaciones mientras el usuario no pulsa ninguna tecla.

    while True:

        WINDOW.fill(BACKGROUND_COLOR)

        animation1 = pygame.transform.rotate(text1, degreesText1)
        straight1 = animation1.get_rect()
        straight1.center = (WIDTH / 2, HEIGHT / 2)
        WINDOW.blit(animation1, straight1)

        animation2 = pygame.transform.rotate(text2, degreesText2)
        straight2 = animation2.get_rect()
        straight2.center = (WIDTH / 2, HEIGHT / 2)
        WINDOW.blit(animation2, straight2)

        showPressKey()

        if exitKeys():

            pygame.event.get() 
            return

        pygame.display.update()

        CLOCK.tick(FPS)

        degreesText1 += 3   #   rota 3 grados por frame
        degreesText2 += 7   #   rota 7 grados por frame

# Función para salir del juego.

def exit():

    pygame.quit()
    sys.exit()

# Función para reubicar aleatoriamente la manzana.

def randomPosition():

    return {'x': random.randint(0, WIDTH_CELL - 1), 'y': random.randint(0, HEIGHT_CELL - 1)}

# Función para mostrar mensaje de game over.

def game_over():

    font = pygame.font.Font('freesansbold.ttf', 75)

    animationWord1 = font.render('Game', True, WHITE)
    animationWord2 = font.render('Over', True, WHITE)

    straightWord1 = animationWord1.get_rect()
    straightWord2 = animationWord2.get_rect()
    
    straightWord1.midtop = (WIDTH / 2, 10 + 140)
    straightWord2.midtop = (WIDTH / 2, straightWord1.height + 75 + 100)

    WINDOW.blit(animationWord1, straightWord1)
    WINDOW.blit(animationWord2, straightWord2)

    showPressKey()

    pygame.display.update()
    pygame.time.wait(500)

    exitKeys() 

    while True:

        if exitKeys():
            pygame.event.get() 
            return

# Función para mostrar la puntuación.

def showPunctuation(punctuation):

    animation = FONT.render('Score: %s' % punctuation, True, WHITE)
    straight = animation.get_rect()
    straight.topleft = (WIDTH - 150, 10)

    WINDOW.blit(animation, straight)

# Función para mostrar el gusano.

def showWorm(coordinates):

    for c in coordinates:

        x = c['x'] * SIZE_CELL
        y = c['y'] * SIZE_CELL

        straightSegment = pygame.Rect(x, y, SIZE_CELL, SIZE_CELL)
        pygame.draw.rect(WINDOW, DARK_GREEN, straightSegment)

        internalStraightSegment = pygame.Rect(x + 4, y + 4, SIZE_CELL - 8, SIZE_CELL - 8)
        pygame.draw.rect(WINDOW, GREEN, internalStraightSegment)

# Función para mostrar la manzana.

def showAppel(coordinates):

    x = coordinates['x'] * SIZE_CELL
    y = coordinates['y'] * SIZE_CELL
    straight = pygame.Rect(x, y, SIZE_CELL, SIZE_CELL)

    pygame.draw.rect(WINDOW, RED, straight)

# Función para mostrar la cuadrícula.

def showGrid():

    # Líneas verticales.

    for x in range(0, WIDTH, SIZE_CELL): 

        pygame.draw.line(WINDOW, DARK_GREY, (x, 0), (x, HEIGHT))

    # Líneas horizontales.

    for y in range(0, HEIGHT, SIZE_CELL): 

        pygame.draw.line(WINDOW, DARK_GREY, (0, y), (WIDTH, y))

# Comprueba si es el archivo principal.

if __name__ == '__main__':

    main()