---
name: fsp-cumplimiento-gesia
description: >
  Valida contra las facturas escaneadas la muestra de una PRUEBA DE CUMPLIMIENTO
  de ForSampling (el módulo de muestreo de la suite de Gesia): localiza el
  documento de cada elemento seleccionado, comprueba lo que se puede comprobar
  desde el documento —que existe y es el del apunte, que base + IVA = total, que
  importe y fecha coinciden con libros— y propone por elemento un veredicto por
  atributo (Ok, hallazgo con cifras, o «auditor» cuando el control no se infiere
  del documento), redactado con la fórmula «Asistente IA: A1: Ok · A2: … · A3:
  auditor». Genera el papel de trabajo en Excel: una hoja con un elemento por fila,
  el documento localizado, lo leído en él y la observación propuesta. Usa este skill
  cuando el usuario pida validar, revisar o documentar la muestra de una prueba de
  cumplimiento, cruzar la muestra con las facturas escaneadas, rellenar los
  atributos de una prueba de ForSampling, o diga cosas como "valida la muestra de
  compras contra las facturas", "revisa las facturas de la prueba de cumplimiento",
  "cruza la selección con los PDF", "rellena los atributos" o "prueba de
  cumplimiento de ForSampling". NO es la prueba MUM (importes según auditor y
  errores) ni la circularización (cartas de terceros), ni la cancelación de saldos
  del diario. Requiere Gesia o ForSampling abierto con el servidor API arrancado, el
  expediente con cliente de muestreo vinculado (o el .cli directamente), y la
  carpeta con los documentos escaneados.
---

# Prueba de cumplimiento de ForSampling (fsp-cumplimiento)

Una prueba de cumplimiento selecciona N elementos de una población —facturas de
compra, nóminas— y el auditor comprueba en cada uno una serie de **atributos**
binarios: ¿está el documento?, ¿cuadran los cálculos?, ¿se contabilizó en fecha y
cuenta correctas?, ¿está autorizado? Este skill hace la parte que se puede hacer
desde el documento y deja explícitamente al auditor la que no.

Los ficheros se escriben en `<expediente>\InformesGesia\FspCumplimiento\` y
**nunca se publican** en ninguna URL: llevan la contabilidad de un cliente auditado.

**Este skill no escribe en ForSampling.** El MCP solo lee. La observación propuesta
por elemento se copia a mano a ForSampling, y la firma «Asistente IA» deja
constancia de quién la redactó.

---

## Lo que evalúa y lo que no

Cada atributo de la prueba se clasifica en un **rol**, y el rol decide qué hace el
skill con él:

| Rol | Qué comprueba el skill | Ejemplos de atributo |
|---|---|---|
| `documento` | que el documento existe en la carpeta y es el del apunte (lo ata el importe o el número) | «12 DOCUMENTO — evidencia documental», «CI02_07 Albaranes» |
| `calculo` | la aritmética del documento: base + IVA = total, y con exención o retención de IRPF, la regla que corresponda | «03 CALCULO» |
| `contabilizacion` | que el importe y la fecha del documento coinciden con los de libros | «11 CONTABILIZACIÓN — en fecha y cuenta correcta» |
| `auditor` | **nada**: el atributo no se infiere del documento | «02 AUTORIZACIÓN», «05 REGISTRO oportuno», pedidos, anticipos, pagos |

**El rol lo confirma el auditor, siempre.** El skill propone uno por el nombre del
atributo, pero los nombres cambian por firma —`12 DOCUMENTO` en un despacho,
`CI02_07 Albaranes` en otro— y el mismo nombre puede significar otra cosa en otra
prueba. Nunca se aplica una clasificación que el auditor no haya visto.

**Casar por la base imponible no es hallazgo.** En una cuenta de gasto o de ingreso el
apunte lleva la base y el IVA va a la 472/477. Medido en la calibración: los 18
elementos de una prueba de compras casan por la base, y marcarlo habría sido 18
falsos hallazgos.

**El número de factura de libros puede no ser el de la factura.** En la población de
calibración la columna `Documento` era un número interno de registro (374, 253…),
no el del proveedor. Por eso el documento se localiza con **el importe como clave
fuerte**, el tercero y el número exacto como medias, y la fecha como débil; y que el
número de libros no coincida **se informa, no se marca**.

---

## Dónde están los scripts

Al cargarse, el runtime indica el **directorio base del skill**. Las rutas
`scripts/…` son relativas a él, no al directorio de trabajo.

```bash
SKILL="<directorio base indicado al cargar el skill>"
TRABAJO="$(pwd)/trabajo" && mkdir -p "$TRABAJO"
```

Son cuatro: `preparar_documentos.py` (inventaría y renderiza las páginas que hacen falta,
y lleva la cuenta de lo transcrito), `verificar_contrato.py`, `generar_papel.py` y
`ejecutar_fsp.py`, que encadena los dos últimos. Más `probar_fsp.py`, el arnés.

---

## Secuencia

### Paso 1 — Expediente, cliente de muestreo y prueba

```
configurar()            # sin parámetros: ver estado
contexto_expediente()
```

Si el fichero activo es un `.gs3`, `configurar` deduce solo el `.cli` del cliente de
muestreo (`cli_file`). Si dice «sin cliente de muestreo vinculado», el encargo no
tiene ForSampling enlazado desde Gesia: pregunta al usuario si existe el `.cli` —suele
estar en la carpeta `Muestreo` del expediente— y pásaselo a `configurar` como fichero
activo. Si tampoco existe, **para**: sin pruebas de muestreo no hay nada que validar.

```
obtener_entidad('pruebas')
```

**Pregunta qué prueba quiere validar** si hay más de una de cumplimiento, enseñando
nombre, ejercicio, área y referencia. No adivines por el nombre: «Compras 24» y
«Compras 25» son dos pruebas distintas con dos carpetas de facturas distintas. Si el
usuario nombra la prueba y el ejercicio, no preguntes.

Una prueba de tipo `MUM` o `Confirmación Terceros` **no es de este skill**: dilo y para.

### Paso 2 — Traer la muestra y los parámetros

```
exportar_consulta(entidad = "muestra", id = <MuestraId>, ruta = "<DATOS>/muestra.json")
obtener_entidad('parametros', id = <MuestraId>)      → guárdalo tal cual en <DATOS>/parametros.json
```

Y si el auditor ya evaluó la prueba (la `_AN` existe), también:

```
exportar_consulta(entidad = "evaluacion", id = <MuestraId>, ruta = "<DATOS>/evaluacion.json")
```

Con ella, al ejecutar se imprime la comparación celda a celda: lo que puso el auditor
frente a lo que propone el skill. No va al papel, va a la pantalla, y es la calibración
del skill sobre ese encargo: donde se ve si se dejaría pasar algo.

**Dónde es `<DATOS>` no depende del producto, depende de una propiedad**: si los scripts
y el MCP comparten disco. Compruébalo por la ruta que te devuelve `configurar`, no por
dónde creas que estás corriendo.

```bash
# Comparten disco (los scripts ven las rutas de Windows del MCP): directo.
DATOS="$TRABAJO"

# No lo comparten (los scripts corren en un contenedor): exportar DENTRO de una carpeta
# conectada -una ruta del sandbox o del $TEMP de Windows no sirve-, subirla, y leer la
# copia del sandbox.
#   exportar_consulta(..., ruta = "<raíz conectada>/_tmp_cowork/muestra.json")
DATOS="/mnt/user-data/uploads/_tmp_cowork"
```
**El escenario habitual en Cowork**, para no volver a razonarlo cada sesión: el MCP corre en
el equipo del usuario y los scripts en el contenedor de la nube, así que **no comparten
disco**. Ahí la receta es fija: exportar dentro de la carpeta conectada del expediente, subir,
y trabajar con la copia del sandbox. Reutiliza siempre la **misma** carpeta temporal
(`_tmp_cowork`) en vez de crear una por ejecución: `limpiar_exportaciones()` borra los
ficheros pero no la carpeta, y quedan directorios vacíos por ahí.

`parametros.json` lo escribes tú desde la respuesta de `obtener_entidad`: son dos KB,
no hace falta exportarlo.

### Paso 3 — Confirmar los roles de los atributos · PUERTA

Enseña al usuario los atributos de la prueba tal como vienen en `parametros.json`
(`atributos`: id, nombre, descripción) **con el rol que propones para cada uno**, y
espera su confirmación o sus cambios. Guárdalo en `<DATOS>/roles.json`:

```json
{"1": "auditor", "2": "contabilizacion", "3": "documento", "4": "auditor", "5": "calculo"}
```

Regla para proponer: el documento, la evidencia documental, los albaranes → `documento`;
los cálculos, el IVA → `calculo`; «contabilizado en fecha y cuenta» → `contabilizacion`;
autorización, aprobación, pedido, anticipo, pago, oportunidad del registro → `auditor`.
**Ante la duda, `auditor`**: un `Ok` que el skill no puede sostener con el documento
delante es peor que dejárselo al auditor.

### Paso 4 — Leer los documentos

Pide la carpeta con los documentos escaneados de la prueba (puede subirla o indicarte
dónde está; suele estar en `Documentacion\<ejercicio>\<área>` del expediente). Y prepárala
antes de leer nada:

```bash
python "$SKILL/scripts/preparar_documentos.py" --carpeta "<la carpeta>" --trabajo "$DATOS"
```

Inventaría los PDF, aparta los justificantes de pago y **renderiza a PNG la primera página
de cada documento**, a 100 puntos por pulgada. No renderiza el resto a propósito: de una
factura interesan la primera página, que lleva la identidad, y la última, que suele llevar
los totales; las de en medio son líneas de detalle que esta prueba no mira. Una página
cuesta unos 1.290 tokens, así que leerlas todas sale un 50 % más caro sin aportar nada.

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
totales —hay facturas donde la página 1 dice «SEGUE» y el total está en la siguiente—, pide
la que falte y no des ningún total por leído hasta verlo escrito como total:

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --ampliar "<fichero>"
# y con --pagina N si hace falta una concreta en vez de la última
```

De cada factura anota lo siguiente, y **escribe `<DATOS>/facturas.json` cada cinco o seis
documentos**, no al final:

```json
{"facturas": [
  {"fichero": "7 - PROVEEDOR FRA A-125.pdf", "proveedor": "Asesores Argos, S.L.P.", "cif": "B00000000",
   "numero": "A-125", "fecha": "14/04/2025", "base": "1000,00", "pct_iva": "21",
   "iva": "210,00", "irpf": "150,00", "total": "1210,00", "albaranes": ["25-0018"],
   "paginas": 3, "notas": ""}
]}
```

`fichero` tal cual se llama en la carpeta; importes como los ves, con coma decimal; el
número de factura **tal como lo escribe el proveedor** (`FA25/00042`, `A00/00000901`,
`FT 1/1130`): el cruce lo normaliza él. `pct_iva` e `irpf`, solo si el documento los trae.
Si algo no se lee, **déjalo vacío** y dilo en `notas`: nunca lo completes por deducción ni
lo copies de otra factura del mismo proveedor. El contrato avisa de cuántos van sin total
o sin número.

Escribirlo por lotes no es burocracia: leer veinte facturas es una sesión larga y el
contexto se compacta a mitad. Si eso pasa, **no preguntes al usuario por dónde ibas**:

```bash
python "$SKILL/scripts/preparar_documentos.py" --trabajo "$DATOS" --estado
```

compara el inventario con lo ya transcrito y te dice qué queda y con qué imágenes seguir.

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
  el número del proveedor, que está en el cuerpo junto a «Factura nº». Y en libros la
  columna del documento puede ser otro número interno distinto de los dos.
- **El CIF que se pide es el del proveedor**, no el del cliente, que sale más arriba en
  «Facturado a».
- **Hay tres formas legítimas de que el total no sea base + IVA**: exención o no sujeción
  (intracomunitaria, art. 20 LIVA, formación: IVA cero y base = total), retención de IRPF
  cuando el documento imprime el neto a pagar (15 % profesionales, 19 % arrendamientos), y
  el redondeo. Transcribe la retención en `irpf` y el script aplica la regla que toque;
  ninguna de las tres es hallazgo.
- **Las rectificativas llevan importes negativos**, que son correctos, y se numeran con
  `R/` o `FR-`.

Si el script aparta un fichero que era la factura, o deja como factura un justificante,
dilo y sigue con la lista corregida: el reparto por nombre acierta casi siempre pero no
puede acertar del todo.

### Paso 5 — Verificar y generar el papel (puede abortar)

Una sola orden: comprueba el contrato y, solo si se puede seguir, escribe el papel.

```bash
PAPEL="Cumplimiento <PRUEBA> <CLIENTE> <EJERCICIO>.xlsx"
# Si el nombre de la prueba ya empieza por «Cumplimiento», no lo repitas: «Cumplimiento Ventas 25», no
# «Cumplimiento Cumplimiento Ventas 25». Medido en el primer uso real.
python "$SKILL/scripts/ejecutar_fsp.py" \
    --muestra "$DATOS/muestra.json" --parametros "$DATOS/parametros.json" \
    --facturas "$DATOS/facturas.json" --roles "$DATOS/roles.json" \
    --evaluacion "$DATOS/evaluacion.json" \
    --salida "$TRABAJO/$PAPEL" --generado "<AAAA-MM-DD, la fecha que te dé el usuario>"
```

`--evaluacion` solo si existe. `--generado` es la fecha de generación, que se pasa
porque **nada lee el reloj**: el papel tiene que poder regenerarse idéntico.

Salida `2` → **para**: el contrato no se cumple —la población no tiene columna de
importe o de fecha, la prueba no es de cumplimiento, no hay atributos, los roles no
cubren todos— y **no se ha escrito nada**.

Salida `1` → el papel **sí está escrito**, pero hay avisos: documentos sin total o sin
número legible, menos documentos que elementos, roles sin confirmar. **Léelos y
cuéntalos al entregar**, no los escondas.

Imprime, además, cada elemento con algún hallazgo y, si había evaluación del auditor,
el recuento frente a ella. **Lee esa salida antes de entregar.**

**En Cowork el script escribe en el sandbox, no en el expediente**: se envía con
`SendUserFile`, que devuelve un `file_uuid`, y con `device_commit_files` se escribe en
`<expediente>/InformesGesia/FspCumplimiento/<PAPEL>`. En la máquina del auditor pásale
directamente a `--salida` la ruta del expediente: el script crea el árbol.

**Si el expediente está en OneDrive, el entorno puede rechazar la escritura antes de
ejecutar nada** y pedir autorización expresa. No es un fallo: pídesela al usuario y
repite la orden.

### Paso 6 — Entregar

Di dónde ha quedado el fichero y, **antes que nada**, los elementos con hallazgo con
sus cifras —«ALFA FA25/00042: importe en factura 4.500,00, en libros 4.950,00,
diferencia 450,00»—. Después: cuántos documentos se localizaron y por qué clave,
cuántos elementos quedan sin documento, cuántos documentos sobran en la carpeta, y
qué atributos quedaron al auditor.

Si había evaluación del auditor, traslada las cuatro cifras que imprime el script. La
que importa es **«skill Ok, auditor No»**: hallazgos que el skill se habría dejado
pasar. «Skill señala, auditor Sí» hay que mirarlos, no darlos por error del skill: en
la calibración eran dos, los dos del mismo elemento, y el propio auditor tenía la
diferencia anotada a mano en la factura.

**Lo que no digas**: si la prueba pasa o no. Eso es del auditor y de ForSampling.

**Los temporales.** `parametros.json` lo escribiste tú desde la respuesta de `obtener_entidad`, así que `limpiar_exportaciones()` **no lo borra**: bórralo aparte, y en una carpeta conectada puede pedir permiso de borrado. `limpiar_exportaciones()` borra la muestra y la evaluación
exportadas. `facturas.json` y `roles.json` los escribiste tú: bórralos con el
directorio de trabajo. Los PDF no se copian a ningún sitio.

---

## Cómo se lee el papel

**Una sola hoja, «Análisis muestra».** Una fila por elemento seleccionado: sus columnas
de población tal como vienen, el documento localizado y lo leído en él (número, fecha,
base, IVA, retención, total), por qué clave casó, la diferencia de importe, los días
entre documento y libros, **una columna por atributo en blanco** y la **observación
propuesta**, lista para copiar a ForSampling.

Las columnas de atributos van vacías a propósito: el skill no marca `Ok` ni escribe
`auditor` en ellas. Cuenta lo que ha visto en la observación y deja las casillas a quien
firma. Un solo color, **amarillo en la observación** cuando señala algo.

Arriba, la hoja se identifica: prueba, tipo, área, referencia, ejercicio y fecha de
generación, más las dos líneas que dicen que es una propuesta y lo que el papel no prueba.

**Lo que no está en la hoja se imprime al ejecutar**: los recuentos, los elementos con
hallazgo, los documentos de la carpeta que no son de ningún elemento y, si se pasó la
evaluación, la comparación con el auditor. Eso hay que leerlo y contarlo al entregar,
porque el papel ya no lo lleva escrito.

---

## Lo que este skill no hace

- **No escribe en ForSampling ni en Gesia.** El MCP solo lee.
- **No decide si la prueba pasa.** Ni cuenta desviaciones contra un tamaño de
  muestra ni calcula tasas: eso lo hace ForSampling cuando el auditor introduce los
  atributos.
- **No evalúa lo que no está en el documento**: autorización, pedido, anticipo,
  oportunidad del registro. Esos atributos salen como `auditor`, siempre.
- **No es OCR de facturas en general.** Lee las de la muestra, y solo para cruzarlas.
- **No elige la prueba ni la carpeta.** Eso lo dice el auditor en los pasos 1 y 4.

## Degradación

| Situación | Qué sale |
|---|---|
| Sin `.cli` vinculado ni indicado | **para** en el paso 1 |
| La prueba no es de cumplimiento | **para** (C04): MUM y circularización van por otro skill |
| La prueba no tiene atributos | **para** (C04): no hay controles que evaluar |
| La población no tiene columna de importe o de fecha | **para** (C02) |
| La población no tiene número de factura ni concepto | sigue: cruce por importe, tercero y fecha (A01) |
| Sin `--roles` | sigue con la propuesta automática, y avisa (A05). El paso 3 dice que no |
| Documentos sin total o sin número legible | sigue, y avisa cuántos (A06, A07) |
| Menos documentos que elementos | sigue: los elementos sin documento salen con «No localizada» (A09) |
| Sin evaluación del auditor | sigue: no hay comparación que imprimir |
| Fichero de salida abierto en Excel | **para** al guardar, y dice que hay que cerrarlo |
| Sin PyMuPDF ni `pdftoppm` en el entorno | `preparar_documentos.py` **para** y lo dice. Camino alterno: abrir los PDF directamente, pidiendo solo la primera página de cada uno |
| El expediente en OneDrive con los PDF sin sincronizar | **para** con el error 22 y el paso a seguir: «Mantener siempre en este dispositivo» |
| Un justificante mal clasificado como factura, o al revés | sigue: el que sobra se imprime como «documento que no es de ningún elemento»; el que falta, dilo y amplía la lista a mano |
| Una columna de tercero que vale lo mismo en todas las filas | el skill cambia de columna solo, y lo avisa (A00) |
| Dos documentos del mismo tercero encajan igual en un elemento | sigue: gana el de fecha más cercana; si empatan, el atributo de documento lo dice y pide confirmación |
| Un elemento sin documento y un documento sobrante del mismo tercero | sigue, y el script lo señala como POSIBLE DIFERENCIA: se ata con `poblacion_id` |

## Comprobar que el skill funciona

```bash
python "$SKILL/scripts/probar_fsp.py"
```

No hace falta ForSampling ni un solo PDF: 46 comprobaciones sobre un fixture sintético de
nueve elementos de respuesta conocida —factura exacta, número con formato distinto e
importe que no cuadra, sin documento, número dentro de un concepto, contabilizada por la
base y fuera de ventana, importe cero, honorarios con retención, alquiler cuyo documento
imprime el neto, y formación exenta contabilizada por el neto— más un documento intruso.

Y las reglas que salieron de las calibraciones: `159` no casa con `59`, `FA25/00042` sí con
`2500042`, el tercero casa por una palabra significativa sin las formas jurídicas, y una
factura que lleva el justificante escaneado detrás no se aparta como justificante.
