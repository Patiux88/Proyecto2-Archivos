# Configuración general de la Agenda de Contactos
# Aquí se definen las rutas de los archivos y la estructura del registro.

from pathlib import Path

# Carpeta donde se guardan los archivos que genera la aplicación
# (se crea junto a este archivo, dentro de "datos").
CARPETA_DATOS = Path(__file__).resolve().parent / "datos"
CARPETA_RESPALDOS = CARPETA_DATOS / "respaldos"

ARCHIVO_CONTACTOS = CARPETA_DATOS / "contactos.dat"
ARCHIVO_INDICE = CARPETA_DATOS / "indice.json"
ARCHIVO_HASH = CARPETA_DATOS / "contactos.sha256"
ARCHIVO_JSON = CARPETA_DATOS / "contactos_exportados.json"
ARCHIVO_PDF = CARPETA_DATOS / "reporte_contactos.pdf"

# Todos los archivos se leen y escriben en UTF-8
CODIFICACION = "utf-8"


# Estructura del registro de tamaño fijo
# Cada campo tiene un largo máximo en BYTES. Si el dato es más corto,
# se rellena con espacios hasta completar su largo.
#
#   Campo       Largo
#   id            6
#   nombre       28
#   telefono     15
#   correo       32
#   ciudad       18
#   salto línea   1   (\n al final, para que el archivo se pueda abrir en un editor)
#   TOTAL       100 bytes por registro
CAMPOS = [
    ("id", 6),
    ("nombre", 28),
    ("telefono", 15),
    ("correo", 32),
    ("ciudad", 18),
]

# Suma de los largos de los campos + 1 byte del salto de línea
TAMANO_REGISTRO = sum(largo for campo, largo in CAMPOS) + 1

# El id ocupa 6 posiciones, así que el mayor id permitido es 999999
ID_MAXIMO = 10 ** CAMPOS[0][1] - 1
