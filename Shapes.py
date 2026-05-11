import math, random, numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

class Shape:
    def __init__(self):
        self.type = "Shape"
        self.vertices = []
        self.edges = []
        self.surfaces = []
        self.matrixStack = [np.identity(4)]
        self.curMatrix = np.identity(4)
    
    def updateMatrix(self, matrix):
        self.matrixStack.append(matrix)
        self.curMatrix = np.matmul(matrix, self.curMatrix)
        i = 0
        for vertex in self.vertices:
            vec = np.matmul(matrix, [vertex[0], vertex[1], vertex[2], 1])
            self.vertices[i] = [vec[0], vec[1], vec[2]]
            i += 1

    def undo(self):
        # TODO: Implement a second stack to store projection matrices or other singular transformation matrices
        if len(self.matrixStack) > 1:
            self.updateMatrix(np.linalg.inv(self.matrixStack[-1]))
            self.matrixStack.pop()
            self.matrixStack.pop()
    
    def resetMatrix(self):
        while len(self.matrixStack) > 1:
            self.undo()

    def draw(self):
        print("Cannot draw generic shape; please override this method in a subclass of Shape")
        pass

    def translate(self, x, y, z):
        self.updateMatrix([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]])
        return self
    
    def reflectPlane(self, a, b, c, d):
        if a == 0 and b == 0 and c == 0:
            print("Error: Plane normal is the zero vector")
            return
        self.updateMatrix(np.array(
            [[b ** 2 + c ** 2 - a ** 2, -2 * a * b, -2 * a * c, 2 * a * d],
             [-2 * a * b, a ** 2 + c ** 2 - b ** 2, -2 * b * c, 2 * b * d],
             [-2 * a * c, -2 * b * c, a ** 2 + b ** 2 - c ** 2, 2 * c * d],
             [0, 0, 0, a ** 2 + b ** 2 + c ** 2]]) / (a ** 2 + b ** 2 + c ** 2))
        return self

    def reflectLine(self, p1, p2, p3, d1, d2, d3):
        if d1 == 0 and d2 == 0 and d3 == 0:
            print("Error: Axis is the zero vector")
            return
        L = math.sqrt(d1 * d1 + d2 * d2 + d3 * d3)
        d1, d2, d3 = d1/L, d2/L, d3/L
        c = p1 * d1 + p2 * d2 + p3 * d3
        self.updateMatrix(np.array(
            [[2 * d1 ** 2 - 1, 2 * d1 * d2, 2 * d1 * d3, 2 * (p1 - d1 * c)],
             [2 * d1 * d2, 2 * d2 ** 2 - 1, 2 * d2 * d3, 2 * (p2 - d2 * c)],
             [2 * d1 * d3, 2 * d2 * d3, 2 * d3 ** 2 - 1, 2 * (p3 - d3 * c)],
             [0, 0, 0, 1]]))
        return self

class Cube(Shape):
    def __init__(self, r):
        super().__init__()
        self.type = "Cube"
        self.r = r
        self.vertices = [[-0.5 * r, -0.5 * r, -0.5 * r],
                         [0.5 * r, -0.5 * r, -0.5 * r],
                         [-0.5 * r, 0.5 * r, -0.5 * r],
                         [0.5 * r, 0.5 * r, -0.5 * r],
                         [-0.5 * r, -0.5 * r, 0.5 * r],
                         [0.5 * r, -0.5 * r, 0.5 * r],
                         [-0.5 * r, 0.5 * r, 0.5 * r],
                         [0.5 * r, 0.5 * r, 0.5 * r]]
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
            glColor4fv((1 - i * 0.2, i * 0.2, 0.5, 0.7))
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