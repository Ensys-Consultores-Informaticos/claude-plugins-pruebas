# -*- coding: utf-8 -*-
"""Arnes de fsp-mum. No necesita ForSampling ni un solo PDF.

Un fixture sintetico de ocho elementos de respuesta conocida, elegidos por lo
que puede salir mal en una MUM, que no es lo mismo que en una de cumplimiento:

  E1  gasto contabilizado por la BASE, documento que la sostiene  -> error 0
  E2  gasto por la base con diferencia real de 450,00             -> error y tasa
  E3  sin documento en la carpeta                                 -> sin medir
  E4  contabilizado por el TOTAL, documento que lo sostiene       -> error 0
  E5  INGRESO con saldo negativo y documento que lo sostiene      -> error 0
  E6  ingreso negativo con diferencia                             -> error negativo
  E7  documento sin total legible y libros con IVA                -> pista de IVA
  E8  sin importe en la poblacion                                 -> sin medir

Y las reglas que no se pueden romper: el termino de comparacion sale de la
propia muestra, los errores NO se netean, y lib_fsp.py es el mismo fichero que
en fsp-cumplimiento.

    python probar_mum.py        ->  0 si todo va bien, 1 si algo falla
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_fsp import columnas_de_muestra, cruzar, detectar_columnas, salida_utf8  # noqa: E402
from lib_mum import (  # noqa: E402
    comparar_con_auditor_mum,
    evaluar_mum,
    observacion_mum,
    recuento,
    termino_mayoritario,
)

MUESTRA = [
    {"GA1Poblacion_ID": "1", "Seleccionado": "True", "Repeticiones": "2", "Fecha": "13/03/25 0:00:00",
     "CuentaContable": "62300011", "DescripcinApunte": "OMICRON", "Saldo": "12500", "Acreedor": "OMICRON"},
    {"GA1Poblacion_ID": "2", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "26/02/25 0:00:00",
     "CuentaContable": "62300004", "DescripcinApunte": "ALFA", "Saldo": "4950,00", "Acreedor": "ALFA, Lda."},
    {"GA1Poblacion_ID": "3", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "03/04/25 0:00:00",
     "CuentaContable": "62900200", "DescripcinApunte": "SIN PAPELES", "Saldo": "3344,83", "Acreedor": "SIN PAPELES"},
    {"GA1Poblacion_ID": "4", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "06/05/25 0:00:00",
     "CuentaContable": "62700000", "DescripcinApunte": "GAMMA", "Saldo": "1210", "Acreedor": "GAMMA, S.L."},
    {"GA1Poblacion_ID": "5", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "30/07/25 0:00:00",
     "CuentaContable": "70000000", "DescripcinApunte": "CLIENTE UNO", "Saldo": "-5000", "Acreedor": "CLIENTE UNO, S.A."},
    {"GA1Poblacion_ID": "6", "Seleccionado": "True", "Repeticiones": "2", "Fecha": "01/09/25 0:00:00",
     "CuentaContable": "70000000", "DescripcinApunte": "CLIENTE DOS", "Saldo": "-8000", "Acreedor": "CLIENTE DOS, S.L."},
    {"GA1Poblacion_ID": "7", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "06/10/25 0:00:00",
     "CuentaContable": "62900000", "DescripcinApunte": "DELTA", "Saldo": "12100", "Acreedor": "DELTA SERVICIOS"},
    {"GA1Poblacion_ID": "8", "Seleccionado": "True", "Repeticiones": "1", "Fecha": "10/11/25 0:00:00",
     "CuentaContable": "62900000", "DescripcinApunte": "OMEGA", "Saldo": "", "Acreedor": "OMEGA"},
]

FACTURAS = [
    # E1: base 17.000 = saldo -> casa por base
    {"fichero": "1 - OMICRON 25-114.pdf", "proveedor": "OMICRON CONSULTORES", "numero": "25-114",
     "fecha": "13/03/2025", "base": "12500,00", "iva": "2625,00", "total": "15125,00"},
    # E2: la factura dice 4.500,00 y los libros 4.950,00
    {"fichero": "2 - ALFA FK25-00133.pdf", "proveedor": "ALFA, LDA.", "numero": "FA25/00042",
     "fecha": "25/02/2025", "base": "4500,00", "iva": "0,00", "total": "4500,00"},
    # E4: contabilizado por el total
    {"fichero": "4 - GAMMA 900.pdf", "proveedor": "GAMMA, S.L.", "numero": "900",
     "fecha": "05/05/2025", "base": "1000,00", "iva": "210,00", "total": "1210,00"},
    # E5: ingreso, el documento sostiene los 5.000
    {"fichero": "5 - CLIENTE UNO FV-31.pdf", "proveedor": "CLIENTE UNO, S.A.", "numero": "FV-31",
     "fecha": "30/07/2025", "base": "5000,00", "iva": "1050,00", "total": "6050,00"},
    # E6: ingreso, el documento dice 7.900 y los libros 8.000
    {"fichero": "6 - CLIENTE DOS FV-77.pdf", "proveedor": "CLIENTE DOS, S.L.", "numero": "FV-77",
     "fecha": "01/09/2025", "base": "7900,00", "iva": "1659,00", "total": "9559,00"},
    # E7: sin total legible; los libros llevan 12.100 = base + 21 %
    {"fichero": "7 - DELTA 5512.pdf", "proveedor": "DELTA SERVICIOS", "numero": "5512",
     "fecha": "06/10/2025", "base": "10000,00", "iva": "", "total": "", "notas": "total ilegible"},
]

EVALUACION_AUDITOR = [
    {"GA1Poblacion_ID": "1", "Saldo": "12500", "SaldoAuditoria": "12500", "ErrorAuditoria": "0",
     "GA1Poblacion_OBSERV": "Ok. Revisada factura de honorarios"},
    # el auditor SI vio el error de 450,00
    {"GA1Poblacion_ID": "2", "Saldo": "4950,00", "SaldoAuditoria": "4500,00", "ErrorAuditoria": "450",
     "GA1Poblacion_OBSERV": "Diferencia de 450,00 con la factura"},
    # y aqui puso un error que el skill no ve: es la cifra que importa
    {"GA1Poblacion_ID": "4", "Saldo": "1210", "SaldoAuditoria": "1000", "ErrorAuditoria": "210",
     "GA1Poblacion_OBSERV": "El apunte lleva el IVA, que no es gasto"},
]


def main() -> int:
    salida_utf8()
    fallos = 0

    def ok(cond: bool, texto: str) -> None:
        nonlocal fallos
        print(("OK   " if cond else "FALLA") + "  " + texto)
        if not cond:
            fallos += 1

    cols, _ = detectar_columnas(MUESTRA[0])
    ok(cols.get("importe") == "Saldo" and cols.get("id") == "GA1Poblacion_ID",
       "reconoce el importe y el id de una poblacion de MUM (GA1Poblacion_ID, Saldo)")
    ok(cols.get("tercero") in ("DescripcinApunte", "Acreedor"),
       "reconoce una columna de tercero aunque la poblacion no traiga numero de documento")

    cruce = cruzar(MUESTRA, FACTURAS, cols)
    ev = evaluar_mum(cruce, cols)
    for e in ev:
        e["observacion"] = observacion_mum(e)
    por_id = {e["fila"]["GA1Poblacion_ID"]: e for e in ev}
    e1, e2, e3, e4, e5, e6, e7, e8 = (por_id[str(i)] for i in range(1, 9))

    # -- el termino de comparacion sale de la muestra, no del plan contable
    ok(termino_mayoritario(cruce["filas"]) == "base",
       "el termino mayoritario de la muestra es la base: lo votan los elementos que casan")
    ok(termino_mayoritario([{"criterios": {"importe": "total"}}]) == "",
       "con un solo elemento casado no hay criterio: no se propone termino")
    ok(termino_mayoritario([{"criterios": {"importe": "total"}}, {"criterios": {"importe": "total"}},
                            {"criterios": {"importe": "base"}}, {"criterios": {"importe": "base"}}]) == "",
       "y con empate tampoco: lo decide el auditor")

    # -- los elementos
    ok(e1["error"] == 0.0 and e1["termino"] == "base" and e1["observacion"].startswith("Asistente IA: Ok."),
       "E1: gasto por la base que el documento sostiene -> error 0 y observacion Ok")
    ok(e2["saldo_auditoria"] == 4500.0 and e2["error"] == 450.0 and e2["tasa"] == 9.09,
       "E2: diferencia real -> saldo auditoria 4.500,00, error 450,00 y tasa 9,09 %")
    ok("4.500,00" in e2["observacion"] and "4.950,00" in e2["observacion"]
       and "de mas en libros" in e2["observacion"].replace("á", "a"),
       "E2: la observacion lleva las dos cifras y dice de que lado esta la diferencia")
    ok(e3["error"] is None and e3["saldo_auditoria"] is None and "no localizado" in e3["observacion"],
       "E3: sin documento no se inventa importe segun auditoria")
    ok(e4["error"] == 0.0 and e4["termino"] == "total",
       "E4: un elemento contabilizado por el total casa por el total aunque la muestra vaya por base")
    ok(e5["error"] == 0.0 and e5["saldo_auditoria"] == -5000.0,
       "E5: ingreso negativo -> el importe segun auditoria conserva el signo del saldo")
    ok(e6["saldo_auditoria"] == -7900.0 and e6["error"] == -100.0,
       "E6: ingreso con diferencia -> error = Saldo - SaldoAuditoria, con su signo")
    ok("de mas en libros" in e6["observacion"].replace("á", "a"),
       "E6: y la redaccion no se lia con el signo: compara magnitudes")
    ok(e7["error"] == 2100.0 and "IVA del 21 %" in e7["nota"],
       "E7: sin total legible, la diferencia es la cuota de IVA y se avisa de que puede ser criterio")
    ok(e8["error"] is None and "no trae importe" in e8["nota"],
       "E8: sin importe en la poblacion no hay nada que medir")

    # -- el recuento no netea NUNCA
    r = recuento(ev)
    ok(r["elementos"] == 8 and r["repeticiones"] == 10,
       "el recuento cuenta 8 elementos y 10 unidades de muestreo con las repeticiones")
    ok(r["n_exceso"] == 2 and r["suma_exceso"] == 2550.0 and r["n_defecto"] == 1 and r["suma_defecto"] == -100.0,
       "exceso y defecto van POR SEPARADO: 2 por exceso suman 2.550,00 y 1 por defecto -100,00")
    ok("neto" not in r and not any("neto" in k for k in r),
       "y no existe ninguna cifra de error neto: netear una MUM esconde las incorrecciones")
    ok(r["sin_medir"] == 2 and r["con_documento"] == 6,
       "dos elementos quedan sin medir y seis tienen documento")

    # -- comparacion con el auditor
    comp = comparar_con_auditor_mum(ev, EVALUACION_AUDITOR, cols)
    c = comp["recuento"]
    ok(c["coinciden"] == 2, "coincide con el auditor en los dos elementos que los dos midieron igual")
    ok(c["skill_cero_auditor_error"] == 1,
       "y detecta el caso peligroso: el skill da 0 donde el auditor puso un error de 210,00")
    ok(any(f["estado"].startswith("EL SKILL DA 0") and f["observacion_auditor"] for f in comp["filas"]),
       "arrastrando la observacion del auditor, que es donde esta el motivo")

    # -- el rotulo de la columna miente: se elige por el dato (caso medido 03/09/2026)
    VENTAS = [
        {"POBLACION_ID": "1", "Repeticiones": "1", "Fecha": "02/01/25 0:00:00", "Cuenta": "70000000",
         "Nombre": "Ventas", "Descripcin": "CLIENTE UNO, S.A.", "Saldo": "-5709", "Proveedores": "CLIENTE UNO, S.A."},
        {"POBLACION_ID": "2", "Repeticiones": "1", "Fecha": "28/03/25 0:00:00", "Cuenta": "70000000",
         "Nombre": "Ventas", "Descripcin": "ZETAFER CARIBE, S.L.", "Saldo": "-1500,00", "Proveedores": "ZETAFER CARIBE, S.L."},
        {"POBLACION_ID": "3", "Repeticiones": "1", "Fecha": "15/05/25 0:00:00", "Cuenta": "70000000",
         "Nombre": "Ventas", "Descripcin": "TERCERO TRES, S.A.", "Saldo": "-3200", "Proveedores": "TERCERO TRES, S.A."},
    ]
    F_VENTAS = [
        {"fichero": "2025000008 CLIENTE UNO.pdf", "proveedor": "CLIENTE UNO, S.A.", "numero": "2025000008",
         "fecha": "02/01/2025", "base": "5709,00", "iva": "1198,89", "total": "6907,89"},
        # el importe NO casa: la factura dice 1234,56 y los libros 1500,00
        {"fichero": "2025000042 ZETAFER CARIBE.pdf", "proveedor": "ZETAFER CARIBE, S.L.", "numero": "2025000042",
         "fecha": "28/03/2025", "base": "1234,56", "iva": "49,68", "total": "286,25"},
        {"fichero": "2025000900 TERCERO TRES.pdf", "proveedor": "TERCERO TRES, S.A.", "numero": "2025000900",
         "fecha": "15/05/2025", "base": "3200,00", "iva": "672,00", "total": "3872,00"},
    ]
    colv, _, avisos_col = columnas_de_muestra(VENTAS)
    ok(colv.get("tercero") == "Descripcin",
       "el tercero se elige por el dato: 'Nombre' vale 'Ventas' en todas las filas y no identifica a nadie")
    ok(any("identifica mucho mejor" in a for a in avisos_col),
       "y el cambio de columna se avisa, no se hace a escondidas")
    ok(detectar_columnas(VENTAS[0])[0].get("tercero") == "Nombre",
       "mirando solo la primera fila se elegiria 'Nombre': por eso hace falta la muestra entera")
    crv = cruzar(VENTAS, F_VENTAS, colv)
    evv = evaluar_mum(crv, colv)
    e_dif = next(e for e in evv if e["fila"]["POBLACION_ID"] == "2")
    ok(e_dif["factura"] is not None and e_dif["error"] == -265.44,
       "el elemento con diferencia real se localiza por tercero y fecha, y sale como error de 265,44")
    ok(not crv["facturas_sin_fila"] and not crv["candidatos_sueltos"],
       "no quedan ni elementos sin documento ni documentos sobrantes")

    # -- dos elementos del mismo tercero y fecha: el reparto no puede elegir a ciegas
    GEMELOS = [
        {"POBLACION_ID": "1", "Repeticiones": "1", "Fecha": "02/01/25 0:00:00", "Cuenta": "70000000",
         "Descripcin": "ZETAFER CARIBE, S.L.", "Saldo": "-1000"},
        {"POBLACION_ID": "2", "Repeticiones": "1", "Fecha": "02/01/25 0:00:00", "Cuenta": "70000000",
         "Descripcin": "ZETAFER CARIBE, S.L.", "Saldo": "-2000"},
    ]
    F_GEMELOS = [
        {"fichero": "A.pdf", "proveedor": "ZETAFER CARIBE, S.L.", "numero": "", "fecha": "02/01/2025",
         "base": "900,00", "iva": "189,00", "total": "1089,00"},
        {"fichero": "B.pdf", "proveedor": "ZETAFER CARIBE, S.L.", "numero": "", "fecha": "02/01/2025",
         "base": "1800,00", "iva": "378,00", "total": "2178,00"},
    ]
    colg, _, _ = columnas_de_muestra(GEMELOS)
    crg = cruzar(GEMELOS, F_GEMELOS, colg)
    ok(all(it["criterios"].get("ambiguo") for it in crg["filas"] if it["factura"]),
       "con dos candidatos empatados por tercero y fecha, la asignacion se marca AMBIGUA en vez de elegir en silencio")
    evg = evaluar_mum(crg, colg)
    for e in evg:
        e["observacion"] = observacion_mum(e)
    ok(all("ATENCIÓN" in e["observacion"] for e in evg),
       "y la observacion lo dice, que es lo que el auditor va a leer")

    # -- la salida de emergencia: atar el documento a mano
    F_ATADA = [dict(F_GEMELOS[1], poblacion_id="1")]
    cra = cruzar(GEMELOS, F_ATADA, colg)
    at = next(it for it in cra["filas"] if it["fila"]["POBLACION_ID"] == "1")
    ok(at["factura"] is not None and at["criterios"].get("declarado"),
       "un documento con poblacion_id se ata a ese elemento sin pasar por la puntuacion")
    eva = evaluar_mum(cra, colg)
    for e in eva:
        e["observacion"] = observacion_mum(e)
    ok("a mano" in next(e for e in eva if e["fila"]["POBLACION_ID"] == "1")["observacion"],
       "y el papel hace constar que el vinculo lo puso el auditor, no el cruce")

    # -- cuando de verdad no hay documento, se proponen las parejas candidatas
    SOLOS = [GEMELOS[0]]
    F_SOLOS = [{"fichero": "otro.pdf", "proveedor": "ZETAFER CARIBE, S.L.", "numero": "",
                "fecha": "20/06/2025", "base": "50,00", "iva": "10,50", "total": "60,50"}]
    crs = cruzar(SOLOS, F_SOLOS, columnas_de_muestra(SOLOS)[0])
    ok(len(crs["candidatos_sueltos"]) == 1 and crs["candidatos_sueltos"][0]["tercero"],
       "un elemento sin documento y un documento sobrante del mismo tercero salen como pareja candidata")


    # -- lotes para los lectores, y la fusion de lo que devuelven (agente lector)
    import json as _json, tempfile as _tf
    from pathlib import Path as _P
    from preparar_documentos import fusionar, repartir_lotes
    _t = _P(_tf.mkdtemp())
    (_t / "manifiesto.json").write_text(_json.dumps({"carpeta": "x", "ppp": 100, "apartados": [], "documentos": [
        {"id": "f01", "fichero": "a.pdf", "ruta": "x/a.pdf", "paginas": 1, "imagenes": ["x/f01_p1.png"]},
        {"id": "f02", "fichero": "b.pdf", "ruta": "x/b.pdf", "paginas": 2, "imagenes": ["x/f02_p1.png"]},
        {"id": "f03", "fichero": "c.pdf", "ruta": "x/c.pdf", "paginas": 1, "imagenes": ["x/f03_p1.png"]}]}), encoding="utf-8")
    (_t / "facturas.json").write_text(_json.dumps({"facturas": [{"fichero": "a.pdf", "total": "1,00"}]}), encoding="utf-8")
    _lotes = repartir_lotes(_t, 1)
    ok(len(_lotes) == 2 and [d["fichero"] for l in _lotes for d in l["documentos"]] == ["b.pdf", "c.pdf"],
       "los lotes solo llevan los documentos PENDIENTES: lo ya transcrito no se relee")
    ok(all(l["salida"].endswith(f"facturas_lote_{l['lote']}.json") for l in _lotes) and (_t / "lotes.json").exists(),
       "cada lote sabe donde tiene que dejar su resultado, y lotes.json queda escrito")
    (_t / "facturas_lote_1.json").write_text(_json.dumps({"facturas": [{"fichero": "b.pdf", "total": "2,00", "poblacion_id": "9"}]}), encoding="utf-8")
    (_t / "facturas_lote_2.json").write_text(_json.dumps({"facturas": [{"fichero": "c.pdf", "total": "3,00"},
                                                                       {"fichero": "z.pdf", "total": "9,00"}]}), encoding="utf-8")
    (_t / "facturas_lote_3.json").write_text("{esto no es json", encoding="utf-8")
    _r = fusionar(_t)
    _f = _json.loads((_t / "facturas.json").read_text(encoding="utf-8"))["facturas"]
    ok([x["fichero"] for x in _f] == ["a.pdf", "b.pdf", "c.pdf", "z.pdf"],
       "la fusion conserva lo que ya habia, anade los lotes en el orden del manifiesto y deja al final lo desconocido")
    ok(_r["faltan"] == [] and _r["sobran"] == ["z.pdf"],
       "y dice que sobra z.pdf, que ningun documento del inventario respalda")
    ok("poblacion_id" not in _f[1], "un lector no puede atar documentos a elementos: la fusion le quita poblacion_id")
    ok(_r["parciales"] == 3 and _r["entradas"] == 3, "un lote con JSON invalido se ignora avisando, sin tumbar la fusion")

    # -- la libreria compartida no puede derivar entre skills
    propia = Path(__file__).resolve().parent / "lib_fsp.py"
    hermana = Path(__file__).resolve().parents[2] / "fsp-cumplimiento" / "scripts" / "lib_fsp.py"
    if hermana.exists():
        h1 = hashlib.sha256(propia.read_bytes()).hexdigest()
        h2 = hashlib.sha256(hermana.read_bytes()).hexdigest()
        ok(h1 == h2, "lib_fsp.py es byte a byte el mismo que en fsp-cumplimiento (una sola fuente del cruce)")
    else:
        print("-      lib_fsp.py: sin la copia hermana al lado, no se comprueba la deriva (normal ya instalado)")

    print("\n" + ("RESULTADO: todo correcto" if not fallos else f"RESULTADO: {fallos} fallo(s)"))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
