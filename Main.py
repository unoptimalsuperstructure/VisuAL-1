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

        self.objects = [Shapes.UnitCube()]
        self.last = [[self.objects[0], Shapes.Shape(), Shapes.Shape()]]

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
        if self.last:
            self.last[-1][1].draw()
            self.last[-1][2].draw()

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
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.transformationPanel = TransformationPanel(self)
        self.objectPanel = ObjectPanel(self)
        self.activeObj = None
        self.lastObj = None
    
    def translateWindow(self):
        self.window = Windows.TranslateWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.translate)
    
    def translate(self, nums):
        self.activeObj.translate(*nums)
        if self.activeObj.lastTransform:
            self.viewer.last.append([self.activeObj, self.activeObj.lastTransform[-1], self.activeObj.lastShape])
            self.lastObj = self.activeObj
    
    def reflectLineWindow(self):
        self.window = Windows.ReflectLineWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.reflectLine)
    
    def reflectLine(self, nums):
        self.activeObj.reflectLine(*nums)
        if self.activeObj.lastTransform:
            self.viewer.last.append([self.activeObj, self.activeObj.lastTransform[-1], self.activeObj.lastShape])
            self.lastObj = self.activeObj

    def reflectPlaneWindow(self):
        self.window = Windows.ReflectPlaneWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.reflectPlane)
    
    def reflectPlane(self, nums):
        self.activeObj.reflectPlane(*nums)
        if self.activeObj.lastTransform:
            self.viewer.last.append([self.activeObj, self.activeObj.lastTransform[-1], self.activeObj.lastShape])
    
    def rotate(self, nums):
        self.activeObj.rotate(*nums)
        if self.activeObj.lastTransform:
            self.viewer.last.append([self.activeObj, self.activeObj.lastTransform[-1], self.activeObj.lastShape])
            self.lastObj = self.activeObj
    
    def rotateWindow(self):
        self.window = Windows.RotateWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.rotate)

    def undo(self):
        if self.viewer.last:
            lastObj = self.viewer.last.pop()[0]
            if len(lastObj.matrixStack) == 1:
                self.viewer.objects.pop()
                if self.viewer.objects:
                    self.activeObj = self.viewer.objects[-1]
                else:
                    self.activeObj = None
                self.objectPanel.deleteButton(lastObj)
            else:
                lastObj.undo()
        self.viewer.update()
    
    def resetShape(self):
        if self.activeObj:
            self.activeObj.resetMatrix()
            self.viewer.last = []
        self.viewer.update()
    
    def deleteShape(self):
        if self.activeObj:
            self.viewer.objects.pop(self.viewer.objects.index(self.activeObj))
            self.viewer.last = []
            self.objectPanel.deleteButton(self.activeObj)
            self.activeObj = None
        self.viewer.update()
    
    def addShapeWindow(self):
        self.window = Windows.AddShapeWindow()
        self.window.show()
        self.window.params.connect(self.addShape)
    
    def addShape(self, params):
        shape, nums = params[0], params[1:]
        lookup = {"UnitCube": Shapes.UnitCube}
        obj = lookup[shape](*nums)
        self.viewer.objects.append(obj)
        self.viewer.last.append([obj, Shapes.Shape(), Shapes.Shape()])
        self.objectPanel.addButton(obj)
    
    def viewStackWindow(self):
        if self.activeObj:
            self.window = Windows.ViewStackWindow(self.activeObj)
            self.window.show()

class TransformationPanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Transformations"))
        self.sidePanel = sidePanel

        translateButton = QPushButton("Translate")
        translateButton.clicked.connect(self.sidePanel.translateWindow)

        reflectLineButton = QPushButton("Reflect about Line")
        reflectLineButton.clicked.connect(self.sidePanel.reflectLineWindow)

        reflectPlaneButton = QPushButton("Reflect about Plane")
        reflectPlaneButton.clicked.connect(self.sidePanel.reflectPlaneWindow)

        rotateButton = QPushButton("Rotate about Line")
        rotateButton.clicked.connect(self.sidePanel.rotateWindow)

        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.sidePanel.undo)

        resetButton = QPushButton("Reset current object (irreversible)")
        resetButton.clicked.connect(self.sidePanel.resetShape)

        deleteButton = QPushButton("Delete current object (irreversible)")
        deleteButton.clicked.connect(self.sidePanel.deleteShape)
        
        self.addWidget(translateButton)
        self.addWidget(reflectLineButton)
        self.addWidget(reflectPlaneButton)
        self.addWidget(rotateButton)
        self.addWidget(undoButton)
        self.addWidget(resetButton)
        self.addWidget(deleteButton)
        self.addStretch()
    
class ObjectPanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Objects"))
        self.sidePanel = sidePanel
        self.buttons = []
        addButton = QPushButton("Add new Shape...")
        addButton.clicked.connect(self.sidePanel.addShapeWindow)
        self.addWidget(addButton)
        viewStackButton = QPushButton("View Matrix Stack")
        viewStackButton.clicked.connect(self.sidePanel.viewStackWindow)
        self.addWidget(viewStackButton)
        for obj in sidePanel.viewer.objects:
            button = QRadioButton(obj.type)
            button.obj = obj
            button.toggled.connect(self.onToggle)
            self.buttons.append(button)
            self.addWidget(button)
    
    def addButton(self, obj):
        button = QRadioButton(obj.type)
        button.obj = obj
        button.toggled.connect(self.onToggle)
        self.buttons.append(button)
        self.addWidget(button)
    
    def deleteButton(self, obj):
        for button in self.buttons:
            if button.obj == obj:
                self.buttons.pop(self.buttons.index(button))
                self.removeWidget(button)
    
    def onToggle(self):
        rb = self.sender()
        if rb.isChecked():
            self.sidePanel.activeObj = rb.obj
        else:
            self.sidePanel.activeObj = None
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visu(AL)-1 - 3D Visualiser v0.0.2a")
        self.resize(960, 540)

        central = QWidget()
        self.setCentralWidget(central)

        mainLayout = QHBoxLayout()
        central.setLayout(mainLayout)
        
        self.viewer = Viewer()

        sidePanel = QWidget()
        sidePanelLayout = SidePanel(self.viewer)
        transformationPanel = sidePanelLayout.transformationPanel
        objectPanel = sidePanelLayout.objectPanel
        sidePanelLayout.addLayout(transformationPanel, stretch = 1)
        sidePanelLayout.addLayout(objectPanel, stretch = 1)
        sidePanel.setLayout(sidePanelLayout)
        mainLayout.addWidget(self.viewer, stretch = 3)

        mainLayout.addWidget(sidePanel, stretch = 1)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())