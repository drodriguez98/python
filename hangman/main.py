#   https://www.youtube.com/watch?v=tWnyBD2src0

import random 
import string

from palabras import palabras
from diagramas import vidas_diccionario_visual


#   Función que selecciona una palabra al azar de la lista de palabras válidas. Si la palabra tiene un espacio en blanco o un guión, busca una nueva palabra. Si realmente es válida recgemos su valor en letras mayúsculas.

def obtener_palabra_valida(lista_palabras):

    palabra = random.choice(palabras)

    while '-' in palabra or ' ' in palabra:

        palabra = random.choice(palabras)
    
    return palabra.upper()


#   Función princiopal. Llama a la función anterior para obtener una palabra.

def main():

    print ("=================================")
    print ("Bienvenido al juego del ahorcado")
    print ("=================================")

    palabra = obtener_palabra_valida(palabras)

    #   Hace un subconjunto con las letras que componen la palabra que obtiene y otro con las letras que va adivinando el jugador con la función set. Genera todas las letras del abecedario con la función string.

    letras_por_adivinar = set(palabra)
    letras_adivinadas = set()
    abecedario = set(string.ascii_uppercase)

    vidas = 7

    #   Mientras el juego no finalice...

    while len(letras_por_adivinar) > 0 and vidas > 0:

        print(f"Te quedan {vidas} vidas y has usado estas letras: {' '.join(letras_adivinadas)}")

        #   Estado actual de la palabra

        palabra_lista = [letra if letra in letras_adivinadas else '-' for letra in palabra]

        #   Estado del ahorcado

        print(vidas_diccionario_visual[vidas])

        #   Letras separadas por un espacio

        print (f"Palabra: {' '.join(palabra_lista)}")

        #   Si la letra escogida por el usuario está en el abecedario y no está en el conjunto de letras que ya se han ingresado, se añade la letra al conjunto de letras ingresadas. Si la letra ya ha sido ingresada anteriormente se pode introducir una nueva, y si no cumple ninguna de las condiciones decimos que no es válida..

        letra_usuario = input("Escoge una letra: ").upper()

        if letra_usuario in abecedario - letras_adivinadas:

            letras_adivinadas.add(letra_usuario)

            #   Si la letra ingresada está en la palabra quitamos la letra del conjunto de letras pendientes por adivinar. Si no está en la palabra restamos una vida.

            if letra_usuario in letras_por_adivinar:

                letras_por_adivinar.remove(letra_usuario)
                print('')
            
            else: 

                vidas = vidas - 1
                print(f"\n La letra {letra_usuario} no está en la palabra.")
        
        elif letra_usuario in letras_adivinadas:

            print("\n Ya escogiste esta letra. Por favor, introduce una nueva.")

        else:

            print("\n Esta letra no es válida.")
    
    #   Si se adivinan todas las letras de la palabra o se agotan las vidas del jugador...

    if vidas == 0:

        print(vidas_diccionario_visual[vidas])
        print(f"Ahorcado! La palabra era {palabra}")

    else:

        print(f" Enhorabuena! Adivinaste la palabra.")


#   Llamamos a la función principal de nuestro juego

main()