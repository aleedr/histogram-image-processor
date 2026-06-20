from PySide6.QtCore import QTimer
# QTimer: permite ejecutar código después de un tiempo determinado, o de forma
# repetitiva. Aquí se usa en modo "singleShot" (una sola ejecución retrasada)

from PySide6.QtWidgets import (
    QMainWindow,      # Ventana principal "completa" de una app de escritorio
                        # (a diferencia de QWidget, ya incluye soporte para
                        # barra de menú, barra de estado, toolbar, etc.)
    QWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,        # La barra inferior donde se muestran mensajes de estado
    QStackedWidget,    # Contenedor que muestra UNA sola "página" a la vez de
                        # varias que tiene apiladas — como un mazo de cartas donde
                        # solo ves la de encima. Perfecto para cambiar entre
                        # "pantalla de procesamiento" y "pantalla de resultados"
    QMessageBox,
)

from app.ui.pagina_procesamiento import PaginaProcesamiento
from app.ui.pagina_resultados import PaginaResultados
from app.ui.widgets.superposicion_carga import SuperposicionCarga
from app.utilidades.constantes import TITULO_APP


class VentanaPrincipal(QMainWindow):
    # Esta es la ventana RAÍZ de toda la aplicación — el "main.py" de la UI.
    # Aquí se conectan finalmente PaginaProcesamiento y PaginaResultados,
    # y se orquesta el llamado real a los servicios matemáticos

    INDICE_PAGINA_PROCESAMIENTO = 0
    INDICE_PAGINA_RESULTADOS = 1
    # Constantes para identificar qué página mostrar en el QStackedWidget,
    # en vez de usar números "mágicos" (0, 1) sueltos en el código — más legible

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(TITULO_APP)
        # Usa la constante "Gray Histogram Processor" que vimos al principio

        self.setMinimumSize(1280, 760)

        self.pagina_procesamiento = PaginaProcesamiento()
        self.pagina_resultados = PaginaResultados()
        # Crea ambas "pantallas" completas de la app

        self.pila_paginas = QStackedWidget()
        # El contenedor que va a alternar entre ambas pantallas

        self.superposicion_carga = None
        # Se inicializa como None aquí y se crea de verdad más abajo en
        # _construir_interfaz, porque necesita el widget_central ya creado
        # como su "parent" (para poder cubrirlo completamente)

        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)
        # setStatusBar es un método propio de QMainWindow (no existe en QWidget)
        # que coloca la barra fija en la parte inferior de la ventana

        self._construir_interfaz()
        self._conectar_senales()
        self._establecer_estado_inicial()

    def _construir_interfaz(self) -> None:
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        # QMainWindow requiere un "widget central" — el área principal de
        # contenido, distinta de la barra de menú, toolbar, statusbar, etc.

        diseno_raiz = QVBoxLayout(widget_central)
        diseno_raiz.setContentsMargins(18, 18, 18, 12)
        diseno_raiz.setSpacing(14)

        encabezado = self._crear_encabezado()

        self.pila_paginas.addWidget(self.pagina_procesamiento)
        self.pila_paginas.addWidget(self.pagina_resultados)
        # El orden de adición determina el índice: procesamiento=0, resultados=1
        # (coincide con las constantes INDICE_PAGINA_* definidas arriba)

        diseno_raiz.addWidget(encabezado)
        diseno_raiz.addWidget(self.pila_paginas, stretch=1)
        # stretch=1: la pila de páginas ocupa todo el espacio vertical restante
        # (el encabezado solo ocupa su tamaño natural)

        self.superposicion_carga = SuperposicionCarga(widget_central)
        # AHORA sí se crea, pasando widget_central como parent — esto es
        # justo lo que permite que el overlay cubra TODA el área de contenido
        # (incluyendo encabezado y ambas páginas), como vimos en su archivo

    def _crear_encabezado(self) -> QWidget:
        # Construye el título superior de toda la app (distinto de los títulos
        # internos de cada página)
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
        # Cuando PaginaProcesamiento termina de recolectar todos los datos
        # (método, rango, grid, imagen) y emite su señal, arranca aquí
        # el flujo real de procesamiento

        self.pagina_resultados.solicitud_volver.connect(self.volver_a_procesamiento)
        # Cuando el usuario presiona "Volver al procesamiento" en resultados

    def _establecer_estado_inicial(self) -> None:
        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_PROCESAMIENTO)
        # Al abrir la app, siempre se empieza en la pantalla de procesamiento

        self.barra_estado.showMessage("Listo. Configura la imagen y el procesamiento.")
        # Mensaje inicial en la barra de estado inferior

    def iniciar_procesamiento(self, datos: dict) -> None:
        # Recibe el diccionario completo que armó PaginaProcesamiento
        # (metodo, modo_analisis, minimo, maximo, datos_grid, ruta_imagen, imagen_cv)

        minimo = datos["minimo"]
        maximo = datos["maximo"]

        if minimo >= maximo:
            # VALIDACIÓN A NIVEL UI: aunque ya existía una validación similar
            # dentro de procesador_histograma.py (que lanza ValueError), aquí
            # se valida ANTES para mostrar un mensaje amigable al usuario
            # en vez de que el error explote más adentro del flujo
            QMessageBox.warning(
                self,
                "Rango inválido",
                "La intensidad mínima debe ser menor que la intensidad máxima."
            )
            self.barra_estado.showMessage("No se pudo procesar: rango inválido.")
            return

        self.barra_estado.showMessage("Procesando imagen...")
        self.superposicion_carga.mostrar_superposicion("Procesando imagen...")
        # Muestra el overlay de "cargando" ANTES de empezar el trabajo pesado

        QTimer.singleShot(1400, lambda: self.finalizar_procesamiento(datos))
        # CLAVE: en vez de llamar a finalizar_procesamiento() inmediatamente,
        # se espera 1400 milisegundos (1.4 segundos) antes de ejecutarlo.
        # ¿Por qué? Esto da tiempo a que la UI se actualice y MUESTRE el overlay
        # de carga primero. Si se llamara directo, Qt podría "congelar" la
        # interfaz mientras procesa y el usuario nunca vería la animación de
        # carga (porque el procesamiento real es muy rápido y bloquea el hilo
        # principal). Es un truco para mejorar la UX, simulando que el proceso
        # toma un tiempo "visible", aunque matemáticamente sea instantáneo.
        # singleShot = se ejecuta UNA SOLA VEZ después del delay (no se repite)

    def finalizar_procesamiento(self, datos: dict) -> None:
        # Import dentro de la función (no al principio del archivo): esto es
        # un patrón usado a veces para evitar imports circulares, o simplemente
        # para retrasar la carga de estos módulos hasta que realmente se necesiten
        from app.servicios.procesador_histograma import procesar_imagen
        from app.servicios.selector_region import seleccionar_region_de_procesamiento

        try:
            # PASO 1: decidir qué porción de la imagen procesar (completa o grid)
            imagen_a_procesar = seleccionar_region_de_procesamiento(
                imagen=datos["imagen_cv"],
                datos_grid=datos["datos_grid"],
            )

            # PASO 2: aplicar la matemática (expansión o ecualización) sobre
            # esa porción de imagen
            resultado = procesar_imagen(
                imagen=imagen_a_procesar,
                metodo=datos["metodo"],
                s_min=datos["minimo"],
                s_max=datos["maximo"],
            )

            datos["resultado_procesamiento"] = resultado
            # Agrega el resultado completo al mismo diccionario "datos" que
            # ya traía toda la info original — así pagina_resultados.py
            # recibe TODO junto (metodo, minimo, maximo, Y el resultado)

        except Exception as error:
            # Si algo falla en cualquiera de los dos pasos anteriores
            # (ej: una excepción no prevista en los servicios), se construye
            # un resultado "vacío" con el mensaje de error, para que
            # pagina_resultados.py pueda mostrarlo sin romper la app
            datos["resultado_procesamiento"] = {
                "imagen_original": None,
                "imagen_procesada": None,
                "hist_niveles_orig": None,
                "hist_conteos_orig": None,
                "hist_niveles_proc": None,
                "hist_conteos_proc": None,
                "metodo": datos.get("metodo"),
                "error": str(error),
            }

        self.pagina_resultados.establecer_resultados(datos)
        # Le pasa TODO el diccionario a la página de resultados para que
        # actualice los 4 paneles (imágenes + histogramas) y habilite el
        # botón de tabla de transformación

        self.superposicion_carga.ocultar_superposicion()
        # Oculta el overlay de "cargando" ya que el proceso terminó

        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_RESULTADOS)
        # Cambia visualmente de pantalla: de "procesamiento" a "resultados"

        self.barra_estado.showMessage("Procesamiento completado. Resultados generados.")

    def volver_a_procesamiento(self) -> None:
        # Se ejecuta cuando el usuario presiona "← Volver al procesamiento"
        self.pila_paginas.setCurrentIndex(self.INDICE_PAGINA_PROCESAMIENTO)
        self.barra_estado.showMessage("Volviste al panel de procesamiento.")