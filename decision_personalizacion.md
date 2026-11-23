# Decision de personalizacion

## 1. El problema
El asistente de postventa de la tienda responde preguntas de clientes con las políticas vigentes sobre pedidos, plazos y devoluciones. El proyecto es ahora un asistente de e-commerce completo, que además debe responder con catálogo, inventario y políticas de envío. El problema no es de formato de respuesta: es de conocimiento, porque el asistente necesita información que cambia y que el modelo no tiene.

## 2. Resultado del metodo de decision
- RAG: 0 puntos
- Fine-tuning completo: 0 puntos
- PEFT: 0 puntos

**Empate entre: RAG, Fine-tuning completo, PEFT.** El método no distingue entre las tres técnicas para este caso, así que la elección de la sección 3 es de criterio y no del puntaje.

## 3. Técnica elegida y por qué
Elijo RAG. El problema es de conocimiento: el asistente debe responder con las políticas vigentes. RAG permite actualizar esa información reindexando, sin reentrenar, y que cada respuesta cite la política que aplicó. Descarto el ajuste fino del modelo para este caso: entrenarlo fija la información en los pesos, y cada cambio de política obligaría a reentrenar. Como el asistente es de e-commerce, el inventario y los datos de pedidos viven en la base de datos y se consultan con herramientas, así que el índice solo guarda texto estable: políticas, catálogo y envíos.

## 4. Qué necesitarias para ejecutarla
Hoy el índice solo tiene cinco documentos de políticas de postventa, indexados en `vectorstore/`. Para el asistente de e-commerce faltaría indexar:

- **Catálogo de productos:** nombre, categoría, descripción y si admite devolución. Precio y disponibilidad no se indexan: se consultan en la base de datos con una herramienta.
- **Inventario y disponibilidad:** no se indexa. Cambia con frecuencia, así que el asistente lo consulta en la base de datos con una herramienta.
- **Políticas de envío:** hoy no están en el índice. Son las que faltan para responder preguntas sobre plazos de envío.

Para indexarlo hace falta decidir el tamaño de los fragmentos y el número de resultados (k), y medirlos con el conjunto de evaluación del bloque 27.