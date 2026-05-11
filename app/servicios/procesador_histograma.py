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
import cv2
# ---------------------------------------------------------------------------
# Expansión de histograma
# ---------------------------------------------------------------------------
def expandir_histograma(
    imagen: np.ndarray,
    s_min: int = 0,
    s_max: int = 255,
) -> np.ndarray:
    """
    Aplica expansión de histograma a una imagen en escala de grises.
 
    La transformación es una recta T(r) que mapea el rango real de
    intensidades [r_min, r_max] al rango deseado [s_min, s_max].
 
    Fórmula (slide 10 del PPT):
        s = T(r) = ((s_max - s_min) / (r_max - r_min)) * (r - r_min) + s_min
 
    Parámetros
    ----------
    imagen : np.ndarray
        Imagen en escala de grises (2D, dtype uint8).
    s_min : int
        Intensidad mínima del rango de salida (0–255).
    s_max : int
        Intensidad máxima del rango de salida (0–255).
 
    Retorna
    -------
    np.ndarray
        Imagen expandida (2D, dtype uint8).
    """
    if imagen is None or imagen.ndim != 2:
        raise ValueError("La imagen debe ser un arreglo 2D en escala de grises.")
 
    if s_min >= s_max:
        raise ValueError("s_min debe ser menor que s_max.")
 
    # Intensidad mínima y máxima REALES de la imagen (r_min, r_max)
    r_min = int(imagen.min())
    r_max = int(imagen.max())
 
    # Si la imagen ya tiene el rango completo, no hay nada que expandir.
    if r_max == r_min:
        return imagen.copy()
 
    # Construimos la tabla de transformación T(r) para los 256 niveles posibles.
    # Usamos float para no perder precisión durante el cálculo.
    tabla = np.arange(256, dtype=np.float64)
 
    pendiente = (s_max - s_min) / (r_max - r_min)   # m = (s_max-s_min)/(r_max-r_min)
    tabla = pendiente * (tabla - r_min) + s_min       # T(r) = m*(r - r_min) + s_min
 
    # Recortamos los valores al rango [0, 255] y convertimos a uint8.
    tabla = np.clip(tabla, 0, 255).astype(np.uint8)
 
    # Aplicamos la tabla de transformación a cada píxel de la imagen.
    imagen_expandida = tabla[imagen]
 
    return imagen_expandida
 
 
# ---------------------------------------------------------------------------
# Ecualización de histograma
# ---------------------------------------------------------------------------
 
def ecualizar_histograma(imagen: np.ndarray) -> np.ndarray:
    """
    Aplica ecualización de histograma a una imagen en escala de grises.
 
    El objetivo es obtener una distribución de probabilidades uniforme
    de los niveles de gris en la imagen resultante.
 
    Fórmulas (slides 13–15 del PPT):
        p_j   = n_j / (M * N)          frecuencia relativa del nivel j
        s_k   = T(r_k) = (L-1) * Σ p_j  (suma acumulada de j=0 hasta k)
        L = 256 (número de niveles de gris)
 
    Parámetros
    ----------
    imagen : np.ndarray
        Imagen en escala de grises (2D, dtype uint8).
 
    Retorna
    -------
    np.ndarray
        Imagen ecualizada (2D, dtype uint8).
    """
    if imagen is None or imagen.ndim != 2:
        raise ValueError("La imagen debe ser un arreglo 2D en escala de grises.")
 
    M, N = imagen.shape          # filas x columnas = total de píxeles
    L = 256                      # niveles de gris posibles (0 a 255)
    total_pixeles = M * N        # M * N
 
    # 1. Histograma: n_k = número de píxeles con nivel de gris k
    histograma, _ = np.histogram(imagen.flatten(), bins=256, range=(0, 255))
 
    # 2. Frecuencias relativas: p_k = n_k / (M * N)
    frecuencias_relativas = histograma / total_pixeles
 
    # 3. Distribución acumulada (CDF): suma acumulada de p_k
    cdf = np.cumsum(frecuencias_relativas)
 
    # 4. Tabla de transformación: s_k = (L - 1) * CDF(k), redondeado
    tabla = np.round((L - 1) * cdf).astype(np.uint8)
 
    # 5. Aplicar la tabla a cada píxel de la imagen
    imagen_ecualizada = tabla[imagen]
 
    return imagen_ecualizada
 
 
# ---------------------------------------------------------------------------
# Cálculo del histograma (para graficar)
# ---------------------------------------------------------------------------
 
def calcular_histograma(imagen: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calcula el histograma de una imagen en escala de grises.
 
    Parámetros
    ----------
    imagen : np.ndarray
        Imagen en escala de grises (2D, dtype uint8).
 
    Retorna
    -------
    tuple (niveles, conteos)
        niveles : array de 0 a 255.
        conteos : número de píxeles por cada nivel.
    """
    conteos, bordes = np.histogram(imagen.flatten(), bins=256, range=(0, 255))
    niveles = np.arange(256)
    return niveles, conteos
 
 
# ---------------------------------------------------------------------------
# Función principal de procesamiento (punto de entrada desde la UI)
# ---------------------------------------------------------------------------
 
def procesar_imagen(
    imagen: np.ndarray,
    metodo: str,
    s_min: int = 0,
    s_max: int = 255,
) -> dict:
    """
    Procesa una imagen aplicando el método indicado.
 
    Parámetros
    ----------
    imagen : np.ndarray
        Imagen original en escala de grises.
    metodo : str
        "Expansión de histograma" o "Ecualización de histograma".
    s_min : int
        Intensidad mínima de salida (solo para expansión).
    s_max : int
        Intensidad máxima de salida (solo para expansión).
 
    Retorna
    -------
    dict con:
        "imagen_original"    : np.ndarray  — imagen original
        "imagen_procesada"   : np.ndarray  — imagen resultado
        "hist_niveles_orig"  : np.ndarray  — niveles del histograma original
        "hist_conteos_orig"  : np.ndarray  — conteos del histograma original
        "hist_niveles_proc"  : np.ndarray  — niveles del histograma procesado
        "hist_conteos_proc"  : np.ndarray  — conteos del histograma procesado
        "metodo"             : str
        "error"              : str | None
    """
    resultado = {
        "imagen_original": imagen,
        "imagen_procesada": None,
        "hist_niveles_orig": None,
        "hist_conteos_orig": None,
        "hist_niveles_proc": None,
        "hist_conteos_proc": None,
        "metodo": metodo,
        "error": None,
    }
 
    try:
        # Histograma de la imagen original
        niveles_orig, conteos_orig = calcular_histograma(imagen)
        resultado["hist_niveles_orig"] = niveles_orig
        resultado["hist_conteos_orig"] = conteos_orig
 
        # Aplicar el método seleccionado
        if "Expansión" in metodo or "Expansion" in metodo:
            imagen_procesada = expandir_histograma(imagen, s_min=s_min, s_max=s_max)
        elif "Ecualización" in metodo or "Ecualizacion" in metodo:
            imagen_procesada = ecualizar_histograma(imagen)
        else:
            resultado["error"] = f"Método desconocido: {metodo}"
            return resultado
 
        resultado["imagen_procesada"] = imagen_procesada
 
        # Histograma de la imagen procesada
        niveles_proc, conteos_proc = calcular_histograma(imagen_procesada)
        resultado["hist_niveles_proc"] = niveles_proc
        resultado["hist_conteos_proc"] = conteos_proc
 
    except Exception as e:
        resultado["error"] = str(e)
 
    return resultado