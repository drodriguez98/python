import pyttsx3
import keyboard
import webbrowser
import time
from datetime import datetime
import speech_recognition as sr
import os

# Diccionario con las rutas de los juegos instalados
diccionarioJuegos = {
    "assetto corsa": "D:\\SteamLibrary\\steamapps\\common\\assettocorsa\\AssettoCorsa.exe",
    "dirt rally": "D:\\SteamLibrary\\steamapps\\common\\DiRT Rally 2.0\\dirtrally2.exe",
    "fifa": "D:\\games\\EA SPORTS FC 24\\FC24.exe",
    "formula 1": "D:\\SteamLibrary\\steamapps\\common\\F1 2021\\F1_2021_dx12.exe",
    "gta 4": "D:\\games\\Grand Theft Auto IV\\GTAIV.exe",
    "gta 5": "D:\\games\\Grand Theft Auto V\\GTA5.exe",
    "monopoly": "D:\\games\\Monopoly Plus\\Monopoly.exe",
    "nba ": "D:\\SteamLibrary\\steamapps\\common\\NBA 2K23\\NBA2K23.exe",
    "outlast": "D:\\SteamLibrary\\steamapps\\common\\Outlast\\OutlastLauncher.exe",
    "outlast 2": "D:\\SteamLibrary\\steamapps\\common\\Outlast 2\\Binaries\\Win64\\Outlast2.exe",
    "risk": "D:\\SteamLibrary\\steamapps\\common\\RISK Global Domination\\RISK.exe",
    "rocket league": "D:\\games\\rocketleague\\Binaries\\Win64\\RocketLeague.exe",
    "warzone": "D:\\games\\Call of Duty\\Call of Duty Launcher.exe",
    "wrc": "D:\\SteamLibrary\\steamapps\\common\\WRC 10 FIA World Rally Championship\\WRC10.exe",    
    "x defiant": "D:\\games\\XDefiant\\XDefiant.exe",
    # Agregar más juegos o aplicaciones y sus rutas aquí
}

# Función para configurar e inicializar el motor de voz
def inicializarVoz():
    motor = pyttsx3.init()
    motor.setProperty('rate', 125)  # Velocidad del habla
    motor.setProperty('volume', 0.85)  # Volumen
    return motor

# Función para convertir texto a voz
def hablar(motor, texto):
    motor.say(texto)
    motor.runAndWait()

# Función para reconocer el input de voz del usuario
def reconocerVoz(idioma="es-ES"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        audio = recognizer.listen(source)
    try:
        input = recognizer.recognize_google(audio, language=idioma)
        print(f"Tú: {input}")
        return input.lower()
    except sr.UnknownValueError:
        return "No entendí lo que dijiste."
    except sr.RequestError:
        return "Error al conectar con el servicio de reconocimiento de voz."

# Función para realizar una búsqueda en Google
def realizarBusqueda(busqueda):
    url = f"https://www.google.com/search?q={busqueda}"
    webbrowser.open(url)
    return f"Buscando {busqueda} en Google."

# Función para abrir una juego
def abrirJuego(ruta):
    if os.path.exists(ruta):
        os.startfile(ruta)
        return f"Abriendo el juego solicitado."
    else:
        return "No se encontró el juego solicitado."

def main():
    # Inicializar el motor de voz
    motor = inicializarVoz()
    # Saludo inicial
    hablar(motor, "Hola, estoy listo para ayudarte.")
    print("Mantén presionada la tecla F7 para hablar.")
    # Bucle infinito hasta que el usuario diga "salir" o "adiós"
    while True:
        # Usar la tecla F7 para activar el asistente de voz
        if keyboard.is_pressed('F7'):
            hablar(motor, "¿Qué deseas hacer?")
            input = reconocerVoz()
            # Cerrar el asistente
            if "salir" in input or "adiós" in input:
                hablar(motor, "Hasta luego.")
                break
            # Hacer búsquedas en Google
            elif "buscar" in input:
                hablar(motor, "¿Qué deseas buscar?")
                busqueda = reconocerVoz()
                resultado_busqueda = realizarBusqueda(busqueda)
                hablar(motor, resultado_busqueda)
            # Abrir un juego
            elif "abrir juego" in input:
                hablar(motor, "¿Qué juego deseas abrir?")
                juego = reconocerVoz()
                # Detectar idioma automáticamente para el nombre del juego
                if juego not in diccionarioJuegos:
                    hablar(motor, "Intentaré detectar el idioma del nombre.")
                    juego = reconocerVoz(idioma="en-US")
                if juego in diccionarioJuegos:
                    ruta = diccionarioJuegos[juego]
                    resultado_apertura = abrirJuego(ruta)
                    hablar(motor, resultado_apertura)
                else:
                    hablar(motor, "No tengo registrado ese juego.")
            # inputs no reconocidos
            else:
                hablar(motor, "No reconozco ese input.")
        time.sleep(0.1)

if __name__ == "__main__":
    main()