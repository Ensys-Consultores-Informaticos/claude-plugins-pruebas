---
name: fsp-mum-gesia
description: >
  Valida contra las facturas escaneadas la muestra de una PRUEBA MUM (muestreo
  por unidades monetarias) de ForSampling, el módulo de muestreo de la suite de
  Gesia: localiza el documento de cada elemento seleccionado, mide el importe que
  el documento sostiene y propone las tres columnas que espera ForSampling —saldo
  según auditoría, error y tasa de error— más la observación redactada para
  copiar, con la firma «Asistente IA». Genera el papel de trabajo en Excel con un
  elemento por fila. Usa este skill cuando el usuario pida validar o revisar la
  muestra de una prueba MUM, comprobar los importes contabilizados contra las
  facturas, calcular las diferencias o el error por elemento, rellenar el saldo
  según auditoría, o diga cosas como "revisa la MUM de servicios exteriores",
  "cuadra los importes de la muestra con las facturas", "qué diferencias hay
  entre libros y las facturas de la muestra", "rellena el saldo de auditoría" o
  "prueba MUM de ForSampling". NO es la prueba de cumplimiento (atributos Sí/No,
  que va por fsp-cumplimiento) ni la circularización de terceros, ni la
  cancelación de saldos del diario. **No proyecta el error a la población, no lo
  compara con el error tolerable y no concluye si la prueba pasa: eso lo hace
  ForSampling.** Requiere Gesia o ForSampling abierto con el servidor API
  arrancado, el expediente con cliente de muestreo vinculado (o el .cli
  directamente), y la carpeta con los documentos escaneados.
---

# Prueba MUM de ForSampling (fsp-mum)

Una MUM selecciona elementos de una población con probabilidad proporcional a su
importe, y el auditor comprueba en cada uno **cuánto vale de verdad**. De la diferencia
entre lo contabilizado y lo que sostiene el documento sale el error, y ForSampling lo
proyecta a la población. Este skill hace la parte de mirar el documento y medir.

Los ficheros se escriben en `<expediente>\InformesGesia\FspMum\` y **nunca se publican**
en ninguna URL: llevan la contabilidad de un cliente auditado.

**Este skill no escribe en ForSampling.** El MCP solo lee. Los importes propuestos y la
observación se copian a mano, y la firma «Asistente IA» deja constancia de quién los
redactó.

---

## Lo que mide, y lo que no hace por ti

Tres columnas por elemento, con los nombres que usa ForSampling:

| Columna | Qué es |
|---|---|
| `SaldoAuditoria` | lo que el documento sostiene para ese apunte |
| `ErrorAuditoria` | `Saldo − SaldoAuditoria`. Positivo: los libros dicen de más |
| `ErrorAuditoriaTasa` | el error sobre el saldo, en tanto por ciento |

**Lo que no hace, y no es un olvido:**

- **No proyecta el error a la población.** La proyección, el límite superior del error y
  la conclusión los calcula ForSampling con la muestra evaluada. Hacerlos aquí sería
  sustituir el motor estadístico de la prueba por una cuenta a ojo.
- **No compara con el error tolerable.** El papel lo enseña como contexto de la prueba,
  y ahí se queda.
- **No suma los errores, y sobre todo no los netea.** Un error de +600 y otro de −600 no
  se cancelan: son dos incorrecciones que se proyectan cada una por su lado. Decir «error
  neto cero» es el fallo más caro que puede cometer quien lee esta prueba, y ha pasado. Al
  ejecutar, los errores por exceso y por defecto se imprimen **por separado**.
- **No dice si la prueba pasa.** Eso es del auditor.

**El término de comparación lo fija la propia muestra.** Un apunte de gasto suele llevar
la base imponible y el IVA va a otra cuenta; otro puede llevar el total. En vez de
suponerlo por el plan contable, el skill mira **con qué casan los elementos que casan** y
usa ese término —base, total o neto tras retención— para medir los que no casan. Si la
muestra no da un criterio claro, no propone importe: lo decide el auditor. Equivocarse de
término convierte una cuota de IVA en un error de auditoría, y ese error se proyectaría a
toda la población.

---

## Dónde están los scripts

Al cargarse, el runtime indica el **directorio base del skill**. Las rutas `scripts/…`
son relativas a él, no al directorio de trabajo.

```bash
SKILL="<directorio base indicado al cargar el skill>"
TRABAJO="$(pwd)/trabajo" && mkdir -p "$TRABAJO"
```

Son cuatro: `preparar_documentos.py` (inventaría y renderiza las páginas que hacen falta,
y lleva la cuenta de lo transcrito), `verificar_contrato.py`, `generar_papel.py` y
`ejecutar_mum.py`, que encadena los dos últimos. Más `probar_mum.py`, el arnés.

---

## Secuencia

### Paso 1 — Expediente, cliente de muestreo y prueba

```
configurar()            # sin parámetros: ver estado
contexto_expediente()
```

Si el fichero activo es un `.gs3`, `configurar` deduce solo el `.cli` del cliente de
muestreo (`cli_file`). Si dice «sin cliente de muestreo vinculado», pregunta al usuario si
existe el `.cli` —suele estar en la carpeta `Muestreo` del expediente— y pásaselo a
`configurar` como fichero activo. Si tampoco existe, **para**.

```
obtener_entidad('pruebas')
```

**Pregunta qué prueba quiere validar** si hay más de una MUM, enseñando nombre, ejercicio,
área y referencia. No adivines por el nombre: «Servicios exteriores 24» y «Servicios
exteriores 25» son dos pruebas distintas con dos carpetas de facturas distintas. Si el
usuario nombra la prueba y el ejercicio, no preguntes.

Una prueba de tipo `Cumplimiento` **no es de este skill** —va por `fsp-cumplimiento`— y
una de `Confirmación Terceros` tampoco. Dilo y para.

### Paso 2 — Traer la muestra, los parámetros y la evaluación

```
exportar_consulta(entidad = "muestra", id = <MuestraId>, ruta = "<DATOS>/muestra.json")
obtener_entidad('parametros', id = <MuestraId>)      → guárdalo tal cual en <DATOS>/parametros.json
```

Y si el auditor ya evaluó la prueba, también:

```
exportar_consulta(entidad = "evaluacion", id = <MuestraId>, ruta = "<DATOS>/evaluacion.json")
```

Con ella, al ejecutar se imprime la comparación elemento a elemento: su importe frente al
propuesto. Es la calibración del skill sobre ese encargo, y donde se ve si se dejaría pasar
una incorrección.

`parametros.json` trae, además del tipo de prueba, el contexto que va al encabezado del
papel: unidad de muestreo, número de elementos de la población, **error tolerable** y
tamaño de muestra deseado. Guárdalo tal cual, sin recortarlo.

**Dónde es `<DATOS>` no depende del producto, depende de una propiedad**: si los scripts y
el MCP comparten disco. Compruébalo por la ruta que te devuelve `configurar`, no por dónde
creas que estás corriendo.

```bash
# Comparten disco (los scripts ven las rutas de Windows del MCP): directo.
DATOS="$TRABAJO"

# No lo comparten (los scripts corren en un contenedor): exportar DENTRO de una carpeta
# conectada -una ruta del sandbox o del $TEMP de Windows no sirve-, subirla, y leer la
# copia del sandbox.
DATOS="/mnt/user-data/uploads/_tmp_cowork"
```
**El escenario habitual en Cowork**, para no volver a razonarlo cada sesión: el MCP corre en
el equipo del usuario y los scripts en el contenedor de la nube, así que **no comparten
disco**. Ahí la receta es fija: exportar dentro de la carpeta conectada del expediente, subir,
y trabajar con la copia del sandbox. Reutiliza siempre la **misma** carpeta temporal
(`_tmp_cowork`) en vez de crear una por ejecución: `limpiar_exportaciones()` borra los
ficheros pero no la carpeta, y quedan directorios vacíos por ahí.

### Paso 3 — Preparar y leer los documentos

Pide la carpeta con los documentos escaneados de la prueba (suele estar en
`Documentacion\<ejercicio>\<área>` del expediente, y a veces en una subcarpeta
`Facturas` dentro de ella; el script busca en profundidad).

```bash
python "$SKILL/scripts/preparar_documentos.py" --carpeta "<la carpeta>" --trabajo "$DATOS"
```

Inventaría los PDF, aparta los justificantes de pago y **renderiza a PNG la primera página
de cada documento**, a 100 puntos por pulgada. No renderiza el resto a propósito: de una
factura interesan la primera página, que lleva la identidad, y la última, que suele llevar
los totales. Una página cuesta unos 1.290 tokens.

**Si el entorno tiene subagentes** (Claude Cowork y Claude Code los tienen; ChatGPT Cowork
no), **no leas tú las imágenes: reparte la lectura en lotes y lanza el agente lector**, que
es del plugin y se llama `lector-facturas`. El coste total de mirar las páginas es el mismo,
pero sale de tu contexto y los lotes van en paralelo: la MUM de 42 elementos pasó de diez
minutos leyendo en línea a leer cuatro lotes a la vez.

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --lotes 10
```

Escribe `lotes.json` y te imprime cada lote con sus imágenes y la ruta donde ese lector
tiene que dejar su resultado (`facturas_lote_N.json`). Lanza **un agente por lote, todos en
la misma tanda**, hasta cuatro a la vez; a cada uno le pasas en el prompt **el nombre de la entidad
auditada** (el de `contexto_expediente`), la lista de sus documentos con las imágenes y la
ruta de salida, y nada más: ni la muestra, ni los importes de libros. El nombre de la entidad
va para que el lector sepa qué lado del documento NO es el tercero: en una prueba de ventas
las facturas las emite la propia entidad y el tercero es el destinatario. Cada lector devuelve una línea de resumen; si uno devuelve el JSON entero en vez
de escribir el fichero, escríbelo tú en su ruta. Si uno falla, **un reintento** con el mismo
lote; si vuelve a fallar, lee tú ese lote en línea. Después:

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --fusionar
```

junta los lotes en `facturas.json` y te dice si falta algún documento del inventario o si
algún lector se inventó uno. Con todo transcrito, sigue en el paso siguiente. **Solo si tu
entorno no tiene subagentes**, lee las imágenes tú, como sigue.

**Lee las imágenes que te ha dejado**, no los PDF. Si en la primera página no están los
totales, pide la que falte:

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --ampliar "<fichero>"
```

De cada factura anota lo siguiente, y **escribe `<DATOS>/facturas.json` cada cinco o seis
documentos**, no al final:

```json
{"facturas": [
  {"fichero": "20260226142827850.pdf", "proveedor": "Inmobiliaria X, S.L.", "cif": "B00000000",
   "numero": "A-2025-118", "fecha": "13/03/2025", "base": "12500,00", "pct_iva": "21",
   "iva": "2625,00", "irpf": "", "total": "15125,00", "paginas": 1, "notas": ""}
]}
```

**En una MUM la base y el total pesan igual**: el término de comparación se decide después,
así que hay que leer los dos siempre que estén. Si uno no se lee, déjalo vacío y dilo en
`notas`: nunca lo calcules aplicando un tipo de IVA, porque entonces el error que salga
será el de tu cálculo y no el del documento.

Si algo no se lee, **déjalo vacío**. Nunca lo completes por deducción ni lo copies de otra
factura del mismo proveedor.

Si el contexto se compacta a mitad, **no preguntes al usuario por dónde ibas**:

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --estado
```

compara el inventario con lo ya transcrito y dice qué queda.

**Si un elemento sale «sin documento» y a la vez sobra un documento del mismo tercero**, casi
siempre no es un extravío: **es una diferencia real de importe**. El cruce se apoya en el
importe, que es justo lo que la prueba pone en duda, así que cuando no cuadra puede quedarse
sin atar. El script lo detecta y lo dice como «POSIBLE DIFERENCIA, no extravío» con las dos
cifras. No lo resuelvas reintentando: mira los dos, y si son el mismo documento, **átalo a
mano** añadiendo `poblacion_id` a esa entrada de `facturas.json` con el id del elemento:

```json
{"fichero": "2025000042 X.pdf", "poblacion_id": "301", "proveedor": "…", "base": "1234,56", "…": ""}
```

Con eso el documento se asigna a ese elemento sin pasar por la puntuación, y el papel hace
constar que el vínculo lo puso el auditor.

**Y si la observación dice «ATENCIÓN: asignado solo por tercero y fecha, y había más de un
candidato»**, confírmalo antes de entregar: hay dos documentos del mismo tercero que encajan
igual de bien y el skill no puede saber cuál va con cuál. Se resuelve igual, con
`poblacion_id`.

**Cuatro trampas de la lectura**, todas medidas:

- **El número del ángulo superior derecho suele ser el sello de registro del cliente**, no
  el número del proveedor, que está en el cuerpo junto a «Factura nº».
- **El CIF que se pide es el del proveedor**, no el del cliente.
- **Hay tres formas legítimas de que el total no sea base + IVA**: exención o no sujeción
  (intracomunitaria, inversión del sujeto pasivo, art. 20 LIVA), retención de IRPF cuando
  el documento imprime el neto a pagar, y el redondeo. Transcribe la retención en `irpf`.
- **Las rectificativas llevan importes negativos**, que son correctos.

### Paso 4 — Verificar y generar el papel (puede abortar)

```bash
PAPEL="MUM <PRUEBA> <CLIENTE> <EJERCICIO>.xlsx"
# Si el nombre de la prueba ya empieza por «MUM», no lo repitas: «MUM Ventas 25», no
# «MUM MUM Ventas 25». Medido en el primer uso real.
python "$SKILL/scripts/ejecutar_mum.py" \
    --muestra "$DATOS/muestra.json" --parametros "$DATOS/parametros.json" \
    --facturas "$DATOS/facturas.json" --evaluacion "$DATOS/evaluacion.json" \
    --salida "$TRABAJO/$PAPEL" --generado "<AAAA-MM-DD, la fecha que te dé el usuario>"
```

`--evaluacion` solo si existe. `--generado` es la fecha de generación, que se pasa porque
**nada lee el reloj**: el papel tiene que poder regenerarse idéntico.

Salida `2` → **para**: el contrato no se cumple —la población no tiene columna de importe,
la prueba no es MUM, la evaluación tiene forma de prueba de cumplimiento— y **no se ha
escrito nada**.

Salida `1` → el papel **sí está escrito**, pero hay avisos. **Léelos y cuéntalos al
entregar.**

Imprime, además, el término con el que compara esta población, los elementos con diferencia
y, si había evaluación, el recuento frente al auditor. **Lee esa salida antes de entregar.**

En un entorno donde los scripts no comparten disco con el expediente, el papel se escribe
en el sandbox y se envía; donde sí lo comparten, pásale a `--salida` la ruta del expediente
directamente y el script crea el árbol. Si el expediente está en OneDrive, el entorno puede
pedir autorización antes de escribir: pídesela al usuario y repite.

### Paso 5 — Entregar

Di dónde ha quedado el fichero y, **antes que nada**:

1. **El término de comparación** que ha usado la muestra (base, total o neto). Todo lo
   demás depende de eso.
2. **Los elementos con diferencia**, uno por uno y con sus cifras.
3. Los errores **por exceso y por defecto, por separado**, tal como los imprime el script.
   Nunca sumados entre sí.
4. Cuántos elementos quedaron sin documento o sin medir, y qué documentos de la carpeta no
   son de ningún elemento.

Si había evaluación del auditor, traslada las cifras de la comparación. La que importa es
**«el skill da 0 y el auditor puso error»**: incorrecciones que se habrían dejado pasar.

**Lo que no digas**: el error proyectado, el error neto, si se supera el error tolerable, o
si la prueba pasa. Nada de eso sale de este papel.

**Los temporales.** `parametros.json` lo escribiste tú desde la respuesta de `obtener_entidad`, así que `limpiar_exportaciones()` **no lo borra**: bórralo aparte, y en una carpeta conectada puede pedir permiso de borrado. `limpiar_exportaciones()` borra la muestra y la evaluación exportadas.
`facturas.json` y el directorio de imágenes los escribiste tú: bórralos con el directorio de
trabajo. Los PDF no se copian a ningún sitio.

---

## Cómo se lee el papel

**Una sola hoja, «Análisis muestra».** Una fila por elemento seleccionado: sus columnas de
población tal como vienen —incluidas `Repeticiones`, que es cuántas unidades de muestreo
representa—, el documento localizado y lo leído en él, por qué clave casó, las tres columnas
de la MUM rotuladas **(propuesto)**, con qué término se comparó, y la **observación
propuesta** lista para copiar a ForSampling.

Las tres columnas **sí** se rellenan, al contrario que los atributos de la prueba de
cumplimiento, y la diferencia no es un descuido: un atributo es un veredicto, y rellenarlo
es concluir; un importe leído en un documento es una medida, y decirlo es describir.

Un solo color, **amarillo en la observación** cuando hay diferencia o cuando el elemento no
se ha podido medir. Arriba, la hoja se identifica: prueba, área, referencia, ejercicio,
unidad de muestreo, tamaño de la población, error tolerable y fecha de generación.

**No hay fila de totales, a propósito.** Sumar los errores de una MUM es proyectar a ojo.

## Degradación

| Situación | Qué sale |
|---|---|
| Sin `.cli` vinculado ni indicado | **para** en el paso 1 |
| La prueba no es MUM | **para** (C04): las de cumplimiento van por `fsp-cumplimiento` |
| La población no tiene columna de importe | **para** (C02): en una MUM el importe es lo que se mide |
| La evaluación tiene forma de prueba de cumplimiento (A1..An) | **para** (C06): se ha exportado la prueba equivocada |
| La población no trae fecha o número de documento | sigue: el cruce va por importe y tercero, y el papel lo dice (A01, A02) |
| La muestra mezcla importes positivos y negativos | sigue, y avisa (A04): el error sigue el signo del saldo |
| Un documento sin base ni total legibles | sigue: ese elemento queda sin medir, y se dice (A07) |
| La muestra no fija un término de comparación claro | sigue: los elementos que no casan quedan sin importe propuesto, con el motivo |
| Una columna de tercero que vale lo mismo en todas las filas | el skill cambia de columna solo, y lo avisa (A00). Fue el fallo de la MUM de ventas: «Nombre» valía «Ventas» en las 42 filas |
| Dos documentos del mismo tercero encajan igual en un elemento | sigue: se asigna el de fecha más cercana, y si empatan también en fecha se marca la observación como dudosa |
| Un elemento sin documento y un documento sobrante del mismo tercero | sigue, y el script lo señala como POSIBLE DIFERENCIA con las cifras: se ata con `poblacion_id` |
| Sin PyMuPDF ni `pdftoppm` | `preparar_documentos.py` **para** y lo dice; camino alterno, abrir los PDF directamente |
| Sin evaluación del auditor | sigue: no hay comparación que imprimir |
| Fichero de salida abierto en Excel | **para** al guardar, y dice que hay que cerrarlo |

## Comprobar que el skill funciona

```bash
python "$SKILL/scripts/probar_mum.py"
```

No hace falta ForSampling ni un solo PDF: 23 comprobaciones sobre un fixture sintético de
ocho elementos elegidos por lo que puede salir mal en una MUM —gasto por la base, diferencia
real con su tasa, sin documento, contabilizado por el total, ingreso con saldo negativo,
ingreso negativo con diferencia, documento sin total legible cuya diferencia es justo la
cuota de IVA, y un elemento sin importe—. Comprueba además que el término de comparación sale
de la muestra, que **los errores no se netean nunca**, que se detecta el caso en que el skill
da 0 donde el auditor puso error, y que `lib_fsp.py` es byte a byte el mismo fichero que en
`fsp-cumplimiento`.
