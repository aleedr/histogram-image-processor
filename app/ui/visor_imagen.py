from PySide6.QtCore import Qt, QRect, Signal
# PySide6: es el binding oficial de Qt para Python. Qt es un framework para
# construir interfaces gráficas de escritorio (ventanas, botones, widgets).
# QtCore: módulo con clases "base" sin parte visual:
#   - Qt: namespace con constantes (ej: Qt.LeftButton, Qt.AlignCenter)
#   - QRect: representa un rectángulo (x, y, ancho, alto) — útil para geometría en pantalla
#   - Signal: permite crear "señales" propias (el patrón Observer de Qt) para
#     comunicar eventos entre widgets sin que estén directamente acoplados

from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
# QtGui: módulo con clases relacionadas a gráficos/dibujo (pero sin lógica de widgets)
#   - QPixmap: representa una imagen cargada en memoria, lista para dibujarse
#   - QPainter: el "pincel" que permite dibujar formas, líneas, texto sobre un widget
#   - QPen: define el estilo del trazo/línea (color, grosor, tipo de línea)
#   - QColor: representa un color (RGB/RGBA)
#   - QBrush: define el relleno de una forma (color/textura de fondo)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
# QtWidgets: módulo con los widgets visuales reales (botones, layouts, etiquetas)
#   - QWidget: clase base de CUALQUIER elemento visual en Qt (ventanas, paneles, etc.)
#   - QVBoxLayout: organiza widgets hijos en una columna vertical automáticamente
#   - QLabel: widget simple para mostrar texto (o imágenes)
#   - QSizePolicy: define cómo se comporta un widget al cambiar de tamaño
#     (ej: si se expande para llenar espacio o mantiene tamaño fijo)

from app.utilidades.constantes import TAMANO_GRID_PREDETERMINADO
# Reutiliza la constante que vimos antes (15 por defecto) para el tamaño inicial del grid


class LienzoImagen(QWidget):
    # "Lienzo" = el área donde se dibuja la imagen Y el cuadrito de selección (grid)
    # Hereda de QWidget, así que ES un widget de Qt y puede pintarse, recibir clicks, etc.

    cambio_posicion_grid = Signal(int, int, int)
    # Declaración de una SEÑAL propia llamada "cambio_posicion_grid".
    # Cuando el grid cambia de posición o tamaño, este widget "emite" esta señal
    # con 3 enteros (x, y, tamaño). Otros widgets (como panel_control.py) pueden
    # "escuchar" (connect) esta señal para reaccionar, sin que LienzoImagen sepa
    # nada de quién la está escuchando. Es el patrón Observer/Publish-Subscribe de Qt.

    def __init__(self) -> None:
        super().__init__()
        # Llama al constructor de QWidget para inicializar todo lo necesario de Qt

        self.setObjectName("LienzoImagen")
        # Nombre interno usado normalmente para aplicar estilos CSS/QSS (archivos en assets/estilos)

        self.setMinimumHeight(480)
        # Fuerza que el widget nunca sea más chico que 480px de alto

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Le dice al layout padre: "si hay espacio disponible, dame todo el que puedas"
        # (tanto horizontal como vertical)

        self.pixmap_original: QPixmap | None = None
        # Guarda la imagen ORIGINAL cargada, en su resolución real, sin escalar.
        # "| None" indica que puede no haber imagen cargada todavía

        self.pixmap_escalado: QPixmap | None = None
        # Versión de la imagen ya REDIMENSIONADA para caber en el widget actual
        # (se recalcula cada vez que la ventana cambia de tamaño)

        self.grid_habilitado = True
        # Si el grid (cuadrito de selección) está activo o no

        self.tamano_grid = TAMANO_GRID_PREDETERMINADO
        # Tamaño del cuadrito EN UNIDADES REALES de la imagen (no en píxeles de pantalla)
        # Esta distinción "real vs visual" es clave en todo el archivo

        self.grid_x = 40
        self.grid_y = 40
        # Posición inicial del grid (en coordenadas visuales/de pantalla)

        self.arrastrando = False
        # Flag que indica si el usuario está actualmente arrastrando el grid con el mouse

        self.desfase_arrastre_x = 0
        self.desfase_arrastre_y = 0
        # Guarda la diferencia entre dónde clickeaste dentro del cuadrito y su esquina
        # superior izquierda. Esto evita que el cuadrito "salte" a estar centrado en el
        # cursor apenas empiezas a arrastrar — mantiene el punto exacto donde agarraste

    def cargar_imagen(self, ruta_archivo: str) -> None:
        # Se llama desde fuera (probablemente desde pagina_procesamiento.py) cuando
        # el usuario selecciona un archivo de imagen
        self.pixmap_original = QPixmap(ruta_archivo)
        # QPixmap puede construirse directamente desde una ruta de archivo

        self.grid_x = 40
        self.grid_y = 40
        # Reinicia la posición del grid cada vez que se carga una imagen nueva

        self._actualizar_pixmap_escalado()
        # Recalcula la versión escalada para el tamaño actual del widget

        self._limitar_grid_a_imagen()
        # Asegura que el grid no quede fuera de los límites de la nueva imagen

        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)
        # Notifica a quien esté escuchando (ej: panel_control.py) la posición inicial

        self.update()
        # Le dice a Qt: "este widget cambió, hay que redibujarlo"
        # (dispara paintEvent en el próximo ciclo de renderizado)

    def establecer_grid_habilitado(self, habilitado: bool) -> None:
        # Setter llamado probablemente desde un checkbox en panel_control.py
        self.grid_habilitado = habilitado
        self.update()

    def establecer_tamano_grid(self, tamano: int) -> None:
        # Setter llamado probablemente desde un slider/input numérico de tamaño de grid
        self.tamano_grid = tamano
        self._limitar_grid_a_imagen()
        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)
        self.update()

    def obtener_datos_grid(self) -> dict:
        # Esta es la función que arma el diccionario "datos_grid" que recibe
        # selector_region.py para decidir si recortar la imagen o no
        return {
            "x_visual": self.grid_x,
            "y_visual": self.grid_y,
            "tamano_real": self.tamano_grid,
            "activo": self.grid_habilitado,
            "region_real": self.obtener_region_real_grid(),
            # region_real es lo que selector_region.py realmente usa (x, y, ancho, alto reales)
    }

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def resizeEvent(self, event) -> None:
        # Qt llama esta función AUTOMÁTICAMENTE cada vez que el widget cambia de tamaño
        # (ej: el usuario maximiza la ventana). Es un método "override" de QWidget.
        self._actualizar_pixmap_escalado()
        self._limitar_grid_a_imagen()
        super().resizeEvent(event)
        # Llama también a la versión original de QWidget para no romper comportamiento base

    def paintEvent(self, event) -> None:
        # Qt llama esta función AUTOMÁTICAMENTE cada vez que el widget necesita
        # redibujarse (ej: tras llamar a self.update(), o al abrir la ventana)
        pintor = QPainter(self)
        # Crea el "pincel" que dibuja directamente sobre este widget

        pintor.setRenderHint(QPainter.Antialiasing)
        # Suaviza los bordes de las formas dibujadas (anti-aliasing), se ve menos "pixeleado"

        self._dibujar_fondo(pintor)
        # Dibuja el rectángulo de fondo con borde punteado (estilo "drop zone")

        if self.pixmap_escalado is None:
            # Si todavía no se cargó ninguna imagen, muestra un mensaje en vez de la imagen
            self._dibujar_estado_vacio(pintor)
            return

        rectangulo_imagen = self._obtener_rectangulo_imagen()
        pintor.drawPixmap(rectangulo_imagen, self.pixmap_escalado)
        # Dibuja la imagen escalada dentro del rectángulo calculado (centrada)

        if self.grid_habilitado:
            self._dibujar_grid(pintor)
            # Solo dibuja el cuadrito de selección si está habilitado

    def mousePressEvent(self, event) -> None:
        # Qt llama esto automáticamente cuando el usuario hace click dentro del widget
        if not self.grid_habilitado or self.pixmap_escalado is None:
            return
            # Si no hay grid activo o no hay imagen, ignora el click

        if event.button() == Qt.LeftButton:
            # Solo reacciona al botón IZQUIERDO del mouse
            ancho_visual, alto_visual = self._obtener_tamano_grid_visual()
            rectangulo_grid = QRect(self.grid_x, self.grid_y, ancho_visual, alto_visual)

            if rectangulo_grid.contains(event.position().toPoint()):
                # .contains() verifica si el punto donde clickeaste está DENTRO
                # del rectángulo del grid (solo entonces se puede empezar a arrastrar)
                self.arrastrando = True
                self.desfase_arrastre_x = int(event.position().x()) - self.grid_x
                self.desfase_arrastre_y = int(event.position().y()) - self.grid_y
                # Guarda dónde, dentro del cuadrito, hiciste click (offset)
                self.setCursor(Qt.ClosedHandCursor)
                # Cambia el cursor del mouse a una "mano cerrada" (feedback visual de arrastre)

    def mouseMoveEvent(self, event) -> None:
        # Qt llama esto automáticamente cada vez que el mouse se mueve sobre el widget
        if not self.arrastrando:
            return
            # Si no estás arrastrando, no hace nada (evita mover el grid solo por pasar el mouse)

        self.grid_x = int(event.position().x()) - self.desfase_arrastre_x
        self.grid_y = int(event.position().y()) - self.desfase_arrastre_y
        # Nueva posición del grid = posición del mouse menos el offset guardado antes
        # (así el cuadrito se mueve "pegado" al punto exacto donde lo agarraste)

        self._limitar_grid_a_imagen()
        # Evita que el grid se salga del área de la imagen mientras arrastras

        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)
        # Notifica en tiempo real la nueva posición (ej: para actualizar coordenadas en pantalla)

        self.update()
        # Redibuja el widget con la nueva posición

    def mouseReleaseEvent(self, event) -> None:
        # Qt llama esto cuando se suelta el botón del mouse
        if event.button() == Qt.LeftButton:
            self.arrastrando = False
            self.setCursor(Qt.ArrowCursor)
            # Vuelve el cursor a la flecha normal

    def _actualizar_pixmap_escalado(self) -> None:
        # Método "privado" (por convención, el guion bajo indica uso interno)
        if self.pixmap_original is None:
            self.pixmap_escalado = None
            return

        ancho_disponible = max(1, self.width() - 28)
        alto_disponible = max(1, self.height() - 28)
        # Resta 28px como margen interno (padding visual), nunca menor a 1 para evitar errores

        self.pixmap_escalado = self.pixmap_original.scaled(
            ancho_disponible,
            alto_disponible,
            Qt.KeepAspectRatio,
            # Mantiene la proporción original de la imagen (no la deforma)
            Qt.SmoothTransformation,
            # Usa un algoritmo de escalado suavizado (mejor calidad visual que el básico)
        )

    def _obtener_rectangulo_imagen(self) -> QRect:
        # Calcula dónde exactamente se dibuja la imagen DENTRO del widget (centrada)
        if self.pixmap_escalado is None:
            return QRect()

        x = (self.width() - self.pixmap_escalado.width()) // 2
        y = (self.height() - self.pixmap_escalado.height()) // 2
        # Centrado clásico: (espacio total - tamaño del contenido) / 2

        return QRect(x, y, self.pixmap_escalado.width(), self.pixmap_escalado.height())

    def _dibujar_fondo(self, pintor: QPainter) -> None:
        pintor.setPen(QPen(QColor("#CBD5E1"), 2, Qt.DashLine))
        # Línea gris clara, 2px de grosor, punteada (Qt.DashLine)
        pintor.setBrush(QBrush(QColor("#F9FAFB")))
        # Relleno gris muy claro/casi blanco
        pintor.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        # Dibuja un rectángulo con esquinas redondeadas (radio 14px)
        # .adjusted(1,1,-1,-1) reduce el rectángulo 1px en cada borde para que
        # la línea no se corte en el borde exacto del widget

    def _dibujar_estado_vacio(self, pintor: QPainter) -> None:
        pintor.setPen(QColor("#64748B"))
        pintor.drawText(
            self.rect(),
            Qt.AlignCenter,
            "Carga una imagen JPG en escala de grises",
        )
        # Mensaje centrado cuando todavía no hay imagen cargada

    def _obtener_tamano_grid_visual(self) -> tuple[int, int]:
        """
        Convierte el tamaño real del grid a tamaño visual en pantalla.

        self.tamano_grid representa unidades reales de la imagen.
        Para dibujarlo, se convierte al tamaño equivalente en pantalla.
        """
        # PUNTO CLAVE de todo el archivo: la imagen real puede ser, ej, 1200x800 px,
        # pero en pantalla se muestra escalada a, digamos, 600x400. Por lo tanto,
        # un grid de "15x15 unidades reales" no mide 15x15 píxeles en PANTALLA,
        # sino proporcionalmente más chico. Esta función hace esa conversión.

        if self.pixmap_original is None or self.pixmap_escalado is None:
            return self.tamano_grid, self.tamano_grid
            # Sin imagen cargada, no hay escala que aplicar; devuelve el valor tal cual

        rectangulo_imagen = self._obtener_rectangulo_imagen()

        if rectangulo_imagen.width() <= 0 or rectangulo_imagen.height() <= 0:
            return self.tamano_grid, self.tamano_grid

        escala_visual_x = rectangulo_imagen.width() / self.pixmap_original.width()
        escala_visual_y = rectangulo_imagen.height() / self.pixmap_original.height()
        # Factor de escala = (tamaño en pantalla) / (tamaño real)

        ancho_visual = int(round(self.tamano_grid * escala_visual_x))
        alto_visual = int(round(self.tamano_grid * escala_visual_y))
        # Aplica el factor de escala al tamaño real del grid

        ancho_visual = max(1, ancho_visual)
        alto_visual = max(1, alto_visual)
        # Nunca permite que el grid se dibuje con tamaño 0 (invisible)

        return ancho_visual, alto_visual

    def _dibujar_grid(self, pintor: QPainter) -> None:
        ancho_visual, alto_visual = self._obtener_tamano_grid_visual()

        rectangulo = QRect(self.grid_x, self.grid_y, ancho_visual, alto_visual)

        pintor.setBrush(QBrush(QColor(59, 130, 246, 45)))
        # Azul semi-transparente (el 4to número, 45, es el canal Alpha/transparencia de 0-255)
        pintor.setPen(QPen(QColor(37, 99, 235), 2))
        # Borde azul más sólido/oscuro, 2px
        pintor.drawRect(rectangulo)
        # Dibuja el cuadrito de selección sobre la imagen

        pintor.setPen(QPen(QColor(37, 99, 235, 150), 1))
        # Cambia a un pincel más fino para las líneas internas de la cuadrícula

        paso = max(3, min(ancho_visual, alto_visual) // 5)
        # Calcula cada cuántos píxeles dibujar una línea divisoria interna
        # (divide el cuadrito en ~5 secciones, mínimo 3px de separación)

        for x in range(self.grid_x, self.grid_x + ancho_visual + 1, paso):
            pintor.drawLine(x, self.grid_y, x, self.grid_y + alto_visual)
            # Líneas verticales internas (efecto "cuadrícula" dentro del cuadrito)

        for y in range(self.grid_y, self.grid_y + alto_visual + 1, paso):
            pintor.drawLine(self.grid_x, y, self.grid_x + ancho_visual, y)
            # Líneas horizontales internas

    def obtener_region_real_grid(self) -> dict | None:
        """
        Convierte la posición visual del grid en coordenadas reales
        de la imagen original.

        self.tamano_grid representa unidades reales de la imagen.
        Por eso el ancho y alto reales son directamente self.tamano_grid.
        """
        # Esta es la función "inversa" de _obtener_tamano_grid_visual:
        # en vez de convertir tamaño real -> visual, convierte POSICIÓN visual -> real.
        # Es la pieza clave que conecta la UI con selector_region.py

        if self.pixmap_original is None or self.pixmap_escalado is None:
            return None

        if not self.grid_habilitado:
            return None

        rect_imagen = self._obtener_rectangulo_imagen()

        if rect_imagen.width() <= 0 or rect_imagen.height() <= 0:
            return None

        escala_real_x = self.pixmap_original.width() / rect_imagen.width()
        escala_real_y = self.pixmap_original.height() / rect_imagen.height()
        # Factor de escala inverso: (tamaño real) / (tamaño en pantalla)

        x_visual_relativo = self.grid_x - rect_imagen.left()
        y_visual_relativo = self.grid_y - rect_imagen.top()
        # Resta el offset del rectángulo de imagen (porque está centrada, no empieza en 0,0)
        # para obtener la posición del grid RELATIVA al borde de la imagen, no del widget completo

        x_real = int(round(x_visual_relativo * escala_real_x))
        y_real = int(round(y_visual_relativo * escala_real_y))
        # Convierte la posición visual relativa a posición real en la imagen original

        ancho_real = self.tamano_grid
        alto_real = self.tamano_grid
        # El tamaño YA estaba en unidades reales desde el principio (no hace falta convertir)

        x_real = max(0, min(x_real, self.pixmap_original.width() - 1))
        y_real = max(0, min(y_real, self.pixmap_original.height() - 1))
        # Asegura que la posición no se salga de los límites de la imagen real

        ancho_real = max(1, min(ancho_real, self.pixmap_original.width() - x_real))
        alto_real = max(1, min(alto_real, self.pixmap_original.height() - y_real))
        # Asegura que el cuadrito no se salga del borde derecho/inferior

        return {
            "x": x_real,
            "y": y_real,
            "ancho": ancho_real,
            "alto": alto_real,
        }
        # Este diccionario es EXACTAMENTE lo que espera selector_region.py
        # en su parámetro datos_grid["region_real"]
    
    def _limitar_grid_a_imagen(self) -> None:
        # Asegura que el cuadrito de selección (en coordenadas VISUALES/pantalla)
        # nunca se dibuje fuera del área visible de la imagen
        ancho_visual, alto_visual = self._obtener_tamano_grid_visual()

        if self.pixmap_escalado is None:
            # Sin imagen, solo limita contra los bordes del widget completo
            self.grid_x = max(0, min(self.grid_x, self.width() - ancho_visual))
            self.grid_y = max(0, min(self.grid_y, self.height() - alto_visual))
            return

        rectangulo_imagen = self._obtener_rectangulo_imagen()
        minimo_x = rectangulo_imagen.left()
        minimo_y = rectangulo_imagen.top()

        maximo_x = rectangulo_imagen.left() + rectangulo_imagen.width() - ancho_visual
        maximo_y = rectangulo_imagen.top() + rectangulo_imagen.height() - alto_visual
        # Calcula los límites válidos para que el grid quede SIEMPRE dentro del
        # rectángulo donde se dibuja la imagen (no del widget completo, que puede ser más grande)

        self.grid_x = max(minimo_x, min(self.grid_x, maximo_x))
        self.grid_y = max(minimo_y, min(self.grid_y, maximo_y))


class VisorImagen(QWidget):
    # Esta es la clase "contenedora" que se usa desde afuera (pagina_procesamiento.py).
    # Envuelve al LienzoImagen agregándole un título y texto de ayuda.
    # Patrón de diseño: COMPOSICIÓN — VisorImagen "tiene un" LienzoImagen adentro,
    # en vez de heredar de él. Esto separa "la lógica de dibujo/interacción" (Lienzo)
    # de "la presentación con título y ayuda" (Visor)

    cambio_posicion_grid = Signal(int, int, int)
    # Declara su PROPIA señal, que simplemente "reenvía" la señal del lienzo interno

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("Tarjeta")
        # Nombre usado para aplicar estilo CSS de "tarjeta" (probablemente con sombra/borde)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lienzo = LienzoImagen()
        # Crea la instancia del widget de dibujo real

        self.lienzo.cambio_posicion_grid.connect(self.cambio_posicion_grid.emit)
        # CONEXIÓN DE SEÑALES: cuando el lienzo interno emite su señal,
        # automáticamente se reemite la señal de VisorImagen con los mismos datos.
        # Esto permite que quien usa VisorImagen no necesite saber que existe
        # un LienzoImagen escondido adentro — solo se conecta a VisorImagen directamente.

        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)
        # Crea un layout vertical y lo asigna directamente a este widget (self)
        diseno.setContentsMargins(18, 14, 18, 18)
        # Márgenes internos: izquierda, arriba, derecha, abajo
        diseno.setSpacing(6)
        # Espacio entre elementos del layout

        titulo = QLabel("Vista de imagen")
        titulo.setObjectName("TituloSeccion")
        titulo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # "Fixed" en vertical: el título no se estira, mantiene su altura natural

        ayuda = QLabel("Arrastra el grid sobre la zona que deseas analizar.")
        ayuda.setObjectName("AyudaSeccion")
        ayuda.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        diseno.addWidget(titulo)
        diseno.addWidget(ayuda)
        diseno.addSpacing(6)
        diseno.addWidget(self.lienzo, stretch=1)
        # stretch=1: el lienzo ocupa TODO el espacio restante disponible
        # (a diferencia del título y la ayuda, que solo ocupan su tamaño natural)

    # Los siguientes métodos son "delegación": VisorImagen no implementa la lógica,
    # simplemente pasa la llamada al lienzo interno. Esto oculta los detalles
    # internos del Lienzo a quien usa VisorImagen (encapsulamiento)

    def cargar_imagen(self, ruta_archivo: str) -> None:
        self.lienzo.cargar_imagen(ruta_archivo)

    def establecer_grid_habilitado(self, habilitado: bool) -> None:
        self.lienzo.establecer_grid_habilitado(habilitado)

    def establecer_tamano_grid(self, tamano: int) -> None:
        self.lienzo.establecer_tamano_grid(tamano)

    def obtener_datos_grid(self) -> dict:
        return self.lienzo.obtener_datos_grid()