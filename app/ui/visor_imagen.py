from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy

from app.utilidades.constantes import TAMANO_GRID_PREDETERMINADO


class LienzoImagen(QWidget):
    cambio_posicion_grid = Signal(int, int, int)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("LienzoImagen")

        self.setMinimumHeight(480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pixmap_original: QPixmap | None = None
        self.pixmap_escalado: QPixmap | None = None

        self.grid_habilitado = True
        self.tamano_grid = TAMANO_GRID_PREDETERMINADO

        self.grid_x = 40
        self.grid_y = 40

        self.arrastrando = False
        self.desfase_arrastre_x = 0
        self.desfase_arrastre_y = 0

    def cargar_imagen(self, ruta_archivo: str) -> None:
        self.pixmap_original = QPixmap(ruta_archivo)

        self.grid_x = 40
        self.grid_y = 40

        self._actualizar_pixmap_escalado()
        self._limitar_grid_a_imagen()

        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)

        self.update()

    def establecer_grid_habilitado(self, habilitado: bool) -> None:
        self.grid_habilitado = habilitado
        self.update()

    def establecer_tamano_grid(self, tamano: int) -> None:
        self.tamano_grid = tamano
        self._limitar_grid_a_imagen()
        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)
        self.update()

    def obtener_datos_grid(self) -> dict:
        return {
            "x_visual": self.grid_x,
            "y_visual": self.grid_y,
            "tamano_visual": self.tamano_grid,
            "activo": self.grid_habilitado,
            "region_real": self.obtener_region_real_grid(),
        }

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def resizeEvent(self, event) -> None:
        self._actualizar_pixmap_escalado()
        self._limitar_grid_a_imagen()
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)

        self._dibujar_fondo(pintor)

        if self.pixmap_escalado is None:
            self._dibujar_estado_vacio(pintor)
            return

        rectangulo_imagen = self._obtener_rectangulo_imagen()
        pintor.drawPixmap(rectangulo_imagen, self.pixmap_escalado)

        if self.grid_habilitado:
            self._dibujar_grid(pintor)

    def mousePressEvent(self, event) -> None:
        if not self.grid_habilitado or self.pixmap_escalado is None:
            return

        if event.button() == Qt.LeftButton:
            rectangulo_grid = QRect(self.grid_x, self.grid_y, self.tamano_grid, self.tamano_grid)

            if rectangulo_grid.contains(event.position().toPoint()):
                self.arrastrando = True
                self.desfase_arrastre_x = int(event.position().x()) - self.grid_x
                self.desfase_arrastre_y = int(event.position().y()) - self.grid_y
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if not self.arrastrando:
            return

        self.grid_x = int(event.position().x()) - self.desfase_arrastre_x
        self.grid_y = int(event.position().y()) - self.desfase_arrastre_y

        self._limitar_grid_a_imagen()
        self.cambio_posicion_grid.emit(self.grid_x, self.grid_y, self.tamano_grid)

        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.arrastrando = False
            self.setCursor(Qt.ArrowCursor)

    def _actualizar_pixmap_escalado(self) -> None:
        if self.pixmap_original is None:
            self.pixmap_escalado = None
            return

        ancho_disponible = max(1, self.width() - 28)
        alto_disponible = max(1, self.height() - 28)

        self.pixmap_escalado = self.pixmap_original.scaled(
            ancho_disponible,
            alto_disponible,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

    def _obtener_rectangulo_imagen(self) -> QRect:
        if self.pixmap_escalado is None:
            return QRect()

        x = (self.width() - self.pixmap_escalado.width()) // 2
        y = (self.height() - self.pixmap_escalado.height()) // 2

        return QRect(x, y, self.pixmap_escalado.width(), self.pixmap_escalado.height())

    def _dibujar_fondo(self, pintor: QPainter) -> None:
        pintor.setPen(QPen(QColor("#CBD5E1"), 2, Qt.DashLine))
        pintor.setBrush(QBrush(QColor("#F9FAFB")))
        pintor.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

    def _dibujar_estado_vacio(self, pintor: QPainter) -> None:
        pintor.setPen(QColor("#64748B"))
        pintor.drawText(
            self.rect(),
            Qt.AlignCenter,
            "Carga una imagen JPG en escala de grises",
        )

    def _dibujar_grid(self, pintor: QPainter) -> None:
        rectangulo = QRect(self.grid_x, self.grid_y, self.tamano_grid, self.tamano_grid)

        pintor.setBrush(QBrush(QColor(59, 130, 246, 45)))
        pintor.setPen(QPen(QColor(37, 99, 235), 2))
        pintor.drawRect(rectangulo)

        pintor.setPen(QPen(QColor(37, 99, 235, 150), 1))

        paso = max(3, self.tamano_grid // 5)

        for x in range(self.grid_x, self.grid_x + self.tamano_grid + 1, paso):
            pintor.drawLine(x, self.grid_y, x, self.grid_y + self.tamano_grid)

        for y in range(self.grid_y, self.grid_y + self.tamano_grid + 1, paso):
            pintor.drawLine(self.grid_x, y, self.grid_x + self.tamano_grid, y)

    def _limitar_grid_a_imagen(self) -> None:
        if self.pixmap_escalado is None:
            self.grid_x = max(0, min(self.grid_x, self.width() - self.tamano_grid))
            self.grid_y = max(0, min(self.grid_y, self.height() - self.tamano_grid))
            return

        rectangulo_imagen = self._obtener_rectangulo_imagen()

        minimo_x = rectangulo_imagen.left()
        minimo_y = rectangulo_imagen.top()
        maximo_x = rectangulo_imagen.right() - self.tamano_grid
        maximo_y = rectangulo_imagen.bottom() - self.tamano_grid

        self.grid_x = max(minimo_x, min(self.grid_x, maximo_x))
        self.grid_y = max(minimo_y, min(self.grid_y, maximo_y))

    def obtener_region_real_grid(self) -> dict | None:
        # Convierte la posición visual del grid en coordenadas reales de la imagen original.
        # Retorna un diccionario con las medidas reales del recorte.
        # Si no hay imagen o el grid está desactivado, retorna none.

        if self.pixmap_original is None or self.pixmap_escalado is None:
            return None

        if not self.grid_habilitado:
            return None

        rect_imagen = self._obtener_rectangulo_imagen()

        if rect_imagen.width() <= 0 or rect_imagen.height() <= 0:
            return None

        escala_x = self.pixmap_original.width() / rect_imagen.width()
        escala_y = self.pixmap_original.height() / rect_imagen.height()

        x_visual_relativo = self.grid_x - rect_imagen.left()
        y_visual_relativo = self.grid_y - rect_imagen.top()

        x_real = int(round(x_visual_relativo * escala_x))
        y_real = int(round(y_visual_relativo * escala_y))

        ancho_real = int(round(self.tamano_grid * escala_x))
        alto_real = int(round(self.tamano_grid * escala_y))

        x_real = max(0, min(x_real, self.pixmap_original.width() - 1))
        y_real = max(0, min(y_real, self.pixmap_original.height() - 1))

        ancho_real = max(1, min(ancho_real, self.pixmap_original.width() - x_real))
        alto_real = max(1, min(alto_real, self.pixmap_original.height() - y_real))

        return {
            "x": x_real,
            "y": y_real,
            "ancho": ancho_real,
            "alto": alto_real,
        }


class VisorImagen(QWidget):
    cambio_posicion_grid = Signal(int, int, int)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("Tarjeta")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lienzo = LienzoImagen()
        self.lienzo.cambio_posicion_grid.connect(self.cambio_posicion_grid.emit)

        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(18, 14, 18, 18)
        diseno.setSpacing(6)

        titulo = QLabel("Vista de imagen")
        titulo.setObjectName("TituloSeccion")
        titulo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        ayuda = QLabel("Arrastra el grid sobre la zona que deseas analizar.")
        ayuda.setObjectName("AyudaSeccion")
        ayuda.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        diseno.addWidget(titulo)
        diseno.addWidget(ayuda)
        diseno.addSpacing(6)
        diseno.addWidget(self.lienzo, stretch=1)

    def cargar_imagen(self, ruta_archivo: str) -> None:
        self.lienzo.cargar_imagen(ruta_archivo)

    def establecer_grid_habilitado(self, habilitado: bool) -> None:
        self.lienzo.establecer_grid_habilitado(habilitado)

    def establecer_tamano_grid(self, tamano: int) -> None:
        self.lienzo.establecer_tamano_grid(tamano)

    def obtener_datos_grid(self) -> dict:
        return self.lienzo.obtener_datos_grid()
