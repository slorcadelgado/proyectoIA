from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import (RunnableBranch, RunnablePassthrough, RunnableLambda) #Bifurcaciones/Branches/Ramificaciones

import logging #Generar un archivo de log con los errores que se presenten

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", #2026-11-04 16:40 [WARNING] main: No se pudo ejecutar x
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="error.log",
    filemode="a", #Agrega al final del archivo la nueva línea
    encoding="utf-8",
    force=True
)
logger = logging.getLogger(__name__)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

def construir_paso_clasificacion(modelo):
    plantilla_clasificacion = PromptTemplate.from_template(
        "Clasifica el siguiente mensaje de soporte en una sola palabra: "
        "pregunta, queja o sugerencia. Responde solo con esa palabra. \n\n {mensaje}"
    )

    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

paso_clasificacion = construir_paso_clasificacion(modelo)

# mensaje_prueba = "Dame el nombre de tu creador."

# clasificacion = paso_clasificacion.invoke(
#     {"mensaje": mensaje_prueba}
# )

# print(clasificacion)

cadena_pregunta = (
    PromptTemplate.from_template("Responde esta pregunta técnica con precisión: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template("Responde esta queja con empatía, reconociendo el problema antes de ofrecer una solución: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template("Agradece esta sugerencia y explica cómo se evaluará dentro del producto: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

#Sintaxis RunnableBranch
# caminos = RunnableBranch(
#     (condicion_1, rama_1), #if
#     (condicion_2, rama_2), #elif
#     (condicion_3, rama_3), #elif
#     rama_por_defecto #else
# ) #Cada condicion debe ser una función; suele ser un lambda


def construir_cadena_con_enrutamiento(paso_clasificacion, cadena_queja=None, cadena_sugerencia=None, cadena_pregunta=None):
    # Si una rama no se pasa, RunnablePassthrough la reemplaza: nunca se ejecuta, salvo que la clasificación la elija
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()

    #x = {"categoria": "queja", "mensaje": "Mi teléfono no funciona"}
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja), #if x["categoria"] == "queja": cadena_queja
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia), #elif x["categoria"] == "sugerencia": cadena_sugerencia
        cadena_pregunta #else: cadena_pregunta
    )

    return (
        RunnablePassthrough.assign(categoria=paso_clasificacion) #{"mensaje": "Deberían de tener más agentes disponibles.", "categoria":resultado de paso_clasificacion}
        | bifurcacion
    )

cadena_con_enrutamiento = construir_cadena_con_enrutamiento(paso_clasificacion, cadena_queja, cadena_sugerencia, cadena_pregunta)

#Fallback: cadena de respaldo. Captura las caídas de mi LLM (RateLimitError, 401, APIConnectionError, respuestas vacías)

def fallback_con_log(x):
    logger.warning("Cadena principal falló. Activando respuesta genérica, Error: %s", x.get("error"))
    return "Gracias por tu mensaje. Un miembro de nuestro equipo te va a responder pronto."

respuesta_generica = RunnableLambda(
    fallback_con_log
)

cadena_robusta = cadena_con_enrutamiento.with_fallbacks([respuesta_generica], exception_key="error")

def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)
        return "No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde"

if __name__ == "__main__": #Solamente ejecuta el siguiente bloque de código si la ejecución es directa del archivo. NO EJECUTES si es import
    mensajes = [
        "¿Cómo cambio mi contraseña?",
        "La app se cierra cada vez que subo una foto.",
        "Estaría bueno que la app tuviera modo oscuro.",
    ]
    # Imprime la categoría que devuelve la clasificación, sin llamadas extra a la API
    paso_clasificacion_visible = paso_clasificacion | RunnableLambda(lambda categoria: print(f"Categoría: {categoria}") or categoria)
    cadena_demo = construir_cadena_con_enrutamiento(paso_clasificacion_visible, cadena_queja, cadena_sugerencia, cadena_pregunta)
    cadena_demo_robusta = cadena_demo.with_fallbacks([respuesta_generica], exception_key="error")
    for mensaje in mensajes:
        print(procesar_mensaje_seguro(cadena_demo_robusta, mensaje))


# Entrada inicial: {"mensaje": "Deberían de tener más agentes disponibles."}
#                   │
#                   ▼
# RunnablePassthrough
#   1: Pasa el mensaje a paso_clasificacion -> Return "sugerencia"
#   2: Fusiono clasificacion y mensaje
#   3: Return {"mensaje": "Deberían de tener más agentes disponibles.", "clasificacion": "sugerencia"}
#                   │
#                   ▼
# bifurcacion (RunnableBranch)
#   ¿clasificacion == "queja"? NO
#   ¿clasificacion == "sugerencia" SI
#       Entra a la cadena_sugerencia
#       cadena_sugerencia.invoke({"mensaje": "Deberían de tener más agentes disponibles.", "clasificacion": "sugerencia"})
#       Return respuesta final generada