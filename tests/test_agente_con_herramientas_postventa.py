import io
import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src import agente_con_herramientas_postventa as postventa
from src.agente_con_herramientas_postventa import (
    consultar_estado_pedido,
    verificar_plazo_devolucion,
    generar_reembolso,
    construir_agente,
    registrar_traza,
)


def test_consultar_estado_pedido_existente():
    resultado = consultar_estado_pedido.invoke({"numero_pedido": 1069})

    assert resultado == "El pedido 1069 está en estado: en_transito."


def test_consultar_estado_pedido_inexistente_no_lanza_error():
    resultado = consultar_estado_pedido.invoke({"numero_pedido": 9999})

    assert "No se encontró" in resultado


def test_aprobacion_sin_entrada_a_tiempo_se_rechaza():
    with patch.object(postventa.select, "select", return_value=([], [], [])) as seleccion:
        aprobado = postventa.esperar_aprobacion("¿Aprobar? ", tiempo_limite_segundos=15)

    assert aprobado is False
    assert seleccion.call_args.args[3] == 15


def test_aprobacion_con_s_se_aprueba():
    with patch.object(postventa.select, "select", return_value=([sys.stdin], [], [])), \
         patch.object(postventa.sys, "stdin", io.StringIO("s\n")):
        aprobado = postventa.esperar_aprobacion("¿Aprobar? ")

    assert aprobado is True


def test_aprobacion_con_n_se_rechaza():
    with patch.object(postventa.select, "select", return_value=([sys.stdin], [], [])), \
         patch.object(postventa.sys, "stdin", io.StringIO("n\n")):
        aprobado = postventa.esperar_aprobacion("¿Aprobar? ")

    assert aprobado is False


def test_aprobacion_con_fin_de_entrada_se_rechaza():
    # stdin cerrado: select lo marca como legible y readline devuelve ""
    with patch.object(postventa.select, "select", return_value=([sys.stdin], [], [])), \
         patch.object(postventa.sys, "stdin", io.StringIO("")):
        aprobado = postventa.esperar_aprobacion("¿Aprobar? ")

    assert aprobado is False


def test_prompt_no_pide_confirmacion_al_cliente_para_reembolso():
    texto_sistema = postventa.prompt_agente.messages[0].prompt.template

    assert "no le pidas confirmación al cliente" in texto_sistema
    assert "personal de la tienda" in texto_sistema
    assert "dilo como aprobado y no como pendiente" in texto_sistema


def test_docstring_de_plazo_lista_las_categorias_validas():
    assert "electrónica, ropa, producto personalizado" in verificar_plazo_devolucion.description


def test_verificar_plazo_dentro_de_electronica():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "electrónica", "dias_desde_entrega": 10})

    assert "Está dentro del plazo" in resultado


def test_verificar_plazo_fuera_de_electronica():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "electrónica", "dias_desde_entrega": 11})

    assert "Está fuera del plazo" in resultado


def test_verificar_plazo_personalizado_no_admite_devolucion():
    resultado = verificar_plazo_devolucion.invoke({"categoria": "producto personalizado", "dias_desde_entrega": 2})

    assert "no admiten devolución" in resultado


def test_construir_agente_expone_intermediate_steps_y_limite():
    # Solo se verifica la configuración; no se invoca el modelo
    modelo_falso = MagicMock()

    ejecutor = construir_agente(modelo_falso)

    assert ejecutor.return_intermediate_steps is True
    assert ejecutor.max_iterations == 5


def test_reembolso_aprobado_se_genera_y_queda_registrado(monkeypatch):
    monkeypatch.setattr(postventa, "registro_aprobaciones", [])
    monkeypatch.setitem(postventa.PEDIDOS, 2001, {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 3})

    with patch.object(postventa, "esperar_aprobacion", return_value=True) as aprobacion:
        resultado = generar_reembolso.invoke({"numero_pedido": 2001, "monto": 500.0})

    assert aprobacion.called
    assert "generado con éxito" in resultado
    assert postventa.registro_aprobaciones[-1]["aprobado"] is True


def test_reembolso_rechazado_no_se_genera(monkeypatch):
    monkeypatch.setattr(postventa, "registro_aprobaciones", [])
    monkeypatch.setitem(postventa.PEDIDOS, 2001, {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 3})

    with patch.object(postventa, "esperar_aprobacion", return_value=False):
        resultado = generar_reembolso.invoke({"numero_pedido": 2001, "monto": 500.0})

    assert "no aprobado" in resultado
    assert postventa.registro_aprobaciones[-1]["aprobado"] is False


def test_reembolso_fuera_de_plazo_se_rechaza_sin_pedir_aprobacion():
    # El pedido 1042 tiene 17 días desde la entrega y electrónica vence a los 10
    with patch.object(postventa, "esperar_aprobacion") as aprobacion:
        resultado = generar_reembolso.invoke({"numero_pedido": 1042, "monto": 500.0})

    assert not aprobacion.called
    assert "fuera del plazo" in resultado


def test_pedido_1080_esta_dentro_de_plazo_para_probar_aprobacion():
    assert postventa.motivo_fuera_de_politica(1080) is None


def test_reembolso_pedido_no_entregado_se_rechaza(monkeypatch):
    monkeypatch.setattr(postventa, "PEDIDOS", {**postventa.PEDIDOS})

    with patch.object(postventa, "esperar_aprobacion") as aprobacion:
        resultado = generar_reembolso.invoke({"numero_pedido": 1069, "monto": 500.0})

    assert not aprobacion.called
    assert "solo se reembolsan pedidos entregados" in resultado


def test_reembolso_dentro_de_plazo_pide_aprobacion(monkeypatch):
    monkeypatch.setattr(postventa, "registro_aprobaciones", [])
    monkeypatch.setitem(postventa.PEDIDOS, 2001, {"estado": "entregado", "categoria": "electrónica", "dias_desde_entrega": 3})

    with patch.object(postventa, "esperar_aprobacion", return_value=True) as aprobacion:
        resultado = generar_reembolso.invoke({"numero_pedido": 2001, "monto": 500.0})

    assert aprobacion.called
    assert "generado con éxito" in resultado


def test_reembolso_pedido_inexistente_no_pide_aprobacion():
    with patch.object(postventa, "esperar_aprobacion") as aprobacion:
        resultado = generar_reembolso.invoke({"numero_pedido": 9999, "monto": 500.0})

    assert not aprobacion.called
    assert "No se encontró" in resultado


def test_registrar_traza_escribe_una_linea_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    accion = SimpleNamespace(tool="consultar_estado_pedido", tool_input={"numero_pedido": 1069})
    resultado = {
        "intermediate_steps": [(accion, "El pedido 1069 está en estado: en_transito.")],
        "output": "Tu pedido está en tránsito.",
    }

    registrar_traza(session_id="cliente_test", entrada="¿Dónde está mi pedido?", resultado=resultado)

    lineas = (tmp_path / "trazas_postventa.jsonl").read_text(encoding="utf-8").splitlines()
    registro = json.loads(lineas[0])
    assert len(lineas) == 1
    assert registro["acciones"][0]["herramienta"] == "consultar_estado_pedido"
    assert registro["respuesta_final"] == "Tu pedido está en tránsito."
