from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import RunnablePassthrough #Conserva los valores anteriores y agrega uno nuevo

load_dotenv()

def construir_cadena(modelo):

    plantilla_regla = PromptTemplate.from_template("Lee la consulta y los datos del pedido, y devuelve solo la política que aplica, en una oración, sin agregar condiciones: \n\n {consulta}")

    paso_regla = plantilla_regla | modelo | StrOutputParser()

    plantilla_respuesta = PromptTemplate.from_template("Redacta una respuesta breve y amable para el cliente en español, usando solo esta regla: \n\n {regla}")

    paso_respuesta = plantilla_respuesta | modelo | StrOutputParser()

    plantilla_revision = PromptTemplate.from_template("Revisa este mensaje: usa solo 'tú' para el cliente y elimina cualquier condición que no esté en la regla. Devuelve solo el mensaje final.\n\nRegla: {regla}\n\nMensaje: {respuesta}")

    paso_revision = plantilla_revision | modelo | StrOutputParser()

    return (
        paso_regla | (lambda regla: {"regla": regla}) |
        RunnablePassthrough.assign(respuesta=paso_respuesta) |
        paso_revision
    )


if __name__ == "__main__":
    
    modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    cadena = construir_cadena(modelo)

    consulta_prueba = (
        "Consulta: ¿Puedo devolver un audífono que me entregaron hace 17 días?\n"
        "Datos verificados: {\"categoria\": \"electrónica\", \"estado\": \"entregado\", \"dias_desde_entrega\": 17, \"plazo_aplicable\": 10}"
    )

    resultado = cadena.invoke({"consulta": consulta_prueba})
    print(resultado)
