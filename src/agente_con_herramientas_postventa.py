from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

import json
import select
import sys
from datetime import datetime, timezone

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

PEDIDOS = {
    1042: {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 17},
    1077: {"estado": "entregado", "categoria": "producto personalizado", "dias_desde_entrega": 2},
    1069: {"estado": "en_transito", "categoria": "electrónica", "dias_desde_entrega": None},
    1080: {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 3},
}

PLAZOS_DEVOLUCION = {
    "electrónica": 10,
    "ropa": 30,
}

#=== Auditoría y trazas ===
registro_aprobaciones = []

def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "fecha_hora": datetime.now().isoformat(),
    })

def registrar_traza(session_id: str, entrada: str, resultado: dict) -> None:
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": resultado.get("output", ""),
    }
    with open("trazas_postventa.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

#=== Aprobación humana ===
def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
    # Sin ninguna línea en stdin dentro del tiempo límite, se rechaza. No hay hilos en segundo plano:
    # una respuesta tardía no puede quedar pendiente para otra solicitud.
    # Usa select sobre stdin, así que solo funciona en Linux y macOS (WSL2 cuenta como Linux).
    print(mensaje, end="", flush=True)
    listos, _, _ = select.select([sys.stdin], [], [], tiempo_limite_segundos)
    if not listos:
        print("\nTiempo de espera agotado. Solicitud denegada por timeout")
        return False
    respuesta = sys.stdin.readline()
    return respuesta.strip().lower() == "s"

#=== Herramientas ===
@tool
def consultar_estado_pedido(numero_pedido: int) -> str:
    """
    Consulta el estado actual de un pedido a partir de su número.
    Usar cuando el cliente pregunta dónde está su pedido o en qué estado se encuentra.
    """
    try:
        pedido = PEDIDOS[numero_pedido]
    except KeyError:
        return f"No se encontró un pedido con el número {numero_pedido}."
    return f"El pedido {numero_pedido} está en estado: {pedido['estado']}."

@tool
def verificar_plazo_devolucion(categoria: str, dias_desde_entrega: int) -> str:
    """
    Indica si un producto sigue dentro del plazo de devolución según su categoría y los días desde la entrega.
    Categorías válidas: electrónica, ropa, producto personalizado. Si el producto no encaja en ninguna, indícalo al cliente sin volver a llamar a esta herramienta.
    Usar cuando el cliente pregunta si puede devolver un producto.
    """
    if categoria == "producto personalizado":
        return "Los productos personalizados no admiten devolución."
    plazo = PLAZOS_DEVOLUCION.get(categoria)
    if plazo is None:
        return f"No hay una política de devolución para la categoría '{categoria}'."
    if dias_desde_entrega <= plazo:
        return f"Está dentro del plazo: {dias_desde_entrega} de {plazo} días corridos."
    return f"Está fuera del plazo: {dias_desde_entrega} días, y el máximo es {plazo}."

def motivo_fuera_de_politica(numero_pedido: int) -> str | None:
    # Las mismas reglas que verificar_plazo_devolucion: solo pedidos entregados, dentro del plazo de su categoría
    pedido = PEDIDOS[numero_pedido]
    if pedido["estado"] != "entregado":
        return f"El pedido {numero_pedido} está en estado {pedido['estado']}; solo se reembolsan pedidos entregados."
    if pedido["categoria"] == "producto personalizado":
        return "Los productos personalizados no admiten devolución."
    plazo = PLAZOS_DEVOLUCION.get(pedido["categoria"])
    if plazo is None:
        return f"No hay una política de devolución para la categoría '{pedido['categoria']}'."
    if pedido["dias_desde_entrega"] > plazo:
        return f"El pedido {numero_pedido} está fuera del plazo: {pedido['dias_desde_entrega']} días, y el máximo es {plazo}."
    return None

@tool
def generar_reembolso(numero_pedido: int, monto: float) -> str:
    """
    Genera un reembolso para un pedido. Acción irreversible: requiere aprobación del personal de la tienda antes de ejecutarse.
    Usar cuando el cliente pide un reembolso de un pedido. No pidas confirmación al cliente antes de llamarla.
    """
    if numero_pedido not in PEDIDOS:
        return f"No se encontró un pedido con el número {numero_pedido}. No se generó ningún reembolso."

    motivo = motivo_fuera_de_politica(numero_pedido)
    if motivo is not None:
        return f"No se generó el reembolso. {motivo}"

    mensaje = f"[SUPERVISIÓN HUMANA REQUERIDA] El cliente solicita reembolsar ${monto} para el pedido {numero_pedido}. ¿Desea aprobar? (s/n): "
    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )

    if not aprobado:
        return "Reembolso no aprobado por el supervisor o cancelado por timeout."
    return f"Reembolso de {monto} aprobado por el personal de la tienda y generado con éxito para el pedido {numero_pedido}."

herramientas = [consultar_estado_pedido, verificar_plazo_devolucion, generar_reembolso]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente de postventa que responde en tú. Usa las herramientas disponibles para consultar pedidos, plazos y reembolsos. No inventes información que no obtengas de ellas. Si el cliente pide un reembolso, llama a generar_reembolso directamente: no le pidas confirmación al cliente. La aprobación la da el personal de la tienda y la herramienta la solicita por su cuenta. Si la herramienta indica que el reembolso fue aprobado, dilo como aprobado y no como pendiente."
    ),
    (
        "human", "{entrada}"
    ),
    MessagesPlaceholder("agent_scratchpad")
])

def construir_agente(modelo):
    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,
        max_iterations=5,
    )

if __name__ == "__main__":

    ejecutor_agente = construir_agente(modelo)

    preguntas = [
        "¿Dónde está mi pedido 1069?",
        "Compré un audífono, me llegó hace 17 días. ¿Todavía lo puedo devolver?",
        "Mi pedido 1042 llegó con una pieza rota. Quiero que me devuelvan 500 pesos.",
        "Mi pedido 1080 llegó con una pieza rota. Quiero que me devuelvan 500 pesos.",
    ]
    for pregunta in preguntas:
        try:
            resultado = ejecutor_agente.invoke({"entrada": pregunta})
        except Exception as error:
            print("Pregunta:", pregunta)
            print("Error:", error)
            print()
            continue
        herramientas_usadas = [paso[0].tool for paso in resultado["intermediate_steps"]]
        respuesta = resultado["output"][0]["text"] if isinstance(resultado["output"], list) else resultado["output"]
        resultado["output"] = respuesta
        registrar_traza(session_id="postventa_demo", entrada=pregunta, resultado=resultado)
        print("Pregunta:", pregunta)
        print("Herramientas usadas:", herramientas_usadas)
        print("Respuesta:", respuesta)
        print()
