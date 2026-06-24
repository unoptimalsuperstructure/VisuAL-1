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

        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_action)
        self.timer.setInterval(0)

        self.pressed_keys = set()

        self.lastOpStack = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self.last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            cur_pos = event.position().toPoint()
            delta = cur_pos - self.last_mouse_pos
            self.last_mouse_pos = cur_pos
    
    def mouseReleaseEvent(self, event):
        pass
            
        self.update()

    def keyPressEvent(self, event):
        self.pressZ = False
        self.pressH = False
        self.pressV = False
        if not event.isAutoRepeat():
            self.pressed_keys.add(event.key())
            self.perform_action()
            if not self.timer.isActive():
                self.timer.start()
        
    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.pressed_keys.discard(event.key())
            if not self.pressed_keys:
                self.timer.stop()
        
        self.update()

    def perform_action(self):
        if Qt.Key.Key_W in self.pressed_keys:
            pass
        if Qt.Key.Key_S in self.pressed_keys:
            pass
        if Qt.Key.Key_A in self.pressed_keys:
            pass
        if Qt.Key.Key_D in self.pressed_keys:
            pass
        if Qt.Key.Key_Z in self.pressed_keys:
            pass
            
        self.update()

    def update(self):
        gc.collect()

class NumStabilitySidePanel(QVBoxLayout):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer

        self.matrix = None
        self.basis = None

        addDataButton = QPushButton("Import CSV...")
        addDataButton.clicked.connect(self.loadCSV)
        randomDataButton = QPushButton("Generate random data...")
        actionButton = QPushButton("Action...")
        actionButton.clicked.connect(self.actionWindow)

        self.addWidget(addDataButton)
        self.addWidget(randomDataButton)
        self.addWidget(actionButton)

    def select(self):
        pass


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
                    mat.append(list(map(lambda x: float(x), row)))
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
            disp = displayAsMatrix(toString(self.matrix, 6), True)
            self.displayMatrix = QLabel(disp)
            self.displayMatrix.setStyleSheet("""
            * {
                font-size: 12px;
                font-family: Cascadia Mono;
                text-align: center;
            }
            """)

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
            self.soln.setStyleSheet("""
            * {
                font-size: 12px;
                font-family: Cascadia Mono;
                text-align: center;
            }
            """)
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
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], 6)))
        except:
            pass
    
    def nextPage(self):
        if self.page < self.last:
            self.page += 1
        self.pageLabel.setText(f"Page {self.page + 1} of {self.last + 1}")
        try:
            self.op.setText(self.hist[self.page][1])
            self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], 6)))
        except:
            pass
    
    def actionWindow(self):
        self.window = NumStabilityWindows.ActionWindow()
        self.window.show()
        self.window.num.connect(self.action)
    
    def displayType(self, string):
        return displayAsMatrix(string, True) if self.asMatrix else displayAsBasis(string)
    
    def action(self, num):
        if num == 1:
            if self.matrix is not None:
                self.asMatrix = True
                final, self.hist = GaussianEliminate(self.matrix)
                lst = GaussianSolve(self.matrix.copy())
                if isinstance(lst, list):
                    for i in range(len(lst)):
                        lst[i] = f"x{i}: {lst[i].evalf(3)}"
                    self.soln.setText(str(lst)[1:-1].replace("'",""))
                else:
                    self.soln.setText(lst)
                self.page = 0
                self.last = len(self.hist) - 1
                self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], 6)))
                self.pageLabel.setText(f"Page 1 of {self.last + 1}")
                self.op.setText(self.hist[0][1])
        elif num == 2:
            if self.matrix is not None:
                self.soln.setText("")
                self.asMatrix = False
                self.hist = GramSchmidtOrth(self.matrix.copy())
                self.page = 0
                self.last = len(self.hist) - 1
                self.displayMatrix.setText(self.displayType(toString(self.hist[self.page][0], 6)))
                self.pageLabel.setText(f"Page 1 of {self.last + 1}")
                self.op.setText(self.hist[0][1])