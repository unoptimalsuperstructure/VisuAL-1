LIGHT_THEME = """
QWidget {
    background-color: #f0f0f0;
    color: #000000;
}

QLabel {
    color: #000000;
}

QSpinBox {
    background-color: #eeeeee;
}

QSpinBox:disabled {
    background-color: #c0c0c0;
}

QPushButton, QLineEdit {
    background-color: #eeeeee;
    color: black;
    border: 1px solid #aaaaaa;
    border-radius: 4px;
    padding: 5px;
}

QPushButton:hover {
    background-color: #ffffff;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #c0c0c0;
    color: #777777;
    border-color: #555555;
}

QPushButton:focus {
    border: 2px solid #4da6ff;
}

QTableWidget {
    background-color: white;
    color: black;
    gridline-color: #cccccc;
}

QTableWidget::item:selected {
    background: #e0e0e0;
    color: black;
}

QHeaderView::section, QTableCornerButton::section {
    background-color: #eeeeee;
    color: black;
    border: 1px solid #cccccc;
}
"""

DARK_THEME = """
QWidget {
    background-color: #303030;
    color: #ffffff;
}

QLabel {
    color: #ffffff;
}

QSpinBox {
    background-color: #505050;
}

QSpinBox:disabled {
    background-color: #303030;
}

QPushButton, QLineEdit {
    background-color: #505050;
    color: white;
    border: 1px solid #777777;
    border-radius: 4px;
    padding: 5px;
}

QPushButton:hover {
    background-color: #606060;
}

QPushButton:pressed {
    background-color: #404040;
}

QPushButton:disabled {
    background-color: #303030;
    color: #777777;
    border-color: #555555;
}

QPushButton:focus {
    border: 2px solid #4da6ff;
}

QTableWidget {
    background-color: #252525;
    color: white;
    gridline-color: #555555;
}

QTableWidget::item:selected {
    background: #404040;
    color: white;
}

QHeaderView::section, QTableCornerButton::section {
    background-color: #2b2b2b;
    color: white;
    border: 1px solid #555555;
}
"""