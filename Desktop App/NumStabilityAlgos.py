import NumStabilityWindows, gc
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
import csv
import numpy as np, sympy as sp
from MatrixPrinter import *
from LinearAlgebraAlgos import *

class NumStabilityViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.pressed_keys = set()

        self.lastOpStack = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

class NumStabilitySidePanel(QGridLayout):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer

        self.matrix = None
        self.augcol = 0
        self.basis = None

        self.displayAcc = 6
        self.calculationAcc = 16

        self.addWidget(QLabel("DP for display matrix:"), 0, 0)
        self.displayAccWheel = QSpinBox()
        self.displayAccWheel.setValue(6)
        self.displayAccWheel.setRange(2, 12)
        self.displayAccWheel.valueChanged.connect(self.setDisplayAcc)
        self.addWidget(self.displayAccWheel, 0, 1)
        self.addWidget(QLabel("DP for calculations:"), 1, 0)
        self.calculationAccWheel = QSpinBox()
        self.calculationAccWheel.setValue(16)
        self.calculationAccWheel.setRange(6, 16)
        self.calculationAccWheel.valueChanged.connect(self.setCalculationAcc)
        self.addWidget(self.calculationAccWheel, 1, 1)

        addDataButton = QPushButton("Import CSV...")
        addDataButton.clicked.connect(self.loadCSV)
        randomDataButton = QPushButton("Generate random data...")
        actionButton = QPushButton("Action...")
        actionButton.clicked.connect(self.actionWindow)

        self.addWidget(addDataButton)
        self.addWidget(randomDataButton)
        self.addWidget(actionButton)
    
    def setDisplayAcc(self, x):
        self.displayAcc = int(x)
    
    def setCalculationAcc(self, x):
        self.calculationAcc = int(x)

    def loadCSV(self):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )[0]

        if not file_path:
            return
        
        mat = []
        valid = True

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                try:
                    mat.append(list(map(lambda x: eval(x), row)))
                except:
                    valid = False
                    self.error = NumStabilityWindows.ErrorWindow(1, None)
                    self.error.show()
                    break
        
        try:
            self.matrix = np.array(mat)
            self.asMatrix = True
        except:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(2, None)
            self.error.show()
        
        if valid:
            try:
                self.viewer.layout.removeWidget(self.displayMatrix)
            except:
                pass
            self.calculationAccWheel.setEnabled(True)
            self.augcol = 0
            disp = displayAsMatrix(toString(self.matrix, self.displayAcc), 0)
            self.displayMatrix = QLabel(disp)
            self.displayMatrix.setStyleSheet("font-family: Cascadia Mono")

            self.page = 0
            self.last = 0

            self.viewer.layout.addWidget(self.displayMatrix)
            try:
                self.viewer.layout.removeWidget(self.op)
                self.viewer.layout.removeWidget(self.pageView)
                self.viewer.layout.removeWidget(self.soln)
            except:
                pass
            
            self.op = QLabel()
            self.viewer.layout.addWidget(self.op)
            self.pageView = self.pageLoader()
            self.viewer.layout.addWidget(self.pageView)

            self.soln = QLabel()
            self.viewer.layout.addWidget(self.soln)
            
    def pageLoader(self):
        self.pageLayout = QHBoxLayout()
        prev = QPushButton("<--")
        prev.clicked.connect(self.prevPage)
        self.pageLayout.addWidget(prev)

        self.pageLabel = QLabel(f"Page {self.page + 1} of {self.last + 1}")
        self.pageLayout.addWidget(self.pageLabel)
        
        self.page = 0
        self.last = 0

        next = QPushButton("-->")
        next.clicked.connect(self.nextPage)
        self.pageLayout.addWidget(next)
        widget = QWidget()
        widget.setLayout(self.pageLayout)
        return widget
    
    def prevPage(self):
        if self.page > 0:
            self.page -= 1
        self.pageLabel.setText(f"Page {self.page + 1} of {self.last + 1}")
        try:
            self.op.setText(self.hist[self.page][1])
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass
    
    def nextPage(self):
        if self.page < self.last:
            self.page += 1
        self.pageLabel.setText(f"Page {self.page + 1} of {self.last + 1}")
        try:
            self.op.setText(self.hist[self.page][1])
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass
    
    def actionWindow(self):
        self.window = NumStabilityWindows.ActionWindow()
        self.window.show()
        self.window.nums.connect(self.action)
    
    def displayType(self, string):
        return displayAsMatrix(string, self.augcol) if self.asMatrix else displayAsBasis(string)
    
    def action(self, params):
        num, stability = params
        if self.matrix is None:
            return
        self.calculationAccWheel.setDisabled(True)
        if num == 1:
            self.augcol = 1
            self.asMatrix = True
            final, self.hist = GaussianEliminate(self.matrix.copy(), stability)
            self.soln.setStyleSheet("color: black; font-family: Cascadia Mono")
            lst = GaussianSolve(final, stability)
            if isinstance(lst, list):
                for i in range(len(lst)):
                    lst[i] = f"x{i}: {lst[i].evalf(3)}"
                self.soln.setText(str(lst)[1:-1].replace("'",""))
            else:
                self.soln.setText(lst)
            self.page = 0
            self.last = len(self.hist) - 1
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
            self.pageLabel.setText(f"Page 1 of {self.last + 1}")
            self.op.setText(self.hist[0][1])
        elif num == 2:
            self.asMatrix = False
            self.hist, norm = GramSchmidtOrth(self.matrix.copy(), stability, self.calculationAcc)
            statusColour = (lambda x: "black" if norm is None else "green" if norm < 10 ** -12 else "orange" if norm < 10 ** -8 else "red")(norm)
            statusText = (lambda x: "N/A" if norm is None else "Good" if norm < 10 ** -12 else "Fair" if norm < 10 ** -8 else "Poor")(norm)
            self.soln.setText(f"Orthogonality Error (Frobenius norm): {norm} ({statusText})")
            self.soln.setStyleSheet(f"color: {statusColour}; font-family: Cascadia Mono")
            self.page = 0
            self.last = len(self.hist) - 1
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
            self.pageLabel.setText(f"Page 1 of {self.last + 1}")
            self.op.setText(self.hist[0][1])