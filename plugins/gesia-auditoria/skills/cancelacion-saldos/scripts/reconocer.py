# -*- coding: utf-8 -*-
"""Mira el extracto ANTES de emparejar, y dice con que se cuenta y que preguntar.

    python reconocer.py --entrada extracto.csv

Por que existe. La cancelacion de saldos no tiene un algoritmo unico: depende de
como pague el cliente y de que columnas trajo el diario. La mejora mas grande que
ha tenido este skill vino de una columna OPCIONAL que no se pedia nunca
-`NN_Factura`-, y sin ella el resultado era tres veces peor. Lanzarse a cincuenta
cuentas sin haber mirado eso es gastar el trabajo para acabar con un papel malo.

Asi que este script hace una pasada en seco -no escribe ningun papel- y responde
tres cosas:

  1. QUE HAY: columnas presentes, cuentas, apuntes, aperturas.
  2. CUANTO APORTA CADA SEÑAL, medido sobre este cliente y no en general: cuanto
     cerraria el numero de documento, cuanto la apertura, cuanto queda.
  3. QUE PREGUNTAR AL AUDITOR, y solo lo que no se puede ver aqui. Lo que se
     mide no se pregunta: es lo que mantiene la entrevista corta.

Es barato -son unos miles de filas- y no gasta contexto del modelo: imprime un
resumen corto, no las filas.

No lee el reloj, no escribe nada y no decide nada.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_cancelacion import (  # noqa: E402
    TOL,
    MAX_LEFTOVER_FOR_COMBOS,
    _indice_apertura_informe,
    asignar_indices_cuenta,
    cargar_extracto,
)


def _eur(v) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def reconocer(df) -> dict:
    """Todo lo que se puede saber del extracto sin preguntar nada."""
    tiene_fra = "FACTURA" in df.columns
    info = {
        "apuntes": len(df),
        "cuentas": int(df["CUENTA"].nunique()),
        "columnas": {
            "punteo_previo": "INDICE_PREVIO" in df.columns,
            "numero_documento": tiene_fra,
            "asiento": "ASIENTO" in df.columns,
            "concepto": "CONCEPTO" in df.columns,
        },
        "sin_documento": int((df["FACTURA"] == "").sum()) if tiene_fra else None,
        "cuentas_detalle": [],
    }

    for cta, g in df.groupby("CUENTA"):
        res, _ = asignar_indices_cuenta(g)
        pend = res[res["INDICE"] == 0]
        # la MISMA deteccion que usan el emparejamiento y el papel: una sola regla
        idx_ap = _indice_apertura_informe(res)
        orden = res.sort_values("FECHA")
        ap = res.loc[idx_ap] if idx_ap is not None else orden.iloc[0]
        es_ap = idx_ap is not None
        info["cuentas_detalle"].append({
            "cuenta": str(cta),
            "nombre": str(res["NOMBRE"].iloc[0])[:30],
            "apuntes": len(res),
            "grupos": int(res.loc[res["INDICE"] > 0, "INDICE"].nunique()),
            "sueltos": len(pend),
            "por_documento": int(res["GRUPO_FACTURA"].sum()) if "GRUPO_FACTURA" in res else 0,
            "apertura": round(float(ap["SALDO"]), 2) if es_ap else 0.0,
            "apertura_abierta": bool(es_ap and int(ap["INDICE"]) == 0),
            # el primero es del 1 de enero pero la regla no puede decir cual es la
            # apertura (varios ese dia, o cuenta de un solo apunte): NO se ha
            # intentado, y eso no es lo mismo que no haber podido
            "apertura_no_identificable": bool(
                idx_ap is None and len(res) and orden.iloc[0]["FECHA"].month == 1
                and orden.iloc[0]["FECHA"].day == 1),
            "apertura_aparente": round(float(orden.iloc[0]["SALDO"]), 2) if len(res) else 0.0,
            "total": round(float(res["SALDO"].sum()), 2),
            "tamanos": Counter(res.loc[res["INDICE"] > 0].groupby("INDICE").size().tolist()),
        })

    d = info["cuentas_detalle"]
    info["resumen"] = {
        "apuntes_en_grupos": sum(c["apuntes"] - c["sueltos"] for c in d),
        "sueltos": sum(c["sueltos"] for c in d),
        "por_documento": sum(c["por_documento"] for c in d),
        "aperturas": sum(1 for c in d if c["apertura"]),
        "aperturas_abiertas": sum(1 for c in d if c["apertura_abierta"]),
        # en VALOR ABSOLUTO, como lo reporta el papel: sumar con signo dejaria
        # que una apertura deudora tapase una acreedora y el importe vivo saldria
        # menor de lo que es. Los dos informes tienen que dar la misma cifra.
        "importe_aperturas": round(sum(abs(c["apertura"]) for c in d), 2),
        "importe_aperturas_abiertas": round(
            sum(abs(c["apertura"]) for c in d if c["apertura_abierta"]), 2),
        "atascadas": [c["cuenta"] for c in d if c["sueltos"] > MAX_LEFTOVER_FOR_COMBOS],
        # CON NOMBRE Y APELLIDOS. La pregunta por el mayor del ejercicio anterior
        # decia «queda 1 apertura sin cancelar por 1.460,78» y NO decia de que
        # cuenta, asi que el auditor no podia ir a buscar el mayor de nada. Lo
        # reporto David el 08/09/2026 probando el canal de pruebas.
        "abiertas_detalle": sorted(
            [(c["cuenta"], c["nombre"], c["apertura"]) for c in d if c["apertura_abierta"]],
            key=lambda x: -abs(x[2])),
        "no_identificadas_detalle": sorted(
            [(c["cuenta"], c["nombre"], c["apertura_aparente"]) for c in d
             if c["apertura_no_identificable"]],
            key=lambda x: -abs(x[2])),
    }
    # patron de pago: cuantos grupos de mas de dos apuntes salen del documento.
    # Muchos grupos de 3 o 4 son pagos a plazos, y eso se VE, no hace falta
    # preguntarlo.
    tam = Counter()
    for c in d:
        tam.update(c["tamanos"])
    info["tamanos_grupo"] = dict(sorted(tam.items()))

    # parejas que se quedan a un centimo: la pregunta de materialidad
    casi = []
    for cta, g in df.groupby("CUENTA"):
        if not tiene_fra:
            break
        for fra, gg in g[g["FACTURA"] != ""].groupby("FACTURA"):
            if len(gg) < 2:
                continue
            s = round(float(gg["SALDO"].sum()), 2)
            if TOL <= abs(s) <= 0.05:
                casi.append((str(cta), str(fra), s, len(gg)))
    info["casi_cuadran"] = casi
    return info


def _informe(info: dict) -> list[str]:
    r, cols = info["resumen"], info["columnas"]
    L = [
        "RECONOCIMIENTO DEL EXTRACTO (pasada en seco, no se ha escrito ningun papel)",
        "",
        f"  {info['apuntes']} apuntes en {info['cuentas']} cuenta(s)",
        "",
        "  COLUMNAS OPCIONALES:",
        f"    punteo previo (Indice) ....... {'SI' if cols['punteo_previo'] else 'NO'}",
        f"    numero de documento .......... {'SI' if cols['numero_documento'] else 'NO'}"
        + (f" ({info['sin_documento']} apuntes sin numero)"
           if cols["numero_documento"] else "  <-- SIN ESTO EL RESULTADO ES MUCHO PEOR"),
        f"    asiento ...................... {'SI' if cols['asiento'] else 'NO'}",
        "",
        "  LO QUE SE CANCELARIA, medido sobre este extracto:",
        f"    apuntes emparejados .......... {r['apuntes_en_grupos']} de {info['apuntes']}",
        f"    de ellos, por documento ...... {r['por_documento']}",
        f"    quedarian sueltos ............ {r['sueltos']}",
        f"    tamaños de grupo ............. {info['tamanos_grupo']}",
        "",
        "  LA APERTURA, que es lo que mas vale del procedimiento:",
        f"    cuentas con apertura ......... {r['aperturas']}  ({_eur(r['importe_aperturas'])})",
        f"    se quedarian SIN cancelar .... {r['aperturas_abiertas']}"
        f"  ({_eur(r['importe_aperturas_abiertas'])})",
    ]
    if r["abiertas_detalle"]:
        L += ["", "    las que se quedan sin cerrar:"]
        L += [f"      {c}  {n:30} {_eur(imp):>14}" for c, n, imp in r["abiertas_detalle"][:10]]
        if len(r["abiertas_detalle"]) > 10:
            L.append(f"      ... y {len(r['abiertas_detalle']) - 10} mas")
    if r["no_identificadas_detalle"]:
        L += ["",
              f"    NO IDENTIFICABLES ({len(r['no_identificadas_detalle'])}): varios apuntes el "
              "1 de enero, o cuenta de un solo apunte.",
              "    El emparejamiento NO las ha intentado: no es que no cuadren, es que no se "
              "sabe cual es la apertura."]
        L += [f"      {c}  {n:30} {_eur(imp):>14}"
              for c, n, imp in r["no_identificadas_detalle"][:10]]
        if len(r["no_identificadas_detalle"]) > 10:
            L.append(f"      ... y {len(r['no_identificadas_detalle']) - 10} mas")
    if r["atascadas"]:
        L += ["",
              f"  CUENTAS QUE SE ATASCAN ({len(r['atascadas'])}): mas de "
              f"{MAX_LEFTOVER_FOR_COMBOS} sueltos, la combinatoria no se intenta",
              "    " + ", ".join(r["atascadas"][:12])
              + (" ..." if len(r["atascadas"]) > 12 else "")]

    # ── las preguntas, solo las que cambian el resultado ──────────────────────
    P = []
    if not cols["numero_documento"]:
        P.append("¿El diario del cliente trae numero de factura o de documento? Si existe con "
                 "otro nombre, dime cual: es la señal que mas cancela y el extracto no la trae.")
    if r["aperturas_abiertas"]:
        # con la cuenta y el nombre: sin eso el auditor no puede ir a buscar el
        # mayor de nada, que es justo lo que se le esta pidiendo
        cuales = "; ".join(f"{c} {n} ({_eur(imp)})"
                           for c, n, imp in r["abiertas_detalle"][:6])
        if len(r["abiertas_detalle"]) > 6:
            cuales += f"; y {len(r['abiertas_detalle']) - 6} mas"
        P.append(f"Quedan {r['aperturas_abiertas']} apertura(s) sin cancelar por "
                 f"{_eur(r['importe_aperturas_abiertas'])}: {cuales}. ¿Hay mayor del ejercicio "
                 "anterior de esas cuentas, y donde esta? Con el se puede atar factura por "
                 "factura, y cerrar aperturas pagadas solo en parte.")
    if info["casi_cuadran"]:
        n = len(info["casi_cuadran"])
        cuales = "; ".join(f"{cta} doc. {fra} ({_eur(s)})"
                           for cta, fra, s, _ in info["casi_cuadran"][:4])
        if n > 4:
            cuales += f"; y {n - 4} mas"
        P.append(f"Hay {n} grupo(s) de un mismo documento que se quedan a menos de 5 centimos "
                 f"de cuadrar: {cuales}. ¿Se pueden barrer esas diferencias, y con que umbral? "
                 "Es materialidad y la decide el auditor: por defecto se quedan pendientes.")
    P.append("¿Como paga o cobra este cliente? Plazos (30/60/90), remesas que agrupan varias "
             "facturas, confirming, pagos parciales. Lo que digas cambia el tamaño de grupo "
             "que se busca.")
    if cols["numero_documento"]:
        P.append("¿El numero de documento se reutiliza entre ejercicios? Si se reutiliza, hay "
                 "que exigir ademas una ventana de fechas.")

    L += ["", "  PREGUNTAS AL AUDITOR antes de procesar:"]
    L += [f"    {i}. {q}" for i, q in enumerate(P, start=1)]
    if info["casi_cuadran"]:
        L += ["", "  los grupos que se quedan a un centimo:"]
        for cta, fra, s, n in info["casi_cuadran"][:10]:
            L.append(f"    cuenta {cta} · documento {fra} · {n} apuntes · descuadre {_eur(s)}")
        if len(info["casi_cuadran"]) > 10:
            L.append(f"    ... y {len(info['casi_cuadran']) - 10} mas")
    L += ["",
          "  NADA de esto se ha escrito en disco. Cuando el auditor conteste, se procesa."]
    return L


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entrada", required=True)
    args = p.parse_args()

    df = cargar_extracto(args.entrada)
    info = reconocer(df)
    for linea in _informe(info):
        print(linea)
    return 0


if __name__ == "__main__":
    sys.exit(main())
