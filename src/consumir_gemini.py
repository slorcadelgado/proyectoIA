import os
import requests
from dotenv import load_dotenv

load_dotenv()

def obtener_dato_de_prueba(pregunta):
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = {
        0: "gemini-flash-latest",
        1: "gemini-3.8-flash"
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo[0]}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "contents": [{
            "parts": [{
                "text": pregunta
            }]
        }]
    }
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))