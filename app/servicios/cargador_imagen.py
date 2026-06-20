from pathlib import Path
# Path: librería estándar de Python para manejar rutas de archivos de forma
# orientada a objetos (en vez de usar strings y concatenarlos a mano).
# Permite cosas como sacar la extensión de un archivo fácilmente (.suffix)

import numpy as np
# NumPy: librería para manejar arrays numéricos de forma eficiente.
# Las imágenes, una vez cargadas, se representan como arrays (matrices) de números
# donde cada número es el valor de intensidad de un píxel.
# np.ndarray es el tipo de dato que usa OpenCV para representar imágenes.

import cv2
# OpenCV (cv2): librería especializada en procesamiento de imágenes/visión computacional.
# Aquí se usa para leer archivos de imagen, dividir canales de color,
# calcular diferencias entre canales, y convertir BGR a escala de grises.


# Una imagen en escala de grises puede ser un solo canal o una imagen
# en escala de grises guardada como BGR/BGRA de 3/4 canales.
# (Esto pasa porque a veces un jpg "se ve" en blanco y negro pero internamente
#  sigue guardando 3 canales de color con los mismos valores repetidos)

# Validar condiciones para cargar imagen

def es_formato_jpg(ruta_archivo: str) -> bool:
    # Convierte el string de ruta en un objeto Path para poder usar .suffix
    # .suffix devuelve la extensión del archivo (ej: ".jpg")
    # .lower() la pasa a minúsculas para que no falle si alguien sube ".JPG"
    # Se compara contra un set {".jpg", ".jpeg"} (sets son más rápidos para "in" que listas)
    return Path(ruta_archivo).suffix.lower() in {".jpg", ".jpeg"}

def es_escala_grises(imagen: np.ndarray, tolerancia: int = 5) -> bool:
    # tolerancia: margen de error permitido entre canales de color,
    # porque compresión JPG puede generar mínimas diferencias aunque la imagen
    # sea "visualmente" gris. Por defecto se permite una diferencia de hasta 5.

    if imagen is None:
        # Si cv2 no pudo leer el archivo, imagen viene como None
        return False

    # imagen.ndim = número de dimensiones del array.
    # Si el ndarray tiene dos dimensiones, la imagen está en escala de grises.
    if imagen.ndim == 2:
        # Una imagen con shape (alto, ancho) -- sin canal de color -- ya es gris pura
        return True

    # Si el ndarray tiene tres dimensiones, vemos la similitud entre sus canales de color.
    if imagen.ndim == 3:
        # shape sería (alto, ancho, canales) -- ej: BGR o BGRA

        # Descompone el 3darray en tres 2darrays con sus valores de color.
        # Con el split en 3 tomamos sólo los canales de color, ignorando un posible canal Alpha.
        # imagen[:, :, :3] = toma todas las filas, todas las columnas, y solo los primeros 3 canales
        # (descarta el canal Alpha/transparencia si existe, el 4to canal)
        # cv2.split separa el array en 3 arrays 2D: uno por canal (Blue, Green, Red)
        # OJO: OpenCV usa orden BGR, no RGB
        b, g, r = cv2.split(imagen[:, :, :3])

        # Calcula la diferencia absoluta pixel a pixel entre los canales.
        # cv2.absdiff resta los dos arrays y devuelve el valor absoluto de cada resta
        # Si la imagen es gris real, b, g y r deberían tener casi el mismo valor en cada píxel,
        # entonces la diferencia entre ellos debería ser ~0
        diff_bg = cv2.absdiff(b, g)
        diff_gr = cv2.absdiff(g, r)

        # Busca el máximo valor encontrado y lo compara con la tolerancia.
        # .max() recorre todo el array de diferencias y saca el valor más grande
        # Si incluso la diferencia máxima está dentro de la tolerancia, se considera gris
        return diff_bg.max() <= tolerancia and diff_gr.max() <= tolerancia

    # Si no es ni 2D ni 3D (caso raro/inválido), no se considera válida
    return False


# Cargar imagen

def cargar_imagen_desde_ruta(ruta_imagen: str):
    # Nota: ruta_path se crea pero no se usa después en la función (posible código sobrante)
    ruta_path = Path(ruta_imagen)

    # Primer filtro: validar extensión del archivo antes de gastar recursos leyéndolo
    if not es_formato_jpg(ruta_imagen):
        return {
            "exito": False,
            "error": "Formato inválido. Solo se aceptan imágenes JPG o JPEG.",
            "imagen": None,
            "ruta": ruta_imagen,
        }
    # Se retorna un diccionario como "respuesta estándar" de la función:
    # esto facilita que la UI sepa qué pasó sin necesidad de try/except en cada llamada

    # cv2.imread lee el archivo desde disco y lo convierte en un array de NumPy
    # IMREAD_UNCHANGED: carga la imagen tal cual está guardada (sin forzar conversión a color),
    # respetando si es 1, 3 o 4 canales, y conservando el canal Alpha si existe
    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_UNCHANGED)

    # Si la ruta era válida en extensión pero el archivo está corrupto o no existe,
    # cv2.imread devuelve None en vez de lanzar una excepción
    if imagen is None:
        return {
            "exito": False,
            "error": "No se pudo cargar la imagen seleccionada.",
            "imagen": None,
            "ruta": ruta_imagen,
        }

    # Segundo filtro: validar que sea realmente escala de grises (no solo por extensión)
    if not es_escala_grises(imagen):
        return {
            "exito": False,
            "error": "La imagen no está en escala de grises.",
            "imagen": None,
            "ruta": ruta_imagen,
        }

    # Si la imagen tiene 3 dimensiones (BGR/BGRA aunque sea "gris visualmente"),
    # se convierte formalmente a un solo canal para trabajar más liviano en el resto del programa
    if imagen.ndim == 3:
        # cv2.cvtColor cambia el espacio de color; aquí de BGR a escala de grises (1 canal)
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    else:
        # Si ya era 2D, no hace falta convertir, ya está en el formato correcto
        imagen_gris = imagen

    # Respuesta de éxito: se devuelve la imagen ya normalizada a un solo canal de grises
    return {
        "exito": True,
        "error": None,
        "imagen": imagen_gris,
        "ruta": ruta_imagen,
    }