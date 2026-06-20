import io

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Sin ventana, solo genera imágenes en memoria
import matplotlib.pyplot as plt

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QSizePolicy,
)

from app.ui.tabla_transformacion import VentanaTablaTransformacion

# ---------------------------------------------------------------------------
# Helpers para convertir datos a QPixmap
# ---------------------------------------------------------------------------

def _numpy_a_qpixmap(imagen: np.ndarray) -> QPixmap:
    """Convierte un array numpy (escala de grises, uint8) a QPixmap."""
    alto, ancho = imagen.shape
    q_imagen = QImage(imagen.data, ancho, alto, ancho, QImage.Format_Grayscale8)
    return QPixmap.fromImage(q_imagen)


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
    fig.patch.set_facecolor("#F9FAFB")
    ax.set_facecolor("#F1F5F9")

    ax.bar(niveles, conteos, width=1.0, color=color, alpha=0.85, linewidth=0)

    ax.set_title(titulo, fontsize=9, color="#1E293B", pad=6)
    ax.set_xlabel("Nivel de gris (0–255)", fontsize=7, color="#64748B")
    ax.set_ylabel("Cantidad de píxeles", fontsize=7, color="#64748B")
    ax.set_xlim(0, 255)
    ax.tick_params(labelsize=6, colors="#64748B")
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout(pad=1.2)

    # Guardar en memoria como PNG y convertir a QPixmap
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)

    q_imagen = QImage.fromData(buffer.read())
    return QPixmap.fromImage(q_imagen)


# ---------------------------------------------------------------------------
# Panel de resultado (tarjeta con título e imagen)
# ---------------------------------------------------------------------------

class PanelResultado(QFrame):
    def __init__(self, titulo: str) -> None:
        super().__init__()

        self.setObjectName("PanelResultado")
        self.pixmap_original = None

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(18, 18, 18, 18)
        diseno.setSpacing(12)

        self.etiqueta_titulo = QLabel(titulo)
        self.etiqueta_titulo.setObjectName("TituloPanelResultado")

        self.etiqueta_contenido = QLabel("Pendiente de resultado.")
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
        self.etiqueta_contenido.setText(texto)

    def establecer_imagen(self, pixmap: QPixmap) -> None:
        """Muestra una imagen escalada en el panel."""
        self.etiqueta_contenido.setText("")
        self.etiqueta_contenido.setPixmap(
            pixmap.scaled(
                self.etiqueta_contenido.width(),
                self.etiqueta_contenido.minimumHeight(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )


# ---------------------------------------------------------------------------
# Página de resultados
# ---------------------------------------------------------------------------

class PaginaResultados(QWidget):
    solicitud_volver = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.tabla_transformacion_actual = None
        self.metodo_actual = None
        self.tabla_transformacion_actual = None
        self.conteos_originales_actuales = None
        self.metodo_actual = None
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

        cuadricula.addWidget(self.panel_imagen_original, 0, 0)
        cuadricula.addWidget(self.panel_imagen_procesada, 0, 1)
        cuadricula.addWidget(self.panel_histograma_original, 1, 0)
        cuadricula.addWidget(self.panel_histograma_procesado, 1, 1)

        diseno_raiz.addWidget(encabezado)
        diseno_raiz.addLayout(cuadricula)

    def _crear_encabezado(self) -> QWidget:
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
        resultado = datos.get("resultado_procesamiento")

        # Si no hay resultado real, mostrar texto informativo
        if resultado is None or resultado.get("error"):
            error = resultado["error"] if resultado else "Sin resultado"
            self.panel_imagen_original.establecer_texto("Error en el procesamiento.")
            self.panel_imagen_procesada.establecer_texto(f"Error: {error}")
            self.panel_histograma_original.establecer_texto("Sin histograma.")
            self.panel_histograma_procesado.establecer_texto("Sin histograma.")
            return

        metodo = datos["metodo"]

        self.tabla_transformacion_actual = resultado.get("tabla_transformacion")
        self.conteos_originales_actuales = resultado.get("hist_conteos_orig")
        self.metodo_actual = metodo
        self.boton_ver_tabla.setEnabled(self.tabla_transformacion_actual is not None)

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
            color="#64748B",
        )
        self.panel_histograma_original.establecer_imagen(pixmap_hist_orig)

        # --- Panel 4: Histograma procesado ---
        color_hist = "#3B82F6" if "Expansión" in metodo else "#10B981"
        pixmap_hist_proc = _histograma_a_qpixmap(
            resultado["hist_niveles_proc"],
            resultado["hist_conteos_proc"],
            titulo=f"Histograma procesado ({metodo})",
            color=color_hist,
        )
        self.panel_histograma_procesado.establecer_imagen(pixmap_hist_proc)

    def mostrar_tabla_transformacion(self) -> None:
        if self.tabla_transformacion_actual is None:
            return

        if self.conteos_originales_actuales is None:
            return

        ventana = VentanaTablaTransformacion(
            tabla_transformacion=self.tabla_transformacion_actual,
            conteos_originales=self.conteos_originales_actuales,
            metodo=self.metodo_actual,
            parent=self,
        )

        ventana.exec()