import numpy as np
# NumPy: para slicing/recorte de la imagen como matriz


def seleccionar_region_de_procesamiento(imagen: np.ndarray, datos_grid: dict) -> np.ndarray:
    # Devuelve la imagen completa o la región seleccionada por el grid.
        # Si el grid está activo y existen coordenadas reales, recorta la imagen.
        # Si no, devuelve una copia de la imagen completa.

    # Esta función decide entre las dos opciones que mencionaste:
    # procesar la IMAGEN COMPLETA, o solo el "cuadrito" (grid/región) que el usuario eligió

    if imagen is None:
        raise ValueError("No hay imagen cargada para procesar.")

    # Mismo chequeo que en procesador_histograma.py: siempre se espera
    # imagen 2D (escala de grises pura, ya normalizada por cargador_imagen.py)
    if imagen.ndim != 2:
        raise ValueError("La imagen debe estar en escala de grises y tener dos dimensiones.")

    # datos_grid es un diccionario que viene de la UI (probablemente de panel_control.py
    # o de un widget donde el usuario dibuja/selecciona el cuadrito sobre la imagen)
    grid_activo = datos_grid.get("activo")
    # .get() en vez de datos_grid["activo"] evita un KeyError si la clave no existe,
    # simplemente devuelve None en ese caso

    region_real = datos_grid.get("region_real")
    # region_real esperaría ser un dict con x, y, ancho, alto: las coordenadas
    # reales en la imagen (no en píxeles de pantalla) del cuadrito seleccionado

    # Si el usuario NO activó el grid, o no hay coordenadas válidas seleccionadas,
    # se procesa la imagen completa (se hace .copy() para no modificar el original
    # por accidente cuando después se le aplique ecualización/expansión)
    if not grid_activo or region_real is None:
        return imagen.copy()

    # Si llegamos aquí: el grid SÍ está activo y hay una región definida.
    # Se extraen las coordenadas del cuadrito (convertidas a int por seguridad,
    # ya que pueden venir como floats desde la UI)
    x = int(region_real["x"])
    y = int(region_real["y"])
    ancho = int(region_real["ancho"])
    alto = int(region_real["alto"])

    # Dimensiones reales de la imagen completa
    # imagen.shape para un array 2D devuelve (filas, columnas) = (alto, ancho)
    alto_imagen, ancho_imagen = imagen.shape

    # SANITIZACIÓN DE COORDENADAS: evita que el cuadrito se salga de los bordes
    # de la imagen (lo cual rompería el slicing o daría una región vacía/inválida)

    # x se fuerza a estar entre 0 y (ancho_imagen - 1)
    x = max(0, min(x, ancho_imagen - 1))
    y = max(0, min(y, alto_imagen - 1))

    # El ancho/alto del cuadrito se ajusta para que, sumado a x/y, no se pase
    # del borde derecho/inferior de la imagen. Mínimo 1 píxel para evitar región vacía.
    ancho = max(1, min(ancho, ancho_imagen - x))
    alto = max(1, min(alto, alto_imagen - y))

    # RECORTE (slicing de NumPy): imagen[y:y+alto, x:x+ancho]
    # Recuerda que en arrays de imagen el primer índice es la fila (eje Y/vertical)
    # y el segundo es la columna (eje X/horizontal) — por eso va [y...], [x...] y no al revés
    region = imagen[y:y + alto, x:x + ancho]

    # .copy() porque un slice de NumPy es una "vista" (view) que comparte memoria
    # con el array original. Si no se copia, modificar "region" después
    # (ej. al ecualizarla) podría alterar accidentalmente la imagen original.
    return region.copy()