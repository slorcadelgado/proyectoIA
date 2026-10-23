import json
import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

#Constantes
MODELO = "gemini-3.6-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")
PRECIO_ENTRADA = 0.00000075
PRECIO_SALIDA = 0.00000375

#Función para crear la solicitud
def armar_peticion(modelo, pregunta, system_instruction, response_schema=None):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
    body = {
        "systemInstruction": {
            "parts": [ {"text": system_instruction} ]
        },
        "contents": [{
            "parts": [{
                "text": pregunta
            }]
        }]
    }
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    return url, body

def armar_peticion_viejo(modelo, pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
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
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"La respuesta no recibe el texto generado en el lugar esperado: {e}")

def obtener_dato_de_prueba(pregunta):
    system_instruction = "Eres un asistente amigable y respondes en máximo 2 palabras."
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "nivel": {"type": "NUMBER"}
        },
        "required": ["categoria", "nivel"]
    }
    url, body = armar_peticion(MODELO, pregunta, system_instruction, response_schema)
    inicio = time.perf_counter()
    datos = enviar_peticion(url, body)
    fin = time.perf_counter()
    print(f"Latencia de la petición: {fin - inicio:.2f} segundos")
    costo = calcular_costo(datos, PRECIO_ENTRADA, PRECIO_SALIDA)
    print(f"Costo de la petición: ${costo:.6f} USD")
    texto = extraer_texto(datos)
    datos_formateados = parsear_respuesta_json(texto, ["categoria", "nivel"])
    return datos_formateados

def calcular_costo(datos: dict, precio_entrada: float, precio_salida: float) -> float:
    try:
        uso = datos["usageMetadata"]
        tokens_entrada = uso["promptTokenCount"] if "promptTokenCount" in uso else 0
        tokens_salida = uso["candidatesTokenCount"] if "candidatesTokenCount" in uso else 0
        tokens_razonamiento = uso["thoughtsTokenCount"] if "thoughtsTokenCount" in uso else 0
        costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
        return costo
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"No se pudo calcular el costo debido a la falta de información en la respuesta: {e}")

def parsear_respuesta_json(texto, claves_requeridas=None):
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio) 
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al decodificar JSON: {e}")
    
    if claves_requeridas:
        faltantes = [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError(f"La respuesta no tiene la estructura esperada: {faltantes}")
    return datos

if __name__ == "__main__":
    try:
        print(obtener_dato_de_prueba("Confirma si la conexión con Gemini funciona correctamente."))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")