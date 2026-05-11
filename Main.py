import math, Shapes, sys, Windows
from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *

class Viewer(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_action)
        self.timer.setInterval(10)

        self.pressed_keys = set()

        self.objects = [Shapes.Cube(1)]

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def reset(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glViewport(0, 0, 960, 720)
        self.resetFlag = True

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        if self.resetFlag:
            glLoadIdentity()
            gluPerspective(60, 4/3, 0.1, 50.0)
            glTranslate(0, 0, -4)
            glRotatef(60, -1, 0, 0)
            glRotatef(45, 0, 0, 1)
            self.yaw = 45
            self.pitch = 30
            self.roll = 0
            self.x_off = 0
            self.y_off = 0
            self.z_off = 0
            self.resetFlag = False
        else:
            glTranslate(-self.x_off, -self.y_off, -self.z_off)
            glRotatef(self.yawDelta, 0, 0, 1)
            glRotatef(self.pitchDelta, math.cos(self.yaw*math.pi/180), -math.sin(self.yaw*math.pi/180), 0)
            glRotatef(self.rollDelta, math.sin(self.yaw*math.pi/180), math.cos(self.yaw*math.pi/180), 0)
            self.x_off += self.x_delta
            self.y_off += self.y_delta
            self.z_off += self.z_delta
            self.yaw += self.yawDelta
            self.pitch += self.pitchDelta
            self.roll += self.rollDelta
            glTranslate(self.x_off, self.y_off, self.z_off)
        self.yawDelta = 0
        self.pitchDelta = 0
        self.rollDelta = 0
        self.x_delta = 0
        self.y_delta = 0
        self.z_delta = 0
        Shapes.drawAxes()
        for obj in self.objects:
            obj.draw()

    def mousePressEvent(self, event):
        self.x_delta = 0
        self.y_delta = 0
        self.z_delta = 0
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self.last_mouse_pos = event.position().toPoint()
        
        if event.button() == Qt.MouseButton.MiddleButton:
            self.resetFlag = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            cur_pos = event.position().toPoint()
            delta = cur_pos - self.last_mouse_pos
            self.last_mouse_pos = cur_pos
            self.rollDelta = 0

            self.yawDelta = 0.5 * delta.x()

            if (self.pitch < 90 and delta.y() > 0) or (self.pitch > -90 and delta.y() < 0):
               self.pitchDelta = 0.5 * delta.y()
            else:
                self.pitchDelta = 0
            self.update()
        
        if event.buttons() == Qt.MouseButton.RightButton:
            cur_pos = event.position().toPoint()
            delta = cur_pos - self.last_mouse_pos
            self.last_mouse_pos = cur_pos
            self.yawDelta = 0
            self.pitchDelta = 0

            self.rollDelta = 0.5 * delta.x()
            self.update()
    
    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            self.pressed_keys.add(event.key())
            self.perform_action()
            if not self.timer.isActive():
                self.timer.start()
        
        glTranslate(self.x_off, self.y_off, -self.z_off)
        
    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.pressed_keys.discard(event.key())
            if not self.pressed_keys:
                self.timer.stop()

    def perform_action(self):
        self.yawDelta = 0
        self.pitchDelta = 0
        self.rollDelta = 0
        self.x_delta = 0
        self.y_delta = 0
        self.z_delta = 0
        if Qt.Key.Key_W in self.pressed_keys:
            self.x_delta = -0.1 * math.sin(self.yaw*math.pi/180)
            self.y_delta = -0.1 * math.cos(self.yaw*math.pi/180)
        if Qt.Key.Key_S in self.pressed_keys:
            self.x_delta = 0.1 * math.sin(self.yaw*math.pi/180)
            self.y_delta = 0.1 * math.cos(self.yaw*math.pi/180)
        if Qt.Key.Key_A in self.pressed_keys:
            self.x_delta = 0.1 * math.cos(self.yaw*math.pi/180)
            self.y_delta = -0.1 * math.sin(self.yaw*math.pi/180)
        if Qt.Key.Key_D in self.pressed_keys:
            self.x_delta = -0.1 * math.cos(self.yaw*math.pi/180)
            self.y_delta = 0.1 * math.sin(self.yaw*math.pi/180)
        if Qt.Key.Key_Space in self.pressed_keys:
            self.z_delta = -0.1
        if Qt.Key.Key_Shift in self.pressed_keys:
            self.z_delta = 0.1
        
        self.update()

class SidePanel(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.viewer = None
        self.addWidget(QLabel("Transformations"))

        translateButton = QPushButton("Translate")
        translateButton.clicked.connect(self.translateWindow)

        reflectLineButton = QPushButton("Reflect about Line")
        reflectLineButton.clicked.connect(self.reflectLineWindow)

        reflectPlaneButton = QPushButton("Reflect about Plane")
        reflectPlaneButton.clicked.connect(self.reflectPlaneWindow)

        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.undo)

        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.resetShape)
        
        self.addWidget(translateButton)
        self.addWidget(reflectLineButton)
        self.addWidget(reflectPlaneButton)
        self.addWidget(undoButton)
        self.addWidget(resetButton)
        self.addStretch()
    
    def translateWindow(self):
        self.window = Windows.TranslateWindow()
        self.window.show()
        self.window.nums.connect(self.translate)
    
    def translate(self, nums):
        for obj in self.viewer.objects:
            obj.translate(*nums)
    
    def reflectLineWindow(self):
        self.window = Windows.ReflectLineWindow()
        self.window.show()
        self.window.nums.connect(self.reflectLine)
    
    def reflectLine(self, nums):
        for obj in self.viewer.objects:
            obj.reflectLine(*nums)

    def reflectPlaneWindow(self):
        self.window = Windows.ReflectPlaneWindow()
        self.window.show()
        self.window.nums.connect(self.reflectPlane)
    
    def reflectPlane(self, nums):
        for obj in self.viewer.objects:
            obj.reflectPlane(*nums)
    
    def undo(self):
        for obj in self.viewer.objects:
            obj.undo()
        self.viewer.update()
    
    def resetShape(self):
        for obj in self.viewer.objects:
            obj.resetMatrix()
        self.viewer.update()
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visual(LA)-1 - 3D Visualiser v0.0.1")
        self.resize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)

        mainLayout = QHBoxLayout()
        central.setLayout(mainLayout)
        
        self.viewer = Viewer()

        sidePanel = QWidget()
        sidePanelLayout = SidePanel()
        sidePanelLayout.viewer = self.viewer
        sidePanel.setLayout(sidePanelLayout)
        mainLayout.addWidget(self.viewer, stretch = 3)

        mainLayout.addWidget(sidePanel, stretch = 1)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())