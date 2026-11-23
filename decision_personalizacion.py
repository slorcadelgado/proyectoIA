def recomendar_estrategia(respuestas):
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}

    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, p in puntos.items() if p == maximo]
    return puntos, ganadoras

respuestas_mi_caso = {
    "informacion_cambia_seguido": False,
    "problema_de_formato_o_tono": False,  # 0 de 20 respuestas con formato inválido (docs/medicion_formato_clasificador.json)
    "dataset_grande_y_de_calidad": False,  # 12 ejemplos etiquetados en docs/dataset_tuning.jsonl; el criterio pide 200 o más
    "presupuesto_limitado_o_iterar_rapido": False,  # puede pagar varios entrenamientos y obtiene el resultado en menos de una hora
    "necesita_multiples_variantes": False,  # el proyecto necesita una sola variante del modelo
}

if any(valor is None for valor in respuestas_mi_caso.values()):
    raise SystemExit("Completa las cinco respuestas con True o False antes de continuar.")

def generar_esqueleto_decision(problema, puntos, ganadoras):
    """Arma el esqueleto del documento a partir del resultado real del método. Las partes que faltan quedan marcadas con [COMPLETAR]."""
    empate = len(ganadoras) > 1
    lineas = []
    lineas.append("# Decision de personalizacion")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")
    lineas.append("## 2. Resultado del metodo de decision")
    for tecnica, p in sorted(puntos.items(), key=lambda x: -x[1]):
        lineas.append(f"- {tecnica}: {p} puntos")
    lineas.append("")
    if empate:
        lineas.append(f"**Empate entre: {', '.join(ganadoras)}**")
        lineas.append("")
    lineas.append("## 3. Tecnica elegida y por que")
    if empate:
        lineas.append("[COMPLETAR: el puntaje no resolvio el empate solo -- justifica aqui con criterio propio]")
    else:
        lineas.append(f"[COMPLETAR: por que {ganadoras[0]} responde mejor a este caso]")
    lineas.append("")
    lineas.append("## 4. Que necesitarias para ejecutarla")
    lineas.append("[COMPLETAR: corpus faltante, o cantidad de ejemplos etiquetados que faltan]")
    return "\n".join(lineas)

puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)

problema_mi_caso = (
    "El clasificador de mensajes de soporte de la tienda devuelve un formato consistente, "
    "pero no sabemos si las categorias asignadas son correctas, porque solo medimos el formato."
)

esqueleto = generar_esqueleto_decision(problema_mi_caso, puntos, ganadoras)
print(esqueleto)
with open("decision_personalizacion.md", "w", encoding="utf-8") as f:
    f.write(esqueleto)
print("\nEsqueleto guardado en decision_personalizacion.md")
