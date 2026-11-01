from collections import Counter
from pipeline_limpieza import *
from cliente import *
import json
import time

POLITICAS = """
- Electrónica: se puede devolver dentro de 10 días corridos desde la entrega.
- Ropa: se puede devolver dentro de 30 días corridos desde la entrega.
- Productos personalizados: no admiten devolución.
- Solo se aceptan devoluciones de pedidos en estado "entregado".
- Cancelación: solo si el pedido está en estado "en_central"; se reembolsa el total.
- Pedidos en "en_transito" o "en_reparto" no se cancelan; si el cliente no quiere el producto, lo devuelve después de la entrega.
- Cambios de talla: no hay cambios directos. El cliente solicita la devolución y puede volver a comprar el producto en la talla que necesita.
- La fecha de entrega está en la cuenta del cliente.
"""

INSTRUCCION = f"""Eres el asistente de postventa de una tienda online. Responde en español en una o dos oraciones, usando solo estas políticas. No inventes condiciones ni excepciones.

Políticas:
{POLITICAS}"""


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

casos = [
    ("¿Cuántos días tengo para devolver un producto de electrónica?", "Los productos de electrónica se pueden devolver dentro de 10 días corridos desde la entrega."),
    ("¿Cuánto tiempo tengo para devolver ropa?", "La ropa se puede devolver dentro de 30 días corridos desde la entrega."),
    ("¿Puedo devolver un producto personalizado?", "No, los productos personalizados no admiten devolución."),
    ("¿Puedo devolver un pedido que todavía está en tránsito?", "No, solo se aceptan devoluciones de pedidos en estado entregado."),
    ("¿Puedo cancelar mi pedido si ya salió de la central?", "No, solo se puede cancelar mientras está en_central; si ya salió, se devuelve después de la entrega."),
    ("¿Desde cuándo se cuentan los días de devolución?", "Los días de devolución se cuentan desde la fecha de entrega."),
    ("¿Qué pasa si devuelvo electrónica después de 10 días?", "La devolución de electrónica no procede después de 10 días corridos desde la entrega."),
    ("¿Y si devuelvo ropa después de 30 días?", "La devolución de ropa no procede después de 30 días corridos desde la entrega."),
    ("¿Puedo devolver un audífono el décimo día después de recibirlo?", "Sí, la electrónica se puede devolver hasta el día 10 corrido desde la entrega."),
    ("¿Puedo devolver un pedido de ropa que está en estado pendiente?", "No, solo se aceptan devoluciones de pedidos en estado entregado."),
    ("¿Puedo devolver un televisor que me entregaron ayer?", "Sí, la electrónica se puede devolver dentro de 10 días corridos desde la entrega."),
    ("¿Puedo devolver una camiseta personalizada con mi nombre?", "No, los productos personalizados no admiten devolución."),
    ("¿Puedo devolver un pantalón que me llegó hace 25 días?", "Sí, la ropa se puede devolver hasta 30 días corridos desde la entrega."),
    ("¿Puedo devolver un cargador que me llegó hace 15 días?", "No, la electrónica se puede devolver dentro de 10 días corridos desde la entrega."),
    ("¿Me devuelven el dinero de un pedido que todavía no ha llegado?", "Solo se reembolsa el total si cancelas el pedido mientras está en_central. Si ya salió, no se puede cancelar y solo se puede devolver después de la entrega."),
    ("¿Cómo sé la fecha de entrega de mi pedido?", "Puedes consultar la fecha de entrega en tu cuenta."),
    ("¿Puedo pedir la devolución del pedido 9999?", "No encuentro ese pedido, así que el caso requiere revisión."),
    ("¿Puedo devolver un cargador si la caja está abierta?", "Las políticas no lo indican, así que el caso requiere revisión."),
    ("¿Me reembolsan el dinero si cancelo mi pedido en central?", "Sí, la cancelación en estado en_central reembolsa el total."),
    ("¿Puedo cambiar un producto por otra talla?", "No hay cambios directos. Puedes solicitar la devolución y volver a comprar el producto en la talla que necesitas."),
]

def guardar_resultados(resultados):
    with open("resultados_metricas.json", "w", encoding="utf-8") as archivo:
        json.dump(sorted(resultados, key=lambda r: r["f1"]), archivo, indent=2, ensure_ascii=False)

resultados = []

for consulta, referencia in casos:
    respuesta = consultar_modelo(consulta, system_instruction=INSTRUCCION)
    time.sleep(13)

    metricas = calcular_metricas(referencia, respuesta)
    
    print("Consulta:", consulta)
    print("Respuesta:", respuesta)
    print("Métricas:", metricas)
    
    resultados.append({
        "consulta": consulta,
        "respuesta": respuesta,
        **metricas,
    })
    guardar_resultados(resultados)

resultados = sorted(resultados, key=lambda r: r["f1"])

def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,
        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }
    
print("Promedios")
print(resumir_metricas(resultados))
    
peores_casos = sorted(resultados, key=lambda r: r["f1"])

for caso in peores_casos[:3]:
    print(caso["consulta"], caso["f1"])
    
    
# referencia = procesar_texto(
#     "Python es un lenguaje de programación interpretado."
# )

# texto_respuesta = consultar_modelo("¿Qué es Python?",
#                                    system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")

# respuesta = procesar_texto(texto_respuesta)
# resultado = calcular_precision_cobertura_f1(referencia, respuesta)

# print("Respuesta:", texto_respuesta)
# print("Tokens de referencia:", len(referencia))
# print("Tokens de respuesta:", len(respuesta))
# print(resultado)