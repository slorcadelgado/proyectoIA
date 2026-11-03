from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

plantilla = PromptTemplate.from_template("Explica el concepto de {tema} en un párrafo, para alguien que recien comienza en {area}.")

cadena_simple = plantilla | modelo | StrOutputParser()

respuesta = cadena_simple.invoke({"tema": "tokenización", "area": "procesamiento de texto"})

print(respuesta)

plantilla_conrol = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en el área correspondiente, vas a responder siempre con texto simple para el usuario."),
    ("human", "Explica el concepto de {tema} en un párrafo, para alguien que recien comienza en {area}")
])