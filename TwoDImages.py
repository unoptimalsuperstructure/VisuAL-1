import TwoDWindows, gc
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
from Images import *

class TwoDViewer(QWidget):
    def __init__(self, initImages, res):
        super().__init__()

        self.res = res

        self.setStyleSheet("border: 2px solid black;")

        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_action)
        self.timer.setInterval(0)

        self.pressed_keys = set()

        self.lastOpStack = []

        self.images = []
        for img in initImages[::-1]:
            ext = img.name[::-1].index(".")
            img.out = img.name[:len(img.name) - ext - 1] + "-out" + img.name[len(img.name) - ext - 1:]
            self.images.append(img)
            self.lastOpStack.append([img.name])
        self.activeLayers = []
        self.layout = QVBoxLayout()
        self.topImg = QLabel()
        self.topImg.setPixmap(QPixmap())
        if self.images:
            canvas = QPixmap("static/canvas.png").scaled(self.size())
            painter = QPainter(canvas)
            for image in self.images:
                if image.show:
                    painter.drawPixmap(image.x, image.y, image.getImage())
            painter.end()
            self.topImg.setPixmap(canvas)
        self.layout.addWidget(self.topImg)
        self.setLayout(self.layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self.last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            cur_pos = event.position().toPoint()
            delta = cur_pos - self.last_mouse_pos
            self.last_mouse_pos = cur_pos
            for layer in self.activeLayers:
                layer.img.x += delta.x()
                layer.img.y += delta.y()

            self.update()
        
        if event.buttons() == Qt.MouseButton.RightButton:
            cur_pos = event.position().toPoint()
            delta = cur_pos - self.last_mouse_pos
            self.last_mouse_pos = cur_pos
            for layer in self.activeLayers:
                layer.img.size += 0.001 * delta.y()
            self.update()
    
    def mouseReleaseEvent(self, event):
        for layer in self.activeLayers:
            if layer.img.x != layer.img.posStack[-1][0] or layer.img.y != layer.img.posStack[-1][1]:
                layer.img.posStack.append([layer.img.x, layer.img.y])
            
        self.update()

    def keyPressEvent(self, event):
        self.pressZ = False
        self.pressH = False
        self.pressV = False
        if not event.isAutoRepeat():
            self.pressed_keys.add(event.key())
            self.perform_action()
            if not self.timer.isActive():
                self.timer.start()
        
    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.pressed_keys.discard(event.key())
            if not self.pressed_keys:
                self.timer.stop()
        
        if not self.pressed_keys:
            for layer in self.activeLayers:
                if layer.img.x != layer.img.posStack[-1][0] or layer.img.y != layer.img.posStack[-1][1]:
                    layer.img.posStack.append([layer.img.x, layer.img.y])
        
        self.update()

    def perform_action(self):
        if Qt.Key.Key_W in self.pressed_keys:
            for layer in self.activeLayers:
                layer.img.y -= 1
        if Qt.Key.Key_S in self.pressed_keys:
            for layer in self.activeLayers:
                layer.img.y += 1
        if Qt.Key.Key_A in self.pressed_keys:
            for layer in self.activeLayers:
                layer.img.x -= 1
        if Qt.Key.Key_D in self.pressed_keys:
            for layer in self.activeLayers:
                layer.img.x += 1
        if Qt.Key.Key_Z in self.pressed_keys:
            for layer in self.activeLayers:
                if len(layer.img.posStack) > 1 and not self.pressZ:
                    layer.img.posStack.pop()
                    layer.img.x, layer.img.y = layer.img.posStack[-1]
            self.pressZ = True
        if Qt.Key.Key_H in self.pressed_keys:
            for layer in self.activeLayers:
                if not self.pressH:
                    layer.img.stack[-1][0] = cv2.flip(layer.img.stack[-1][0], 1)
                    layer.img.original = cv2.flip(layer.img.original, 1)
            self.pressH = True
        if Qt.Key.Key_V in self.pressed_keys:
            for layer in self.activeLayers:
                if not self.pressV:
                    layer.img.stack[-1][0] = cv2.flip(layer.img.stack[-1][0], 0)
                    layer.img.original = cv2.flip(layer.img.original, 0)
            self.pressV = True
        
        self.update()

    def update(self):
        self.topImg.setPixmap(QPixmap())
        if self.images:
            canvas = QPixmap("static/canvas.png").scaled(self.size())
            painter = QPainter(canvas)
            for image in self.images:
                if image.show:
                    pixmap = image.getImage()
                    painter.drawPixmap(image.x, image.y, pixmap.scaled(int(image.ow * image.size), int(image.oh * image.size), Qt.AspectRatioMode.KeepAspectRatio))
            painter.end()
            self.topImg.setPixmap(canvas)
        self.layout.addWidget(self.topImg)
        gc.collect()
        

class TwoDSidePanel(QVBoxLayout):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.transformationPanel = TwoDTransformationPanel(self)
        self.imagePanel = TwoDImagePanel(self)
        self.namespace = []
        self.activeLayers = None

        for image in self.viewer.images:
            self.namespace.append(image.name)
    
    def select(self):
        self.activeLayers = self.imagePanel.layers.selectedItems()
        self.viewer.activeLayers = self.activeLayers if self.activeLayers else []
    
    def undo(self):
        self.viewer.update()
        if self.viewer.images and self.viewer.lastOpStack:
            toDelete = []
            for pop in self.viewer.lastOpStack.pop():
                for img in self.viewer.images:
                    if pop == img.name:
                        if img.undo(): 
                            toDelete.append(img.name)
                        break
            j = 0
            for i in range(self.imagePanel.layers.count()):
                layer = self.imagePanel.layers.item(j)
                if layer.img.name in toDelete:
                    self.viewer.images.pop(self.viewer.images.index(layer.img))
                    img = self.imagePanel.layers.takeItem(self.imagePanel.layers.row(layer))
                    del img
                    del layer
                else:
                    j += 1
            self.activeLayers = None
        self.viewer.update()
    
    def addImage(self, img):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )[0]
        if file_path:
            img = Image(file_path, self.viewer.res)
            ext_index = len(img.path) - img.path[::-1].find(".") - 1
            no_duplicates = self.namespace.count(img.name)
            self.namespace.append(img.name)
            img.out = img.path[:ext_index]
            if no_duplicates > 0:
                img.out += "-" + str(no_duplicates)
            img.out += "-" + "out" + img.path[ext_index:]
            if no_duplicates > 0:
                ext_index = len(img.name) - img.name[::-1].find(".") - 1
                img.name = img.name[:ext_index] + "-" + str(no_duplicates) + img.name[ext_index:]
            
            self.viewer.images.append(img)
            self.imagePanel.addLayer(img)
            self.viewer.lastOpStack.append([img.name])
            self.viewer.update()
    
    def deleteImage(self):
        if self.activeLayers:
            for layer in self.activeLayers:
                self.viewer.images.pop(self.viewer.images.index(layer.img))
            for layer in self.activeLayers:
                self.imagePanel.deleteLayer()
            self.activeLayers = None
            self.viewer.lastOpStack = []
        self.viewer.update()
    
    def saveImage(self):
        if self.activeLayers:
            for layer in self.activeLayers:
                file_path = QFileDialog.getSaveFileName(
                None,
                "Save...",
                layer.img.out,
                "PNG (*.png);;JPEG (*.jpeg)"
                )[0]
                if file_path:
                    layer.img.write(file_path)
    
    def showhide(self):
        if self.activeLayers:
            for layer in self.activeLayers:
                layer.img.showhide()
            self.viewer.update()
    
    def rerender(self):
        if self.activeLayers:
            for layer in self.activeLayers:
                layer.img.rerender()
            self.viewer.update()
    
    def colourWindow(self):
        self.window = TwoDWindows.ColourWindow(self.activeLayers)
        self.window.show()
        self.window.params.connect(self.colour)
    
    def colour(self, params):
        if isinstance(params[0], TwoDWindows.ErrorWindow):
            params[0].show()
        else:
            newOps = []
            if params[0] == "Colour Filter":
                for img in ColourFilter(*params[1:]).apply(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            if params[0] == "Sepia":
                for img in SepiaFilter().apply(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            self.viewer.lastOpStack.append(newOps)
        self.viewer.update()
    
    def convolutionWindow(self):
        self.window = TwoDWindows.ConvolutionWindow(self.activeLayers)
        self.window.show()
        self.window.params.connect(self.convolution)

    def convolution(self, params):
        if isinstance(params[0], TwoDWindows.ErrorWindow):
            params[0].show()
        else:
            newOps = []
            if params[0] == "Box":
                for img in BoxBlur(params[1]).apply(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            if params[0] == "Median":
                for img in MedianBlur(params[1]).apply(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            elif params[0] == "Gaussian":
                for img in GaussianBlur(params[1], params[2]).apply(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            elif params[0] == "Sharpen":
                for img in BlankConvolution().applySharpen(self.activeLayers, params[1]):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            elif params[0] == "Sobel":
                for img in BlankConvolution().applySobel(self.activeLayers):
                    for i in range(len(self.viewer.images)):
                        if self.viewer.images[i].name == img.name:
                            self.viewer.images[i] = img
                            newOps.append(img.name)
                            break
            self.viewer.lastOpStack.append(newOps)
        self.viewer.update()
            
class TwoDTransformationPanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Transformations"))
        self.sidePanel = sidePanel

        colourButton = QPushButton("Apply Colour Filter")
        colourButton.clicked.connect(self.sidePanel.colourWindow)

        convolutionButton = QPushButton("Apply Convolution")
        convolutionButton.clicked.connect(self.sidePanel.convolutionWindow)

        showhideButton = QPushButton("Show/Hide selected images")
        showhideButton.clicked.connect(self.sidePanel.showhide)

        rerenderButton = QPushButton("Re-Render Image")
        rerenderButton.clicked.connect(self.sidePanel.rerender)

        undoButton = QPushButton("Undo")
        undoButton.clicked.connect(self.sidePanel.undo)

        deleteButton = QPushButton("Delete selected images (irreversible)")
        deleteButton.clicked.connect(self.sidePanel.deleteImage)

        saveButton = QPushButton("Save selected images")
        saveButton.clicked.connect(self.sidePanel.saveImage)

        self.addWidget(colourButton)
        self.addWidget(convolutionButton)
        self.addWidget(showhideButton)
        self.addWidget(rerenderButton)
        self.addWidget(undoButton)
        self.addWidget(deleteButton)
        self.addWidget(saveButton)
    
class TwoDImagePanel(QVBoxLayout):
    def __init__(self, sidePanel):
        super().__init__()
        self.addWidget(QLabel("Images"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.addWidget(scroll)
        images = QWidget()
        self.imagesLayout = QVBoxLayout(images)
        self.sidePanel = sidePanel
        self.layers = QListWidget()
        self.layers.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layers.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.layers.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layers.itemSelectionChanged.connect(self.sidePanel.select)
        self.layers.model().rowsMoved.connect(self.update)
        for img in sidePanel.viewer.images:
            layer = QListWidgetItem(img.name)
            layer.img = img
            self.addLayer(img)
        self.imagesLayout.addWidget(self.layers, alignment = Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(images)
        addButton = QPushButton("Add new Image...")
        addButton.clicked.connect(self.sidePanel.addImage)
        self.addWidget(addButton)
        viewStackButton = QPushButton("View Matrix Stack (Coming Soon)")
        #viewStackButton.clicked.connect(self.sidePanel.viewStackWindow)
        self.addWidget(viewStackButton)

    def addLayer(self, img):
        layer = QListWidgetItem(img.name)
        layer.img = img
        self.layers.addItem(layer)
        self.update()

    def deleteLayer(self):
        if self.sidePanel.activeLayers:
            for layer in self.sidePanel.activeLayers:
                img = self.layers.takeItem(self.layers.row(layer))
                del img
                del layer
            self.update()
    
    def deleteAllLayers(self): # Only used for garbage collection when closing the window
        for layer in [self.layers.item(i) for i in range(self.layers.count())]:
            img = self.layers.takeItem(self.layers.row(layer))
            del img
            del layer
        self.update()
    
    def update(self):
        new_order = []
        for i in range(len(self.layers)):
            new_order.append(self.layers.item(i).img)
        self.sidePanel.viewer.images = new_order[::-1]
        self.sidePanel.viewer.update()