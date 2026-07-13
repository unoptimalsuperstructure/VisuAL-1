import os, sys, subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import QEvent, Qt
from TwoDImages import TwoDViewer, TwoDSidePanel
from ThreeDGraphics import ThreeDViewer, ThreeDSidePanel
from NumStabilityAlgos import NumStabilityViewer, NumStabilitySidePanel
from MarkovChains import MarkovChainsViewer, MarkovChainsSidePanel, MarkovChainsTimePanel
from Images import Image
import Shapes, json, numpy as np
from PathFinder import resource_path
from Themes import LIGHT_THEME, DARK_THEME

f1 = open(str(resource_path("static/sizeconfig.txt")))
size = int(f1.readline())
f1.close()
f2 = open(str(resource_path("static/theme.txt")))
theme = int(f2.readline())
f2.close()

app = QApplication(sys.argv)

class HomeBar(QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.addWidget(QLabel("Home Bar"))

class OptionPanel(QVBoxLayout):
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.previewPanelLayout = mainWindow.previewPanelLayout
        self.Button1 = QPushButton("2D Image Processing")
        self.Button2 = QPushButton("3D Graphics Sandbox")
        self.Button3 = QPushButton("Numerical Stability")
        self.Button4 = QPushButton("Markov Chains")
        self.Button5 = QPushButton("Settings")
        self.Button1.setFixedWidth(150)
        self.Button2.setFixedWidth(150)
        self.Button3.setFixedWidth(150)
        self.Button4.setFixedWidth(150)
        self.Button5.setFixedWidth(150)
        self.Button1.clicked.connect(self.TwoDee)
        self.Button2.clicked.connect(self.ThreeDee)
        self.Button3.clicked.connect(self.NumStability)
        self.Button4.clicked.connect(self.MarkovChains)
        self.Button5.clicked.connect(self.Settings)
        self.addWidget(self.Button1)
        self.addWidget(self.Button2)
        self.addWidget(self.Button3)
        self.addWidget(self.Button4)
        self.addWidget(self.Button5)
        
        self.addWidget(QLabel("Hello!"))

        self.hover = False

        self.Button1.installEventFilter(self)
        self.Button2.installEventFilter(self)
        self.Button3.installEventFilter(self)
        self.Button4.installEventFilter(self)
        self.Button5.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if obj in [self.Button1, self.Button2, self.Button3, self.Button4, self.Button5]:
            width = int(self.mainWindow.previewPanel.width() * 0.75)
            height = int(self.mainWindow.previewPanel.height() * 0.75)
            if width > 4/3 * height:
                width = int(4/3 * height)
            else:
                height = int(3/4 * width)
            img = self.previewPanelLayout.previewImage
            label = self.previewPanelLayout.defaultLabel
            if not self.hover:
                item = {self.Button1: "2DImageProcessing", self.Button2: "3DGraphicsSandbox", self.Button3: "NumericalStability", self.Button4: "MarkovChains", self.Button5: "SystemSettings"}[obj]
                img.setPixmap(QPixmap(str(resource_path(f"static/{item}.png"))).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio))
                if event.type() == QEvent.Type.Enter:
                    img.show()
                    label.hide()
                    self.hover = True
            if event.type() == QEvent.Type.Leave:
                img.hide()
                label.show()
                self.hover = False
        
        return super().eventFilter(obj, event)
    
    def TwoDee(self):
        self.newWindow = TwoDMainWindow()
        self.newWindow.show()
        self.mainWindow.close()

    def ThreeDee(self):
        self.newWindow = ThreeDMainWindow([], [], [])
        self.newWindow.show()
        self.mainWindow.close()
    
    def NumStability(self):
        self.newWindow = NumStabilityMainWindow()
        self.newWindow.show()
        self.mainWindow.close()
    
    def MarkovChains(self):
        self.newWindow = MarkovChainsMainWindow()
        self.newWindow.show()
        self.mainWindow.close()
    
    def Settings(self):
        self.newWindow = SettingsWindow(self.mainWindow)
        self.newWindow.show()

class PreviewPanel(QVBoxLayout):
    def __init__(self, home):
        super().__init__()
        self.home = home
        self.previewImage = QLabel()
        self.previewImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previewImage.hide()
        self.defaultLabel = QLabel("Visu(AL)-1")
        self.defaultLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.previewImage)
        self.addWidget(self.defaultLabel)

class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        app.setStyleSheet(LIGHT_THEME if theme == 0 else DARK_THEME)

        self.setWindowTitle("Visu(AL)-1 v0.2.1a - Home")
        if size == 1:
            self.resize(800, 600 - 30)
        elif size == 2:
            self.resize(1024, 768 - 30)
        elif size == 3 or size == 4:
            self.resize(1280, 720 - 30)
        else:
            sys.exit()

        central = QWidget()
        self.setCentralWidget(central)

        mainLayout = QVBoxLayout()
        central.setLayout(mainLayout)

        homeBar = QWidget()
        homeBar.setLayout(HomeBar())
        homeBar.setStyleSheet("""
            * {
                background-color: blue;
                color: white;
            }
        """)

        self.previewPanel = QWidget()
        self.previewPanel.setStyleSheet("""
            * {
                font-size: 96px;
                font-family: Cascadia Mono;
                text-align: center;
            }
        """)
        self.previewPanelLayout = PreviewPanel(self.previewPanel)
        self.previewPanel.setLayout(self.previewPanelLayout)

        optionPanel = QWidget()
        self.optionPanelLayout = OptionPanel(self)
        optionPanel.setLayout(self.optionPanelLayout)

        homePanel = QWidget()
        self.homePanelLayout = QHBoxLayout()
        homePanel.setLayout(self.homePanelLayout)

        self.homePanelLayout.addWidget(optionPanel, stretch = 1)
        self.homePanelLayout.addWidget(self.previewPanel, stretch = 3)
        mainLayout.addWidget(homeBar, stretch = 1)
        mainLayout.addWidget(homePanel, stretch = 16)
    
    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        if w/h < 4/3:
            self.resize(max(720, int(h / 3 * 4)), max(540, h))
        if w < 720:
            self.resize(720, h)
        if h < 540:
            self.resize(w, 540)
        self.homePanelLayout.setStretch(0, 200)
        self.homePanelLayout.setStretch(1, w - 200)

class TwoDMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 v0.2.1a - 2D Image Processing")
        self.viewer = TwoDViewer([Image(resource_path("static/kagura.png"), size)], size)
        if size == 1:
            self.resize(800, 600 - 30)
            self.viewer.setFixedSize(560, 420)
        elif size == 2:
            self.resize(1024, 768 - 30)
            self.viewer.setFixedSize(720, 540)
        elif size == 3:
            self.resize(1280, 720 - 30)
            self.viewer.setFixedSize(960, 540)
        elif size == 4:
            self.resize(1920, 1080 - 30)
            self.viewer.setFixedSize(1600, 900)

        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QHBoxLayout()
        central.setLayout(self.mainLayout)

        sidePanel = QWidget()
        sidePanelLayout = TwoDSidePanel(self.viewer)
        transformationPanel = sidePanelLayout.transformationPanel
        self.imagePanel = sidePanelLayout.imagePanel
        sidePanelLayout.addLayout(transformationPanel, stretch = 1)
        sidePanelLayout.addLayout(self.imagePanel, stretch = 1)
        sidePanel.setLayout(sidePanelLayout)
        self.mainLayout.addWidget(self.viewer, stretch = 100)
        self.mainLayout.addWidget(sidePanel, stretch = 1)
    
    def resizeEvent(self, event):
        if size == 3 or size == 4:
            w = event.size().width()
            h = event.size().height()
            if w/h < 8/5:
                self.resize(max(720, int(h / 5 * 8)), max(415, h))
            if w < 720 or h < 415:
                self.resize(720, 415)
            self.mainLayout.setStretch(0, 4 * h)
            self.mainLayout.setStretch(1, 3 * w - 4 * h)
    
    def closeEvent(self, event):
        self.imagePanel.deleteAllLayers()
        self.window = HomeWindow()
        self.window.show()
        event.accept()

class ThreeDMainWindow(QMainWindow):
    def __init__(self, shapes, linesPlanes, namespace):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 v0.2.1a - 3D Visualiser")
        self.viewer = ThreeDViewer(shapes, linesPlanes, namespace)
        if size == 1:
            self.resize(800, 600 - 30)
            self.viewer.setFixedSize(560, 420)
        elif size == 2:
            self.resize(1024, 768 - 30)
            self.viewer.setFixedSize(720, 540)
        elif size == 3 or size == 4:
            self.resize(1280, 720 - 30)
        else:
            sys.exit()
        
        self.openMainWindowOnClose = True

        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        load = QAction("Load", self)
        load.triggered.connect(self.load)
        save = QAction("Save", self)
        save.triggered.connect(self.save)
        toolbar.addAction(load)
        toolbar.addAction(save)

        toolbar.addSeparator()

        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QHBoxLayout()
        central.setLayout(self.mainLayout)

        sidePanel = QWidget()
        sidePanelLayout = ThreeDSidePanel(self.viewer)
        transformationPanel = sidePanelLayout.transformationPanel
        objectPanel = sidePanelLayout.objectPanel
        linePlanePanel = sidePanelLayout.linePlanePanel
        sidePanelLayout.addLayout(transformationPanel, stretch = 1)
        sidePanelLayout.addLayout(objectPanel, stretch = 100)
        sidePanelLayout.addLayout(linePlanePanel, stretch = 100)
        sidePanel.setLayout(sidePanelLayout)
        self.mainLayout.addWidget(self.viewer, stretch = 3)
        self.mainLayout.addWidget(sidePanel, stretch = 1)

    def load(self):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select Shapes",
            "",
            "JSON File (*.json)"
        )[0]
        if file_path:
            with open(file_path, "r") as file:
                dics = json.load(file)
            initShapes = []
            initLinesPlanes = []
            i = 0
            for j in range(len(dics) - 1):
                obj = None
                while not obj:
                    obj = dics[j].get(str(i))
                    if obj and "Line" in obj['name']:
                        initLinesPlanes.append(Shapes.Line(obj['a1'], obj['a2'], obj['a3'], obj['d1'], obj['d2'], obj['d3']))
                    elif obj and "Plane" in obj['name']:
                        initLinesPlanes.append(Shapes.Plane(obj['a'], obj['b'], obj['c'], obj['d']))
                    elif obj:
                        initShapes.append(Shapes.Solid(obj['name'], obj['vertices'], obj['edges'], obj['surfaces'], obj['params']))
                    i += 1
            
            self.newWindow = ThreeDMainWindow(initShapes, initLinesPlanes, dics[-1]['namespace'])
            self.newWindow.show()
            self.openMainWindowOnClose = False
            self.close()

    def save(self):
        data = []
        i = 0
        for obj in self.viewer.objects:
            data.append({str(i):
            {
                "name": obj.name,
                "vertices": obj.vertices,
                "edges": obj.edges,
                "surfaces": obj.surfaces,
                "params": obj.params
            }})
            i += 1
        for obj in self.viewer.linesPlanes:
            if isinstance(obj, Shapes.Line):
                data.append({str(i):
                {
                    "name": obj.name,
                    "a1": obj.a1,
                    "a2": obj.a2,
                    "a3": obj.a3,
                    "d1": obj.d1,
                    "d2": obj.d2,
                    "d3": obj.d3
                }})
            else:
                data.append({str(i):
                {
                    "name": obj.name,
                    "a": obj.a,
                    "b": obj.b,
                    "c": obj.c,
                    "d": obj.d
                }})
            i += 1
        data.append({"namespace": self.viewer.namespace})
        
        file_path = QFileDialog.getSaveFileName(
        None,
        "Save...",
        "",
        "JSON File (*.json)"
        )[0]
        if file_path:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)

    def resizeEvent(self, event):
        if size == 3 or size == 4:
            w = event.size().width()
            h = event.size().height()
            if w/h < 8/5:
                self.resize(max(720, int(h / 5 * 8)), max(415, h))
            if w < 720 or h < 415:
                self.resize(720, 415)
            self.mainLayout.setStretch(0, 4 * h)
            self.mainLayout.setStretch(1, 3 * w - 4 * h)
    
    def closeEvent(self, event):
        if self.openMainWindowOnClose:
            self.window = HomeWindow()
            self.window.show()
        event.accept()

class NumStabilityMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 v0.2.1a - Numerical Stability")
        self.resize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QHBoxLayout()
        central.setLayout(self.mainLayout)
        
        self.viewer = NumStabilityViewer()

        sidePanel = QWidget()
        sidePanelLayout = NumStabilitySidePanel(self.viewer)
        sidePanel.setLayout(sidePanelLayout)
        self.mainLayout.addWidget(self.viewer, stretch = 3)
        self.mainLayout.addWidget(sidePanel, stretch = 1)
    
    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        if w/h < 8/5:
            self.resize(max(720, int(h / 5 * 8)), max(415, h))
        if w < 720 or h < 415:
            self.resize(720, 415)
        self.mainLayout.setStretch(0, 4 * h)
        self.mainLayout.setStretch(1, 3 * w - 4 * h)
    
    def closeEvent(self, event):
        self.window = HomeWindow()
        self.window.show()
        event.accept()

class MarkovChainsMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 v0.2.1a - Markov Chains")
        mat = np.array([[0.2, 0.4, 0.3],
                        [0.5, 0.1, 0.3],
                        [0.3, 0.5, 0.4]])
        init = np.array([1, 0, 0])
        viewer = MarkovChainsViewer(mat, init, theme, size)
        self.graphViewer = QGraphicsView(viewer)

        if size == 1:
            self.resize(800, 600 - 30)
            self.graphViewer.setFixedSize(420, 420)
        elif size == 2:
            self.resize(1024, 768 - 30)
            self.graphViewer.setFixedSize(600, 600)
        elif size == 3 or size == 4:
            self.resize(1280, 720 - 30)
            self.graphViewer.setFixedSize(600, 600)
        else:
            sys.exit()

        central = QWidget()
        self.layout = QGridLayout()
        timePanel = QWidget()
        self.timePanelLayout = MarkovChainsTimePanel(viewer)
        timePanel.setLayout(self.timePanelLayout)
        sidePanel = QWidget()
        sidePanelLayout = MarkovChainsSidePanel(self, viewer, timePanel, size)
        sidePanel.setLayout(sidePanelLayout)
        self.layout.addWidget(self.graphViewer, 0, 0)
        self.layout.addWidget(sidePanel, 0, 1, 2, 1)
        self.layout.addWidget(timePanel, 1, 0)
        central.setLayout(self.layout)

        self.setCentralWidget(central)
    
    def closeEvent(self, event):
        self.window = HomeWindow()
        self.window.show()
        event.accept()

class SettingsWindow(QMainWindow):
    def __init__(self, home):
        super().__init__()
        self.home = home
        self.updated = False
        self.darkTheme = theme
        self.curSize = size

        self.setWindowTitle("Settings")
        
        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QGridLayout()
        central.setLayout(self.mainLayout)

        self.mainLayout.addWidget(QLabel("System Theme:"), 0, 0, 1, 2)
        self.light = QRadioButton("Light")
        self.light.clicked.connect(self.setLight)
        self.dark = QRadioButton("Dark")
        self.dark.clicked.connect(self.setDark)

        if theme == 0:
            self.light.setChecked(True)
        else:
            self.dark.setChecked(True)
        self.mainLayout.addWidget(self.light, 0, 2)
        self.mainLayout.addWidget(self.dark, 0, 3)

        self.mainLayout.addWidget(QLabel("Config size:"), 1, 0, 1, 2)
        self.sizeBox = QSpinBox()
        self.sizeBox.setRange(1, 4)
        self.sizeBox.setValue(size)
        self.sizeBox.valueChanged.connect(self.setSize)
        self.mainLayout.addWidget(self.sizeBox, 1, 2, 1, 2)
        self.mainLayout.addWidget(QLabel("Configure the default window size for Visu(AL)-1 depending on your display resolution.\n" \
                                         "Currently only supported for 3D Visualiser and 2D Image Processing.\n\n" \
                                         "Size 1: Use this for 800x600 displays. Preview panels will be sized to 560x420.\n" \
                                         "Size 2: Use this for 1024x768 displays. Preview panels will be sized to 720x540.\n" \
                                         "Size 3: Suitable for displays 1280x720 or larger. 2D image processing panel will be\n" \
                                         "sized to 960x540, and 3D graphics has no theoretical limit.\n" \
                                         "Size 4: Enable high-definition image previews for 2D image processing; preview panel will be\n" \
                                         "sized to 1600x900. Warning: Higher memory load and requires a 1920x1080 or larger display."), 2, 0, 1, 4)
        self.submit = QPushButton("Save")
        self.submit.clicked.connect(self.updateSize)
        self.mainLayout.addWidget(self.submit, 3, 0, 1, 4)
    
    def setSize(self):
        self.curSize = self.sizeBox.value()

    def setLight(self):
        self.darkTheme = 0
    
    def setDark(self):
        self.darkTheme = 1

    def updateSize(self):
        self.updated = True
        f1 = open(resource_path("static/sizeconfig.txt"), "w")
        f1.write(str(self.curSize))
        f1.close()
        f2 = open(resource_path("static/theme.txt"), "w")
        f2.write(str(self.darkTheme))
        f2.close()
        self.close()
    
    def closeEvent(self, event):
        if self.updated:
            global size, theme
            size = self.curSize
            theme = self.darkTheme
            self.window = HomeWindow()
            self.window.show()
            self.home.close()
        event.accept()

window = HomeWindow()
window.show()

sys.exit(app.exec())