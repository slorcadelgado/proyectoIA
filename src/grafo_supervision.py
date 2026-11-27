import uuid
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    # Aquí se podría validar la versión propuesta antes de pedir aprobación
    return {}


def supervisar(estado: EstadoDespliegue):
    # interrupt pausa el grafo y entrega este diccionario a quien debe decidir
    decision = interrupt({
        "motivo": "aprobar nueva version de prompt en produccion",
        "huella_propuesta": estado["huella_nueva"],
    })
    # Al reanudar con Command(resume=...), el valor llega aquí como decision
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print("version", estado["huella_nueva"], "activada")
    else:
        print("version", estado["huella_nueva"], "rechazada, se mantiene la anterior")
    return {}


grafo = StateGraph(EstadoDespliegue)
grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

app_despliegue = grafo.compile(checkpointer=InMemorySaver())


#Genera un thread_id (id único) para cada solicitud de despliegue, para no reutilizar un hilo ya terminado
def nuevo_thread_id(prefijo="despliegue"):
    return f"{prefijo}-{uuid.uuid4().hex[:8]}"

#Comprueba que exista una aprobación pendiente antes de reanudar el grafo
def resolver(app, config, aprobar: bool):
    snapshot = app.get_state(config)
    if not snapshot.next:
        raise ValueError("Este thread/proceso no tiene ninguna aprobación pendiente")
    #Command(resume=True/False): reanuda el flujo con la decisión humana
    return app.invoke(Command(resume=aprobar), config=config)


if __name__ == "__main__":
    huella = "38bc76289e2f"  # huella de la versión nueva, la que devuelve registro_prompts.py

    # Camino de aprobación: el grafo se pausa, se revisa el estado pendiente y se reanuda con True
    config_aprobar = {"configurable": {"thread_id": nuevo_thread_id()}}
    resultado = app_despliegue.invoke({"huella_nueva": huella, "aprobado": False}, config=config_aprobar)
    print("1) tras invocar:", resultado)
    print("2) pendiente:", app_despliegue.get_state(config_aprobar).interrupts[0].value)
    resultado = resolver(app_despliegue, config_aprobar, True)
    print("3) tras aprobar:", resultado)

    # Camino de rechazo: otro thread_id, porque el primero ya terminó
    config_rechazar = {"configurable": {"thread_id": nuevo_thread_id()}}
    app_despliegue.invoke({"huella_nueva": huella, "aprobado": False}, config=config_rechazar)
    resultado = resolver(app_despliegue, config_rechazar, False)
    print("4) tras rechazar:", resultado)
