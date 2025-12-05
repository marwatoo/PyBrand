#!/usr/bin/python3

from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import sys
import io


def pil_to_qpixmap(pil_image):
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    qimage = QImage.fromData(buffer.getvalue(), "PNG")
    return QPixmap.fromImage(qimage)


class PreviewWindow(QWidget):
    def __init__(self, pil_image):
        super().__init__()
        self.setWindowTitle("Image Preview (50%)")

        # Convert PIL → QPixmap
        pixmap = pil_to_qpixmap(pil_image)

        # Scale to 50%
        scaled_pixmap = pixmap.scaled(
            pixmap.width() // 2,
            pixmap.height() // 2,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.label = QLabel()
        self.label.setPixmap(scaled_pixmap)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Resize window to the scaled image size
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())
