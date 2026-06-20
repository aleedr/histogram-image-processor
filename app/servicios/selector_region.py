import numpy as np


def seleccionar_region_de_procesamiento(imagen: np.ndarray, datos_grid: dict) -> np.ndarray:
    # Devuelve la imagen completa o la región seleccionada por el grid.
        # Si el grid estáa activo y existen coordenadas reales, recorta la imagen.
        # Si no, devuelve una copia de la imagen completa.

    if imagen is None:
        raise ValueError("No hay imagen cargada para procesar.")

    if imagen.ndim != 2:
        raise ValueError("La imagen debe estar en escala de grises y tener dos dimensiones.")

    grid_activo = datos_grid.get("activo")
    region_real = datos_grid.get("region_real")

    if not grid_activo or region_real is None:
        return imagen.copy()

    x = int(region_real["x"])
    y = int(region_real["y"])
    ancho = int(region_real["ancho"])
    alto = int(region_real["alto"])

    alto_imagen, ancho_imagen = imagen.shape

    x = max(0, min(x, ancho_imagen - 1))
    y = max(0, min(y, alto_imagen - 1))

    ancho = max(1, min(ancho, ancho_imagen - x))
    alto = max(1, min(alto, alto_imagen - y))

    region = imagen[y:y + alto, x:x + ancho]

    return region.copy()