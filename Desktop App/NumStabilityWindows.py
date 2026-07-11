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
        elif type == 101: #Invalid stochastic matrix and probability vector (wrong shape)
            self.layout.addWidget(QLabel("Invalid dimensions. Must be n x (n + 1). Please try again."))
        elif type == 102: #Invalid stochastic matrix and probability vector (negative entries detected)
            self.layout.addWidget(QLabel("Stochastic matrix and probability vector must have non-negative entries. Please try again."))
        elif type == 103: #Invalid stochastic matrix and probability vector (zero column detected)
            self.layout.addWidget(QLabel("Stochastic matrix columns and probability vector must be non-zero. Please try again."))
        elif type == 104: #Stochastic matrix is bigger than 6x6 (practical limit for visualisation purposes)
            self.layout.addWidget(QLabel("Visu(AL)-1 currently allows at most 6 states. Please try again."))
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
            self.submit.clicked.connect(self.gaussianElimSend)
            npivot = QRadioButton("No Pivoting")
            npivot.setObjectName("0")
            npivot.clicked.connect(self.gaussianPivotToggle)
            ppivot = QRadioButton("Partial Pivoting")
            ppivot.setObjectName("1")
            ppivot.clicked.connect(self.gaussianPivotToggle)
            self.valuesLayout.addWidget(npivot)
            self.valuesLayout.addWidget(ppivot)
        elif self.val == 2:
            self.submit.clicked.connect(self.GSSend)
            cgs = QRadioButton("Classical Gram-Schmidt")
            cgs.setObjectName("0")
            cgs.clicked.connect(self.MGSToggle)
            mgs = QRadioButton("Modified Gram-Schmidt")
            mgs.setObjectName("1")
            mgs.clicked.connect(self.MGSToggle)
            normalise = QCheckBox("Normalise Vectors")
            normalise.clicked.connect(self.GSNorm)
            self.valuesLayout.addWidget(cgs)
            self.valuesLayout.addWidget(mgs)
            self.valuesLayout.addWidget(normalise)
    
    def gaussianPivotToggle(self):
        try:
            self.layout.removeWidget(self.submit)
        except:
            pass
        rb = self.sender()
        self.pivot = int(rb.objectName())
        if self.pivot:
            self.LUBox = QCheckBox("LU Factorisation")
            self.LUBox.clicked.connect(self.gaussianLUToggle)
            self.valuesLayout.addWidget(self.LUBox)
            pass
        else:
            try:
                self.valuesLayout.removeWidget(self.LUBox)
            except:
                pass
        self.enableLU = False
        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.gaussianElimSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)
    
    def gaussianLUToggle(self):
        cb = self.sender()
        self.enableLU = cb.isChecked()
    
    def gaussianElimSend(self):
        self.nums.emit([self.val, self.pivot, self.enableLU])
        self.close()
    
    def MGSToggle(self):
        try:
            self.layout.removeWidget(self.submit)
        except:
            pass
        rb = self.sender()
        self.modified = int(rb.objectName())
        self.normed = False
        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.GSSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)
    
    def GSNorm(self):
        cb = self.sender()
        self.normed = cb.isChecked()
    
    def GSSend(self):
        self.nums.emit([self.val, self.modified, self.normed])
        self.close()