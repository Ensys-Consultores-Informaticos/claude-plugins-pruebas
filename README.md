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

**MCP 1.14.0 — ticket 5: las facturas escaneadas se tachan en el equipo (plugin de pruebas 1.13.0, 15/09/2026).**
En `fsp-mum`, al llegar a los documentos el skill pregunta **«¿Cómo subo las facturas? (1) Tachadas · (2) Tal
cual»** con la consecuencia de cada una, y en los dos casos las imágenes las hace el MCP en el equipo del
auditor con `preparar_facturas`: los PDF no salen del equipo, suben JPEG a 100 ppp. Tachadas: cabecera,
nombre del emisor con su **token estampado** encima, CIF/IBAN/teléfono/correo/web, pie y márgenes en negro;
importes, fechas y número quedan legibles. Tal cual: nada se tapa, el token va en una esquina. El lector
transcribe el sello en `token` y el cruce lo usa en vez del nombre. Qué probar: una MUM o un cumplimiento con
«tachadas» de punta a punta —que las imágenes que suben no lleven el nombre del emisor, que el papel salga
igual que en claro (la calibración era 42/42 y 18/18), y qué tarda (unos 4 s por factura en el equipo)—; y
otra con «tal cual», que el token en la esquina no estorbe. `fsp-cumplimiento` todavía no pregunta.
**1.13.2 (16/09/2026), de reproducir en local la MUM del segundo registro (24 elementos) con «tachadas»:** la contrapartida sale 24 de 24 (la
muestra trae `Cuenta` como nombre y `CodigoCuenta` como código, y el 472 ya no cuenta como tercero: lo de «población
ajustada» era un diagnóstico falso); el tachado ya no se come el número de factura (importes ingleses, fechas en letras e
ISO son «dato»; la fila de rótulos se conserva en cadena y solo si toda es segura; el bloque de dirección no pisa la fila
de la fecha) y tapa lo que quedaba en claro (IBAN extranjero, UTR y sort code, TBAI, LOPD a media página, y el emisor
persona física bajo «Servicios prestados por:»). Qué probar: esa misma MUM con «tachadas» de punta a punta,
y ver si el lector deja de avisar de números y fechas ilegibles.
**1.13.1 (16/09/2026), del primer registro con el ticket 5:** `preparar_facturas` es incremental y se para a los
45 s (`pendientes`, se vuelve a llamar; el timeout de 60 s de Cowork ya no es un fallo); una población MUM
ajustada —los asientos están, los importes no— ya no se toma por «otro diario» y la contrapartida sale del
asiento; y la sección «PARA CONTAR AL ENTREGAR» va literal al auditor.

**MCP 1.13.0 — la muestra de ForSampling tokenizada por la contrapartida (plugin de pruebas 1.12.0, 15/09/2026).**
`fsp-mum` y `fsp-cumplimiento` tienen perfil: con `configurar(perfil=…)`, la muestra que exporta
`exportar_consulta(entidad="muestra")` —y la que enseña `obtener_entidad`— sale con el tercero
de cada fila como token. En una población de compras la columna «cuenta» es la de gasto (60x), así
que la cuenta del proveedor se busca como **contrapartida del asiento en el diario** (`NN_Contrapartida`
si existe; si no, la única 40/41 del asiento), y sin contrapartida o sin diario queda un token de
reserva `TER h…` que también rehidrata. Con un `.cli` activo el diario **lo indica el auditor**:
`configurar(smn_file=…)`, y `consultar_diario` se lo pide con la frase «necesito la contrapartida…».
El resumen de la exportación dice cuántos tokens salen por cuenta propia, por contrapartida y de
reserva, y cuántos asientos casan en el diario; si ninguno casa, error: «ese diario no es el de esta
población». **Plugin 1.12.1 (15/09/2026): `fsp-mum` ya lo usa.** Pone el perfil al empezar, pide la ruta del
diario al auditor cuando el fichero activo es un `.cli`, dice en una línea que las facturas se leen tal cual
(el tachado es el ticket 5, pendiente), traslada el resumen de tokens, y al entregar desanonimiza el papel
con `rehidratar(…, leyenda=true)`. `fsp-cumplimiento` todavía no. Qué probar: una MUM de punta a punta —que
en el chat no aparezca ninguna razón social de la muestra, que el papel del expediente llegue con nombres
reales y hoja «Tokens», y que el elemento con importe distinto salga como «sin documento» con su documento
sobrante al lado (el cruce va sin tercero hasta que las facturas lleven el token estampado).
**1.12.2 (15/09/2026), del primer registro de ejecución:** reintentar `configurar` hasta tres veces ante
«Connection closed»; los lotes del lector son los que imprime el script (seis facturas, un lote); y el conteo
de páginas sin PyMuPDF lee el `/Count` del PDF, no los objetos repetidos (daba 4 en un documento de una).

**MCP 1.12.0 — confidencialidad, tickets 2 y 3 (plugin de pruebas 1.11.0, 10/09/2026).**
`cancelacion-saldos`, `continuidad-saldos` y `cuadro-mando-diario` empiezan con
`configurar(perfil=…)`: el MCP retira del extracto las columnas que el skill no necesita y
**tokeniza los nombres de terceros** en todas sus salidas —`PROV 40000012`, `CLI 43000007`— para
que la razón social no salga del equipo del auditor ni al contenedor ni al chat. Al entregar,
`rehidratar(ruta, leyenda=true)` devuelve los nombres al papel ya en el disco del auditor (hoja
«Tokens» con la equivalencia). `configurar(nombres="claro")` lo apaga. Qué probar: que el modelo
ponga el perfil al empezar, hable por cuenta y token sin preguntar «quién es», y rehidrate al
final; y que el papel llegue con nombres reales y la hoja Tokens.

**MCP 1.11.1 (plugin de pruebas 1.10.3, 10/09/2026).** `configurar(gs3_anterior=…)` para el expediente
del ejercicio anterior —`configurar()` lo sugiere en `gs3_anterior_sugerido` cuando existe `<mismo nombre>
<año-1>.gs3` en la misma carpeta o en la hermana—, y `exportar_consulta` / `columnas` con
`fuente="diario_anterior"`, mismas reglas que `diario`. Es la pieza del MCP del futuro paso 0c de la
cancelación; el skill aún no lo usa. Y las REGLAS SQL de la ayuda dicen lo que JET no sabe hacer
(`COUNT(DISTINCT)`, `LIMIT`, `CASE WHEN`, `COALESCE`) con su forma correcta. Qué probar: que
`configurar()` sobre un expediente con `.gs3` de N-1 al lado lo sugiera, y que el modelo no lo
configure si nadie se lo pide.

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
