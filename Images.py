import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtGui import QPixmap
import cv2, qimage2ndarray

class Image:
    def __init__(self, path):
        self.original = cv2.imread(path, -1)
        h, w = self.original.shape[:2]
        self.image = cv2.resize(self.original, (int(min(800, 600 * w/h)), int(min(600, 800 * h/w))))
        self.path = path
        self.name = path.split("/")[-1]
        self.out = ""
        
        self.channels = self.image.shape[2] if len(self.image.shape) == 3 else 1
        self.original = self.original if self.channels == 4 else cv2.cvtColor(self.original, cv2.COLOR_BGR2BGRA) if self.channels == 3 else cv2.cvtColor(self.original, cv2.COLOR_GRAY2BGRA)
        self.const = cv2.COLOR_BGRA2RGBA if self.channels == 4 else cv2.COLOR_BGR2RGBA if self.channels == 3 else cv2.COLOR_GRAY2RGBA
        self.stack = [[self.image, self.channels, Filter(np.array([[1, 0, 0, 0, 0],
                                                                   [0, 1, 0, 0, 0],
                                                                   [0, 0, 1, 0, 0],
                                                                   [0, 0, 0, 1, 0]]))]]
        self.matrixStack = []
        self.show = True
        self.x = 0
        self.y = 0
        self.posStack = [[0, 0]]
    
    def getImage(self):
        return QPixmap.fromImage(qimage2ndarray.array2qimage(cv2.cvtColor(self.stack[-1][0], self.const)))
    
    def write(self, path):
        temp = self.original.copy()
        for op in self.stack:
            if isinstance(op[2], Filter) or isinstance(op[2], Convolution):
                temp = op[2].applyToRawImage(temp)
            elif isinstance(op[2], IndividualConvolution): # Non-standard convolution such as Sobel or unmasked sharpening
                temp = op[2].get(temp)
        temp = temp.astype(np.uint8)
        cv2.imwrite(path, temp)
    
    def undo(self):
        self.stack.pop()
        if self.matrixStack:
            self.matrixStack.pop()
        return len(self.stack) == 0
    
    def showhide(self):
        self.show = not self.show

class Filter:
    def __init__(self, matrix):
        self.matrix = matrix
        self.result = []
    
    def apply(self, layers):
        for layer in layers:
            image, channels = layer.img.stack[-1][:2]
            if channels == 1:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
            elif channels == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            image = image.astype(np.float32)
            h, w = image.shape[:2]
            image = image.reshape(-1, 4)
            image = np.column_stack([image, np.ones(h * w)])
            image = np.dot(image, self.matrix.T)
            image = np.clip(image, 0, 255)
            layer.img.stack.append([image.reshape(h, w, 4).astype(np.uint8), channels, self])
            self.result.append(layer.img)
        return self.result
    
    def applyToRawImage(self, image): # Only used for saving operations on raw images without the image wrapper
        channels = image.shape[2] if len(image.shape) == 3 else 1
        if channels == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
        elif channels == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        image = image.astype(np.float32)
        h, w = image.shape[:2]
        image = image.reshape(-1, 4)
        image = np.column_stack([image, np.ones(h * w)])
        image = np.dot(image, self.matrix.T)
        image = np.clip(image, 0, 255)
        image = image.reshape(h, w, 4)
        return image

class SepiaFilter(Filter):
    def __init__(self):
        super().__init__(np.array([[0.131, 0.534, 0.272, 0, 0],
                                   [0.168, 0.686, 0.349, 0, 0],
                                   [0.189, 0.769, 0.393, 0, 0],
                                   [0, 0, 0, 1, 0]]))

# TODO
"""class TransparencyFilter(Filter):
    def __init__(self):
        super().__init__(np.array([[0.131]]))"""

class ColourFilter(Filter):
    def __init__(self, relR, relG, relB, relA, absR, absG, absB, absA):
        super().__init__(np.array([[relB, 0, 0, 0, absB],
                                   [0, relG, 0, 0, absG],
                                   [0, 0, relR, 0, absR],
                                   [0, 0, 0, relA, absA]]))

class Convolution:
    def __init__(self, type, params):
        self.type = type
        self.params = params
        self.matrix = []
        self.result = []
    
    def apply(self, layers):
        for layer in layers:
            layer.img.stack.append([self.type(layer.img.stack[-1][0], *self.params), layer.img.channels, self])
            self.result.append(layer.img)
        return self.result
    
    def applySobel(self, layers):
        for layer in layers:
            sobel = Sobel()
            layer.img.stack.append([sobel.get(layer.img.stack[-1][0]), 4, sobel])
            self.result.append(layer.img)
        return self.result
    
    def applySharpen(self, layers, v):
        for layer in layers:
            sharpen = Sharpen(v)
            layer.img.stack.append([sharpen.get(layer.img.stack[-1][0]), 4, sharpen])
            self.result.append(layer.img)
        return self.result
    
    def applyToRawImage(self, image): # Only used for saving operations on raw images without the image wrapper
        try:
            return self.type(image, *self.params)
        except: # Some convolutions such as median blur only work with unsigned 8-bit integers
            image = image.astype(np.uint8)
            image = self.type(image, *self.params)
            image = image.astype(np.float32)
            return image
    
    def undo(self, images):
        for img in images:
            img.stack.pop()
            if not img.stack:
                del img

class BlankConvolution(Convolution):
    def __init__(self):
        super().__init__(None, [])

class BoxBlur(Convolution):
    def __init__(self, r):
        super().__init__(cv2.blur, [(2 * r + 1, 2 * r + 1)])

class MedianBlur(Convolution):
    def __init__(self, r):
        super().__init__(cv2.medianBlur, [2 * r + 1])

class GaussianBlur(Convolution):
    def __init__(self, r, sd):
        super().__init__(cv2.GaussianBlur, [(2 * r + 1, 2 * r + 1), sd])

class IndividualConvolution:
    def __init__(self, params):
        self.params = params

class Sharpen(IndividualConvolution):
    def __init__(self, v):
        super().__init__([v])
        
    def get(self, image):
        v = self.params[0]
        blurred = cv2.GaussianBlur(image, (11, 11), 50)
        sharpened = cv2.addWeighted(image, v + 1, blurred, -v, 0)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        return sharpened

class Sobel(IndividualConvolution):
    def __init__(self):
        super().__init__([])

    def get(self, image):
        channels = image.shape[2] if len(image.shape) == 3 else 1
        image = image.astype(np.uint8)
        if channels == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif channels == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sobelX = cv2.Sobel(image, cv2.CV_32F, 1, 0, 3)
        sobelY = cv2.Sobel(image, cv2.CV_32F, 1, 0, 3)
        d = np.sqrt(sobelX ** 2 + sobelY ** 2)
        bwImg = (d * 255 / d.max()).astype(np.uint8)
        h, w = bwImg.shape[:2]
        rgba = np.zeros((h, w, 4), dtype=np.uint8)

        rgba[:, :, 0] = 0  # Blue
        rgba[:, :, 1] = 0  # Green
        rgba[:, :, 2] = 0  # Red
        rgba[:, :, 3] = bwImg
        return rgba