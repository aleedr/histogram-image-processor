# Título que se muestra en la ventana principal de la app (la barra de título del programa)
TITULO_APP = "Gray Histogram Processor"

# Valor mínimo posible de intensidad en una imagen en escala de grises
# (en escala de grises de 8 bits, el negro puro = 0)
INTENSIDAD_MINIMA = 0

# Valor máximo posible de intensidad en una imagen en escala de grises
# (el blanco puro = 255, porque 8 bits = 2^8 = 256 niveles, del 0 al 255)
INTENSIDAD_MAXIMA = 255

# Tamaño por defecto del "grid" (cuadrícula) cuando el usuario elige
# procesar solo una región/cuadrito de la imagen en vez de la imagen completa.
# Ej: si es 15, el cuadrito de análisis mide 15x15 píxeles
TAMANO_GRID_PREDETERMINADO = 15

# Tupla con las extensiones de archivo que la app acepta al subir una imagen.
# Se usa una tupla (no lista) porque es un valor fijo que no debería modificarse en tiempo de ejecución.
# Esto es lo que usará cargador_imagen.py para validar y rechazar formatos no soportados (ej. .png)
FORMATOS_COMPATIBLES = ("jpg", "jpeg")