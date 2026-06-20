import io
# io: librería estándar para trabajar con flujos de datos en memoria.
# Aquí se usa io.BytesIO() como un "archivo virtual" en RAM, para guardar
# la imagen del gráfico SIN escribir ningún archivo real en el disco

import numpy as np

import matplotlib
matplotlib.use("Agg")  # Sin ventana, solo genera imágenes en memoria
# Matplotlib normalmente intenta abrir una ventana propia para mostrar gráficos
# (su propio GUI). "Agg" es un backend que NO abre ninguna ventana — solo
# renderiza el gráfico como imagen en memoria/archivo. Esto es necesario porque
# ya estamos dentro de una app Qt, y no queremos que Matplotlib abra su propia
# ventana compitiendo con la nuestra

import matplotlib.pyplot as plt
# pyplot: la interfaz de "alto nivel" de Matplotlib para crear gráficos
# (parecida a cómo se grafica en MATLAB, de ahí el nombre)

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QImage
# QImage: representa una imagen en memoria a más bajo nivel que QPixmap
# (mejor para crear imágenes desde datos crudos, como un array de NumPy
# o bytes de un PNG). QPixmap está más optimizado para DIBUJAR en pantalla.
# El flujo típico es: datos crudos -> QImage -> QPixmap

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,    # Layout en forma de cuadrícula (filas y columnas), ideal
                     # para los 4 paneles: imagen original/procesada arriba,
                     # histogramas abajo
    QLabel,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QSizePolicy,
)

from app.ui.tabla_transformacion import VentanaTablaTransformacion
# La ventana que documentamos en el paso anterior

# ---------------------------------------------------------------------------
# Helpers para convertir datos a QPixmap
# ---------------------------------------------------------------------------

def _numpy_a_qpixmap(imagen: np.ndarray) -> QPixmap:
    """Convierte un array numpy (escala de grises, uint8) a QPixmap."""
    # Esta función es el "puente" entre el mundo matemático (NumPy/OpenCV)
    # y el mundo visual (Qt). Las imágenes procesadas por procesador_histograma.py
    # son arrays de NumPy; para MOSTRARLAS en la UI hay que convertirlas a QPixmap

    alto, ancho = imagen.shape
    # Un array 2D de escala de grises tiene shape (filas, columnas) = (alto, ancho)

    q_imagen = QImage(imagen.data, ancho, alto, ancho, QImage.Format_Grayscale8)
    # QImage puede construirse directamente desde un buffer de bytes crudo:
    #   - imagen.data: acceso a los bytes crudos del array de NumPy (sin copiar)
    #   - ancho, alto: dimensiones de la imagen
    #   - el segundo "ancho": es el "bytesPerLine" (cuántos bytes ocupa cada fila;
    #     en escala de grises de 8 bits, 1 byte por píxel = mismo valor que el ancho)
    #   - Format_Grayscale8: le dice a Qt que interprete los datos como 1 byte
    #     por píxel, escala de grises de 8 bits (0-255), igual que uint8 de NumPy

    return QPixmap.fromImage(q_imagen)
    # Convierte el QImage a QPixmap, que es lo que los QLabel pueden mostrar
    # directamente con .setPixmap()


def _histograma_a_qpixmap(
    niveles: np.ndarray,
    conteos: np.ndarray,
    titulo: str,
    color: str = "#3B82F6",
) -> QPixmap:
    """
    Genera una gráfica de histograma con matplotlib y la convierte a QPixmap.
    La imagen se genera en memoria, sin guardar archivos en disco.
    """
    fig, ax = plt.subplots(figsize=(4.5, 2.8), dpi=90)
    # plt.subplots() crea una "figura" (fig, el lienzo completo) y unos "ejes"
    # (ax, el área donde se dibuja el gráfico en sí). figsize en pulgadas, dpi
    # controla la resolución/nitidez

    fig.patch.set_facecolor("#F9FAFB")
    # Color de fondo de TODA la figura (incluyendo márgenes alrededor del gráfico)
    ax.set_facecolor("#F1F5F9")
    # Color de fondo SOLO del área donde se dibujan las barras

    ax.bar(niveles, conteos, width=1.0, color=color, alpha=0.85, linewidth=0)
    # Dibuja un gráfico de BARRAS: eje X = niveles de gris (0-255), eje Y = conteos
    # width=1.0: cada barra ocupa exactamente 1 unidad (sin espacios entre barras,
    # esto hace que se vea como un histograma "continuo" en vez de barras separadas)
    # alpha=0.85: ligera transparencia (85% opaco)

    ax.set_title(titulo, fontsize=9, color="#1E293B", pad=6)
    ax.set_xlabel("Nivel de gris (0–255)", fontsize=7, color="#64748B")
    ax.set_ylabel("Cantidad de píxeles", fontsize=7, color="#64748B")
    ax.set_xlim(0, 255)
    # Fuerza que el eje X SIEMPRE muestre el rango completo 0-255, sin importar
    # si la imagen no usa todo ese rango (para comparar visualmente antes/después
    # en la misma escala)

    ax.tick_params(labelsize=6, colors="#64748B")
    # Tamaño y color de los números/marcas en los ejes
    ax.spines[["top", "right"]].set_visible(False)
    # Oculta los bordes superior y derecho del gráfico (estilo más limpio/moderno,
    # dejando solo los ejes izquierdo e inferior visibles)

    plt.tight_layout(pad=1.2)
    # Ajusta automáticamente los márgenes para que nada se corte (títulos, etiquetas)

    # Guardar en memoria como PNG y convertir a QPixmap
    buffer = io.BytesIO()
    # Crea un "archivo en memoria" vacío

    fig.savefig(buffer, format="png", bbox_inches="tight")
    # En vez de guardar el gráfico en un archivo .png en disco, lo guarda
    # DENTRO del buffer en memoria, como si fuera un archivo

    plt.close(fig)
    # Libera la memoria usada por la figura de Matplotlib (buena práctica,
    # evita acumular figuras abiertas en memoria si se llama esta función muchas veces)

    buffer.seek(0)
    # Mueve el "cursor" del buffer al principio, para poder leerlo desde el inicio
    # (savefig dejó el cursor al final, después de escribir)

    q_imagen = QImage.fromData(buffer.read())
    # Lee los bytes PNG del buffer y construye un QImage a partir de ellos
    # (QImage sabe "decodificar" formatos de imagen comunes como PNG/JPG)

    return QPixmap.fromImage(q_imagen)


# ---------------------------------------------------------------------------
# Panel de resultado (tarjeta con título e imagen)
# ---------------------------------------------------------------------------

class PanelResultado(QFrame):
    # Componente reutilizable: una "tarjeta" que puede mostrar texto O una imagen.
    # Se usa 4 veces: imagen original, imagen procesada, histograma original,
    # histograma procesado — mismo componente, contenido distinto

    def __init__(self, titulo: str) -> None:
        super().__init__()

        self.setObjectName("PanelResultado")
        self.pixmap_original = None
        # Nota: este atributo se declara pero no se usa en ningún otro lado
        # del archivo (posible remanente de una versión anterior)

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(18, 18, 18, 18)
        diseno.setSpacing(12)

        self.etiqueta_titulo = QLabel(titulo)
        self.etiqueta_titulo.setObjectName("TituloPanelResultado")

        self.etiqueta_contenido = QLabel("Pendiente de resultado.")
        # Este QLabel hace "doble función": puede mostrar texto (estado inicial,
        # o mensajes de error) O una imagen (el resultado real), dependiendo
        # de qué método se llame (establecer_texto o establecer_imagen)

        self.etiqueta_contenido.setObjectName("ContenidoPanelResultado")
        self.etiqueta_contenido.setAlignment(Qt.AlignCenter)
        self.etiqueta_contenido.setMinimumHeight(220)
        self.etiqueta_contenido.setWordWrap(True)
        self.etiqueta_contenido.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        diseno.addWidget(self.etiqueta_titulo)
        diseno.addWidget(self.etiqueta_contenido)

    def establecer_texto(self, texto: str) -> None:
        """Muestra texto en el panel."""
        self.etiqueta_contenido.setPixmap(QPixmap())  # Limpia imagen previa
        # QPixmap() vacío "borra" cualquier imagen que estuviera mostrándose antes,
        # para que no quede una imagen vieja superpuesta con el texto nuevo
        self.etiqueta_contenido.setText(texto)

    def establecer_imagen(self, pixmap: QPixmap) -> None:
        """Muestra una imagen escalada en el panel."""
        self.etiqueta_contenido.setText("")
        # Limpia cualquier texto previo antes de mostrar la imagen
        self.etiqueta_contenido.setPixmap(
            pixmap.scaled(
                self.etiqueta_contenido.width(),
                self.etiqueta_contenido.minimumHeight(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        # Escala la imagen para que quepa en el espacio del panel,
        # manteniendo proporción y con suavizado


# ---------------------------------------------------------------------------
# Página de resultados
# ---------------------------------------------------------------------------

class PaginaResultados(QWidget):
    # Esta es la pantalla que el usuario ve DESPUÉS de presionar "Procesar imagen":
    # muestra los 4 paneles (imagen original, procesada, histograma original,
    # histograma procesado) y el botón para ver la tabla de valores

    solicitud_volver = Signal()
    # Señal para "avisar" cuando el usuario quiere regresar a la pantalla
    # de procesamiento (probablemente escuchada por ventana_principal.py
    # para cambiar de página/vista)

    def __init__(self) -> None:
        super().__init__()
        self.tabla_transformacion_actual = None
        self.metodo_actual = None
        self.tabla_transformacion_actual = None  # (duplicado, ya se inicializó arriba)
        self.conteos_originales_actuales = None
        self.metodo_actual = None  # (duplicado también)
        # Guarda referencias a los datos del ÚLTIMO procesamiento, para poder
        # abrir la ventana de tabla de transformación cuando se pida, sin
        # necesidad de recalcular nada
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        diseno_raiz = QVBoxLayout(self)
        diseno_raiz.setContentsMargins(0, 0, 0, 0)
        diseno_raiz.setSpacing(14)

        encabezado = self._crear_encabezado()

        self.panel_imagen_original = PanelResultado("Imagen original")
        self.panel_imagen_procesada = PanelResultado("Imagen procesada")
        self.panel_histograma_original = PanelResultado("Histograma original")
        self.panel_histograma_procesado = PanelResultado("Histograma procesado")

        cuadricula = QGridLayout()
        cuadricula.setSpacing(14)

        # Organiza los 4 paneles en una grilla 2x2:
        # (0,0) imagen original     (0,1) imagen procesada
        # (1,0) histograma original (1,1) histograma procesado
        cuadricula.addWidget(self.panel_imagen_original, 0, 0)
        cuadricula.addWidget(self.panel_imagen_procesada, 0, 1)
        cuadricula.addWidget(self.panel_histograma_original, 1, 0)
        cuadricula.addWidget(self.panel_histograma_procesado, 1, 1)

        diseno_raiz.addWidget(encabezado)
        diseno_raiz.addLayout(cuadricula)

    def _crear_encabezado(self) -> QWidget:
        # Construye la parte superior: título + descripción + botones de acción
        encabezado = QWidget()
        encabezado.setObjectName("EncabezadoResultados")

        diseno = QHBoxLayout(encabezado)
        diseno.setContentsMargins(18, 16, 18, 16)
        diseno.setSpacing(12)

        contenedor_texto = QWidget()
        diseno_texto = QVBoxLayout(contenedor_texto)
        diseno_texto.setContentsMargins(0, 0, 0, 0)
        diseno_texto.setSpacing(4)

        titulo = QLabel("Resultados del procesamiento")
        titulo.setObjectName("TituloResultados")

        subtitulo = QLabel(
            "Compara la imagen original y la imagen procesada con sus respectivos histogramas."
        )
        subtitulo.setObjectName("SubtituloResultados")

        diseno_texto.addWidget(titulo)
        diseno_texto.addWidget(subtitulo)

        self.boton_ver_tabla = QPushButton("Ver tabla de valores")
        self.boton_ver_tabla.setObjectName("BotonPrimario")
        self.boton_ver_tabla.clicked.connect(self.mostrar_tabla_transformacion)
        self.boton_ver_tabla.setEnabled(False)
        # Empieza deshabilitado: no hay nada que mostrar hasta que se procese una imagen

        self.boton_volver = QPushButton("← Volver al procesamiento")
        self.boton_volver.setObjectName("BotonSecundario")
        self.boton_volver.clicked.connect(self.solicitud_volver.emit)

        diseno.addWidget(contenedor_texto, stretch=1)
        diseno.addWidget(self.boton_ver_tabla)
        diseno.addWidget(self.boton_volver)

        return encabezado

    def establecer_resultados(self, datos: dict) -> None:
        """
        Recibe los datos del procesamiento y actualiza los 4 paneles
        con las imágenes e histogramas reales.
        """
        # Este método es el punto de entrada PRINCIPAL: lo llama quien orquesta
        # todo el flujo (probablemente ventana_principal.py) después de llamar
        # a procesador_histograma.procesar_imagen()

        resultado = datos.get("resultado_procesamiento")
        # Espera un diccionario "datos" más amplio que contenga, entre otras cosas,
        # el resultado de procesar_imagen() bajo la clave "resultado_procesamiento"

        # Si no hay resultado real, mostrar texto informativo
        if resultado is None or resultado.get("error"):
            error = resultado["error"] if resultado else "Sin resultado"
            self.panel_imagen_original.establecer_texto("Error en el procesamiento.")
            self.panel_imagen_procesada.establecer_texto(f"Error: {error}")
            self.panel_histograma_original.establecer_texto("Sin histograma.")
            self.panel_histograma_procesado.establecer_texto("Sin histograma.")
            return
            # Maneja el caso de error sin romper la UI: muestra mensajes
            # informativos en cada panel en vez de crashear

        metodo = datos["metodo"]

        self.tabla_transformacion_actual = resultado.get("tabla_transformacion")
        self.conteos_originales_actuales = resultado.get("hist_conteos_orig")
        self.metodo_actual = metodo
        # Guarda estos datos como "estado" de la página, para poder usarlos
        # después si el usuario presiona "Ver tabla de valores"

        self.boton_ver_tabla.setEnabled(self.tabla_transformacion_actual is not None)
        # Solo habilita el botón si realmente hay una tabla de transformación válida

        # --- Panel 1: Imagen original ---
        pixmap_original = _numpy_a_qpixmap(resultado["imagen_original"])
        self.panel_imagen_original.establecer_imagen(pixmap_original)

        # --- Panel 2: Imagen procesada ---
        pixmap_procesada = _numpy_a_qpixmap(resultado["imagen_procesada"])
        self.panel_imagen_procesada.establecer_imagen(pixmap_procesada)

        # --- Panel 3: Histograma original ---
        pixmap_hist_orig = _histograma_a_qpixmap(
            resultado["hist_niveles_orig"],
            resultado["hist_conteos_orig"],
            titulo="Histograma original",
            color="#64748B",  # gris, para diferenciarlo visualmente del procesado
        )
        self.panel_histograma_original.establecer_imagen(pixmap_hist_orig)

        # --- Panel 4: Histograma procesado ---
        color_hist = "#3B82F6" if "Expansión" in metodo else "#10B981"
        # Color azul si fue expansión, verde si fue ecualización — ayuda visualmente
        # a identificar de un vistazo qué método se aplicó

        pixmap_hist_proc = _histograma_a_qpixmap(
            resultado["hist_niveles_proc"],
            resultado["hist_conteos_proc"],
            titulo=f"Histograma procesado ({metodo})",
            color=color_hist,
        )
        self.panel_histograma_procesado.establecer_imagen(pixmap_hist_proc)

    def mostrar_tabla_transformacion(self) -> None:
        # Se ejecuta cuando se presiona "Ver tabla de valores"
        if self.tabla_transformacion_actual is None:
            return

        if self.conteos_originales_actuales is None:
            return
        # Doble chequeo de seguridad antes de abrir la ventana (aunque el botón
        # ya debería estar deshabilitado si faltan estos datos)

        ventana = VentanaTablaTransformacion(
            tabla_transformacion=self.tabla_transformacion_actual,
            conteos_originales=self.conteos_originales_actuales,
            metodo=self.metodo_actual,
            parent=self,
        )

        ventana.exec()
        # .exec() abre el QDialog en modo MODAL: bloquea la interacción con
        # el resto de la app hasta que el usuario cierre esa ventana
        # (distinto de .show(), que abriría la ventana sin bloquear nada)