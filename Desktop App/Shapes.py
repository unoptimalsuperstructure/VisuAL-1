import math, numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from copy import deepcopy

def tlsplane(lst):
    try:
        for i in range(len(lst)):
            for j in range(len(lst[0])):
                lst[i][j] = float(lst[i][j])
        temp = np.matrix(lst, dtype = 'float64')
        if temp.shape[1] not in (2, 3) or temp.shape[0] < 3:
            print(1/0)
        elif temp.shape[1] == 2:
            temp = np.block([temp, np.matrix([[0]]*len(temp))])
            edges = []
            for i in range(len(lst)):
                edges.append([i, (i + 1) % len(lst)])
            return [Polygon("Polygon", temp, edges, [0, 0, 1])]
    except:
        return "Error: Invalid data or not enough data points"
    mat = []
    avg = np.array([0.0, 0.0, 0.0])
    for vec in temp:
        avg = avg + vec
    avg /= len(temp)
    for vec in temp:
        mat.append(list((vec - avg).A1))
    mat = np.matrix(mat).transpose()*np.matrix(mat)
    svd = np.linalg.svd(mat)
    if abs(svd[1][0]) < 0.001 or abs(svd[1][1]) < 0.001:
        return "Error: At least one of the two largest eigenvalues is almost zero.\nYour points cannot be well-fitted to a plane."
    elif svd[1][2] != 0 and 1/1.001 < svd[1][1]/svd[1][2] < 1.001:
        return "Error: The two smallest eigenvalues are too close.\nYour points cannot be well-fitted to a plane."
    else:
        a, b, c, d = *svd[2][2].A1, np.dot(svd[2][2], avg.A1).A1[0]
        proj = np.array([[1 - a ** 2, -a * b, -a * c, a * d],
                         [-a * b, 1 - b ** 2, -b * c, b * d],
                         [-a * c, -b * c, 1 - c ** 2, c * d],
                         [0, 0, 0, 1]])
        vecs = []
        for i in range(len(temp)):
            vec = temp[i].tolist()[0]
            vecs.append(np.matmul(proj, np.matrix([[vec[0]], [vec[1]], [vec[2]], [1]])).transpose().tolist()[0][:-1])
        edges = []
        for i in range(len(lst)):
            edges.append([i, (i + 1) % len(lst)])
        return [Polygon("Polygon", vecs, edges, svd[2][2].A1.tolist()), np.dot(svd[2][2], avg.A1).A1[0]]

class Polygon:
    def __init__(self, name, vertices, edges, normal):
        self.name = name
        self.vertices = vertices.tolist() if isinstance(vertices, np.matrix) or isinstance(vertices, np.ndarray) else vertices
        self.edges = edges.tolist() if isinstance(edges, np.matrix) or isinstance(edges, np.ndarray) else edges
        self.normal = normal
    
    def draw(self):
        glBegin(GL_POLYGON)
        glColor4fv((1, 0.8, 0.4, 0.7))
        for i in range(len(self.vertices)):
            glVertex3fv(self.vertices[i])
        glEnd()
    
    def makePyramid(self, name, a, b, c):
        solid = Solid(name, self.vertices, self.edges, [], [1, 0, 0, 0])
        L = len(self.vertices)
        for i in range(L):
            solid.edges.append([i, L])
        for i in range(L):
            solid.surfaces.append([i, (i + 1) % L, L])
        solid.vertices.append([a, b, c])
        solid.surfaces.append(list(range(L)))

        centre = np.array([0, 0, 0])
        for vertex in solid.vertices:
            centre = centre + vertex
        centre /= len(solid.vertices)
        solid.vertices.append(centre.tolist())

        solid.default = [solid.vertices.copy(), solid.edges.copy(), solid.surfaces.copy()]
        return solid
    
    def makePrism(self, name, h):
        solid = Solid(name, self.vertices, self.edges, [], [1, 0, 0, 0])
        L = len(self.vertices)
        for i in range(L):
            solid.edges.append([L + i, (i + 1) % L + L])
            solid.edges.append([i, L + i])
            solid.vertices.append((np.matrix(self.vertices[i]) + np.matrix(self.normal) * h).tolist()[0])
        for i in range(L):
            solid.surfaces.append([i, (i + 1) % L, (i + 1) % L + L, L + i])
        solid.surfaces.append(list(range(L)))
        solid.surfaces.append(list(range(L, 2 * L)))

        centre = np.array([0, 0, 0])
        for vertex in solid.vertices:
            centre = centre + vertex
        centre /= len(solid.vertices)
        solid.vertices.append(centre.tolist())

        solid.default = [solid.vertices.copy(), solid.edges.copy(), solid.surfaces.copy()]
        return solid

class Solid:
    def __init__(self, name, vertices, edges, surfaces, params):
        self.name = name
        self.show = True
        self.isActive = False
        self.isShadow = False
        self.params = params
        for i in range(len(vertices)):
            for j in range(3):
                vertices[i][j] *= params[0]
                vertices[i][j] += params[j + 1]
        self.default = [vertices.copy(), edges.copy(), surfaces.copy()]
        self.vertices = vertices
        self.initVertices = vertices.copy()
        self.edges = edges
        self.surfaces = surfaces
        
        self.singularMatrixStack = []
        self.matrixStack = [[np.identity(4), "Identity", Shadow()]]
        self.curMatrix = [np.identity(4), "Identity", Shadow()]
    
    def showhide(self):
        self.show = not self.show

    def getShadow(self):
        if self.matrixStack:
            return self.matrixStack[-1][2]
        else:
            return Shadow()
    
    def draw(self):
        if self.show:
            glBegin(GL_POLYGON)
            i = 0
            a = 1 if self.isActive else 0.8
            for surface in self.surfaces:
                glColor4fv((a * (1 - i * 1/(len(self.surfaces) - 1)),  a * (i * 1/(len(self.surfaces) - 1)), a * 0.5, 0.1 if self.isShadow else 0.7))
                for vertex in surface:
                    glVertex3fv(self.vertices[vertex])
                i += 1
            glEnd()
        if self.isActive:
            glBegin(GL_LINES)
            glColor3fv((1, 1, 1))
            for edge in self.edges:
                for vertex in edge:
                    glVertex3fv(self.vertices[vertex])
            glEnd()
    
    def updateMatrix(self, matrix, redrawEdges):
        i = 0
        for vertex in self.vertices:
            vec = np.matmul(matrix[0], [vertex[0], vertex[1], vertex[2], 1])
            self.vertices[i] = [vec[0], vec[1], vec[2]]
            i += 1
        if not self.isShadow:
            lastShape = Solid(self.name, *deepcopy(self.default), [1, 0, 0, 0])
            lastShape.isShadow = True
            lastShape.updateMatrix(self.curMatrix, False)
            if float(abs(np.linalg.det(matrix[0]))) < 0.00001:
                self.singularMatrixStack.append(self.curMatrix.copy())
            if redrawEdges:
                for i in range(len(self.vertices)):
                    matrix[2].append(*self.vertices[i], *lastShape.vertices[i])
                matrix[2].lastShape = lastShape
            self.matrixStack.append(matrix)
            self.curMatrix = [np.matmul(matrix[0], self.curMatrix[0]), matrix[1], matrix[2]]

    def repeat(self, n):
        if len(self.matrixStack) > 1:
            lastOp = self.matrixStack[-n].copy()
            if lastOp[1] == "Scaling":
                self.scale(lastOp[0][0][0])
            else:
                if lastOp[1] in ["Identity", "Translation"]:
                    lastOp[2] = Shadow()
                else:
                    lastOp[2] = lastOp[2].copy()
                    lastOp[2].segments = []
                    lastOp[2].lastShape = Solid(self.name, *deepcopy(self.default), [1, 0, 0, 0])
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
        plane = Plane(a, b, c, d)
        plane.isActive = True
        shadow.addPlane(plane)
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
        line = Line(p1, p2, p3, d1, d2, d3)
        line.isActive = True
        shadow.addLine(line)
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
        line = Line(p1, p2, p3, d1, d2, d3)
        line.isActive = True
        shadow.addLine(line)
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
        plane = Plane(a, b, c, d)
        plane.isActive = True
        shadow.addPlane(plane)
        self.updateMatrix([newMatrix, "Projection onto Plane", shadow], True)
        return shadow
    
    def scale(self, c):
        if c <= 0 or c == 1:
            return
        centre = self.vertices[-1]
        newMatrix = np.array([[c, 0, 0, (1 - c)*centre[0]], [0, c, 0, (1 - c)*centre[1]], [0, 0, c, (1 - c)*centre[2]], [0, 0, 0, 1]])
        self.updateMatrix([newMatrix, "Scaling", Shadow()], True)
        return Shadow()
    
    def shear(self, a1, a2, a3, d1, d2, d3, c1, c2, c3, k):
        if (d1 == 0 and d2 == 0 and d3 == 0) or (c1 == 0 and c2 == 0 and c3 == 0):
            print("Error: Axis or direction is the zero vector")
            return
        elif abs(float(np.linalg.norm(np.cross([d1, d2, d3]/np.linalg.norm([d1, d2, d3]), [c1, c2, c3]/np.linalg.norm([c1, c2, c3]))))) < 0.001:
            print("Error: Axis and direction are parallel or almost parallel")
            return
        else:
            n = np.cross([d1, d2, d3], [c1, c2, c3])
            M = np.identity(3) + k/(np.linalg.norm(n) ** 2) * np.transpose(np.matrix([c1, c2, c3])) * n
            t = -k/(np.linalg.norm(n) ** 2) * np.dot(n, [a1, a2, a3]) * np.transpose(np.matrix([c1, c2, c3]))
            newMatrix = np.block([[M, t], [0, 0, 0, 1]]).A
            self.updateMatrix([newMatrix, "Shearing", Shadow()], True)
            return Shadow()
    
    def applyCustomMatrix(self, mat):
        if abs(np.matrix(mat).sum()) < 0.001 or abs((np.matrix(mat) - np.identity(4)).sum()) < 0.001:
            return
        else:
            self.updateMatrix([np.array(mat), "Custom", Shadow()], True)
            return Shadow()

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

class Line():
    def __init__(self, a1, a2, a3, d1, d2, d3):
        self.isActive = False
        self.vis = True
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        self.lst = [a1, a2, a3, d1, d2, d3]
        self.name = f"Line: r = ({round(a1, 2)}, {round(a2, 2)}, {round(a3, 2)}) + t({round(d1, 2)}, {round(d2, 2)}, {round(d3, 2)})"
    
    def draw(self):
        glBegin(GL_LINES)
        f = 1 if self.isActive else 0.6
        glColor3fv((f, f, f))
        glVertex3fv([self.a1 - 500 * self.d1, self.a2 - 500 * self.d2, self.a3 - 500 * self.d3])
        glVertex3fv([self.a1 + 500 * self.d1, self.a2 + 500 * self.d2, self.a3 + 500 * self.d3])
        glEnd()
    
    def drawShadow(self):
        glBegin(GL_LINES)
        glColor3fv((1, 1, 0))
        glVertex3fv([self.a1 - 500 * self.d1, self.a2 - 500 * self.d2, self.a3 - 500 * self.d3])
        glVertex3fv([self.a1 + 500 * self.d1, self.a2 + 500 * self.d2, self.a3 + 500 * self.d3])
        glEnd()
    
    def show(self):
        self.vis = True
    
    def hide(self):
        self.vis = False

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
            line.drawShadow()
        for plane in self.planes:
            plane.drawShadow()

class Plane():
    def __init__(self, a, b, c, d):
        self.isActive = False
        self.vis = True
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.lst = [a, b, c, d]
        self.name = f"Plane: {round(a, 2)}x + {round(b, 2)}y + {round(c, 2)}z = {round(d, 2)}"
    
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
        perp1 = 10 * perp1
        perp2 = 10 * perp2
        plane_points = [[pt[0] - perp1[0] - perp2[0], pt[1] - perp1[1] - perp2[1], pt[2] - perp1[2] - perp2[2]],
                        [pt[0] - perp1[0] + perp2[0], pt[1] - perp1[1] + perp2[1], pt[2] - perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] + perp2[0], pt[1] + perp1[1] + perp2[1], pt[2] + perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] - perp2[0], pt[1] + perp1[1] - perp2[1], pt[2] + perp1[2] - perp2[2]]]
    
        plane_edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    
        glBegin(GL_QUADS)
        f = 0.7 if self.isActive else 0.3
        for edge in plane_edges:
            for vertex in edge:
                glColor4fv((0.7, 0.7, 0.7, f))
                glVertex3fv(plane_points[vertex])
        glEnd()
    
    def drawShadow(self):
        if self.a != 0 and self.b != 0:
            perp1 = [1, -self.a/self.b, 0]
        else:
            perp1 = [int(self.a == 0), int(self.b == 0), int(self.c == 0)]
        normal = np.array([self.a, self.b, self.c])
        pt = normal * self.d/(np.linalg.norm(normal) ** 2)
        normal = normal/np.linalg.norm(normal)
        perp1 = np.array(perp1)/np.linalg.norm(perp1)
        perp2 = np.cross(normal, perp1)
        perp1 = 10 * perp1
        perp2 = 10 * perp2
        plane_points = [[pt[0] - perp1[0] - perp2[0], pt[1] - perp1[1] - perp2[1], pt[2] - perp1[2] - perp2[2]],
                        [pt[0] - perp1[0] + perp2[0], pt[1] - perp1[1] + perp2[1], pt[2] - perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] + perp2[0], pt[1] + perp1[1] + perp2[1], pt[2] + perp1[2] + perp2[2]],
                        [pt[0] + perp1[0] - perp2[0], pt[1] + perp1[1] - perp2[1], pt[2] + perp1[2] - perp2[2]]]
    
        plane_edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    
        glBegin(GL_QUADS)
        for edge in plane_edges:
            for vertex in edge:
                glColor4fv((0.3, 0.7, 0.7, 0.3))
                glVertex3fv(plane_points[vertex])
        glEnd()
    
    def show(self):
        self.vis = True

    def hide(self):
        self.vis = False