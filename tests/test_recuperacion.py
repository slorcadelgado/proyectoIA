from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_chroma import Chroma

from src.recuperacion import formatear_contexto, recuperar_y_armar_prompt


def test_formatear_contexto_numera_y_mapea_fuentes():
    chunks = [
        Document(page_content="El cliente reintenta 3 veces.", metadata={"fuente": "politica_1.md"}),
        Document(page_content="El costo se calcula por token.", metadata={"fuente": "politica_2.md"}),
    ]

    contexto, citas = formatear_contexto(chunks)

    assert contexto.startswith("[1] El cliente reintenta 3 veces.")
    assert "[2] El costo se calcula por token." in contexto
    assert citas == {1: "politica_1.md", 2: "politica_2.md"}


def test_formatear_contexto_sin_fuente_marca_desconocida():
    chunks = [Document(page_content="Texto sin metadata.")]

    _, citas = formatear_contexto(chunks)

    assert citas == {1: "desconocida"}


def test_recuperar_y_armar_prompt_con_vectorstore_local():
    # Embeddings falsos y colección propia: no consume la API
    textos = [
        "El cliente reintenta hasta 3 veces ante un TimeoutError.",
        "El costo de cada llamada se calcula a partir de totalTokenCount.",
        "Las pruebas unitarias usan mocks.",
        "El agente decide qué herramienta usar.",
    ]
    metadatas = [{"fuente": f"politica_{i}.md"} for i in range(1, len(textos) + 1)]
    vectorstore = Chroma.from_texts(
        textos,
        embedding=DeterministicFakeEmbedding(size=16),
        metadatas=metadatas,
        collection_name="test_recuperacion_prompt",
    )
    pregunta = "¿Qué pasa si hay un TimeoutError?"

    prompt, citas = recuperar_y_armar_prompt(vectorstore, pregunta, k=3)

    assert len(citas) == 3
    assert set(citas.values()) <= {f"politica_{i}.md" for i in range(1, 5)}
    assert f"Pregunta: {pregunta}" in prompt
    assert "[1] " in prompt and "[3] " in prompt
    assert "[4] " not in prompt


def test_prompt_pide_citar_y_admitir_falta_de_contexto():
    vectorstore = Chroma.from_texts(
        ["Un texto cualquiera."],
        embedding=DeterministicFakeEmbedding(size=16),
        metadatas=[{"fuente": "politica_1.md"}],
        collection_name="test_recuperacion_instruccion",
    )

    prompt, _ = recuperar_y_armar_prompt(vectorstore, "¿Algo?", k=1)

    assert "Cita la fuente" in prompt
    assert "dilo explícitamente" in prompt
