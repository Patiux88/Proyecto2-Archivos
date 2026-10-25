# Manejo del archivo de registros de tamaño fijo (contactos.dat)
# Aquí está el acceso aleatorio: seek() para ubicarse en un registro
# y tell() para saber en qué posición del archivo estamos.
#
# El archivo se abre en modo binario ("rb", "ab", "rb+") porque seek()
# trabaja con bytes. Si se abriera en modo texto:
# - en Windows el "\n" se guardaría como "\r\n" (101 bytes en vez de 100)
# - una letra con tilde o una ñ ocupa 2 bytes en UTF-8
# y los registros dejarían de medir lo mismo. Por eso cada campo se
# convierte a bytes UTF-8 y se rellena con espacios usando ljust().

from config import ARCHIVO_CONTACTOS, CAMPOS, TAMANO_REGISTRO, CODIFICACION, CARPETA_DATOS


def formatear_campo(texto, largo):
    # Convierte el texto a bytes UTF-8 y lo rellena con espacios hasta su largo.
    texto = str(texto).strip().replace("\n", " ").replace("\r", " ")
    datos = texto.encode(CODIFICACION)

    # Si el texto es más largo que el campo, se recorta letra por letra
    # (así no se corta una letra con tilde a la mitad).
    while len(datos) > largo:
        texto = texto[:-1]
        datos = texto.encode(CODIFICACION)

    return datos.ljust(largo, b" ")


def crear_registro(contacto):
    # Une todos los campos del contacto en un registro de TAMANO_REGISTRO bytes.
    registro = b""
    for campo, largo in CAMPOS:
        registro += formatear_campo(contacto[campo], largo)
    registro += b"\n"
    return registro


def separar_registro(datos):
    # Convierte los bytes de un registro en un diccionario con sus campos.
    if len(datos) != TAMANO_REGISTRO:
        raise ValueError("El registro está incompleto (el archivo puede estar corrupto).")

    contacto = {}
    inicio = 0
    for campo, largo in CAMPOS:
        contacto[campo] = datos[inicio:inicio + largo].decode(CODIFICACION).strip()
        inicio += largo

    contacto["id"] = int(contacto["id"])
    return contacto


def preparar_carpeta():
    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)


def cantidad_registros():
    # Como todos los registros miden lo mismo:
    # cantidad = tamaño del archivo / tamaño del registro
    if not ARCHIVO_CONTACTOS.exists():
        return 0
    return ARCHIVO_CONTACTOS.stat().st_size // TAMANO_REGISTRO


def validar_archivo():
    # Revisa que el tamaño del archivo sea múltiplo del tamaño del registro.
    # Devuelve None si está bien, o un mensaje con el problema.
    if not ARCHIVO_CONTACTOS.exists():
        return None

    tamano = ARCHIVO_CONTACTOS.stat().st_size
    if tamano % TAMANO_REGISTRO != 0:
        return (f"El archivo mide {tamano} bytes y no es múltiplo de "
                f"{TAMANO_REGISTRO}. Puede estar corrupto.")
    return None


def leer_registro(numero):
    # Lee el registro número "numero" sin recorrer el archivo.
    # Devuelve el contacto y la información de posiciones (seek / tell).
    posicion = numero * TAMANO_REGISTRO

    with open(ARCHIVO_CONTACTOS, "rb") as archivo:

        # Nos movemos directamente al inicio del registro.
        archivo.seek(posicion)
        posicion_inicio = archivo.tell()

        # Leemos solamente ese registro.
        datos = archivo.read(TAMANO_REGISTRO)
        posicion_final = archivo.tell()

    contacto = separar_registro(datos)

    movimiento = (f"Registro #{numero}: seek({posicion}) -> tell() = {posicion_inicio}; "
                  f"read({TAMANO_REGISTRO}) -> tell() = {posicion_final}")
    return contacto, movimiento


def agregar_registro(contacto):
    # Escribe un registro nuevo al final del archivo.
    # Devuelve el número de registro donde quedó guardado.
    preparar_carpeta()
    registro = crear_registro(contacto)

    with open(ARCHIVO_CONTACTOS, "ab") as archivo:

        # Nos ubicamos al final para saber dónde empieza el nuevo registro.
        archivo.seek(0, 2)
        posicion = archivo.tell()

        # Si el final no coincide con un inicio de registro, el archivo está dañado.
        if posicion % TAMANO_REGISTRO != 0:
            raise ValueError("El archivo de contactos no tiene registros completos.")

        numero = posicion // TAMANO_REGISTRO
        archivo.write(registro)
        posicion_final = archivo.tell()

    movimiento = (f"Nuevo registro #{numero}: seek(0, 2) -> tell() = {posicion}; "
                  f"write({TAMANO_REGISTRO}) -> tell() = {posicion_final}")
    return numero, movimiento


def modificar_registro(numero, contacto):
    # Sobrescribe SOLO el registro indicado; el resto del archivo no se toca.
    registro = crear_registro(contacto)
    posicion = numero * TAMANO_REGISTRO

    # "rb+" abre para leer y escribir sin borrar el contenido del archivo.
    with open(ARCHIVO_CONTACTOS, "rb+") as archivo:

        archivo.seek(posicion)
        posicion_inicio = archivo.tell()

        archivo.write(registro)
        posicion_final = archivo.tell()

    movimiento = (f"Registro #{numero} modificado en el lugar: seek({posicion}) -> "
                  f"tell() = {posicion_inicio}; write({TAMANO_REGISTRO}) -> tell() = {posicion_final}")
    return movimiento


def leer_todos():
    # Recorre el archivo completo (se usa para exportar y para reconstruir el índice).
    # Devuelve una lista de tuplas (numero_registro, contacto).
    contactos = []

    if not ARCHIVO_CONTACTOS.exists():
        return contactos

    with open(ARCHIVO_CONTACTOS, "rb") as archivo:
        numero = 0
        while True:
            datos = archivo.read(TAMANO_REGISTRO)
            if not datos:
                break
            contactos.append((numero, separar_registro(datos)))
            numero += 1

    return contactos
