"""Comprueba que el emparejamiento hace lo que tiene que hacer, con un
fixture sintetico -- no hace falta Gesia ni ningun .smn real para ejecutar
esto.

    python probar_cancelacion.py

Ocho cuentas de prueba: una por procedimiento, una que combina dos, y tres
de punteo previo (la columna Indice que traen muchos .smn):

  9999901  2.1 -- toda la cuenta suma 0
  9999902  2.2 -- el total coincide con el ultimo apunte cronologico
  9999903  2.3 -- solo pareo directo, con un apunte suelto sin cancelar
  9999904  2.3 + 2.4 secuencial -- una apertura que solo se cancela
           acumulando tres pagos del mismo dia (como paso de verdad en
           una cuenta de clientes del expediente de calibracion), mas un
           pareo directo aparte y un apunte suelto
  9999905  2.4 combinatorio -- tres apuntes de importes distintos que
           solo cancelan si se combinan SIN ser contiguos en el tiempo
           (nunca hay un tramo cronologico continuo que sume 0), mas dos
           apuntes que quedan sin cancelar
  9999906  punteo previo parcial -- un par ya punteado en contabilidad
           (indice 3) que se respeta tal cual, mas un par sin puntear que
           el skill cancela con un indice NUEVO por encima del previo
  9999907  punteo previo descuadrado -- un grupo previo que NO suma 0:
           se respeta (no se toca), se reporta como descuadre, y la
           verificacion estructural sigue cuadrando
  9999908  punteo previo completo -- todo punteado: el skill no añade
           ningun grupo y no toca nada

Por que hace falta: en una cuenta sin nada que cancelar, un emparejador
roto y uno correcto pueden dar el mismo resultado (todo en INDICE 0). Que
una cuenta salga limpia no demuestra que esto funcione; hace falta un
caso con respuesta conocida.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_cancelacion import (  # noqa: E402
    ORIGEN_AUDITORIA,
    ORIGEN_CONTABLE,
    asignar_indices_cuenta,
    verificar_cuenta,
)


def _df(filas, con_punteo=False):
    cols = ["FECHA", "CUENTA", "NOMBRE", "CONCEPTO", "SALDO"]
    if con_punteo:
        cols.append("INDICE_PREVIO")
    d = pd.DataFrame(filas, columns=cols)
    d["FECHA"] = pd.to_datetime(d["FECHA"])
    d["SALDO"] = d["SALDO"].astype(float)
    return d


FIXTURES = {
    "9999901": _df([
        ("2024-01-05", "9999901", "Cliente Uno", "Fra 1", 100.00),
        ("2024-02-10", "9999901", "Cliente Uno", "Pago 1", -60.00),
        ("2024-03-01", "9999901", "Cliente Uno", "Pago 2", -40.00),
    ]),
    "9999902": _df([
        ("2024-01-01", "9999902", "Cliente Dos", "Apertura", 500.00),
        ("2024-01-10", "9999902", "Cliente Dos", "Pago apertura", -500.00),
        ("2024-06-01", "9999902", "Cliente Dos", "Fra pendiente", 200.00),
    ]),
    "9999903": _df([
        ("2024-01-01", "9999903", "Cliente Tres", "Fra A", 300.00),
        ("2024-01-05", "9999903", "Cliente Tres", "Pago A", -300.00),
        ("2024-01-10", "9999903", "Cliente Tres", "Fra Suelta", 90.00),
        ("2024-02-01", "9999903", "Cliente Tres", "Fra B", 150.00),
        ("2024-02-05", "9999903", "Cliente Tres", "Pago B", -150.00),
    ]),
    "9999904": _df([
        ("2024-01-01", "9999904", "Cliente Cuatro", "Apertura", 1000.00),
        ("2024-01-15", "9999904", "Cliente Cuatro", "Pago 1", -400.00),
        ("2024-01-15", "9999904", "Cliente Cuatro", "Pago 2", -350.00),
        ("2024-01-15", "9999904", "Cliente Cuatro", "Pago 3", -250.00),
        ("2024-03-01", "9999904", "Cliente Cuatro", "Fra Suelta", 75.00),
        ("2024-04-01", "9999904", "Cliente Cuatro", "Fra D", 200.00),
        ("2024-04-10", "9999904", "Cliente Cuatro", "Pago D", -200.00),
    ]),
    "9999905": _df([
        ("2024-01-01", "9999905", "Cliente Cinco", "M1", 200.00),
        ("2024-01-05", "9999905", "Cliente Cinco", "N1 (ruido)", 90.00),
        ("2024-01-10", "9999905", "Cliente Cinco", "M2", 150.00),
        ("2024-01-15", "9999905", "Cliente Cinco", "N2 (ruido)", -60.00),
        ("2024-01-20", "9999905", "Cliente Cinco", "M3", -350.00),
        ("2024-01-25", "9999905", "Cliente Cinco", "Pendiente", 500.00),
    ]),
    # Punteo previo parcial: el par punteado lleva el indice 3 (numeracion
    # del cliente, con huecos: no hay 1 ni 2). El skill tiene que numerar
    # sus grupos nuevos a partir del 4.
    "9999906": _df([
        ("2024-01-05", "9999906", "Cliente Seis", "Fra punteada", 300.00, 3),
        ("2024-01-20", "9999906", "Cliente Seis", "Pago punteado", -300.00, 3),
        ("2024-02-01", "9999906", "Cliente Seis", "Fra nueva", 120.00, 0),
        ("2024-02-15", "9999906", "Cliente Seis", "Pago nuevo", -120.00, 0),
        ("2024-03-01", "9999906", "Cliente Seis", "Fra pendiente", 80.00, 0),
    ], con_punteo=True),
    # Punteo previo descuadrado: el grupo 1 suma +50 (mal punteado en la
    # contabilidad). Se respeta, se reporta, y la conciliacion estructural
    # descuenta ese descuadre.
    "9999907": _df([
        ("2024-01-05", "9999907", "Cliente Siete", "Fra mal punteada", 400.00, 1),
        ("2024-01-20", "9999907", "Cliente Siete", "Pago mal punteado", -350.00, 1),
        ("2024-02-01", "9999907", "Cliente Siete", "Fra C", 90.00, 0),
        ("2024-02-15", "9999907", "Cliente Siete", "Pago C", -90.00, 0),
    ], con_punteo=True),
    # Punteo previo completo: nada que hacer.
    "9999908": _df([
        ("2024-01-05", "9999908", "Cliente Ocho", "Fra 1", 250.00, 1),
        ("2024-01-20", "9999908", "Cliente Ocho", "Cobro 1", -250.00, 1),
        ("2024-02-01", "9999908", "Cliente Ocho", "Fra 2", 130.00, 2),
        ("2024-02-15", "9999908", "Cliente Ocho", "Cobro 2", -130.00, 2),
    ], con_punteo=True),
    # Apertura que NO se puede cancelar: ningun subconjunto de los pagos da
    # exactamente su importe. Tiene que quedarse pendiente, no forzarse.
    "9999909": _df([
        ("2024-01-01", "9999909", "Cliente Nueve", "Apertura", 1000.00),
        ("2024-01-15", "9999909", "Cliente Nueve", "Pago 1", -400.00),
        ("2024-02-15", "9999909", "Cliente Nueve", "Pago 2", -350.00),
        ("2024-03-15", "9999909", "Cliente Nueve", "Fra tardia", 120.00),
    ]),
}


def _mismo_indice(res, conceptos):
    idx = res.set_index("CONCEPTO")["INDICE"]
    valores = {idx[c] for c in conceptos}
    return len(valores) == 1 and 0 not in valores


def _es_cero(res, concepto):
    idx = res.set_index("CONCEPTO")["INDICE"]
    return idx[concepto] == 0


def main() -> int:
    fallos = []

    # 9999901 -- 2.1: todo un mismo indice
    res, _ = asignar_indices_cuenta(FIXTURES["9999901"])
    if not _mismo_indice(res, ["Fra 1", "Pago 1", "Pago 2"]):
        fallos.append("9999901 (2.1): se esperaba un unico indice para las 3 filas")
    else:
        print("OK  9999901 (2.1): total=0, un solo grupo")

    # 9999902 -- 2.2: cancela todo menos el ultimo apunte cronologico
    res, _ = asignar_indices_cuenta(FIXTURES["9999902"])
    if not _mismo_indice(res, ["Apertura", "Pago apertura"]):
        fallos.append("9999902 (2.2): Apertura y Pago apertura deberian compartir indice")
    if not _es_cero(res, "Fra pendiente"):
        fallos.append("9999902 (2.2): Fra pendiente deberia quedar en INDICE 0")
    if not fallos or fallos[-1].startswith("9999901"):
        print("OK  9999902 (2.2): el ultimo apunte cronologico queda pendiente")

    # 9999903 -- 2.3: pareo directo, con un suelto
    res, _ = asignar_indices_cuenta(FIXTURES["9999903"])
    ok3 = _mismo_indice(res, ["Fra A", "Pago A"]) and _mismo_indice(res, ["Fra B", "Pago B"])
    if not ok3:
        fallos.append("9999903 (2.3): Fra A/Pago A y Fra B/Pago B deberian cancelar por pares")
    if not _es_cero(res, "Fra Suelta"):
        fallos.append("9999903 (2.3): Fra Suelta deberia quedar en INDICE 0")
    idxA = res.set_index("CONCEPTO")["INDICE"]["Fra A"]
    idxB = res.set_index("CONCEPTO")["INDICE"]["Fra B"]
    if idxA == idxB:
        fallos.append("9999903 (2.3): el par A y el par B no deberian compartir indice")
    if ok3 and _es_cero(res, "Fra Suelta") and idxA != idxB:
        print("OK  9999903 (2.3): dos pares directos, un suelto sin cancelar")

    # 9999904 -- 2.2b: la apertura la resuelve su propio paso, antes que nadie
    res, _ = asignar_indices_cuenta(FIXTURES["9999904"])
    grupo_ap = _mismo_indice(res, ["Apertura", "Pago 1", "Pago 2", "Pago 3"])
    marca_ap = res.set_index("CONCEPTO").loc[
        ["Apertura", "Pago 1", "Pago 2", "Pago 3"], "GRUPO_APERTURA"].all()
    parD = _mismo_indice(res, ["Fra D", "Pago D"])
    suelta_pendiente = _es_cero(res, "Fra Suelta")
    if not grupo_ap:
        fallos.append("9999904 (2.2b): Apertura+Pago1+Pago2+Pago3 deberian compartir indice")
    if not marca_ap:
        fallos.append("9999904 (2.2b): ese grupo deberia venir marcado GRUPO_APERTURA=True")
    if not parD:
        fallos.append("9999904 (2.3): Fra D / Pago D deberian cancelar por pareo directo")
    if not suelta_pendiente:
        fallos.append("9999904: Fra Suelta deberia quedar en INDICE 0")
    if grupo_ap and marca_ap and parD and suelta_pendiente:
        print("OK  9999904 (2.2b): la apertura se cancela en su propio paso, "
              "par directo aparte, un suelto pendiente")

    # 9999905 -- 2.4 combinatorio (no contiguo en el tiempo)
    res, _ = asignar_indices_cuenta(FIXTURES["9999905"])
    grupoM = _mismo_indice(res, ["M1", "M2", "M3"])
    marcaM = res.set_index("CONCEPTO").loc[["M1", "M2", "M3"], "GRUPO_24"].all()
    resto_pendiente = all(_es_cero(res, c) for c in ["N1 (ruido)", "N2 (ruido)", "Pendiente"])
    if not grupoM:
        fallos.append("9999905 (2.4 combinatorio): M1+M2+M3 deberian compartir indice")
    if not marcaM:
        fallos.append("9999905 (2.4 combinatorio): ese grupo deberia venir GRUPO_24=True")
    if not resto_pendiente:
        fallos.append("9999905: N1, N2 y Pendiente deberian quedar en INDICE 0")
    if grupoM and marcaM and resto_pendiente:
        print("OK  9999905 (2.4 combinatorio): M1/M2/M3 cancelan sin ser contiguos "
              "en fecha, el resto queda pendiente")

    # 9999906 -- punteo previo parcial: se respeta y se numera por encima
    res, _ = asignar_indices_cuenta(FIXTURES["9999906"])
    porc = res.set_index("CONCEPTO")
    ok = True
    if not (porc.loc["Fra punteada", "INDICE"] == 3
            and porc.loc["Pago punteado", "INDICE"] == 3):
        fallos.append("9999906 (punteo previo): el par punteado deberia conservar "
                      "su indice 3 tal cual")
        ok = False
    if not (porc.loc[["Fra punteada", "Pago punteado"], "ORIGEN"] == ORIGEN_CONTABLE).all():
        fallos.append("9999906 (punteo previo): el par punteado deberia venir con "
                      "ORIGEN contable")
        ok = False
    if not _mismo_indice(res, ["Fra nueva", "Pago nuevo"]):
        fallos.append("9999906 (punteo previo): Fra nueva / Pago nuevo deberian "
                      "cancelar con un indice nuevo")
        ok = False
    elif porc.loc["Fra nueva", "INDICE"] <= 3:
        fallos.append("9999906 (punteo previo): el indice nuevo deberia ser > 3 "
                      "(el maximo previo), y es "
                      + str(int(porc.loc["Fra nueva", "INDICE"])))
        ok = False
    if not (porc.loc[["Fra nueva", "Pago nuevo"], "ORIGEN"] == ORIGEN_AUDITORIA).all():
        fallos.append("9999906 (punteo previo): el par nuevo deberia venir con "
                      "ORIGEN auditoria")
        ok = False
    if not _es_cero(res, "Fra pendiente"):
        fallos.append("9999906 (punteo previo): Fra pendiente deberia quedar en INDICE 0")
        ok = False
    info = verificar_cuenta(res)
    if info["num_grupos_previos"] != 1 or info["num_grupos_nuevos"] != 1:
        fallos.append("9999906 (punteo previo): se esperaba 1 grupo previo y 1 nuevo, "
                      "y hay " + str(info["num_grupos_previos"]) + " / "
                      + str(info["num_grupos_nuevos"]))
        ok = False
    if ok:
        print("OK  9999906 (punteo previo parcial): el punteo se respeta, el skill "
              "completa con indices nuevos por encima del previo")

    # 9999907 -- punteo previo descuadrado: se respeta, se reporta, y la
    # verificacion estructural sigue cuadrando
    res, _ = asignar_indices_cuenta(FIXTURES["9999907"])
    porc = res.set_index("CONCEPTO")
    info = verificar_cuenta(res)
    ok = True
    if not (porc.loc["Fra mal punteada", "INDICE"] == 1
            and porc.loc["Pago mal punteado", "INDICE"] == 1):
        fallos.append("9999907 (descuadre previo): el grupo descuadrado deberia "
                      "conservar su indice 1 tal cual")
        ok = False
    if info["grupos_previos_descuadrados"] != {1: 50.0}:
        fallos.append("9999907 (descuadre previo): se esperaba reportar {1: 50.0} y "
                      "se reporta " + str(info["grupos_previos_descuadrados"]))
        ok = False
    if not info["coincide_total_con_no_cancelado"]:
        fallos.append("9999907 (descuadre previo): la conciliacion estructural "
                      "deberia cuadrar descontando el descuadre previo")
        ok = False
    if info["grupos_con_error"]:
        fallos.append("9999907 (descuadre previo): el descuadre es del punteo "
                      "previo, no deberia contarse como error del skill")
        ok = False
    if not _mismo_indice(res, ["Fra C", "Pago C"]):
        fallos.append("9999907 (descuadre previo): Fra C / Pago C deberian cancelar "
                      "por pareo directo igualmente")
        ok = False
    if ok:
        print("OK  9999907 (punteo previo descuadrado): se respeta, se reporta como "
              "descuadre, y la verificacion sigue cuadrando")

    # 9999908 -- punteo previo completo: el skill no toca nada
    res, _ = asignar_indices_cuenta(FIXTURES["9999908"])
    info = verificar_cuenta(res)
    ok = True
    if info["num_grupos_nuevos"] != 0:
        fallos.append("9999908 (punteo completo): el skill no deberia añadir grupos, "
                      "y añade " + str(info["num_grupos_nuevos"]))
        ok = False
    if info["num_grupos_previos"] != 2:
        fallos.append("9999908 (punteo completo): se esperaban 2 grupos previos y "
                      "hay " + str(info["num_grupos_previos"]))
        ok = False
    if (res["INDICE"] != res["INDICE_PREVIO"]).any():
        fallos.append("9999908 (punteo completo): los indices previos no deberian "
                      "cambiar")
        ok = False
    if ok:
        print("OK  9999908 (punteo previo completo): nada que añadir, nada tocado")

    # Verificacion estructural sobre todas las cuentas: para cada una, la
    # suma de INDICE=0 tiene que coincidir con el total de la cuenta menos
    # el descuadre de los grupos previos (0 si no hay punteo o esta bien).
    # 9999909 -- la apertura que no cuadra no se fuerza
    res, _ = asignar_indices_cuenta(FIXTURES["9999909"])
    ap_pendiente = _es_cero(res, "Apertura")
    nada_apertura = not res["GRUPO_APERTURA"].any()
    if not ap_pendiente:
        fallos.append("9999909 (2.2b): la apertura no cuadra con ningun subconjunto "
                      "y deberia quedar en INDICE 0, no forzarse")
    if not nada_apertura:
        fallos.append("9999909 (2.2b): no deberia haberse marcado ningun GRUPO_APERTURA")
    if ap_pendiente and nada_apertura:
        print("OK  9999909 (2.2b): una apertura que no cuadra se queda pendiente")

    for cuenta, datos in FIXTURES.items():
        res, _ = asignar_indices_cuenta(datos)
        info = verificar_cuenta(res)
        if not info["coincide_total_con_no_cancelado"] or info["grupos_con_error"]:
            fallos.append("verificacion " + cuenta + ": " + str(info))

    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  - " + f)
        return 1

    print("\nTodo detectado. El emparejador ve los nueve casos y las verificaciones cuadran.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
