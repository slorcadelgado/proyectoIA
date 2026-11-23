import json
from collections import Counter

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODELO = "gemini-3.6-flash"
RUTA_RESULTADOS = "docs/medicion_formato_clasificador.json"

CATEGORIAS_VALIDAS = {"devolucion", "cobro", "envio", "promocion"}
PRIORIDADES_VALIDAS = {"alta", "media", "baja"}

INSTRUCCION = (
    "Clasifica el mensaje de soporte de una tienda online. Responde solo con un objeto JSON, "
    'sin texto antes ni después, con las claves "categoria" (devolucion, cobro, envio o promocion) '
    'y "prioridad" (alta, media o baja).'
)

# 20 mensajes nuevos, distintos de los 12 de entrenamiento, con variaciones de redacción
mensajes = [
    "Hola, el paquete todavía no aparece en la app después de cuatro días.",
    "Quiero que me regresen el dinero del zapato, no me quedó bien.",
    "Me llegó doble cobro en la tarjeta por la misma compra del martes.",
    "¿Puedo cambiar la dirección de entrega de un pedido que ya está en camino?",
    "El descuento de 15 por ciento no se aplicó en mi carrito.",
    "Compré una lámpara y vino sin el cable de alimentación.",
    "¿Cuánto cobran por envío a Valparaíso? Lo necesito urgente para mañana.",
    "No puedo usar mi cupón de bienvenida, dice que ya expiró pero lo recibí ayer.",
    "Me cobraron el envío dos veces en el mismo pedido.",
    "Quisiera saber si el reembolso de mi tarjeta ya se procesó.",
    "El repartidor dejó el pedido con otro vecino sin avisarme.",
    "¿Hay promoción en productos de cocina este fin de semana?",
    "Devolví una chaqueta hace una semana y todavía no tengo mi dinero.",
    "La caja llegó aplastada pero el producto está bien, ¿qué hago?",
    "Tengo un cupón de regalo y quiero saber si sirve para envíos.",
    "Me aparece un cargo que no reconozco de su tienda en mi estado de cuenta.",
    "El pedido salió hace tres días y el rastreo sigue en la misma ciudad.",
    "¿Puedo devolver unos audífonos que compré con descuento del 30 por ciento?",
    "Mi factura tiene el monto mal, cobraron más de lo que marca el carrito.",
    "Quiero saber si las ofertas del Black Friday acumulan con cupones.",
]

def extraer_texto(contenido):
    """Gemini a veces devuelve el contenido como lista de bloques; aquí se junta solo el texto."""
    if isinstance(contenido, str):
        return contenido
    partes = [b.get("text", "") for b in contenido if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(partes)

def clasificar(modelo, mensaje):
    respuesta = modelo.invoke(f"{INSTRUCCION}\n\nMensaje: {mensaje}")
    return extraer_texto(respuesta.content)

def evaluar_formato(texto):
    """Devuelve (es_valido, motivo). Válido = JSON con las dos claves y valores permitidos."""
    limpio = texto.strip()
    # El parser de consumir_gemini.py tolera este envoltorio; se cuenta aparte para que la decisión sea explícita
    if limpio.startswith("```"):
        return False, "envuelto en bloque ```json"
    try:
        datos = json.loads(limpio)
    except json.JSONDecodeError:
        return False, "no es JSON"
    if not isinstance(datos, dict):
        return False, "JSON que no es un objeto"
    faltantes = {"categoria", "prioridad"} - set(datos)
    if faltantes:
        return False, f"faltan claves: {sorted(faltantes)}"
    if datos["categoria"] not in CATEGORIAS_VALIDAS:
        return False, f"categoria no permitida: {datos['categoria']}"
    if datos["prioridad"] not in PRIORIDADES_VALIDAS:
        return False, f"prioridad no permitida: {datos['prioridad']}"
    return True, "ok"

if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(model=MODELO)
    resultados = []
    for mensaje in mensajes:
        try:
            texto = clasificar(modelo, mensaje)
        except Exception as error:
            # Un error de cuota no detiene la medición: queda registrado y cuenta como fallo
            texto = ""
            motivo_error = str(error)[:200]
            resultados.append({"mensaje": mensaje, "respuesta": None, "valido": False, "motivo": f"error de API: {motivo_error}"})
            print("ERROR:", mensaje[:50], "->", motivo_error[:80])
            continue
        valido, motivo = evaluar_formato(texto)
        resultados.append({"mensaje": mensaje, "respuesta": texto, "valido": valido, "motivo": motivo})
        print("OK " if valido else "FALLA", "|", motivo, "|", mensaje[:50])

    invalidas = [r for r in resultados if not r["valido"]]
    print(f"\nRespuestas con formato inválido: {len(invalidas)} de {len(resultados)} ({len(invalidas) / len(resultados):.0%})")
    print("Motivos:", Counter(r["motivo"] for r in invalidas))
    print("Criterio de la clave: 3 o más de 20 (15 % o más) fallan -> True")

    with open(RUTA_RESULTADOS, "w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, indent=2, ensure_ascii=False)
    print(f"Resultados guardados en {RUTA_RESULTADOS}")
