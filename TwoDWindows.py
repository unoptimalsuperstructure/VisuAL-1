from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from MatrixPrinter import toString, concat

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

class ConvolutionWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self, activeLayers):
        super().__init__()
        self.setWindowTitle("Apply Convolution")
        self.layout = QGridLayout()
        convList = QWidget()
        convListLayout = QVBoxLayout()
        self.submit = QWidget()
        self.valuesLayout = QGridLayout()

        if activeLayers:
            self.layout.addWidget(QLabel("Which convolution would you like to apply to the selected images?"), 0, 0, 1, 2)
            box = QRadioButton("Box Blur")
            box.toggled.connect(self.boxBlur)
            convListLayout.addWidget(box)
            median = QRadioButton("Median Blur*")
            median.toggled.connect(self.medianBlur)
            convListLayout.addWidget(median)
            gaussian = QRadioButton("Gaussian Blur")
            gaussian.toggled.connect(self.gaussianBlur)
            convListLayout.addWidget(gaussian)
            sharpen = QRadioButton("Sharpen")
            sharpen.toggled.connect(self.sharpen)
            convListLayout.addWidget(sharpen)
            sobel = QRadioButton("Sobel Edge Detection")
            sobel.toggled.connect(self.sobel)
            convListLayout.addWidget(sobel)

            convList.setLayout(convListLayout)

            self.layout.addWidget(convList, 1, 0, 1, 1)
            
        else:
            self.layout.addWidget(QLabel("Cannot apply convolution when no images are selected"))
        
        self.setLayout(self.layout)

    def boxBlur(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()
        
        self.radius = QSpinBox()
        self.radius.setRange(1, 5)
        self.valuesLayout.addWidget(QLabel("Kernel radius:"), 0, 0)
        self.valuesLayout.addWidget(self.radius, 0, 1)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.boxSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def medianBlur(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()
        
        self.radius = QSpinBox()
        self.radius.setRange(1, 5)
        self.valuesLayout.addWidget(QLabel("Kernel radius:"), 0, 0)
        self.valuesLayout.addWidget(self.radius, 0, 1)
        self.valuesLayout.addWidget(QLabel("*Note: Non-linear convolution"), 1, 0, 1, 2)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.medianSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)
    
    def gaussianBlur(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.radius = QSpinBox()
        self.radius.setRange(1, 5)
        self.sd = QLineEdit()
        self.valuesLayout.addWidget(QLabel("Kernel radius:"), 0, 0)
        self.valuesLayout.addWidget(self.radius, 0, 1)
        self.valuesLayout.addWidget(QLabel("Standard deviation:"), 1, 0)
        self.valuesLayout.addWidget(self.sd, 1, 1)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.gaussianSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def sharpen(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.v = QSlider(Qt.Orientation.Horizontal)
        self.v.label = QLabel("20")
        self.v.setRange(0, 100)
        self.v.setValue(20)
        self.valuesLayout.addWidget(QLabel("Intensity"), 0, 0)
        self.valuesLayout.addWidget(self.v, 0, 1)
        self.valuesLayout.addWidget(self.v.label, 0, 2)
        
        self.v.valueChanged.connect(lambda val: self.v.label.setText(str(val)))

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.sharpenSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def sobel(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.sobelSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def boxSend(self):
        rad = self.radius.value()
        self.params.emit(["Box", rad])
        self.close()

    def medianSend(self):
        rad = self.radius.value()
        self.params.emit(["Median", rad])
        self.close()

    def gaussianSend(self):
        rad = self.radius.value()
        sd = num(self.sd.text())
        if sd == None or sd <= 0:
            self.error = ErrorWindow(1, self)
            self.params.emit([self.error])
        else:
            self.params.emit(["Gaussian", rad, sd])
        self.close()
    
    def sharpenSend(self):
        v = self.v.value() / 100
        self.params.emit(["Sharpen", v])
        self.close()

    def sobelSend(self):
        self.params.emit(["Sobel"])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class ColourWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self, activeLayers):
        super().__init__()
        self.setWindowTitle("Apply Colour Filter")
        self.layout = QGridLayout()
        filterList = QWidget()
        filterListLayout = QVBoxLayout()
        self.submit = QWidget()
        self.valuesLayout = QGridLayout()

        if activeLayers:
            self.layout.addWidget(QLabel("Which colour filter would you like to apply to the selected images?"), 0, 0, 1, 2)
            
            colourAdjust = QRadioButton("Colour Adjustment")
            colourAdjust.toggled.connect(self.colourAdjustment)
            filterListLayout.addWidget(colourAdjust)
            sepia = QRadioButton("Sepia")
            sepia.toggled.connect(self.sepiaFilter)
            filterListLayout.addWidget(sepia)

            filterList.setLayout(filterListLayout)

            self.layout.addWidget(filterList, 1, 0, 1, 1)
            
        else:
            self.layout.addWidget(QLabel("Cannot apply filter when no images are selected"))
        
        self.setLayout(self.layout)
    
    def colourAdjustment(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.relR = QSlider(Qt.Orientation.Horizontal)
        self.relR.name = "relR"
        self.relG = QSlider(Qt.Orientation.Horizontal)
        self.relG.name = "relG"
        self.relB = QSlider(Qt.Orientation.Horizontal)
        self.relB.name = "relB"
        self.absR = QSlider(Qt.Orientation.Horizontal)
        self.absR.name = "absR"
        self.absG = QSlider(Qt.Orientation.Horizontal)
        self.absG.name = "absG"
        self.absB = QSlider(Qt.Orientation.Horizontal)
        self.absB.name = "absB"

        relSliders = [self.relR, self.relG, self.relB]
        absSliders = [self.absR, self.absG, self.absB]

        i = 1

        for slider in relSliders:
            slider.label = QLabel("100%")
            slider.setRange(0, 200)
            slider.setValue(100)
            self.valuesLayout.addWidget(QLabel(slider.name), i, 0)
            self.valuesLayout.addWidget(slider, i, 1)
            self.valuesLayout.addWidget(slider.label, i, 2)
            i += 1

        for slider in absSliders:
            slider.label = QLabel("0")
            slider.setRange(-255, 255)
            self.valuesLayout.addWidget(QLabel(slider.name), i, 0)
            self.valuesLayout.addWidget(slider, i, 1)
            self.valuesLayout.addWidget(slider.label, i, 2)
            i += 1
        
        self.relR.valueChanged.connect(lambda val: self.relR.label.setText(str(val) + "%"))
        self.relG.valueChanged.connect(lambda val: self.relG.label.setText(str(val) + "%"))
        self.relB.valueChanged.connect(lambda val: self.relB.label.setText(str(val) + "%"))

        self.absR.valueChanged.connect(lambda val: self.absR.label.setText(("+" if val >= 0 else "") + str(val)))
        self.absG.valueChanged.connect(lambda val: self.absG.label.setText(("+" if val >= 0 else "") + str(val)))
        self.absB.valueChanged.connect(lambda val: self.absB.label.setText(("+" if val >= 0 else "") + str(val)))

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.colourSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def sepiaFilter(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.sepiaSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)

    def colourSend(self):
        relR = self.relR.value() / 100
        relG = self.relG.value() / 100
        relB = self.relB.value() / 100
        absR = self.absR.value()
        absG = self.absG.value()
        absB = self.absB.value()
        self.params.emit(["Colour Filter", relR, relG, relB, 1, absR, absG, absB, 1])
        self.close()
    
    def sepiaSend(self):
        self.params.emit(["Sepia"])
        self.close()
    
    def closeEvent(self, event):
        event.accept()