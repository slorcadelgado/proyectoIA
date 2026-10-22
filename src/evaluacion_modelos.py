import consumir_gemini
import time

def enviar_con_reintentos(url, body, reintentos=3, espera_base=5):
    """
    Reintenta la petición si el servidor responde 503 (alta demanda) o 429 (límite de uso).
    Espera 5s, 10s, 20s... entre intentos.
    """
    for intento in range(1, reintentos + 1):
        try:
            return consumir_gemini.enviar_peticion(url, body)
        except RuntimeError as e:
            temporal = "503" in str(e) or "429" in str(e)
            if not temporal or intento == reintentos:
                raise
            espera = espera_base * (2 ** (intento - 1))
            print(f"  Servidor ocupado, reintento {intento} en {espera}s...")
            time.sleep(espera)

def evaluar_modelo(nombre_modelo, pregunta, precio_entrada, precio_salida, repeticiones=4):
    """
    Ejecuta 'repeticiones' veces la misma petición para un modelo específico.
    Calcula e imprime Latencia, Costo y Respuesta de cada intento,
    además del promedio de latencia al final.
    """
    print("=" * 70)
    print(f" EVALUANDO MODELO: {nombre_modelo}")
    print("=" * 70)
    
    latencias = []
    costos = []

    for i in range(1, repeticiones + 1):
        print(f"\n--- Intento {i} de {repeticiones} ({nombre_modelo}) ---")
        
        # 1. Armar petición (puedes pasar el modelo si tu función lo requiere)
        url, body = consumir_gemini.armar_peticion(nombre_modelo, pregunta) 

        # 2. Medir latencia
        try:
            inicio = time.perf_counter()
            datos = enviar_con_reintentos(url, body)
            fin = time.perf_counter()
        except RuntimeError as e:
            print(f"Intento {i} descartado: {e}")
            continue

        latencia = fin - inicio
        latencias.append(latencia)
        
        # 3. Calcular costo
        costo = consumir_gemini.calcular_costo(datos, precio_entrada, precio_salida)
        costos.append(costo)
        
        # 4. Extraer respuesta
        respuesta = consumir_gemini.extraer_texto(datos)
        
        # 5. Imprimir resultados de la petición actual
        print(f"Latencia:  {latencia:.2f} segundos")
        print(f"Costo:     ${costo:.6f} USD")
        print(f"Respuesta: {respuesta}")

    # Si ningún intento tuvo éxito, no hay promedio que calcular
    if not latencias:
        print(f" Ningún intento exitoso para {nombre_modelo}")
        print("-" * 40 + "\n")
        return

    # Resumen acumulado del modelo
    latencia_promedio = sum(latencias) / len(latencias)
    costo_total = sum(costos)
    
    print("\n" + "-" * 40)
    print(f" RESUMEN {nombre_modelo}:")
    print(f" Latencia promedio: {latencia_promedio:.2f} segundos")
    print(f" Costo acumulado ({repeticiones} peticiones): ${costo_total:.6f} USD")
    print("-" * 40 + "\n")


pregunta_prueba = """
Eres un asistente de soporte postventa de una tienda online. Responde SOLO con la información de las políticas y los datos del pedido que te entrego. Si falta información, di que no la tienes; no inventes nada.

POLÍTICAS
- Electrónica: se puede devolver dentro de 10 días corridos desde la entrega.
- Ropa: se puede devolver dentro de 30 días corridos desde la entrega.
- Productos personalizados: no admiten devolución.
- Solo se aceptan devoluciones de pedidos en estado "entregado".

DATOS DEL PEDIDO
- Pedido: 1077
- Producto: taza personalizada con nombre grabado (categoría: producto personalizado)
- Estado: entregado
- Fecha de entrega: 2026-10-20
- Fecha de hoy: 2026-10-22

CONSULTA DEL CLIENTE
"Hola, me llegó hace dos días la taza pero me equivoqué de color. ¿Puedo devolverla?"

Responde en formato JSON con estos campos:
{
  "decision": "permitida" | "rechazada" | "requiere_revision",
  "motivo": "explicación breve",
  "politica_citada": "regla que aplicaste",
  "respuesta_al_cliente": "mensaje amable en español"
}
"""
modelos = [
    # {
    #     "nombre": "gemini-3.6-flash",
    #     "precio_entrada": 0.00000075,
    #     "precio_salida": 0.00000375
    # },
    # {
    #     "nombre": "gemini-3-flash-preview",
    #     "precio_entrada": 0.00000050,
    #     "precio_salida": 0.00000300
    # },
    {
        "nombre": "gemini-3.5-flash-lite",
        "precio_entrada": 0.00000030,
        "precio_salida": 0.00000250
    }
]

# Procesar los 3 modelos consecutivamente
for config in modelos:
    evaluar_modelo(
        nombre_modelo=config["nombre"],
        pregunta=pregunta_prueba,
        precio_entrada=config["precio_entrada"],
        precio_salida=config["precio_salida"],
        repeticiones=4
    )