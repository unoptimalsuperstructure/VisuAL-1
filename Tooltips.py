import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QPixmap
from PathFinder import resource_path

class Tooltip(QWidget):
    def __init__(self, icon, message):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.resize(300, 100)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        layout = QHBoxLayout()
        img = QLabel()
        img.setPixmap(QPixmap(str(resource_path("static/" + icon + ".png"))).scaled(80, 80))
        layout.addWidget(img, 1)
        layout.addWidget(QLabel(message), 2)
        self.setLayout(layout)

class TooltipButton(QPushButton):
    def __init__(self, name, img, desc):
        super().__init__(name)
        self.tooltip = Tooltip(img, desc)