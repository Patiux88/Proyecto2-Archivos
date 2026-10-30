# Exportación a JSON y generación del reporte PDF
# El PDF se genera a partir del JSON exportado (no directamente del .dat).
# Se usa reportlab, la misma librería de la actividad 20.

import json
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from config import ARCHIVO_JSON, ARCHIVO_PDF, CODIFICACION
from registros import leer_todos, preparar_carpeta


def exportar_json():
    # Lee todos los registros de contactos.dat y los guarda en un JSON.
    contactos = [contacto for numero, contacto in leer_todos()]
    contactos.sort(key=lambda contacto: contacto["id"])

    datos = {
        "fecha_exportacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_contactos": len(contactos),
        "contactos": contactos,
    }

    preparar_carpeta()
    with open(ARCHIVO_JSON, "w", encoding=CODIFICACION) as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

    return ARCHIVO_JSON, len(contactos)


# Reporte PDF

ANCHO, ALTO = letter
MARGEN = 40
AZUL = colors.HexColor("#1F3A5F")
GRIS_CLARO = colors.HexColor("#EEF1F5")

# Columnas de la tabla: (título, clave en el JSON, posición x, ancho)
COLUMNAS = [
    ("ID", "id", MARGEN + 5, 40),
    ("Nombre", "nombre", MARGEN + 45, 145),
    ("Teléfono", "telefono", MARGEN + 195, 75),
    ("Correo", "correo", MARGEN + 275, 160),
    ("Ciudad", "ciudad", MARGEN + 440, 90),
]


def recortar(texto, ancho, fuente, tamano):
    # Recorta el texto si no cabe en la columna.
    texto = str(texto)
    if stringWidth(texto, fuente, tamano) <= ancho:
        return texto
    while texto and stringWidth(texto + "...", fuente, tamano) > ancho:
        texto = texto[:-1]
    return texto + "..."


def generar_pdf():
    # Si el JSON no existe se exporta primero.
    if not ARCHIVO_JSON.exists():
        exportar_json()

    with open(ARCHIVO_JSON, "r", encoding=CODIFICACION) as archivo:
        datos = json.load(archivo)

    contactos = datos["contactos"]
    fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    pdf = canvas.Canvas(str(ARCHIVO_PDF), pagesize=letter)
    pdf.setTitle("Reporte de contactos")
    pagina = 1

    def pie_de_pagina():
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(MARGEN, 25, "Generado a partir de " + ARCHIVO_JSON.name)
        pdf.drawRightString(ANCHO - MARGEN, 25, f"Página {pagina}")

    def encabezado_tabla(y):
        pdf.setFillColor(AZUL)
        pdf.rect(MARGEN, y - 6, ANCHO - 2 * MARGEN, 20, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 9)
        for titulo, clave, x, ancho in COLUMNAS:
            pdf.drawString(x, y, titulo)
        return y - 20

    # Encabezado del reporte
    pdf.setFillColor(AZUL)
    pdf.rect(0, ALTO - 90, ANCHO, 90, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(MARGEN, ALTO - 45, "Agenda de Contactos")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(MARGEN, ALTO - 65,
                   "Universidad Rafael Landívar  |  Manejo e Implementación de Archivos")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(MARGEN, ALTO - 115, f"Fecha de generación: {fecha_generacion}")
    pdf.drawRightString(ANCHO - MARGEN, ALTO - 115, f"Total de contactos: {len(contactos)}")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.grey)
    pdf.drawString(MARGEN, ALTO - 128, f"Datos exportados el {datos['fecha_exportacion']}")

    y = ALTO - 160
    y = encabezado_tabla(y)

    if not contactos:
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawString(MARGEN + 5, y, "No hay contactos registrados.")

    for i, contacto in enumerate(contactos):

        # Si ya no cabe otra fila, se pasa a otra página
        if y < 60:
            pie_de_pagina()
            pdf.showPage()
            pagina += 1
            y = encabezado_tabla(ALTO - 60)

        # Filas alternas sombreadas
        if i % 2 == 0:
            pdf.setFillColor(GRIS_CLARO)
            pdf.rect(MARGEN, y - 6, ANCHO - 2 * MARGEN, 18, fill=1, stroke=0)

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 9)
        for titulo, clave, x, ancho in COLUMNAS:
            pdf.drawString(x, y, recortar(contacto[clave], ancho - 5, "Helvetica", 9))

        y -= 18

    pie_de_pagina()
    pdf.save()

    return ARCHIVO_PDF, len(contactos)
