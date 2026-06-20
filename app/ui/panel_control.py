from PySide6.QtCore import Signal, Qt
# Signal: para crear señales propias (eventos que el panel emite hacia afuera)
# Qt: namespace con constantes (ej: Qt.ScrollBarAlwaysOff)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,    # layout vertical
    QLabel,         # texto
    QPushButton,    # botón clickeable
    QRadioButton,   # botón de opción única (selecciona uno entre varios)
    QButtonGroup,   # agrupa RadioButtons para que solo uno esté marcado a la vez
    QSpinBox,       # campo numérico con flechitas arriba/abajo para subir/bajar valor
    QHBoxLayout,    # layout horizontal (fila)
    QFrame,         # contenedor visual simple, también usado para líneas separadoras
    QSizePolicy,    # cómo se comporta un widget al cambiar de tamaño
    QScrollArea,    # contenedor con scroll si el contenido no cabe
)

from app.utilidades.constantes import INTENSIDAD_MINIMA, INTENSIDAD_MAXIMA, TAMANO_GRID_PREDETERMINADO
# Reutiliza las constantes 0, 255 y 15 que vimos al principio


class TarjetaOpcion(QFrame):
    # Widget reutilizable: una "tarjeta" visual con título + contenido,
    # usada para agrupar cada sección del panel (Modo de análisis, Método, Rango, etc.)
    # Es un patrón de "componente reutilizable" para no repetir el mismo layout 4 veces

    def __init__(self, titulo: str) -> None:
        super().__init__()

        self.setObjectName("TarjetaOpcion")
        # Para aplicar estilo CSS/QSS (bordes, fondo, sombra de "tarjeta")

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Se expande horizontalmente (llena el ancho disponible) pero su alto es fijo
        # (no crece verticalmente más de lo necesario para su contenido)

        self.diseno = QVBoxLayout(self)
        self.diseno.setContentsMargins(16, 14, 16, 14)
        self.diseno.setSpacing(10)

        self.etiqueta_titulo = QLabel(titulo)
        self.etiqueta_titulo.setObjectName("TituloTarjetaOpcion")

        self.diseno.addWidget(self.etiqueta_titulo)

    def agregar_widget(self, widget: QWidget) -> None:
        # Método helper para agregar widgets hijos debajo del título de la tarjeta
        self.diseno.addWidget(widget)

    def agregar_diseno(self, diseno: QHBoxLayout) -> None:
        # Igual, pero para agregar un layout completo (ej: una fila con etiqueta + input)
        self.diseno.addLayout(diseno)


class PanelControl(QWidget):
    # Este es el panel lateral completo con TODOS los controles que el usuario manipula:
    # botón de cargar imagen, elegir grid o imagen completa, elegir método, rangos, etc.

    # Señales que el panel emite hacia afuera (hacia ventana_principal.py probablemente,
    # que es quien coordina qué pasa cuando el usuario interactúa)
    solicitud_cargar_imagen = Signal()
    # Se emite cuando el usuario presiona "Cargar imagen JPG" (sin datos, solo "avisa")

    solicitud_procesar = Signal()
    # Se emite cuando el usuario presiona "Procesar imagen"

    cambio_modo_grid = Signal(bool)
    # Se emite cuando cambia entre modo "grid" y "imagen completa" (True/False)

    cambio_tamano_grid = Signal(int)
    # Se emite cuando el usuario cambia el tamaño del grid con el QSpinBox

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("PanelLateral")
        self.setMinimumWidth(340)
        self.setMaximumWidth(400)
        # El panel siempre mide entre 340 y 400px de ancho (no se estira más ni menos)

        self._construir_interfaz()
        self._conectar_senales()
        self.establecer_imagen_cargada(False)
        # Al iniciar, no hay imagen cargada, así que el botón "Procesar" empieza deshabilitado

    def _construir_interfaz(self) -> None:
        diseno_raiz = QVBoxLayout(self)
        diseno_raiz.setContentsMargins(0, 0, 0, 0)
        diseno_raiz.setSpacing(0)

        area_scroll = QScrollArea()
        area_scroll.setObjectName("AreaScrollControl")
        area_scroll.setWidgetResizable(True)
        # Permite que el contenido interno se redimensione junto con el área de scroll
        area_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Nunca muestra scroll horizontal (solo vertical si hace falta, ej. en pantallas chicas)

        contenido = QWidget()
        contenido.setObjectName("ContenidoControl")
        # Este widget interno es el que realmente contiene todo; el QScrollArea
        # solo "envuelve" a este widget para poder scrollearlo si no cabe

        diseno = QVBoxLayout(contenido)
        diseno.setContentsMargins(18, 18, 18, 18)
        diseno.setSpacing(14)

        titulo = QLabel("Panel de control")
        titulo.setObjectName("TituloPanel")

        subtitulo = QLabel("Configura la imagen, el área de análisis y el método.")
        subtitulo.setObjectName("SubtituloPanel")
        subtitulo.setWordWrap(True)
        # Permite que el texto haga salto de línea si no cabe en el ancho disponible

        self.boton_cargar = QPushButton("Cargar imagen JPG")
        self.boton_cargar.setObjectName("BotonPrimario")

        self.etiqueta_validacion = QLabel("Estado: sin imagen cargada")
        self.etiqueta_validacion.setObjectName("EstadoNeutral")
        self.etiqueta_validacion.setWordWrap(True)
        # Esta etiqueta cambia de texto/color cuando la imagen es válida o inválida
        # (ver establecer_estado_validacion más abajo) — conecta con la validación
        # que vimos en cargador_imagen.py

        diseno.addWidget(titulo)
        diseno.addWidget(subtitulo)
        diseno.addWidget(self.boton_cargar)
        diseno.addWidget(self.etiqueta_validacion)
        diseno.addWidget(self._crear_separador())

        # Cada "tarjeta" agrupa un bloque de opciones relacionadas
        diseno.addWidget(self._crear_tarjeta_analisis())   # grid vs imagen completa
        diseno.addWidget(self._crear_tarjeta_grid())        # tamaño del grid
        diseno.addWidget(self._crear_tarjeta_metodo())      # expansión vs ecualización
        diseno.addWidget(self._crear_tarjeta_rango())       # intensidad mínima/máxima

        self.boton_procesar = QPushButton("Procesar imagen")
        self.boton_procesar.setObjectName("BotonExito")

        self.etiqueta_info_grid = QLabel("Grid: x=40, y=40, tamaño=15 px")
        self.etiqueta_info_grid.setObjectName("InfoPequena")
        self.etiqueta_info_grid.setWordWrap(True)
        # Muestra en tiempo real la posición/tamaño actual del grid
        # (se actualiza con actualizar_posicion_grid, llamado probablemente cuando
        # LienzoImagen emite su señal cambio_posicion_grid)

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
        # addStretch() agrega un "espacio elástico" al final: empuja todo el contenido
        # hacia arriba y deja el espacio vacío restante abajo (si lo hay)

        area_scroll.setWidget(contenido)
        # Coloca el widget de contenido DENTRO del área con scroll
        diseno_raiz.addWidget(area_scroll)

    def _crear_tarjeta_analisis(self) -> TarjetaOpcion:
        # Construye la tarjeta donde el usuario elige: ¿analizar con grid o imagen completa?
        tarjeta = TarjetaOpcion("Modo de análisis")
        tarjeta.setMinimumHeight(105)

        self.radio_grid = QRadioButton("Usar grid sobre la imagen")
        self.radio_imagen_completa = QRadioButton("Analizar imagen completa")

        self.radio_grid.setChecked(True)
        # Por defecto, el modo grid viene seleccionado

        self.grupo_analisis = QButtonGroup(self)
        # QButtonGroup asegura que solo UNO de los dos radio buttons pueda estar
        # marcado a la vez (comportamiento de "selección única" tipo radio)
        self.grupo_analisis.addButton(self.radio_grid)
        self.grupo_analisis.addButton(self.radio_imagen_completa)

        tarjeta.agregar_widget(self.radio_grid)
        tarjeta.agregar_widget(self.radio_imagen_completa)

        return tarjeta

    def _crear_tarjeta_grid(self) -> TarjetaOpcion:
        # Construye la tarjeta donde se ajusta el tamaño del cuadrito/grid
        tarjeta = TarjetaOpcion("Tamaño del grid")
        tarjeta.setMinimumHeight(92)

        fila = QHBoxLayout()
        fila.setSpacing(10)

        etiqueta = QLabel("Tamaño:")
        etiqueta.setObjectName("EtiquetaCampo")

        self.selector_tamano_grid = QSpinBox()
        self.selector_tamano_grid.setRange(15, 150)
        # El tamaño del grid puede ir de 15 a 150 unidades/píxeles reales
        self.selector_tamano_grid.setSingleStep(5)
        # Cada click en las flechitas sube/baja de 5 en 5
        self.selector_tamano_grid.setValue(TAMANO_GRID_PREDETERMINADO)
        # Valor inicial: 15 (la constante que vimos al principio)
        self.selector_tamano_grid.setSuffix(" px")
        # Muestra " px" después del número automáticamente (ej: "15 px")

        fila.addWidget(etiqueta)
        fila.addWidget(self.selector_tamano_grid, stretch=1)
        # stretch=1 en el spinbox: ocupa todo el espacio horizontal restante de la fila

        tarjeta.agregar_diseno(fila)

        return tarjeta

    def _crear_tarjeta_metodo(self) -> TarjetaOpcion:
        # Construye la tarjeta donde el usuario elige expansión o ecualización
        tarjeta = TarjetaOpcion("Método de procesamiento")
        tarjeta.setMinimumHeight(105)

        self.radio_expansion = QRadioButton("Expansión de histograma")
        self.radio_ecualizacion = QRadioButton("Ecualización de histograma")

        self.radio_expansion.setChecked(True)
        # Por defecto, expansión viene seleccionada

        self.grupo_metodo = QButtonGroup(self)
        self.grupo_metodo.addButton(self.radio_expansion)
        self.grupo_metodo.addButton(self.radio_ecualizacion)

        tarjeta.agregar_widget(self.radio_expansion)
        tarjeta.agregar_widget(self.radio_ecualizacion)

        return tarjeta

    def _crear_tarjeta_rango(self) -> TarjetaOpcion:
        # Construye la tarjeta donde se eligen los valores s_min y s_max
        # (los mismos parámetros que recibe procesador_histograma.py)
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
        # Ambos limitados al rango 0-255 (constantes de constantes.py)

        self.selector_minimo.setValue(40)
        self.selector_maximo.setValue(130)
        # Valores iniciales sugeridos (no 0 y 255, sino un ejemplo intermedio)

        fila_minima.addWidget(etiqueta_minima)
        fila_minima.addWidget(self.selector_minimo, stretch=1)

        fila_maxima.addWidget(etiqueta_maxima)
        fila_maxima.addWidget(self.selector_maximo, stretch=1)

        tarjeta.agregar_diseno(fila_minima)
        tarjeta.agregar_diseno(fila_maxima)

        return tarjeta

    def _crear_separador(self) -> QFrame:
        # Crea una simple línea horizontal divisoria entre secciones
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        # HLine = línea horizontal (en vez de un marco rectangular completo)
        linea.setObjectName("Separador")
        return linea

    def _conectar_senales(self) -> None:
        # Conecta los eventos internos de Qt (clicks, cambios de valor) con
        # las señales PROPIAS del panel, o con métodos internos que reaccionan

        self.boton_cargar.clicked.connect(self.solicitud_cargar_imagen.emit)
        # Cuando se hace click en "Cargar imagen", simplemente reemite la señal
        # solicitud_cargar_imagen hacia quien esté escuchando (ventana_principal.py)

        self.boton_procesar.clicked.connect(self.solicitud_procesar.emit)

        self.radio_grid.toggled.connect(self._al_cambiar_modo_grid)
        # toggled se dispara cada vez que el estado marcado/desmarcado cambia

        self.selector_tamano_grid.valueChanged.connect(self.cambio_tamano_grid.emit)
        # Reenvía directamente el nuevo valor numérico hacia afuera

    def _al_cambiar_modo_grid(self, marcado: bool) -> None:
        # Se ejecuta cuando el radio "Usar grid" cambia de estado
        self.selector_tamano_grid.setEnabled(marcado)
        # Si el modo grid NO está activo, deshabilita el selector de tamaño
        # (no tiene sentido elegir tamaño de grid si se va a analizar la imagen completa)
        self.cambio_modo_grid.emit(marcado)
        # Avisa hacia afuera el nuevo modo (probablemente lo escucha LienzoImagen
        # para activar/desactivar el dibujo del grid)

    def establecer_imagen_cargada(self, cargada: bool) -> None:
        # Llamado desde afuera (ventana_principal.py) cuando se carga o no una imagen
        self.boton_procesar.setEnabled(cargada)
        # El botón "Procesar" solo se puede usar si HAY una imagen cargada

    def establecer_estado_validacion(self, valido: bool) -> None:
        # Llamado desde afuera con el resultado de cargador_imagen.py (exito/error)
        if valido:
            self.etiqueta_validacion.setText("Estado: imagen válida en escala de grises")
            self.etiqueta_validacion.setObjectName("EstadoExito")
            # Cambia el objectName para que el QSS/CSS le aplique un estilo distinto (ej. verde)
        else:
            self.etiqueta_validacion.setText("Estado: imagen inválida")
            self.etiqueta_validacion.setObjectName("EstadoError")
            # Estilo de error (probablemente rojo)

        self.etiqueta_validacion.setStyleSheet("")
        self.etiqueta_validacion.style().unpolish(self.etiqueta_validacion)
        self.etiqueta_validacion.style().polish(self.etiqueta_validacion)
        self.etiqueta_validacion.update()
        # Este bloque es un "truco" típico de Qt: cambiar el objectName en tiempo de
        # ejecución NO actualiza automáticamente el estilo visual aplicado por QSS.
        # unpolish + polish fuerza a Qt a "releer" el estilo CSS para el nuevo objectName
        # (sin esto, el color/estilo se quedaría con el de antes aunque cambie el texto)

    def obtener_metodo_seleccionado(self) -> str:
        # Traduce la selección visual (radio button) a un string que entiende
        # procesador_histograma.py ("Expansión de histograma" / "Ecualización de histograma")
        if self.radio_expansion.isChecked():
            return "Expansión de histograma"

        return "Ecualización de histograma"

    def obtener_modo_analisis(self) -> str:
        # Similar, pero para el modo de análisis (aunque este string probablemente
        # solo se usa para mostrar en la UI, ya que selector_region.py espera
        # un dict con "activo" y "region_real", no este texto)
        if self.radio_grid.isChecked():
            return "Región seleccionada"

        return "Imagen completa"

    def obtener_rango_intensidad(self) -> tuple[int, int]:
        # Devuelve (s_min, s_max) tal cual los espera procesar_imagen()
        return self.selector_minimo.value(), self.selector_maximo.value()

    def actualizar_posicion_grid(self, x: int, y: int, tamano: int) -> None:
        # Llamado desde afuera (probablemente conectado a la señal
        # cambio_posicion_grid de VisorImagen) para refrescar el texto informativo
        self.etiqueta_info_grid.setText(f"Grid: x={x}, y={y}, tamaño={tamano} pixeles")