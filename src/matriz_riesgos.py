def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"

mis_riesgos = [
    {
        "riesgo": "Inyeccion de prompt via comentario de usuario indexado",
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": "Filtro de patrones de inyeccion sobre el contexto recuperado (src/logging_rag.py, Bloque 31)",
        "supervision": "Revision humana antes de responder cuando el filtro descarta un documento (NO CONSTRUIDO: hoy solo se registra el descarte como WARNING)",
    },
    {
        "riesgo": "Reembolso generado sin aprobacion humana",
        "probabilidad": 2,
        "impacto": 5,
        "mitigacion": "esperar_aprobacion con registro en registro_aprobaciones (src/agente_con_herramientas_postventa.py, Bloque 23). Demo de consola: 15 s",
        "supervision": "Aprobacion del personal de la tienda; sin respuesta a tiempo, se rechaza. En la API el plazo es de 1 dia, no de 15 s: la solicitud queda pendiente en el checkpointer y un proceso la rechaza al vencer",
    },
    {
        "riesgo": "Politica desactualizada en el indice RAG tras un cambio de regla",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": "Reindexado con ids predecibles y fuente en metadata (src/indexar_corpus.py, Bloques 24 a 26)",
        "supervision": "Revision humana del texto nuevo de la politica antes de reindexar (NO CONSTRUIDO: hoy el reindexado no tiene paso de revision)",
    },
    {
        "riesgo": "Cuota de la API agotada durante una corrida de evaluacion",
        "probabilidad": 4,
        "impacto": 2,
        "mitigacion": "Pausa de 13 s entre llamadas (src/consistencia.py) y reintento con espera creciente (src/cliente.py, Bloque 13)",
    },
    {
        "riesgo": "Cambio de prompt en produccion sin revision",
        "probabilidad": 2,
        "impacto": 4,
        "mitigacion": "Huella del prompt y punto de supervision con interrupt antes de activar la version (Bloque 32)",
    },
]

def esta_en_el_limite(probabilidad, impacto):
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False


if __name__ == "__main__":
    for r in mis_riesgos:
        r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
        r["categoria"] = categoria_riesgo(r["puntaje"])

    for r in sorted(mis_riesgos, key=lambda x: x["puntaje"], reverse=True):
        print(f"{r['categoria']:<8} ({r['puntaje']:>2}) - {r['riesgo']}")

    print("\nRiesgos ALTO o CRITICO sin punto de supervision:")
    for r in mis_riesgos:
        if r["categoria"] in ("ALTO", "CRITICO") and not r.get("supervision"):
            print(f"falta supervision: {r['riesgo']}")

    print("\nRiesgos justo en el límite de su categoría:")
    for r in mis_riesgos:
        if esta_en_el_limite(r["probabilidad"], r["impacto"]):
            print(f"revisar con otra persona: {r['riesgo']}")
