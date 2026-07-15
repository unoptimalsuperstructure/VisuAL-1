import sys
import math

import networkx as nx
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPen, QBrush, QPolygonF, QPainter
from PyQt6.QtCore import QPointF, Qt, QRectF
import pyqtgraph as pg
from MatrixPrinter import *
import csv
from MarkovChainsWindows import *
from scipy.linalg import expm


class NodeItem(QGraphicsEllipseItem):

    def __init__(self, state, colour):
        super().__init__()
        self.state = state
        self.highlight = False
        self.colour = colour

    def setProbability(self, p):
        radius = 10 + 20 * p
        self.setRect(-radius, -radius, 2 * radius, 2 * radius)
    
    def paint(self, painter, option, widget):
        super().paint(painter, option, None)
        self.setBrush(QBrush((Qt.GlobalColor.cyan if self.colour else Qt.GlobalColor.yellow) if self.highlight else Qt.GlobalColor.red))
        self.setPen(QPen(Qt.GlobalColor.white if self.colour else Qt.GlobalColor.black))

class EdgeItem(QGraphicsLineItem):

    def __init__(self, source, target, weight, sides, rotpos, colour):
        super().__init__()

        self.source = source
        self.target = target
        self.weight = weight
        self.arrow_size = 15
        self.highlight = False
        self.sides = sides
        self.rotpos = rotpos
        self.colour = colour
    
    def boundingRect(self):
        p1 = self.line().p1()
        rect = QRectF((p1.x() - 22) * 1.1, (p1.y() - 22) * 1.1, 50, 50)
        return super().boundingRect() | rect
    
    def paint(self, painter, option, widget):
        super().paint(painter, option, None)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(Qt.GlobalColor.blue if self.colour == 0 else Qt.GlobalColor.yellow, 3) if self.highlight
                       else QPen(Qt.GlobalColor.black if self.colour == 0 else Qt.GlobalColor.white))
        self.arrow_size = 30 if self.highlight else 15
        if self.source == self.target:
            painter.drawArc(self.boundingRect(), int(self.rotpos * 360 * (1 - 1 / self.sides) - 270/(1 + self.sides/3)) * 16, 330 * 16)
        else:
            line = self.line()
            painter.drawLine(line)
            angle = math.atan2(-line.dy(), line.dx())
            wing_angle = math.pi / 12
            end_point = line.p2()
        
            p1 = end_point + QPointF(
                math.cos(angle + math.pi - wing_angle) * self.arrow_size,
                -math.sin(angle + math.pi - wing_angle) * self.arrow_size
            ) - 0.1 * (line.p2() - line.p1())
            p2 = end_point + QPointF(
                math.cos(angle + math.pi + wing_angle) * self.arrow_size,
                -math.sin(angle + math.pi + wing_angle) * self.arrow_size
            ) - 0.1 * (line.p2() - line.p1())

            painter.setBrush((Qt.GlobalColor.blue if self.colour == 0 else Qt.GlobalColor.yellow) if self.highlight
                             else (Qt.GlobalColor.black if self.colour == 0 else Qt.GlobalColor.white))
            painter.setPen(Qt.PenStyle.NoPen)
        
            arrow_head = QPolygonF([end_point - 0.1 * (line.p2() - line.p1()), p1, p2])
            painter.drawPolygon(arrow_head)

def regular_polygon_layout(n, radius, centre):

    cx, cy = centre
    if n == 3:
        cy -= 30

    positions = {}
    textpos = {}

    for i in range(n):

        angle = 2 * math.pi * i / n - math.pi / 2 + math.pi / (n)

        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        positions[i] = (x + cx, y + cy)
        textpos[i] = ((x - 14) * 1.2 + cx, (y - 26) * 1.2 + cy)

    return positions, textpos

def tableToMatrix(table: QTableWidget):
    rows, cols = table.rowCount(), table.columnCount()
    A = np.zeros((rows, cols), dtype = np.float64)
    for i in range(rows):
        for j in range(cols):
            item = table.item(i, j)
            A[i, j] = float(item.text()) if item is not None else 0
    
    return A.ravel() if A.shape[1] == 1 else A

class MarkovChainsViewer(QGraphicsScene):
    def __init__(self, mat, init, colour, size):
        super().__init__()
        self.setSceneRect(-200, -160, 440, 320)
        self.graph = nx.DiGraph()
        for i in range(mat.shape[0]):
            for j in range(mat.shape[0]):
                self.graph.add_edge(i, j, weight = mat[i, j])
        self.mat = mat
        self.nodes = {}
        self.edges = []
        self.hist = [init]
        self.init = init
        self.state = init
        self.colour = colour
        self.size = size
        self.isCTMC = False
        positions, textpos = regular_polygon_layout(self.graph.number_of_nodes(), 150 if self.size == 1 else 200, (18, -10))

        i = 0
        for node, (x, y) in positions.items():

            item = NodeItem(node, colour)

            item.setPos(x, y)
            item.setProbability(init[len(init) - 1 - node])

            self.addItem(item)
            item.label = self.addText(str(round(init[len(init) - 1 - node], 3)))
            item.label.setDefaultTextColor(Qt.GlobalColor.black if colour == 0 else Qt.GlobalColor.white)
            item.label.setScale(2)
            item.label.setPos(textpos[i][0], textpos[i][1])

            self.nodes[len(init) - 1 - node] = item
            i += 1

        offset = 6
        rotpos = len(init)

        for u, v in self.graph.edges():
            if u == v:
                rotpos -= 1

            edge = EdgeItem(
                self.nodes[u],
                self.nodes[v],
                self.graph[u][v]["weight"], mat.shape[0], rotpos if u == v else -1, self.colour
            )

            x1 = self.nodes[u].x()
            y1 = self.nodes[u].y()

            x2 = self.nodes[v].x()
            y2 = self.nodes[v].y()

            dx = x2 - x1
            dy = y2 - y1

            length = math.hypot(dx, dy)

            if length != 0:

                ux = dx / length
                uy = dy / length

                px = -uy
                py = ux

                x1 += offset * px
                y1 += offset * py

                x2 += offset * px
                y2 += offset * py

            edge.setLine(x1, y1, x2, y2)
            self.addItem(edge)
            self.edges.append(edge)
        
        self.plot = pg.PlotWidget()
        self.curves = []

        num_states = mat.shape[0]

        for i in range(num_states):
            curve = self.plot.plot(name=f"State {i}")
            self.curves.append(curve)
        
        self.newStateVector()
    
    def update_plot(self):
        x = np.arange(len(self.hist))
        for i, curve in enumerate(self.curves):
            curve.setData(x, np.array(self.hist)[:, i])
    
    def nextState(self):
        self.state = expm(0.1 * len(self.hist) * self.mat) @ self.init if self.isCTMC else self.mat @ self.state
        self.hist.append(self.state)
        i, j = 0, 0
        for item in self.items():
            if isinstance(item, NodeItem):
                item.setProbability(self.state[j])
                self.nodes[j] = item
                item.label.setPlainText(str(round(self.state[j], 3)))
                j += 1
            i += 1
        self.graph.update(nodes = self.nodes)
        self.update_plot()
        self.updateStateVector()
    
    def prevState(self):
        self.hist.pop()
        self.state = self.hist[-1] if self.hist else self.init
        i, j = 0, 0
        for item in self.items():
            if isinstance(item, NodeItem):
                item.setProbability(self.state[j])
                self.nodes[j] = item
                item.label.setPlainText(str(round(self.state[j], 3)))
                j += 1
            i += 1
        self.graph.update(nodes = self.nodes)
        self.update_plot()
        self.updateStateVector()
    
    def newStateVector(self):
        self.stateVector = makeStateVector(self.state, self.colour)
        self.stateVector.cellEntered.connect(self.onHover)
        self.stateVector.mouseLeft.connect(self.onLeave)
    
    def updateStateVector(self):
        for i in range(len(self.state)):
            self.stateVector.setItem(i, 0, QTableWidgetItem(f"{self.state[i]:.2f}"))

    def onHover(self, i, j):
        for index in range(len(self.nodes)):
            self.nodes[index].highlight = (index == i)
            self.nodes[index].update()
    
    def onLeave(self):
        for index in range(len(self.nodes)):
            self.nodes[index].highlight = False
            self.nodes[index].update()

class MarkovChainsSidePanel(QGridLayout):
    def __init__(self, main, viewer, timePanel, size):
        super().__init__()
        self.main = main
        self.viewer = viewer
        self.timePanel = timePanel

        self.matrix = self.viewer.mat
        self.vec = self.viewer.init
        self.size = size
        self.isCTMC = False

        self.tol = 6

        self.addWidget(QLabel("Start time:"), 0, 0, 1, 2)
        self.startTime = QSpinBox()
        self.startTime.setRange(0, 100000)
        self.startTime.setValue(0)
        self.addWidget(self.startTime, 0, 2)
        self.addWidget(QLabel("Max duration:"), 0, 3, 1, 2)
        self.duration = QSpinBox()
        self.duration.setRange(1, 100000)
        self.duration.setValue(20)
        self.addWidget(self.duration, 0, 5)
        self.addWidget(QLabel("Number of intervals (CTMC only):"), 1, 0, 1, 5)
        self.intervals = QSpinBox()
        self.intervals.setRange(10, 1000)
        self.intervals.setValue(100)
        self.intervals.setDisabled(True)
        self.addWidget(self.intervals, 1, 5)

        self.addWidget(QLabel("DP for convergence threshold:"), 2, 0, 1, 5)
        self.tolWheel = QSpinBox()
        self.tolWheel.setValue(6)
        self.tolWheel.setRange(2, 12)
        self.tolWheel.valueChanged.connect(self.setTol)
        self.addWidget(self.tolWheel, 2, 5)

        self.importDTMCButton = QPushButton("Import DTMC CSV")
        self.importDTMCButton.clicked.connect(self.loadDTMC)
        self.importCTMCButton = QPushButton("Import CTMC CSV")
        self.importCTMCButton.clicked.connect(self.loadCTMC)
        self.addMarkovButton = QPushButton("New Markov Chain")
        self.addMarkovButton.clicked.connect(self.addMarkovWindow)
        self.startResetButton = QPushButton("Start")
        self.startResetButton.clicked.connect(self.start)

        self.matrix = self.matrix / np.sum(self.matrix, 0)
        self.vec = self.vec / np.sum(self.vec)
        self.valid = True
        self.newTransitionMatrix()

        self.conv = QLabel()

        self.addWidget(self.importDTMCButton, 3, 0, 1, 3)
        self.addWidget(self.importCTMCButton, 3, 3, 1, 3)
        self.addWidget(self.addMarkovButton, 4, 0, 1, 3)
        self.addWidget(self.startResetButton, 4, 3, 1, 3)
        self.addWidget(self.viewer.stateVector, 5, 5)
        self.addWidget(self.viewer.plot, 6, 0, 1, 6)
        self.addWidget(self.conv, 7, 0, 1, 6)
    
    def addMarkovWindow(self):
        self.window = AddMarkovWindow(self.viewer.colour)
        self.window.show()
        self.window.params.connect(self.addMarkov)
    
    def addMarkov(self, params):
        self.isCTMC = params[2]
        self.matrix = np.array(params[0])
        self.viewer.state = np.array(params[1])
        self.vec = np.array(params[1])
        makeTransitionMatrix(self.matrix, self.viewer.colour)
        makeStateVector(self.viewer.state, self.viewer.colour)
        self.updateMatrix(False, False, False)

    def setTol(self, x):
        self.tol = x
    
    def start(self):
        if self.matrix is not None:
            self.matrix = tableToMatrix(self.transitionMatrix)
            self.vec = tableToMatrix(self.viewer.stateVector)
            if self.validate(self.matrix, self.vec, self.isCTMC, False):
                self.updateMatrix(True, False, False)
                self.startResetButton.setText("Reset")
                self.startResetButton.clicked.disconnect(self.start)
                self.startResetButton.clicked.connect(self.reset)
                self.startTime.setDisabled(True)
                self.duration.setDisabled(True)
                self.intervals.setDisabled(True)
                self.tolWheel.setDisabled(True)
                self.importDTMCButton.setDisabled(True)
                self.importCTMCButton.setDisabled(True)
                self.addMarkovButton.setDisabled(True)
                self.transitionMatrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                self.viewer.stateVector.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                self.timePanel.layout().prev.setEnabled(True)
                self.timePanel.layout().next.setEnabled(True)
                self.timePanel.update()
    
    def reset(self):
        if self.matrix is not None:
            self.updateMatrix(False, False, True)
            self.startResetButton.setText("Start")
            self.startResetButton.clicked.disconnect(self.reset)
            self.startResetButton.clicked.connect(self.start)
            self.startTime.setEnabled(True)
            self.duration.setEnabled(True)
            self.intervals.setEnabled(self.isCTMC)
            self.tolWheel.setEnabled(True)
            self.importDTMCButton.setEnabled(True)
            self.importCTMCButton.setEnabled(True)
            self.addMarkovButton.setEnabled(True)
            self.timePanel.layout().prev.setDisabled(True)
            self.timePanel.layout().next.setDisabled(True)
            self.timePanel.layout().t = 0
            self.timePanel.layout().pageLabel.setText("t = 0")
            self.timePanel.update()

    def validate(self, mat, init, isCTMC, load):
        valid = True
        try:
            self.matrix = np.array(mat)
            self.vec = np.array(init).T
        except:
            valid = False
            self.error = ErrorWindow(2, None)
            self.error.show()
        
        if self.matrix.shape[0] != self.matrix.shape[1] + (isCTMC and load):
            valid = False
            self.error = ErrorWindow(101, None)
            self.error.show()
        
        else:
            for col in self.matrix.T:
                if np.linalg.norm(col) == 0:
                    valid = False
                    self.error = ErrorWindow(103, None)
                    self.error.show()
                elif load and np.min(col) < 0:
                    valid = False
                    self.error = ErrorWindow(102, None)
                    self.error.show()
        
        if valid and np.linalg.norm(self.vec) == 0:
            valid = False
            self.error = ErrorWindow(103, None)
            self.error.show()
        
        if valid and np.min(self.vec) < 0:
            valid = False
            self.error = ErrorWindow(102, None)
            self.error.show()
        
        if valid and self.matrix.size > 36:
            valid = False
            self.error = ErrorWindow(104, None)
            self.error.show()
        
        return valid
    
    def updateMatrix(self, calc, load, reset):
        try:
            self.removeWidget(self.viewer.plot)
            self.viewer.plot.deleteLater()
            self.removeWidget(self.conv)
            self.conv.deleteLater()
            self.removeWidget(self.viewer.stateVector)
            self.viewer.stateVector.deleteLater()
        except:
            pass
        finally:
            if self.isCTMC:
                if load:
                    d = self.matrix.shape[0]
                    mat = np.eye(d)
                    for i in range(d):
                        k = 0
                        for j in range(d):
                            if i == j:
                                k = 1
                            else:
                                mat[i, j] = self.matrix[i, j - k]
                    for i in range(d):
                        mat[i, i] = 1 - sum(mat[:, i])
                    self.matrix = mat
            else:
                self.matrix = self.matrix / np.sum(self.matrix, 0)
            self.vec = self.vec / np.sum(self.vec)
            v = self.vec.copy()
            if not reset:
                if self.isCTMC:
                    v = expm(self.startTime.value() * self.matrix) @ v
                else:
                    for i in range(self.startTime.value()):
                        v = self.matrix @ v
            self.viewer = MarkovChainsViewer(self.matrix, v, self.viewer.colour, self.size)
            self.viewer.isCTMC = self.isCTMC
            self.intervals.setEnabled(self.isCTMC)
            newViewer = QGraphicsView(self.viewer)
            dim = 420 if self.size == 1 else 600
            newViewer.setFixedSize(dim, dim)
            oldViewer = self.main.graphViewer
            self.main.layout.replaceWidget(self.main.graphViewer, newViewer)
            self.main.graphViewer = newViewer
            oldViewer.deleteLater()
            self.main.timePanelLayout.newViewer(self.viewer)
            self.newTransitionMatrix()
            self.viewer.newStateVector()
            self.addWidget(self.viewer.stateVector, 5, 5)
            self.addWidget(self.viewer.plot, 6, 0, 1, 6)

            s = self.startTime.value()
            temp = (expm(s * self.matrix) if self.isCTMC else np.linalg.matrix_power(self.matrix, s)) @ self.vec.copy()
            self.conv = QLabel("")
            if calc:
                d = self.duration.value()
                r = self.intervals.value()
                self.conv = QLabel(f"Did not converge within {r if self.isCTMC else d} steps")
                self.timePanel.layout().maxSteps = r - 1 if self.isCTMC else d - 1
                if self.isCTMC:
                    self.limit = self.matrix.copy()
                    t = 1.0
                    while True:
                        self.limit = expm(self.matrix * t)
                        P = expm(self.matrix * (2 * t))
                        if np.allclose(self.limit, P, rtol=1e-12, atol=1e-15):
                            break
                        t *= 2
                    base = self.vec.copy()
                    final = self.limit @ base
                    for i in range(1, r + 1):
                        temp = expm((s + i * d / r) * self.matrix) @ base
                        if np.linalg.norm(temp - final, np.inf) < 10 ** -self.tol:
                            self.conv = QLabel(f"Converged after {i} steps")
                            self.timePanel.layout().maxSteps = i - 1
                            break
                else:
                    def conv(P):
                        for lam in np.linalg.eigvals(P):
                            if abs(abs(lam) - 1) < 1e-10 and abs(lam - 1) > 1e-10:
                                return False
                        return True
                    if conv(self.matrix):
                        self.limit = self.matrix.copy()
                        while True:
                            lim = self.limit @ self.limit
                            if np.allclose(lim, self.limit, rtol=1e-12, atol=1e-15):
                                break
                            self.limit = lim
                        final = self.limit @ self.vec.copy()
                        for i in range(s, d + s):
                            temp2 = self.matrix @ temp
                            if np.linalg.norm(temp2 - final, np.inf) < 10 ** -self.tol:
                                self.conv = QLabel(f"Converged after {i - s + 1} steps")
                                self.timePanel.layout().maxSteps = i - s
                                break
                            temp = temp2
            
                self.addWidget(self.conv, 7, 0, 1, 6)

    def loadCSV(self, isCTMC):
        file_path = QFileDialog.getOpenFileName(
            None,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )[0]

        if not file_path:
            return
        
        mat = []
        init = []
        valid = True

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                try:
                    entries = list(map(lambda x: eval(x), row))
                    mat.append(entries[:-1])
                    init.append(entries[-1])
                except:
                    valid = False
                    self.error = ErrorWindow(1, None)
                    self.error.show()
                    break
        
        if valid and self.validate(mat, init, isCTMC, True):
            self.isCTMC = isCTMC
            self.updateMatrix(False, True, False)
    
    def loadDTMC(self):
        self.loadCSV(False)
    
    def loadCTMC(self):
        self.loadCSV(True)
    
    def newTransitionMatrix(self):
        try:
            self.removeWidget(self.transitionMatrix)
            self.transitionMatrix.deleteLater()
        except:
            pass
        self.transitionMatrix = makeTransitionMatrix(self.matrix, self.viewer.colour)
        if self.isCTMC:
            self.transitionMatrix.itemChanged.connect(self.CTMCUpdate)
            for i in range(self.matrix.shape[0]):
                item = self.transitionMatrix.item(i, i)
                item.setBackground(QColor("#505050" if self.viewer.colour else "#E0E0E0"))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.transitionMatrix.cellEntered.connect(self.onHover)
        self.transitionMatrix.mouseLeft.connect(self.onLeave)
        self.addWidget(self.transitionMatrix, 5, 0, 1, 5)
    
    def CTMCUpdate(self, item):
        self.transitionMatrix.blockSignals(True)
        for i in range(self.matrix.shape[0]):
            total = 0
            for j in range(self.matrix.shape[0]):
                if i != j:
                    total += float(self.transitionMatrix.item(j, i).text())
            self.transitionMatrix.item(i, i).setText(f"{-total:.3f}")
        self.transitionMatrix.blockSignals(False)
    
    def onHover(self, i, j):
        k = self.matrix.shape[0] * j + i
        index = 0
        for index in range(len(self.viewer.edges)):
            self.viewer.edges[index].highlight = (index == k)
            self.viewer.edges[index].update()
    
    def onLeave(self):
        for index in range(len(self.viewer.edges)):
            self.viewer.edges[index].highlight = False
            self.viewer.edges[index].update()

class MarkovChainsTimePanel(QHBoxLayout):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.t = 0

        self.prev = QPushButton("<--")
        self.prev.setDisabled(True)
        self.prev.clicked.connect(self.prevPage)
        self.addWidget(self.prev)

        self.pageLabel = QLabel("t = 0")
        self.addWidget(self.pageLabel)

        self.next = QPushButton("-->")
        self.next.setDisabled(True)
        self.next.clicked.connect(self.nextPage)
        self.addWidget(self.next)
    
    def newViewer(self, viewer):
        self.viewer = viewer
        self.t = 0
        self.update()

    def prevPage(self):
        if self.t > 0:
            self.t -= 1
            self.viewer.prevState()
        self.pageLabel.setText(f"t = {self.t}")
    
    def nextPage(self):
        if self.t <= self.maxSteps:
            self.t += 1
            self.viewer.nextState()
        self.pageLabel.setText(f"t = {self.t}")