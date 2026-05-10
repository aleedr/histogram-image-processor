import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from app.ui.ventana_principal import VentanaPrincipal


def cargar_hoja_estilos(app: QApplication) -> None:
    ruta_qss = Path("assets/estilos/main.qss")

    if ruta_qss.exists():
        with open(ruta_qss, "r", encoding="utf-8") as archivo:
            app.setStyleSheet(archivo.read())


def ejecutar_aplicacion() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Gray Histogram Processor")

    cargar_hoja_estilos(app)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    ejecutar_aplicacion()
