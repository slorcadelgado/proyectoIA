from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

# Corpus propio: políticas de postventa del proyecto, cada documento menor a 200 caracteres
corpus = [
    "Electrónica: se puede devolver dentro de 10 días corridos desde la entrega. Solo si el pedido está en estado entregado.",
    "Ropa: se puede devolver dentro de 30 días corridos desde la entrega. El pedido debe estar en estado entregado.",
    "Productos personalizados: no admiten devolución, ni siquiera dentro del plazo de su categoría.",
    "Cancelación: un pedido solo se puede cancelar mientras está en_central. Se reembolsa el total.",
    "Cambios de talla: no hay cambios directos. El cliente solicita la devolución y puede volver a comprar en la talla que necesita.",
]

CARPETA_VECTORES = "vectorstore/"

# Chunking: recursivo, tamaño 200 y solapamiento 30
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
# Cada documento lleva su fuente en la metadata; sin ella, las citas salen como 'desconocida'
documentos = [
    Document(page_content=texto, metadata={"fuente": f"politica_{i}.md"})
    for i, texto in enumerate(corpus, start=1)
]
chunks = splitter.split_documents(documentos)

# Embeddings reales de Gemini: una llamada a la API por lote de chunks
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Indexar y guardar en disco
# ids predecibles (doc1, doc2, ...) para poder referenciar cada chunk en la evaluación del bloque 27
ids = [f"doc{i}" for i in range(1, len(chunks) + 1)]

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    ids=ids,
    persist_directory=CARPETA_VECTORES,
)

print(f"Indexados {len(chunks)} chunks en {CARPETA_VECTORES}")
