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

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

PEDIDOS = {
    1042: {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 17},
    1077: {"estado": "entregado", "categoria": "producto personalizado", "dias_desde_entrega": 2},
    1069: {"estado": "en_transito", "categoria": "electrónica", "dias_desde_entrega": None},
}

PLAZOS_DEVOLUCION = {
    "electrónica": 10,
    "ropa": 30,
}

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

herramientas = [consultar_estado_pedido, verificar_plazo_devolucion]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente de postventa que responde en tú. Usa las herramientas disponibles para consultar pedidos y plazos. No inventes información que no obtengas de ellas."
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
    )

if __name__ == "__main__":

    ejecutor_agente = construir_agente(modelo)

    preguntas = [
        "¿Dónde está mi pedido 1069?",
        "Compré un audífono, me llegó hace 17 días. ¿Todavía lo puedo devolver?",
        "¿Me puedes explicar qué significa que un pedido esté en tránsito?",
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
        print("Pregunta:", pregunta)
        print("Herramientas usadas:", herramientas_usadas)
        print("Respuesta:", respuesta)
        print()
