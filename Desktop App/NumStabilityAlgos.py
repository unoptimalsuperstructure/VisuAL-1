import NumStabilityWindows
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPoint, QEvent
from Tooltips import TooltipButton
import csv
import numpy as np
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
        randomDataButton = TooltipButton("Generate random data...",
                                         "CustomMatrix",
                                         "Feature coming soon")
        randomDataButton.setDisabled(True)
        randomDataButton.installEventFilter(self)
        actionButton = QPushButton("Action...")
        actionButton.clicked.connect(self.actionWindow)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)

        self.addWidget(addDataButton)
        self.addWidget(randomDataButton)
        self.addWidget(actionButton)
        self.addWidget(resetButton)

    def eventFilter(self, obj, event):
            if isinstance(obj, TooltipButton):
                if event.type() == QEvent.Type.Enter:
                    self.show_bubble_above_button(obj)
                    return True
                elif event.type() == QEvent.Type.Leave:
                    obj.tooltip.hide()
                    return True
            return super().eventFilter(obj, event)
    
    def show_bubble_above_button(self, button):
        button_global_pos = button.mapToGlobal(QPoint(0, 0))
            
        x = button_global_pos.x() - button.tooltip.width() - 15
        y = button_global_pos.y() + (button.height() // 2) - (button.tooltip.height() // 2)
            
        button.tooltip.move(x, y)
        button.tooltip.show()
    
    def setDisplayAcc(self, x):
        self.displayAcc = int(x)
    
    def setCalculationAcc(self, x):
        self.calculationAcc = int(x)
    
    def reset(self):
        if self.matrix is not None:
            try:
                self.viewer.layout.removeWidget(self.displayMatrix)
            except:
                pass
            self.calculationAccWheel.setEnabled(True)
            self.asMatrix = True
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
                self.viewer.layout.removeWidget(self.soln1)
                self.viewer.layout.removeWidget(self.soln2)
                self.viewer.layout.removeWidget(self.soln3)
            except:
                pass
            
            self.op = QLabel()
            self.viewer.layout.addWidget(self.op)
            self.pageView = self.pageLoader()
            self.viewer.layout.addWidget(self.pageView)

            self.soln1 = QLabel()
            self.viewer.layout.addWidget(self.soln1)

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
                self.viewer.layout.removeWidget(self.soln1)
                self.viewer.layout.removeWidget(self.soln2)
                self.viewer.layout.removeWidget(self.soln3)
            except:
                pass
            
            self.op = QLabel()
            self.op.setStyleSheet("font-family: Cascadia Mono")
            self.enableLU = False
            self.viewer.layout.addWidget(self.op)
            self.pageView = self.pageLoader()
            self.viewer.layout.addWidget(self.pageView)

            self.soln1 = QLabel()
            self.viewer.layout.addWidget(self.soln1)
            
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
            if self.enableLU:
                self.op.setText(self.hist[self.page][1] + "\n" + concat([toString(np.linalg.inv(self.hist[self.page][2]), 3), toString(self.hist[self.page][3], 3), toString(self.hist[self.page][0], 3)]))
            else:
                self.op.setText(self.hist[self.page][1])
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass
    
    def nextPage(self):
        if self.page < self.last:
            self.page += 1
        self.pageLabel.setText(f"Page {self.page + 1} of {self.last + 1}")
        try:
            if self.enableLU:
                self.op.setText(self.hist[self.page][1] + "\n" + concat([toString(np.linalg.inv(self.hist[self.page][2]), 3), toString(self.hist[self.page][3], 3), toString(self.hist[self.page][0], 3)]))
            else:
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
        val = params[0]
        if self.matrix is None:
            return
        self.calculationAccWheel.setDisabled(True)
        try:
            self.viewer.layout.removeWidget(self.soln2)
            self.viewer.layout.removeWidget(self.soln3)
        except:
            pass
        if val == 1:
            pivot, enableLU = params[1:]
            self.asMatrix = True
            final, self.hist = GaussianEliminate(self.matrix.copy(), pivot, enableLU, self.calculationAcc)
            self.soln1.setStyleSheet("color: black; font-family: Cascadia Mono")
            if enableLU:
                self.enableLU = True
                self.augcol = 0
                self.soln1.setText("LUP Decomposition: P^-1LU = A")
                self.op.setText(self.hist[0][1] + "\n" + concat([toString(np.linalg.inv(self.hist[0][2]), 3), toString(self.hist[0][3], 3), toString(self.hist[0][0], 3)]))
            else:
                self.enableLU = False
                self.augcol = 1
                lst = GaussianSolve(final, pivot, enableLU, self.calculationAcc)
                if isinstance(lst, list):
                    for i in range(len(lst)):
                        lst[i] = f"x{i}: {lst[i].evalf(3)}"
                    self.soln1.setText(str(lst)[1:-1].replace("'",""))
                else:
                    self.soln1.setText(lst)
                self.op.setText(self.hist[0][1])
            self.page = 0
            self.last = len(self.hist) - 1
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
            self.pageLabel.setText(f"Page 1 of {self.last + 1}")
        elif val == 3:
            self.enableLU = False
            modified, normed = params[1:]
            self.asMatrix = False
            self.hist, norm = GramSchmidtOrth(self.matrix.copy(), modified, normed, self.calculationAcc)
            statusColour = "black" if norm is None else "green" if norm < 10 ** -12 else "orange" if norm < 10 ** -8 else "red"
            statusText = "N/A" if norm is None else "Good" if norm < 10 ** -12 else "Fair" if norm < 10 ** -8 else "Poor"
            self.soln1.setText(f"Orthogonality Error (Frobenius norm): {norm} ({statusText})")
            self.soln1.setStyleSheet(f"color: {statusColour}; font-family: Cascadia Mono")
            self.page = 0
            self.last = len(self.hist) - 1
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
            self.pageLabel.setText(f"Page 1 of {self.last + 1}")
            self.op.setText(self.hist[0][1])
        elif val == 2:
            self.enableLU = False
            invMode = params[1]
            if invMode == 1:
                self.hist, iden, norm, cond = GJInverse(self.matrix.copy(), False, self.calculationAcc)
            elif invMode == 2:
                self.hist, iden, norm, cond = GJInverse(self.matrix.copy(), True, self.calculationAcc)
            if self.hist is not None:
                self.augcol = self.matrix.shape[0]
                statusColour = "green" if iden < 10 ** -12 else "orange" if iden < 10 ** -8 else "red"
                statusText = f"Identity Residual (Frobenius norm): {iden} ({"Good" if iden < 10 ** -12 else "Fair" if iden < 10 ** -8 else "Poor; matrix possibly singular"})"
                invrColour = "green" if norm < 10 ** -12 else "orange" if norm < 10 ** -8 else "red"
                invrText = f"Inverse Residual (Frobenius norm): {norm} ({"Good" if norm < 10 ** -12 else "Fair" if norm < 10 ** -8 else "Poor"})\n"
                condColour = "green" if cond < 10 ** 6 else "orange" if cond < 10 ** 10 else "red"
                condText = f"Condition Number (Frobenius norm): {cond} ({"Good" if cond < 10 ** 6 else "Fair" if cond < 10 ** 10 else "Poor"})"
                self.soln1.setText(statusText)
                self.soln1.setStyleSheet(f"color: {statusColour}; font-family: Cascadia Mono")

                self.soln2 = QLabel(invrText)
                self.soln2.setStyleSheet(f"color: {invrColour}; font-family: Cascadia Mono")
                self.soln3 = QLabel(condText)
                self.soln3.setStyleSheet(f"color: {condColour}; font-family: Cascadia Mono")
                self.viewer.layout.addWidget(self.soln2)
                self.viewer.layout.addWidget(self.soln3)

                self.page = 0
                self.last = len(self.hist) - 1
                self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
                self.pageLabel.setText(f"Page 1 of {self.last + 1}")
                self.op.setText(self.hist[0][1])
            else:
                self.calculationAccWheel.setDisabled(False)
                self.error = NumStabilityWindows.ErrorWindow(3, None)
                self.error.show()
        elif val == 4:
            self.enableLU = False
            self.asMatrix = True
            self.hist = DiagonaliseMatrix(self.matrix.copy())
            self.soln1.setText("Diagonalisation")
            self.page = 0
            self.last = len(self.hist) - 1
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
            self.pageLabel.setText(f"Page 1 of {self.last + 1}")
            self.op.setText(self.hist[0][1])
                              
                              