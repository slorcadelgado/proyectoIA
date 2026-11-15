# Límites de autonomía del agente de postventa

## Herramientas y nivel de riesgo

- `consultar_estado_pedido`: **bajo**. Solo lee el estado de un pedido. No modifica nada.
- `verificar_plazo_devolucion`: **bajo**. Calcula si un producto sigue dentro del plazo de su categoría. No ejecuta ninguna acción. Su descripción lista las categorías válidas (electrónica, ropa y producto personalizado), para que el modelo no invente nombres.
- `generar_reembolso`: **alto**. Mueve dinero de forma irreversible, por eso requiere aprobación del personal de la tienda.

## Aprobación humana

`generar_reembolso` revisa tres condiciones antes de pedir aprobación: que el pedido exista, que esté entregado y que esté dentro del plazo de su categoría. Si alguna falla, responde con el motivo y no solicita aprobación.

Si las tres se cumplen, muestra en consola el monto y el número de pedido, y espera una respuesta durante 15 segundos:

- `s`: el reembolso se aprueba y se genera.
- `n`, otra respuesta o ninguna respuesta: el reembolso se rechaza.

La espera usa `select` sobre `stdin`, sin hilos en segundo plano. Así, una respuesta tardía no queda pendiente para la siguiente solicitud. Si `stdin` se cierra, la solicitud también se rechaza.

Limitaciones:

- `select` sobre `stdin` no funciona en Windows. El proyecto corre en WSL2, que es Linux.
- Cada decisión se guarda en `registro_aprobaciones`, que vive solo en memoria. Se pierde al cerrar el programa.
- La traza no registra quién aprobó. Solo registra el resultado de la herramienta.

## Revisión de trazas

Cada interacción se guarda en `trazas_postventa.jsonl`, una línea JSON por interacción. Propongo revisar el archivo cada 10 interacciones y después de cada cambio en el prompt o en las descripciones de las herramientas.

Busco tres patrones:

- Una herramienta llamada varias veces con argumentos que no corresponden a la política.
- `generar_reembolso` llamada sin que el cliente la haya pedido, o sin una aprobación registrada.
- Una respuesta final que no coincide con la observación de la herramienta.

Resultados verificados en consola:

- **Estado de pedido:** una sola llamada y respuesta correcta.
- **Plazo de devolución:** una sola llamada, con la categoría válida. Antes de agregar la lista de categorías, el modelo llamaba varias veces con nombres inventados.
- **Reembolso fuera de plazo:** rechazado sin pedir aprobación.
- **Reembolso dentro de plazo, sin respuesta:** rechazado por timeout a los 15 segundos.
- **Reembolso dentro de plazo, con `n`:** rechazado. La respuesta final lo comunica al cliente y lo deriva a atención al cliente.
- **Reembolso dentro de plazo, con `s`:** aprobado y generado. La respuesta final lo dice como aprobado.

Dos problemas que aparecieron durante las pruebas y ya corregí:

- Antes de ajustar la instrucción de sistema, el agente le pedía confirmación al cliente en lugar de llamar a `generar_reembolso`. La aprobación corresponde al personal de la tienda, así que la instrucción ahora indica que el agente debe llamar a la herramienta directamente.
- En una ejecución, la respuesta final decía que el reembolso seguía pendiente de aprobación, aunque ya había sido aprobado. La observación de éxito no lo decía, así que cambié su texto y la instrucción del prompt.

## Qué hacer si el agente se comporta de forma inesperada

1. Revisar la última línea de `trazas_postventa.jsonl`: qué herramienta usó, con qué argumentos y qué observación devolvió.
2. Si llama a `generar_reembolso` sin que el cliente lo pida, o sin una aprobación registrada, quitar la herramienta de la lista `herramientas` y reconstruir el agente con `construir_agente`. No hace falta cambiar el código de la herramienta para desactivarla.
3. Si responde sin usar una herramienta a una pregunta de pedido o de plazo, revisar la descripción de esa herramienta, porque el modelo la usa para decidir cuándo llamarla.
4. Si repite una herramienta varias veces, `AgentExecutor` se detiene al llegar a `max_iterations=5` y devuelve un error. Revisar el prompt antes de subir ese límite.

## Pendientes

- Diferenciar en la traza un rechazo por `n` de un rechazo por timeout. Hoy el mensaje de la herramienta es el mismo para los dos casos.
- Registrar en la traza quién aprobó. Hoy `registro_aprobaciones` solo vive en memoria.
