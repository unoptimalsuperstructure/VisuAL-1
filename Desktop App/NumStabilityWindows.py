from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

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
        if type == 1:
            self.layout.addWidget(QLabel("At least one of your entries is invalid. Please try again."))
        elif type == 2:
            self.layout.addWidget(QLabel("Matrix has inconsistent dimensions. Please try again."))
        elif type == 3:
            self.layout.addWidget(QLabel("This operation only applies to square matrices. Please try again."))
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

        MatrixInv = QRadioButton("Matrix Inversion")
        MatrixInv.setObjectName("2")
        MatrixInv.toggled.connect(self.onToggle)
        self.optionLayout.addWidget(MatrixInv)

        GramSchmidt = QRadioButton("Gram-Schmidt Process")
        GramSchmidt.setObjectName("3")
        GramSchmidt.toggled.connect(self.onToggle)
        self.optionLayout.addWidget(GramSchmidt)

        Diagonalise = QRadioButton("Diagonalisation")
        Diagonalise.setObjectName("4")
        Diagonalise.toggled.connect(self.onToggle)
        self.optionLayout.addWidget(Diagonalise)

        self.layout.addWidget(self.optionPanel, 1, 0)
        self.layout.addWidget(self.valuesPanel, 1, 1)
        self.submit = QPushButton("Submit")
        self.submit.setEnabled(False)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)
        self.setLayout(self.layout)
    
    def onToggle(self):
        self.submit.setEnabled(False)
        try:
            self.submit.clicked.disconnect()
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
            self.submit.clicked.connect(self.matrixInvSend)
            npivot = QRadioButton("Gauss-Jordan")
            npivot.setObjectName("1")
            npivot.clicked.connect(self.matrixInvMode)
            ppivot = QRadioButton("GJ with Pivoting")
            ppivot.setObjectName("2")
            ppivot.clicked.connect(self.matrixInvMode)
            lup = QRadioButton("LUP Factorisation")
            lup.setObjectName("3")
            lup.clicked.connect(self.matrixInvMode)
            self.valuesLayout.addWidget(npivot)
            self.valuesLayout.addWidget(ppivot)
            #self.valuesLayout.addWidget(lup)
        elif self.val == 3:
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
        elif self.val == 4:
            self.submit.clicked.connect(self.diagonalise)
            self.submit.setEnabled(True)
    
    def gaussianPivotToggle(self):
        self.submit.setEnabled(True)
        rb = self.sender()
        self.pivot = int(rb.objectName())
        try:
            self.valuesLayout.removeWidget(self.LUBox)
        except:
            pass
        if self.pivot:
            self.LUBox = QCheckBox("LU Factorisation")
            self.LUBox.clicked.connect(self.gaussianLUToggle)
            self.valuesLayout.addWidget(self.LUBox)
            pass
            
        self.enableLU = False
    
    def gaussianLUToggle(self):
        cb = self.sender()
        self.enableLU = cb.isChecked()
    
    def gaussianElimSend(self):
        self.nums.emit([self.val, self.pivot, self.enableLU])
        self.close()
    
    def matrixInvMode(self):
        self.submit.setEnabled(True)
        rb = self.sender()
        self.invMode = int(rb.objectName())
    
    def matrixInvSend(self):
        self.nums.emit([self.val, self.invMode])
        self.close()
    
    def MGSToggle(self):
        self.submit.setEnabled(True)
        rb = self.sender()
        self.modified = int(rb.objectName())
        self.normed = False
    
    def GSNorm(self):
        cb = self.sender()
        self.normed = cb.isChecked()
    
    def GSSend(self):
        self.nums.emit([self.val, self.modified, self.normed])
        self.close()
    
    def diagonalise(self):
        self.nums.emit([self.val])
        self.close()