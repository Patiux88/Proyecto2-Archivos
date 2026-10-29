# Lógica de la agenda: agregar, buscar por id y modificar contactos.
# Une el archivo de registros, el índice y el hash de integridad.
# Los errores se lanzan como ErrorAgenda para que la interfaz los muestre
# sin que la aplicación se cierre.

import re

from config import CAMPOS, ID_MAXIMO, CODIFICACION
from registros import (leer_registro, agregar_registro, modificar_registro,
                       validar_archivo, cantidad_registros)
from indice import cargar_indice, guardar_indice, reconstruir_indice
from integridad import guardar_hash


class ErrorAgenda(Exception):
    pass


# Largos de cada campo, para validar lo que escribe el usuario
LARGOS = dict(CAMPOS)


class Agenda:

    def __init__(self):
        self.indice = {}
        self.mensajes = []
        self.iniciar()

    def iniciar(self):
        # Carga el índice al abrir la aplicación y guarda los avisos para mostrarlos.
        self.mensajes = []

        problema = validar_archivo()
        if problema:
            self.mensajes.append(problema)

        try:
            self.indice, mensaje = cargar_indice()
            if mensaje:
                self.mensajes.append(mensaje)
        except PermissionError:
            self.mensajes.append("No hay permisos para leer o escribir el índice.")
        except (ValueError, OSError) as error:
            self.mensajes.append(f"No se pudo cargar el índice: {error}")

        # Si el índice no coincide con la cantidad de registros, se reconstruye.
        try:
            if len(self.indice) != cantidad_registros() and not problema:
                self.indice = reconstruir_indice()
                self.mensajes.append("El índice no coincidía con contactos.dat y se reconstruyó.")
        except (ValueError, OSError) as error:
            self.mensajes.append(f"No se pudo reconstruir el índice: {error}")

    # Validaciones

    def validar_id(self, texto):
        texto = str(texto).strip()
        if not texto.isdigit() or int(texto) <= 0:
            raise ErrorAgenda("El id debe ser un número entero mayor que 0.")
        if int(texto) > ID_MAXIMO:
            raise ErrorAgenda(f"El id no puede ser mayor que {ID_MAXIMO}.")
        return int(texto)

    def validar_datos(self, datos):
        contacto = {}

        for campo in ("nombre", "telefono", "correo", "ciudad"):
            valor = str(datos.get(campo, "")).strip()

            if valor == "":
                raise ErrorAgenda(f"El campo '{campo}' no puede estar vacío.")

            if "|" in valor or "\n" in valor:
                raise ErrorAgenda(f"El campo '{campo}' tiene caracteres no permitidos.")

            # El largo se mide en bytes porque así se guarda en el archivo
            if len(valor.encode(CODIFICACION)) > LARGOS[campo]:
                raise ErrorAgenda(f"El campo '{campo}' admite máximo {LARGOS[campo]} "
                                  f"caracteres (las letras con tilde cuentan doble).")
            contacto[campo] = valor

        if not re.fullmatch(r"[0-9+\- ]+", contacto["telefono"]):
            raise ErrorAgenda("El teléfono solo puede tener números, espacios, + o -.")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", contacto["correo"]):
            raise ErrorAgenda("El correo no tiene un formato válido (ejemplo: ana@correo.com).")

        return contacto

    # Operaciones

    def agregar(self, id_texto, datos):
        id_contacto = self.validar_id(id_texto)

        if id_contacto in self.indice:
            raise ErrorAgenda(f"Ya existe un contacto con el id {id_contacto}.")

        contacto = self.validar_datos(datos)
        contacto["id"] = id_contacto

        try:
            numero, movimiento = agregar_registro(contacto)

            # El índice se actualiza cada vez que se agrega un contacto
            self.indice[id_contacto] = numero
            guardar_indice(self.indice)

            # Se guarda el hash después de cada cambio
            guardar_hash()

        except PermissionError:
            raise ErrorAgenda("No hay permisos para escribir en contactos.dat.")
        except (ValueError, OSError) as error:
            raise ErrorAgenda(f"No se pudo guardar el contacto: {error}")

        return contacto, movimiento

    def buscar(self, id_texto):
        id_contacto = self.validar_id(id_texto)

        # Primero se consulta el índice
        if id_contacto not in self.indice:
            raise ErrorAgenda(f"No existe ningún contacto con el id {id_contacto}.")

        numero = self.indice[id_contacto]

        # Luego se hace seek() directo al registro
        try:
            contacto, movimiento = leer_registro(numero)
        except FileNotFoundError:
            raise ErrorAgenda("No se encontró el archivo contactos.dat.")
        except PermissionError:
            raise ErrorAgenda("No hay permisos para leer contactos.dat.")
        except ValueError:
            raise ErrorAgenda(f"El registro #{numero} está dañado o incompleto.")

        if contacto["id"] != id_contacto:
            raise ErrorAgenda("El índice no coincide con el archivo de contactos. "
                              "Puede que contactos.dat haya sido modificado.")

        movimiento = f"Índice: id {id_contacto} -> registro #{numero}. " + movimiento
        return contacto, movimiento

    def modificar(self, id_texto, datos):
        # Se busca primero para comprobar que existe y que el registro está bien
        contacto_actual, _ = self.buscar(id_texto)

        contacto = self.validar_datos(datos)
        contacto["id"] = contacto_actual["id"]
        numero = self.indice[contacto["id"]]

        try:
            movimiento = modificar_registro(numero, contacto)
            guardar_hash()
        except PermissionError:
            raise ErrorAgenda("No hay permisos para modificar contactos.dat.")
        except OSError as error:
            raise ErrorAgenda(f"No se pudo modificar el contacto: {error}")

        return contacto, movimiento

    def total(self):
        return len(self.indice)
