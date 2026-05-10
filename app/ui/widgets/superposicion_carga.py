from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar


class SuperposicionCarga(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setVisible(False)

        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)
        diseno.setAlignment(Qt.AlignCenter)
        diseno.setSpacing(16)

        self.tarjeta = QWidget()
        self.tarjeta.setObjectName("TarjetaCarga")

        diseno_tarjeta = QVBoxLayout(self.tarjeta)
        diseno_tarjeta.setContentsMargins(28, 24, 28, 24)
        diseno_tarjeta.setSpacing(14)
        diseno_tarjeta.setAlignment(Qt.AlignCenter)

        self.titulo = QLabel("Procesando imagen...")
        self.titulo.setObjectName("TituloCarga")
        self.titulo.setAlignment(Qt.AlignCenter)

        self.subtitulo = QLabel("Generando imagen procesada e histogramas.")
        self.subtitulo.setObjectName("SubtituloCarga")
        self.subtitulo.setAlignment(Qt.AlignCenter)

        self.progreso = QProgressBar()
        self.progreso.setObjectName("ProgresoCarga")
        self.progreso.setRange(0, 0)

        diseno_tarjeta.addWidget(self.titulo)
        diseno_tarjeta.addWidget(self.subtitulo)
        diseno_tarjeta.addWidget(self.progreso)

        diseno.addWidget(self.tarjeta)

    def mostrar_superposicion(self, mensaje: str = "Procesando imagen...") -> None:
        self.titulo.setText(mensaje)
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.setVisible(True)

    def ocultar_superposicion(self) -> None:
        self.setVisible(False)

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def resizeEvent(self, event) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())

        super().resizeEvent(event)

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def paintEvent(self, event) -> None:
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor(17, 24, 39, 145))
