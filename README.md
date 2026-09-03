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
