from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

class Keyboard(QWidget):
    ROWS = (
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM",
    )

    KEY_WIDTH = 36
    KEY_HEIGHT = 44

    def __init__(self):
        super().__init__()
        self.setObjectName("keyboard")
        self.key_labels = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        for row_letters in self.ROWS:
            row_widget = QWidget()

            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(4)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            for letter in row_letters:
                key = QLabel(letter)
                key.setObjectName("keyboardKey")
                key.setProperty("status", "unused")
                key.setFixedSize(self.KEY_WIDTH, self.KEY_HEIGHT)
                key.setAlignment(Qt.AlignmentFlag.AlignCenter)

                row_layout.addWidget(key)

                self.key_labels[letter] = key

            layout.addWidget(row_widget)

    def set_letter_status(self, letter, status):
        letter = letter.upper()
        if letter not in self.key_labels:
            return

        key = self.key_labels[letter]
        key.setProperty("status", status)

        key.style().unpolish(key)
        key.style().polish(key)

    def update_statuses(self, statuses):
        for letter in self.key_labels:
            status = statuses.get(letter.lower(), "unused")
            self.set_letter_status(letter, status)

    def reset(self):
        self.update_statuses({})