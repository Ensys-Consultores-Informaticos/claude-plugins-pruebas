# Gesia para Claude — canal de PRUEBAS

**Esto no es para clientes.** Es el marketplace donde Ensys prueba las versiones beta del
plugin `gesia-auditoria` antes de publicarlas en el canal de producción,
[`claude-plugins`](https://github.com/Ensys-Consultores-Informaticos/claude-plugins).
Lo que hay aquí puede cambiar sin aviso y puede tener defectos.

## Instalar para probar

1. **Desactiva el plugin de producción** (`gesia-auditoria` del marketplace `ensys`) en
   Configuración > Plugins. Los dos declaran el mismo servidor MCP y las mismas
   herramientas: con ambos activos no se sabe cuál contesta.
2. Añade el marketplace de pruebas: `Ensys-Consultores-Informaticos/claude-plugins-pruebas`
   (aparece como **`ensys-pruebas`**).
3. Instala **Gesia — Expediente de auditoría (PRUEBAS)** y reinicia Claude del todo.
4. La descripción del plugin termina en `(PRUEBAS vX · MCP Y)`: es la versión que tienes.

Para volver a producción: desactiva o desinstala este, reactiva el de `ensys` y reinicia.

## Qué se prueba ahora

**Plugin de pruebas 1.10.2 — segundo registro del 10/09/2026.** En `cancelacion-saldos`: la
puntuación de las columnas candidatas se mide sobre el extracto de cada alcance (y dice «vacía aquí»
cuando lo está); las cuentas de un solo apunte del 1 de enero van aparte de las aperturas no
identificables, con su recuento e importe; el stdout del papel acaba con una línea `TOTAL`
(cuentas, apuntes, pendiente, verificación) que no se lleva el corte a 30 cuentas; y la ruta de
entrega se deriva siempre de `configurar().gs3_file`.

**Plugin de pruebas 1.10.1 — lo que salió de la primera prueba en frío (10/09/2026).** En
`cancelacion-saldos`: la columna `ORIGEN` del papel dice el paso que formó cada grupo (documento,
apertura, total, importe, acumulación, combinación) y criterios cuenta cuántos hay de cada uno; si el
diario trae varias columnas de número de documento, el script puntúa cada una por grupos que cierran a
cero y elige (pídelas todas en el SELECT); los pagos anteriores a una factura **sin** fecha de documento
van a su propia fila y no se presentan como hallazgos ciertos; el recuento del paso 1 da cuentas y
apuntes con el mismo filtro; los grupos a un céntimo son dato, no pregunta; y las preguntas al auditor
llevan opciones para hacerlas con la herramienta de preguntas. Qué probar: la misma tarea contestando
**no** al concepto, y que las preguntas salgan como preguntas.

**MCP 1.11.0 — confidencialidad, ticket 1** (plugin de pruebas 1.10.0, 10/09/2026). El MCP
no sirve nunca el `DNI` de `Personal` ni la tabla `ContactosSede`. Herramienta nueva
`columnas(fuente, tabla)`: qué columnas hay, sin traer ninguna fila —sustituye al
`SELECT TOP 1 *`—. Al exportar el diario, `CONCEPTO` no sale: en su lugar van
`NumeroEnConcepto` y `FechaEnConcepto`, derivadas en local; `configurar(concepto=true)` deja
pasar el texto si el auditor lo decide, solo en esa sesión. Y cada exportación queda anotada en
`<expediente>/InformesGesia/RegistroEmision.jsonl` (columnas y filas, nunca valores). Qué
probar: `cancelacion-saldos` de punta a punta —debe usar `columnas()`, pedir `CONCEPTO` en el
SELECT, hacer la pregunta del concepto tal cual, y el papel debe salir con `FECHA DOC.` y decir
en criterios de dónde salen el número y la fecha—.


**MCP 1.9.2 — la ayuda de `evaluacion` corta la evaluación de la MUM.** Tras el primer
ensayo real: el modelo neteó los errores y dio un porcentaje sobre la muestra. Ahora la ayuda
dice que se listan los elementos con error y ahí se para; la proyección es de ForSampling.


**MCP 1.9.2 — los vínculos desde Gesia.** Con el `.gs3` activo, el plugin deduce el `.cli`
del expediente (`cli_file` en `configurar`) y las entidades `pruebas`, `muestra`, `evaluacion`
y `parametros` funcionan sin pasar el `.cli`. `vinculos` reconoce la prueba de muestreo
colgada de una referencia y devuelve su `MuestraId`.


**MCP 1.9.2 — tercer producto: ForSampling (`.cli`).** Pásale a `configurar` la ruta del
`.cli` del cliente de muestreo (suele estar en la carpeta `Muestreo` del expediente).
`contexto_expediente` devuelve las pruebas de muestreo; `obtener_entidad` gana cuatro
entidades: `pruebas`, `muestra` (los elementos seleccionados de una prueba), `evaluacion`
(la evaluación del auditor: atributos Sí/No, `SaldoAuditoria`, respuestas de la
circularización) y `parametros`. Las tres últimas necesitan `id = MuestraId`.

Los procedimientos (skills) son los mismos que en producción, en su versión de desarrollo.

## Requisitos

Los mismos que el canal de producción: Windows, Gesia abierto con el servidor API
arrancado (*Herramientas > Gesia - Cuadro de mando > Arrancar servidor API*), y el driver
de Access de 64 bits para el diario.
