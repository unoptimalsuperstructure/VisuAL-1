import math, Shapes, Windows
from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *

class ThreeDViewer(QOpenGLWidget):
    def __init__(self, initShapes):
        super().__init__()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_action)
        self.timer.setInterval(10)

        self.pressed_keys = set()

        self.objects = initShapes
        self.lastObjStack = self.objects.copy()
        self.shadow = None

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
        if self.shadow:
            self.shadow.draw()

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

class ThreeDSidePanel(QVBoxLayout):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.transformationPanel = ThreeDTransformationPanel(self)
        self.objectPanel = ThreeDObjectPanel(self)
        self.activeObj = None
    
    def translateWindow(self):
        self.window = Windows.TranslateWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.translate)
    
    def translate(self, nums):
        self.activeObj.translate(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)
    
    def reflectLineWindow(self):
        self.window = Windows.ReflectLineWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.reflectLine)
    
    def reflectLine(self, nums):
        self.activeObj.reflectLine(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)

    def reflectPlaneWindow(self):
        self.window = Windows.ReflectPlaneWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.reflectPlane)
    
    def reflectPlane(self, nums):
        self.activeObj.reflectPlane(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)
    
    def rotateLineWindow(self):
        self.window = Windows.RotateLineWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.rotateLine)
    
    def rotateLine(self, nums):
        self.activeObj.rotateLine(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)
    
    def projectPlaneWindow(self):
        self.window = Windows.ProjectPlaneWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.projectPlane)
    
    def projectPlane(self, nums):
        self.activeObj.projectPlane(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)
    
    def scaleWindow(self):
        self.window = Windows.ScaleWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.scale)
    
    def scale(self, nums):
        self.activeObj.scale(*nums)
        self.viewer.shadow = self.activeObj.getShadow()
        if self.viewer.shadow:
            self.viewer.lastObjStack.append(self.activeObj)

    def repeat(self):
        if self.activeObj:
            self.activeObj.repeat()
            self.viewer.shadow = self.activeObj.getShadow()
            self.viewer.lastObjStack.append(self.activeObj)
        self.viewer.update()
    
    def undo(self):
        if self.viewer.objects and self.viewer.lastObjStack:
            lastObj = self.viewer.lastObjStack.pop()
            if len(lastObj.matrixStack) == 1:
                self.viewer.objects.pop()
                if self.viewer.objects:
                    self.activeObj = self.viewer.objects[-1]
                else:
                    self.activeObj = None
                self.objectPanel.deleteButton(lastObj)
            else:
                lastObj.undo()
            if self.viewer.lastObjStack:
                self.viewer.shadow = self.viewer.lastObjStack[-1].getShadow()
            else:
                self.viewer.shadow = None
        self.viewer.update()
    
    def resetShape(self):
        if self.activeObj:
            self.activeObj.resetMatrix()
            self.viewer.shadow = None
            self.viewer.lastObjStack = []
        self.viewer.update()
    
    def deleteShape(self):
        if self.activeObj:
            self.viewer.objects.pop(self.viewer.objects.index(self.activeObj))
            self.viewer.shadow = None
            self.viewer.lastObjStack = []
            self.objectPanel.deleteButton(self.activeObj)
            self.activeObj = None
        self.viewer.update()
    
    def addShapeWindow(self):
        self.window = Windows.AddShapeWindow()
        self.window.show()
        self.window.params.connect(self.addShape)
    
    def addShape(self, params):
        shape, nums = params[0], params[1:]
        lookup = {"UnitCube": Shapes.UnitCube, "UnitTetrahedron": Shapes.UnitTetrahedron}
        obj = lookup[shape](*nums)
        self.viewer.objects.append(obj)
        self.viewer.lastObjStack.append(obj)
        self.objectPanel.addButton(obj)
    
    def viewStackWindow(self):
        if self.activeObj:
            self.window = Windows.ViewStackWindow(self.activeObj)
            self.window.show()

class ThreeDTransformationPanel(QVBoxLayout):
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

        rotateLineButton = QPushButton("Rotate about Line")
        rotateLineButton.clicked.connect(self.sidePanel.rotateLineWindow)

        projectPlaneButton = QPushButton("Project onto Plane")
        projectPlaneButton.clicked.connect(self.sidePanel.projectPlaneWindow)

        scaleButton = QPushButton("Scale")
        scaleButton.clicked.connect(self.sidePanel.scaleWindow)

        repeatButton = QPushButton("Repeat last Transformation")
        repeatButton.clicked.connect(self.sidePanel.repeat)

        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.sidePanel.undo)

        resetButton = QPushButton("Reset current object (irreversible)")
        resetButton.clicked.connect(self.sidePanel.resetShape)

        deleteButton = QPushButton("Delete current object (irreversible)")
        deleteButton.clicked.connect(self.sidePanel.deleteShape)
        
        self.addWidget(translateButton)
        self.addWidget(reflectLineButton)
        self.addWidget(reflectPlaneButton)
        self.addWidget(rotateLineButton)
        self.addWidget(projectPlaneButton)
        self.addWidget(scaleButton)
        self.addWidget(repeatButton)
        self.addWidget(undoButton)
        self.addWidget(resetButton)
        self.addWidget(deleteButton)
        self.addStretch()
    
class ThreeDObjectPanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Objects"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.addWidget(scroll)
        objects = QWidget()
        self.objectsLayout = QVBoxLayout(objects)
        self.sidePanel = sidePanel
        self.buttons = []
        for obj in sidePanel.viewer.objects:
            button = QRadioButton(obj.type)
            button.obj = obj
            button.toggled.connect(self.onToggle)
            self.buttons.append(button)
            self.objectsLayout.addWidget(button, alignment = Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(objects)
        addButton = QPushButton("Add new Shape...")
        addButton.clicked.connect(self.sidePanel.addShapeWindow)
        self.addWidget(addButton)
        viewStackButton = QPushButton("View Matrix Stack")
        viewStackButton.clicked.connect(self.sidePanel.viewStackWindow)
        self.addWidget(viewStackButton)
    
    def addButton(self, obj):
        button = QRadioButton(obj.type)
        button.obj = obj
        button.toggled.connect(self.onToggle)
        self.buttons.append(button)
        self.objectsLayout.addWidget(button, alignment = Qt.AlignmentFlag.AlignTop)
    
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