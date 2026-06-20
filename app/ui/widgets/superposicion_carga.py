from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
# QProgressBar: la típica barra de "cargando" — aquí se usa en modo indeterminado
# (sin porcentaje fijo, solo animación de "está trabajando")


class SuperposicionCarga(QWidget):
    # Este widget es un "overlay" (capa flotante semi-transparente) que se dibuja
    # ENCIMA de toda la ventana mientras se procesa la imagen, bloqueando
    # visualmente la interacción y mostrando un mensaje de "cargando"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # parent: el widget "padre" sobre el cual se va a superponer (normalmente
        # la ventana principal completa). Pasarlo a super() lo registra dentro
        # de la jerarquía de Qt para que se posicione/destruya correctamente

        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # False = este widget SÍ "atrapa" los clicks del mouse (no los deja pasar
        # a los widgets debajo). Esto es justamente lo que bloquea la interacción
        # con el resto de la app mientras se está procesando

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # Le dice a Qt que no dibuje un fondo "por defecto" del sistema operativo,
        # porque este widget va a dibujar su propio fondo semi-transparente manualmente
        # (en paintEvent)

        self.setVisible(False)
        # Empieza oculto: solo aparece cuando se llama a mostrar_superposicion()

        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)
        diseno.setAlignment(Qt.AlignCenter)
        # Centra todo el contenido (la tarjeta) tanto vertical como horizontalmente
        diseno.setSpacing(16)

        self.tarjeta = QWidget()
        self.tarjeta.setObjectName("TarjetaCarga")
        # Esta es la "cajita" blanca/clara que aparece en el centro de la pantalla
        # con el mensaje de carga (visualmente diferenciada del fondo oscuro)

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
        # CLAVE: setRange(0, 0) pone la barra en modo "indeterminado"
        # (la animación de rayitas moviéndose, sin mostrar un % específico)
        # Se usa cuando no sabes cuánto va a tardar el proceso exactamente

        diseno_tarjeta.addWidget(self.titulo)
        diseno_tarjeta.addWidget(self.subtitulo)
        diseno_tarjeta.addWidget(self.progreso)

        diseno.addWidget(self.tarjeta)

    def mostrar_superposicion(self, mensaje: str = "Procesando imagen...") -> None:
        # Llamado desde afuera justo ANTES de empezar a procesar la imagen
        self.titulo.setText(mensaje)
        # Permite personalizar el texto si se quiere (por defecto "Procesando imagen...")

        self.setGeometry(self.parent().rect())
        # Hace que este widget ocupe EXACTAMENTE el mismo tamaño que su padre
        # (toda la ventana), para que el overlay cubra la pantalla completa

        self.raise_()
        # Trae este widget al FRENTE de la pila de widgets (z-order), asegurando
        # que se dibuje por encima de todo lo demás, no escondido detrás

        self.setVisible(True)

    def ocultar_superposicion(self) -> None:
        # Llamado cuando termina el procesamiento (éxito o error)
        self.setVisible(False)

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def resizeEvent(self, event) -> None:
        # Si el padre cambia de tamaño (ej. se maximiza la ventana) mientras
        # el overlay está visible, este método lo redimensiona para que siga
        # cubriendo toda la pantalla y no quede "descuadrado"
        if self.parent():
            self.setGeometry(self.parent().rect())

        super().resizeEvent(event)

    # Este método conserva su nombre en inglés porque Qt lo llama automáticamente.
    def paintEvent(self, event) -> None:
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor(17, 24, 39, 145))
        # Pinta todo el widget con un color oscuro casi negro (17, 24, 39)
        # con transparencia 145/255 (~57% opaco). Esto crea el efecto de
        # "oscurecer" el fondo de la app mientras se procesa, dejando ver
        # difusamente lo que hay detrás — el clásico efecto "modal overlay"