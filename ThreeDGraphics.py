import math, Shapes, ThreeDWindows
from PyQt6.QtWidgets import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPoint, QTimer, QEvent
from OpenGL.GL import *
from OpenGL.GLU import *
from Tooltips import TooltipButton
from pathlib import Path
from bson import json_util
from pymongo import MongoClient

class ThreeDViewer(QOpenGLWidget):
    def __init__(self, initSolids):
        super().__init__()

        client = MongoClient("mongodb://localhost:27017/")
        db = client["geometry"]
        self.solids = db["solids"]
        self.solids.drop()

        for json_file in Path("./Shapes/Solids").glob("*.json"):
            try:
                with open(json_file, "r") as file:
                    self.solids.insert_one(json_util.loads(file.read()))
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")
        
        self.templates = []
        cursor = self.solids.find("")
        self.allSolids = []
        for solid in cursor:
            self.allSolids.append(solid)
        for solid in initSolids:
            self.templates.append(self.solids.find_one({"name": solid}))
        self.objects = []
        for solid in self.templates:
            self.objects.append(Shapes.Solid(solid["name"], solid["vertices"], solid["edges"], solid["surfaces"], [1, 0, 0, 0]))
        self.lastObjStack = self.objects.copy()
        self.linesPlanes = []

        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_action)
        self.timer.setInterval(10)

        self.pressed_keys = set()

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
        
        for obj in self.linesPlanes:
            if obj.vis or obj.isActive:
                obj.draw()
        for obj in self.objects:
            obj.draw()
        if self.lastObjStack:
            lastObj = self.lastObjStack[-1]
            if lastObj.show:
                lastObj.getShadow().draw()

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
        self.linePlanePanel = ThreeDLinePlanePanel(self)
        self.objectPanel = ThreeDObjectPanel(self)
        self.activeObj = None
        self.activeLinePlane = None
    
    def addLineWindow(self):
        self.window = ThreeDWindows.AddLineWindow()
        self.window.show()
        self.window.nums.connect(self.addLine)
    
    def addLine(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            newLine = Shapes.Line(*nums[:-1])
            duplicate = False
            for line in self.viewer.linesPlanes:
                if newLine.name == line.name:
                    duplicate = True
                    self.error = ThreeDWindows.ErrorWindow(3, nums[-1])
                    self.error.show()
                    del newLine
                    break
            if not duplicate:
                self.viewer.linesPlanes.append(newLine)
                self.linePlanePanel.addButton(newLine)

    def addPlaneWindow(self):
        self.window = ThreeDWindows.AddPlaneWindow()
        self.window.show()
        self.window.nums.connect(self.addPlane)
    
    def addPlane(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            newPlane = Shapes.Plane(*nums[:-1])
            duplicate = False
            for plane in self.viewer.linesPlanes:
                if newPlane.name == plane.name:
                    duplicate = True
                    self.error = ThreeDWindows.ErrorWindow(3, nums[-1])
                    self.error.show()
                    del newPlane
                    break
            if not duplicate:
                self.viewer.linesPlanes.append(newPlane)
                self.linePlanePanel.addButton(newPlane)
    
    def deleteLinePlaneWindow(self):
        self.window = ThreeDWindows.DeleteLinePlaneWindow(self.viewer.linesPlanes)
        self.window.show()
        self.window.objName.connect(self.deleteLinePlane)
    
    def deleteLinePlane(self, objName):
        if objName == "Close":
            for linePlane in self.viewer.linesPlanes:
                linePlane.isActive = False
        elif objName == "Done":
            i = 0
            while i < len(self.viewer.linesPlanes):
                if self.viewer.linesPlanes[i].isActive:
                    self.linePlanePanel.deleteButton(self.viewer.linesPlanes.pop(i))
                else:
                    i += 1
        else:
            for linePlane in self.viewer.linesPlanes:
                if linePlane.name == objName:
                    linePlane.isActive = not linePlane.isActive
                    break
        self.viewer.update()
    
    def translateWindow(self):
        self.window = ThreeDWindows.TranslateWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.translate)
    
    def translate(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            self.activeObj.translate(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
    
    def reflectLineWindow(self):
        self.window = ThreeDWindows.ReflectLineWindow(self.activeObj, self.viewer.linesPlanes)
        self.window.show()
        self.window.nums.connect(self.reflectLine)
    
    def reflectLine(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        elif isinstance(nums[0], str):
            if nums[0] == "Existing Line":
                self.activeObj.reflectLine(*self.activeLinePlane.lst)
                self.viewer.shadow = self.activeObj.getShadow()
                if self.viewer.shadow:
                    self.viewer.lastObjStack.append(self.activeObj)
            elif nums[0] != "Deselect":
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                for line in self.viewer.linesPlanes:
                    if line.name == nums[0]:
                        line.isActive = True
                        self.activeLinePlane = line
                        break
            else:
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                    self.activeLinePlane = None
            self.viewer.update()
        else:
            self.activeObj.reflectLine(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
            self.viewer.update()

    def reflectPlaneWindow(self):
        self.window = ThreeDWindows.ReflectPlaneWindow(self.activeObj, self.viewer.linesPlanes)
        self.window.show()
        self.window.nums.connect(self.reflectPlane)
    
    def reflectPlane(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        elif isinstance(nums[0], str):
            if nums[0] == "Existing Plane":
                self.activeObj.reflectPlane(*self.activeLinePlane.lst)
                self.viewer.shadow = self.activeObj.getShadow()
                if self.viewer.shadow:
                    self.viewer.lastObjStack.append(self.activeObj)
                self.activeLinePlane.isActive = False
            elif nums[0] != "Deselect":
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                for plane in self.viewer.linesPlanes:
                    if plane.name == nums[0]:
                        plane.isActive = True
                        self.activeLinePlane = plane
                        break
            else:
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                    self.activeLinePlane = None
            self.viewer.update()
        else:
            if self.activeLinePlane:
                self.activeLinePlane.isActive = False
                self.activeLinePlane = None
            self.activeObj.reflectPlane(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
            self.viewer.update()
    
    def rotateLineWindow(self):
        self.window = ThreeDWindows.RotateLineWindow(self.activeObj, self.viewer.linesPlanes)
        self.window.show()
        self.window.nums.connect(self.rotateLine)
    
    def rotateLine(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        elif isinstance(nums[0], str):
            if nums[0] == "Existing Line":
                self.activeObj.rotateLine(*self.activeLinePlane.lst, nums[1])
                self.viewer.shadow = self.activeObj.getShadow()
                if self.viewer.shadow:
                    self.viewer.lastObjStack.append(self.activeObj)
            elif nums[0] != "Deselect":
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                for line in self.viewer.linesPlanes:
                    if line.name == nums[0]:
                        line.isActive = True
                        self.activeLinePlane = line
                        break
            else:
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                    self.activeLinePlane = None
            self.viewer.update()
        else:
            self.activeObj.rotateLine(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
            self.viewer.update()
    
    def projectPlaneWindow(self):
        self.window = ThreeDWindows.ProjectPlaneWindow(self.activeObj, self.viewer.linesPlanes)
        self.window.show()
        self.window.nums.connect(self.projectPlane)
    
    def projectPlane(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        elif isinstance(nums[0], str):
            if nums[0] == "Existing Plane":
                self.activeObj.projectPlane(*self.activeLinePlane.lst)
                self.viewer.shadow = self.activeObj.getShadow()
                if self.viewer.shadow:
                    self.viewer.lastObjStack.append(self.activeObj)
                self.activeLinePlane.isActive = False
            elif nums[0] != "Deselect":
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                for plane in self.viewer.linesPlanes:
                    if plane.name == nums[0]:
                        plane.isActive = True
                        self.activeLinePlane = plane
                        break
            else:
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                    self.activeLinePlane = None
            self.viewer.update()
        else:
            if self.activeLinePlane:
                self.activeLinePlane.isActive = False
                self.activeLinePlane = None
            self.activeObj.projectPlane(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
            self.viewer.update()
    
    def scaleWindow(self):
        self.window = ThreeDWindows.ScaleWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.scale)
    
    def scale(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            self.activeObj.scale(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
    
    def shearWindow(self):
        self.window = ThreeDWindows.ShearWindow(self.activeObj, self.viewer.linesPlanes)
        self.window.show()
        self.window.nums.connect(self.shear)
    
    def shear(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        elif isinstance(nums[0], str):
            if nums[0] == "Existing Line":
                self.activeObj.shear(*self.activeLinePlane.lst, *nums[1:])
                self.viewer.shadow = self.activeObj.getShadow()
                if self.viewer.shadow:
                    self.viewer.lastObjStack.append(self.activeObj)
            elif nums[0] != "Deselect":
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                for line in self.viewer.linesPlanes:
                    if line.name == nums[0]:
                        line.isActive = True
                        self.activeLinePlane = line
                        break
            else:
                if self.activeLinePlane:
                    self.activeLinePlane.isActive = False
                    self.activeLinePlane = None
            self.viewer.update()
        else:
            self.activeObj.shear(*nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
            self.viewer.update()
    
    def customMatrixWindow(self):
        self.window = ThreeDWindows.CustomMatrixWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.customMatrix)
    
    def customMatrix(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            self.activeObj.applyCustomMatrix(nums)
            self.viewer.shadow = self.activeObj.getShadow()
            if self.viewer.shadow:
                self.viewer.lastObjStack.append(self.activeObj)
    
    def repeatWindow(self):
        self.window = ThreeDWindows.RepeatWindow(self.activeObj)
        self.window.show()
        self.window.nums.connect(self.repeat)

    def repeat(self, nums):
        if isinstance(nums[0], ThreeDWindows.ErrorWindow):
            nums[0].show()
        else:
            n = min(nums[0], len(self.activeObj.matrixStack) - 1)
            for i in range(n):
                self.activeObj.repeat(n)
                self.viewer.shadow = self.activeObj.getShadow()
                self.viewer.lastObjStack.append(self.activeObj)
        self.viewer.update()
    
    def undo(self):
        if self.viewer.objects and self.viewer.lastObjStack:
            lastObj = self.viewer.lastObjStack.pop()
            if len(lastObj.matrixStack) == 1:
                if self.activeObj == self.viewer.objects.pop():
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
        self.window = ThreeDWindows.AddShapeWindow(self.viewer.allSolids)
        self.window.show()
        self.window.params.connect(self.addShape)
    
    def addShape(self, params):
        shape, nums = params[0], params[1:]
        solid = self.viewer.solids.find_one({"name": shape})
        obj = Shapes.Solid(solid["name"], solid["vertices"], solid["edges"], solid["surfaces"], nums)
        self.viewer.objects.append(obj)
        self.viewer.lastObjStack.append(obj)
        self.objectPanel.addButton(obj)
    
    def showHide(self):
        if self.activeObj:
            self.activeObj.showhide()
        self.viewer.update()
    
    def viewStackWindow(self):
        if self.activeObj:
            self.window = ThreeDWindows.ViewStackWindow(self.activeObj)
            self.window.show()

class ThreeDTransformationPanel(QGridLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Transformations"))
        self.sidePanel = sidePanel

        translateButton = TooltipButton("Translate",
                                        "Translate",
                                        "Translate the current object\n" \
                                        "along the x, y and z-axes")
        translateButton.clicked.connect(self.sidePanel.translateWindow)
        translateButton.installEventFilter(self)

        reflectLineButton = TooltipButton("ReflectLine",
                                          "ReflectLine",
                                          "Reflect the current object\n" \
                                          "about a specified line")
        reflectLineButton.clicked.connect(self.sidePanel.reflectLineWindow)
        reflectLineButton.installEventFilter(self)

        reflectPlaneButton = TooltipButton("ReflectPlane",
                                           "ReflectPlane",
                                           "Reflect the current object\n" \
                                           "about a specified plane")
        reflectPlaneButton.clicked.connect(self.sidePanel.reflectPlaneWindow)
        reflectPlaneButton.installEventFilter(self)

        rotateLineButton = TooltipButton("RotateLine",
                                         "RotateLine",
                                         "Rotate the current object\n" \
                                         "about a specified line\n" \
                                         "through a specified angle")
        rotateLineButton.clicked.connect(self.sidePanel.rotateLineWindow)
        rotateLineButton.installEventFilter(self)

        projectPlaneButton = TooltipButton("ProjectPlane",
                                           "ProjectPlane",
                                           "Project the current object\n" \
                                           "onto a specified plane")
        projectPlaneButton.clicked.connect(self.sidePanel.projectPlaneWindow)
        projectPlaneButton.installEventFilter(self)

        scaleButton = TooltipButton("Scale",
                                    "Scale",
                                    "Scale the current object by\n" \
                                    "a specified scale factor")
        scaleButton.clicked.connect(self.sidePanel.scaleWindow)
        scaleButton.installEventFilter(self)

        repeatButton = TooltipButton("Repeat",
                                     "Repeat",
                                     "Repeat a specified number\n" \
                                     "of previous transformations")
        repeatButton.clicked.connect(self.sidePanel.repeatWindow)
        repeatButton.installEventFilter(self)

        undoButton = TooltipButton("Undo",
                                   "Undo",
                                   "Undo the most recent\n" \
                                   "transformation, or delete the\n" \
                                   "object if there is none")
        undoButton.clicked.connect(self.sidePanel.undo)
        undoButton.installEventFilter(self)

        resetButton = TooltipButton("Reset current object (irreversible)",
                                    "Reset",
                                    "Reset the current object to its\n" \
                                    "default position. IRREVERSIBLE!")
        resetButton.clicked.connect(self.sidePanel.resetShape)
        resetButton.installEventFilter(self)

        deleteButton = TooltipButton("Delete current object (irreversible)",
                                     "Delete",
                                     "Delete the current object\n" \
                                     "permanently. IRREVERSIBLE!")
        deleteButton.clicked.connect(self.sidePanel.deleteShape)
        deleteButton.installEventFilter(self)
        
        showHideButton = TooltipButton("Show/Hide object",
                                       "ShowHide",
                                       "Show or hide the current\n" \
                                       "object from view")
        showHideButton.clicked.connect(self.sidePanel.showHide)
        showHideButton.installEventFilter(self)

        shearButton = TooltipButton("Shear",
                                    "Shear",
                                    "Shear the current object with\n" \
                                    "a specified invariant line,\n" \
                                    "a specified shear direction and\n" \
                                    "a specified shear factor")
        shearButton.clicked.connect(self.sidePanel.shearWindow)
        shearButton.installEventFilter(self)

        customButton = TooltipButton("Custom",
                                     "CustomMatrix",
                                     "Specify your own 4x4 affine\n" \
                                     "transformation matrix")
        customButton.clicked.connect(self.sidePanel.customMatrixWindow)
        customButton.installEventFilter(self)
        
        self.addWidget(translateButton, 0, 0)
        self.addWidget(scaleButton, 0, 1)
        self.addWidget(reflectLineButton, 1, 0)
        self.addWidget(reflectPlaneButton, 1, 1)
        self.addWidget(rotateLineButton, 2, 0)
        self.addWidget(projectPlaneButton, 2, 1)
        self.addWidget(shearButton, 3, 0)
        self.addWidget(customButton, 3, 1)
        self.addWidget(undoButton, 4, 0)
        self.addWidget(repeatButton, 4, 1)
        self.addWidget(showHideButton, 5, 0, 1, 2)
        self.addWidget(resetButton, 6, 0, 1, 2)
        self.addWidget(deleteButton, 7, 0, 1, 2)
    
    def eventFilter(self, obj, event):
        if isinstance(obj, TooltipButton):
            if event.type() == QEvent.Type.Enter:
                self.show_bubble_above_button(obj)
                return True
            elif event.type() == QEvent.Type.Leave:
                obj.tooltip.hide()
                return True
        return super().eventFilter(obj, event)

    def show_bubble_above_button(self, button):
        button_global_pos = button.mapToGlobal(QPoint(0, 0))
        
        x = button_global_pos.x() - button.tooltip.width() - 15
        y = button_global_pos.y() + (button.height() // 2) - (button.tooltip.height() // 2)
        
        button.tooltip.move(x, y)
        button.tooltip.show()

class ThreeDLinePlanePanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        objects = QWidget()
        self.objectsLayout = QVBoxLayout(objects)
        self.sidePanel = sidePanel
        self.buttons = []
        self.addWidget(QLabel())

        header = QWidget()
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(QLabel("Lines / Planes"), stretch = 100)
        addLineButton = TooltipButton("+L",
                                      "AddLine",
                                      "Add a new line by specifying\n" \
                                      "its vector equation")
        addLineButton.installEventFilter(self)
        addLineButton.setFixedWidth(30)
        addLineButton.clicked.connect(self.sidePanel.addLineWindow)
        headerLayout.addWidget(addLineButton, alignment = Qt.AlignmentFlag.AlignRight)
        addPlaneButton = TooltipButton("+P",
                                       "AddPlane",
                                       "Add a new plane by specifying\n" \
                                       "its Cartesian equation")
        addPlaneButton.installEventFilter(self)
        addPlaneButton.setFixedWidth(30)
        addPlaneButton.clicked.connect(self.sidePanel.addPlaneWindow)
        headerLayout.addWidget(addPlaneButton, alignment = Qt.AlignmentFlag.AlignRight)
        deleteButton = TooltipButton("-",
                                     "Delete",
                                     "Delete lines or planes")
        deleteButton.installEventFilter(self)
        deleteButton.setFixedWidth(20)
        deleteButton.clicked.connect(self.sidePanel.deleteLinePlaneWindow)
        headerLayout.addWidget(deleteButton, alignment = Qt.AlignmentFlag.AlignRight)
        
        header.setLayout(headerLayout)
        self.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.addWidget(scroll)
        scroll.setWidget(objects)
    
    def eventFilter(self, obj, event):
        if isinstance(obj, TooltipButton):
            if event.type() == QEvent.Type.Enter:
                self.show_bubble_above_button(obj)
                return True
            elif event.type() == QEvent.Type.Leave:
                obj.tooltip.hide()
                return True
        return super().eventFilter(obj, event)
    
    def show_bubble_above_button(self, button):
        button_global_pos = button.mapToGlobal(QPoint(0, 0))
        
        x = button_global_pos.x() - button.tooltip.width() - 15
        y = button_global_pos.y() + (button.height() // 2) - (button.tooltip.height() // 2)
        
        button.tooltip.move(x, y)
        button.tooltip.show()

    def addButton(self, obj):
        button = QCheckBox(obj.name)
        button.setChecked(True)
        button.obj = obj
        button.toggled.connect(self.onToggle)
        self.buttons.append(button)
        self.objectsLayout.addWidget(button, alignment = Qt.AlignmentFlag.AlignTop)
    
    def deleteButton(self, obj):
        for button in self.buttons:
            if button.obj == obj:
                self.buttons.pop(self.buttons.index(button))
                self.removeWidget(button)
                break
    
    def onToggle(self):
        cb = self.sender()
        if cb.isChecked():
            cb.obj.show()
        else:
            cb.obj.hide()
        self.sidePanel.viewer.update()

class ThreeDObjectPanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        objects = QWidget()
        self.objectsLayout = QVBoxLayout(objects)
        self.sidePanel = sidePanel
        self.buttons = []

        header = QWidget()
        headerLayout = QHBoxLayout()
        headerLayout.addWidget(QLabel("Objects"), stretch = 100)
        addObjectButton = TooltipButton("+",
                                        "AddShape",
                                        "Add a new 3D shape")
        addObjectButton.installEventFilter(self)
        addObjectButton.setFixedWidth(20)
        addObjectButton.clicked.connect(self.sidePanel.addShapeWindow)
        headerLayout.addWidget(addObjectButton, alignment = Qt.AlignmentFlag.AlignRight)
        viewStackButton = TooltipButton("View Matrix Stack",
                                        "MatrixStack",
                                        "View the matrix stack for the\n" \
                                        "currently selected object")
        viewStackButton.installEventFilter(self)
        viewStackButton.clicked.connect(self.sidePanel.viewStackWindow)
        headerLayout.addWidget(viewStackButton, alignment = Qt.AlignmentFlag.AlignRight)
        header.setLayout(headerLayout)
        self.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.addWidget(scroll)
        
        for obj in sidePanel.viewer.objects:
            button = QRadioButton(obj.name)
            button.obj = obj
            button.toggled.connect(self.onToggle)
            self.buttons.append(button)
            self.objectsLayout.addWidget(button, alignment = Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(objects)
    
    def eventFilter(self, obj, event):
        if isinstance(obj, TooltipButton):
            if event.type() == QEvent.Type.Enter:
                self.show_bubble_above_button(obj)
                return True
            elif event.type() == QEvent.Type.Leave:
                obj.tooltip.hide()
                return True
        return super().eventFilter(obj, event)
    
    def show_bubble_above_button(self, button):
        button_global_pos = button.mapToGlobal(QPoint(0, 0))
        
        x = button_global_pos.x() - button.tooltip.width() - 15
        y = button_global_pos.y() + (button.height() // 2) - (button.tooltip.height() // 2)
        
        button.tooltip.move(x, y)
        button.tooltip.show()
    
    def addButton(self, obj):
        button = QRadioButton(obj.name)
        button.obj = obj
        button.toggled.connect(self.onToggle)
        self.buttons.append(button)
        self.objectsLayout.addWidget(button, alignment = Qt.AlignmentFlag.AlignTop)
    
    def deleteButton(self, obj):
        for button in self.buttons:
            if button.obj == obj:
                self.buttons.pop(self.buttons.index(button))
                self.removeWidget(button)
                break
    
    def onToggle(self):
        rb = self.sender()
        if self.sidePanel.activeObj:
            self.sidePanel.activeObj.isActive = False
        if rb.isChecked():
            rb.obj.isActive = True
            self.sidePanel.activeObj = rb.obj
        else:
            self.sidePanel.activeObj = None
        self.sidePanel.viewer.update()