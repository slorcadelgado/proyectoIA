from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from src.cadena_tres_pasos_postventa import construir_cadena


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="La electrónica se puede devolver dentro de 10 días corridos desde la entrega."),
        AIMessage(content="Lamentablemente tu audífono ya no se puede devolver, porque pasaron 17 días desde la entrega."),
        AIMessage(content="Lamentablemente, tu audífono ya no se puede devolver: pasaron 17 días desde la entrega."),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"consulta": "¿Puedo devolver un audífono que me entregaron hace 17 días?"})

    assert modelo_falso.call_count == 3
    assert resultado == "Lamentablemente, tu audífono ya no se puede devolver: pasaron 17 días desde la entrega."
