---
name: registro-ejecucion-gesia
description: >
  Escribe en el chat el registro de cómo ha ido la ejecución de un skill de
  auditoría de Gesia en esta misma sesión: qué se pidió, qué salió, con qué
  tropezó, qué convendría cambiar y dónde vive cada arreglo. La estructura es
  fija y anónima, para que el auditor la copie y la lleve al proyecto del
  plugin y siga la mejora continua desde ahí. Usa este skill cuando el usuario
  pida evaluar cómo ha ido el proceso, qué se podría mejorar o optimizar de la
  ejecución, qué fallos han aparecido, un registro o una retrospectiva de la
  sesión, o diga cosas como "cómo ha ido", "evalúa la ejecución", "qué se
  podría mejorar de este proceso", "apunta los fallos para el plugin" o
  "registro de ejecución".
  NO analiza al cliente ni su contabilidad: no lee el expediente ni el diario,
  y no juzga si las cifras del papel de trabajo están bien —eso lo hace el
  auditor—. No es la revisión analítica, ni el cuadro de mando del diario, ni
  ninguna de las pruebas de auditoría.
---

# Registro de ejecución (Gesia)

Cuando un skill de este plugin termina, lo que se ha aprendido sobre **el skill**
—no sobre el cliente— vive solo en la conversación, y en Cowork la conversación
se cierra y no vuelve. Este skill lo pone por escrito con una estructura fija,
para que el auditor lo copie y lo lleve al repositorio del plugin.

Precedente que da la medida de para qué sirve: de la prueba en frío de
`cancelacion-saldos` del 27/08/2026 salieron tres correcciones —campos `NN_*`
que la ayuda del MCP recomendaba y no debía, mayores sin ordenar por fecha, y
extractos temporales que nadie podía borrar— y las tres se descubrieron porque
el auditor preguntó en el momento. Lo que no se pregunta, se pierde.

---

## Reglas duras

**1. La salida es texto en el chat. No se escribe ningún fichero.** Ni en el
expediente, ni en `InformesGesia`, ni temporal. Este registro no es un papel de
trabajo: es información sobre el producto, y no pinta nada en el archivo de un
encargo firmado. El auditor lo copia del chat.

**2. Anónimo, sin excepciones.** Este texto va a viajar a otra conversación y a
acabar pegado en un repositorio, así que **no puede contener contabilidad ni
identidad del cliente**:

- el expediente se cita **ofuscado**: tres primeras letras del nombre del
  fichero, asteriscos y extensión → `Tab****.gs3`;
- **ningún importe, ningún nombre de tercero, ningún concepto contable, ningún
  número de cuenta completo.** Se habla de magnitudes y de estructura: «una
  cuenta de clientes con 508 apuntes, 497 sin parear», nunca el tercero ni su
  saldo;
- si hace falta señalar una cuenta concreta, por su grupo: «una cuenta del
  grupo 43», no la cuenta entera.

Si un hallazgo no se puede contar sin datos del cliente, se cuenta en abstracto
o no se cuenta.

**3. No se lee el expediente.** Nada de `consultar_gesia`, `consultar_diario`,
`obtener_entidad` ni `exportar_consulta`. Todo sale de lo que ya ha pasado en
esta sesión. Se admite una sola llamada, `configurar()` sin parámetros, y solo
para leer `version_mcp` — **de su respuesta no se copia la razón social del
cliente**, que viene dentro.

**4. Observado o hipótesis, y se distingue.** Cuando esto corre, la ejecución ya
terminó: no hay cronómetros, ni recuento de tokens, ni registro de llamadas.
Pedir «cómo optimizar el proceso» produce una respuesta plausible con o sin
datos, y una mejora inventada para un problema que no existe cuesta trabajo real
en el repositorio. Por eso cada punto va marcado:

- **[OBSERVADO]** — pasó, y se cita la evidencia: el aviso literal, el mensaje de
  error, la cifra que lo dice;
- **[HIPÓTESIS]** — puede ser, y se dice **qué haría falta para confirmarlo**.

Ante la duda, hipótesis. Un registro con dos hechos sólidos vale más que uno con
diez conjeturas presentadas como hallazgos.

**5. «No hubo fricciones» hay que justificarlo.** Un modelo que evalúa su propio
trabajo tiende a decir que fue bien. Si de verdad no hay nada, se dice **qué se
ha mirado** para poder afirmarlo.

**6. El tiempo: úsalo si está medido, no lo estimes.** Hay una diferencia que la
primera versión de este skill no hacía, y por su culpa se perdía información
útil: **leer las marcas de tiempo que el entorno ya deja no es estimar, es
medir.** En Cowork el registro de tareas y de llamadas a herramientas viene
fechado; de ahí sale cuánto tardó el conjunto y qué paso se llevó la mayor
parte, y eso hay que contarlo diciendo de dónde sale el dato.

Lo que no vale es poner un tiempo a ojo cuando no hay nada que leer: entonces el
bloque dice «no se midió». Y si las marcas son de grano grueso, se dice así —
«unos cuatro minutos, según el registro de tareas»— en vez de dar una precisión
que no se tiene.

Lo mismo con el volumen, que casi siempre sí consta: apuntes procesados, cuentas,
filas exportadas. Eso da la medida de si el tiempo fue razonable o no.

---

## Qué se busca antes de escribir

Repasa la sesión y recoge, en este orden:

1. **Identificación.** Qué skill se ejecutó y su versión si consta; versión del
   MCP; expediente ofuscado. La versión importa más de lo que parece: el
   27/08/2026 convivían la copia de Cowork de un skill y la publicada, y no se
   sabía cuál se estaba ejecutando.
2. **Qué pidió el usuario** y con cuántas vueltas se entendió. Si hubo que
   preguntarle algo que el `SKILL.md` podría haber resuelto solo, eso es una
   fricción.
3. **Qué devolvió el verificador de contrato**: si abortó, qué avisos dio, y si
   esos avisos se trasladaron al usuario o se quedaron por el camino.
4. **Errores y reintentos.** Cada consulta que falló y por qué: campo que no
   existía, tipo que no coincidía, comodín equivocado, tabla mal nombrada. Los
   errores literales son la mejor materia prima de este registro.
5. **Correcciones del usuario.** Todo lo que el auditor tuvo que rectificar a
   mano es, por definición, algo que el skill no hizo bien.
6. **Residuos.** Ficheros que quedaron sin borrar, y si se avisó de ellos.
7. **Lo que funcionó**, breve: sirve para no romperlo en la siguiente iteración.

Para cada fricción, decide **dónde vive el arreglo**, que es lo que convierte
esto en trabajo aprovechable:

| Dónde | Cuándo |
|---|---|
| `SKILL.md` | el procedimiento estaba mal explicado, incompleto o ambiguo |
| script | el cálculo o el entregable fallan, o les falta algo |
| MCP | el dato no se puede leer, o la ayuda embebida induce a error |
| nada | pasó, pero es del entorno o del expediente y no hay nada que cambiar |

---

## La plantilla

Se escribe **en el chat**, tal cual, rellenando los huecos y quitando los
bloques que no apliquen. Sin adornos y sin resumen ejecutivo: quien lo lee es un
desarrollador con el repositorio abierto.

```markdown
## Registro de ejecución

- **Skill:** <nombre> <versión si consta>
- **MCP:** <version_mcp>
- **Expediente:** <Tab****.gs3>
- **Fecha:** <dd/mm/aaaa>
- **Entorno:** <Cowork | Claude Code>

### Qué se pidió y qué salió
<una o dos líneas: la petición, y el entregable que se produjo o por qué no>

### Contrato
<abortó / pasó con N avisos / pasó limpio. Los avisos, literales, y si se
trasladaron al usuario>

### Fricciones
1. **[OBSERVADO]** <qué pasó>
   - Evidencia: <mensaje o cifra literal, sin datos del cliente>
   - Arreglo: <SKILL.md | script | MCP | nada> — <qué habría que cambiar>
2. **[HIPÓTESIS]** <qué podría estar pasando>
   - Para confirmarlo haría falta: <qué medir o probar>
   - Arreglo: <dónde viviría, si se confirma>

<si no hay ninguna: «Ninguna. Se ha revisado: contrato, errores de consulta,
correcciones del usuario, residuos y trasvase de avisos.»>

### Rendimiento
<duración del conjunto y el paso que se llevó la mayor parte, leídos de las
marcas de tiempo del entorno, diciendo de dónde salen. Con el volumen al lado:
apuntes, cuentas, filas exportadas. Si el entorno no deja marcas: «No se midió:
este entorno no dejó marcas de tiempo.»>

### Lo que funcionó
<breve, para no romperlo después>

### Para el repositorio
<los hallazgos accionables, redactados como para pegar en mejoras-mcp.md o en
el DISENO.md del skill: qué se cambia, dónde y por qué>
```

---

## Lo que este skill no hace

- **No escribe ficheros.** Ninguno, en ningún sitio.
- **No lee el expediente ni el diario.**
- **No juzga si el papel de trabajo está bien.** Si las cifras cuadran lo dice
  el auditor, que es quien firma.
- **No arregla nada.** Propone; el arreglo se hace en el repositorio del plugin.
- **No mide tiempos que nadie midió**, ni estima cuánto costó en tokens.
- **No evalúa al cliente ni su contabilidad.** Si el usuario quiere eso, es otro
  skill.

## Degradación

| Situación | Qué sale |
|---|---|
| No se ha ejecutado ningún skill en la sesión | **para** y lo dice: no hay nada que registrar. No se inventa una ejecución |
| La conversación viene resumida y falta detalle | sigue, y marca como hipótesis lo que no puede citar con evidencia |
| No consta la versión del skill | se dice «no consta» — nunca se supone |
| El entorno deja marcas de tiempo (Cowork) | se usan: son medición, no estimación. Se dice de dónde salen |
| El entorno no deja marcas de tiempo | el bloque dice «no se midió». **Nunca un tiempo a ojo** |
| Solo hay una fricción, o ninguna | se entrega igual: un registro corto y honesto es el resultado correcto |
