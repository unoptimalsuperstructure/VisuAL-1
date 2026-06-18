import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Toolbar Demo")
        self.resize(600, 300)

        # 1. Initialize the toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))  # Set size for icons
        self.addToolBar(toolbar)

        # 2. Define a standard clickable action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close_app)
        save = QAction("Save", self)
        toolbar.addAction(exit_action)
        toolbar.addAction(save)

        # 3. Add a visual separator line
        toolbar.addSeparator()

        # 4. Insert an interactive widget (Search bar)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        toolbar.addWidget(self.search_input)

    def close_app(self):
        QApplication.instance().quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#json_string = json_util.dumps(doc)

#with open("output.json", "w") as file:
    #file.write(json_string)