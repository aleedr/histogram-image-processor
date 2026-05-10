from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QHBoxLayout,
)


class PanelResultado(QFrame):
    def __init__(self, titulo: str) -> None:
        super().__init__()

        self.setObjectName("PanelResultado")

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

        diseno.addWidget(self.etiqueta_titulo)
        diseno.addWidget(self.etiqueta_contenido)

    def establecer_contenido(self, texto: str) -> None:
        self.etiqueta_contenido.setText(texto)


class PaginaResultados(QWidget):
    solicitud_volver = Signal()

    def __init__(self) -> None:
        super().__init__()

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

        self.boton_volver = QPushButton("← Volver al procesamiento")
        self.boton_volver.setObjectName("BotonSecundario")
        self.boton_volver.clicked.connect(self.solicitud_volver.emit)

        diseno.addWidget(contenedor_texto, stretch=1)
        diseno.addWidget(self.boton_volver)

        return encabezado

    def establecer_resultados(self, datos: dict) -> None:
        metodo = datos["metodo"]
        modo_analisis = datos["modo_analisis"]
        minimo = datos["minimo"]
        maximo = datos["maximo"]
        datos_grid = datos["datos_grid"]

        self.panel_imagen_original.establecer_contenido(
            "Aquí se mostrará la imagen original cargada."
        )

        self.panel_histograma_original.establecer_contenido(
            "Aquí se mostrará el histograma original."
        )

        self.panel_imagen_procesada.establecer_contenido(
            f"Método aplicado: {metodo}\n"
            f"Modo de análisis: {modo_analisis}\n"
            f"Rango de salida: {minimo} - {maximo}"
        )

        if datos_grid.get("habilitado", False):
            texto_region = (
                f"Región seleccionada:\n"
                f"x={datos_grid['x']}, "
                f"y={datos_grid['y']}, "
                f"tamaño={datos_grid['tamano']} px"
            )
        else:
            texto_region = "Se analizó la imagen completa."

        self.panel_histograma_procesado.establecer_contenido(
            f"Aquí se mostrará el histograma procesado.\n\n{texto_region}"
        )
