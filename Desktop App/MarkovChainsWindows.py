from PyQt6.QtWidgets import *
from PyQt6.QtGui import QDoubleValidator, QColor
from PyQt6.QtCore import pyqtSignal, Qt, QEvent
import numpy as np

def num(x):
    if x == "":
        return 0
    else:
        try:
            return eval(x)
        except:
            return None

def makeStateVector(state, theme):
    d = len(state)
    stateVector = TableWithLeave()
    stateVector.installEventFilter(stateVector)
    stateVector.setItemDelegate(NonNegativeDelegate(theme))
    stateVector.setRowCount(d)
    stateVector.setColumnCount(1)
    stateVector.setFixedSize(40, 40 * d)
    stateVector.verticalHeader().setDefaultSectionSize(40)
    stateVector.horizontalHeader().setDefaultSectionSize(40)
    stateVector.verticalHeader().hide()
    stateVector.horizontalHeader().hide()
    stateVector.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    stateVector.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    for i in range(d):
        stateVector.setItem(i, 0, QTableWidgetItem(f"{state[i]:.2f}"))
    stateVector.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
    stateVector.setMouseTracking(True)
    return stateVector

def makeTransitionMatrix(mat, theme):
    d = mat.shape[0]
    transitionMatrix = TableWithLeave()
    transitionMatrix.installEventFilter(transitionMatrix)
    transitionMatrix.setItemDelegate(NonNegativeDelegate(theme))
    transitionMatrix.setRowCount(d)
    transitionMatrix.setColumnCount(d)
    states = ["A", "B", "C", "D", "E", "F"][:d]
    transitionMatrix.setVerticalHeaderLabels(states)
    transitionMatrix.setHorizontalHeaderLabels(states)
    transitionMatrix.verticalHeader().setDefaultSectionSize(40)
    transitionMatrix.horizontalHeader().setDefaultSectionSize(40)
    transitionMatrix.setFixedSize(40 * d + 20, 40 * d + 25)
    transitionMatrix.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    transitionMatrix.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    transitionMatrix.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    transitionMatrix.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    transitionMatrix.verticalHeader().setHighlightSections(False)
    transitionMatrix.horizontalHeader().setHighlightSections(False)
    for i in range(d):
        for j in range(d):
            transitionMatrix.setItem(i, j, QTableWidgetItem(f"{mat[i, j]:.2f}"))
    transitionMatrix.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
    transitionMatrix.setMouseTracking(True)
    return transitionMatrix

class TableWithLeave(QTableWidget):
    mouseLeft = pyqtSignal()

    def leaveEvent(self, event):
        self.mouseLeft.emit()
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            self.clearSelection()
        
        return super().eventFilter(obj, event)

class NonNegativeDelegate(QStyledItemDelegate):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setStyleSheet("QLineEdit { background-color: #505050; }" if self.theme else "QLineEdit { background-color: #f0f0f0; }")

        validator = QDoubleValidator(0.0, 1e100, 10, editor)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        editor.setValidator(validator)
        return editor

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

class AddMarkovWindow(QWidget):
    params = pyqtSignal(list)
    def __init__(self, theme):
        super().__init__()
        self.states = 2
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("What type of Markov chain?"), 0, 0)
        self.isCTMC = False
        self.requestCTMCDiagonal = False
        self.theme = theme

        self.transitionMatrix = makeTransitionMatrix(np.zeros((6, 6)), theme)
        self.transitionMatrix.itemChanged.connect(self.CTMCUpdate)
        self.stateVector = makeStateVector([0, 0, 0, 0, 0, 0], theme)
        self.changeStates(2)
        self.layout.addWidget(self.transitionMatrix, 2, 0, 1, 2)
        self.layout.addWidget(self.stateVector, 2, 2)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.send)
        self.layout.addWidget(self.submit, 3, 0, 1, 3)

        DTMC = QRadioButton("DTMC")
        DTMC.setObjectName("0")
        DTMC.toggled.connect(self.onToggle)
        DTMC.setChecked(True)
        self.layout.addWidget(DTMC, 0, 1)

        CTMC = QRadioButton("CTMC")
        CTMC.setObjectName("1")
        CTMC.toggled.connect(self.onToggle)
        self.layout.addWidget(CTMC, 0, 2)

        self.layout.addWidget(QLabel("Number of states:"), 1, 0, 1, 2)
        self.numStates = QSpinBox()
        self.numStates.setRange(2, 6)
        self.numStates.setValue(2)
        self.numStates.valueChanged.connect(self.changeStates)
        self.layout.addWidget(self.numStates, 1, 2)
        
        self.setLayout(self.layout)
    
    def changeStates(self, x):
        self.requestCTMCDiagonal = False
        self.states = x
        for i in range(6):
            for j in range(6):
                item = QTableWidgetItem("-" if i >= x or j >= x else "0")
                if (self.isCTMC and i == j) or (i >= x or j >= x):
                    item.setBackground(QColor("#505050" if self.theme else "#E0E0E0"))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.transitionMatrix.setItem(i, j, item)
            item = QTableWidgetItem("-" if i >= x else "0")
            if i >= x:
                item.setBackground(QColor("#505050" if self.theme else "#E0E0E0"))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.stateVector.setItem(i, 0, item)
        self.requestCTMCDiagonal = self.isCTMC
    
    def onToggle(self):
        rb = self.sender()
        self.isCTMC = int(rb.objectName())
        self.changeStates(self.states)
    
    def CTMCUpdate(self, item):
        if self.requestCTMCDiagonal:
            self.transitionMatrix.blockSignals(True)
            for i in range(self.states):
                total = 0
                for j in range(self.states):
                    if i != j:
                        total += float(self.transitionMatrix.item(j, i).text())
                self.transitionMatrix.item(i, i).setText(f"{-total:.3f}")
            self.transitionMatrix.blockSignals(False)
    
    def validate(self, mat, init):
        valid = True
        try:
            matrix = np.array(mat)
            vec = np.array(init).T
        except:
            valid = False
            self.error = ErrorWindow(2, None)
            self.error.show()
        
        if matrix.shape[0] != matrix.shape[1]:
            valid = False
            self.error = ErrorWindow(101, None)
            self.error.show()
        
        else:
            for col in matrix.T:
                if np.linalg.norm(col) == 0:
                    valid = False
                    self.error = ErrorWindow(103, None)
                    self.error.show()
                elif not self.isCTMC and np.min(col) < 0:
                    valid = False
                    self.error = ErrorWindow(102, None)
                    self.error.show()
        
        if valid and np.linalg.norm(vec) == 0:
            valid = False
            self.error = ErrorWindow(103, None)
            self.error.show()
        
        if valid and np.min(vec) < 0:
            valid = False
            self.error = ErrorWindow(102, None)
            self.error.show()
        
        if valid and matrix.size > 36:
            valid = False
            self.error = ErrorWindow(104, None)
            self.error.show()
        
        return valid
    
    def send(self):
        mat = []
        vec = []
        for i in range(self.states):
            row = []
            for j in range(self.states):
                row.append(float(self.transitionMatrix.item(i, j).text()))
            mat.append(row)
        for i in range(self.states):
            vec.append(float(self.stateVector.item(i, 0).text()))
        if self.validate(mat, vec):
            self.params.emit([mat, vec, self.isCTMC])
            self.close()
    
    def closeEvent(self, event):
        event.accept()