from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QPainter, QFont
from MatrixPrinter import toString, displayAsMatrix
from NumStabilityWindows import ErrorWindow as NSEW
import csv, cv2, qimage2ndarray, math, numpy as np

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

class CropWindow(QWidget):
    params = pyqtSignal(list)

    def __init__(self, activeLayers):
        super().__init__()
        self.setWindowTitle("Crop")
        self.layout = QGridLayout()
        self.submit = QWidget()

        if activeLayers and len(activeLayers) == 1:
            self.image = activeLayers[0].img
            self.oh, self.ow = self.image.stack[-1][0].shape[:2]
            self.ch, self.cw = int(min(300, 400 * self.oh/self.ow)), int(min(400, 300 * self.ow/self.oh))
            self.preview = cv2.resize(self.image.stack[-1][0], (self.cw, self.ch))
            self.layout.addWidget(QLabel("Specify the crop dimensions"), 0, 0, 1, 4)
            self.pixmap = QPixmap.fromImage(qimage2ndarray.array2qimage(cv2.cvtColor(self.preview, self.image.const)))
            self.imagePreview = QLabel()
            self.imagePreview.setPixmap(self.pixmap)
            
            self.layout.addWidget(QLabel("Top"), 2, 0)
            self.layout.addWidget(QLabel("Bottom"), 2, 1)
            self.layout.addWidget(QLabel("Left"), 2, 2)
            self.layout.addWidget(QLabel("Right"), 2, 3)
            
            self.layout.addWidget(self.imagePreview, 1, 0, 1, 4)
            self.up = QSpinBox()
            self.up.setRange(0, self.image.stack[-1][0].shape[0])
            self.up.setValue(0)
            self.up.valueChanged.connect(self.drawBox)
            self.layout.addWidget(self.up, 3, 0)
            self.down = QSpinBox()
            self.down.setRange(0, self.image.stack[-1][0].shape[0])
            self.down.setValue(self.image.stack[-1][0].shape[0])
            self.down.valueChanged.connect(self.drawBox)
            self.layout.addWidget(self.down, 3, 1)
            self.left = QSpinBox()
            self.left.setRange(0, self.image.stack[-1][0].shape[1])
            self.left.setValue(0)
            self.left.valueChanged.connect(self.drawBox)
            self.layout.addWidget(self.left, 3, 2)
            self.right = QSpinBox()
            self.right.setRange(0, self.image.stack[-1][0].shape[1])
            self.right.setValue(self.image.stack[-1][0].shape[1])
            self.right.valueChanged.connect(self.drawBox)
            self.layout.addWidget(self.right, 3, 3)

            self.submit = QPushButton("Submit")
            self.submit.clicked.connect(self.send)
            self.layout.addWidget(self.submit, 4, 0, 1, 4)
        
        else:
            self.layout.addWidget(QLabel("Can only crop when exactly 1 image is selected"))
        
        self.setLayout(self.layout)
    
    def drawBox(self):
        self.pixmap = QPixmap.fromImage(qimage2ndarray.array2qimage(cv2.cvtColor(self.preview, self.image.const)))
        painter = QPainter(self.pixmap)
        painter.drawRect(int(self.left.value() / self.ow * self.cw),
                         int(self.up.value() / self.oh * self.ch),
                         int((self.right.value() - self.left.value()) / self.ow * self.cw),
                         int((self.down.value() - self.up.value()) / self.oh * self.ch))
        painter.end()
        self.imagePreview.setPixmap(self.pixmap)
    
    def send(self):
        self.params.emit(["Crop", self.up.value(), self.down.value(), self.left.value(), self.right.value()])
        self.close()

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
            pixelate = QRadioButton("Pixelate*")
            pixelate.toggled.connect(self.pixelate)
            convListLayout.addWidget(pixelate)
            sharpen = QRadioButton("Sharpen")
            sharpen.toggled.connect(self.sharpen)
            convListLayout.addWidget(sharpen)
            sobel = QRadioButton("Sobel Edge Detection")
            sobel.toggled.connect(self.sobel)
            convListLayout.addWidget(sobel)
            custom = QRadioButton("Custom Convolution Kernel")
            custom.toggled.connect(self.custom)
            convListLayout.addWidget(custom)

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
    
    def pixelate(self):
        self.layout.removeWidget(self.submit)
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()
        
        self.v = QSpinBox()
        self.v.setRange(2, 10)
        self.valuesLayout.addWidget(QLabel("Pixelation radius:"), 0, 0)
        self.valuesLayout.addWidget(self.v, 0, 1)
        self.valuesLayout.addWidget(QLabel("*Note: Non-linear convolution"), 1, 0, 1, 2)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.pixelateSend)
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
    
    def custom(self):
        self.layout.removeWidget(self.submit)
        self.valid = False
        while self.valuesLayout.count() > 0:
            widget = self.valuesLayout.itemAt(0).widget()
            self.valuesLayout.removeWidget(widget)
            widget.deleteLater()

        self.valuesLayout.addWidget(QLabel("Upload a convolution kernel matrix as a CSV.\n" \
                                           "Note: The matrix must have odd dimensions."), 0, 0, 1, 2)

        self.upload = QPushButton("Upload CSV")
        self.upload.clicked.connect(self.loadCSV)
        self.valuesLayout.addWidget(self.upload, 0, 2)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.customSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)
    
    def loadCSV(self):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )[0]

        if not file_path:
            return

        try:
            self.valuesLayout.removeWidget(self.displayMatrix)
            self.displayMatrix.deleteLater()
            self.valuesLayout.removeWidget(self.n)
            self.n.deleteLater()
            self.valuesLayout.removeWidget(self.label1)
            self.label1.deleteLater()
            self.valuesLayout.removeWidget(self.label2)
            self.label2.deleteLater()
        except:
            pass

        mat = []
        self.valid = True

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                try:
                    mat.append(list(map(lambda x: float(x), row)))
                except:
                    self.valid = False
                    self.error = NSEW(1, None)
                    self.error.show()
                    break
        
        try:
            self.matrix = np.array(mat)
            self.rank = np.linalg.matrix_rank(self.matrix)
        except:
            self.valid = False
            self.error = NSEW(2, None)
            self.error.show()
        
        r, c = np.shape(self.matrix)
        if r % 2 == 0 or c % 2 == 0:
            self.valid = False
            self.error = NSEW(99, None)
            self.error.show()
        
        if self.valid:
            disp = displayAsMatrix(toString(self.matrix, 3), False)
            self.displayMatrix = QLabel(disp)
            self.displayMatrix.setStyleSheet("""
            * {
                font-size: 12px;
                font-family: Cascadia Mono;
                text-align: center;
            }
            """)

            self.valuesLayout.addWidget(self.displayMatrix, 1, 0, 1, 3)

            self.n = QSpinBox()
            self.n.setRange(1, self.rank)
            self.n.setValue(self.rank)
            self.label1 = QLabel("Order of approximation:")
            self.label2 = QLabel("<i>Leave it as is for exact calculation</i>")
            self.valuesLayout.addWidget(self.label1, 2, 0, 1, 2)
            self.valuesLayout.addWidget(self.n, 2, 2)
            self.valuesLayout.addWidget(self.label2, 3, 0, 1, 3)

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
    
    def pixelateSend(self):
        v = self.v.value()
        self.params.emit(["Pixelate", v])
        self.close()
    
    def sharpenSend(self):
        v = self.v.value() / 100
        self.params.emit(["Sharpen", v])
        self.close()

    def sobelSend(self):
        self.params.emit(["Sobel"])
        self.close()
    
    def customSend(self):
        if self.valid:
            self.params.emit(["Custom", self.matrix, self.n.value()])
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
            grayscale = QRadioButton("Grayscale")
            grayscale.toggled.connect(self.grayscaleFilter)
            filterListLayout.addWidget(grayscale)
            sepia = QRadioButton("Sepia")
            sepia.toggled.connect(self.sepiaFilter)
            filterListLayout.addWidget(sepia)
            inversion = QRadioButton("Colour Inversion")
            inversion.toggled.connect(self.inversionFilter)
            filterListLayout.addWidget(inversion)

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

    def grayscaleFilter(self):
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
        self.submit.clicked.connect(self.grayscaleSend)
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
        
        self.v = QSlider(Qt.Orientation.Horizontal)
        self.v.label = QLabel("20")
        self.v.setRange(0, 100)
        self.v.setValue(20)
        self.valuesLayout.addWidget(QLabel("Intensity"), 0, 0)
        self.valuesLayout.addWidget(self.v, 0, 1)
        self.valuesLayout.addWidget(self.v.label, 0, 2)
        
        self.v.valueChanged.connect(lambda val: self.v.label.setText(str(val)))

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.sepiaSend)
        self.layout.addWidget(self.submit, 2, 0, 1, 2)

        values = QWidget()
        values.setLayout(self.valuesLayout)
        self.layout.addWidget(values, 1, 1, 1, 1)
    
    def inversionFilter(self):
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
        self.submit.clicked.connect(self.inversionSend)
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
        self.params.emit(["Colour Filter", relR, relG, relB, 1, absR, absG, absB, 0])
        self.close()
    
    def grayscaleSend(self):
        v = self.v.value() / 100
        self.params.emit(["Grayscale", v])
        self.close()

    def sepiaSend(self):
        v = self.v.value() / 100
        self.params.emit(["Sepia", v])
        self.close()
    
    def inversionSend(self):
        v = self.v.value() / 100
        self.params.emit(["Inversion", v])
        self.close()
    
    def closeEvent(self, event):
        event.accept()

class ViewStackWindow(QWidget):
    def __init__(self, activeLayers):
        super().__init__()
        self.setWindowTitle("Operation Stack")
        self.layout = QVBoxLayout()
        if activeLayers and len(activeLayers) == 1:
            image = activeLayers[0].img
            self.matrixStack = []
            tempStack = image.matrixStack.copy()
            tempStack.reverse()
            for entry in tempStack:
                if isinstance(entry[0], np.ndarray):
                    topString = entry[1] + " " * (30 + 4 * math.floor(math.log(abs(entry[0]).max(), 10)) - len(entry[1]))
                    for line in toString(entry[0], 3):
                        topString += "\n" + str(line).replace(",","").replace("'","")
                    self.matrixStack.append(topString)
                else:
                    self.matrixStack.append(entry[1] + "\nNon-linear filter/convolution")
            self.curMatrix = QLabel(self.matrixStack[0])
            self.curMatrix.setFont(QFont("Courier New"))

            self.page = 0
            self.last = len(self.matrixStack) - 1

            self.layout.addWidget(self.curMatrix)
            self.layout.addWidget(self.pageLoader())
        else:
            self.layout.addWidget(QLabel("Can only view operation stack of 1 image at a time"))
        self.setLayout(self.layout)
    
    def pageLoader(self):
        self.pageLayout = QHBoxLayout()
        prev = QPushButton("<--")
        prev.clicked.connect(self.prevPage)
        self.pageLayout.addWidget(prev)

        self.pageLabel = QLabel(f"Page {self.page + 1} of {self.last + 1}")
        self.pageLayout.addWidget(self.pageLabel)

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
            self.curMatrix.setText(self.matrixStack[self.page])
        except:
            pass
    
    def nextPage(self):
        if self.page < self.last:
            self.page += 1
        self.pageLabel.setText(f"Page {self.page + 1} of {self.last + 1}")
        try:
            self.curMatrix.setText(self.matrixStack[self.page])
        except:
            pass