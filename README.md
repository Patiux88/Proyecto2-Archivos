# Agenda de Contactos con Acceso Aleatorio

Laboratorio No. 2 - Manejo e Implementación de Archivos
Universidad Rafael Landívar, Campus de Quetzaltenango

Aplicación de escritorio en Python (Tkinter) que guarda una agenda de contactos
en un archivo de registros de tamaño fijo, con acceso aleatorio mediante
`seek()` y `tell()`, índice primario en JSON, exportación a JSON y PDF,
verificación de integridad con SHA-256 y respaldo comprimido en ZIP.

## Requisitos e instalación

- Python 3.10 o superior (Tkinter viene incluido en Windows)
- reportlab para el reporte PDF

```
pip install -r requirements.txt
python main.py
```

## Estructura del registro

Cada contacto ocupa exactamente **100 bytes** en `contactos.dat`.
Cada campo se rellena con espacios hasta su largo máximo usando `ljust()`.

| Campo       | Largo (bytes) |
|-------------|---------------|
| id          | 6             |
| nombre      | 28            |
| telefono    | 15            |
| correo      | 32            |
| ciudad      | 18            |
| salto línea | 1             |
| **Total**   | **100**       |

El largo se mide en bytes porque en UTF-8 una letra con tilde o una ñ ocupa
2 bytes. Por eso el archivo se abre en modo binario: así todos los registros
miden siempre 100 bytes, también en Windows.

Posición de un registro dentro del archivo:

```
posición = número de registro × 100
```

## Archivos que genera la aplicación (carpeta `datos`)

| Archivo                     | Contenido                                   |
|-----------------------------|---------------------------------------------|
| contactos.dat               | Registros de tamaño fijo                    |
| indice.json                 | Índice primario: id -> número de registro   |
| contactos.sha256            | Hash SHA-256 de contactos.dat               |
| contactos_exportados.json   | Exportación de todos los contactos          |
| reporte_contactos.pdf       | Reporte generado a partir del JSON          |
| respaldos/respaldo_*.zip    | Respaldo de contactos.dat e indice.json     |

## Módulos

| Archivo          | Función                                                       |
|------------------|---------------------------------------------------------------|
| main.py          | Punto de entrada                                              |
| config.py        | Rutas y estructura del registro                               |
| registros.py     | Registros de tamaño fijo, seek(), tell(), modificación en el lugar |
| indice.py        | Índice primario en JSON                                       |
| integridad.py    | Hash SHA-256                                                  |
| agenda.py        | Agregar, buscar por id y modificar, con validaciones          |
| exportar.py      | Exportación a JSON y reporte PDF                              |
| herramientas.py  | Respaldo ZIP e información del archivo (os.stat y os.access)  |
| interfaz.py      | Interfaz gráfica y menú principal                             |

## Menú principal

- **Contactos:** agregar, buscar por ID, modificar
- **Exportar:** exportar a JSON, generar reporte PDF
- **Herramientas:** verificar integridad, crear respaldo ZIP, información del archivo
- **Ayuda:** manual de usuario (simulado), estructura del registro, acerca de
