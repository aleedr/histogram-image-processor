import numpy as np
# Para manejar la tabla de transformación y los conteos como arrays

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QDialog,            # Ventana emergente independiente (modal o no), distinta de QWidget normal
    QVBoxLayout,
    QLabel,
    QTableWidget,        # Widget de tabla con filas/columnas tipo hoja de cálculo
    QTableWidgetItem,    # Representa una celda individual dentro de QTableWidget
    QPushButton,
    QHBoxLayout,
)


class VentanaTablaTransformacion(QDialog):
    # Esta es justo la "función recién agregada" que mencionaste: una ventana
    # aparte que muestra la tabla con los valores originales y sus transformados

    def __init__(
        self,
        tabla_transformacion: np.ndarray,
        # La LUT (lookup table) de 256 valores que retornan expandir_histograma()
        # o ecualizar_histograma() — el mapeo de cada nivel de gris original a su nuevo valor

        conteos_originales: np.ndarray,
        # El histograma original (cuántos píxeles hay de cada nivel de gris 0-255)

        metodo: str,
        # Texto del método aplicado, para mostrarlo informativamente

        parent=None,
    ) -> None:
        super().__init__(parent)

        self.tabla_transformacion = tabla_transformacion
        self.conteos_originales = conteos_originales
        self.metodo = metodo

        self.setWindowTitle("Tabla de transformación")
        self.setMinimumSize(520, 560)

        self.setObjectName("VentanaTablaTransformacion")

        self.setStyleSheet("""
            QDialog#VentanaTablaTransformacion {
            background-color: #F8FAFC;
            color: #0F172A;
            }

            QLabel {
                color: #0F172A;
                background-color: transparent;
            }

            QTableWidget {
                background-color: #FFFFFF;
                color: #0F172A;
                gridline-color: #CBD5E1;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
            }

            QHeaderView::section {
                background-color: #E2E8F0;
                color: #0F172A;
                padding: 6px;
                border: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 1px solid #CBD5E1;
                font-weight: bold;
            }

            QPushButton {
                background-color: #475569;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #334155;
            }
        """)
        # setStyleSheet con QSS (el "CSS" de Qt). A diferencia de los otros archivos
        # que usan setObjectName y dependen de un archivo de estilos global
        # (en assets/estilos), esta ventana define su propio estilo EN LÍNEA,
        # probablemente porque es una ventana independiente (QDialog) que no
        # siempre hereda el estilo de la ventana principal automáticamente

        self._construir_interfaz()
        self._llenar_tabla()

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(18, 18, 18, 18)
        diseno.setSpacing(12)

        titulo = QLabel("Tabla de valores originales y transformados")
        titulo.setObjectName("TituloResultados")

        subtitulo = QLabel(
            f"Método aplicado: {self.metodo}\n"
            "Solo se muestran los niveles de gris que sí existen en la imagen original."
        )
        # Aclara al usuario que la tabla NO muestra los 256 niveles posibles,
        # solo los que realmente aparecen en la imagen (evita una tabla gigante
        # llena de filas con "0 píxeles" que no aportan información)
        subtitulo.setObjectName("SubtituloResultados")
        subtitulo.setWordWrap(True)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels([
            "Valor original",
            "Cantidad de píxeles",
            "Valor transformado",
        ])
        # Define las 3 columnas: el nivel de gris ANTES, cuántos píxeles tenían
        # ese nivel, y a qué nivel se transformó DESPUÉS

        self.tabla.verticalHeader().setVisible(False)
        # Oculta los números de fila automáticos (0,1,2,3...) del lado izquierdo,
        # ya que no aportan información útil aquí

        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        # Hace la tabla de SOLO LECTURA: el usuario no puede hacer doble-click
        # y editar los valores (tendría sentido editar datos que son resultado
        # de un cálculo, no datos de entrada)

        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        # Al hacer click en una celda, selecciona toda la FILA (no solo la celda)

        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.setObjectName("BotonSecundario")
        self.boton_cerrar.clicked.connect(self.close)
        # .close() es un método heredado de QDialog que cierra la ventana

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        # addStretch() antes del botón empuja el botón hacia la derecha
        # (efecto: botón "Cerrar" alineado a la derecha de la ventana)
        fila_botones.addWidget(self.boton_cerrar)

        diseno.addWidget(titulo)
        diseno.addWidget(subtitulo)
        diseno.addWidget(self.tabla, stretch=1)
        # stretch=1: la tabla ocupa todo el espacio vertical disponible
        diseno.addLayout(fila_botones)

    def _llenar_tabla(self) -> None:
        # Aquí se traduce la matemática (arrays de NumPy) a filas visibles de la tabla

        valores_presentes = np.where(self.conteos_originales > 0)[0]
        # np.where devuelve los ÍNDICES donde la condición es verdadera.
        # Aquí, los índices son justamente los niveles de gris (0-255), y la
        # condición filtra solo los niveles que SÍ tienen al menos 1 píxel
        # en la imagen original. El [0] extrae el array de índices del resultado
        # (np.where devuelve una tupla, incluso cuando es una sola dimensión)

        self.tabla.setRowCount(len(valores_presentes))
        # Crea tantas filas en la tabla como niveles de gris distintos existan

        for fila, valor_original in enumerate(valores_presentes):
            # enumerate da el número de fila (0,1,2...) y el valor real del nivel de gris

            cantidad_pixeles = int(self.conteos_originales[valor_original])
            # Cuántos píxeles tenían ese nivel de gris en la imagen original

            valor_transformado = int(self.tabla_transformacion[valor_original])
            # A qué nuevo valor se transformó ese nivel, usando la LUT calculada
            # antes en expandir_histograma() o ecualizar_histograma()

            item_original = QTableWidgetItem(str(valor_original))
            item_cantidad = QTableWidgetItem(str(cantidad_pixeles))
            item_transformado = QTableWidgetItem(str(valor_transformado))
            # QTableWidgetItem necesita strings, por eso se convierten los números

            item_original.setTextAlignment(Qt.AlignCenter)
            item_cantidad.setTextAlignment(Qt.AlignCenter)
            item_transformado.setTextAlignment(Qt.AlignCenter)
            # Centra el texto dentro de cada celda (estético)

            self.tabla.setItem(fila, 0, item_original)
            self.tabla.setItem(fila, 1, item_cantidad)
            self.tabla.setItem(fila, 2, item_transformado)
            # Coloca cada celda en su posición (fila, columna) dentro de la tabla

        self.tabla.resizeColumnsToContents()
        # Ajusta automáticamente el ancho de cada columna según el contenido
        # más largo que tenga (evita columnas demasiado anchas o que cortan el texto)