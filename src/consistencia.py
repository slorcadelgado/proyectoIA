import json
import time
from prompts.banco import BANCO_DE_PROMPT
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json

MODELO = "gemini-3.6-flash"
RUTA_REGISTRO = "src/prompts/registro_resultados.json"
INTENTOS = 3
# El plan gratuito permite 5 peticiones por minuto para este modelo
PAUSA_ENTRE_PETICIONES = 13
REINTENTOS_TEMPORALES = 4
ESPERA_BASE = 15

registro = {}

def guardar_registro():
    with open(RUTA_REGISTRO, "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

def enviar_con_reintentos(url, body):
    for intento in range(1, REINTENTOS_TEMPORALES + 1):
        try:
            return enviar_peticion(url, body)
        except RuntimeError as e:
            temporal = "429" in str(e) or "503" in str(e)
            if not temporal or intento == REINTENTOS_TEMPORALES:
                raise
            espera = ESPERA_BASE * intento
            print(f"  Límite o servidor ocupado, reintento {intento} en {espera}s...")
            time.sleep(espera)

for prompt in BANCO_DE_PROMPT:
    exitos = 0
    errores = []
    for intento in range(INTENTOS):
        try:
            url, body = armar_peticion(
                MODELO,
                prompt["ejemplo_usuario"],
                prompt["system_instruction"],
                prompt["response_schema"],
            )
            respuesta = enviar_con_reintentos(url, body)
            datos = parsear_respuesta_json(extraer_texto(respuesta), prompt["claves_esperadas"])
            exitos += 1
            print(f"Respuesta: {datos}")
        except (ValueError, RuntimeError) as e:
            errores.append(str(e)[:200])
            print(f"Intento {intento + 1} falló: {e}")
        time.sleep(PAUSA_ENTRE_PETICIONES)
    print(f"Prompt '{prompt['nombre']}': {exitos}/{INTENTOS} respuestas válidas.")
    registro[prompt["nombre"]] = {
        "exitos": exitos,
        "intentos": INTENTOS,
        "errores": errores,
    }
    guardar_registro()
