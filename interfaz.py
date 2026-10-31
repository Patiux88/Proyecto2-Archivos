# Interfaz gráfica de la Agenda de Contactos (Tkinter)
# La interfaz solo llama a las funciones de los otros módulos y muestra
# los resultados; todo el manejo de archivos está en registros.py,
# indice.py, integridad.py, exportar.py y herramientas.py.

import json
import tkinter as tk
from tkinter import ttk, messagebox

from config import ARCHIVO_CONTACTOS, ARCHIVO_INDICE, TAMANO_REGISTRO, CAMPOS
from agenda import Agenda, ErrorAgenda
from registros import leer_todos
from integridad import verificar_integridad, guardar_hash
from exportar import exportar_json, generar_pdf
from herramientas import crear_respaldo_zip, informacion_archivo


class Aplicacion:

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Agenda de Contactos - Acceso Aleatorio")
        self.ventana.geometry("980x640")
        self.ventana.minsize(860, 560)

        self.agenda = None
        self.entradas = {}

        self.crear_menu()
        self.crear_formulario()
        self.crear_lista()
        self.crear_bitacora()
        self.crear_barra_estado()

        # Se carga la agenda y se revisa la integridad al iniciar
        self.ventana.after(200, self.revisar_al_iniciar)

    # Construcción de la ventana

    def crear_menu(self):
        barra = tk.Menu(self.ventana)

        menu_contactos = tk.Menu(barra, tearoff=0)
        menu_contactos.add_command(label="Agregar contacto", command=self.agregar)
        menu_contactos.add_command(label="Buscar por ID", command=self.buscar)
        menu_contactos.add_command(label="Modificar contacto", command=self.modificar)
        menu_contactos.add_separator()
        menu_contactos.add_command(label="Actualizar lista", command=self.actualizar_lista)
        menu_contactos.add_command(label="Limpiar formulario", command=self.limpiar)
        menu_contactos.add_separator()
        menu_contactos.add_command(label="Salir", command=self.ventana.destroy)
        barra.add_cascade(label="Contactos", menu=menu_contactos)

        menu_exportar = tk.Menu(barra, tearoff=0)
        menu_exportar.add_command(label="Exportar a JSON", command=self.exportar_json)
        menu_exportar.add_command(label="Generar reporte PDF", command=self.generar_pdf)
        barra.add_cascade(label="Exportar", menu=menu_exportar)

        menu_herramientas = tk.Menu(barra, tearoff=0)
        menu_herramientas.add_command(label="Verificar integridad", command=self.verificar)
        menu_herramientas.add_command(label="Crear respaldo ZIP", command=self.respaldo)
        menu_herramientas.add_command(label="Información del archivo", command=self.ventana_informacion)
        barra.add_cascade(label="Herramientas", menu=menu_herramientas)

        menu_ayuda = tk.Menu(barra, tearoff=0)
        menu_ayuda.add_command(label="Manual de usuario", command=self.ayuda_manual)
        menu_ayuda.add_command(label="Estructura del registro", command=self.ayuda_estructura)
        menu_ayuda.add_command(label="Acerca de", command=self.ayuda_acerca)
        barra.add_cascade(label="Ayuda", menu=menu_ayuda)

        self.ventana.config(menu=barra)

    def crear_formulario(self):
        marco = ttk.LabelFrame(self.ventana, text="Contacto", padding=10)
        marco.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        etiquetas = {
            "id": "ID",
            "nombre": "Nombre",
            "telefono": "Teléfono",
            "correo": "Correo",
            "ciudad": "Ciudad",
        }

        fila = 0
        for campo, largo in CAMPOS:
            ttk.Label(marco, text=f"{etiquetas[campo]} (máx. {largo}):").grid(
                row=fila, column=0, sticky="w", pady=3)
            entrada = ttk.Entry(marco, width=38)
            entrada.grid(row=fila, column=1, sticky="ew", pady=3)
            self.entradas[campo] = entrada
            fila += 1

        botones = ttk.Frame(marco)
        botones.grid(row=fila, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(botones, text="Agregar", command=self.agregar).grid(row=0, column=0, padx=3)
        ttk.Button(botones, text="Buscar por ID", command=self.buscar).grid(row=0, column=1, padx=3)
        ttk.Button(botones, text="Modificar", command=self.modificar).grid(row=0, column=2, padx=3)
        ttk.Button(botones, text="Limpiar", command=self.limpiar).grid(row=0, column=3, padx=3)

        # Enter en el campo ID hace la búsqueda
        self.entradas["id"].bind("<Return>", lambda evento: self.buscar())

    def crear_lista(self):
        marco = ttk.LabelFrame(self.ventana, text="Contactos guardados", padding=10)
        marco.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(10, 5))

        columnas = ("registro", "id", "nombre", "telefono", "correo", "ciudad")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=10)

        titulos = ["Reg.", "ID", "Nombre", "Teléfono", "Correo", "Ciudad"]
        anchos = [45, 60, 140, 90, 170, 100]
        for columna, titulo, ancho in zip(columnas, titulos, anchos):
            self.tabla.heading(columna, text=titulo)
            self.tabla.column(columna, width=ancho, anchor="w")

        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        # Al seleccionar una fila se busca ese id usando el índice
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)

    def crear_bitacora(self):
        marco = ttk.LabelFrame(self.ventana, text="Operaciones de archivo (seek / tell)", padding=10)
        marco.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.bitacora = tk.Text(marco, height=10, wrap="word", font=("Consolas", 9))
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.bitacora.yview)
        self.bitacora.configure(yscrollcommand=barra.set, state="disabled")

        self.bitacora.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        self.ventana.columnconfigure(1, weight=1)
        self.ventana.rowconfigure(0, weight=1)
        self.ventana.rowconfigure(1, weight=1)

    def crear_barra_estado(self):
        self.estado = ttk.Label(self.ventana, relief="sunken", anchor="w", padding=(8, 2))
        self.estado.grid(row=2, column=0, columnspan=2, sticky="ew")

    # Utilidades de la interfaz

    def escribir(self, texto):
        self.bitacora.configure(state="normal")
        self.bitacora.insert("end", texto + "\n")
        self.bitacora.see("end")
        self.bitacora.configure(state="disabled")

    def datos_formulario(self):
        return {campo: entrada.get() for campo, entrada in self.entradas.items()}

    def mostrar_contacto(self, contacto):
        for campo, entrada in self.entradas.items():
            entrada.delete(0, "end")
            entrada.insert(0, str(contacto[campo]))

    def limpiar(self):
        for entrada in self.entradas.values():
            entrada.delete(0, "end")
        self.entradas["id"].focus()

    def actualizar_estado(self):
        total = self.agenda.total() if self.agenda else 0
        self.estado.config(text=f"Contactos: {total}   |   Tamaño del registro: "
                                f"{TAMANO_REGISTRO} bytes   |   Archivo: {ARCHIVO_CONTACTOS.name}")

    def ejecutar(self, funcion):
        # Ejecuta una operación y muestra cualquier error sin cerrar la aplicación.
        try:
            return funcion()
        except ErrorAgenda as error:
            messagebox.showerror("Agenda", str(error))
        except PermissionError:
            messagebox.showerror("Permisos", "No hay permisos para acceder al archivo.")
        except FileNotFoundError as error:
            messagebox.showerror("Archivo no encontrado", str(error))
        except (json.JSONDecodeError, UnicodeDecodeError):
            messagebox.showerror("Archivo corrupto", "El archivo no tiene un formato válido.")
        except (ValueError, KeyError) as error:
            messagebox.showerror("Datos dañados", f"El archivo parece estar corrupto: {error}")
        except OSError as error:
            messagebox.showerror("Error de archivo", str(error))
        return None

    # Inicio

    def revisar_al_iniciar(self):
        self.agenda = self.ejecutar(Agenda)
        if self.agenda is None:
            return

        self.escribir(f"Aplicación iniciada. Cada registro mide {TAMANO_REGISTRO} bytes.")
        for mensaje in self.agenda.mensajes:
            self.escribir("Aviso: " + mensaje)
            messagebox.showwarning("Aviso", mensaje)

        self.revisar_integridad_inicio()
        self.actualizar_lista()
        self.actualizar_estado()

    def revisar_integridad_inicio(self):
        try:
            estado, mensaje, guardado, actual = verificar_integridad()
        except OSError as error:
            messagebox.showerror("Integridad", f"No se pudo verificar la integridad: {error}")
            return

        self.escribir("Integridad al iniciar: " + mensaje)

        if estado == "modificado":
            respuesta = messagebox.askyesno(
                "Integridad",
                mensaje + "\n\n"
                f"Hash guardado:\n{guardado}\n\nHash actual:\n{actual}\n\n"
                "¿Desea aceptar el archivo actual como válido y actualizar el hash?")
            if respuesta:
                guardar_hash()
                self.escribir("Se aceptó el archivo actual y se actualizó contactos.sha256.")

        elif estado == "sin_hash":
            respuesta = messagebox.askyesno(
                "Integridad", mensaje + "\n\n¿Desea registrar el hash actual?")
            if respuesta:
                guardar_hash()
                self.escribir("Se registró el hash actual en contactos.sha256.")

    # Contactos

    def agregar(self):
        if self.agenda is None:
            return

        def accion():
            contacto, movimiento = self.agenda.agregar(self.entradas["id"].get(), self.datos_formulario())
            self.escribir(movimiento)
            self.escribir(f"Contacto {contacto['id']} agregado. Índice y hash actualizados.")
            messagebox.showinfo("Agregar", f"Contacto {contacto['id']} guardado correctamente.")
            self.limpiar()
            self.actualizar_lista()
            self.actualizar_estado()

        self.ejecutar(accion)

    def buscar(self):
        if self.agenda is None:
            return

        def accion():
            contacto, movimiento = self.agenda.buscar(self.entradas["id"].get())
            self.mostrar_contacto(contacto)
            self.escribir(movimiento)

        self.ejecutar(accion)

    def modificar(self):
        if self.agenda is None:
            return

        def accion():
            contacto, movimiento = self.agenda.modificar(self.entradas["id"].get(), self.datos_formulario())
            self.escribir(movimiento)
            self.escribir(f"Contacto {contacto['id']} modificado. Solo se reescribió su registro.")
            messagebox.showinfo("Modificar", f"Contacto {contacto['id']} modificado correctamente.")
            self.actualizar_lista()

        self.ejecutar(accion)

    def actualizar_lista(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        def accion():
            for numero, contacto in leer_todos():
                self.tabla.insert("", "end", values=(
                    numero, contacto["id"], contacto["nombre"], contacto["telefono"],
                    contacto["correo"], contacto["ciudad"]))

        self.ejecutar(accion)

    def seleccionar_fila(self, evento):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0], "values")
        self.entradas["id"].delete(0, "end")
        self.entradas["id"].insert(0, valores[1])
        self.buscar()

    # Exportar

    def exportar_json(self):
        def accion():
            ruta, total = exportar_json()
            self.escribir(f"Exportados {total} contactos a {ruta.name}.")
            messagebox.showinfo("Exportar", f"Se exportaron {total} contactos a:\n{ruta}")

        self.ejecutar(accion)

    def generar_pdf(self):
        def accion():
            # Se exporta el JSON de nuevo para que el PDF tenga los datos actuales
            exportar_json()
            ruta, total = generar_pdf()
            self.escribir(f"Reporte PDF generado con {total} contactos: {ruta.name}.")
            messagebox.showinfo("Reporte PDF", f"Reporte generado a partir del JSON:\n{ruta}")

        self.ejecutar(accion)

    # Herramientas

    def verificar(self):
        def accion():
            estado, mensaje, guardado, actual = verificar_integridad()
            self.escribir("Verificación de integridad: " + mensaje)

            texto = mensaje
            if guardado or actual:
                texto += f"\n\nHash guardado:\n{guardado or '(no existe)'}\n\nHash actual:\n{actual}"

            if estado == "integro":
                messagebox.showinfo("Integridad", texto)
            else:
                messagebox.showwarning("Integridad", texto)

        self.ejecutar(accion)

    def respaldo(self):
        def accion():
            resultado = crear_respaldo_zip()
            texto = (f"Respaldo creado: {resultado['ruta'].name}\n"
                     f"Archivos incluidos: {', '.join(resultado['archivos'])}\n\n"
                     f"Tamaño original:   {resultado['original']} bytes\n"
                     f"Tamaño comprimido: {resultado['comprimido']} bytes\n"
                     f"Reducción:         {resultado['reduccion']:.2f}%")
            self.escribir(texto.replace("\n\n", "\n"))
            messagebox.showinfo("Respaldo ZIP", texto)

        self.ejecutar(accion)

    def ventana_informacion(self):
        ventana = tk.Toplevel(self.ventana)
        ventana.title("Información del archivo")
        ventana.resizable(False, False)

        fila = 0
        for ruta in (ARCHIVO_CONTACTOS, ARCHIVO_INDICE):
            ttk.Label(ventana, text=ruta.name, font=("Segoe UI", 11, "bold")).grid(
                row=fila, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 4))
            fila += 1

            try:
                informacion = informacion_archivo(ruta)
            except (FileNotFoundError, PermissionError, OSError) as error:
                ttk.Label(ventana, text=str(error)).grid(
                    row=fila, column=0, columnspan=2, sticky="w", padx=20)
                fila += 1
                continue

            datos = [
                ("Ruta:", informacion["ruta"]),
                ("Tamaño:", f"{informacion['tamano']} bytes"),
                ("Última modificación:", informacion["modificacion"]),
                ("Permisos:", informacion["permisos"]),
                ("Lectura:", "Sí" if informacion["lectura"] else "No"),
                ("Escritura:", "Sí" if informacion["escritura"] else "No"),
            ]
            if "registros" in informacion:
                datos.append(("Registros:", f"{informacion['registros']} "
                                            f"(de {informacion['tamano_registro']} bytes cada uno)"))

            for etiqueta, valor in datos:
                ttk.Label(ventana, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=20)
                ttk.Label(ventana, text=valor).grid(row=fila, column=1, sticky="w", padx=(0, 12))
                fila += 1

        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).grid(
            row=fila, column=0, columnspan=2, pady=12)

    # Ayuda (simulado)

    def ayuda_manual(self):
        messagebox.showinfo(
            "Manual de usuario",
            "Manual de usuario (simulado)\n\n"
            "1. Escriba los datos del contacto y presione Agregar.\n"
            "2. Escriba un ID y presione Buscar por ID.\n"
            "3. Busque un contacto, cambie sus datos y presione Modificar.\n"
            "4. En Exportar puede generar el JSON y el reporte PDF.\n"
            "5. En Herramientas puede verificar la integridad, crear un respaldo ZIP\n"
            "   y ver la información del archivo.")

    def ayuda_estructura(self):
        texto = "Estructura del registro\n\n"
        for campo, largo in CAMPOS:
            texto += f"{campo:<10} {largo:>3} bytes\n"
        texto += f"{'salto':<10} {1:>3} byte\n"
        texto += f"\nTotal: {TAMANO_REGISTRO} bytes por registro\n"
        texto += f"Posición de un registro = número de registro x {TAMANO_REGISTRO}"
        messagebox.showinfo("Estructura del registro", texto)

    def ayuda_acerca(self):
        messagebox.showinfo(
            "Acerca de",
            "Agenda de Contactos con Acceso Aleatorio\n"
            "Laboratorio No. 2 - Manejo e Implementación de Archivos\n"
            "Universidad Rafael Landívar, Campus de Quetzaltenango")


def iniciar():
    ventana = tk.Tk()
    Aplicacion(ventana)
    ventana.mainloop()
