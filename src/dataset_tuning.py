import json
import time
from collections import Counter
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

#Paso 1: construcción del dataset. Cada ejemplo es (mensaje del cliente, clasificación esperada)
ejemplos_raw = [
    ("Quiero devolver el audífono que compré hace 3 días, ¿cómo lo hago?",
    {"categoria": "devolucion", "prioridad": "media"}),
    ("¿Cuánto tiempo tengo para devolver una camiseta que no me quedó?",
    {"categoria": "devolucion", "prioridad": "baja"}),
    ("El producto llegó roto, quiero que me devuelvan el dinero.",
    {"categoria": "devolucion", "prioridad": "alta"}),
    ("Me cobraron dos veces el mismo pedido en mi tarjeta.",
    {"categoria": "cobro", "prioridad": "alta"}),
    ("No me aparece el cargo del pedido en mi estado de cuenta, ¿es normal?",
    {"categoria": "cobro", "prioridad": "media"}),
    ("El precio en el carrito no coincide con el precio del producto.",
    {"categoria": "cobro", "prioridad": "media"}),
    ("¿Dónde está mi pedido? Lleva cinco días en tránsito.",
    {"categoria": "envio", "prioridad": "media"}),
    ("Mi paquete llegó a una dirección que no es la mía.",
    {"categoria": "envio", "prioridad": "alta"}),
    ("¿Cuánto cuesta enviar a una ciudad fuera de la capital?",
    {"categoria": "envio", "prioridad": "baja"}),
    ("El cupón de descuento no me funciona en el checkout.",
    {"categoria": "promocion", "prioridad": "media"}),
    ("¿Esta oferta de 20 por ciento incluye los productos en liquidación?",
    {"categoria": "promocion", "prioridad": "baja"}),
    ("Tengo un código de regalo y no sé dónde canjearlo.",
    {"categoria": "promocion", "prioridad": "baja"}),
]

#Construyendo una lista de objetos TuningExample: el mensaje es la entrada y la clasificación en JSON es la salida
examples = [
    types.TuningExample(text_input=texto, output=json.dumps(salida, ensure_ascii=False))
    for texto, salida in ejemplos_raw
]

#Paso 2: revisar el balance entre categorías. Una categoría dominante haría que el modelo tienda a esa categoría
def chequear_balance(ejemplos_raw):
    categorias = Counter(salida["categoria"] for _, salida in ejemplos_raw)
    return categorias

#Paso 3: validar antes de enviar nada. Devuelve una lista vacía si el dataset está bien
def validar_dataset(examples, claves_esperadas=("categoria", "prioridad")):
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
    return problemas

#Paso 4: exportar a JSONL en el formato de contents de Vertex, el que lee el trabajo de tuning
def exportar_jsonl(ejemplos_raw, ruta="docs/dataset_tuning.jsonl"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for texto, salida in ejemplos_raw:
            linea = {
                "contents": [
                    {"role": "user", "parts": [{"text": texto}]},
                    {"role": "model", "parts": [{"text": json.dumps(salida, ensure_ascii=False)}]},
                ]
            }
            archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")
    print(f"Dataset exportado a {ruta} ({len(ejemplos_raw)} líneas)")

#Mismo proyecto y región que el script de clase, donde el trabajo de ejemplo terminó bien
PROYECTO = "summer-surfer-344819"
UBICACION = "us-central1"
GCS_URI = "gs://bucket-ejemplo-ai-sild/dataset_tuning.jsonl"
MODELO_BASE = "gemini-2.5-flash"
RUTA_NOMBRE_TRABAJO = "docs/nombre_trabajo_tuning.txt"

#Estados donde el trabajo ya no va a cambiar: el bucle se detiene en cualquiera de ellos
ESTADOS_FINALES = {
    types.JobState.JOB_STATE_SUCCEEDED,
    types.JobState.JOB_STATE_FAILED,
    types.JobState.JOB_STATE_CANCELLED,
    types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    types.JobState.JOB_STATE_EXPIRED,
}

def esperar_a_que_termine(client, nombre_trabajo, intervalo_segundos=30, tiempo_maximo_segundos=3 * 60 * 60):
    """Consulta el estado hasta un estado final o hasta el tiempo máximo. Solo lee: no crea otro trabajo."""
    inicio = time.time()
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"Estado actual: {trabajo.state}")
        if trabajo.state in ESTADOS_FINALES:
            return trabajo
        if time.time() - inicio > tiempo_maximo_segundos:
            print("Tiempo máximo de espera alcanzado. El trabajo sigue en curso; revísalo en Vertex AI.")
            return trabajo
        time.sleep(intervalo_segundos)

if __name__ == "__main__":
    print("PASO 1: balance de MI dataset")
    for categoria, cuenta in chequear_balance(ejemplos_raw).most_common():
        print(f"{categoria}: {cuenta}")

    print("\nPASO 2: validación de MI dataset")
    problemas = validar_dataset(examples)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)

    print("\nPASO 3: rompo un ejemplo a propósito")
    examples_rotos = examples + [types.TuningExample(text_input="Mensaje de prueba roto.", output="no es json")]
    problemas_rotos = validar_dataset(examples_rotos)
    print(f"{len(examples_rotos)} ejemplos, {len(problemas_rotos)} problemas encontrados")
    for p in problemas_rotos:
        print(" -", p)

    # Paso 5: lanzar el trabajo de tuning con el dataset propio y esperar su estado final
    client = genai.Client(vertexai=True, project=PROYECTO, location=UBICACION)
    dataset = types.TuningDataset(gcs_uri=GCS_URI)
    config = types.CreateTuningJobConfig(
        tuning_mode=types.TuningMode.TUNING_MODE_PEFT_ADAPTER,
        adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR,
        epoch_count=5,
        tuned_model_display_name="clasificador-soporte",
    )
    try:
        print("\nPASO 5: enviando el trabajo de tuning con el dataset propio...")
        trabajo = client.tunings.tune(
            base_model=MODELO_BASE,
            training_dataset=dataset,
            config=config,
        )
        print(f"Trabajo creado. Nombre: {trabajo.name}")
        with open(RUTA_NOMBRE_TRABAJO, "w", encoding="utf-8") as archivo:
            archivo.write(trabajo.name + "\n")

        resultado_final = esperar_a_que_termine(client, trabajo.name)
        print("\nProceso finalizado con estado:", resultado_final.state)
        if resultado_final.state == types.JobState.JOB_STATE_SUCCEEDED:
            print("Modelo listo para usar:", resultado_final.tuned_model.model)
    except Exception as error:
        print("No se pudo completar el trabajo de tuning:", error)
