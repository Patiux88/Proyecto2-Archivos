# Verificación de integridad con SHA-256
# Cada vez que la aplicación guarda un cambio se calcula el hash de
# contactos.dat y se guarda en contactos.sha256. Al iniciar se vuelve a
# calcular y se compara: si no coincide, el archivo se modificó fuera
# de la aplicación.

import hashlib

from config import ARCHIVO_CONTACTOS, ARCHIVO_HASH, CODIFICACION
from registros import preparar_carpeta


def calcular_hash(ruta):
    # SHA-256 leyendo por bloques (igual que en la actividad 21).
    sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        while True:
            bloque = archivo.read(4096)
            if not bloque:
                break
            sha256.update(bloque)

    return sha256.hexdigest()


def guardar_hash():
    # Calcula el hash actual de contactos.dat y lo guarda.
    preparar_carpeta()
    hash_actual = calcular_hash(ARCHIVO_CONTACTOS)

    with open(ARCHIVO_HASH, "w", encoding=CODIFICACION) as archivo:
        archivo.write(hash_actual + "\n")

    return hash_actual


def leer_hash_guardado():
    with open(ARCHIVO_HASH, "r", encoding=CODIFICACION) as archivo:
        return archivo.read().strip()


def verificar_integridad():
    # Devuelve (estado, mensaje, hash_guardado, hash_actual)
    # estado puede ser: "integro", "modificado", "sin_hash" o "sin_archivo"
    if not ARCHIVO_CONTACTOS.exists():
        return ("sin_archivo",
                "Todavía no existe contactos.dat (la agenda está vacía).",
                "", "")

    hash_actual = calcular_hash(ARCHIVO_CONTACTOS)

    try:
        hash_guardado = leer_hash_guardado()
    except FileNotFoundError:
        return ("sin_hash",
                "No existe contactos.sha256, no se puede comprobar la integridad.",
                "", hash_actual)

    if hash_guardado == hash_actual:
        return ("integro",
                "ÍNTEGRO: el archivo no ha sido modificado fuera de la aplicación.",
                hash_guardado, hash_actual)

    return ("modificado",
            "ALERTA: contactos.dat fue modificado fuera de la aplicación.",
            hash_guardado, hash_actual)
