from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la fuente de cada afirmación con su número entre corchetes, como [1]. Si el contexto no alcanza para responder, dilo explícitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""

def formatear_contexto(chunks_recuperados):
    """Arma un bloque de contexto numerado para el prompt, y un mapa número -> fuente para reconstruir la cita después."""
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente
    contexto = "\n\n".join(lineas)
    return contexto, citas

def recuperar_y_armar_prompt(vectorstore, pregunta, k=3):
    """Recupera los k chunks más relevantes y arma el prompt. No reindexa: solo lee el vectorstore ya cargado."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    chunks_recuperados = retriever.invoke(pregunta)
    contexto, citas = formatear_contexto(chunks_recuperados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas

def construir_prompt(pregunta, persist_directory, k=3):
    """Carga el índice guardado en disco y arma el prompt. Usa la API para embeber la pregunta."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return recuperar_y_armar_prompt(vectorstore, pregunta, k)

if __name__ == "__main__":
    preguntas = [
        "¿Puedo cancelar un pedido que ya salió de la central?",
        "¿Cuántos días tengo para devolver un producto de electrónica?",
    ]
    for pregunta in preguntas:
        prompt, citas = construir_prompt(pregunta, persist_directory="vectorstore/")
        print(prompt)
        print(citas)
        print()
