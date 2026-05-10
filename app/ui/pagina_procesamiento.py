from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox

from app.ui.visor_imagen import VisorImagen
from app.ui.panel_control import PanelControl
from app.servicios.cargador_imagen import cargar_imagen_desde_ruta


class PaginaProcesamiento(QWidget):
    # Se declara una señal que lleva un diccionario como dato.
    solicitud_procesar = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self.ruta_imagen_actual = None
        self.imagen_cv_actual = None

        self.visor_imagen = VisorImagen()
        self.panel_control = PanelControl()

        self._construir_interfaz()
        self._conectar_senales()

    def _construir_interfaz(self) -> None:
        diseno = QHBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(14)

        diseno_izquierdo = QVBoxLayout()
        diseno_izquierdo.setSpacing(14)
        diseno_izquierdo.addWidget(self.visor_imagen)

        diseno.addLayout(diseno_izquierdo, stretch=4)
        diseno.addWidget(self.panel_control, stretch=1)

    def _conectar_senales(self) -> None:
        self.panel_control.solicitud_procesar.connect(self._emitir_datos_procesamiento)
        self.panel_control.solicitud_cargar_imagen.connect(self.cargar_imagen)

        self.panel_control.cambio_modo_grid.connect(self.visor_imagen.establecer_grid_habilitado)
        self.panel_control.cambio_tamano_grid.connect(self.visor_imagen.establecer_tamano_grid)

        self.visor_imagen.cambio_posicion_grid.connect(
            self.panel_control.actualizar_posicion_grid
        )

    def _emitir_datos_procesamiento(self) -> None:
        minimo, maximo = self.panel_control.obtener_rango_intensidad()

        datos = {
            "metodo": self.panel_control.obtener_metodo_seleccionado(),
            "modo_analisis": self.panel_control.obtener_modo_analisis(),
            "minimo": minimo,
            "maximo": maximo,
            "datos_grid": self.visor_imagen.obtener_datos_grid(),
            "ruta_imagen": self.ruta_imagen_actual,
            "imagen_cv": self.imagen_cv_actual,
        }

        self.solicitud_procesar.emit(datos)

    def cargar_imagen(self) -> None:
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes JPG (*.jpg *.jpeg)"
        )

        if not ruta_archivo:
            return

        resultado = cargar_imagen_desde_ruta(ruta_archivo)

        if not resultado["exito"]:
            QMessageBox.warning(
                self,
                "Imagen no válida",
                resultado["error"]
            )
            self.ruta_imagen_actual = None
            self.imagen_cv_actual = None
            self.panel_control.establecer_imagen_cargada(False)
            return

        self.ruta_imagen_actual = resultado["ruta"]
        self.imagen_cv_actual = resultado["imagen"]

        self.visor_imagen.cargar_imagen(self.ruta_imagen_actual)
        self.panel_control.establecer_imagen_cargada(True)
