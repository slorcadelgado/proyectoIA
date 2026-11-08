from unittest.mock import MagicMock
from src.agente_con_herramientas_postventa import (
    consultar_estado_pedido,
    verificar_plazo_devolucion,
    construir_agente,
)


def test_consultar_estado_pedido_existente():
    resultado = consultar_estado_pedido.invoke({"numero_pedido": 1069})

    assert resultado == "El pedido 1069 está en estado: en_transito."


def test_consultar_estado_pedido_inexistente_no_lanza_error():
    resultado = consultar_estado_pedido.invoke({"numero_pedido": 9999})

    assert "No se encontró" in resultado


def test_verificar_plazo_dentro_de_electronica():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "electrónica", "dias_desde_entrega": 10})

    assert "Está dentro del plazo" in resultado


def test_verificar_plazo_fuera_de_electronica():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "electrónica", "dias_desde_entrega": 11})

    assert "Está fuera del plazo" in resultado


def test_verificar_plazo_personalizado_no_admite_devolucion():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "producto personalizado", "dias_desde_entrega": 2})

    assert "no admiten devolución" in resultado


def test_construir_agente_expone_intermediate_steps():

    modelo_falso = MagicMock()

    ejecutor = construir_agente(modelo_falso)

    assert ejecutor.return_intermediate_steps is True
