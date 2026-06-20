"""
Servicio de procesamiento de histogramas.
 
Implementa la expansión y ecualización de histogramas según la teoría
del curso MA475 - Matemática Computacional (Unidad 1).
 
Fórmulas utilizadas:
  Expansión : s = T(r) = ((s_max - s_min) / (r_max - r_min)) * (r - r_min) + s_min
  Ecualización: s_k = T(r_k) = (L - 1) * sum(p_j, j=0..k)
                donde p_j = n_j / (M * N)
"""
 
import numpy as np
# NumPy: para manejar la imagen como matriz numérica y hacer cálculos vectorizados
# (operar sobre todos los píxeles a la vez, sin loops manuales — mucho más rápido)

import cv2
# OpenCV: importado pero en este archivo no se usa directamente ninguna función cv2.*
# (probablemente quedó de una versión anterior, podría removerse sin problema)

# ---------------------------------------------------------------------------
# Expansión de histograma
# ---------------------------------------------------------------------------
def expandir_histograma(imagen: np.ndarray, s_min: int = 0, s_max: int = 255) -> tuple[np.ndarray, np.ndarray]:
    # -> tuple[np.ndarray, np.ndarray] es un "type hint": indica que la función
    # retorna dos arrays de NumPy (la imagen procesada y la tabla de transformación)

    """
    Aplica expansión de histograma a una imagen en escala de grises.
 
    La transformación es una recta T(r) que mapea el rango real de
    intensidades [r_min, r_max] al rango deseado [s_min, s_max].
 
    Fórmula (slide 10 del PPT):
        s = T(r) = ((s_max - s_min) / (r_max - r_min)) * (r - r_min) + s_min
    """
    # IDEA CLAVE: la expansión es literalmente "estirar" el contraste.
    # Si tu imagen solo usa grises del 50 al 200 (rango chico), esta función
    # los reescala para que usen todo el rango 0-255 (más contraste visual).
    # Es una transformación LINEAL: una recta y=mx+b

    # Validación: la imagen debe venir ya en escala de grises (2D), no a color (3D)
    if imagen is None or imagen.ndim != 2:
        raise ValueError("La imagen debe ser un arreglo 2D en escala de grises.")
 
    if s_min >= s_max:
        # No tiene sentido pedir un rango de salida invertido o vacío
        raise ValueError("s_min debe ser menor que s_max.")
 
    # Intensidad mínima y máxima REALES de la imagen (r_min, r_max)
    # .min() / .max() recorren TODOS los píxeles de la imagen y devuelven el extremo
    r_min = int(imagen.min())
    r_max = int(imagen.max())
 
    # Caso borde: si toda la imagen tiene el mismo valor de gris (r_max == r_min),
    # no se puede dividir entre (r_max - r_min) porque sería división por cero.
    # En ese caso no hay nada que "expandir", se devuelve la imagen igual.
    if r_max == r_min:
        tabla = np.arange(256, dtype=np.uint8)  # tabla "identidad": 0,1,2,...,255
        return imagen.copy(), tabla
 
    # ESTRATEGIA: en vez de recalcular la fórmula para cada píxel uno por uno,
    # se construye una "tabla de lookup" (LUT) de 256 posiciones: una por cada
    # nivel de gris posible (0 a 255). Luego se aplica esa tabla a toda la imagen
    # de una sola vez. Esto es MUCHO más eficiente que iterar pixel por pixel.
    tabla = np.arange(256, dtype=np.float64)
    # tabla = [0, 1, 2, ..., 255] representando los posibles valores "r" de entrada
 
    pendiente = (s_max - s_min) / (r_max - r_min)   # m = (s_max-s_min)/(r_max-r_min)
    # Es la "m" de la ecuación de la recta y = m*x + b

    tabla = pendiente * (tabla - r_min) + s_min       # T(r) = m*(r - r_min) + s_min
    # Aquí se aplica la fórmula de expansión a TODOS los 256 valores posibles a la vez
    # (operación vectorizada de NumPy: no hay un for loop explícito)
 
    # Recortamos los valores al rango [0, 255] y convertimos a uint8.
    # np.clip "fuerza" cualquier valor fuera de [0,255] a quedar dentro de ese rango
    # (por seguridad, aunque matemáticamente no debería pasarse del rango)
    # uint8 = entero sin signo de 8 bits (0 a 255), el tipo estándar para imágenes
    tabla = np.clip(tabla, 0, 255).astype(np.uint8)
 
    # Aplicamos la tabla de transformación a cada píxel de la imagen.
    # ESTO ES LA MAGIA: tabla[imagen] usa cada valor de "imagen" como índice
    # dentro de "tabla". Si un píxel vale 120, busca tabla[120] y ese es su nuevo valor.
    # NumPy hace esto para TODOS los píxeles de la imagen en una sola operación.
    imagen_expandida = tabla[imagen]

    # Se retorna la imagen procesada Y la tabla (la tabla se usa después para
    # mostrar la tabla_transformacion en la UI: cómo cambió cada nivel de gris)
    return imagen_expandida, tabla
 
 
# ---------------------------------------------------------------------------
# Ecualización de histograma
# ---------------------------------------------------------------------------
 
def ecualizar_histograma(imagen: np.ndarray, s_min: int = 0, s_max: int = 255) -> tuple[np.ndarray, np.ndarray]:

    """
    Aplica ecualización de histograma a una imagen en escala de grises.
 
    El objetivo es obtener una distribución de probabilidades uniforme
    de los niveles de gris en la imagen resultante.
 
    Fórmulas (slides 13–15 del PPT):
        p_j   = n_j / (M * N)          frecuencia relativa del nivel j
        s_k   = T(r_k) = (L-1) * Σ p_j  (suma acumulada de j=0 hasta k)
        L = 256 (número de niveles de gris)
    """
    # IDEA CLAVE: a diferencia de la expansión (que es lineal/una recta),
    # la ecualización es una transformación basada en PROBABILIDADES.
    # Busca que todos los niveles de gris se usen "parejo" en la imagen final,
    # mejorando el contraste donde hay más concentración de píxeles.

    if imagen is None or imagen.ndim != 2:
        raise ValueError("La imagen debe ser un arreglo 2D en escala de grises.")

    if s_min >= s_max:
        # Nota: el mensaje de error dice "mayor a s_max" pero la condición
        # realmente exige que s_min sea MENOR que s_max (posible error de tipeo en el mensaje)
        raise ValueError("s_min debe ser mayor a s_max.")
 
    L = 256                         # niveles de gris posibles (0 a 255)
    total_pixeles = imagen.size     # M*N: cantidad total de píxeles (alto x ancho)
 
    # 1. Histograma: n_k = número de píxeles con nivel de gris k
    # imagen.flatten() convierte la matriz 2D en un array 1D (lista plana de píxeles)
    # np.histogram cuenta cuántos píxeles caen en cada uno de los 256 "bins" (niveles 0-255)
    histograma, _ = np.histogram(imagen.flatten(), bins=256, range=(0, 256))
    # el "_" descarta el segundo valor que retorna (los bordes de los bins), no se usa
 
    # 2. Frecuencias relativas: p_k = n_k / (M * N)
    # Convierte conteos absolutos en PROBABILIDADES (proporción de píxeles en cada nivel)
    frecuencias_relativas = histograma / total_pixeles
 
    # 3. Distribución acumulada (CDF): suma acumulada de p_k
    # cumsum va sumando progresivamente: cdf[0]=p[0], cdf[1]=p[0]+p[1], cdf[2]=p[0]+p[1]+p[2]...
    # Esto es la "Función de Distribución Acumulada" (CDF) de la teoría de probabilidad
    cdf = np.cumsum(frecuencias_relativas)

    # Validando y normalizando la distribución acumulada
    # Se filtran solo los valores de cdf que son mayores a 0 (para encontrar el primer
    # nivel de gris que realmente aparece en la imagen)
    cdf_valores_validos = cdf[cdf > 0]
    if len(cdf_valores_validos) == 0:
        # Caso borde raro: imagen completamente vacía/sin píxeles válidos
        tabla = np.arange(256, dtype=np.uint8)
        return imagen.copy(), tabla
    
    cdf_min = cdf_valores_validos[0]
    # cdf_min es el primer valor acumulado distinto de cero (corresponde al nivel
    # de gris más oscuro presente realmente en la imagen)

    if cdf_min == 1:
        # Caso borde: si el primer valor de CDF ya es 1, significa que TODOS los
        # píxeles de la imagen tienen el mismo nivel de gris (imagen totalmente plana).
        # No se puede ecualizar (división entre 1-1=0), se devuelve una imagen sólida
        tabla = np.full(256, s_min, dtype=np.uint8)
        return np.full_like(imagen, s_min, dtype=np.uint8), tabla
    
    # NORMALIZACIÓN: esta es la versión "clásica" de ecualización de histograma
    # (similar a la fórmula estándar con cdf_min), que evita que la imagen pierda
    # el valor 0 o 255 reales por errores de redondeo, y "estira" el cdf entre 0 y 1
    cdf_normalizada = (cdf - cdf_min) / (1 - cdf_min)
    cdf_normalizada = np.clip(cdf_normalizada, 0, 1)  # por seguridad, fuerza rango [0,1]
 
    # 4. Tabla de transformación: s_k = (L - 1) * CDF(k), redondeado
    # En vez de multiplicar siempre por 255 (L-1), aquí se generaliza para que el
    # resultado caiga dentro del rango [s_min, s_max] elegido por el usuario
    tabla = s_min + (s_max - s_min) * cdf_normalizada
    tabla = np.round(tabla).astype(np.uint8)  # redondea y convierte a entero de imagen
 
    # 5. Aplicar la tabla a cada píxel de la imagen
    # Mismo truco de LUT (lookup table) que en expandir_histograma
    imagen_ecualizada = tabla[imagen]

    return imagen_ecualizada, tabla
 
 
# ---------------------------------------------------------------------------
# Cálculo del histograma (para graficar)
# ---------------------------------------------------------------------------
 
def calcular_histograma(imagen: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcula el histograma de una imagen en escala de grises.
    Retorna (niveles, conteos)
    """
    # Esta función NO transforma la imagen, solo CUENTA cuántos píxeles
    # hay de cada nivel de gris — se usa para dibujar el gráfico de histograma
    # tanto de la imagen original como de la procesada (para comparar antes/después)
    conteos, bordes = np.histogram(imagen.flatten(), bins=256, range=(0, 255))
    # Nota: aquí el range es (0, 255) mientras que en ecualizar_histograma fue (0, 256).
    # Es una inconsistencia menor que puede afectar levemente el último bin (255)

    niveles = np.arange(256)  # eje X del histograma: [0, 1, 2, ..., 255]
    return niveles, conteos
 
 
# ---------------------------------------------------------------------------
# Función principal de procesamiento (punto de entrada desde la UI)
# ---------------------------------------------------------------------------
 
def procesar_imagen(imagen: np.ndarray, metodo: str, s_min: int = 0, s_max: int = 255) -> dict: 
    """
    Procesa una imagen aplicando el método indicado.
    Retorna un diccionario con imagen original, procesada, histogramas y posible error.
    """
    # Esta es la función "orquestadora": la UI solo llama a esta función,
    # sin necesidad de saber los detalles internos de expandir/ecualizar.
    # Sigue el mismo patrón de diccionario con "error" que vimos en cargador_imagen.py

    resultado = {
        "imagen_original": imagen,
        "imagen_procesada": None,
        "hist_niveles_orig": None,
        "hist_conteos_orig": None,
        "hist_niveles_proc": None,
        "hist_conteos_proc": None,
        "tabla_transformacion": None,
        "metodo": metodo,
        "error": None,
    }
 
    try:
        # Histograma de la imagen original (para el gráfico "antes")
        niveles_orig, conteos_orig = calcular_histograma(imagen)
        resultado["hist_niveles_orig"] = niveles_orig
        resultado["hist_conteos_orig"] = conteos_orig
 
        # Aplicar el método seleccionado según el texto que llega desde la UI.
        # Se busca "Expansión" o "Expansion" (sin tilde) por si el texto viene
        # de un combobox/selector que no maneja bien tildes
        if "Expansión" in metodo or "Expansion" in metodo:
            imagen_procesada, tabla_transformacion = expandir_histograma(
                imagen,
                s_min=s_min,
                s_max=s_max,
            )
        elif "Ecualización" in metodo or "Ecualizacion" in metodo:
            imagen_procesada, tabla_transformacion = ecualizar_histograma(
                imagen,
                s_min=s_min,
                s_max=s_max,
            )
        else:
            # Si el texto del método no coincide con ninguno esperado, se devuelve error
            # en vez de lanzar una excepción (mantiene consistencia con el patrón de retorno)
            resultado["error"] = f"Método desconocido: {metodo}"
            return resultado

        resultado["imagen_procesada"] = imagen_procesada
        resultado["tabla_transformacion"] = tabla_transformacion
        # tabla_transformacion es la que probablemente alimenta tabla_transformacion.py
        # en la UI (la tabla de "cómo cambió cada valor")
 
        # Histograma de la imagen procesada (para el gráfico "después")
        niveles_proc, conteos_proc = calcular_histograma(imagen_procesada)
        resultado["hist_niveles_proc"] = niveles_proc
        resultado["hist_conteos_proc"] = conteos_proc
 
    except Exception as e:
        # Si algo falla en cualquier punto del try (ej. ValueError de las validaciones
        # internas), se captura y se guarda el mensaje de error en el resultado
        resultado["error"] = str(e)
 
    return resultado