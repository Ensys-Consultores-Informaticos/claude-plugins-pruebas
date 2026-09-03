"""Emparejamiento de saldos (facturas vs pagos) para el mayor de una cuenta
de un expediente de auditoria de Gesia.

No imprime: devuelve datos. Quien llama (verificar_contrato.py,
generar_papel.py) decide que hacer con ellos.

PUNTEO PREVIO. Muchos .smn traen la columna `Indice`: el punteo hecho en la
contabilidad o en Gesia, numerado POR CUENTA (la clave es CUENTA+Indice; ver
docs/contrato-datos.md). Cuando el extracto la trae, se respeta: los apuntes
con indice previo > 0 son grupos ya cancelados, no entran al emparejamiento,
y los indices que asigna este modulo arrancan por encima del maximo previo
de la cuenta. Cada grupo previo se verifica igualmente (¿suma 0?): si no
suma, SE AVISA PERO SE RESPETA -- la contabilidad del cliente manda y el
auditor decide. Si la columna no existe (es una opcion de importacion que
falta con normalidad), el emparejamiento parte de cero, como siempre.

Procedimientos (2.1 a 2.4 del encargo original que dio pie a este skill),
aplicados cuenta por cuenta SOBRE LOS APUNTES SIN PUNTEAR:

  2.1  si todo lo pendiente suma 0, un solo INDICE para esos apuntes.
  2.2  si no, pero el total pendiente coincide con el saldo del ULTIMO
       apunte pendiente en orden cronologico, se cancela todo menos ese
       ultimo (que queda como saldo pendiente, INDICE 0).
  2.3  cancelacion directa: apuntes de igual importe absoluto y signo
       contrario se emparejan 1 a 1, sin mirar la fecha.
  2.4  lo que queda se intenta cancelar en orden cronologico, acumulando
       SALDO hasta que de 0 (agrupacion secuencial: cualquier tramo
       contiguo en el tiempo que sume 0 se cierra como grupo). Lo que
       sigue sin cancelar se intenta con combinaciones acotadas (hasta
       MAX_GRUPO_COMBOS apuntes a la vez) buscando subconjuntos --no
       necesariamente contiguos en fecha-- que sumen 0.

Lo que este modulo NO hace: no usa el texto de CONCEPTO para decidir que
apuntes van juntos, aunque el encargo original lo menciona como señal de
apoyo ("por alguna similitud en el campo CONCEPTO"). Se decidio no
implementarlo: es un emparejamiento difuso sin regla objetiva de cuando
aceptar una coincidencia de texto, y el criterio numerico (fecha + importe)
ya resolvio sin ambiguedad el caso real usado para calibrar esto (una
cuenta de clientes del expediente de calibracion: 46 de 46 grupos
correctos).
CONCEPTO se conserva en el informe para que el auditor lo lea, no para que
el algoritmo decida por el. Tampoco usa los campos NN_*: pueden no existir
y su semantica no esta garantizada entre expedientes.

La busqueda combinatoria del 2.4 es un backstop, no magia: sobre cuentas
con muchos apuntes sin cancelar por los pasos anteriores, buscar
subconjuntos que sumen 0 crece muy rapido (es un subset-sum), asi que se
acota a MAX_LEFTOVER_FOR_COMBOS apuntes de entrada y grupos de hasta
MAX_GRUPO_COMBOS. Por encima de eso, sencillamente no se intenta y esos
apuntes quedan en INDICE 0 -- no es un fallo silencioso: verificar_contrato
avisa cuando una cuenta es lo bastante grande para que esto importe.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import pandas as pd

TOL = 0.005                    # tolerancia de redondeo en euros
MAX_LEFTOVER_FOR_COMBOS = 22   # por encima de esto, no se intenta la combinatoria
MAX_GRUPO_COMBOS = 6           # tamaño maximo de grupo que se busca por combinacion
MAX_PAGOS_APERTURA = 14        # candidatos que se prueban por combinacion al cancelar
                               # la apertura. 14 sobre grupos de hasta 6 son 3.003
                               # subconjuntos: instantaneo, y en el caso medido la
                               # apertura se cancela con los pagos de enero, que
                               # siempre caen dentro de esos primeros candidatos

COLUMNAS_REQUERIDAS = ("FECHA", "CUENTA", "NOMBRE", "CONCEPTO")

# valores de la columna ORIGEN del resultado
ORIGEN_CONTABLE = "contable"     # el grupo venia punteado en el .smn (Indice)
ORIGEN_AUDITORIA = "auditoría"   # el grupo lo asigno este modulo


def _round2(v) -> float:
    return round(float(v), 2)


def cargar_extracto(ruta) -> pd.DataFrame:
    """Carga el fichero que exporta Gesia con exportar_consulta: .csv con
    ';' como separador, o .json. Si no trae SALDO pero si DEBE/HABER, lo
    deriva como DEBE-HABER -- que es, comprobado sobre el diario real, el
    mismo importe con signo que Gesia guarda en su columna SALDO/NN_Saldo
    para cada apunte (no es un saldo acumulado, pese al nombre).

    Si trae la columna del punteo previo (`Indice`, en cualquier
    capitalizacion), la normaliza a INDICE_PREVIO: entero, sin negativos,
    0 = sin puntear. Es OPCIONAL: su ausencia no es un error.

    Lanza ValueError si faltan columnas obligatorias -- no adivina nombres
    de campo alternativos: eso lo decide quien llama (o el auditor, si el
    extracto viene de otro sitio).
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(str(ruta))

    if ruta.suffix.lower() == ".json":
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        df = pd.DataFrame(datos)
    else:
        df = pd.read_csv(ruta, sep=";")

    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        raise ValueError("faltan columnas obligatorias: " + str(faltan))

    if "SALDO" not in df.columns:
        if "DEBE" in df.columns and "HABER" in df.columns:
            df["SALDO"] = (
                pd.to_numeric(df["DEBE"], errors="coerce").fillna(0)
                - pd.to_numeric(df["HABER"], errors="coerce").fillna(0)
            )
        else:
            raise ValueError("no hay columna SALDO ni DEBE/HABER para derivarla")

    col_prev = next(
        (c for c in df.columns
         if str(c).strip().lower() in ("indice", "índice", "indice_previo")),
        None,
    )
    if col_prev is not None:
        df["INDICE_PREVIO"] = (
            pd.to_numeric(df[col_prev], errors="coerce")
            .fillna(0).astype(int).clip(lower=0)
        )
        if col_prev != "INDICE_PREVIO":
            df = df.drop(columns=[col_prev])

    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce", dayfirst=False)
    df["SALDO"] = pd.to_numeric(df["SALDO"], errors="coerce")
    df["CUENTA"] = df["CUENTA"].astype(str)
    df["NOMBRE"] = df["NOMBRE"].fillna("").astype(str)
    df["CONCEPTO"] = df["CONCEPTO"].fillna("").astype(str)

    # ORDEN PROPIO, sin fiarse de quien llame. El pareo directo recorre las
    # filas en el orden en que vienen, asi que un ORDER BY distinto en la
    # consulta daba un papel distinto con el MISMO dato. Medido el 31/08/2026
    # sobre un expediente real: por FECHA salian 45 hallazgos, por ASIENTO 49
    # y en orden inverso 53, y hasta el importe de apertura vivo cambiaba.
    #
    # La clave es solo de datos -no incluye el indice de entrada-, asi que dos
    # extractos con las mismas filas dan el mismo papel aunque lleguen en
    # cualquier orden. Es lo que hace que el papel se pueda regenerar.
    clave = [c for c in ("CUENTA", "FECHA", "ASIENTO", "SALDO", "CONCEPTO")
             if c in df.columns]
    df = df.sort_values(clave, kind="mergesort").reset_index(drop=True)
    return df


def _emparejar_pendientes(df: pd.DataFrame, next_idx: int) -> int:
    """Aplica 2.1-2.4 a un df cuyos apuntes vienen TODOS con INDICE 0,
    mutando INDICE, GRUPO_24 y GRUPO_APERTURA sobre sus etiquetas de indice (que no tienen
    por que ser 0..n: puede ser el subconjunto sin puntear de una cuenta).
    Devuelve el primer indice libre tras asignar.
    """
    total = _round2(df["SALDO"].sum())

    # --- 2.1: si el total pendiente ya es cero, todo un solo indice ---
    if abs(total) < TOL:
        df["INDICE"] = next_idx
        return next_idx + 1

    # --- 2.2: si el total coincide con el saldo del ULTIMO apunte
    #          (orden cronologico), cancelar todos menos ese ---
    orden_fecha = df.sort_values(["FECHA"]).index.tolist()
    ultimo_idx = orden_fecha[-1]
    ultimo_saldo = _round2(df.loc[ultimo_idx, "SALDO"])

    if abs(total - ultimo_saldo) < TOL and len(df) > 1:
        mascara = df.index != ultimo_idx
        df.loc[mascara, "INDICE"] = next_idx
        return next_idx + 1  # el ultimo se queda con INDICE 0 (pendiente)

    # --- 2.2b: la apertura primero ---------------------------------------
    # Matar el saldo de apertura es el objetivo del procedimiento, y hasta
    # ahora la apertura era un apunte mas: el pareo directo de 2.3 se llevaba
    # sus pagos antes de que nadie mirase si servian para eso, y la apertura
    # se quedaba viva. Medido el 30/08/2026 en las cuentas 40 y 41 de un
    # expediente real: 74 aperturas sin cancelar por 169.332 EUR; con este
    # paso, 67 por 49.637 EUR -un 71% menos-, sin ningun grupo descuadrado.
    #
    # Se reconoce POR ESTRUCTURA, no por el texto del concepto: la apertura
    # es del 1 de enero -no puede haber saldo anterior a eso- y es el apunte
    # mas antiguo de la cuenta. Y no se presupone el signo: en una cuenta
    # acreedora es un abono que cancelan pagos, y en una deudora al reves.
    pend = df[df["INDICE"] == 0].sort_values("FECHA")
    if len(pend) > 1:
        primero = pend.index[0]
        del_dia_1 = pend[(pend["FECHA"].dt.month == 1) & (pend["FECHA"].dt.day == 1)]
        if len(del_dia_1) == 1 and del_dia_1.index[0] == primero:
            objetivo = -_round2(df.loc[primero, "SALDO"])
            signo = 1 if objetivo > 0 else -1
            candidatos = [i for i in pend.index[1:]
                          if signo * df.loc[i, "SALDO"] > TOL]
            grupo = None

            # a) los primeros pagos en orden, acumulando hasta dar el importe
            acc = 0.0
            tramo = []
            for i in candidatos:
                acc = _round2(acc + df.loc[i, "SALDO"])
                tramo.append(i)
                if abs(acc - objetivo) < TOL:
                    grupo = list(tramo)
                    break
                if abs(acc) > abs(objetivo) + TOL:
                    break

            # b) si no cuadra asi, subconjuntos acotados de los primeros
            if grupo is None:
                cand = candidatos[:MAX_PAGOS_APERTURA]
                for n in range(1, min(MAX_GRUPO_COMBOS, len(cand)) + 1):
                    for combo in combinations(cand, n):
                        s = _round2(sum(df.loc[x, "SALDO"] for x in combo))
                        if abs(s - objetivo) < TOL:
                            grupo = list(combo)
                            break
                    if grupo:
                        break

            # si no hay conjunto exacto, no se fuerza nada: la apertura queda
            # pendiente y el auditor la ve en amarillo, que es lo correcto.
            if grupo:
                for x in [primero] + grupo:
                    df.loc[x, "INDICE"] = next_idx
                    df.loc[x, "GRUPO_APERTURA"] = True
                next_idx += 1

    # --- 2.3: cancelacion directa (mismo importe absoluto, signo contrario) ---
    buckets = defaultdict(lambda: {"pos": [], "neg": []})
    # SOLO lo que sigue sin asignar: 2.2b ya se ha llevado los apuntes de la
    # apertura. Antes recorria todo el df, que era correcto mientras 2.3 fuese
    # el primer paso que asigna, y deja de serlo en cuanto algo va delante.
    for idx, row in df[df["INDICE"] == 0].iterrows():
        b = buckets[row["SaldoABS"]]
        if row["SALDO"] > TOL:
            b["pos"].append(idx)
        elif row["SALDO"] < -TOL:
            b["neg"].append(idx)

    for _, b in buckets.items():
        pares = min(len(b["pos"]), len(b["neg"]))
        for i in range(pares):
            p, n = b["pos"][i], b["neg"][i]
            df.loc[p, "INDICE"] = next_idx
            df.loc[n, "INDICE"] = next_idx
            next_idx += 1

    # apuntes con SALDO 0 exacto se autocancelan (caso raro)
    for idx in df[(df["INDICE"] == 0) & (df["SaldoABS"] < TOL)].index:
        df.loc[idx, "INDICE"] = next_idx
        next_idx += 1

    # --- 2.4a: agrupacion secuencial por SaldoAcumulado, en orden cronologico ---
    pendientes = df[df["INDICE"] == 0].sort_values(["FECHA"]).index.tolist()
    usados = set()
    i = 0
    while i < len(pendientes):
        if pendientes[i] in usados:
            i += 1
            continue
        acc = 0.0
        grupo = []
        j = i
        while j < len(pendientes):
            ridx = pendientes[j]
            if ridx in usados:
                j += 1
                continue
            acc = _round2(acc + df.loc[ridx, "SALDO"])
            grupo.append(ridx)
            if abs(acc) < TOL and len(grupo) > 1:
                for gidx in grupo:
                    df.loc[gidx, "INDICE"] = next_idx
                    df.loc[gidx, "GRUPO_24"] = True
                    usados.add(gidx)
                next_idx += 1
                grupo = []
                acc = 0.0
            j += 1
        i += 1

    # --- 2.4b: combinaciones acotadas sobre lo que quede ---
    leftover = df[df["INDICE"] == 0].index.tolist()
    if 1 < len(leftover) <= MAX_LEFTOVER_FOR_COMBOS:
        encontrado_algo = True
        while encontrado_algo and len(leftover) > 1:
            encontrado_algo = False
            cents = {idx: int(round(df.loc[idx, "SALDO"] * 100)) for idx in leftover}
            grupo_hallado = None
            tope = min(MAX_GRUPO_COMBOS, len(leftover))
            for r in range(2, tope + 1):
                for combo in combinations(leftover, r):
                    if sum(cents[c] for c in combo) == 0:
                        grupo_hallado = combo
                        break
                if grupo_hallado:
                    break
            if grupo_hallado:
                for gidx in grupo_hallado:
                    df.loc[gidx, "INDICE"] = next_idx
                    df.loc[gidx, "GRUPO_24"] = True
                next_idx += 1
                leftover = [x for x in leftover if x not in grupo_hallado]
                encontrado_algo = True

    return next_idx


def asignar_indices_cuenta(df_cta: pd.DataFrame):
    """Aplica el emparejamiento a UNA sola cuenta. df_cta: columnas FECHA
    (datetime), CUENTA, NOMBRE, CONCEPTO, SALDO (float, importe con signo
    del apunte) y, opcionalmente, INDICE_PREVIO (punteo del .smn).

    Devuelve (df_resultado, siguiente_indice_libre). df_resultado añade:
      SaldoABS   importe absoluto
      INDICE     int, 0 = sin cancelar. Conserva los previos tal cual y
                 numera los nuevos por encima del maximo previo
      ORIGEN     ORIGEN_CONTABLE si el grupo venia punteado en el .smn,
                 ORIGEN_AUDITORIA si lo asigno este modulo, "" si pendiente
      GRUPO_24   True si el emparejamiento vino del procedimiento 2.4
                 (para resaltar en el informe)
      GRUPO_APERTURA  True si el grupo es el de la apertura y sus pagos
                 (procedimiento 2.2b)
    """
    df = df_cta.copy().reset_index(drop=True)
    df["SaldoABS"] = df["SALDO"].abs().round(2)

    if "INDICE_PREVIO" in df.columns:
        prev = (
            pd.to_numeric(df["INDICE_PREVIO"], errors="coerce")
            .fillna(0).astype(int).clip(lower=0)
        )
    else:
        prev = pd.Series(0, index=df.index, dtype=int)

    df["INDICE"] = prev
    df["ORIGEN"] = ""
    df.loc[prev > 0, "ORIGEN"] = ORIGEN_CONTABLE
    df["GRUPO_24"] = False
    df["GRUPO_APERTURA"] = False

    next_idx = int(prev.max()) + 1
    pendientes = df.index[df["INDICE"] == 0]
    if len(pendientes) == 0:
        return df, next_idx

    sub = df.loc[pendientes, ["FECHA", "SALDO", "SaldoABS", "INDICE",
                             "GRUPO_24", "GRUPO_APERTURA"]].copy()
    next_idx = _emparejar_pendientes(sub, next_idx)

    df.loc[sub.index, "INDICE"] = sub["INDICE"]
    df.loc[sub.index, "GRUPO_24"] = sub["GRUPO_24"]
    df.loc[sub.index, "GRUPO_APERTURA"] = sub["GRUPO_APERTURA"]
    df.loc[sub.index[sub["INDICE"] > 0], "ORIGEN"] = ORIGEN_AUDITORIA
    return df, next_idx


def verificar_cuenta(df_resultado: pd.DataFrame) -> dict:
    """Comprueba las reglas de verificacion.

    Para los grupos asignados por este modulo (ORIGEN auditoria) sumar 0 es
    una propiedad estructural del algoritmo: si no se cumple hay un bug de
    contabilidad interna, no un caso limite de los datos. Para los grupos
    del punteo previo (ORIGEN contable) NO esta garantizado: un grupo
    previo que no suma 0 se reporta en grupos_previos_descuadrados y se
    respeta -- es punteo del cliente y lo juzga el auditor.

    La conciliacion estructural descuenta ese descuadre previo: la suma de
    INDICE=0 tiene que coincidir con el total de la cuenta menos lo que
    sumen (bien o mal) los grupos punteados.
    """
    total = _round2(df_resultado["SALDO"].sum())
    idx0 = _round2(df_resultado.loc[df_resultado["INDICE"] == 0, "SALDO"].sum())
    origen = (df_resultado["ORIGEN"] if "ORIGEN" in df_resultado.columns
              else pd.Series("", index=df_resultado.index))

    grupos_auditoria = {}
    grupos_previos = {}
    for i in sorted(df_resultado["INDICE"].unique()):
        if i == 0:
            continue
        filas = df_resultado[df_resultado["INDICE"] == i]
        s = _round2(filas["SALDO"].sum())
        if (origen.loc[filas.index] == ORIGEN_CONTABLE).any():
            grupos_previos[int(i)] = s
        else:
            grupos_auditoria[int(i)] = s

    grupos_con_error = {k: v for k, v in grupos_auditoria.items() if abs(v) > TOL}
    previos_descuadrados = {k: v for k, v in grupos_previos.items() if abs(v) > TOL}
    descuadre_previo = _round2(sum(previos_descuadrados.values()))

    return {
        "total_cuenta": total,
        "suma_indice_0": idx0,
        "coincide_total_con_no_cancelado": abs(total - descuadre_previo - idx0) < TOL,
        "num_grupos_previos": len(grupos_previos),
        "num_grupos_nuevos": len(grupos_auditoria),
        "num_grupos_cancelados": len(grupos_previos) + len(grupos_auditoria),
        "grupos_con_error": grupos_con_error,
        "grupos_previos_descuadrados": previos_descuadrados,
        "descuadre_punteo_previo": descuadre_previo,
        "num_registros_sin_cancelar": int((df_resultado["INDICE"] == 0).sum()),
    }


# Muchas contabilidades registran la factura a fin de mes y escriben en el
# concepto la fecha del documento ("Fra - PROVEEDOR - 21/01/2025 - FVR2025...").
# Comparar contra la fecha de asiento fabrica entonces "pagos anteriores a su
# factura" que no lo son. Medido en un expediente real: 820 casos con la fecha
# contable y 198 con la del documento -- el 76% eran la fecha de registro.
#
# Esta fecha se usa SOLO PARA INFORMAR. El emparejamiento sigue trabajando con
# la fecha contable: hacerlo depender de un campo de texto libre que el cliente
# rellena como quiere seria fragil, y un 8% de las facturas no lo traen.
_FECHA_CONCEPTO = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def fecha_documento(concepto, por_defecto):
    """Fecha del documento escrita en el concepto, o la que se pase si no hay."""
    m = _FECHA_CONCEPTO.search(str(concepto))
    if not m:
        return por_defecto
    try:
        return pd.Timestamp(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return por_defecto


def _signo_documento(res) -> int:
    """Que signo tienen los documentos (facturas) en esta cuenta: +1 o -1.

    Por estructura, sin mirar el texto. La APERTURA arrastra los documentos
    que quedaron pendientes del ejercicio anterior, asi que lleva su mismo
    signo: en una cuenta de proveedor es un abono, y en una de cliente un
    cargo. Si no hay apertura, sirve el signo del saldo de la cuenta, que
    apunta en la misma direccion mientras quede algo pendiente.

    Devuelve 0 si no se puede decidir -cuenta sin apertura y con saldo cero-,
    y entonces el grupo no entra en los recuentos de fechas: mejor no evaluar
    que evaluar al reves.
    """
    if len(res):
        primero = res.sort_values("FECHA").iloc[0]
        if primero["FECHA"].month == 1 and primero["FECHA"].day == 1                 and abs(primero["SALDO"]) > TOL:
            return 1 if primero["SALDO"] > 0 else -1
    total = _round2(res["SALDO"].sum())
    if abs(total) > TOL:
        return 1 if total > 0 else -1
    return 0


def _lados(grupo, signo_doc: int):
    """Separa el grupo en (documentos, pagos) segun el signo de la cuenta."""
    if signo_doc == 0:
        return None, None
    docs = grupo[grupo["SALDO"] * signo_doc > TOL]
    pagos = grupo[grupo["SALDO"] * signo_doc < -TOL]
    if docs.empty or pagos.empty:
        return None, None
    return docs, pagos


def _lados_por_texto(grupo):
    """Respaldo cuando el signo no se puede deducir: que lado trae fecha.

    Las lineas de factura suelen escribir la fecha del documento en el
    concepto y las de pago no. Es una pista de texto, y por eso va SEGUNDA:
    solo se usa en cuentas sin apertura y con saldo cero, donde el criterio
    estructural no dice nada. Si tampoco decide, el grupo no se evalua.
    """
    pos = grupo[grupo["SALDO"] > TOL]
    neg = grupo[grupo["SALDO"] < -TOL]
    if pos.empty or neg.empty:
        return None, None
    con_pos = sum(1 for c in pos["CONCEPTO"] if _FECHA_CONCEPTO.search(str(c)))
    con_neg = sum(1 for c in neg["CONCEPTO"] if _FECHA_CONCEPTO.search(str(c)))
    if con_neg > con_pos:
        return neg, pos
    if con_pos > con_neg:
        return pos, neg
    return None, None


def analizar_hallazgos(df: pd.DataFrame, por_cuenta: dict) -> dict:
    """Recuentos para la hoja de criterios y hallazgos. No juzga nada."""
    plazos = []
    facturas = con_fecha = 0
    anom_doc = anom_solo_registro = no_evaluables = 0
    forzados = con_alternativa = grandes = 0
    ap_detectadas = ap_canceladas = ap_vivas = 0
    ap_importe_vivo = 0.0
    ctas_sin_apertura = 0

    for cuenta, (res, _info) in por_cuenta.items():
        # cuantos apuntes de cada importe hay: dice si el pareo tenia eleccion
        cuenta_por_importe = defaultdict(lambda: {"pos": 0, "neg": 0})
        for _, r in res.iterrows():
            if abs(r["SALDO"]) < TOL:
                continue
            lado = "pos" if r["SALDO"] > 0 else "neg"
            cuenta_por_importe[round(abs(r["SALDO"]), 2)][lado] += 1

        primero = res.sort_values("FECHA").iloc[0] if len(res) else None
        hay_apertura = (primero is not None
                        and primero["FECHA"].month == 1 and primero["FECHA"].day == 1)
        if hay_apertura:
            ap_detectadas += 1
            if primero["INDICE"] > 0:
                ap_canceladas += 1
            else:
                ap_vivas += 1
                ap_importe_vivo = _round2(ap_importe_vivo + abs(primero["SALDO"]))
        else:
            ctas_sin_apertura += 1

        signo_doc = _signo_documento(res)
        for ind, g in res[res["INDICE"] > 0].groupby("INDICE"):
            docs, pagos = _lados(g, signo_doc)
            if docs is None:
                docs, pagos = _lados_por_texto(g)
            if docs is None:
                no_evaluables += 1
                continue
            facturas += len(docs)
            con_fecha += sum(1 for c in docs["CONCEPTO"]
                             if _FECHA_CONCEPTO.search(str(c)))
            f_pago = pagos["FECHA"].min()
            f_doc = min(fecha_documento(r["CONCEPTO"], r["FECHA"])
                        for _, r in docs.iterrows())
            if f_pago < f_doc:
                anom_doc += 1
                if len(g) > 2:
                    grandes += 1
                else:
                    c = cuenta_por_importe[round(abs(g["SALDO"].iloc[0]), 2)]
                    if c["pos"] == 1 and c["neg"] == 1:
                        forzados += 1
                    else:
                        con_alternativa += 1
            elif f_pago < docs["FECHA"].min():
                anom_solo_registro += 1
            else:
                plazos.append((f_pago - f_doc).days)

    plazos.sort()
    def pct(q):
        return int(plazos[int(q * (len(plazos) - 1))]) if plazos else None

    return {
        "cuentas": len(por_cuenta),
        "apuntes": int(len(df)),
        "grupos_evaluados": anom_doc + anom_solo_registro + len(plazos),
        "facturas_con_fecha_doc": con_fecha,
        "facturas_totales": facturas,
        "anomalos": anom_doc,
        "solo_fecha_registro": anom_solo_registro,
        "grupos_no_evaluables": no_evaluables,
        "anom_forzados": forzados,
        "anom_con_alternativa": con_alternativa,
        "anom_grupos_grandes": grandes,
        "plazo_p25": pct(0.25),
        "plazo_mediana": pct(0.50),
        "plazo_p75": pct(0.75),
        "plazo_muestra": len(plazos),
        "aperturas_detectadas": ap_detectadas,
        "aperturas_canceladas": ap_canceladas,
        "aperturas_vivas": ap_vivas,
        "aperturas_importe_vivo": ap_importe_vivo,
        "cuentas_sin_apertura": ctas_sin_apertura,
    }


def procesar_extracto(df: pd.DataFrame) -> dict:
    """Aplica el emparejamiento a CADA cuenta distinta del extracto.
    Devuelve {cuenta: (df_resultado, verificacion)}, en el orden en que
    aparecen las cuentas al ordenar por CUENTA."""
    resultado = {}
    for cuenta, grupo in df.groupby("CUENTA", sort=True):
        res, _ = asignar_indices_cuenta(grupo)
        info = verificar_cuenta(res)
        resultado[cuenta] = (res, info)
    return resultado
