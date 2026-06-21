from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont

from MatrixPrinter import toString, concat
import math, csv, Shapes

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
        elif type == 3:
            self.layout.addWidget(QLabel("This line or plane already exists. Please try again."))
        elif type == 4:
            self.layout.addWidget(QLabel("Name must be non-empty and alphanumeric only. Please try again."))
        elif type == 5:
            self.layout.addWidget(QLabel("This name is already in use. Please try again."))
        else:
            self.layout.addWidget(QLabel("Unknown error occurred."))
        self.submit = QPushButton("OK")
        self.submit.clicked.connect(self.close)
        self.layout.addWidget(self.submit)
        self.setLayout(self.layout)
    
    def closeEvent(self, event):
        self.window.show()
        event.accept()

class InputLine(QWidget):
    def __init__(self):
        super().__init__()
        self.inputLayout = QGridLayout()

        self.setStyleSheet("QLabel{font-family: Cascadia Mono}")

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
            
        self.inputLayout.addWidget(QLabel("Enter the vector equation of the line.\n" \
                                          "The format is r: (a1, a2, a3) + t(d1, d2, d3)\n" \
                                          "where t is a real parameter."), 1, 0, 1, 5)
        self.inputLayout.addWidget(QLabel("    ["), 2, 0)
        self.inputLayout.addWidget(self.inputA1, 2, 1)
        self.inputLayout.addWidget(QLabel("]     ["), 2, 2)
        self.inputLayout.addWidget(self.inputD1, 2, 3)
        self.inputLayout.addWidget(QLabel("]"), 2, 4)
        self.inputLayout.addWidget(QLabel("r = ["), 3, 0)
        self.inputLayout.addWidget(self.inputA2, 3, 1)
        self.inputLayout.addWidget(QLabel("] + t ["), 3, 2)
        self.inputLayout.addWidget(self.inputD2, 3, 3)
        self.inputLayout.addWidget(QLabel("]"), 3, 4)
        self.inputLayout.addWidget(QLabel("    ["), 4, 0)
        self.inputLayout.addWidget(self.inputA3, 4, 1)
        self.inputLayout.addWidget(QLabel("]     ["), 4, 2)
        self.inputLayout.addWidget(self.inputD3, 4, 3)
        self.inputLayout.addWidget(QLabel("]"), 4, 4)
        self.inputLayout.addWidget(self.submit, 5, 0, 1, 5)

        self.setLayout(self.inputLayout)

class InputPlane(QWidget):
    def __init__(self):
        super().__init__()
        self.inputLayout = QGridLayout()

        self.inputA = QLineEdit()
        self.inputB = QLineEdit()
        self.inputC = QLineEdit()
        self.inputD = QLineEdit()
        self.inputA.setFixedWidth(70)
        self.inputB.setFixedWidth(70)
        self.inputC.setFixedWidth(70)
        self.inputD.setFixedWidth(70)
        self.submit = QPushButton("Submit")
            
        self.inputLayout.addWidget(QLabel("Enter a, b, c, d for the plane with equation ax + by + cz = d."), 0, 0, 1, 7)
        self.inputLayout.addWidget(self.inputA, 1, 0)
        self.inputLayout.addWidget(QLabel("x +"), 1, 1)
        self.inputLayout.addWidget(self.inputB, 1, 2)
        self.inputLayout.addWidget(QLabel("y +"), 1, 3)
        self.inputLayout.addWidget(self.inputC, 1, 4)
        self.inputLayout.addWidget(QLabel("z ="), 1, 5)
        self.inputLayout.addWidget(self.inputD, 1, 6)
        self.inputLayout.addWidget(self.submit, 2, 0, 1, 7)

        self.setLayout(self.inputLayout)

class AddLineWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add new Line")
        self.layout = QVBoxLayout()
        self.input = InputLine()
        self.input.submit.clicked.connect(self.send)
        self.layout.addWidget(self.input)
        
        self.setLayout(self.layout)

    def send(self):
        a1 = num(self.input.inputA1.text())
        a2 = num(self.input.inputA2.text())
        a3 = num(self.input.inputA3.text())
        d1 = num(self.input.inputD1.text())
        d2 = num(self.input.inputD2.text())
        d3 = num(self.input.inputD3.text())
        if a1 == None or a2 == None or a3 == None or d1 == None or d2 == None or d3 == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif d1 == 0 and d2 == 0 and d3 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a1, a2, a3, d1, d2, d3, self])
            self.close()
    
    def closeEvent(self, event):
        event.accept()

class AddPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add new Plane")
        self.layout = QVBoxLayout()
        self.input = InputPlane()
        self.input.submit.clicked.connect(self.send)
        self.layout.addWidget(self.input)
        
        self.setLayout(self.layout)

    def send(self):
        a = num(self.input.inputA.text())
        b = num(self.input.inputB.text())
        c = num(self.input.inputC.text())
        d = num(self.input.inputD.text())
        if a == None or b == None or c == None or d == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif a == 0 and b == 0 and c == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a, b, c, d, self])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class DeleteLinePlaneWindow(QWidget):
    objName = pyqtSignal(str)

    def __init__(self, linesPlanes):
        super().__init__()
        self.setWindowTitle("Delete Lines/Planes")
        self.layout = QVBoxLayout()
        selectLinePlaneArea = QScrollArea()
        selectLinePlaneArea.setWidgetResizable(True)
        selectLinePlaneArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectLinePlaneArea.setFixedHeight(100)
        self.selectLinePlane = QWidget()
        self.selectLinePlaneLayout = QVBoxLayout()

        self.layout.addWidget(QLabel("Select the lines/planes to delete:"))
        for obj in linesPlanes:
            option = QCheckBox(obj.name)
            option.setObjectName(obj.name)
            option.toggled.connect(self.onToggle)
            self.selectLinePlaneLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
        
        self.selectLinePlane.setLayout(self.selectLinePlaneLayout)
        selectLinePlaneArea.setWidget(self.selectLinePlane)
        self.layout.addWidget(selectLinePlaneArea, alignment = Qt.AlignmentFlag.AlignTop)

        submit = QPushButton("Submit")
        submit.clicked.connect(self.send)
        self.layout.addWidget(submit)
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        cb = self.sender()
        self.objName.emit(cb.objectName())

    def send(self):
        self.objName.emit("Done")
        self.close()
    
    def closeEvent(self, event):
        self.objName.emit("Close")
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

    def __init__(self, activeObj, linesPlanes):
        super().__init__()
        self.setWindowTitle("Reflect about Line")
        self.layout = QVBoxLayout()
        self.activeObj = activeObj
        selectLineArea = QScrollArea()
        selectLineArea.setWidgetResizable(True)
        selectLineArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectLineArea.setFixedHeight(100)
        self.selectLine = QWidget()
        self.selectLineLayout = QVBoxLayout()

        if self.activeObj:
            self.layout.addWidget(QLabel("Select an existing line to reflect about, or specify a one-time use line:"))
            for obj in linesPlanes:
                if "Line" in obj.name:
                    option = QRadioButton(obj.name)
                    option.setObjectName(obj.name)
                    option.toggled.connect(self.onToggle)
                    self.selectLineLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
            
            addNew = QRadioButton("Specify a one-time use Line...")
            addNew.setObjectName("new")
            addNew.toggled.connect(self.onToggle)
            self.selectLineLayout.addWidget(addNew, alignment = Qt.AlignmentFlag.AlignTop)
            self.selectLine.setLayout(self.selectLineLayout)
            selectLineArea.setWidget(self.selectLine)
            self.layout.addWidget(selectLineArea, alignment = Qt.AlignmentFlag.AlignTop)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "new":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
                QTimer.singleShot(0, self.shrink)
            except:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    QTimer.singleShot(0, self.shrink)
                except:
                    pass
            finally:
                self.input = InputLine()
                self.input.submit.clicked.connect(self.sendNew)
                self.layout.addWidget(self.input)
                self.nums.emit(["Deselect"])
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            finally:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                except:
                    pass
                finally:
                    self.nums.emit([rb.objectName()])
                    self.submit = QPushButton("Submit")
                    self.submit.clicked.connect(self.sendExisting)
                    self.layout.addWidget(self.submit)
                    QTimer.singleShot(0, self.shrink)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendExisting(self):
        self.nums.emit(["Existing Line"])
        self.close()

    def sendNew(self):
        a1 = num(self.input.inputA1.text())
        a2 = num(self.input.inputA2.text())
        a3 = num(self.input.inputA3.text())
        d1 = num(self.input.inputD1.text())
        d2 = num(self.input.inputD2.text())
        d3 = num(self.input.inputD3.text())
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
        self.nums.emit(["Close"])
        event.accept()

class ReflectPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj, linesPlanes):
        super().__init__()
        self.setWindowTitle("Reflect about Plane")
        self.layout = QVBoxLayout()
        self.activeObj = activeObj
        selectLineArea = QScrollArea()
        selectLineArea.setWidgetResizable(True)
        selectLineArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectLineArea.setFixedHeight(100)
        self.selectLine = QWidget()
        self.selectLineLayout = QVBoxLayout()

        if self.activeObj:
            self.layout.addWidget(QLabel("Select an existing plane to reflect about, or specify a one-time use plane:"))
            for obj in linesPlanes:
                if "Plane" in obj.name:
                    option = QRadioButton(obj.name)
                    option.setObjectName(obj.name)
                    option.toggled.connect(self.onToggle)
                    self.selectLineLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
            
            addNew = QRadioButton("Specify a one-time use Plane...")
            addNew.setObjectName("new")
            addNew.toggled.connect(self.onToggle)
            self.selectLineLayout.addWidget(addNew, alignment = Qt.AlignmentFlag.AlignTop)
            self.selectLine.setLayout(self.selectLineLayout)
            selectLineArea.setWidget(self.selectLine)
            self.layout.addWidget(selectLineArea, alignment = Qt.AlignmentFlag.AlignTop)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "new":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
                QTimer.singleShot(0, self.shrink)
            except:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    QTimer.singleShot(0, self.shrink)
                except:
                    pass
            finally:
                self.input = InputPlane()
                self.input.submit.clicked.connect(self.sendNew)
                self.layout.addWidget(self.input)
                self.nums.emit(["Deselect"])
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            finally:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                except:
                    pass
                finally:
                    self.nums.emit([rb.objectName()])
                    self.submit = QPushButton("Submit")
                    self.submit.clicked.connect(self.sendExisting)
                    self.layout.addWidget(self.submit)
                    QTimer.singleShot(0, self.shrink)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendExisting(self):
        self.nums.emit(["Existing Plane"])
        self.close()

    def sendNew(self):
        a = num(self.input.inputA.text())
        b = num(self.input.inputB.text())
        c = num(self.input.inputC.text())
        d = num(self.input.inputD.text())
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
        self.nums.emit(["Close"])
        event.accept()

class RotateLineWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj, linesPlanes):
        super().__init__()
        self.setWindowTitle("Rotate about Line")
        self.layout = QVBoxLayout()
        self.activeObj = activeObj
        selectLineArea = QScrollArea()
        selectLineArea.setWidgetResizable(True)
        selectLineArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectLineArea.setFixedHeight(100)
        self.selectLine = QWidget()
        self.selectLineLayout = QVBoxLayout()

        if self.activeObj:
            header = QWidget()
            headerLayout = QHBoxLayout()
            headerLayout.addWidget(QLabel("Enter the rotation angle, r, in degrees:"))
            self.inputR = QLineEdit()
            headerLayout.addWidget(self.inputR)
            header.setLayout(headerLayout)
            self.layout.addWidget(header)
            self.layout.addWidget(QLabel("Select an existing line to rotate about, or specify a one-time use line:"))
            for obj in linesPlanes:
                if "Line" in obj.name:
                    option = QRadioButton(obj.name)
                    option.setObjectName(obj.name)
                    option.toggled.connect(self.onToggle)
                    self.selectLineLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
            
            addNew = QRadioButton("Specify a one-time use Line...")
            addNew.setObjectName("new")
            addNew.toggled.connect(self.onToggle)
            self.selectLineLayout.addWidget(addNew, alignment = Qt.AlignmentFlag.AlignTop)
            self.selectLine.setLayout(self.selectLineLayout)
            selectLineArea.setWidget(self.selectLine)
            self.layout.addWidget(selectLineArea, alignment = Qt.AlignmentFlag.AlignTop)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "new":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
                QTimer.singleShot(0, self.shrink)
            except:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    QTimer.singleShot(0, self.shrink)
                except:
                    pass
            finally:
                self.input = InputLine()
                self.input.submit.clicked.connect(self.sendNew)
                self.layout.addWidget(self.input)
                self.nums.emit(["Deselect"])
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            finally:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                except:
                    pass
                finally:
                    self.nums.emit([rb.objectName()])
                    self.submit = QPushButton("Submit")
                    self.submit.clicked.connect(self.sendExisting)
                    self.layout.addWidget(self.submit)
                    QTimer.singleShot(0, self.shrink)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendExisting(self):
        r = num(self.inputR.text())
        if r == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif r % 360 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit(["Existing Line", r])
            self.close()

    def sendNew(self):
        a1 = num(self.input.inputA1.text())
        a2 = num(self.input.inputA2.text())
        a3 = num(self.input.inputA3.text())
        d1 = num(self.input.inputD1.text())
        d2 = num(self.input.inputD2.text())
        d3 = num(self.input.inputD3.text())
        r = num(self.inputR.text())
        if a1 == None or a2 == None or a3 == None or d1 == None or d2 == None or d3 == None or r == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif d1 == 0 and d2 == 0 and d3 == 0 or r % 360 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a1, a2, a3, d1, d2, d3, r])
            self.close()
    
    def closeEvent(self, event):
        self.nums.emit(["Close"])
        event.accept()

class ProjectPlaneWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj, linesPlanes):
        super().__init__()
        self.setWindowTitle("Project onto Plane")
        self.layout = QVBoxLayout()
        self.activeObj = activeObj
        selectLineArea = QScrollArea()
        selectLineArea.setWidgetResizable(True)
        selectLineArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectLineArea.setFixedHeight(100)
        self.selectLine = QWidget()
        self.selectLineLayout = QVBoxLayout()

        if self.activeObj:
            self.layout.addWidget(QLabel("Select an existing plane to project onto, or specify a one-time use plane:"))
            for obj in linesPlanes:
                if "Plane" in obj.name:
                    option = QRadioButton(obj.name)
                    option.setObjectName(obj.name)
                    option.toggled.connect(self.onToggle)
                    self.selectLineLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
            
            addNew = QRadioButton("Specify a one-time use Plane...")
            addNew.setObjectName("new")
            addNew.toggled.connect(self.onToggle)
            self.selectLineLayout.addWidget(addNew, alignment = Qt.AlignmentFlag.AlignTop)
            self.selectLine.setLayout(self.selectLineLayout)
            selectLineArea.setWidget(self.selectLine)
            self.layout.addWidget(selectLineArea, alignment = Qt.AlignmentFlag.AlignTop)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "new":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
                QTimer.singleShot(0, self.shrink)
            except:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    QTimer.singleShot(0, self.shrink)
                except:
                    pass
            finally:
                self.input = InputPlane()
                self.input.submit.clicked.connect(self.sendNew)
                self.layout.addWidget(self.input)
                self.nums.emit(["Deselect"])
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            finally:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                except:
                    pass
                finally:
                    self.nums.emit([rb.objectName()])
                    self.submit = QPushButton("Submit")
                    self.submit.clicked.connect(self.sendExisting)
                    self.layout.addWidget(self.submit)
                    QTimer.singleShot(0, self.shrink)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendExisting(self):
        self.nums.emit(["Existing Plane"])
        self.close()

    def sendNew(self):
        a = num(self.input.inputA.text())
        b = num(self.input.inputB.text())
        c = num(self.input.inputC.text())
        d = num(self.input.inputD.text())
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
        self.nums.emit(["Close"])
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

class ShearWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj, linesPlanes):
        super().__init__()
        self.setWindowTitle("Shear")
        self.setMaximumHeight(480)
        self.layout = QVBoxLayout()
        self.activeObj = activeObj
        selectLineArea = QScrollArea()
        selectLineArea.setWidgetResizable(True)
        selectLineArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.selectLine = QWidget()
        self.selectLineLayout = QVBoxLayout()

        if self.activeObj:
            header = QWidget()
            headerLayout = QHBoxLayout()
            headerLayout.addWidget(QLabel("Enter the shear factor, k:"))
            self.inputK = QLineEdit()
            self.inputK.setFixedWidth(50)
            headerLayout.addWidget(self.inputK)
            header.setLayout(headerLayout)

            footer = QWidget()
            footerLayout = QHBoxLayout()
            footerLayout.addWidget(QLabel("Enter the shear direction vector:"))
            self.inputC1 = QLineEdit()
            self.inputC2 = QLineEdit()
            self.inputC3 = QLineEdit()
            self.inputC1.setFixedWidth(50)
            self.inputC2.setFixedWidth(50)
            self.inputC3.setFixedWidth(50)
            footerLayout.addWidget(self.inputC1)
            footerLayout.addWidget(QLabel("<b>i</b> +"))
            footerLayout.addWidget(self.inputC2)
            footerLayout.addWidget(QLabel("<b>j</b> +"))
            footerLayout.addWidget(self.inputC3)
            footerLayout.addWidget(QLabel("<b>k</b>"))
            footer.setLayout(footerLayout)

            self.layout.addWidget(header)
            self.layout.addWidget(footer)
            self.layout.addWidget(QLabel("Select an existing line as the invariant line, or specify a one-time use line:"))
            for obj in linesPlanes:
                if "Line" in obj.name:
                    option = QRadioButton(obj.name)
                    option.setObjectName(obj.name)
                    option.toggled.connect(self.onToggle)
                    self.selectLineLayout.addWidget(option, alignment = Qt.AlignmentFlag.AlignTop)
            
            addNew = QRadioButton("Specify a one-time use Line...")
            addNew.setObjectName("new")
            addNew.toggled.connect(self.onToggle)
            self.selectLineLayout.addWidget(addNew, alignment = Qt.AlignmentFlag.AlignTop)
            self.selectLine.setLayout(self.selectLineLayout)
            selectLineArea.setWidget(self.selectLine)
            self.layout.addWidget(selectLineArea, alignment = Qt.AlignmentFlag.AlignTop)

            self.layout.setStretch(3, 100)

        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "new":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
                QTimer.singleShot(0, self.shrink)
            except:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    QTimer.singleShot(0, self.shrink)
                except:
                    pass
            finally:
                self.input = InputLine()
                self.input.submit.clicked.connect(self.sendNew)
                self.layout.addWidget(self.input)
                self.nums.emit(["Deselect"])
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            finally:
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                except:
                    pass
                finally:
                    self.nums.emit([rb.objectName()])
                    self.submit = QPushButton("Submit")
                    self.submit.clicked.connect(self.sendExisting)
                    self.layout.addWidget(self.submit)
                    QTimer.singleShot(0, self.shrink)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendExisting(self):
        c1 = num(self.inputC1.text())
        c2 = num(self.inputC2.text())
        c3 = num(self.inputC3.text())
        k = num(self.inputK.text())
        if c1 == None or c2 == None or c3 == None or k == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif k % 360 == 0:
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit(["Existing Line", c1, c2, c3, k])
            self.close()

    def sendNew(self):
        a1 = num(self.input.inputA1.text())
        a2 = num(self.input.inputA2.text())
        a3 = num(self.input.inputA3.text())
        d1 = num(self.input.inputD1.text())
        d2 = num(self.input.inputD2.text())
        d3 = num(self.input.inputD3.text())
        c1 = num(self.inputC1.text())
        c2 = num(self.inputC2.text())
        c3 = num(self.inputC3.text())
        k = num(self.inputK.text())
        if a1 == None or a2 == None or a3 == None or d1 == None or d2 == None or d3 == None or c1 == None or c2 == None or c3 == None or k == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        elif (d1 == 0 and d2 == 0 and d3 == 0) or (c1 == 0 and c2 == 0 and c3 == 0):
            self.error = ErrorWindow(2, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([a1, a2, a3, d1, d2, d3, c1, c2, c3, k])
            self.close()
    
    def closeEvent(self, event):
        self.nums.emit(["Close"])
        event.accept()

class CustomMatrixWindow(QWidget):
    nums = pyqtSignal(list)

    def __init__(self, activeObj):
        super().__init__()
        self.setWindowTitle("Apply Custom Matrix")
        self.activeObj = activeObj
        self.layout = QGridLayout()

        if self.activeObj:

            self.inputC01 = QLineEdit("1")
            self.inputC01.setFixedWidth(50)
            self.inputC02 = QLineEdit("0")
            self.inputC02.setFixedWidth(50)
            self.inputC03 = QLineEdit("0")
            self.inputC03.setFixedWidth(50)
            self.inputC04 = QLineEdit("0")
            self.inputC04.setFixedWidth(50)
            self.inputC05 = QLineEdit("0")
            self.inputC05.setFixedWidth(50)
            self.inputC06 = QLineEdit("1")
            self.inputC06.setFixedWidth(50)
            self.inputC07 = QLineEdit("0")
            self.inputC07.setFixedWidth(50)
            self.inputC08 = QLineEdit("0")
            self.inputC08.setFixedWidth(50)
            self.inputC09 = QLineEdit("0")
            self.inputC09.setFixedWidth(50)
            self.inputC10 = QLineEdit("0")
            self.inputC10.setFixedWidth(50)
            self.inputC11 = QLineEdit("1")
            self.inputC11.setFixedWidth(50)
            self.inputC12 = QLineEdit("0")
            self.inputC12.setFixedWidth(50)
            self.inputC13 = QLineEdit("0")
            self.inputC13.setFixedWidth(50)
            self.inputC14 = QLineEdit("0")
            self.inputC14.setFixedWidth(50)
            self.inputC15 = QLineEdit("0")
            self.inputC15.setFixedWidth(50)
            self.inputC16 = QLineEdit("1")
            self.inputC16.setFixedWidth(50)
            self.inputC13.setDisabled(True)
            self.inputC14.setDisabled(True)
            self.inputC15.setDisabled(True)
            self.inputC16.setDisabled(True)
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)

            self.layout.addWidget(QLabel("Enter a 4x4 affine transformation matrix."), 0, 0, 1, 4)
            self.layout.addWidget(self.inputC01, 1, 0)
            self.layout.addWidget(self.inputC02, 1, 1)
            self.layout.addWidget(self.inputC03, 1, 2)
            self.layout.addWidget(self.inputC04, 1, 3)
            self.layout.addWidget(self.inputC05, 2, 0)
            self.layout.addWidget(self.inputC06, 2, 1)
            self.layout.addWidget(self.inputC07, 2, 2)
            self.layout.addWidget(self.inputC08, 2, 3)
            self.layout.addWidget(self.inputC09, 3, 0)
            self.layout.addWidget(self.inputC10, 3, 1)
            self.layout.addWidget(self.inputC11, 3, 2)
            self.layout.addWidget(self.inputC12, 3, 3)
            self.layout.addWidget(self.inputC13, 4, 0)
            self.layout.addWidget(self.inputC14, 4, 1)
            self.layout.addWidget(self.inputC15, 4, 2)
            self.layout.addWidget(self.inputC16, 4, 3)
            self.layout.addWidget(self.submit, 5, 0, 1, 4)
        
        else:
            self.layout.addWidget(QLabel("Cannot transform when no object is selected"))
        
        self.setLayout(self.layout)

    def send(self):
        c01 = num(self.inputC01.text())
        c02 = num(self.inputC02.text())
        c03 = num(self.inputC03.text())
        c04 = num(self.inputC04.text())
        c05 = num(self.inputC05.text())
        c06 = num(self.inputC06.text())
        c07 = num(self.inputC07.text())
        c08 = num(self.inputC08.text())
        c09 = num(self.inputC09.text())
        c10 = num(self.inputC10.text())
        c11 = num(self.inputC11.text())
        c12 = num(self.inputC12.text())
        c13 = num(self.inputC13.text())
        c14 = num(self.inputC14.text())
        c15 = num(self.inputC15.text())
        c16 = num(self.inputC16.text())
        if c01 == None or c02 == None or c03 == None or c04 == None or c05 == None or c06 == None or c07 == None or c08 == None or c09 == None or c10 == None or c11 == None or c12 == None or c13 == None or c14 == None or c15 == None or c16 == None:
            self.error = ErrorWindow(1, self)
            self.nums.emit([self.error])
        else:
            self.nums.emit([[c01, c02, c03, c04], [c05, c06, c07, c08], [c09, c10, c11, c12], [c13, c14, c15, c16]])
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

    def __init__(self, solids):
        super().__init__()
        self.setWindowTitle("Add Solid")

        self.item = None
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Select a solid to add, or create a new one:"), 0, 0, 1, 2)

        selectShapeArea = QScrollArea()
        selectShapeArea.setWidgetResizable(True)
        selectShapeArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectShapeArea.setFixedHeight(100)
        selectShapeLayout = QVBoxLayout()
        selectShapeLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)

        self.buttons = []

        for solid in solids:
            button = QRadioButton(solid["name"])
            button.type = solid["name"]
            button.toggled.connect(self.onToggle)
            selectShapeLayout.addWidget(button)
            self.buttons.append(button)
        
        addCustomSolidButton = QRadioButton("Add new Solid...")
        addCustomSolidButton.type = "Custom!"
        addCustomSolidButton.toggled.connect(self.onToggle)
        selectShapeLayout.addWidget(addCustomSolidButton)
        self.buttons.append(addCustomSolidButton)

        selectShape = QWidget()
        selectShape.setLayout(selectShapeLayout)
        selectShapeArea.setWidget(selectShape)
        self.layout.addWidget(selectShapeArea, 1, 0, 1, 2)
        
        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.isChecked():
            self.item = self.buttons[self.buttons.index(rb)].type
            if rb.type != "Custom!":
                try:
                    self.layout.removeWidget(self.lab)
                except:
                    pass
                self.lab = QLabel("You can specify the size and offset. Default is size 1 with no offset.")
                try:
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    self.layout.removeWidget(self.delLater)
                    self.delLater.deleteLater()
                except:
                    pass
                try:
                    while self.footerLayout.count():
                        self.footerLayout.removeWidget(self.footerLayout.itemAt(0).widget())
                except:
                    pass
                self.submit = QPushButton("Submit")
                self.submit.clicked.connect(self.send)
                self.delLater = QPushButton("Delete")
                self.delLater.clicked.connect(self.delete)
                self.layout.addWidget(self.lab, 2, 0, 1, 2)

                self.inputSize = QLineEdit("1")
                self.inputC1 = QLineEdit("0")
                self.inputC2 = QLineEdit("0")
                self.inputC3 = QLineEdit("0")
                self.inputSize.setFixedWidth(50)
                self.inputC1.setFixedWidth(50)
                self.inputC2.setFixedWidth(50)
                self.inputC3.setFixedWidth(50)

                self.footer = QWidget()
                self.footerLayout = QHBoxLayout()
                self.footerLayout.addWidget(QLabel("Size:"))
                self.footerLayout.addWidget(self.inputSize)
                self.footerLayout.addWidget(QLabel("Offset: ("))
                self.footerLayout.addWidget(self.inputC1)
                self.footerLayout.addWidget(self.inputC2)
                self.footerLayout.addWidget(self.inputC3)
                self.footerLayout.addWidget(QLabel(")"))
                self.footer.setLayout(self.footerLayout)
                self.layout.addWidget(self.footer, 3, 0, 1, 2)
                self.layout.addWidget(self.submit, 4, 0)
                self.layout.addWidget(self.delLater, 4, 1)
            else:
                try:
                    self.layout.removeWidget(self.lab)
                    self.lab.deleteLater()
                    self.layout.removeWidget(self.footer)
                    self.footer.deleteLater()
                    self.layout.removeWidget(self.submit)
                    self.submit.deleteLater()
                    self.layout.removeWidget(self.delLater)
                    self.delLater.deleteLater()
                except:
                    pass
                self.submit = QPushButton("Submit")
                self.submit.clicked.connect(self.send)
                self.layout.addWidget(self.submit, 2, 0, 1, 2)
                QTimer.singleShot(0, self.shrink)

        else:
            self.item = None
            self.layout.removeWidget(self.submit)
            self.submit.deleteLater()
            QTimer.singleShot(0, self.shrink)
    
    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def send(self):
        if self.item == "Custom!":
            self.params.emit(["Custom!"])
            self.close()
            return
        size = num(self.inputSize.text())
        c1 = num(self.inputC1.text())
        c2 = num(self.inputC2.text())
        c3 = num(self.inputC3.text())
        if not self.item:
            self.error = ErrorWindow(0, self)
            self.error.show()
        elif size == None or c1 == None or c2 == None or c3 == None:
            self.error = ErrorWindow(1, self)
            self.error.show()
        else:
            self.params.emit([self.item, size, c1, c2, c3])
        self.close()
    
    def delete(self):
        self.params.emit(["DeleteSolid!", self.item])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class CustomPolygonWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self, polygons):
        super().__init__()
        self.setWindowTitle("Custom Polygon")

        selectPolygonArea = QScrollArea()
        selectPolygonArea.setWidgetResizable(True)
        selectPolygonArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        selectPolygonArea.setFixedHeight(100)
        selectPolygonLayout = QVBoxLayout()

        self.layout = QGridLayout()
        self.buttons = []

        self.layout.addWidget(QLabel("Select a polygon, or create a new one:"), 0, 0, 1, 6)

        for poly in polygons:
            button = QRadioButton(poly["name"])
            button.type = [Shapes.Polygon(poly["name"], poly["vertices"], poly["edges"], poly["normal"]), None, False]
            button.toggled.connect(self.onToggle)
            selectPolygonLayout.addWidget(button)
            self.buttons.append(button)
        
        addNewPolygonButton = QRadioButton("Add new Polygon...")
        addNewPolygonButton.toggled.connect(self.onToggleNew)
        self.buttons.append(addNewPolygonButton)
        selectPolygonLayout.addWidget(addNewPolygonButton)
        
        selectPolygon = QWidget()
        selectPolygon.setLayout(selectPolygonLayout)
        selectPolygonArea.setWidget(selectPolygon)
        self.layout.addWidget(selectPolygonArea, 1, 0, 1, 6)

        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        try:
            self.layout.removeWidget(self.newPolygon)
            self.newPolygon.deleteLater()
        except:
            pass
        try:
            self.layout.removeWidget(self.submit)
            self.submit.deleteLater()
            self.layout.removeWidget(self.delLater)
            self.delLater.deleteLater()
        except:
            pass
        if rb.isChecked():
            self.polygon = self.buttons[self.buttons.index(rb)].type
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)
            self.delLater = QPushButton("Delete")
            self.delLater.clicked.connect(self.delete)
            self.layout.addWidget(self.submit, 2, 0, 1, 3)
            self.layout.addWidget(self.delLater, 2, 3, 1, 3)
        else:
            self.polygon = None
        self.params.emit([self.polygon])
    
    def onToggleNew(self):
        rb = self.sender()
        try:
            self.layout.removeWidget(self.newPolygon)
            self.newPolygon.deleteLater()
        except:
            pass
        try:
            self.layout.removeWidget(self.submit)
            self.submit.deleteLater()
        except:
            pass
        if rb.isChecked():
            self.newPolygon = QWidget()
            self.newPolygonLayout = QGridLayout()
            self.newPolygonLayout.addWidget(QLabel("Upload a CSV of vertices which defines a polygon.\n" \
                                                   "Each line should either have exactly 2 numbers, or\n" \
                                                   "exactly 3 numbers. In the latter case, the best fit\n" \
                                                   "polygon will be calculated."), 0, 0, 1, 4)
            uploadButton = QPushButton("Upload")
            uploadButton.clicked.connect(self.loadCSV)
            self.newPolygonLayout.addWidget(uploadButton, 0, 4, 1, 2)
            self.newPolygon.setLayout(self.newPolygonLayout)
            self.layout.addWidget(self.newPolygon, 2, 0, 1, 6)

    def loadCSV(self):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )[0]

        if not file_path:
            return
        
        self.destroy = True
        
        try:
            self.newPolygonLayout.removeWidget(self.response)
        except:
            pass
        mat = []

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                mat.append(row)

        try:
            self.layout.removeWidget(self.submit)
            self.submit.deleteLater()
        except:
            pass
        try:
            self.newPolygonLayout.removeWidget(self.lab)
            self.lab.deleteLater()
        except:
            pass
        try:
            self.newPolygonLayout.removeWidget(self.response)
            self.response.deleteLater()
        except:
            pass
        try:
            self.newPolygonLayout.removeWidget(self.eqn)
            self.eqn.deleteLater()
        except:
            pass
        try:
            self.newPolygonLayout.removeWidget(self.name)
            self.name.deleteLater()
        except:
            pass
        
        self.result = Shapes.tlsplane(mat)
        if isinstance(self.result[0], Shapes.Polygon):
            self.lab = QLabel("Name your polygon:")
            self.name = QLineEdit()
            if len(self.result) > 1:
                self.response = QLabel("3D points parsed successfully!")
                self.is3D = True
                self.polygon = [self.result[0], self.result[1:-1], -1]
                self.eqn = QLabel(f"Equation of plane: {round(self.result[0].normal[0], 3)}x + {round(self.result[0].normal[1], 3)}y + {round(self.result[0].normal[2], 3)}z = {round(self.result[1], 3)}")
                self.newPolygonLayout.addWidget(self.response, 2, 0, 1, 6)
                self.newPolygonLayout.addWidget(self.eqn, 3, 0, 1, 6)
                self.newPolygonLayout.addWidget(self.lab, 4, 0, 1, 2)
                self.newPolygonLayout.addWidget(self.name, 4, 2, 1, 4)
            else:
                self.response = QLabel("2D points parsed successfully!")
                self.is3D = False
                self.polygon = [self.result[0], [0, 0, 1], -1]
                self.newPolygonLayout.addWidget(self.response, 2, 0, 1, 6)
                self.newPolygonLayout.addWidget(self.lab, 3, 0, 1, 2)
                self.newPolygonLayout.addWidget(self.name, 3, 2, 1, 4)
        else:
            self.response = QLabel(self.result)
            self.is3D = False
            self.newPolygonLayout.addWidget(self.response, 2, 0, 1, 6)
        
        if not self.is3D:
            try:
                self.newPolygonLayout.removeWidget(self.eqn)
                self.eqn.deleteLater()
            except:
                pass

        if not isinstance(self.result, str):
            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)
            self.layout.addWidget(self.submit, 3, 0, 1, 6)
    
    def send(self):
        em = True
        try:
            name = self.name.text()
            self.polygon[0].name = name
        except:
            name = self.polygon[0].name
        if self.polygon[2] in (-1, False):
            if not name or not name.isalnum():
                em = False
                self.error = ErrorWindow(4, self)
                self.params.emit([self.error])
            elif self.polygon[2] == False:
                self.polygon[2] = True
        if em:
            self.params.emit([self.polygon])
        self.destroy = True
        self.close()
    
    def delete(self):
        self.params.emit(["DeletePolygon!", self.polygon[0].name])
        self.destroy = False
        self.close()
    
    def closeEvent(self, event):
        if self.destroy:
            self.params.emit(["Close!"])
        event.accept()

class CustomSolidWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self, norm):
        super().__init__()
        self.setWindowTitle("Custom Solid")
        self.layout = QGridLayout()
        self.norm = norm

        self.destroy = True
            
        addNewPyramid = QRadioButton("Pyramid")
        addNewPyramid.setObjectName("newPyramid")
        addNewPyramid.toggled.connect(self.onToggle)
        addNewPrism = QRadioButton("Prism")
        addNewPrism.setObjectName("newPrism")
        addNewPrism.toggled.connect(self.onToggle)

        self.layout.addWidget(QLabel("Make a prism or pyramid using your base polygon:"), 0, 0, 1, 2)
        
        self.layout.addWidget(addNewPyramid, 1, 0)
        self.layout.addWidget(addNewPrism, 1, 1)

        self.layout.addWidget(QLabel("Name your solid:"), 2, 0)
        self.name = QLineEdit()
        self.layout.addWidget(self.name, 2, 1)

        self.setLayout(self.layout)
    
    def onToggle(self):
        rb = self.sender()
        if rb.objectName() == "newPyramid":
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            try:
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
            except:
                pass
            finally:
                QTimer.singleShot(0, self.shrink)
                self.input = QWidget()
                self.inputLayout = QGridLayout()
                self.inputLayout.addWidget(QLabel("Enter the coordinates of the apex:"), 0, 0, 1, 4)
                self.inputC1 = QLineEdit()
                self.inputC2 = QLineEdit()
                self.inputC3 = QLineEdit()
                self.inputC1.setFixedWidth(50)
                self.inputC2.setFixedWidth(50)
                self.inputC3.setFixedWidth(50)
                self.submit = QPushButton("Submit")
                self.submit.clicked.connect(self.sendPyramid)
                self.inputLayout.addWidget(self.inputC1, 1, 0)
                self.inputLayout.addWidget(self.inputC2, 1, 1)
                self.inputLayout.addWidget(self.inputC3, 1, 2)
                self.inputLayout.addWidget(self.submit, 1, 3)
                self.input.setLayout(self.inputLayout)
                self.layout.addWidget(self.input, 3, 0, 1, 2)
        else:
            try:
                self.layout.removeWidget(self.input)
                self.input.deleteLater()
            except:
                pass
            try:
                self.layout.removeWidget(self.submit)
                self.submit.deleteLater()
            except:
                pass
            finally:
                QTimer.singleShot(0, self.shrink)
                self.input = QWidget()
                self.inputLayout = QHBoxLayout()
                self.inputLayout.addWidget(QLabel("Enter the height of the prism:"))
                self.inputH = QLineEdit()
                self.inputH.setFixedWidth(50)
                self.submit = QPushButton("Submit")
                self.submit.clicked.connect(self.sendPrism)
                self.inputLayout.addWidget(self.inputH)
                self.inputLayout.addWidget(self.submit)
                self.input.setLayout(self.inputLayout)
                self.layout.addWidget(self.input, 3, 0, 1, 2)

    def shrink(self):
        self.layout.activate()
        self.adjustSize()

    def sendPyramid(self):
        self.destroy = False
        c1 = num(self.inputC1.text())
        c2 = num(self.inputC2.text())
        c3 = num(self.inputC3.text())
        name = self.name.text()
        if c1 == None or c2 == None or c3 == None:
            self.error = ErrorWindow(1, self)
            self.params.emit([self.error])
        elif not name or not name.isalnum():
            self.error = ErrorWindow(4, self)
            self.params.emit([self.error])
        else:
            self.params.emit(["Pyramid!", name, c1, c2, c3])
            self.close()
    
    def sendPrism(self):
        self.destroy = False
        h = num(self.inputH.text())
        name = self.name.text()
        if not h:
            self.error = ErrorWindow(1, self)
            self.params.emit([self.error])
        elif not name or not name.isalnum():
            self.error = ErrorWindow(4, self)
            self.params.emit([self.error])
        else:
            self.params.emit(["Prism!", name, h])
            self.close()
    
    def closeEvent(self, event):
        if self.destroy:
            self.params.emit(["Close!"])
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
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setMinimumWidth(210)
        area.setFixedHeight(100)
        area.setWidget(label)
        self.layout.addWidget(area)
        self.setLayout(self.layout)