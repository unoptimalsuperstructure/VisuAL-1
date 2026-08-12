import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtGui import QPixmap
import cv2, qimage2ndarray
import gc

dic = {1: (560, 420), 2: (720, 540), 3: (960, 540), 4: (1600, 900)}

class Image:
    def __init__(self, path, res):
        self.original = cv2.imread(path, -1)
        h, w = self.original.shape[:2]
        if w > dic[res][0] or h > dic[res][1]:
            self.ow, self.oh = int(min(dic[res][0], dic[res][1] * w/h)), int(min(dic[res][1], dic[res][0] * h/w))
        else:
            self.ow, self.oh = w, h
        self.image = cv2.resize(self.original, (self.ow, self.oh))
        self.path = str(path)
        name1 = self.path.split("/")[-1]
        name2 = self.path.split("\\")[-1]
        self.name = name1 if len(name1) < len(name2) else name2
        self.out = ""
        
        self.channels = self.image.shape[2] if len(self.image.shape) == 3 else 1
        self.original = self.original if self.channels == 4 else cv2.cvtColor(self.original, cv2.COLOR_BGR2BGRA) if self.channels == 3 else cv2.cvtColor(self.original, cv2.COLOR_GRAY2BGRA)
        self.const = cv2.COLOR_BGRA2RGBA if self.channels == 4 else cv2.COLOR_BGR2RGBA if self.channels == 3 else cv2.COLOR_GRAY2RGBA
        self.stack = [[self.image, self.channels, Filter(np.array([[1, 0, 0, 0, 0],
                                                                   [0, 1, 0, 0, 0],
                                                                   [0, 0, 1, 0, 0],
                                                                   [0, 0, 0, 1, 0]]), "Identity")]]
        self.matrixStack = [[np.array([[1, 0, 0, 0, 0],
                                      [0, 1, 0, 0, 0],
                                      [0, 0, 1, 0, 0],
                                      [0, 0, 0, 1, 0]]), "Identity"]]
        self.show = True
        self.x = 0
        self.y = 0
        self.size = 1
        self.posStack = [[0, 0]]
    
    def getImage(self):
        return QPixmap.fromImage(qimage2ndarray.array2qimage(cv2.cvtColor(np.uint8(self.stack[-1][0]), self.const)))
    
    def write(self, path):
        temp = self.original.copy()
        for op in self.stack:
            if isinstance(op[2], Filter) or isinstance(op[2], Convolution):
                temp = op[2].applyToRawImage(temp)
            elif isinstance(op[2], IndividualConvolution): # Non-standard convolution such as Sobel or unmasked sharpening
                if isinstance(op[2], Compress):
                    channels = temp.shape[2] if len(temp.shape) == 3 else 1
                    if channels == 1:
                        temp = op[2].get(temp)
                    elif channels == 3:
                        b, g, r = cv2.split(temp)
                        b = op[2].get(b)
                        g = op[2].get(g)
                        r = op[2].get(r)
                        temp = cv2.merge([b, g, r])
                    else:
                        b, g, r, a = cv2.split(temp)
                        b = op[2].get(b)
                        g = op[2].get(g)
                        r = op[2].get(r)
                        a = a.astype(np.uint8)
                        temp = cv2.merge([b, g, r, a])
                else:
                    temp = op[2].get(temp)
                if isinstance(temp, tuple):
                    temp = temp[0]
            elif isinstance(op[2], list) and op[2][0] == "Crop":
                h, w = self.original.shape[:2]
                params = []
                for j in range(4):
                    params.append(int(op[2][1][j] * (w if j < 2 else h)))
                temp = temp[params[0]:params[1],params[2]:params[3]]
        temp = temp.astype(np.uint8)
        cv2.imwrite(path, temp)
    
    def undo(self):
        self.stack.pop()
        if self.matrixStack:
            self.matrixStack.pop()
        return len(self.stack) == 0
    
    def showhide(self):
        self.show = not self.show
    
    def rerender(self):
        self.image = cv2.resize(self.original, (int(self.size * self.ow), int(self.size * self.oh)))
        self.oh *= self.size
        self.ow *= self.size
        self.size = 1
        tempStack = self.stack.copy()
        self.stack = [tempStack[0]]
        self.stack[0][0] = self.image
        i = 0
        for op in tempStack:
            if (isinstance(op[2], list)) and op[2][0] == "Crop":
                params = []
                for j in range(4):
                    params.append(int(op[2][1][j] * (self.ow if j < 2 else self.oh)))
                self.image = self.crop(params, False)
            else:
                try:
                    self.image = op[2].applyToRawImage(self.image).astype(np.float32)
                except:
                    operation = op[2].get(self.image)
                    if isinstance(operation, tuple):
                        self.image = operation[0].astype(np.float32)
                    else:
                        self.image = operation.astype(np.float32)
            self.stack.append([self.image, tempStack[i][1], tempStack[i][2]])
            i += 1
        del tempStack
        gc.collect()
    
    def crop(self, params, append):
        img = self.stack[-1].copy()
        if params[0] > params[1]:
            params[0], params[1] = params[1], params[0]
        if params[2] > params[3]:
            params[2], params[3] = params[3], params[2]
        img[2] = ["Crop", [params[0]/img[0].shape[1], params[1]/img[0].shape[1], params[2]/img[0].shape[0], params[3]/img[0].shape[0]]]
        img[0] = img[0][params[0]:params[1],params[2]:params[3]]
        if append:
            self.stack.append(img)
            self.matrixStack.append([None, "Crop"])
        return img[0]

class Filter:
    def __init__(self, matrix, name):
        self.matrix = matrix
        self.name = name
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
            layer.img.matrixStack.append([self.matrix, self.name])
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

class GrayscaleFilter(Filter):
    def __init__(self, v):
        super().__init__(np.array([[0.2126, 0.7152, 0.0722, 0, 0],
                                   [0.2126, 0.7152, 0.0722, 0, 0],
                                   [0.2126, 0.7152, 0.0722, 0, 0],
                                   [0, 0, 0, 1, 0]]) * v +
                        
                         np.array([[1, 0, 0, 0, 0],
                                   [0, 1, 0, 0, 0],
                                   [0, 0, 1, 0, 0],
                                   [0, 0, 0, 1, 0]]) * (1 - v), f"Grayscale ({100 * v}%)")

class SepiaFilter(Filter):
    def __init__(self, v):
        super().__init__(np.array([[0.131, 0.534, 0.272, 0, 0],
                                   [0.168, 0.686, 0.349, 0, 0],
                                   [0.189, 0.769, 0.393, 0, 0],
                                   [0, 0, 0, 1, 0]]) * v +
                        
                         np.array([[1, 0, 0, 0, 0],
                                   [0, 1, 0, 0, 0],
                                   [0, 0, 1, 0, 0],
                                   [0, 0, 0, 1, 0]]) * (1 - v), f"Sepia ({100 * v}%)")

class InversionFilter(Filter):
    def __init__(self, v):
        super().__init__(np.array([[-1, 0, 0, 0, 255],
                                   [0, -1, 0, 0, 255],
                                   [0, 0, -1, 0, 255],
                                   [0, 0, 0, 1, 0]]) * v +
                        
                         np.array([[1, 0, 0, 0, 0],
                                   [0, 1, 0, 0, 0],
                                   [0, 0, 1, 0, 0],
                                   [0, 0, 0, 1, 0]]) * (1 - v), f"Inversion ({100 * v}%)")

# TODO
"""class TransparencyFilter(Filter):
    def __init__(self):
        super().__init__(np.array([[0.131]]))"""

class ColourFilter(Filter):
    def __init__(self, relR, relG, relB, relA, absR, absG, absB, absA):
        super().__init__(np.array([[relB, 0, 0, 0, absB],
                                   [0, relG, 0, 0, absG],
                                   [0, 0, relR, 0, absR],
                                   [0, 0, 0, relA, absA]]), "Colour Filter")

class ColourRotation(Filter):
    def __init__(self, rotation):
        colourDict = {"RGB": np.array([[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0]]),
                      "RBG": np.array([[1, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 1, 0]]),
                      "GRB": np.array([[0, 1, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0]]),
                      "GBR": np.array([[0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 1, 0]]),
                      "BRG": np.array([[0, 0, 1, 0, 0], [1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 1, 0]]),
                      "BGR": np.array([[0, 0, 1, 0, 0], [0, 1, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 1, 0]])}
        super().__init__(colourDict[rotation], "Colour Rotation")

class Convolution:
    def __init__(self, type, params, name):
        self.type = type
        self.params = params
        self.name = name
        self.matrix = None
        self.result = []
    
    def apply(self, layers):
        for layer in layers:
            layer.img.stack[-1][0] = layer.img.stack[-1][0].astype(np.uint8)
            layer.img.stack.append([self.type(layer.img.stack[-1][0], *self.params), layer.img.channels, self])
            layer.img.stack[-1][0] = layer.img.stack[-1][0].astype(np.float32)
            layer.img.matrixStack.append([self.matrix, self.name])
            self.result.append(layer.img)
        return self.result
    
    def applyPixelate(self, layers, v):
        for layer in layers:
            pixelate = Pixelate(v)
            layer.img.stack.append([pixelate.get(layer.img.stack[-1][0]), layer.img.channels, pixelate])
            self.result.append(layer.img)
            layer.img.matrixStack.append([self.matrix, self.name])
        return self.result

    def applySobel(self, layers):
        for layer in layers:
            sobel = Sobel()
            layer.img.stack.append([sobel.get(layer.img.stack[-1][0]), layer.img.channels, sobel])
            self.result.append(layer.img)
            layer.img.matrixStack.append([self.matrix, self.name])
        return self.result
    
    def applySharpen(self, layers, v):
        for layer in layers:
            sharpen = Sharpen(v)
            layer.img.stack.append([sharpen.get(layer.img.stack[-1][0]), layer.img.channels, sharpen])
            self.result.append(layer.img)
            layer.img.matrixStack.append([self.matrix, self.name])
        return self.result
    
    def applyCompression(self, layers, v):
        for layer in layers:
            compress = Compress(v)
            image = layer.img.stack[-1][0]
            if layer.img.channels == 1:
                layer.img.stack.append([compress.get(layer.img.stack[-1][0]), 1, compress])
            elif layer.img.channels == 3:
                try:
                    b, g, r = cv2.split(image)
                except:
                    b, g, r, a = cv2.split(image)
                b = compress.get(b)
                g = compress.get(g)
                r = compress.get(r)
                layer.img.stack.append([cv2.merge([b, g, r]), 3, compress])
            else:
                b, g, r, a = cv2.split(image)
                b = compress.get(b)
                g = compress.get(g)
                r = compress.get(r)
                a = a.astype(np.uint8)
                layer.img.stack.append([cv2.merge([b, g, r, a]), 4, compress])
            
            self.result.append(layer.img)
            layer.img.matrixStack.append([self.matrix, self.name])
        return self.result
    
    def applyCustom(self, layers, matrix, n):
        for layer in layers:
            custom = Custom(matrix, n)
            res, self.matrix = custom.get(layer.img.stack[-1][0])
            layer.img.stack.append([res, layer.img.channels, custom])
            self.result.append(layer.img)
            self.name = "Custom Convolution (" + (f"order-{n} approximation)" if n < np.linalg.matrix_rank(matrix) else "exact)")
            layer.img.matrixStack.append([self.matrix, self.name])
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
    def __init__(self, name):
        super().__init__(None, [], name)
        self.matrix = None

class BoxBlur(Convolution):
    def __init__(self, r):
        super().__init__(cv2.blur, [(2 * r + 1, 2 * r + 1)], f"Box Blur (radius {r})")
        self.matrix = np.ones((2 * r + 1, 2 * r + 1))/(4 * (r ** 2) + 4 * r + 1)

class MedianBlur(Convolution):
    def __init__(self, r):
        super().__init__(cv2.medianBlur, [2 * r + 1], f"Median Blur (radius {r})")

class GaussianBlur(Convolution):
    def __init__(self, r, sd):
        super().__init__(cv2.GaussianBlur, [(2 * r + 1, 2 * r + 1), sd], f"Gaussian Blur (radius {r}, SD {sd})")
        x = np.arange(-r, r + 1)
        g = g = np.exp(-(x**2) / (2 * sd**2))
        g /= g.sum()
        self.matrix = np.outer(g, g)

class IndividualConvolution:
    def __init__(self, params):
        self.params = params

class Pixelate(IndividualConvolution):
    def __init__(self, v):
        super().__init__([v])
        
    def get(self, image):
        h, w = image.shape[:2]
        size = int(max(h, w) / self.params[0])
        temp = cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
        return pixelated

class Sharpen(IndividualConvolution):
    def __init__(self, v):
        super().__init__([v])
        
    def get(self, image):
        v = self.params[0]
        blurred = cv2.GaussianBlur(image, (7, 7), 1)
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

class Compress(IndividualConvolution):
    def __init__(self, v):
        super().__init__([v])
    
    def get(self, image):
        quality = self.params[0]
        image = image.astype(np.float32)
        if len(image.shape) == 3:
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        u, sigma, v = np.linalg.svd(image)
        evrArray = np.cumsum(sigma)
        i = 0
        while i < len(evrArray):
            if evrArray[i] / evrArray[-1] > quality:
                break
            i += 1
        uk = u[:, :i + 1]
        sk = np.diag(sigma[:i + 1])
        vk = v[:i + 1, :]
        return np.clip(np.dot(uk, np.dot(sk, vk)), 0, 255).astype(np.uint8)

class Custom(IndividualConvolution):
    def __init__(self, matrix, n):
        super().__init__([matrix, n])
    
    def get(self, image):
        image = image.astype(np.float32)
        matrix, n = self.params
        u, sigma, v = np.linalg.svd(matrix)

        if n == np.linalg.matrix_rank(matrix):
            return np.clip(cv2.filter2D(image, -1, matrix), 0, 255).astype(np.uint8), matrix
        
        else:
            matrix = np.zeros_like(matrix, np.float32)
            for i in range(n):
                matrix += sigma[i] * np.outer(u.T[i], v[i])

        return np.clip(cv2.filter2D(image, -1, matrix), 0, 255).astype(np.uint8), matrix