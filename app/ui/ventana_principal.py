from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QStackedWidget,
    QMessageBox,
)

from app.ui.pagina_procesamiento import PaginaProcesamiento
from app.ui.pagina_resultados import PaginaResultados
from app.ui.widgets.superposicion_carga import SuperposicionCarga
from app.utilidades.constantes import TITULO_APP


class VentanaPrincipal(QMainWindow):
    INDICE_PAGINA_PROCESAMIENTO = 0
    INDICE_PAGINA_RESULTADOS = 1

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(TITULO_APP)
        self.setMinimumSize(1280, 760)

        self.pagina_procesamiento = PaginaProcesamiento()
        self.pagina_resultados = PaginaResultados()

        self.pila_paginas = QStackedWidget()
        self.superposicion_carga = None

        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)

        self._construir_interfaz()
        self._conectar_senales()
        self._establecer_estado_inicial()

    def _construir_interfaz(self) -> None:
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        diseno_raiz = QVBoxLayout(widget_central)
        diseno_raiz.setContentsMargins(18, 18, 18, 12)
        diseno_raiz.setSpacing(14)

        encabezado = self._crear_encabezado()

        self.pila_paginas.addWidget(self.pagina_procesamiento)
        self.pila_paginas.addWidget(self.pagina_resultados)

        diseno_raiz.addWidget(encabezado)
        diseno_raiz.addWidget(self.pila_paginas, stretch=1)

        self.superposicion_carga = SuperposicionCarga(widget_central)

    def _crear_encabezado(self) -> QWidget:
        encabezado = QWidget()
        encabezado.setObjectName("Encabezado")

        diseno = QVBoxLayout(encabezado)
        diseno.setContentsMargins(18, 14, 18, 14)
        diseno.setSpacing(4)

        titulo = QLabel("Procesador de Histogramas")
        titulo.setObjectName("TituloApp")

        subtitulo = QLabel(
            "Carga una imagen JPG en escala de grises, selecciona una región y aplica expansión o ecualización."
        )
        subtitulo.setObjectName("SubtituloApp")

        diseno.addWidget(titulo)
        diseno.addWidget(subtitulo)

        return encabezado

    def _conectar_senales(self) -> None:
        self.pagina_procesamiento.solicitud_procesar.connect(self.iniciar_procesamiento)
        self.pagina_resultados.solicitud_volver.connect(self.volver_a_procesamiento)

    def _establecer_estado_inicial(self) -> None:
        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_PROCESAMIENTO)
        self.barra_estado.showMessage("Listo. Configura la imagen y el procesamiento.")

    def iniciar_procesamiento(self, datos: dict) -> None:
        minimo = datos["minimo"]
        maximo = datos["maximo"]

        if minimo >= maximo:
            QMessageBox.warning(
                self,
                "Rango inválido",
                "La intensidad mínima debe ser menor que la intensidad máxima."
            )
            self.barra_estado.showMessage("No se pudo procesar: rango inválido.")
            return

        self.barra_estado.showMessage("Procesando imagen...")
        self.superposicion_carga.mostrar_superposicion("Procesando imagen...")

        QTimer.singleShot(1400, lambda: self.finalizar_procesamiento(datos))

    def finalizar_procesamiento(self, datos: dict) -> None:
        self.pagina_resultados.establecer_resultados(datos)

        self.superposicion_carga.ocultar_superposicion()
        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_RESULTADOS)

        self.barra_estado.showMessage("Procesamiento completado. Resultados generados.")

    def volver_a_procesamiento(self) -> None:
        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_PROCESAMIENTO)
        self.barra_estado.showMessage("Volviste al panel de procesamiento.")
