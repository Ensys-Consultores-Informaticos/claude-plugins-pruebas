---
name: investigacion-entidad-gesia
description: >
  Investiga en fuentes públicas de internet a la entidad auditada de un
  expediente de Gesia: información societaria (BORME), contratos públicos
  (PLACE), subvenciones (BDNS), jurisprudencia (CENDOJ), sanciones y prensa.
  Lanza tres agentes investigadores en paralelo y produce el papel de trabajo
  en Word con cada hecho citado a su fuente, más la evidencia en JSON.
  Usa este skill cuando el usuario pida investigar al cliente, buscar
  información pública o externa de la entidad, una due diligence, el
  conocimiento de la entidad y su entorno por fuentes externas, o diga cosas
  como "investiga a este cliente", "qué se sabe de esta empresa", "busca al
  cliente en internet", "mira el BORME", "tiene contratos públicos o
  subvenciones", "busca noticias o sentencias del cliente".
  NO es la identificación de riesgos del expediente (eso usa las cifras de
  Gesia), ni el cuadro de mando del diario, ni la revisión de la memoria.
  Requiere acceso a internet; el expediente de Gesia es opcional (aporta
  denominación y CIF solos).
---

# Investigación de la entidad auditada en fuentes públicas

Convierte la denominación y el CIF del cliente en un informe de due diligence:
hechos societarios, vínculos con el sector público, riesgos legales y
reputacionales — **cada uno con su fuente, y los huecos declarados**.

Es el primer skill del plugin que usa **agentes**: tres investigadores en
paralelo (`agents/` del plugin), cada uno con su contrato JSON. El análisis y la
redacción NO se delegan: son tuyos, en el contexto principal, donde el usuario
puede corregirlos.

El informe y su evidencia van a `<expediente>\InformesGesia\InvestigacionEntidad\`
y **nunca se publican** en ninguna URL, ni como Artifact: forman parte del
archivo de un encargo.

---

## Reglas que gobiernan todo

**1. Hacia internet solo viajan la denominación y el CIF.** Ninguna cifra, saldo
ni dato interno del expediente entra jamás en una búsqueda web ni en el prompt de
un agente. Los agentes no tienen acceso al MCP de Gesia, y así debe seguir.

**2. Cero hechos sin fuente.** Todo lo que llega de los agentes trae fuente, URL
y fecha de consulta; lo que no la traiga no entra en el informe. Tú tampoco
añades hechos: tu papel en el análisis es cruzar los que hay.

**3. La ausencia de información es un resultado, no un fallo.** La parte
gratuita del Registro Mercantil es escasa y muchas pymes no dejan rastro en
PLACE ni en CENDOJ. Un informe lleno de ○ con las fuentes documentadas es un
papel de trabajo válido; un informe que rellena esos huecos por plausibilidad es
un papel falso.

**4. Describir, no dictaminar.** Los cruces del análisis se presentan como
elementos a contrastar, con su incertidumbre, nunca como conclusiones. Concluir
es del auditor, que es quien firma. Y sobre las personas (administradores,
apoderados): cargo y fechas publicados, ni una valoración.

**5. La evidencia JSON se archiva junto al informe.** Las fuentes web cambian y
la búsqueda de hoy no es reproducible mañana: lo que hace defendible el papel es
conservar lo que los agentes devolvieron, tal cual, con su fecha de consulta.

---

## Secuencia

### Paso 1 — Identificar a la entidad

Con expediente de Gesia (el caso normal):

```
configurar()
contexto_expediente()
```

De ahí salen la razón social y la fecha de cierre. **El CIF no está en el
contrato de datos documentado de `DatosAuditoria`**, así que se comprueba en
ejecución:

```sql
SELECT CIF FROM DatosAuditoria
```

y si falla, `SELECT NIF FROM DatosAuditoria`. **Una columna por consulta, nunca
las dos juntas.** Tres casos, y los tres pasan en expedientes reales:

1. **Error «No se han especificado valores para algunos de los parámetros
   requeridos»** → la columna no existe: Access toma el nombre por un parámetro
   (la misma trampa documentada con `Sector` en identificacion-riesgos). Prueba
   la siguiente; agotadas las dos, **pregunta el CIF al usuario**.
2. **La columna existe pero viene vacía** (`""` o nulo) — comprobado en
   expediente real el 26/08/2026: `NIF` existía y estaba en blanco. Se pregunta
   al usuario igual, anotando que la columna existe pero no está cumplimentada.
3. **La columna trae valor** → se usa, y se valida en el paso 2.

Sin expediente (el usuario da denominación y CIF directamente): se sigue igual,
y el informe va al directorio que el usuario indique, diciéndole que fuera del
expediente no queda archivado con el encargo.

### Paso 2 — Validar el CIF (puede parar)

```bash
python "$SKILL/scripts/validar_cif.py" --cif "<CIF>"
```

Salida `2` → **para y pregunta**: investigar un CIF mal tecleado produce un
informe sobre otra entidad, que es el peor resultado posible. Y si
`es_persona_juridica` es `false` (DNI/NIE), también se para: la investigación
mercantil no aplica a personas físicas.

### Paso 3 — Avisar de lo que va a pasar

Antes de lanzar nada, dile al usuario: que vas a lanzar **tres investigadores en
paralelo** sobre fuentes públicas de internet (BORME, PLACE, BDNS, CENDOJ, BOE,
prensa), que hacia fuera solo viajan denominación y CIF, que la ventana de
búsqueda es la que le digas, y que puede tardar varios minutos.

**La ventana temporal por defecto son los 5 años anteriores al cierre auditado,
hasta hoy.** Es la misma profundidad plurianual que maneja el expediente. Si el
usuario quiere otra, se usa la suya y el informe la declara.

### Paso 4 — Lanzar los tres agentes en paralelo

Los tres subagentes del plugin, **en una sola tanda** (una llamada por agente,
las tres en el mismo mensaje para que corran a la vez):

| Subagente | Cubre |
|---|---|
| `investigador-societario` | BORME, Registro Mercantil, actividad, CNAE |
| `investigador-sector-publico` | PLACE, BDNS |
| `investigador-riesgos-legales` | CENDOJ, sanciones BOE, prensa |

(Instalados desde el plugin aparecen con su prefijo, p. ej.
`gesia-auditoria:investigador-societario`.)

El prompt de cada uno lleva exactamente esto, y nada más del expediente:

```
Denominación confirmada: <razón social>
CIF: <CIF>
Cierre del ejercicio auditado: <fecha>
Ventana temporal: desde <cierre − 5 años> hasta <hoy>
Fecha de consulta a registrar: <hoy>
```

Cada agente devuelve **solo un JSON** (su contrato está en su propio fichero de
`agents/`). Si uno devuelve otra cosa o falla, **un reintento y se sigue**: su
sección del informe queda en ○ con la limitación explícita. No se bloquea la
investigación entera por una pata.

### Paso 5 — Archivar la evidencia

Guarda los tres JSON **tal cual llegaron**, sin retocar, en:

```
<expediente>\InformesGesia\InvestigacionEntidad\evidencia\
    <AAAA-MM-DD> societario.json
    <AAAA-MM-DD> sector-publico.json
    <AAAA-MM-DD> riesgos-legales.json
```

(La fecha es la de consulta.) Crea el árbol de carpetas antes de escribir. Esto
va **antes** del análisis: si algo se tuerce después, la evidencia ya está.

### Paso 6 — El análisis (este es tuyo)

Con los tres JSON delante, cruza. No generas hechos nuevos: añades relación
entre los que hay.

1. **Actividad declarada vs contratos públicos**: ¿el objeto social y lo
   adjudicado son coherentes?
2. **Cambios societarios vs procedimientos y sanciones**: ¿coincidencias
   temporales (cambio de administrador y litigio en fechas próximas)?
3. **Dependencia del sector público**: si los importes de contratos y
   subvenciones son relevantes, dilo con la cifra — sin cruzarla con las del
   expediente dentro del informe, que es de fuentes públicas.
4. **Huecos**: cuáles de los `huecos_informacion` importan para el encargo
   (p. ej. sin depósito de cuentas constatable).

Cada elemento del análisis cita los hechos concretos en que se basa y lleva
incertidumbre: `baja` = respaldado por dos o más fuentes; `alta` = hipótesis a
partir de una coincidencia. **La ausencia de información nunca genera un
indicio**: va a huecos. Y recuerda la regla 4: elementos a contrastar, no
conclusiones.

### Paso 7 — El informe, en Word (puede abortar)

El entregable es un `.docx` con la **cabecera común de los papeles del
expediente** (cliente, «AUDITORIA A <cierre>», título, fuente, bloque
`REF. P.T.` / `Realizado` / `Verificado`), como continuidad de saldos e
identificación de riesgos. La genera `generar_informe.py`; tú escribes el
contenido en un JSON y el script maqueta.

**La referencia se le pregunta al usuario**; si no la tiene, se pasa vacía
(`--ref ""`) y la celda queda en blanco — nunca se inventa un código que no
existe en el índice de Gesia.

Primero el contenido, en un temporal (**nunca en `InformesGesia`**):

```bash
TMPI="$TEMP/gesia-investigacion" && mkdir -p "$TMPI"
```

Escribe `$TMPI/informe.json`:

```json
{
  "identificacion": [{"campo": "Forma jurídica", "valor": "..."}],
  "secciones": {
    "societaria":     [{"texto": "...", "marca": "✓", "fuente": "BORME-A-..."}],
    "actividad":      [...],
    "sector_publico": [...],
    "riesgos_legales":[...],
    "analisis":       [{"texto": "...", "marca": "⚠", "incertidumbre": "media",
                        "fuente": "hechos que cruza"}]
  },
  "limitaciones_catalogo": ["borme_sin_historico", "place_sin_api"],
  "limitaciones_especificas": ["..."]
}
```

Las marcas, afirmación a afirmación: **✓** hecho verificado (exige `fuente`),
**⚠** indicio del análisis del paso 6 (con su incertidumbre), **○** sin
información (consta que se buscó). Los datos de fiabilidad `media`
(agregadores) se dicen como tales en el propio texto.

**Las limitaciones estructurales de las fuentes gratuitas no se redactan: se
marcan.** El catálogo vive en `generar_informe.py` con texto fijo
(`borme_sin_historico`, `registro_mercantil_pago`, `aeat_censal`,
`place_sin_api`, `cendoj_no_fetchable`, `boletines_no_fetchable`,
`prensa_no_indexada`, `cnae_no_oficial`): elige por id las que los `avisos` de
los agentes confirmen. En `limitaciones_especificas` va solo lo propio de esta
entidad. Un id fuera del catálogo aborta.

**La sección 8 (fuentes consultadas) no la escribes tú**: el script la
construye desde los `fuentes_consultadas` de la evidencia archivada, con las
que aportaron datos primero. Así el informe no puede citar una fuente que la
evidencia no respalde.

```bash
python "$SKILL/scripts/generar_informe.py" \
    --contenido "$TMPI/informe.json" \
    --evidencia-societario "<...>/evidencia/<fecha> societario.json" \
    --evidencia-sector-publico "<...>/evidencia/<fecha> sector-publico.json" \
    --evidencia-riesgos "<...>/evidencia/<fecha> riesgos-legales.json" \
    --cliente "<razón social>" --cif "<CIF>" --cierre "<dd/mm/aa>" \
    --ventana "<desde> - <hasta>" --generado "<AAAA-MM-DD>" --ref "<ref o vacía>" \
    --salida "<expediente>/InformesGesia/InvestigacionEntidad/Investigacion <CLIENTE> <AAAA>.docx"
```

(AAAA = ejercicio auditado.) Si un agente se degradó, omite su `--evidencia-*`:
el script lo hace constar en la tabla de fuentes. Salida `2` → defectos en el
contenido (marca inválida, hecho ✓ sin fuente, id de limitación inexistente):
**se corrige el JSON, nunca el script**, y se relanza.

### Paso 8 — Entregar

Di dónde han quedado el informe y la evidencia, resume en tres líneas lo más
relevante de cada bloque, y recuerda que el informe recopila y cruza información
pública: la evaluación del efecto en el encargo es del auditor. Si algún agente
se degradó (paso 4), dilo aquí también, no solo dentro del informe.

**Los temporales.** Borra el directorio de trabajo (`rm -rf "$TMPI"`). Si el
entorno no deja borrar (en Cowork pasa), di la ruta exacta de lo que queda: en
`InformesGesia` solo deben quedar el informe y la evidencia.

---

## Lo que este skill no hace

- **No consulta fuentes de pago ni con certificado**: ni el Registro Mercantil
  de pago, ni el censo de la AEAT, ni informes comerciales (eInforma, Axesor de
  pago). Sus fichas públicas gratuitas sí, marcadas como fiabilidad media.
- **No resuelve CAPTCHAs ni crea cuentas** en ningún servicio.
- **No mezcla las cifras del expediente con el informe.** La comparación entre
  lo público y lo contabilizado (p. ej. subvenciones BDNS vs ingresos) es un
  procedimiento de auditoría posterior, del auditor.
- **No identifica riesgos NIA 315**: eso es `identificacion-riesgos`, con las
  cifras del expediente. Este skill le da contexto externo, no lo sustituye.
- **No escribe en el expediente de Gesia.**

## Degradación

| Situación | Qué sale |
|---|---|
| Servidor API de Gesia caído o sin expediente | se piden denominación y CIF al usuario y se sigue |
| CIF sin columna en `DatosAuditoria` | se pregunta al usuario |
| Columna `CIF`/`NIF` existe pero vacía | se pregunta al usuario, anotando que la columna no está cumplimentada |
| CIF con control inválido | **para.** No se investiga una entidad mal identificada |
| DNI/NIE en vez de CIF | **para.** Fuera del alcance |
| Un agente falla o devuelve JSON inválido | un reintento; después, sección en ○ con limitación explícita |
| Homonimia señalada por un agente | se traslada al usuario antes del informe; su decisión consta en Limitaciones |
| Sin hallazgos en todas las fuentes | informe igualmente, con las fuentes y fechas consultadas |
