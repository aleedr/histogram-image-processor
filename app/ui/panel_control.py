from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QScrollArea,
)

from app.utilidades.constantes import INTENSIDAD_MINIMA, INTENSIDAD_MAXIMA, TAMANO_GRID_PREDETERMINADO


class TarjetaOpcion(QFrame):
    def __init__(self, titulo: str) -> None:
        super().__init__()

        self.setObjectName("TarjetaOpcion")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.diseno = QVBoxLayout(self)
        self.diseno.setContentsMargins(16, 14, 16, 14)
        self.diseno.setSpacing(10)

        self.etiqueta_titulo = QLabel(titulo)
        self.etiqueta_titulo.setObjectName("TituloTarjetaOpcion")

        self.diseno.addWidget(self.etiqueta_titulo)

    def agregar_widget(self, widget: QWidget) -> None:
        self.diseno.addWidget(widget)

    def agregar_diseno(self, diseno: QHBoxLayout) -> None:
        self.diseno.addLayout(diseno)


class PanelControl(QWidget):
    solicitud_cargar_imagen = Signal()
    solicitud_procesar = Signal()
    cambio_modo_grid = Signal(bool)
    cambio_tamano_grid = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("PanelLateral")
        self.setMinimumWidth(340)
        self.setMaximumWidth(400)

        self._construir_interfaz()
        self._conectar_senales()
        self.establecer_imagen_cargada(False)

    def _construir_interfaz(self) -> None:
        diseno_raiz = QVBoxLayout(self)
        diseno_raiz.setContentsMargins(0, 0, 0, 0)
        diseno_raiz.setSpacing(0)

        area_scroll = QScrollArea()
        area_scroll.setObjectName("AreaScrollControl")
        area_scroll.setWidgetResizable(True)
        area_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        contenido = QWidget()
        contenido.setObjectName("ContenidoControl")

        diseno = QVBoxLayout(contenido)
        diseno.setContentsMargins(18, 18, 18, 18)
        diseno.setSpacing(14)

        titulo = QLabel("Panel de control")
        titulo.setObjectName("TituloPanel")

        subtitulo = QLabel("Configura la imagen, el área de análisis y el método.")
        subtitulo.setObjectName("SubtituloPanel")
        subtitulo.setWordWrap(True)

        self.boton_cargar = QPushButton("Cargar imagen JPG")
        self.boton_cargar.setObjectName("BotonPrimario")

        self.etiqueta_validacion = QLabel("Estado: sin imagen cargada")
        self.etiqueta_validacion.setObjectName("EstadoNeutral")
        self.etiqueta_validacion.setWordWrap(True)

        diseno.addWidget(titulo)
        diseno.addWidget(subtitulo)
        diseno.addWidget(self.boton_cargar)
        diseno.addWidget(self.etiqueta_validacion)
        diseno.addWidget(self._crear_separador())

        diseno.addWidget(self._crear_tarjeta_analisis())
        diseno.addWidget(self._crear_tarjeta_grid())
        diseno.addWidget(self._crear_tarjeta_metodo())
        diseno.addWidget(self._crear_tarjeta_rango())

        self.boton_procesar = QPushButton("Procesar imagen")
        self.boton_procesar.setObjectName("BotonExito")

        self.etiqueta_info_grid = QLabel("Grid: x=40, y=40, tamaño=15 px")
        self.etiqueta_info_grid.setObjectName("InfoPequena")
        self.etiqueta_info_grid.setWordWrap(True)

        texto_ayuda = QLabel(
            "Recuerda: el rango de intensidad debe estar entre 0 y 255. "
            "La intensidad mínima debe ser menor que la máxima."
        )
        texto_ayuda.setObjectName("TextoAyuda")
        texto_ayuda.setWordWrap(True)

        diseno.addWidget(self.boton_procesar)
        diseno.addWidget(self.etiqueta_info_grid)
        diseno.addWidget(texto_ayuda)
        diseno.addStretch()

        area_scroll.setWidget(contenido)
        diseno_raiz.addWidget(area_scroll)

    def _crear_tarjeta_analisis(self) -> TarjetaOpcion:
        tarjeta = TarjetaOpcion("Modo de análisis")
        tarjeta.setMinimumHeight(105)

        self.radio_grid = QRadioButton("Usar grid sobre la imagen")
        self.radio_imagen_completa = QRadioButton("Analizar imagen completa")

        self.radio_grid.setChecked(True)

        self.grupo_analisis = QButtonGroup(self)
        self.grupo_analisis.addButton(self.radio_grid)
        self.grupo_analisis.addButton(self.radio_imagen_completa)

        tarjeta.agregar_widget(self.radio_grid)
        tarjeta.agregar_widget(self.radio_imagen_completa)

        return tarjeta

    def _crear_tarjeta_grid(self) -> TarjetaOpcion:
        tarjeta = TarjetaOpcion("Tamaño del grid")
        tarjeta.setMinimumHeight(92)

        fila = QHBoxLayout()
        fila.setSpacing(10)

        etiqueta = QLabel("Tamaño:")
        etiqueta.setObjectName("EtiquetaCampo")

        self.selector_tamano_grid = QSpinBox()
        self.selector_tamano_grid.setRange(15, 150)
        self.selector_tamano_grid.setSingleStep(5)
        self.selector_tamano_grid.setValue(TAMANO_GRID_PREDETERMINADO)
        self.selector_tamano_grid.setSuffix(" px")

        fila.addWidget(etiqueta)
        fila.addWidget(self.selector_tamano_grid, stretch=1)

        tarjeta.agregar_diseno(fila)

        return tarjeta

    def _crear_tarjeta_metodo(self) -> TarjetaOpcion:
        tarjeta = TarjetaOpcion("Método de procesamiento")
        tarjeta.setMinimumHeight(105)

        self.radio_expansion = QRadioButton("Expansión de histograma")
        self.radio_ecualizacion = QRadioButton("Ecualización de histograma")

        self.radio_expansion.setChecked(True)

        self.grupo_metodo = QButtonGroup(self)
        self.grupo_metodo.addButton(self.radio_expansion)
        self.grupo_metodo.addButton(self.radio_ecualizacion)

        tarjeta.agregar_widget(self.radio_expansion)
        tarjeta.agregar_widget(self.radio_ecualizacion)

        return tarjeta

    def _crear_tarjeta_rango(self) -> TarjetaOpcion:
        tarjeta = TarjetaOpcion("Rango de intensidad")
        tarjeta.setMinimumHeight(125)

        fila_minima = QHBoxLayout()
        fila_maxima = QHBoxLayout()

        fila_minima.setSpacing(10)
        fila_maxima.setSpacing(10)

        etiqueta_minima = QLabel("Mínima:")
        etiqueta_maxima = QLabel("Máxima:")

        etiqueta_minima.setObjectName("EtiquetaCampo")
        etiqueta_maxima.setObjectName("EtiquetaCampo")

        self.selector_minimo = QSpinBox()
        self.selector_maximo = QSpinBox()

        self.selector_minimo.setRange(INTENSIDAD_MINIMA, INTENSIDAD_MAXIMA)
        self.selector_maximo.setRange(INTENSIDAD_MINIMA, INTENSIDAD_MAXIMA)

        self.selector_minimo.setValue(40)
        self.selector_maximo.setValue(130)

        fila_minima.addWidget(etiqueta_minima)
        fila_minima.addWidget(self.selector_minimo, stretch=1)

        fila_maxima.addWidget(etiqueta_maxima)
        fila_maxima.addWidget(self.selector_maximo, stretch=1)

        tarjeta.agregar_diseno(fila_minima)
        tarjeta.agregar_diseno(fila_maxima)

        return tarjeta

    def _crear_separador(self) -> QFrame:
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setObjectName("Separador")
        return linea

    def _conectar_senales(self) -> None:
        self.boton_cargar.clicked.connect(self.solicitud_cargar_imagen.emit)
        self.boton_procesar.clicked.connect(self.solicitud_procesar.emit)

        self.radio_grid.toggled.connect(self._al_cambiar_modo_grid)
        self.selector_tamano_grid.valueChanged.connect(self.cambio_tamano_grid.emit)

    def _al_cambiar_modo_grid(self, marcado: bool) -> None:
        self.selector_tamano_grid.setEnabled(marcado)
        self.cambio_modo_grid.emit(marcado)

    def establecer_imagen_cargada(self, cargada: bool) -> None:
        self.boton_procesar.setEnabled(cargada)

    def establecer_estado_validacion(self, valido: bool) -> None:
        if valido:
            self.etiqueta_validacion.setText("Estado: imagen válida en escala de grises")
            self.etiqueta_validacion.setObjectName("EstadoExito")
        else:
            self.etiqueta_validacion.setText("Estado: imagen inválida")
            self.etiqueta_validacion.setObjectName("EstadoError")

        self.etiqueta_validacion.setStyleSheet("")
        self.etiqueta_validacion.style().unpolish(self.etiqueta_validacion)
        self.etiqueta_validacion.style().polish(self.etiqueta_validacion)
        self.etiqueta_validacion.update()

    def obtener_metodo_seleccionado(self) -> str:
        if self.radio_expansion.isChecked():
            return "Expansión de histograma"

        return "Ecualización de histograma"

    def obtener_modo_analisis(self) -> str:
        if self.radio_grid.isChecked():
            return "Región seleccionada"

        return "Imagen completa"

    def obtener_rango_intensidad(self) -> tuple[int, int]:
        return self.selector_minimo.value(), self.selector_maximo.value()

    def actualizar_posicion_grid(self, x: int, y: int, tamano: int) -> None:
        self.etiqueta_info_grid.setText(f"Grid: x={x}, y={y}, tamaño={tamano} px")
