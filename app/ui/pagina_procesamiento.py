from PySide6.QtCore import Signal

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox
# QFileDialog: ventana nativa del sistema operativo para "Seleccionar archivo"
# (la que se abre al hacer click en "Cargar imagen JPG")
# QMessageBox: ventanas emergentes simples para mostrar mensajes/errores al usuario

from app.ui.visor_imagen import VisorImagen
from app.ui.panel_control import PanelControl
from app.servicios.cargador_imagen import cargar_imagen_desde_ruta
# Conecta directamente con el servicio que validamos antes (extensión + escala de grises)


class PaginaProcesamiento(QWidget):
    # Esta es la pantalla principal donde el usuario sube la imagen y configura
    # todas las opciones (grid/completa, método, rango). Es el "ensamblador":
    # une VisorImagen (izquierda, donde se ve la imagen) con PanelControl
    # (derecha, donde están todos los controles)

    # Se declara una señal que lleva un diccionario como dato.
    solicitud_procesar = Signal(dict)
    # Esta señal se emite cuando ya se recolectaron TODOS los datos necesarios
    # para procesar (método, rango, datos del grid, imagen). Quien la escuche
    # (probablemente ventana_principal.py) recibirá ese diccionario completo
    # y ahí mismo llamará a procesador_histograma.py / selector_region.py

    def __init__(self) -> None:
        super().__init__()

        self.ruta_imagen_actual = None
        # Guarda la ruta del archivo (string) de la última imagen cargada con éxito

        self.imagen_cv_actual = None
        # Guarda la imagen ya cargada como array de NumPy (formato OpenCV),
        # lista para pasarse a los servicios de procesamiento

        self.visor_imagen = VisorImagen()
        self.panel_control = PanelControl()
        # Crea las dos piezas principales de esta pantalla

        self._construir_interfaz()
        self._conectar_senales()

    def _construir_interfaz(self) -> None:
        diseno = QHBoxLayout(self)
        # Layout horizontal: visor a la izquierda, panel de control a la derecha
        diseno.setContentsMargins(0, 0, 0, 0)
        diseno.setSpacing(14)

        diseno_izquierdo = QVBoxLayout()
        diseno_izquierdo.setSpacing(14)
        diseno_izquierdo.addWidget(self.visor_imagen)
        # Se envuelve el visor en un QVBoxLayout aunque solo tenga un elemento;
        # esto da flexibilidad para agregar más cosas debajo en el futuro sin
        # reestructurar todo el layout principal

        diseno.addLayout(diseno_izquierdo, stretch=4)
        diseno.addWidget(self.panel_control, stretch=1)
        # stretch=4 vs stretch=1: el visor de imagen ocupa proporcionalmente
        # 4 veces más espacio horizontal que el panel de control
        # (panel_control además ya tiene min/max width fijos de 340-400px)

    def _conectar_senales(self) -> None:
        # Aquí se "cablea" toda la comunicación entre PanelControl y VisorImagen,
        # que por sí solos no se conocen entre sí — esta página actúa de intermediaria

        self.panel_control.solicitud_procesar.connect(self._emitir_datos_procesamiento)
        # Cuando el usuario presiona "Procesar imagen" en el panel, se recolectan
        # los datos y se reemiten en un formato más completo (ver método abajo)

        self.panel_control.solicitud_cargar_imagen.connect(self.cargar_imagen)
        # Cuando se presiona "Cargar imagen JPG", se abre el diálogo de archivos

        self.panel_control.cambio_modo_grid.connect(self.visor_imagen.establecer_grid_habilitado)
        # Si el usuario cambia entre "usar grid" / "imagen completa" en el panel,
        # esto se refleja activando/desactivando el dibujo del grid en el visor

        self.panel_control.cambio_tamano_grid.connect(self.visor_imagen.establecer_tamano_grid)
        # Si cambia el tamaño del grid con el QSpinBox, se actualiza visualmente
        # el tamaño del cuadrito dibujado sobre la imagen

        self.visor_imagen.cambio_posicion_grid.connect(
            self.panel_control.actualizar_posicion_grid
        )
        # Y en sentido contrario: si el usuario ARRASTRA el grid sobre la imagen
        # (en visor_imagen.py), se actualiza el texto informativo "Grid: x=.., y=.."
        # en el panel de control

    def _emitir_datos_procesamiento(self) -> None:
        # Se ejecuta cuando el usuario hace click en "Procesar imagen"
        minimo, maximo = self.panel_control.obtener_rango_intensidad()
        # Recupera (s_min, s_max) elegidos en los QSpinBox del panel

        datos = {
            "metodo": self.panel_control.obtener_metodo_seleccionado(),
            # "Expansión de histograma" o "Ecualización de histograma"

            "modo_analisis": self.panel_control.obtener_modo_analisis(),
            # "Región seleccionada" o "Imagen completa" (texto informativo)

            "minimo": minimo,
            "maximo": maximo,

            "datos_grid": self.visor_imagen.obtener_datos_grid(),
            # El diccionario completo con x_visual, y_visual, tamano_real, activo,
            # y region_real — exactamente lo que necesita selector_region.py

            "ruta_imagen": self.ruta_imagen_actual,
            "imagen_cv": self.imagen_cv_actual,
            # La imagen ya cargada como array de NumPy, lista para procesar
        }

        self.solicitud_procesar.emit(datos)
        # Empaqueta TODO en un solo diccionario y lo envía hacia afuera.
        # Quien reciba esta señal (ventana_principal.py) tiene todo lo necesario
        # para llamar a seleccionar_region_de_procesamiento() y luego a procesar_imagen()

    def cargar_imagen(self) -> None:
        # Se ejecuta cuando el usuario hace click en "Cargar imagen JPG"
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",       # título de la ventana de diálogo
            "",                          # carpeta inicial (vacío = la última usada / default del SO)
            "Imágenes JPG (*.jpg *.jpeg)"  # filtro de archivos: solo muestra .jpg/.jpeg
        )
        # getOpenFileName devuelve una tupla (ruta_seleccionada, filtro_usado).
        # El "_" descarta el segundo valor porque no se necesita

        if not ruta_archivo:
            # Si el usuario cierra el diálogo sin elegir nada, ruta_archivo viene vacío
            return

        resultado = cargar_imagen_desde_ruta(ruta_archivo)
        # Llama al servicio que vimos antes: valida extensión + escala de grises real,
        # y devuelve el diccionario {"exito", "error", "imagen", "ruta"}

        if not resultado["exito"]:
            # Si la validación falló (formato incorrecto, no es escala de grises, etc.)
            QMessageBox.warning(
                self,
                "Imagen no válida",
                resultado["error"]
            )
            # Muestra un popup de advertencia con el mensaje de error específico
            # que generó cargador_imagen.py (ej: "La imagen no está en escala de grises")

            self.ruta_imagen_actual = None
            self.imagen_cv_actual = None
            self.panel_control.establecer_imagen_cargada(False)
            # Limpia el estado: sin imagen válida, el botón "Procesar" se deshabilita
            return

        # Si llegamos aquí, la imagen es válida
        self.ruta_imagen_actual = resultado["ruta"]
        self.imagen_cv_actual = resultado["imagen"]
        # Guarda tanto la ruta (para mostrarla visualmente con QPixmap)
        # como el array de NumPy ya normalizado a escala de grises (para procesar)

        self.visor_imagen.cargar_imagen(self.ruta_imagen_actual)
        # Le pasa la RUTA (no el array) al visor, porque LienzoImagen usa QPixmap(ruta)
        # para cargar y mostrar visualmente la imagen

        self.panel_control.establecer_imagen_cargada(True)
        # Habilita el botón "Procesar imagen" ahora que hay una imagen válida cargada