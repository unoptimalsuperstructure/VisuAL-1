import math, random, numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

class Shape:
    def __init__(self):
        global shapes
        shapes = {"UnitCube": UnitCube, "UnitTetrahedron": UnitTetrahedron}
        self.type = "Shape"
        self.isShadow = False
        self.initVertices = []
        self.vertices = []
        self.edges = []
        self.surfaces = []
        self.singularMatrixStack = []
        self.matrixStack = [[np.identity(4), "Identity", Shadow()]]
        self.curMatrix = [np.identity(4), "Identity", Shadow()]
    
    def getShadow(self):
        if self.matrixStack:
            return self.matrixStack[-1][2]
        else:
            return None
    
    def updateMatrix(self, matrix, redrawEdges):
        i = 0
        for vertex in self.vertices:
            vec = np.matmul(matrix[0], [vertex[0], vertex[1], vertex[2], 1])
            self.vertices[i] = [vec[0], vec[1], vec[2]]
            i += 1
        if not self.isShadow:
            lastShape = shapes.get(self.type)()
            lastShape.alpha = 0.1
            lastShape.isShadow = True
            lastShape.updateMatrix(self.curMatrix, False)
            if float(abs(np.linalg.det(matrix[0]))) < 0.00001:
                self.singularMatrixStack.append(self.curMatrix)
            if redrawEdges:
                for i in range(len(self.vertices)):
                    matrix[2].append(*self.vertices[i], *lastShape.vertices[i])
                matrix[2].lastShape = lastShape
            self.matrixStack.append(matrix)
            self.curMatrix = [np.matmul(matrix[0], self.curMatrix[0]), matrix[1], matrix[2]]

    def repeat(self):
        if len(self.matrixStack) > 1:
            lastOp = self.matrixStack[-1].copy()
            if lastOp[1] in ["Identity", "Translation", "Scaling"]:
                lastOp[2] = Shadow()
            else:
                lastOp[2] = lastOp[2].copy()
                lastOp[2].segments = []
                lastOp[2].lastShape = Shape()
            self.updateMatrix(lastOp, True)
    
    def undo(self):
        if len(self.matrixStack) > 1:
            topMatrix = self.matrixStack[-1]
            if float(abs(np.linalg.det(topMatrix[0]))) < 0.00001:
                self.curMatrix = self.singularMatrixStack.pop()
                i = 0
                for vertex in self.initVertices:
                    vec = np.matmul(self.curMatrix[0], [vertex[0], vertex[1], vertex[2], 1])
                    self.vertices[i] = [vec[0], vec[1], vec[2]]
                    i += 1
            else:
                self.updateMatrix([np.linalg.inv(topMatrix[0]), "", Shadow()], False)
                self.matrixStack.pop()
            self.matrixStack.pop()
    
    def resetMatrix(self):
        while len(self.matrixStack) > 1:
            self.undo()

    def draw(self):
        pass

    def translate(self, x, y, z):
        if not (x == 0 and y == 0 and z == 0):
            newMatrix = np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]])
            self.updateMatrix([newMatrix, "Translation", Shadow()], True)
            return Shadow()
        return
    
    def reflectPlane(self, a, b, c, d):
        if a == 0 and b == 0 and c == 0:
            print("Error: Plane normal is the zero vector")
            return
        newMatrix = np.array(
            [[b ** 2 + c ** 2 - a ** 2, -2 * a * b, -2 * a * c, 2 * a * d],
             [-2 * a * b, a ** 2 + c ** 2 - b ** 2, -2 * b * c, 2 * b * d],
             [-2 * a * c, -2 * b * c, a ** 2 + b ** 2 - c ** 2, 2 * c * d],
             [0, 0, 0, a ** 2 + b ** 2 + c ** 2]]) / (a ** 2 + b ** 2 + c ** 2)
        shadow = Shadow()
        shadow.addPlane(Plane(a, b, c, d))
        self.updateMatrix([newMatrix, "Reflection about Plane", shadow], True)
        return shadow

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
        shadow = Shadow()
        shadow.addLine(Line(p1, p2, p3, d1, d2, d3))
        self.updateMatrix([newMatrix, "Reflection about Line", shadow], True)
        return shadow
    
    def rotateLine(self, p1, p2, p3, d1, d2, d3, r):
        if r % 360 == 0 or d1 == 0 and d2 == 0 and d3 == 0:
            print("Error: Rotation angle is 0 or axis is the zero vector")
            return
        L = math.sqrt(d1 * d1 + d2 * d2 + d3 * d3)
        d1, d2, d3 = d1/L, d2/L, d3/L
        r *= math.pi/180
        R1 = (1 - math.cos(r)) * d1 * d1 + math.cos(r)
        R2 = (1 - math.cos(r)) * d1 * d2 - d3 * math.sin(r)
        R3 = (1 - math.cos(r)) * d1 * d3 + d2 * math.sin(r)
        R4 = (1 - math.cos(r)) * d1 * d2 + d3 * math.sin(r)
        R5 = (1 - math.cos(r)) * d2 * d2 + math.cos(r)
        R6 = (1 - math.cos(r)) * d2 * d3 - d1 * math.sin(r)
        R7 = (1 - math.cos(r)) * d1 * d3 - d2 * math.sin(r)
        R8 = (1 - math.cos(r)) * d2 * d3 + d1 * math.sin(r)
        R9 = (1 - math.cos(r)) * d3 * d3 + math.cos(r)
        newMatrix = np.array(
            [[R1, R2, R3, p1 - (R1 * p1 + R2 * p2 + R3 * p3)],
             [R4, R5, R6, p2 - (R4 * p1 + R5 * p2 + R6 * p3)],
             [R7, R8, R9, p3 - (R7 * p1 + R8 * p2 + R9 * p3)],
             [0, 0, 0, 1]])
        shadow = Shadow()
        shadow.addLine(Line(p1, p2, p3, d1, d2, d3))
        self.updateMatrix([newMatrix, "Rotation about Line", shadow], True)
        return shadow
    
    def projectPlane(self, a, b, c, d):
        if a == 0 and b == 0 and c == 0:
            print("Error: Plane normal is the zero vector")
            return
        L = math.sqrt(a ** 2 + b ** 2 + c ** 2)
        a, b, c, d = a/L, b/L, c/L, d/L
        newMatrix = np.array(
            [[1 - a ** 2, -a * b, -a * c, a * d],
             [-a * b, 1 - b ** 2, -b * c, b * d],
             [-a * c, -b * c, 1 - c ** 2, c * d],
             [0, 0, 0, 1]])
        shadow = Shadow()
        shadow.addPlane(Plane(a, b, c, d))
        self.updateMatrix([newMatrix, "Projection onto Plane", shadow], True)
        return shadow
    
    def scale(self, c):
        if c <= 0 or c == 1:
            return
        centre = self.vertices[-1]
        newMatrix = np.array([[c, 0, 0, (1 - c)*centre[0]], [0, c, 0, (1 - c)*centre[1]], [0, 0, c, (1 - c)*centre[2]], [0, 0, 0, 1]])
        self.updateMatrix([newMatrix, "Scaling", Shadow()], True)
        return Shadow()

class Cube(Shape):
    def __init__(self, r, x, y, z):
        super().__init__()
        self.type = "Cube"
        self.r = r
        self.alpha = 0.7
        self.initVertices = [[-0.5 * r, -0.5 * r, -0.5 * r],
                         [0.5 * r, -0.5 * r, -0.5 * r],
                         [-0.5 * r, 0.5 * r, -0.5 * r],
                         [0.5 * r, 0.5 * r, -0.5 * r],
                         [-0.5 * r, -0.5 * r, 0.5 * r],
                         [0.5 * r, -0.5 * r, 0.5 * r],
                         [-0.5 * r, 0.5 * r, 0.5 * r],
                         [0.5 * r, 0.5 * r, 0.5 * r],
                         [0, 0, 0]]
        for vertex in self.initVertices:
            vertex[0] += x
            vertex[1] += y
            vertex[2] += z
        self.vertices = self.initVertices.copy()
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

class UnitCube(Cube):
    def __init__(self):
        super().__init__(1, 0, 0, 0)
        self.type = "UnitCube"

class Tetrahedron(Shape):
    def __init__(self, r, x, y, z):
        super().__init__()
        self.type = "Tetrahedron"
        self.r = r
        self.alpha = 0.7
        self.initVertices = [[-0.5 * r, -math.sqrt(3)/6 * r, -math.sqrt(6)/9 * r],
                         [0.5 * r, -math.sqrt(3)/6 * r, -math.sqrt(6)/9 * r],
                         [0, math.sqrt(3)/3 * r, -math.sqrt(6)/9 * r],
                         [0, 0, 2 * math.sqrt(6)/9 * r],
                         [0, 0, 0]]
        for vertex in self.initVertices:
            vertex[0] += x
            vertex[1] += y
            vertex[2] += z
        self.vertices = self.initVertices.copy()
        self.edges = [[0, 1],
                      [0, 2],
                      [0, 3],
                      [1, 2],
                      [1, 3],
                      [2, 3]]
        self.surfaces = [(0, 1, 2),
                         (0, 1, 3),
                         (0, 2, 3),
                         (1, 2, 3)]
    
    def draw(self):
        glBegin(GL_QUADS)
        i = 0
        for surface in self.surfaces:
            glColor4fv((1 - i / 3, i / 3, 0.5, self.alpha))
            for vertex in surface:
                glVertex3fv(self.vertices[vertex])
            i += 1
        glEnd()

class UnitTetrahedron(Tetrahedron):
    def __init__(self):
        super().__init__(1, 0, 0, 0)
        self.type = "UnitTetrahedron"

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

class Shadow:
    def __init__(self):
        self.segments = []
        self.lines = []
        self.planes = []
        self.lastShape = None
    
    def append(self, a1, a2, a3, b1, b2, b3):
        self.segments.append([[a1, a2, a3], [b1, b2, b3]])
    
    def addLine(self, line):
        self.lines.append(line)
    
    def addPlane(self, plane):
        self.planes.append(plane)
    
    def copy(self):
        temp = Shadow()
        temp.segments = self.segments
        temp.lines = self.lines
        temp.planes = self.planes
        return temp
    
    def draw(self):
        if self.lastShape:
            self.lastShape.draw()
        glBegin(GL_LINES)
        glColor4fv((1, 1, 1, 0.1))
        for s in self.segments:
            glVertex3fv(s[0])
            glVertex3fv(s[1])
        glEnd()
        for line in self.lines:
            line.draw()
        for plane in self.planes:
            plane.draw()

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