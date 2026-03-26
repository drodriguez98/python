import pyttsx3
import keyboard
import webbrowser
import time
import io
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from scipy.io.wavfile import write as wav_write
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
    "nba": "D:\\SteamLibrary\\steamapps\\common\\NBA 2K23\\NBA2K23.exe",
    "outlast": "D:\\SteamLibrary\\steamapps\\common\\Outlast\\OutlastLauncher.exe",
    "outlast 2": "D:\\SteamLibrary\\steamapps\\common\\Outlast 2\\Binaries\\Win64\\Outlast2.exe",
    "risk": "D:\\SteamLibrary\\steamapps\\common\\RISK Global Domination\\RISK.exe",
    "rocket league": "D:\\games\\rocketleague\\Binaries\\Win64\\RocketLeague.exe",
    "warzone": "D:\\games\\Call of Duty\\Call of Duty Launcher.exe",
    "wrc": "D:\\SteamLibrary\\steamapps\\common\\WRC 10 FIA World Rally Championship\\WRC10.exe",
    "x defiant": "D:\\games\\XDefiant\\XDefiant.exe",
}

SAMPLE_RATE = 16000  # 16kHz es suficiente para voz y más liviano
DURACION    = 5      # segundos de grabación por comando

# Función para configurar e inicializar el motor de voz
def inicializarVoz():
    motor = pyttsx3.init()
    motor.setProperty('rate', 125)
    motor.setProperty('volume', 0.85)
    return motor

# Función para convertir texto a voz
def hablar(motor, texto):
    motor.say(texto)
    motor.runAndWait()

# Graba audio con sounddevice y lo convierte a AudioData de SpeechRecognition
def grabarAudio(duracion=DURACION, samplerate=SAMPLE_RATE):
    print("Escuchando...")
    grabacion = sd.rec(
        int(duracion * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16"
    )
    sd.wait()  # espera a que termine la grabación

    # Convertir numpy array -> WAV en memoria -> AudioData
    buffer = io.BytesIO()
    wav_write(buffer, samplerate, grabacion)
    buffer.seek(0)
    audio_data = sr.AudioData(buffer.read(), samplerate, 2)
    return audio_data

# Función para reconocer el input de voz del usuario
def reconocerVoz(idioma="es-ES"):
    recognizer = sr.Recognizer()
    audio = grabarAudio()
    try:
        resultado = recognizer.recognize_google(audio, language=idioma)
        print(f"Tú: {resultado}")
        return resultado.lower()
    except sr.UnknownValueError:
        return "No entendí lo que dijiste."
    except sr.RequestError:
        return "Error al conectar con el servicio de reconocimiento de voz."

# Función para realizar una búsqueda en Google
def realizarBusqueda(busqueda):
    url = f"https://www.google.com/search?q={busqueda}"
    webbrowser.open(url)
    return f"Buscando {busqueda} en Google."

# Función para abrir un juego
def abrirJuego(ruta):
    if os.path.exists(ruta):
        os.startfile(ruta)
        return "Abriendo el juego solicitado."
    else:
        return "No se encontró el juego solicitado."

def main():
    motor = inicializarVoz()
    hablar(motor, "Hola, estoy listo para ayudarte.")
    print("Mantén presionada la tecla F7 para hablar.")

    while True:
        if keyboard.is_pressed('F7'):
            hablar(motor, "¿Qué deseas hacer?")
            comando = reconocerVoz()

            if "salir" in comando or "adiós" in comando:
                hablar(motor, "Hasta luego.")
                break

            elif "buscar" in comando:
                hablar(motor, "¿Qué deseas buscar?")
                busqueda = reconocerVoz()
                resultado = realizarBusqueda(busqueda)
                hablar(motor, resultado)

            elif "abrir juego" in comando:
                hablar(motor, "¿Qué juego deseas abrir?")
                juego = reconocerVoz()
                if juego not in diccionarioJuegos:
                    hablar(motor, "Intentaré detectar el idioma del nombre.")
                    juego = reconocerVoz(idioma="en-US")
                if juego in diccionarioJuegos:
                    ruta = diccionarioJuegos[juego]
                    resultado = abrirJuego(ruta)
                    hablar(motor, resultado)
                else:
                    hablar(motor, "No tengo registrado ese juego.")

            else:
                hablar(motor, "No reconozco ese comando.")

        time.sleep(0.1)

if __name__ == "__main__":
    main()