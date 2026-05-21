from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from MatrixPrinter import toString, concat
import math

class TranslateWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Translate")
        self.activeObj = activeObj
        self.layout = QVBoxLayout()

        if self.activeObj:
            self.xval = None
            self.yval = None
            self.zval = None
            self.inputX = QLineEdit()
            self.inputY = QLineEdit()
            self.inputZ = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("x:"))
            self.layout.addWidget(self.inputX)
            self.layout.addWidget(QLabel("y:"))
            self.layout.addWidget(self.inputY)
            self.layout.addWidget(QLabel("z:"))
            self.layout.addWidget(self.inputZ)
            self.layout.addWidget(self.submit)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        x = self.inputX.text()
        y = self.inputY.text()
        z = self.inputZ.text()
        try:
            self.xval = float(x)
            self.yval = float(y)
            self.zval = float(z)
            self.close()
        except:
            print("Please enter numbers only.")
    
    def closeEvent(self, event):
        if self.activeObj:
            if self.xval == None:
                self.xval = 0
                self.yval = 0
                self.zval = 0
            self.nums.emit([self.xval, self.yval, self.zval])
        event.accept()

class ReflectLineWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Reflect about Line")
        self.activeObj = activeObj
        self.layout = QVBoxLayout()

        if self.activeObj:
            self.a1val = None
            self.a2val = None
            self.a3val = None
            self.d1val = None
            self.d2val = None
            self.d3val = None

            self.inputA1 = QLineEdit()
            self.inputA2 = QLineEdit()
            self.inputA3 = QLineEdit()
            self.inputD1 = QLineEdit()
            self.inputD2 = QLineEdit()
            self.inputD3 = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter the numbers for the vector equation of the line.\n" \
                                         "The format is r: (a1, a2, a3) + t(d1, d2, d3) where t is a real parameter."))
            self.layout.addWidget(QLabel("a1:"))
            self.layout.addWidget(self.inputA1)
            self.layout.addWidget(QLabel("a2:"))
            self.layout.addWidget(self.inputA2)
            self.layout.addWidget(QLabel("a3:"))
            self.layout.addWidget(self.inputA3)
            self.layout.addWidget(QLabel("d1:"))
            self.layout.addWidget(self.inputD1)
            self.layout.addWidget(QLabel("d2:"))
            self.layout.addWidget(self.inputD2)
            self.layout.addWidget(QLabel("d3:"))
            self.layout.addWidget(self.inputD3)
            self.layout.addWidget(self.submit)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        a1 = self.inputA1.text()
        a2 = self.inputA2.text()
        a3 = self.inputA3.text()
        d1 = self.inputD1.text()
        d2 = self.inputD2.text()
        d3 = self.inputD3.text()
        try:
            self.a1val = float(a1)
            self.a2val = float(a2)
            self.a3val = float(a3)
            self.d1val = float(d1)
            self.d2val = float(d2)
            self.d3val = float(d3)
            self.close()
        except:
            print("Please enter numbers only.")
    
    def closeEvent(self, event):
        if self.activeObj:
            if self.a1val == None:
                self.a1val = 0
                self.a2val = 0
                self.a3val = 0
                self.d1val = 0
                self.d2val = 0
                self.d3val = 0
            self.nums.emit([self.a1val, self.a2val, self.a3val, self.d1val, self.d2val, self.d3val])
        event.accept()

class ReflectPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Reflect about Plane")
        self.activeObj = activeObj
        self.layout = QVBoxLayout()

        if self.activeObj:
            self.aval = None
            self.bval = None
            self.cval = None
            self.dval = None

            self.inputA = QLineEdit()
            self.inputB = QLineEdit()
            self.inputC = QLineEdit()
            self.inputD = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter a, b, c, d for the plane with equation ax + by + cz = d."))
            self.layout.addWidget(QLabel("a:"))
            self.layout.addWidget(self.inputA)
            self.layout.addWidget(QLabel("b:"))
            self.layout.addWidget(self.inputB)
            self.layout.addWidget(QLabel("c:"))
            self.layout.addWidget(self.inputC)
            self.layout.addWidget(QLabel("d:"))
            self.layout.addWidget(self.inputD)
            self.layout.addWidget(self.submit)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        a = self.inputA.text()
        b = self.inputB.text()
        c = self.inputC.text()
        d = self.inputD.text()
        try:
            self.aval = float(a)
            self.bval = float(b)
            self.cval = float(c)
            self.dval = float(d)
            self.close()
        except:
            print("Please enter numbers only.")
    
    def closeEvent(self, event):
        if self.activeObj:
            if self.aval == None:
                self.aval = 0
                self.bval = 0
                self.cval = 0
                self.dval = 0
            self.nums.emit([self.aval, self.bval, self.cval, self.dval])
        event.accept()

class RotateWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Rotate about Line")
        self.activeObj = activeObj
        self.layout = QVBoxLayout()

        if self.activeObj:
            self.angle = None
            self.a1val = None
            self.a2val = None
            self.a3val = None

            self.inputAngle = QLineEdit()
            self.inputA1 = QLineEdit()
            self.inputA2 = QLineEdit()
            self.inputA3 = QLineEdit()
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter the numbers for the vector equation of the line and angle in degrees.\n" \
                                         "The format is r: t(a1, a2, a3) where t is a real parameter."))
            self.layout.addWidget(QLabel("Angle:"))
            self.layout.addWidget(self.inputAngle)
            self.layout.addWidget(QLabel("a1:"))
            self.layout.addWidget(self.inputA1)
            self.layout.addWidget(QLabel("a2:"))
            self.layout.addWidget(self.inputA2)
            self.layout.addWidget(QLabel("a3:"))
            self.layout.addWidget(self.inputA3)
            self.layout.addWidget(self.submit)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        angle = self.inputAngle.text()
        a1 = self.inputA1.text()
        a2 = self.inputA2.text()
        a3 = self.inputA3.text()
        try:
            self.angle = float(angle)
            self.a1val = float(a1)
            self.a2val = float(a2)
            self.a3val = float(a3)
            self.close()
        except:
            print("Please enter numbers only.")
    
    def closeEvent(self, event):
        if self.activeObj:
            if self.a1val == None:
                self.a1val = 0
                self.a2val = 0
                self.a3val = 0
            self.nums.emit([self.angle, self.a1val, self.a2val, self.a3val])
        event.accept()    

class AddShapeWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Shape")

        self.shapes = dict({"UnitCube": ["UnitCube"]})

        self.item = None
        self.layout = QVBoxLayout()

        addUnitCubeButton = QRadioButton("UnitCube")
        addUnitCubeButton.type = "UnitCube"
        addUnitCubeButton.toggled.connect(self.onToggle)
        submit = QPushButton("Submit")
        submit.clicked.connect(self.send)
        self.layout.addWidget(addUnitCubeButton)
        self.layout.addWidget(submit)
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.isChecked():
            self.item = self.shapes.get(rb.type)
        else:
            self.item = None

    def send(self):
        if self.item:
            self.close()
        else:
            print("Please select an object.")
    
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