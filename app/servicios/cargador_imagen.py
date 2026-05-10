from pathlib import Path
import numpy as np
import cv2


# Una imagen en escala de grises puede ser un solo canal o una imagen
# en escala de grises guardada como BGR/BGRA de 3/4 canales.

# Validar condiciones para cargar imagen

def es_formato_jpg(ruta_archivo: str) -> bool:
    return Path(ruta_archivo).suffix.lower() in {".jpg", ".jpeg"}

def es_escala_grises(imagen: np.ndarray, tolerancia: int = 5) -> bool:
    if imagen is None:
        return False

    # Si el ndarray tiene dos dimensiones, la imagen está en escala de grises.
    if imagen.ndim == 2:
        return True

    # Si el ndarray tiene tres dimensiones, vemos la similitud entre sus canales de color.
    if imagen.ndim == 3:
        # Descompone el 3darray en tres 2darrays con sus valores de color.
        # Con el split en 3 tomamos sólo los canales de color, ignorando un posible canal Alpha.
        b, g, r = cv2.split(imagen[:, :, :3])

        # Calcula la diferencia absoluta pixel a pixel entre los canales.
        diff_bg = cv2.absdiff(b, g)
        diff_gr = cv2.absdiff(g, r)

        # Busca el máximo valor encontrado y lo compara con la tolerancia.
        return diff_bg.max() <= tolerancia and diff_gr.max() <= tolerancia

    return False


# Cargar imagen

def cargar_imagen_desde_ruta(ruta_imagen: str):
    ruta_path = Path(ruta_imagen)

    if not es_formato_jpg(ruta_imagen):
        return {
            "exito": False,
            "error": "Formato inválido. Solo se aceptan imágenes JPG o JPEG.",
            "imagen": None,
            "ruta": ruta_imagen,
        }

    imagen = cv2.imread(ruta_imagen, cv2.IMREAD_UNCHANGED)

    if imagen is None:
        return {
            "exito": False,
            "error": "No se pudo cargar la imagen seleccionada.",
            "imagen": None,
            "ruta": ruta_imagen,
        }

    if not es_escala_grises(imagen):
        return {
            "exito": False,
            "error": "La imagen no está en escala de grises.",
            "imagen": None,
            "ruta": ruta_imagen,
        }

    if imagen.ndim == 3:
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    else:
        imagen_gris = imagen

    return {
        "exito": True,
        "error": None,
        "imagen": imagen_gris,
        "ruta": ruta_imagen,
    }
