---
name: estados-financieros-gesia
description: >
  Revisión de los estados financieros de un expediente de auditoría de Gesia.
  Produce el papel de trabajo en Excel con el balance y la cuenta de pérdidas y
  ganancias comparados de los ejercicios cargados, y la conciliación del ejercicio
  corriente: del saldo que presenta el cliente al saldo auditado, pasando por los
  ajustes y las reclasificaciones, epígrafe a epígrafe y cuenta a cuenta.
  Usa este skill cuando el usuario pida revisar o cuadrar los estados financieros,
  el balance o la cuenta de resultados, ver los ajustes de auditoría por epígrafe,
  comparar lo presentado por el cliente con lo auditado, o diga cosas como
  "saca el balance comparado", "revisa las cifras del expediente",
  "qué epígrafes han cambiado con los ajustes", "cuadra el balance",
  "revisa el balance y la PyG del expediente" o "papel de estados financieros".
  Hace también la revisión del PATRIMONIO NETO: de la apertura auditada al cierre
  auditado, componente a componente. Úsalo si piden el ECPN, el estado de cambios
  en el patrimonio neto, el movimiento de reservas o de subvenciones, o dicen
  "cómo ha variado el patrimonio neto" o "de dónde sale el patrimonio neto".
  Y la del ESTADO DE FLUJOS DE EFECTIVO, leyendo el módulo EFE del expediente:
  el estado que hay, sus ajustes, cuáles están aprobados y si todo cuadra. Úsalo
  si piden el EFE, el estado de flujos, los flujos de explotación, de inversión o
  de financiación, o "revisa el cash flow del expediente".
  Sabe además PROPONER el importe de los ajustes del estado de flujos a partir del
  catálogo de plantillas del propio expediente. Úsalo si piden ayuda para montar
  el EFE, calcular los ajustes de flujos, o dicen "qué ajustes faltan" o "de dónde
  saco los importes del cuadro".
  NO formula las cuentas anuales: el auditor no las formula, las revisa. NO es el
  cuestionario de la memoria, ni el cuadro de mando del diario, ni la prueba de
  continuidad de saldos de apertura. NO calcula el estado de flujos ni propone
  ajustes a él: lo lee del expediente y lo cuadra. Y NO reproduce el ECPN oficial:
  reconcilia el patrimonio neto, no reparte su variación entre resultado,
  operaciones con socios y otras variaciones, que es del auditor.
  SI EL USUARIO DICE SOLO «CUENTAS ANUALES», NO LANCES NADA: son el conjunto
  entero —balance, resultados, patrimonio neto, flujos y memoria— y hay DOS
  skills que hacen partes distintas. Este trabaja con LAS CIFRAS que ya están
  cargadas en el expediente y no necesita ningún PDF; el cuestionario de cuentas
  anuales revisa EL CONTENIDO DE LA MEMORIA a partir del PDF del cliente.
  Pregunta cuál de los dos quiere antes de tocar nada.
  Requiere Gesia con el servidor API arrancado y un expediente con las cifras
  cargadas en balance y pérdidas y ganancias.
---

# Revisión de estados financieros (Gesia)

Enseña de dónde sale cada epígrafe de las cuentas anuales: qué presentó el cliente, qué
ajustes y reclasificaciones se le hicieron, y qué quedó auditado. Y lo cuadra.

Los ficheros se escriben en `<expediente>\InformesGesia\EstadosFinancieros\` y **nunca se
publican** en ninguna URL: son la contabilidad de un cliente auditado.

---

## Antes de empezar: ¿te han pedido esto, o la memoria?

**«Cuentas anuales» no es este skill, ni es el otro: son las dos cosas.** El conjunto lo
forman el balance, la cuenta de resultados, el estado de cambios en el patrimonio neto, el de
flujos de efectivo y la memoria. Aquí se revisan **las cifras** que el expediente ya tiene
cargadas; el contenido de la memoria lo revisa `cuestionario-cuentas-anuales`, que necesita el
PDF del cliente y produce otro papel distinto.

Si la petición no distingue —«revisa las cuentas anuales», «mira las cuentas del cliente»—,
**pregunta antes de exportar nada** y ofrece las dos. Cuesta una línea, y equivocarse cuesta
un papel que no era el que hacía falta. La pista más fiable: **si el auditor te ha dado o
mencionado un PDF, casi seguro quiere la memoria**.

---

## Cuatro reglas que gobiernan todo

**1. Esto revisa, no formula.** El auditor no formula las cuentas de su cliente. El papel
contrasta lo que hay en el expediente y señala; no propone cifras ni «completa» estados. Si
el usuario pide formular las cuentas anuales, dilo y para.

**2. Solo suman las cuentas asignadas a un epígrafe.** El plan repite la misma cuenta a uno,
dos, tres y cuatro dígitos. Sumarlas todas cuenta el dinero dos o tres veces. La marca es
`AsignadaCCAA`, y en un expediente real son 535 de 4.569 cuentas. El cuadro de mando en Excel
que ya usa la firma hace exactamente lo mismo y la llama `NivelEEFF`.

**3. Solo suman las líneas que admiten cuentas.** `CuentasAsignables` distingue las líneas de
detalle de los totales y subtotales del modelo oficial. Sumar los subtotales duplica igual.

**4. El signo de presentación no es el del dato crudo.** En el balance el pasivo viene con el
signo cambiado; en pérdidas y ganancias la regla de Gesia es epígrafes en magnitud y
subtotales invertidos. El script la replica **tal cual**, sin «mejorarla», para que las cifras
coincidan con las que el auditor ve en la revisión analítica del programa. Si algún día no
coinciden, es un fallo del skill, no del programa.

---

## Dónde están los scripts

Al cargarse, el runtime indica el **directorio base del skill**. Las rutas `scripts/…` son
relativas a él, no al directorio de trabajo:

```bash
SKILL="<directorio base indicado al cargar el skill>"
TRABAJO="$(pwd)/trabajo" && mkdir -p "$TRABAJO"
```

Los scripts no tocan el `.gs3`: leen lo que `exportar_consulta` haya dejado en disco. El
expediente lleva contraseña y **solo lo abre el servidor API**.

**Si no puedes ejecutar los scripts en el equipo del auditor, para y díselo.** No muevas las
exportaciones a una carpeta desde la que se suban a otro sitio: `cuentas.json` lleva el nombre
de todas las cuentas del plan, y las de los grupos 40, 41 y 43 se llaman como el proveedor o
el cliente. Ese fichero está en `<TEMP>` precisamente para que no salga de ahí. Dile al
auditor qué ha fallado y que lo reporte con «cómo ha ido»; es un caso que hay que medir, no
rodear.

---

## Secuencia

### Paso 1 — Expediente

`configurar()` sin parámetros para ver el estado. Si no hay expediente, pide la ruta del
`.gs3`. Si responde que el servidor API no contesta, **llama a `arrancar_api`**: lo levanta en
el equipo del auditor y sigues. No le pidas a él que lo arranque a mano.

Quédate con el nombre del cliente y con la correspondencia de ejercicios:

```
exportar_consulta(sql = "SELECT CodigoAuditoria, Año FROM Auditorias",
                  ruta = "<TEMP>/gesia-eeff/ejercicios.json")
```

**`CodigoAuditoria` es un orden interno, no un año.** El 1 es el ejercicio más reciente. Nunca
etiquetes una columna con un año sin haber leído esta tabla.

### Paso 2 — La estructura de los dos estados

Una sola exportación con las dos tablas unidas. La columna `Estado` es la que luego las
separa en el papel:

```
exportar_consulta(
  sql = "SELECT CodigoCCAA, 'Balance' AS Estado,
                IIf(CodigoClase='A','ACTIVO','PASIVO') AS Activo_Pasivo, CodigoClase,
                CodigoAMostrar, Concepto, CuentasAsignables, CodigoSeccion, CodigoEpigrafe,
                CodigoDesglose, CodigoSubDesglose, Null AS CodigoOrdenI,
                SaldoAuditoria1, SaldoAuditoria2, SaldoAuditoria3, SaldoAuditoria4,
                SaldoAuditoria5
         FROM EstructuraBalance
         UNION ALL
         SELECT CodigoCCAA, 'PyG', '', CodigoClase, CodigoAMostrar, ConceptoIngresos,
                CuentasAsignables, CodigoSeccion, CodigoEpigrafe, CodigoDesglose,
                CodigoSubDesglose, CodigoOrdenI, SaldoAuditoria1, SaldoAuditoria2,
                SaldoAuditoria3, SaldoAuditoria4, SaldoAuditoria5
         FROM EstructuraPyG WHERE CodigoClase IN ('I','T','ST')",
  ruta = "<TEMP>/gesia-eeff/estructura.json")
```

Son del orden de 175 filas. **No las abras**: el script las lee tal cual.

`CodigoOrdenI` es el orden oficial de la cuenta de resultados, y es el mismo por el que ordena
el cuadro de mando en Excel de la firma. El balance no tiene columna de orden —va por sección,
epígrafe y desglose—, por eso ahí se pide `Null`. Sin `CodigoOrdenI` la PyG sale desordenada:
las cifras son correctas y las líneas están cambiadas de sitio, que es la peor de las dos
formas de estar mal.

### Paso 3 — El plan de cuentas con su epígrafe y su saldo

Aquí está la cadena de la revisión: lo del cliente, los ajustes, las reclasificaciones y lo
auditado, por cuenta.

```
exportar_consulta(
  sql = "SELECT ca.Cuenta, c.Nombre, ca.Digitos, ca.CodigoCCAA, ca.AsignadaCCAA,
                ca.SaldoAuditoria, c.SaldoAnterior, c.SaldoCliente, c.SaldoAj, c.SaldoRec
         FROM CuentasAuditorias AS ca INNER JOIN Cuentas AS c ON ca.Cuenta = c.Cuenta
         WHERE ca.CodigoAuditoria = '1'",
  ruta = "<TEMP>/gesia-eeff/cuentas.json")
```

El `'1'` es el ejercicio corriente y va **entrecomillado**: el campo es texto, y sin comillas
Access responde que no coinciden los tipos de datos.

Son varios miles de filas y pesa poco, porque va a fichero y no a tu contexto.

`SaldoAnterior` es **la apertura del ejercicio, y es la auditada**: medido en un expediente
real, coincide con el `SaldoAuditoria` del ejercicio anterior en las 535 cuentas asignadas, sin
una excepción. Sin esa columna no hay papel de patrimonio neto.

### Paso 4 — Verificar el contrato (puede abortar)

```bash
python "$SKILL/scripts/verificar_contrato.py" \
  --estructura "<TEMP>/gesia-eeff/estructura.json" \
  --cuentas    "<TEMP>/gesia-eeff/cuentas.json" \
  --ejercicios "<TEMP>/gesia-eeff/ejercicios.json"
```

Salida `2` → **no se genera nada**. Lee el motivo y trasládalo. Aborta si el balance
descuadra, si no se sabe qué ejercicio es cada columna, si ninguna cuenta está asignada a un
epígrafe o si los epígrafes de las cuentas no existen en la estructura.

Salida `1` → se puede seguir, pero **los avisos van al auditor en la entrega**.

Salida `0` → todo encaja.

### Paso 5 — El papel de trabajo

```bash
python "$SKILL/scripts/generar_papel.py" \
  --estructura "<TEMP>/gesia-eeff/estructura.json" \
  --cuentas    "<TEMP>/gesia-eeff/cuentas.json" \
  --ejercicios "<TEMP>/gesia-eeff/ejercicios.json" \
  --cliente    "<razón social del expediente>" \
  --ejercicio  "<año del ejercicio corriente>" \
  --salida     "<expediente>/InformesGesia/EstadosFinancieros/Estados Financieros <CLIENTE> <EJERCICIO>.xlsx"
```

Cinco hojas: **Balance**, **PyG**, **Conciliacion**, **Ajustes** y **Comprobaciones**.

Si el script termina con salida `1`, imprime una sección **«PARA CONTAR AL ENTREGAR (tal cual,
sin resumir)»**. Esas líneas van al auditor **literales, todas**, no resumidas con tus
palabras.

### Paso 5 bis — El papel de patrimonio neto

**Siempre.** Usa **los mismos tres ficheros** del paso 3: no cuesta ni una exportación más, así
que no hay motivo para dejarlo a que al auditor se le ocurra pedirlo.

```bash
python "$SKILL/scripts/generar_ecpn.py"   --estructura "<TEMP>/gesia-eeff/estructura.json"   --cuentas    "<TEMP>/gesia-eeff/cuentas.json"   --ejercicios "<TEMP>/gesia-eeff/ejercicios.json"   --cliente    "<razón social del expediente>"   --ejercicio  "<año del ejercicio corriente>"   --salida     "<expediente>/InformesGesia/EstadosFinancieros/Patrimonio Neto <CLIENTE> <EJERCICIO>.xlsx"
```

Cuatro hojas: **PatrimonioNeto**, **Movimiento**, **Detalle** y **Comprobaciones**.

**Gesia no tiene módulo de ECPN.** Está comprobado sobre el ejecutable: los nombres de tabla
que aparecen en su propio SQL son los del balance, la PyG, la PyG analítica, las cuentas
anuales antiguas y las tres del estado de flujos. De patrimonio neto no hay tabla ni menú. Por
eso este papel **reconcilia** cada componente —de la apertura auditada al cierre auditado,
pasando por el movimiento del cliente, los ajustes y las reclasificaciones— y **no reparte** la
variación entre resultado, operaciones con socios y otras variaciones. Ese reparto lo hace
quien firma.

La clasificación por componentes tampoco se inventa: es la del propio Gesia, la del epígrafe
del balance al que está asignada cada cuenta.

El semáforo de este papel tiene **tres** estados, no dos. «A TENER EN CUENTA» no es un
descuadre: es algo que el auditor necesita saber, y sale igualmente en la sección de
«PARA CONTAR AL ENTREGAR». El caso típico: el cliente no usa los grupos 8 y 9, así que el
estado de ingresos y gastos reconocidos no se puede sacar de la contabilidad y hay que
construirlo con él. Pasa en los dos expedientes de calibración.

### Paso 5 ter — El papel de flujos de efectivo

**Mira siempre si hay estado que revisar; otra cosa es que lo haya.** No esperes a que te lo
pidan: lo que decide es el dato, y comprobarlo cuesta una exportación.

**La señal son los ajustes APROBADOS, no que el cuadro tenga cifras.** Gesia rellena las
variaciones de balance él solo en cuanto hay dos ejercicios cargados, así que un cuadro con
importes no significa que nadie haya trabajado el estado. Medido en un expediente terminado de
modelo reducido: 159 líneas con importe y cero ajustes aprobados, porque formulando abreviado
no está obligado a presentarlo y el auditor ni lo empezó. Ahí **no se hace el papel**: se dice
en una línea al entregar y se acabó.

Así que primero el catálogo, que es la exportación que responde a la pregunta:

```
exportar_consulta(
  sql = "SELECT CodigoAuditoria, CodigoOrden, CodigoLinea, Descripcion, Origen,
                Aplicacion, OrigenAjuste, AplicacionAjuste, OrigenAjustado,
                AplicacionAjustada, SaldoAuditoriaAnterior, SaldoAuditoria
         FROM CuadroFinanciacion WHERE CodigoAuditoria = '1'",
  ruta = "<TEMP>/gesia-eeff/cuadro.json")

exportar_consulta(
  sql = "SELECT a.NumeroAsientoOA, a.Fecha, a.Descripcion,
                a.GeneracionFondos AS Aprobado, p.ApunteOA, p.Cuenta, p.Concepto,
                p.Contrapartida, p.Origen, p.Aplicacion
         FROM AsientosOA AS a
         LEFT JOIN ApuntesOA AS p ON a.NumeroAsientoOA = p.NumeroAsientoOA",
  ruta = "<TEMP>/gesia-eeff/ajustes_efe.json")
```

El `LEFT JOIN` es a propósito: así vienen también las plantillas del catálogo que nadie ha
usado, y el papel puede decir cuántas hay frente a cuántas están aprobadas.

**Cuenta los aprobados —`Aprobado` a `True`— antes de seguir**, porque es lo que decide qué
estás entregando. Si no hay ninguno, el expediente **no tiene el estado de flujos hecho**:
Gesia rellena el cuadro solo, comparando saldos de balance, y cuadra perfectamente consigo
mismo sin un solo ajuste del auditor.

**Genera el papel igual** —enseña precisamente eso, que está sin hacer— y al entregar **lleva
el aviso por delante**, antes que ninguna cifra: sin ajustes aprobados, eso no es un estado de
flujos, y el verde de las demás comprobaciones no dice que lo esté. El script lo imprime en
«PARA CONTAR AL ENTREGAR»: cópialo tal cual y **no lo resumas en «cuadra»**.

**Y sigue con la propuesta, sin esperar a que te la pidan** (paso 5 quater). Es el caso
normal, no la excepción: de nueve expedientes medidos el 25/09/2026, **ocho** tienen el
catálogo del máster sin tocar y cero ajustes aprobados. Un papel que solo diga «esto no está
hecho» no le sirve de nada al auditor; cuatro ajustes calculados son cuatro que no tiene que
calcular él.

```bash
python "$SKILL/scripts/generar_efe.py" \
  --cuadro     "<TEMP>/gesia-eeff/cuadro.json" \
  --ajustes    "<TEMP>/gesia-eeff/ajustes_efe.json" \
  --estructura "<TEMP>/gesia-eeff/estructura.json" \
  --ejercicios "<TEMP>/gesia-eeff/ejercicios.json" \
  --cliente    "<razón social del expediente>" \
  --ejercicio  "<año del ejercicio corriente>" \
  --salida     "<expediente>/InformesGesia/EstadosFinancieros/Flujos de Efectivo <CLIENTE> <EJERCICIO>.xlsx"
```

Cuatro hojas: **FlujosEfectivo**, **Ajustes**, **Apuntes** y **Comprobaciones**.

**Cuatro cosas de este módulo que no se adivinan**, todas medidas y todas vigiladas por el
papel:

1. **La casilla «Aprobado» es el campo `GeneracionFondos`**, que no significa lo que su nombre
   dice. Solo cuentan los aprobados, igual que en los ajustes de auditoría. Comprobado por
   aritmética: los ajustes del cuadro son exactamente la suma de los apuntes aprobados en las
   159 líneas, sin una excepción.
2. **Un cuadro con cifras no quiere decir que el estado esté hecho.** Gesia rellena las
   variaciones de balance él solo en cuanto hay dos ejercicios cargados. Sin ajustes aprobados
   eso no es un estado de flujos: es la aritmética del programa sin el criterio del auditor, y
   cuadra consigo mismo perfectamente. Pasa en uno de los dos expedientes de calibración, con
   159 líneas con importe y cero ajustes aprobados. El papel lo dice en ámbar, arriba del todo.
3. **`Cuenta` y `Contrapartida` de un apunte NO son cuentas contables**: son líneas del propio
   estado. El ajuste es partida doble entre líneas del cuadro, y sus cobros tienen que igualar
   a sus pagos.
4. **Si la tabla está vacía, no es un error.** Los modelos de pymes no llevan estado de flujos
   porque el plan no se lo exige: se dice y se para, sin ofrecer nada.

Y el cuadre que vale por todos: la suma de los flujos de las actividades es la variación de la
tesorería, y esa variación es la del epígrafe de efectivo del balance. Medido en el expediente
con el estado hecho: 685.252,52 € por los tres caminos.

### Paso 5 quater — Proponer los ajustes del estado de flujos

**Automáticamente cuando el expediente no tiene ningún ajuste aprobado**, y también si el
auditor lo pide. Siempre **después** del papel de flujos, porque ahí se ve qué falta.

**Lo que sale es un BORRADOR, y así hay que entregarlo.** Medido contra el único expediente
que tiene el estado terminado: de los diez ajustes que aprobó el auditor, estas reglas
aciertan **cuatro** —y no fallan ninguna— pero cubren el **32 %** del importe movido. Los seis
que faltan son los grandes: impuesto de sociedades, ventas de inmovilizado, provisiones,
reclasificación de créditos y las dos amortizaciones de deuda; solo la de créditos movía más
del doble que todo lo propuesto junto.

Así que al entregar, **por delante de cualquier cifra**, tres cosas:

1. **Qué se propone y con qué regla**, cada una con su importe.
2. **Qué falta, por nombre**: las plantillas del catálogo sin propuesta salen en la hoja
   `Catalogo` con el criterio que escribió quien montó el máster. Eso es lo que el auditor
   tiene que calcular, y decírselo es la mitad del valor del papel.
3. **Que no va a cuadrar, y que no cuadra porque está a medias**, no porque haya un error en
   las cuentas del cliente. Si esto no se dice, el descuadre se atribuye al cliente.
Necesita el catálogo de plantillas **con su criterio**, que es una exportación más:

```
exportar_consulta(
  sql = "SELECT a.NumeroAsientoOA, a.Descripcion, a.GeneracionFondos AS Aprobado,
                a.Observaciones, p.ApunteOA, p.Cuenta, p.Concepto, p.Contrapartida,
                p.Origen, p.Aplicacion
         FROM AsientosOA AS a
         LEFT JOIN ApuntesOA AS p ON a.NumeroAsientoOA = p.NumeroAsientoOA
         ORDER BY a.NumeroAsientoOA, p.ApunteOA",
  ruta = "<TEMP>/gesia-eeff/catalogo.json")
```

`Observaciones` es el criterio de cada plantilla, escrito por quien montó el máster: dice de
qué cuentas sale el importe y qué mirar. Es doctrina de la casa y el papel lo reproduce tal
cual, sin resumirlo.

```bash
python "$SKILL/scripts/proponer_efe.py" \
  --catalogo "<TEMP>/gesia-eeff/catalogo.json" \
  --cuentas  "<TEMP>/gesia-eeff/cuentas.json" \
  --cuadro   "<TEMP>/gesia-eeff/cuadro.json" \
  --cliente  "<razón social del expediente>" \
  --ejercicio "<año del ejercicio corriente>" \
  --salida   "<expediente>/InformesGesia/EstadosFinancieros/Propuesta EFE <CLIENTE> <EJERCICIO>.xlsx"
```

Tres hojas: **Propuestas**, **Catalogo** y **Comprobaciones**.

**Esto no escribe nada en Gesia**, que el MCP solo lee. Es una propuesta en papel, y al
teclearla va **siempre como ajuste NO APROBADO y con «Asistente IA:» al principio de la
descripción**, para que no se confunda nunca con el trabajo del auditor. El papel ya la
escribe así.

**Solo hay cuatro reglas, y no salen de leer el criterio: salen de reproducir lo que un
auditor puso de verdad.** En el expediente que tiene el estado hecho, las cuatro dan el
importe exacto, y la de amortización acierta apunte por apunte:

| Regla | De dónde sale | Comprobado |
|---|---|---|
| Distribución del resultado (beneficio) | apertura de la 129, repartida por el movimiento de reservas, remanente y pérdidas anteriores; el resto, dividendo | 848.404,89 |
| Amortización del ejercicio | 680, 681 y 682, cada una con su amortización acumulada | 140.498,55 |
| Gastos financieros | saldo de la 66 | 220.875,62 |
| Ingresos financieros | saldo de la 76 | 496.068,23 |

**Lo que NO se propone importa tanto como lo que sí**, y el papel lo dice: el impuesto de
sociedades (el auditor puso 315.413,38 y el gasto de la 630 son 240.077,05, porque la línea es
de cobros y pagos y no del gasto devengado), las provisiones (fueron por la 529, no por la 14)
y la distribución de pérdidas, que se escribió por simetría y al probarla colaba el movimiento
de las subvenciones como si fuera reparto del resultado. Cuadraba, y habría pasado por buena.

Al entregar, di siempre estas dos cosas: **cuántas plantillas del catálogo llevan propuesta y
cuántas no**, y que **donde el auditor ya puso el ajuste manda lo suyo**; si la propuesta no
coincide con lo que hay en Gesia, eso es algo que entender, no algo que corregir.

### Paso 6 — Entregar

**Enumera los cuatro papeles, los hechos y los no hechos, con el motivo.** Es la parte que más
fácil se queda a medias: si solo cuentas el primero, el auditor da por terminado el trabajo y
no sabe que faltan tres.

| Papel | Cuándo sale | Si no sale, qué decir |
|---|---|---|
| Estados financieros | siempre | — |
| Patrimonio neto | siempre | — |
| Flujos de efectivo | si hay ajustes aprobados en el módulo EFE | «el expediente no tiene el estado de flujos hecho: el cuadro está sin ajustes aprobados», o que es un modelo de pymes y no lo lleva |
| Propuesta de ajustes del EFE | solo si el auditor la pide | nada: no se ofrece sola |

Y de cada papel que salga, en pocas líneas:

- dónde está el fichero, con la ruta completa
- qué ejercicios lleva el comparativo
- cuántas cuentas tienen ajuste o reclasificación y cuántos epígrafes mueven
- si todas las comprobaciones cuadran, o cuáles no

Y una advertencia que va siempre: **el papel es una lectura del expediente, no una opinión.**
Que los epígrafes cuadren no dice que las cuentas sean correctas, dice que el expediente es
internamente consistente.

---

## Lo que este skill no hace

- **No formula las cuentas anuales.** Revisa las que hay en el expediente.
- **No hace el estado de flujos de efectivo.** Gesia tiene su propio módulo, con su catálogo
  de ajustes y su casilla de aprobado; está documentado en `docs/esquema-efe.md` y es una fase
  posterior.
- **No formula el ECPN oficial.** Reconcilia el patrimonio neto componente a componente;
  repartir la variación entre resultado, operaciones con socios y otras variaciones es una
  clasificación del auditor.
- **No hace el estado de ingresos y gastos reconocidos** cuando el cliente no usa los grupos 8
  y 9, que es lo normal en una pyme: sin esas cuentas el desglose no está en la contabilidad.
- **No calcula el estado de flujos de efectivo.** Lo lee del módulo EFE del expediente y lo
  cuadra. Gesia hace la aritmética y deja el juicio al auditor; ese reparto es del producto y
  no hay que competir con lo que ya hace bien.
- **No decide los ajustes del estado de flujos: propone el importe de cuatro**, y solo de
  aquellas cuya regla se pudo contrastar contra un expediente real. Las demás las rellena el
  auditor con el criterio que trae cada plantilla.
- **No escribe la propuesta en Gesia.** El MCP solo lee. Cuando el API tenga escritura,
  entrará igual: no aprobada y firmada como Asistente IA.
- **No hace la memoria.**
- **No compara con el ejercicio anterior más allá de lo que el expediente guarda.** El saldo
  del cliente solo existe del ejercicio corriente. Si el auditor quiere la conciliación de un
  año anterior, hace falta el `.gs3` de ese año: se le pide y se pasa con
  `configurar(gs3_anterior=…)`.
- **No escribe nada en Gesia.** El MCP solo lee.
- **No proyecta, no valora y no opina sobre la empresa.**

---

## Degradación

| Situación | Qué hace |
|---|---|
| El servidor API no responde | llama a `arrancar_api` y repite; solo si eso falla, se lo dice al auditor |
| El expediente no tiene cifras cargadas en ningún ejercicio | **para**: no hay nada que revisar |
| El balance descuadra en algún ejercicio | **para**: con un balance descuadrado no se emite papel, y se dice en qué ejercicio y por cuánto |
| Los epígrafes de las cuentas no existen en la estructura | **para**: el mapeo no es de este modelo de cuentas |
| El expediente no trae saldo de cliente | sigue: el papel compara ejercicios pero no lo presentado frente a lo auditado, y se avisa |
| Solo hay un ejercicio con cifras | sigue: sin columna de variación |
| No hay líneas de pérdidas y ganancias | sigue: el papel sale solo con el balance, y se dice |
| El expediente no tiene ajustes ni reclasificaciones | sigue: la hoja de ajustes lo dice expresamente, que es un resultado, no un fallo |
| Un epígrafe no cuadra con la suma de sus cuentas | sigue y lo marca en Comprobaciones: esa línea no se desglosa por cuenta |
| El plan exportado no trae `SaldoAnterior` | **para el papel de patrimonio neto**: sin la apertura no hay estado de cambios. El de estados financieros sale igual |
| La apertura no es el patrimonio neto que cerró el ejercicio anterior | sigue y lo marca en rojo: el ejercicio abre con un patrimonio distinto del que cerró, y eso se explica o se investiga |
| El cliente no usa los grupos 8 y 9 | sigue: lo dice en Comprobaciones como «A tener en cuenta», y avisa de que el estado de ingresos y gastos reconocidos hay que construirlo con el auditor |
| `CuadroFinanciacion` viene vacía | **para el papel de flujos**: es un modelo de pymes y no lleva estado de flujos. Se dice y no se ofrece nada más |
| El cuadro está a cero en todas sus líneas | **para**: el estado no se ha hecho |
| El cuadro tiene cifras pero ningún ajuste aprobado | sigue y lo marca en ámbar arriba del todo: es la aritmética de Gesia sin el criterio del auditor, y cuadra igual |
| Un ajuste aprobado descuadra (cobros ≠ pagos) | sigue y lo marca en rojo: el módulo tiene un «Descuadre» que debería estar a cero |
| Ninguna plantilla del catálogo encaja con una regla verificada | sigue: el papel sale con la hoja Catalogo, que ya es útil, y lo dice |
| La propuesta no coincide con un ajuste que el auditor ya aprobó | sigue y lo marca en rojo: manda lo del auditor, y la diferencia se entiende antes de tocar nada |
| El resultado del ejercicio anterior fue pérdida | no se propone la distribución: esa variante no está calibrada contra ningún expediente |

---

## Comprobar que el skill funciona

```bash
python "$SKILL/scripts/probar_eeff.py"
```

Comprobaciones puras sobre los cuadres, los signos de presentación y la agregación por
epígrafe, sin tocar ningún expediente. Calibrado contra dos expedientes reales terminados, uno
de modelo normal y otro de reducido: en ambos el balance cuadra en los cinco ejercicios y la
cadena del saldo cuadra en todas las cuentas.
