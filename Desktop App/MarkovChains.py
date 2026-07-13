import sys
import math

import networkx as nx
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPen, QBrush, QPolygonF, QPainter, QDoubleValidator
from PyQt6.QtCore import QPointF, Qt, QRectF, pyqtSignal
import pyqtgraph as pg
from MatrixPrinter import *
import NumStabilityWindows, csv


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
        self.state = self.mat @ self.state
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
        self.d = self.mat.shape[0]
        self.stateVector = TableWithLeave()
        self.stateVector.setItemDelegate(NonNegativeDelegate())
        self.stateVector.setRowCount(self.d)
        self.stateVector.setColumnCount(1)
        self.stateVector.setFixedSize(40, 40 * self.d)
        self.stateVector.verticalHeader().setDefaultSectionSize(40)
        self.stateVector.horizontalHeader().setDefaultSectionSize(40)
        self.stateVector.verticalHeader().hide()
        self.stateVector.horizontalHeader().hide()
        self.stateVector.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stateVector.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for i in range(self.d):
            self.stateVector.setItem(i, 0, QTableWidgetItem(f"{self.state[i]:.2f}"))
        self.stateVector.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.stateVector.setMouseTracking(True)
        self.stateVector.cellEntered.connect(self.onHover)
        self.stateVector.mouseLeft.connect(self.onLeave)
    
    def updateStateVector(self):
        for i in range(self.d):
            self.stateVector.setItem(i, 0, QTableWidgetItem(f"{self.state[i]:.2f}"))
    
    def onHover(self, i, j):
        for index in range(len(self.nodes)):
            self.nodes[index].highlight = (index == i)
            self.nodes[index].update()
    
    def onLeave(self):
        for index in range(len(self.nodes)):
            self.nodes[index].highlight = False
            self.nodes[index].update()

class TableWithLeave(QTableWidget):
    mouseLeft = pyqtSignal()

    def leaveEvent(self, event):
        self.mouseLeft.emit()
        super().leaveEvent(event)

class NonNegativeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)

        validator = QDoubleValidator(0.0, 1e100, 10, editor)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        editor.setValidator(validator)
        return editor

class MarkovChainsSidePanel(QGridLayout):
    def __init__(self, main, viewer, timePanel, size):
        super().__init__()
        self.main = main
        self.viewer = viewer
        self.timePanel = timePanel

        self.matrix = self.viewer.mat
        self.vec = self.viewer.init
        self.size = size

        self.tol = 6

        self.addWidget(QLabel("DP for convergence threshold:"), 0, 0, 1, 5)
        self.tolWheel = QSpinBox()
        self.tolWheel.setValue(6)
        self.tolWheel.setRange(2, 12)
        self.tolWheel.valueChanged.connect(self.setTol)
        self.addWidget(self.tolWheel, 0, 5)

        self.importDTMCButton = QPushButton("Import DTMC CSV")
        self.importDTMCButton.clicked.connect(self.loadCSV)
        self.importCTMCButton = QPushButton("Import CTMC CSV")
        self.addMarkovButton = QPushButton("New Markov Chain")
        self.startResetButton = QPushButton("Start")
        self.startResetButton.clicked.connect(self.start)

        self.matrix = self.matrix / np.sum(self.matrix, 0)
        self.vec = self.vec / np.sum(self.vec)
        self.valid = True
        self.makeTransitionMatrix()

        self.conv = QLabel()

        self.addWidget(self.importDTMCButton, 1, 0, 1, 3)
        self.addWidget(self.importCTMCButton, 1, 3, 1, 3)
        self.addWidget(self.addMarkovButton, 2, 0, 1, 3)
        self.addWidget(self.startResetButton, 2, 3, 1, 3)
        self.addWidget(self.viewer.stateVector, 3, 5)
        self.addWidget(self.viewer.plot, 4, 0, 1, 6)
        self.addWidget(self.conv, 5, 0, 1, 6)
    
    def setTol(self, x):
        self.tol = int(x)
    
    def start(self):
        if self.matrix is not None:
            self.matrix = tableToMatrix(self.transitionMatrix)
            self.vec = tableToMatrix(self.viewer.stateVector)
            if self.validate(self.matrix, self.vec):
                self.updateMatrix(True)
                self.startResetButton.setText("Reset")
                self.startResetButton.clicked.disconnect(self.start)
                self.startResetButton.clicked.connect(self.reset)
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
            self.updateMatrix(False)
            self.startResetButton.setText("Start")
            self.startResetButton.clicked.disconnect(self.reset)
            self.startResetButton.clicked.connect(self.start)
            self.tolWheel.setEnabled(True)
            self.importDTMCButton.setEnabled(True)
            self.importCTMCButton.setEnabled(True)
            self.addMarkovButton.setEnabled(True)
            self.timePanel.layout().prev.setDisabled(True)
            self.timePanel.layout().next.setDisabled(True)
            self.timePanel.layout().t = 0
            self.timePanel.layout().pageLabel.setText("t = 0")
            self.timePanel.update()

    def validate(self, mat, init):
        valid = True
        try:
            self.matrix = np.array(mat)
            self.vec = np.array(init).T
        except:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(2, None)
            self.error.show()
        
        if self.matrix.shape[0] != self.matrix.shape[1]:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(101, None)
            self.error.show()
        
        else:
            for col in self.matrix.T:
                if np.linalg.norm(col) == 0:
                    valid = False
                    self.error = NumStabilityWindows.ErrorWindow(103, None)
                    self.error.show()
                elif np.min(col) < 0:
                    valid = False
                    self.error = NumStabilityWindows.ErrorWindow(102, None)
                    self.error.show()
        
        if valid and np.linalg.norm(self.vec) == 0:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(103, None)
            self.error.show()
        
        if valid and np.min(self.vec) < 0:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(102, None)
            self.error.show()
        
        if valid and self.matrix.size > 36:
            valid = False
            self.error = NumStabilityWindows.ErrorWindow(104, None)
            self.error.show()
        
        return valid
    
    def updateMatrix(self, calc):
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
            self.matrix = self.matrix / np.sum(self.matrix, 0)
            self.vec = self.vec / np.sum(self.vec)
            self.viewer = MarkovChainsViewer(self.matrix, self.vec, self.viewer.colour, self.size)
            newViewer = QGraphicsView(self.viewer)
            dim = 420 if self.size == 1 else 600
            newViewer.setFixedSize(dim, dim)
            oldViewer = self.main.graphViewer
            self.main.layout.replaceWidget(self.main.graphViewer, newViewer)
            self.main.graphViewer = newViewer
            oldViewer.deleteLater()
            self.main.timePanelLayout.newViewer(self.viewer)
            self.makeTransitionMatrix()
            self.viewer.newStateVector()
            self.addWidget(self.viewer.stateVector, 3, 5)
            self.addWidget(self.viewer.plot, 4, 0, 1, 6)

            temp = self.vec.copy()
            self.conv = QLabel("Did not converge within 100 steps" if calc else "")
            if calc:
                self.timePanel.layout().maxSteps = 99
                for i in range(100):
                    temp2 = self.matrix @ temp
                    if np.linalg.norm(temp2 - temp) < 10 ** -self.tol:
                        self.conv = QLabel(f"Converged after {i + 1} steps")
                        self.timePanel.layout().maxSteps = i
                        break
                    temp = temp2
            
                self.addWidget(self.conv, 5, 0)

    def loadCSV(self):
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
                    self.error = NumStabilityWindows.ErrorWindow(1, None)
                    self.error.show()
                    break
        
        if valid and self.validate(mat, init):
            self.updateMatrix(False)
    
    def makeTransitionMatrix(self):
        try:
            self.removeWidget(self.transitionMatrix)
            self.transitionMatrix.deleteLater()
        except:
            pass
        self.d = self.matrix.shape[0]
        self.transitionMatrix = TableWithLeave()
        self.transitionMatrix.setItemDelegate(NonNegativeDelegate())
        self.transitionMatrix.setRowCount(self.d)
        self.transitionMatrix.setColumnCount(self.d)
        states = ["A", "B", "C", "D", "E", "F"][:self.d]
        self.transitionMatrix.setVerticalHeaderLabels(states)
        self.transitionMatrix.setHorizontalHeaderLabels(states)
        self.transitionMatrix.verticalHeader().setDefaultSectionSize(40)
        self.transitionMatrix.horizontalHeader().setDefaultSectionSize(40)
        self.transitionMatrix.setFixedSize(40 * self.d + 20, 40 * self.d + 25)
        self.transitionMatrix.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.transitionMatrix.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.transitionMatrix.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.transitionMatrix.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for i in range(self.d):
            for j in range(self.d):
                self.transitionMatrix.setItem(i, j, QTableWidgetItem(f"{self.matrix[i, j]:.2f}"))
        self.transitionMatrix.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.transitionMatrix.setMouseTracking(True)
        self.transitionMatrix.cellEntered.connect(self.onHover)
        self.transitionMatrix.mouseLeft.connect(self.onLeave)
        self.addWidget(self.transitionMatrix, 3, 0, 1, 5)
    
    def onHover(self, i, j):
        k = self.d * j + i
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