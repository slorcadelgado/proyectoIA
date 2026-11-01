# Límites de la métrica de evaluación

## Qué mide

Coincidencia de palabras entre una respuesta generada y una referencia, contando repeticiones (precisión, cobertura y F1).

## Modos de falla conocidos

- **Parafrasis correcta puntúa bajo.** Tres respuestas correctas sobre cancelación, el día 10 de un audífono y el reembolso en central tienen F1 entre 0.36 y 0.43 porque usan otras palabras que la referencia. En el último caso, además, la referencia es corta.
- **Referencia desactualizada castiga una respuesta correcta.** En la corrida anterior, la respuesta sobre reembolso de un pedido que no ha llegado seguía la regla nueva, pero la referencia era la vieja, y su F1 fue 0.24. Ya actualicé la referencia.
- **F1 bajo no dice por qué.** Las respuestas sobre cargador con caja abierta y pedido 9999 tienen F1 de 0.09 y 0.10. Ninguna dice que el caso requiere revisión, y el número no lo indica.
- **F1 de 1.0 solo prueba que la respuesta copia la referencia.** No demuestra que la respuesta sea útil ni completa.

En esta muestra no encontré un caso de F1 alto con respuesta incorrecta, así que no lo documento como modo confirmado.

## Muestra revisada

10 de 20 respuestas generadas con las políticas de 01/11/2026: las 5 con F1 más bajo (0.09 a 0.43) y las 5 con F1 más alto (0.61 a 1.00). Cada una la califiqué con la rúbrica de corrección factual, completitud y contradicción. Ocho de los diez casos son sí, sí, no. En los casos de cargador y pedido 9999, la completitud y la contradicción son no.

## Recomendación de uso

Usar F1 para comparar versiones del cliente en volumen, pero no como prueba de que una respuesta es correcta. Un F1 bajo puede significar una buena paráfrasis, y uno alto puede significar una copia incompleta.

Revisar a mano cualquier respuesta con fechas, cifras o nombres propios, y cualquier respuesta que deba decir "requiere revisión" o cambiar la decisión de una regla.
