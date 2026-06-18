import gc, sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import QEvent, Qt
from TwoDImages import TwoDViewer, TwoDSidePanel
from ThreeDGraphics import ThreeDViewer, ThreeDSidePanel
from Images import Image
import Shapes

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
        self.Button3 = QPushButton("PCA Tool")
        self.Button4 = QPushButton("Markov Chains")
        self.Button1.setFixedWidth(150)
        self.Button2.setFixedWidth(150)
        self.Button3.setFixedWidth(150)
        self.Button4.setFixedWidth(150)
        self.Button1.clicked.connect(self.TwoDee)
        self.Button2.clicked.connect(self.ThreeDee)
        self.addWidget(self.Button1)
        self.addWidget(self.Button2)
        self.addWidget(self.Button3)
        self.addWidget(self.Button4)
        
        self.addWidget(QLabel("Hello!"))

        self.hover = False

        self.Button1.installEventFilter(self)
        self.Button2.installEventFilter(self)
        self.Button3.installEventFilter(self)
        self.Button4.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if obj in [self.Button1, self.Button3, self.Button4]:
            width = int(self.mainWindow.previewPanel.width()//1.2)
            height = int(self.mainWindow.previewPanel.height()//1.2)
            img = self.previewPanelLayout.previewImage
            label = self.previewPanelLayout.defaultLabel
            if not self.hover:
                img.setPixmap(QPixmap("static/ComingSoon.png").scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio))
                if event.type() == QEvent.Type.Enter:
                    img.show()
                    label.hide()
                    self.hover = True
            if event.type() == QEvent.Type.Leave:
                img.hide()
                label.show()
                self.hover = False
        
        if obj in [self.Button2]:
            width = int(self.mainWindow.previewPanel.width()//1.2)
            height = int(self.mainWindow.previewPanel.height()//1.2)
            img = self.previewPanelLayout.previewImage
            label = self.previewPanelLayout.defaultLabel
            if not self.hover:
                img.setPixmap(QPixmap("static/3DGraphics.png").scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio))
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
        self.newWindow = ThreeDMainWindow()
        self.newWindow.show()
        self.mainWindow.close()

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

        self.setWindowTitle("Visu(AL)-1 v0.1.2b - Home")
        self.resize(1280, 720)

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

        self.setWindowTitle("Visu(AL)-1 v0.1.2b - 2D Image Processing")
        self.resize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QHBoxLayout()
        central.setLayout(self.mainLayout)
        
        self.viewer = TwoDViewer([Image("static/kagura.png")])

        sidePanel = QWidget()
        sidePanelLayout = TwoDSidePanel(self.viewer)
        transformationPanel = sidePanelLayout.transformationPanel
        self.imagePanel = sidePanelLayout.imagePanel
        sidePanelLayout.addLayout(transformationPanel, stretch = 1)
        sidePanelLayout.addLayout(self.imagePanel, stretch = 1)
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
        self.imagePanel.deleteAllLayers()
        self.window = HomeWindow()
        self.window.show()
        event.accept()

class ThreeDMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 v0.1.2b - 3D Visualiser")
        f1 = open("sizeconfig.txt")
        self.size = int(f1.readline())
        f1.close()
        self.viewer = ThreeDViewer(["Cube"])
        if self.size == 1:
            self.resize(800, 600)
            self.viewer.setFixedSize(560, 420)
        elif self.size == 2:
            self.resize(1024, 768)
            self.viewer.setFixedSize(720, 540)
        elif self.size == 3 or self.size == 4:
            self.resize(1280, 720)
        else:
            sys.exit()

        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        load = QAction("Load", self)
        #load.triggered.connect(self.load)
        save = QAction("Save", self)
        #save.triggered.connect(self.save)
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
    
    def resizeEvent(self, event):
        if self.size == 3:
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

app = QApplication(sys.argv)

window = HomeWindow()
window.show()

sys.exit(app.exec())