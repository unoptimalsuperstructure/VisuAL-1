from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from MatrixPrinter import toString, concat
import math

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
            self.layout.addWidget(QLabel("Zero direction vector or normal vector is not allowed. Please try again."))
        else:
            self.layout.addWidget(QLabel("Unknown error occurred."))
        self.submit = QPushButton("OK")
        self.submit.clicked.connect(self.close)
        self.layout.addWidget(self.submit)
        self.setLayout(self.layout)
    
    def closeEvent(self, event):
        self.window.show()
        event.accept()

class TranslateWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Translate")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:
            self.inputX = QLineEdit()
            self.inputY = QLineEdit()
            self.inputZ = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter the units to translate along the x, y and z-axes."), 0, 0, 1, 2)
            self.layout.addWidget(QLabel("x:"), 1, 0)
            self.layout.addWidget(self.inputX, 1, 1)
            self.layout.addWidget(QLabel("y:"), 2, 0)
            self.layout.addWidget(self.inputY, 2, 1)
            self.layout.addWidget(QLabel("z:"), 3, 0)
            self.layout.addWidget(self.inputZ, 3, 1)
            self.layout.addWidget(self.submit, 4, 0, 1, 2)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        x = num(self.inputX.text())
        y = num(self.inputY.text())
        z = num(self.inputZ.text())
        if x == None or y == None or z == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([x, y, z])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class ReflectLineWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Reflect about Line")
        self.activeObj = activeObj
        self.header = QWidget()
        self.headerLayout = QVBoxLayout()
        self.input = QWidget()
        self.inputLayout = QGridLayout()
        self.layout = QVBoxLayout()

        self.input.setStyleSheet("QLabel{font-family: Cascadia Mono}")

        if self.activeObj:

            self.inputA1 = QLineEdit()
            self.inputA2 = QLineEdit()
            self.inputA3 = QLineEdit()
            self.inputD1 = QLineEdit()
            self.inputD2 = QLineEdit()
            self.inputD3 = QLineEdit()
            self.inputA1.setFixedWidth(120)
            self.inputA2.setFixedWidth(120)
            self.inputA3.setFixedWidth(120)
            self.inputD1.setFixedWidth(120)
            self.inputD2.setFixedWidth(120)
            self.inputD3.setFixedWidth(120)
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)
            
            self.headerLayout.addWidget(QLabel("Enter the vector equation of the line.\n" \
                                               "The format is r: (a1, a2, a3) + t(d1, d2, d3) where t is a real parameter."))
            self.header.setLayout(self.headerLayout)
            self.layout.addWidget(self.header)
            self.inputLayout.addWidget(QLabel("    ["), 1, 0)
            self.inputLayout.addWidget(self.inputA1, 1, 1)
            self.inputLayout.addWidget(QLabel("]     ["), 1, 2)
            self.inputLayout.addWidget(self.inputD1, 1, 3)
            self.inputLayout.addWidget(QLabel("]"), 1, 4)
            self.inputLayout.addWidget(QLabel("r = ["), 2, 0)
            self.inputLayout.addWidget(self.inputA2, 2, 1)
            self.inputLayout.addWidget(QLabel("] + t ["), 2, 2)
            self.inputLayout.addWidget(self.inputD2, 2, 3)
            self.inputLayout.addWidget(QLabel("]"), 2, 4)
            self.inputLayout.addWidget(QLabel("    ["), 3, 0)
            self.inputLayout.addWidget(self.inputA3, 3, 1)
            self.inputLayout.addWidget(QLabel("]     ["), 3, 2)
            self.inputLayout.addWidget(self.inputD3, 3, 3)
            self.inputLayout.addWidget(QLabel("]"), 3, 4)
            self.inputLayout.addWidget(self.submit, 4, 0, 1, 5)

            self.input.setLayout(self.inputLayout)
            self.layout.addWidget(self.input)

        else:
            self.headerLayout.addWidget(QLabel("Cannot transform when no object is selected"))
            self.header.setLayout(self.headerLayout)
            self.layout.addWidget(self.header)
        
        self.setLayout(self.layout)

    def send(self):
        a1 = num(self.inputA1.text())
        a2 = num(self.inputA2.text())
        a3 = num(self.inputA3.text())
        d1 = num(self.inputD1.text())
        d2 = num(self.inputD2.text())
        d3 = num(self.inputD3.text())
        if a1 == None or a2 == None or a3 == None or d1 == None or d2 == None or d3 == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif d1 == 0 and d2 == 0 and d3 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a1, a2, a3, d1, d2, d3])
            self.close()
    
    def closeEvent(self, event):
        event.accept()

class ReflectPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Reflect about Plane")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:

            self.inputA = QLineEdit()
            self.inputA.setFixedWidth(50)
            self.inputB = QLineEdit()
            self.inputB.setFixedWidth(50)
            self.inputC = QLineEdit()
            self.inputC.setFixedWidth(50)
            self.inputD = QLineEdit()
            self.inputD.setFixedWidth(50)
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter a, b, c, d for the plane with equation ax + by + cz = d."), 0, 0, 1, 7)
            self.layout.addWidget(self.inputA, 1, 0)
            self.layout.addWidget(QLabel("x +"), 1, 1)
            self.layout.addWidget(self.inputB, 1, 2)
            self.layout.addWidget(QLabel("y +"), 1, 3)
            self.layout.addWidget(self.inputC, 1, 4)
            self.layout.addWidget(QLabel("z ="), 1, 5)
            self.layout.addWidget(self.inputD, 1, 6)
            self.layout.addWidget(self.submit, 2, 0, 1, 7)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        a = num(self.inputA.text())
        b = num(self.inputB.text())
        c = num(self.inputC.text())
        d = num(self.inputD.text())
        if a == None or b == None or c == None or d == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif a == 0 and b == 0 and c == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a, b, c, d])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class RotateLineWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Rotate about Line")
        self.activeObj = activeObj
        self.header = QWidget()
        self.headerLayout = QVBoxLayout()
        self.input = QWidget()
        self.inputLayout = QGridLayout()
        self.layout = QVBoxLayout()

        self.input.setStyleSheet("QLabel{font-family: Cascadia Mono}")

        if self.activeObj:

            self.inputA1 = QLineEdit()
            self.inputA2 = QLineEdit()
            self.inputA3 = QLineEdit()
            self.inputD1 = QLineEdit()
            self.inputD2 = QLineEdit()
            self.inputD3 = QLineEdit()
            self.inputR = QLineEdit()
            self.inputA1.setFixedWidth(120)
            self.inputA2.setFixedWidth(120)
            self.inputA3.setFixedWidth(120)
            self.inputD1.setFixedWidth(120)
            self.inputD2.setFixedWidth(120)
            self.inputD3.setFixedWidth(120)
            self.inputR.setFixedWidth(120)
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)
            
            self.headerLayout.addWidget(QLabel("Enter the numbers for the vector equation of the line.\n" \
                                               "The format is r: (a1, a2, a3) + t(d1, d2, d3) where t is a real parameter.\n" \
                                               "Enter also the angle of rotation in degrees."))
            self.header.setLayout(self.headerLayout)
            self.layout.addWidget(self.header)
            self.inputLayout.addWidget(QLabel("    ["), 1, 0)
            self.inputLayout.addWidget(self.inputA1, 1, 1)
            self.inputLayout.addWidget(QLabel("]     ["), 1, 2)
            self.inputLayout.addWidget(self.inputD1, 1, 3)
            self.inputLayout.addWidget(QLabel("]"), 1, 4)
            self.inputLayout.addWidget(QLabel("r = ["), 2, 0)
            self.inputLayout.addWidget(self.inputA2, 2, 1)
            self.inputLayout.addWidget(QLabel("] + t ["), 2, 2)
            self.inputLayout.addWidget(self.inputD2, 2, 3)
            self.inputLayout.addWidget(QLabel("]"), 2, 4)
            self.inputLayout.addWidget(QLabel("    ["), 3, 0)
            self.inputLayout.addWidget(self.inputA3, 3, 1)
            self.inputLayout.addWidget(QLabel("]     ["), 3, 2)
            self.inputLayout.addWidget(self.inputD3, 3, 3)
            self.inputLayout.addWidget(QLabel("]"), 3, 4)
            self.inputLayout.addWidget(QLabel("Rotation angle (degrees):"), 4, 0, 1, 3)
            self.inputLayout.addWidget(self.inputR, 4, 3, 1, 1)
            self.inputLayout.addWidget(self.submit, 5, 0, 1, 5)

            self.input.setLayout(self.inputLayout)
            self.layout.addWidget(self.input)

        else:
            self.headerLayout.addWidget(QLabel("Cannot transform when no object is selected"))
            self.header.setLayout(self.headerLayout)
            self.layout.addWidget(self.header)
        
        self.setLayout(self.layout)

    def send(self):
        a1 = num(self.inputA1.text())
        a2 = num(self.inputA2.text())
        a3 = num(self.inputA3.text())
        d1 = num(self.inputD1.text())
        d2 = num(self.inputD2.text())
        d3 = num(self.inputD3.text())
        r = num(self.inputR.text())
        if a1 == None or a2 == None or a3 == None or d1 == None or d2 == None or d3 == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif d1 == 0 and d2 == 0 and d3 == 0 or r % 360 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a1, a2, a3, d1, d2, d3, r])
            self.close()
    
    def closeEvent(self, event):
        event.accept()

class ProjectPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Project onto Plane")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:

            self.inputA = QLineEdit()
            self.inputA.setFixedWidth(50)
            self.inputB = QLineEdit()
            self.inputB.setFixedWidth(50)
            self.inputC = QLineEdit()
            self.inputC.setFixedWidth(50)
            self.inputD = QLineEdit()
            self.inputD.setFixedWidth(50)
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter a, b, c, d for the plane with equation ax + by + cz = d."), 0, 0, 1, 7)
            self.layout.addWidget(self.inputA, 1, 0)
            self.layout.addWidget(QLabel("x +"), 1, 1)
            self.layout.addWidget(self.inputB, 1, 2)
            self.layout.addWidget(QLabel("y +"), 1, 3)
            self.layout.addWidget(self.inputC, 1, 4)
            self.layout.addWidget(QLabel("z ="), 1, 5)
            self.layout.addWidget(self.inputD, 1, 6)
            self.layout.addWidget(self.submit, 2, 0, 1, 7)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        a = num(self.inputA.text())
        b = num(self.inputB.text())
        c = num(self.inputC.text())
        d = num(self.inputD.text())
        if a == None or b == None or c == None or d == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif a == 0 and b == 0 and c == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a, b, c, d])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class ScaleWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Scale")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:

            self.inputC = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter scaling value c. Note that c > 0.\nValues of c <= 0 will have no effect."), 0, 0, 1, 2)
            self.layout.addWidget(QLabel("c:"), 1, 0)
            self.layout.addWidget(self.inputC, 1, 1)
            self.layout.addWidget(self.submit, 2, 0)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        c = num(self.inputC.text())
        if c == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([c])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class RepeatWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Repeat last Transformations")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:

            self.inputN = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("""Enter the number of past transformations, n, to repeat.\nIf n > the number of transformations so far, it will automatically\nbe rounded down to the number of transformations so far."""), 0, 0, 1, 2)
            self.layout.addWidget(QLabel("n:"), 1, 0)
            self.layout.addWidget(self.inputN, 1, 1)
            self.layout.addWidget(self.submit, 2, 0)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        try:
            n = int(self.inputN.text())
            if n > 0:
                self.nums.emit([n])
            else:
                self.error = ErrorWindow(1, self)
                self.nums.emit([self.error])
        except:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        finally:
            self.close()
    
    def closeEvent(self, event):
        event.accept()

class AddShapeWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Shape")

        self.shapes = {"UnitCube": ["UnitCube"], "UnitTetrahedron": ["UnitTetrahedron"]}

        self.item = None
        self.layout = QVBoxLayout()

        addUnitCubeButton = QRadioButton("UnitCube")
        addUnitCubeButton.type = "UnitCube"
        addUnitCubeButton.toggled.connect(self.onToggle)
        addUnitTetrahedronButton = QRadioButton("UnitTetrahedron")
        addUnitTetrahedronButton.type = "UnitTetrahedron"
        addUnitTetrahedronButton.toggled.connect(self.onToggle)
        submit = QPushButton("Submit")
        submit.clicked.connect(self.send)
        self.layout.addWidget(QLabel("Select a shape to add. The shape will be added at the origin with unit dimensions."))
        self.layout.addWidget(addUnitCubeButton)
        self.layout.addWidget(addUnitTetrahedronButton)
        self.layout.addWidget(submit)
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.isChecked():
            self.item = self.shapes.get(rb.type)
        else:
            self.item = None

    def send(self):
        if not self.item:
            self.error = ErrorWindow(0, self)
            self.error.show()
        self.close()
    
    def closeEvent(self, event):
        if self.item:
            self.params.emit(self.item)
        event.accept()

class ViewStackWindow(QWidget):
    def __init__(self, obj):
        super().__init__()
        self.setWindowTitle("Matrix Stack")
        self.layout = QVBoxLayout()
        matrixStack = []
        tempStack = obj.matrixStack.copy()
        tempStack.reverse()
        topString = ""
        for matrix in tempStack:
            matrixStack.append(toString(matrix[0]))
            topString += matrix[1] + " " * (30 + 4 * math.floor(math.log(abs(matrix[0]).max(), 10)) - len(matrix[1]))
        label = QLabel(topString + "\n" + (concat(matrixStack)))
        label.setFont(QFont("Courier New"))
        self.layout.addWidget(label)
        self.setLayout(self.layout)