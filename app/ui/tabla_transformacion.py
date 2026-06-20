import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
)


class VentanaTablaTransformacion(QDialog):
    def __init__(
        self,
        tabla_transformacion: np.ndarray,
        conteos_originales: np.ndarray,
        metodo: str,
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
        subtitulo.setObjectName("SubtituloResultados")
        subtitulo.setWordWrap(True)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels([
            "Valor original",
            "Cantidad de píxeles",
            "Valor transformado",
        ])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)

        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.setObjectName("BotonSecundario")
        self.boton_cerrar.clicked.connect(self.close)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(self.boton_cerrar)

        diseno.addWidget(titulo)
        diseno.addWidget(subtitulo)
        diseno.addWidget(self.tabla, stretch=1)
        diseno.addLayout(fila_botones)

    def _llenar_tabla(self) -> None:
        valores_presentes = np.where(self.conteos_originales > 0)[0]

        self.tabla.setRowCount(len(valores_presentes))

        for fila, valor_original in enumerate(valores_presentes):
            cantidad_pixeles = int(self.conteos_originales[valor_original])
            valor_transformado = int(self.tabla_transformacion[valor_original])

            item_original = QTableWidgetItem(str(valor_original))
            item_cantidad = QTableWidgetItem(str(cantidad_pixeles))
            item_transformado = QTableWidgetItem(str(valor_transformado))

            item_original.setTextAlignment(Qt.AlignCenter)
            item_cantidad.setTextAlignment(Qt.AlignCenter)
            item_transformado.setTextAlignment(Qt.AlignCenter)

            self.tabla.setItem(fila, 0, item_original)
            self.tabla.setItem(fila, 1, item_cantidad)
            self.tabla.setItem(fila, 2, item_transformado)

        self.tabla.resizeColumnsToContents()