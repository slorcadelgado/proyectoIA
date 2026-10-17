import os
import requests
from dotenv import load_dotenv

load_dotenv()

#Constantes
MODELO = "gemini-flash-latest"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#Función para crear la solicitud
def armar_peticion(pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{MODELO}:generateContent?key={API_KEY}"
    body = {
        "contents": [{
            "parts": [{
                "text": pregunta
            }]
        }]
    }
    return url, body

#Función envía la petición
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Error de conexión: {e}")
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Tiempo de espera agotado: {e}")
    
    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la solicitud: {respuesta.status_code} - {respuesta.text}")
    
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError as e:
        raise RuntimeError(f"Error al decodificar la respuesta JSON: {e}")

#Función procesa y extrae dato
def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no recibe el texto generado en el lugar esperado")

def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)

try:
    print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
except (ValueError, RuntimeError) as e:
    print(f"Error: {e}")