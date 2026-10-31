# Herramientas: respaldo comprimido en ZIP e información del archivo.

import os
import stat
import zipfile
from datetime import datetime

from config import (ARCHIVO_CONTACTOS, ARCHIVO_INDICE, CARPETA_RESPALDOS,
                    TAMANO_REGISTRO)


def porcentaje_reduccion(original, comprimido):
    if original == 0:
        return 0
    return (original - comprimido) / original * 100


def crear_respaldo_zip():
    # Crea un ZIP con contactos.dat e indice.json (como en la actividad 22).
    archivos = [ARCHIVO_CONTACTOS, ARCHIVO_INDICE]

    for ruta in archivos:
        if not ruta.exists():
            raise FileNotFoundError(f"No existe {ruta.name}. Agregue al menos un contacto.")

    CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)

    # El nombre lleva la fecha y hora para no reemplazar respaldos anteriores
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta_zip = CARPETA_RESPALDOS / f"respaldo_{fecha}.zip"

    contador = 2
    while ruta_zip.exists():
        ruta_zip = CARPETA_RESPALDOS / f"respaldo_{fecha}_{contador}.zip"
        contador += 1

    tamano_original = 0
    with zipfile.ZipFile(ruta_zip, "w", compression=zipfile.ZIP_DEFLATED) as archivo_zip:
        for ruta in archivos:
            archivo_zip.write(ruta, arcname=ruta.name)
            tamano_original += os.path.getsize(ruta)

    tamano_zip = os.path.getsize(ruta_zip)

    return {
        "ruta": ruta_zip,
        "archivos": [ruta.name for ruta in archivos],
        "original": tamano_original,
        "comprimido": tamano_zip,
        "reduccion": porcentaje_reduccion(tamano_original, tamano_zip),
    }


def informacion_archivo(ruta=ARCHIVO_CONTACTOS):
    # Metadatos y permisos con os.stat y os.access (como en la actividad 23).
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo {ruta.name} todavía no existe.")

    datos = os.stat(ruta)
    fecha = datetime.fromtimestamp(datos.st_mtime)

    informacion = {
        "nombre": ruta.name,
        "ruta": str(ruta),
        "tamano": datos.st_size,
        "modificacion": fecha.strftime("%d/%m/%Y %H:%M:%S"),
        "permisos": stat.filemode(datos.st_mode),
        "lectura": os.access(ruta, os.R_OK),
        "escritura": os.access(ruta, os.W_OK),
    }

    if ruta == ARCHIVO_CONTACTOS:
        informacion["registros"] = datos.st_size // TAMANO_REGISTRO
        informacion["tamano_registro"] = TAMANO_REGISTRO

    return informacion
