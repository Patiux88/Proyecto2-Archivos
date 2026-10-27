# Índice primario guardado en JSON (indice.json)
# Relaciona cada id con su número de registro dentro de contactos.dat:
#   {"101": 0, "102": 1, "250": 2}
# Para buscar un id primero se consulta el índice y luego se hace
# seek(numero_registro * TAMANO_REGISTRO).

import json

from config import ARCHIVO_INDICE, ARCHIVO_CONTACTOS, CODIFICACION
from registros import leer_todos, preparar_carpeta


def guardar_indice(indice):
    preparar_carpeta()

    # JSON solo acepta claves de texto, por eso el id se guarda como str.
    datos = {str(id_contacto): numero for id_contacto, numero in sorted(indice.items())}

    with open(ARCHIVO_INDICE, "w", encoding=CODIFICACION) as archivo:
        json.dump(datos, archivo, indent=4)


def reconstruir_indice():
    # Recorre contactos.dat una vez y vuelve a crear el índice.
    indice = {}
    for numero, contacto in leer_todos():
        indice[contacto["id"]] = numero

    guardar_indice(indice)
    return indice


def cargar_indice():
    # Carga indice.json. Si no existe o está corrupto, se reconstruye.
    # Devuelve el índice y un mensaje (vacío si todo salió bien).
    try:
        with open(ARCHIVO_INDICE, "r", encoding=CODIFICACION) as archivo:
            datos = json.load(archivo)

        indice = {int(id_contacto): int(numero) for id_contacto, numero in datos.items()}
        return indice, ""

    except FileNotFoundError:
        # Si tampoco existe contactos.dat, la agenda simplemente está vacía.
        if not ARCHIVO_CONTACTOS.exists():
            return {}, ""
        mensaje = "No se encontró indice.json. Se creó de nuevo a partir de contactos.dat."

    except (json.JSONDecodeError, ValueError, AttributeError, UnicodeDecodeError):
        mensaje = "indice.json estaba corrupto. Se reconstruyó a partir de contactos.dat."

    indice = reconstruir_indice()
    return indice, mensaje
