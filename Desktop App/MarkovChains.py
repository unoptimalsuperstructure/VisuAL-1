import sys
import math

import networkx as nx
import numpy as np

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPen, QBrush, QPolygonF, QPainter
from PyQt6.QtCore import QPointF, Qt, QRectF, pyqtSignal
from MatrixPrinter import *
import NumStabilityWindows, csv


class NodeItem(QGraphicsEllipseItem):

    def __init__(self, state):
        super().__init__()

        self.state = state

    def setProbability(self, p):
        radius = 10 + 40 * p

        self.setRect(
            -radius,
            -radius,
            2 * radius,
            2 * radius,
        )

class EdgeItem(QGraphicsLineItem):

    def __init__(self, source, target, weight, sides, rotpos):
        super().__init__()

        self.source = source
        self.target = target
        self.weight = weight
        self.arrow_size = 15
        self.highlight = False
        self.sides = sides
        self.rotpos = rotpos
    
    def boundingRect(self):
        p1 = self.line().p1()
        rect = QRectF(p1.x() - 50, p1.y() - 50, 100, 100)
        return super().boundingRect() | rect
    
    def paint(self, painter, option, widget):
        super().paint(painter, option, None)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(Qt.GlobalColor.blue, 3) if self.highlight else QPen(Qt.GlobalColor.black))
        if self.source == self.target:
            painter.drawArc(self.boundingRect(), int(self.rotpos * 360 * (1 - 1 / self.sides) - 90) * 16, int(360 * (1 - 1 / self.sides)) * 16)
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

            painter.setBrush(Qt.GlobalColor.blue if self.highlight else Qt.GlobalColor.black)
            painter.setPen(Qt.PenStyle.NoPen)
        
            arrow_head = QPolygonF([end_point - 0.1 * (line.p2() - line.p1()), p1, p2])
            painter.drawPolygon(arrow_head)

def regular_polygon_layout(n, radius=250, centre=(0, 0)):

    cx, cy = centre

    positions = {}
    textpos = {}

    for i in range(n):

        angle = 2 * math.pi * i / n - math.pi / 2 + math.pi / (n)

        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        positions[i] = (x, y)
        textpos[i] = (x * 1.2, y * 1.2)

    return positions, textpos


class MarkovChainsViewer(QGraphicsScene):

    def __init__(self, mat, init):
        super().__init__()
        self.setSceneRect(-200, -160, 440, 320)
        self.graph = nx.DiGraph()
        for i in range(mat.shape[0]):
            for j in range(mat.shape[0]):
                self.graph.add_edge(i, j, weight = mat[i, j])
        self.mat = mat
        self.nodes = {}
        self.edges = []
        self.hist = []
        self.init = init.T
        self.state = init.T

        positions, textpos = regular_polygon_layout(
            self.graph.number_of_nodes(),
            radius=200,
            centre=(0, 0),
        )
        i = 0
        for node, (x, y) in positions.items():

            item = NodeItem(node)

            item.setPos(x, y)
            item.setProbability(init[node])

            self.addItem(item)
            item.label = self.addText(str(round(init[node], 3)))
            item.label.setPos(textpos[i][0], textpos[i][1])

            self.nodes[node] = item
            i += 1

        offset = 6
        rotpos = -1

        for u, v in self.graph.edges():
            if u == v:
                rotpos += 1

            edge = EdgeItem(
                self.nodes[u],
                self.nodes[v],
                self.graph[u][v]["weight"], mat.shape[0], rotpos if u == v else -1
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
    
    def nextState(self):
        self.state = self.mat @ self.state
        self.hist.append(self.hist[-1] @ self.mat if self.hist else np.eye(self.mat.shape[0]))
        i, j = 0, 0
        for item in self.items():
            if isinstance(item, NodeItem):
                item.setProbability(self.state[j])
                self.nodes[j] = item
                item.label.setPlainText(str(round(self.state[j], 3)))
                j += 1
            i += 1
        self.graph.update(nodes = self.nodes)
    
    def prevState(self):
        self.state = self.hist.pop() @ self.init
        i, j = 0, 0
        for item in self.items():
            if isinstance(item, NodeItem):
                item.setProbability(self.state[j])
                self.nodes[j] = item
                item.label.setPlainText(str(round(self.state[j], 3)))
                j += 1
            i += 1
        self.graph.update(nodes = self.nodes)

class TransitionMatrix(QTableWidget):
    mouseLeft = pyqtSignal()

    def leaveEvent(self, event):
        self.mouseLeft.emit()
        super().leaveEvent(event)

class MarkovChainsSidePanel(QGridLayout):
    def __init__(self, main, viewer, timePanel):
        super().__init__()
        self.main = main
        self.viewer = viewer
        self.timePanel = timePanel

        self.matrix = None

        self.displayAcc = 2

        self.addWidget(QLabel("DP for display matrix:"), 0, 0)
        self.displayAccWheel = QSpinBox()
        self.displayAccWheel.setValue(2)
        self.displayAccWheel.setRange(2, 12)
        self.displayAccWheel.valueChanged.connect(self.setDisplayAcc)
        self.addWidget(self.displayAccWheel, 0, 1)

        addDataButton = QPushButton("Import CSV...")
        addDataButton.clicked.connect(self.loadCSV)
        randomDataButton = QPushButton("Generate random data...")
        actionButton = QPushButton("Action...")
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)
        self.transitionMatrix = QLabel()

        self.addWidget(addDataButton, 1, 0)
        self.addWidget(randomDataButton, 1, 1)
        self.addWidget(actionButton, 2, 0)
        self.addWidget(resetButton, 2, 1)
        self.addWidget(self.transitionMatrix, 3, 0, 1, 2)
    
    def setDisplayAcc(self, x):
        self.displayAcc = int(x)
    
    def reset(self):
        if self.matrix is not None:
            self.makeTransitionMatrix()
            try:
                self.timePanel.layout.removeWidget(self.op)
                self.timePanel.layout.removeWidget(self.pageView)
                self.timePanel.layout.removeWidget(self.soln)
            except:
                pass
            
            self.op = QLabel()
            self.timePanel.layout.addWidget(self.op)
            self.timePanel.layout.addWidget(self.pageView)

            self.soln = QLabel()
            self.viewer.layout.addWidget(self.soln)

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
        
        if valid:
            self.matrix = self.matrix / np.sum(self.matrix, 0)
            self.vec = self.vec / np.sum(self.vec)
            self.viewer = MarkovChainsViewer(self.matrix, self.vec)
            newViewer = QGraphicsView(self.viewer)
            newViewer.setFixedSize(800, 600)
            oldViewer = self.main.graphViewer
            self.main.layout.replaceWidget(self.main.graphViewer, newViewer)
            self.main.graphViewer = newViewer
            oldViewer.deleteLater()
            self.main.timePanelLayout.update(self.viewer)
            self.makeTransitionMatrix()
    
    def makeTransitionMatrix(self):
        try:
            self.removeWidget(self.transitionMatrix)
            self.transitionMatrix.deleteLater()
        except:
            pass
        self.d = self.matrix.shape[0]
        self.transitionMatrix = TransitionMatrix()
        self.transitionMatrix.setRowCount(self.d)
        self.transitionMatrix.setColumnCount(self.d)
        states = ["A", "B", "C", "D", "E", "F"][:self.d]
        self.transitionMatrix.setVerticalHeaderLabels(states)
        self.transitionMatrix.setHorizontalHeaderLabels(states)
        self.transitionMatrix.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.transitionMatrix.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i in range(self.d):
            for j in range(self.d):
                self.transitionMatrix.setItem(i, j, QTableWidgetItem(f"{self.matrix[i, j]:.2f}"))
        self.transitionMatrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.transitionMatrix.setMouseTracking(True)
        self.transitionMatrix.cellEntered.connect(self.onHover)
        self.transitionMatrix.mouseLeft.connect(self.onLeave)
        self.addWidget(self.transitionMatrix, 3, 0, 1, 2)
    
    def onHover(self, i, j):
        k = self.d * i + j
        index = 0
        for index in range(len(self.viewer.edges)):
            self.viewer.edges[index].highlight = True if index == k else False
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

        prev = QPushButton("<--")
        prev.clicked.connect(self.prevPage)
        self.addWidget(prev)

        self.pageLabel = QLabel("t = 0")
        self.addWidget(self.pageLabel)

        next = QPushButton("-->")
        next.clicked.connect(self.nextPage)
        self.addWidget(next)
    
    def update(self, viewer):
        self.viewer = viewer
        self.t = 0
        self.pageLabel.setText("t = 0")

    def toStart(self):
        self.t = 0
        self.pageLabel.setText("t = 0")
        try:
            self.op.setText(self.hist[self.page][1])
            self.transitionMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass
    
    def prevPage(self):
        if self.t > 0:
            self.t -= 1
            self.viewer.prevState()
        self.pageLabel.setText(f"t = {self.t}")
        try:
            self.op.setText(self.hist[self.page][1])
            self.transitionMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass
    
    def nextPage(self):
        self.t += 1
        self.viewer.nextState()
        self.pageLabel.setText(f"t = {self.t}")
        try:
            self.op.setText(self.hist[self.page][1])
            self.transitionMatrix.setText(self.displayType(toString(self.hist[self.page][0], self.displayAcc)))
        except:
            pass