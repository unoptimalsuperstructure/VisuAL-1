from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from MatrixPrinter import toString, concat

def num(x):
    if x == "":
        return 0
    else:
        try:
            return float(x)
        except:
            return None
        
class ErrorWindow(QWidget):
    def __init__(self, type, window):
        super().__init__()
        self.setWindowTitle("Error")
        self.window = window
        self.layout = QVBoxLayout()
        if type == 0:
            self.layout.addWidget(QLabel("Please select an object."))
        elif type == 1:
            self.layout.addWidget(QLabel("At least one of your entries is invalid. Please try again."))
        elif type == 2:
            self.layout.addWidget(QLabel("Matrix has inconsistent dimensions. Please try again."))
        elif type == 99: #Invalid convolution matrix (even dimensions)
            self.layout.addWidget(QLabel("Convolution kernel must have odd dimensions. Please try again."))
        else:
            self.layout.addWidget(QLabel("Unknown error occurred."))
        self.submit = QPushButton("OK")
        self.submit.clicked.connect(self.close)
        self.layout.addWidget(self.submit)
        self.setLayout(self.layout)
    
    def closeEvent(self, event):
        if self.window:
            self.window.show()
        event.accept()

class ActionWindow(QWidget):
    num = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.val = 0
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Please select an action."))
        GaussianElim = QRadioButton("Gaussian Elimination")
        GaussianElim.setObjectName("1")
        GaussianElim.toggled.connect(self.onToggle)
        self.layout.addWidget(GaussianElim)
        GramSchmidt = QRadioButton("Gram-Schmidt Process")
        GramSchmidt.setObjectName("2")
        GramSchmidt.toggled.connect(self.onToggle)
        self.layout.addWidget(GramSchmidt)

        submit = QPushButton("Submit")
        submit.clicked.connect(self.send)
        self.layout.addWidget(submit)
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        self.val = int(rb.objectName())
    
    def send(self):
        self.num.emit(self.val)
        self.close()