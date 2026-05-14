import math, random, numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

class Shape:
    def __init__(self):
        self.type = "Shape"
        self.isShadow = False
        self.centre = [0, 0, 0]
        self.vertices = []
        self.edges = []
        self.surfaces = []
        self.lastTransform = []
        self.lastShape = None
        self.matrixStack = [[np.identity(4), "Identity"]]
        self.curMatrix = [np.identity(4), "Identity"]
    
    def updateMatrix(self, matrix):
        if not self.isShadow:
            shapes = {"UnitCube": UnitCube}
            self.lastShape = shapes.get(self.type)()
            self.lastShape.isShadow = True
            self.lastShape.alpha = 0.1
            self.lastShape.updateMatrix(self.curMatrix)
            self.matrixStack.append(matrix)
            self.curMatrix = [np.matmul(matrix[0], self.curMatrix[0]), matrix[1]]
        i = 0
        for vertex in self.vertices:
            vec = np.matmul(matrix[0], [vertex[0], vertex[1], vertex[2], 1])
            self.vertices[i] = [vec[0], vec[1], vec[2]]
            i += 1
        self.centre = np.matmul(matrix[0], [self.centre[0], self.centre[1], self.centre[2], 1]).tolist()[:-1]

    def undo(self):
        # TODO: Implement a second stack to store projection matrices or other singular transformation matrices
        if len(self.matrixStack) > 1:
            self.updateMatrix([np.linalg.inv(self.matrixStack[-1][0]), ""])
            self.matrixStack.pop()
            self.matrixStack.pop()
        if self.lastTransform:
            self.lastTransform.pop()
    
    def resetMatrix(self):
        while len(self.matrixStack) > 1:
            self.undo()

    def draw(self):
        pass

    def translate(self, x, y, z):
        newMatrix = np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]])
        self.updateMatrix([newMatrix, "Translation"])
        orig = self.centre - np.array([x, y, z])
        self.lastTransform.append(Segment(*self.centre, *orig.tolist()))
        return self
    
    def reflectPlane(self, a, b, c, d):
        if a == 0 and b == 0 and c == 0:
            print("Error: Plane normal is the zero vector")
            return
        newMatrix = np.array(
            [[b ** 2 + c ** 2 - a ** 2, -2 * a * b, -2 * a * c, 2 * a * d],
             [-2 * a * b, a ** 2 + c ** 2 - b ** 2, -2 * b * c, 2 * b * d],
             [-2 * a * c, -2 * b * c, a ** 2 + b ** 2 - c ** 2, 2 * c * d],
             [0, 0, 0, a ** 2 + b ** 2 + c ** 2]]) / (a ** 2 + b ** 2 + c ** 2)
        self.updateMatrix([newMatrix, "Reflection about Plane"])
        self.lastTransform.append(Plane(a, b, c, d))
        return self

    def reflectLine(self, p1, p2, p3, d1, d2, d3):
        if d1 == 0 and d2 == 0 and d3 == 0:
            print("Error: Axis is the zero vector")
            return
        L = math.sqrt(d1 * d1 + d2 * d2 + d3 * d3)
        d1, d2, d3 = d1/L, d2/L, d3/L
        c = p1 * d1 + p2 * d2 + p3 * d3
        newMatrix = np.array(
            [[2 * d1 ** 2 - 1, 2 * d1 * d2, 2 * d1 * d3, 2 * (p1 - d1 * c)],
             [2 * d1 * d2, 2 * d2 ** 2 - 1, 2 * d2 * d3, 2 * (p2 - d2 * c)],
             [2 * d1 * d3, 2 * d2 * d3, 2 * d3 ** 2 - 1, 2 * (p3 - d3 * c)],
             [0, 0, 0, 1]])
        self.updateMatrix([newMatrix, "Reflection about Line"])
        self.lastTransform.append(Line(p1, p2, p3, d1, d2, d3))
        return self

class Cube(Shape):
    def __init__(self, r, x, y, z):
        super().__init__()
        self.type = "Cube"
        self.r = r
        self.alpha = 0.7
        self.centre = [x, y, z]
        self.vertices = [[-0.5 * r, -0.5 * r, -0.5 * r],
                         [0.5 * r, -0.5 * r, -0.5 * r],
                         [-0.5 * r, 0.5 * r, -0.5 * r],
                         [0.5 * r, 0.5 * r, -0.5 * r],
                         [-0.5 * r, -0.5 * r, 0.5 * r],
                         [0.5 * r, -0.5 * r, 0.5 * r],
                         [-0.5 * r, 0.5 * r, 0.5 * r],
                         [0.5 * r, 0.5 * r, 0.5 * r]]
        for vertex in self.vertices:
            vertex[0] += x
            vertex[1] += y
            vertex[2] += z
        self.edges = [[0, 1],
                      [0, 2],
                      [0, 4],
                      [3, 1],
                      [3, 2],
                      [3, 7],
                      [5, 1],
                      [5, 4],
                      [5, 7],
                      [6, 2],
                      [6, 4],
                      [6, 7]]
        self.surfaces = [(0, 1, 3, 2),
                         (4, 5, 7, 6),
                         (0, 1, 5, 4),
                         (2, 3, 7, 6),
                         (0, 2, 6, 4),
                         (1, 3, 7, 5)]
    
    def draw(self):
        glBegin(GL_QUADS)
        i = 0
        for surface in self.surfaces:
            glColor4fv((1 - i * 0.2, i * 0.2, 0.5, self.alpha))
            for vertex in surface:
                glVertex3fv(self.vertices[vertex])
            i += 1
        glEnd()
    
        glBegin(GL_LINES)
        for edge in self.edges:
            if edge == (0, 8):
                glColor4fv((0, 0, 0, 0))
                for vertex in edge:
                    glVertex3fv(self.vertices[vertex])
        glEnd()

class UnitCube(Cube):
    def __init__(self):
        super().__init__(1, 0, 0, 0)
        self.type = "UnitCube"

def drawAxes():
    plane_points = [[-10, -10, 0],
                    [-10, 10, 0],
                    [10, 10, 0],
                    [10, -10, 0]]
    
    plane_edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    
    glBegin(GL_QUADS)
    for edge in plane_edges:
        for vertex in edge:
            glColor4fv((0.7, 0.7, 0.7, 0.7))
            glVertex3fv(plane_points[vertex])
    glEnd()

    axe_points = [[-100, 0, 0],
                  [100, 0, 0],
                  [0, -100, 0],
                  [0, 100, 0],
                  [0, 0, -100],
                  [0, 0, 100]]
    
    glBegin(GL_LINES)
    glColor3fv((1, 0, 0))
    glVertex3fv(axe_points[0])
    glVertex3fv(axe_points[1])
    glColor3fv((0, 1, 0))
    glVertex3fv(axe_points[2])
    glVertex3fv(axe_points[3])
    glColor3fv((0, 0, 1))
    glVertex3fv(axe_points[4])
    glVertex3fv(axe_points[5])
    glEnd()

class Line(Shape):
    def __init__(self, a1, a2, a3, d1, d2, d3):
        super().__init__()
        self.type = "Line"
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
    
    def draw(self):
        glBegin(GL_LINES)
        glColor3fv((1, 1, 1))
        glVertex3fv([self.a1 - 500 * self.d1, self.a2 - 500 * self.d2, self.a3 - 500 * self.d3])
        glVertex3fv([self.a1 + 500 * self.d1, self.a2 + 500 * self.d2, self.a3 + 500 * self.d3])
        glEnd()

class Segment(Shape):
    def __init__(self, a1, a2, a3, b1, b2, b3):
        super().__init__()
        self.type = "Segment"
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
    
    def draw(self):
        glBegin(GL_LINES)
        glColor3fv((1, 1, 1))
        glVertex3fv([self.a1, self.a2, self.a3])
        glVertex3fv([self.b1, self.b2, self.b3])
        glEnd()

class Plane(Shape):
    def __init__(self, a, b, c, d):
        super().__init__()
        self.type = "Line"
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
    def draw(self):
        if self.a != 0 and self.b != 0:
            perp1 = [1, -self.a/self.b, 0]
        else:
            perp1 = [int(self.a == 0), int(self.b == 0), int(self.c == 0)]
        normal = np.array([self.a, self.b, self.c])
        pt = normal * self.d/(np.linalg.norm(normal) ** 2)
        normal = normal/np.linalg.norm(normal)
        perp1 = np.array(perp1)/np.linalg.norm(perp1)
        perp2 = np.cross(normal, perp1)
        perp1 = 5 * perp1
        perp2 = 5 * perp2
        plane_points = [[pt[0] - perp1[0] - perp2[0], pt[1] - perp1[1] - perp2[1], pt[2] - perp1[2] - perp2[2]],
                        [pt[0] - perp1[0] + perp2[0], pt[1] - perp1[1] + perp2[1], pt[2] - perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] + perp2[0], pt[1] + perp1[1] + perp2[1], pt[2] + perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] - perp2[0], pt[1] + perp1[1] - perp2[1], pt[2] + perp1[2] - perp2[2]]]
    
        plane_edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    
        glBegin(GL_QUADS)
        for edge in plane_edges:
            for vertex in edge:
                glColor4fv((0.7, 0.7, 0.7, 0.7))
                glVertex3fv(plane_points[vertex])
        glEnd()