# pip install pygame os-sys

# imports

import pygame
import os

# Iniciar módulos y mixer para dibujar textos en pantalla e introducir sonidos.

pygame.font.init()
pygame.mixer.init()

# Constantes.

# Tamaño de la ventana principal.

WIDTH, HEIGHT = 900, 500   
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))

# Título.

pygame.display.set_caption("SpaceWar!")

# Colores.

WHITE = (255, 255 , 255)
BLACK = (0, 0, 0)
RED  = (255, 0, 0)
YELLOW = (255, 255, 0)

# Borde central.

BORDER_CENTER = pygame.Rect(WIDTH/2 - 5, 0, 10, HEIGHT)

# Sonidos.

COLLISION_SOUND = pygame.mixer.Sound('assets/collision.wav')
SHOOTING_SOUND = pygame.mixer.Sound('assets/shot.wav')

# Texto para las vidas y mostrar ganador.

FONT_LIVE = pygame.font.SysFont('comicsans', 20)
FONT_WINNER = pygame.font.SysFont('comicsans', 20)

# Fotogramas por segundo y velocidad de movimiento. Cada vez que un usuario pulse una tecla, la nave se moverá 5 px.

FPS = 60
SPEED = 5

# Número de balas que puede disparar una nave a la vez y velocidad.

MAX_BULLETS = 3
SPEED_BULLETS = 7

# Eventos para cuando una de las naves colisiona con una bala.

YELLOW_SHIP_COLLISION = pygame.USEREVENT + 1
RED_SHIP_COLLISION = pygame.USEREVENT + 2

# Rutas a las imágenes, dimensiones y rotación de las naves.

YELLOW_SHIP_IMG = pygame.image.load(os.path.join('assets', 'yellow-ship.png'))
RED_SHIP_IMG = pygame.image.load(os.path.join('assets', 'red-ship.png'))

SHIP_WIDTH, SHIP_HEIGHT = 90, 70

YELLOW_SHIP = pygame.transform.rotate(pygame.transform.scale(YELLOW_SHIP_IMG, (SHIP_WIDTH, SHIP_HEIGHT)), 90)
RED_SHIP = pygame.transform.rotate(pygame.transform.scale(RED_SHIP_IMG, (SHIP_WIDTH, SHIP_HEIGHT)), 270)

SPACE = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'background.png')), (WIDTH, HEIGHT))


# Función para mostrar la ventana de juego.

def showWindow(redRectangle, yellowRectangle, redBullets, yellowBullets, redShipLive, yellowShipLive):

  WINDOW.blit(SPACE, (0, 0))
  pygame.draw.rect(WINDOW, BLACK, BORDER_CENTER)

  WINDOW.blit(YELLOW_SHIP, (yellowRectangle.x, yellowRectangle.y))
  WINDOW.blit(RED_SHIP, (redRectangle.x, redRectangle.y))

  redShipLiveText = FONT_LIVE.render("Vidas: " + str(redShipLive), 1, WHITE)
  yellowShipLiveText = FONT_LIVE.render("Vidas: " +str(yellowShipLive), 1, WHITE)

  WINDOW.blit(redShipLiveText, (WIDTH - redShipLiveText.get_width() - 10, 10))
  WINDOW.blit(yellowShipLiveText, (10, 10))

  for bullet in redBullets:

    pygame.draw.rect(WINDOW, RED, bullet)

  for bullet in yellowBullets:

    pygame.draw.rect(WINDOW, YELLOW, bullet)

  pygame.display.update()


# Función para controlar el movimiento de la nave amarilla.

def yellowShipMovement (pressedKeys, yellowRectangle):

  if pressedKeys[pygame.K_a] and yellowRectangle.x - SPEED > 0:

    yellowRectangle.x -= SPEED

  if pressedKeys[pygame.K_d] and yellowRectangle.x + SPEED + yellowRectangle.width < BORDER_CENTER.x:

    yellowRectangle.x += SPEED

  if pressedKeys[pygame.K_w] and yellowRectangle.y - SPEED > 0:

    yellowRectangle.y -= SPEED
  
  if pressedKeys[pygame.K_s] and yellowRectangle.y + SPEED + yellowRectangle.height < HEIGHT - 15:

    yellowRectangle.y += SPEED


# Función para controlar el movimiento de la nave roja.

def redShipMovement (pressedKeys, redRectangle):

  if pressedKeys[pygame.K_LEFT] and redRectangle.x - SPEED > BORDER_CENTER.x + BORDER_CENTER.width:

    redRectangle.x -= SPEED

  if pressedKeys[pygame.K_RIGHT] and redRectangle.x + SPEED + redRectangle.width < WIDTH:

    redRectangle.x += SPEED

  if pressedKeys[pygame.K_UP] and redRectangle.y - SPEED > 0:

    redRectangle.y -= SPEED
  
  if pressedKeys[pygame.K_DOWN] and redRectangle.y + SPEED + redRectangle.height < HEIGHT - 15:

    redRectangle.y += SPEED


# Función para el movimiento de las balas y detectar colisiones. 

def bulletsMovement(redBullets, yellowBullets, redRectangle, yellowRectangle):

  # Balas de la nave amarilla.

  for bullet in yellowBullets:

    bullet.x -= SPEED_BULLETS

    if redRectangle.colliderect(bullet):

      yellowBullets.remove(bullet)
      pygame.event.post(pygame.event.Event(RED_SHIP_COLLISION))

    elif bullet.x < 0:

      yellowBullets.remove(bullet)

  # Balas de la nave roja.

  for bullet in redBullets:

    bullet.x += SPEED_BULLETS

    if yellowRectangle.colliderect(bullet):

      redBullets.remove(bullet)
      pygame.event.post(pygame.event.Event(YELLOW_SHIP_COLLISION))
      
    elif bullet.x > WIDTH:

      redBullets.remove(bullet)


# Función para mostrar un texto felicitando al ganador.

def showWinner(text):

  showText = FONT_WINNER.render(text, 1, WHITE)
  WINDOW.blit(showText, (WIDTH / 2 - showText.get_width() / 2, HEIGHT / 2 - showText.get_height() / 2))

  pygame.display.update()
  pygame.time.delay(5000)


# Función principal.

def main():

  # Rectángulos que representan las naves (rect)

  redRectangle = pygame.Rect(700,300, SHIP_WIDTH, SHIP_HEIGHT)
  yellowRectangle = pygame.Rect(100,300, SHIP_WIDTH, SHIP_HEIGHT)

  # Balas que aún están en el mapa. Las que colisionan con la otra nave o se salen del mapa se eliminan de la lista.

  yellowBullets = []
  redBullets = []

  # Vidas.

  yellowShipLive = 10
  redShipLive = 10

  # Reloj.

  clock = pygame.time.Clock()

  # Bucle infinito.

  running = True

  while running:

    clock.tick(FPS)

    # Lista de eventos con los botones y teclas que pulsa cada jugador. 

    for event in pygame.event.get():

      # Botón de salir

      if event.type == pygame.QUIT:
        
          running = False
          pygame.quit()
      
      # Botones de disparar.

      if event.type == pygame.KEYDOWN:

        # Nave amarilla (control izquierda).

        if event.key == pygame.K_LCTRL and len(yellowBullets) < MAX_BULLETS:

          bullet = pygame.Rect(yellowRectangle.x + yellowRectangle.width,  yellowRectangle.y + yellowRectangle.height // 2 + 5, 10, 5)

          yellowBullets.append(bullet)

          SHOOTING_SOUND.play()

        # Nave roja (control derecha).
  
        if event.key == pygame.K_RCTRL and len(redBullets) < MAX_BULLETS:

          bullet = pygame.Rect(redRectangle.x + redRectangle.width,  redRectangle.y + redRectangle.height // 2 + 5, 10, 5)

          redBullets.append(bullet)

          SHOOTING_SOUND.play()
      
      # Si se produce una colisión se resta una vida a la nave y se reproduce un sonido.
      
      if event.type == YELLOW_SHIP_COLLISION:

        redShipLive -= 1
        COLLISION_SOUND.play()

      if event.type == RED_SHIP_COLLISION:

        yellowShipLive -= 1
        COLLISION_SOUND.play()   

    # Comprobar si hay un ganador.
    
    winnerText = ""

    if redShipLive <= 0:

      winnerText = "Congratulations yellow ship! You have won the game"

    if yellowShipLive <= 0:

      winnerText = "Congratulations red ship! You have won the game"

    if winnerText != "":

      showWinner(winnerText)
      break
    
    pressedKeys = pygame.key.get_pressed()

    yellowShipMovement(pressedKeys, yellowRectangle)
    redShipMovement(pressedKeys, redRectangle)
    bulletsMovement(yellowBullets, redBullets, yellowRectangle, redRectangle) 
    showWindow(redRectangle, yellowRectangle, redBullets, yellowBullets, redShipLive, yellowShipLive)

  main()


# Comprueba si es el archivo principal.

if __name__ == "__main__":

  main()