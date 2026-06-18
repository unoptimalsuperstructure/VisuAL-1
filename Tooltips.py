import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QPixmap

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
        img.setPixmap(QPixmap("static/" + icon + ".png").scaled(80, 80))
        layout.addWidget(img, 1)
        layout.addWidget(QLabel(message), 2)
        self.setLayout(layout)

class TooltipButton(QPushButton):
    def __init__(self, name, img, desc):
        super().__init__(name)
        self.tooltip = Tooltip(img, desc)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Hover Bubble Demo')
        self.resize(300, 200)
        
        layout = QHBoxLayout()
        self.button = TooltipButton('Hover Me!', Tooltip("ReflectPlane",
                                    "Reflect the current object\n" \
                                    "about a specified plane"))
        layout.addWidget(self.button)
        self.setLayout(layout)
        
        # Instantiate the bubble (keep it hidden initially)
        """self.bubble = Tooltip("Translate",
                              "Translate the current object\n" \
                              "along the x, y and z-axes")"""
        self.reflectLine = Tooltip("ReflectLine",
                                   "Reflect the current object\n" \
                                   "about a specified line")
        self.reflectPlane = Tooltip("ReflectPlane",
                                    "Reflect the current object\n" \
                                    "about a specified plane")
        self.rotateLine = Tooltip("RotateLine",
                                  "Rotate the current object\n" \
                                  "about a specified line\n" \
                                  "through a specified angle")
        self.projectPlane = Tooltip("ProjectPlane",
                                    "Project the current object\n" \
                                    "onto a specified plane")
        self.scale = Tooltip("Scale",
                             "Scale the current object by\n" \
                             "a specified scale factor")
        self.shear = Tooltip("Shear",
                             "Shear the current object by\n" \
                             "a specified invariant line,\n" \
                             "a specified shear direction\n" \
                             "and a specified shear factor")
        self.bubble = Tooltip("Repeat",
                              "Repeat a specified number\n" \
                              "of previous transformations")
        self.undo = Tooltip("Undo",
                             "Undo the most recent\n" \
                             "transformation, or delete the\n" \
                             "object if there is none")
        self.bubble = Tooltip("Reset",
                             "Reset the current object to its\n" \
                             "default position. IRREVERSIBLE!")
        self.delete = Tooltip("Delete",
                              "Delete the current object\n" \
                              "permanently. IRREVERSIBLE!")
        
        self.button.installEventFilter(self)

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Type.Enter:
                self.show_bubble_above_button(obj.tooltip)
                return True
            elif event.type() == QEvent.Type.Leave:
                obj.tooltip.hide()
                return True
        return super().eventFilter(obj, event)

    def show_bubble_above_button(self, bub):
        button_global_pos = self.button.mapToGlobal(QPoint(0, 0))
        
        x = button_global_pos.x() - bub.width() - 15
        y = button_global_pos.y() + (self.button.height() // 2) - (bub.height() // 2)
        
        bub.move(x, y)
        bub.show()