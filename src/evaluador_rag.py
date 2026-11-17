from datetime import date

from rag_indexer import cargar_vectorstore


def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    """
    ids_recuperados los que me trajo el retriever
    De los 'k' chunks que me trajo el retriever, ¿qué fracción realmente sirve?
    Devuelve 0.0 si el retriever no devolvió ningún id
    """
    if not ids_recuperados:
        return 0.0
    
    #Recorro uno por uno cada ID que devolvió el retriever, si acaso existe en ids_relevantes lo agrego a la lista de acertados
    acertados = [i for i in ids_recuperados if i in ids_relevantes] 

    return len(acertados) / len(ids_recuperados)

def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    """
    Exhaustividad
    De todos los chunks relevantes que existen en mi corpus, ¿qué fracción logré rescatar?
    Devuelve None si la pregunta no tiene respuesta en corpus (ids_relevantes es vacío)
    """
    if not ids_relevantes:
        return None
    
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)

def f1_score(precision: float, recall: float | None) -> float:
    """
    Media armónica entre precisión y exhaustividad: equilibrio entre ambos para comparar
    configuraciones distintas de k o chunk_size.
    """
    if recall is None or (precision + recall) == 0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)

def evaluar_recuperacion(retriever, casos: list[dict], k: int = 3):
    """
    Correr cada caso del conjunto de evaluaciones contra el retriever real de Chroma
    y va a calcular precisión, recall y F1
    """
    resultados = []

    for caso in casos:
        #1.- Consultamos al retriever, cuáles son los chunks que me regresa la invocación. SI GASTA TOKENS
        chunks = retriever.invoke(caso["pregunta"])

        #2.- Extraer los IDs
        ids_recuperados = [c.id for c in chunks]

        #3.- Calculamos las métricas
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        f1 = f1_score(p, r)

        #4.- Agregar esas métricas a los resultados
        resultados.append({
            "pregunta": caso["pregunta"],
            "ids_recuperados": ids_recuperados,
            "precision": p,
            "recall": r,
            "f1": f1
        })
    
    return resultados

def guardar_reporte(ruta_archivo: str, resultados: list[dict], k: int, chunk_size: int = 200, chunk_overlap: int = 30):
    """Guarda el registro en un .txt para compararlo cuando cambies k o chunk_size."""
    with open(ruta_archivo, "a", encoding="utf-8") as archivo:
        archivo.write("=" * 70 + "\n")
        archivo.write(f"Fecha: {date.today()}\n")
        archivo.write(f"Configuracion: k={k}, chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n\n")

        for r in resultados:
            recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
            archivo.write(f"P={r['precision']:.2f} | R={recall_txt} | F1={r['f1']:.2f} | {r['pregunta']}\n")

    print(f"\nReporte guardado en '{ruta_archivo}'")

if __name__ == "__main__":
    CARPETA_DB = "vectorstore/"
    K = 3
    vs = cargar_vectorstore(CARPETA_DB)
    retriever = vs.as_retriever(search_kwargs={"k": K})

    casos_evaluacion = [
        {"pregunta": "¿Cuántos días tengo para devolver un producto de electrónica?", "ids_relevantes": {"doc1"}},
        {"pregunta": "¿Puedo devolver un producto personalizado?", "ids_relevantes": {"doc3"}},
        {"pregunta": "¿Puedo cancelar mi pedido si ya salió de la central?", "ids_relevantes": {"doc4"}},
        {"pregunta": "¿Puedo cambiar un producto por otra talla?", "ids_relevantes": {"doc5"}},
    ]

    resultados = evaluar_recuperacion(retriever, casos_evaluacion, k=K)
    for r in resultados:
        print(f"precision={r['precision']:.2f}  recall={r['recall']:.2f}  f1={r['f1']:.2f}  {r['pregunta']}")
        print(f"recuperados: {r['ids_recuperados']}")

    n = len(resultados)
    prom_precision = sum(r["precision"] for r in resultados) / n
    prom_recall = sum(r["recall"] for r in resultados) / n
    prom_f1 = sum(r["f1"] for r in resultados) / n
    print(f"promedio -> precision: {prom_precision:.3f}  recall: {prom_recall:.3f}  f1: {prom_f1:.3f}")

    # chunk_size y chunk_overlap deben coincidir con indexar_corpus.py
    guardar_reporte("resultados_evaluacion.txt", resultados, k=K, chunk_size=200, chunk_overlap=30)

    """
    Precisión: Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Positivos) 

    Exhaustividad (recall ) :
    Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Negativos)
    """