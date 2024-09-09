import io
import sys

from PIL.Image import Image
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QScrollArea
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QMimeData
import os

from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QImage, QPixmap

from BinaryReader import BinaryReader as Reader
import Decode8BPTPattern


def image_conv2(im):
    im = im.convert("RGB")
    data = im.tobytes("raw", "RGB")
    qi = QImage(data, im.size[0], im.size[1], im.size[0] * 3, QImage.Format.Format_RGB888)
    pix = QPixmap.fromImage(qi)
    return pix


def image_conf(image):
    im2 = image.convert("RGBA")
    data = im2.tobytes("raw", "BGRA")
    qim = QImage(data, image.width, image.height, QImage.Format_ARGB32)
    return QPixmap.fromImage(qim)


def extract_images_from_pat(image_data_bytes):
    # Example mockup of extracted binary image data (replace with real image data)
    images = []
    for image_data in image_data_bytes:
        pixmap = image_conv2(image_data)
        if pixmap:
            images.append(pixmap)
    return images


class PATFileDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("PAT File Gallery")
        self.setGeometry(200, 200, 800, 600)

        # Create a central widget and set layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create a scroll area for the image gallery
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Create a container widget for images and set a grid layout
        self.image_container = QWidget()
        self.image_layout = QGridLayout(self.image_container)
        self.scroll_area.setWidget(self.image_container)

        # Set the layout of the central widget
        layout = QGridLayout(self.central_widget)
        layout.addWidget(self.scroll_area)

        # Enable drag and drop
        self.setAcceptDrops(True)

    # Handle drag and drop events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if all(url.toLocalFile().lower().endswith(".pat") for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.endswith(".pat"):
                self.load_pat_file(file_path)

    def load_pat_file(self, pat_filepath):
        with open(pat_filepath, "rb") as f:
            data = f.read()

        reader = Reader(data)
        images = Decode8BPTPattern.readFile(reader)
        print(images)
        images_binary = list()
        for i in images:
            images_binary.append(image_conf(i))
        images = images_binary
        # extract_images_from_pat(images_binary)

        # Clear the existing layout
        for i in reversed(range(self.image_layout.count())):
            widget = self.image_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Display the extracted images
        for i, pixmap in enumerate(images):
            label = QLabel(self)
            label.setPixmap(pixmap)
            self.image_layout.addWidget(label, i // 3, i % 3)  # Arrange in a 3-column grid


# Main application execution
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the main window
    window = PATFileDropWindow()
    window.show()

    sys.exit(app.exec_())
