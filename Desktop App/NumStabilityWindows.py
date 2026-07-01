from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from MatrixPrinter import toString, concat

def num(x):
    if x == "":
        return 0
    else:
        try:
            return eval(x)
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
    nums = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.val = 0
        self.stability = 0
        self.layout = QGridLayout()
        self.optionPanel = QWidget()
        self.optionLayout = QVBoxLayout()
        self.valuesPanel = QWidget()
        self.valuesLayout = QVBoxLayout()
        self.optionPanel.setLayout(self.optionLayout)
        self.valuesPanel.setLayout(self.valuesLayout)
        self.layout.addWidget(QLabel("Please select an action."), 0, 0, 1, 2)

        GaussianElim = QRadioButton("Gaussian Elimination")
        GaussianElim.setObjectName("1")
        GaussianElim.toggled.connect(self.onToggle)
        self.optionLayout.addWidget(GaussianElim)

        GramSchmidt = QRadioButton("Gram-Schmidt Process")
        GramSchmidt.setObjectName("2")
        GramSchmidt.toggled.connect(self.onToggle)
        self.optionLayout.addWidget(GramSchmidt)

        self.layout.addWidget(self.optionPanel, 1, 0)
        self.layout.addWidget(self.valuesPanel, 1, 1)
        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.send)
        self.setLayout(self.layout)
    
    def onToggle(self):
        try:
            self.layout.removeWidget(self.submit)
        except:
            pass
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()
        rb = self.sender()
        self.val = int(rb.objectName())
        if self.val == 1:
            npivot = QRadioButton("No Pivoting")
            npivot.setObjectName("0")
            npivot.clicked.connect(self.onToggle2)
            ppivot = QRadioButton("Partial Pivoting")
            ppivot.setObjectName("1")
            ppivot.clicked.connect(self.onToggle2)
            self.valuesLayout.addWidget(npivot)
            self.valuesLayout.addWidget(ppivot)
        elif self.val == 2:
            cgs = QRadioButton("Classical Gram-Schmidt")
            cgs.setObjectName("0")
            cgs.clicked.connect(self.onToggle2)
            mgs = QRadioButton("Modified Gram-Schmidt")
            mgs.setObjectName("1")
            mgs.clicked.connect(self.onToggle2)
            self.valuesLayout.addWidget(cgs)
            self.valuesLayout.addWidget(mgs)
    
    def onToggle2(self):
        try:
            self.layout.removeWidget(self.submit)
        except:
            pass
        rb = self.sender()
        self.stability = int(rb.objectName())
        self.layout.addWidget(self.submit, 2, 0, 1, 2)
    
    def send(self):
        self.nums.emit([self.val, self.stability])
        self.close()