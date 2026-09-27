# -*- coding: utf-8 -*-
"""Valida el dígito de control de un identificador fiscal español.

Distingue CIF de persona jurídica, DNI y NIE, y valida el control de los tres.
La investigación de entidades solo aplica a personas jurídicas (CIF): el skill
usa el campo `tipo` para pararse si le llega un identificador de persona física.

Salida: un JSON por stdout. Código de salida 0 si el control es válido,
2 si no lo es o el formato no se reconoce (el skill PARA: investigar un CIF
mal tecleado produce un informe sobre otra entidad).
"""

import argparse
import json
import re
import sys

# Letras iniciales admitidas en un CIF de persona jurídica (RD 1065/2007).
LETRAS_CIF = "ABCDEFGHJNPQRSUVW"

# El control es LETRA para organismos públicos y entidades sin forma mercantil,
# y DÍGITO para las formas societarias clásicas. Para el resto valen los dos.
CONTROL_SOLO_LETRA = "PQRSNW"
CONTROL_SOLO_DIGITO = "ABEH"

# Tabla oficial: el dígito de control 0..9 se corresponde con esta letra.
LETRAS_CONTROL_CIF = "JABCDEFGHI"

# Tabla oficial del DNI/NIE: letra = número % 23.
LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"


def normalizar(texto):
    """Quita espacios, guiones y puntos y pasa a mayúsculas."""
    return re.sub(r"[\s\-.]", "", texto or "").upper()


def _control_cif(siete_digitos):
    """Calcula el dígito de control de un CIF a partir de sus 7 dígitos."""
    suma = 0
    for i, caracter in enumerate(siete_digitos):
        digito = int(caracter)
        if i % 2 == 0:  # posiciones impares 1,3,5,7 (índice 0,2,4,6): se duplican
            doble = digito * 2
            suma += doble - 9 if doble > 9 else doble
        else:  # posiciones pares 2,4,6: se suman tal cual
            suma += digito
    return (10 - suma % 10) % 10


def validar(identificador):
    """Devuelve (tipo, valido, motivo) para un identificador ya normalizado."""
    if re.fullmatch(r"[0-9]{8}[A-Z]", identificador):
        numero, letra = int(identificador[:8]), identificador[8]
        ok = LETRAS_DNI[numero % 23] == letra
        return "dni", ok, None if ok else "la letra de control no corresponde"

    if re.fullmatch(r"[XYZ][0-9]{7}[A-Z]", identificador):
        # El prefijo del NIE se sustituye por su dígito antes del módulo 23.
        numero = int(str("XYZ".index(identificador[0])) + identificador[1:8])
        ok = LETRAS_DNI[numero % 23] == identificador[8]
        return "nie", ok, None if ok else "la letra de control no corresponde"

    if re.fullmatch(r"[A-Z][0-9]{7}[0-9A-J]", identificador):
        inicial, digitos, control = identificador[0], identificador[1:8], identificador[8]
        if inicial not in LETRAS_CIF:
            return "cif", False, "la letra inicial %s no es de un CIF válido" % inicial
        esperado = _control_cif(digitos)
        letra_esperada = LETRAS_CONTROL_CIF[esperado]
        if inicial in CONTROL_SOLO_LETRA:
            ok = control == letra_esperada
        elif inicial in CONTROL_SOLO_DIGITO:
            ok = control == str(esperado)
        else:
            ok = control in (str(esperado), letra_esperada)
        return "cif", ok, None if ok else "el carácter de control no corresponde"

    return "desconocido", False, "el formato no es CIF, DNI ni NIE"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cif", required=True, help="identificador a validar")
    argumentos = parser.parse_args()

    identificador = normalizar(argumentos.cif)
    tipo, valido, motivo = validar(identificador)
    print(json.dumps({
        "identificador": identificador,
        "tipo": tipo,
        "valido": valido,
        "motivo": motivo,
        "es_persona_juridica": tipo == "cif" and valido,
    }, ensure_ascii=False, allow_nan=False))
    return 0 if valido else 2


if __name__ == "__main__":
    sys.exit(main())
