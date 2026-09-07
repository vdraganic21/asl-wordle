from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

class Board(QWidget):
    ROWS = 6
    COLUMNS = 5
    CELL_SIZE = 64

    def __init__(self):
        super().__init__()
        self.setObjectName("board")
        self.word_cells = []
        self.setup_ui()

    def setup_ui(self):
        grid = QGridLayout(self)
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)

        for row in range(self.ROWS):
            row_cells = []

            for column in range(self.COLUMNS):
                cell = QLabel()
                cell.setObjectName("wordCell")
                cell.setProperty("status", "empty")
                cell.setFixedSize(self.CELL_SIZE, self.CELL_SIZE)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)

                grid.addWidget(cell, row, column)
                row_cells.append(cell)

            self.word_cells.append(row_cells)

        grid.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)

    def set_letter(self, row, column, letter):
        self.word_cells[row][column].setText(letter.upper())

    def clear_letter(self, row, column):
        self.word_cells[row][column].clear()
        self.set_status(row, column, "empty")

    def set_status(self, row, column, status):
        cell = self.word_cells[row][column]
        cell.setProperty("status", status)
        cell.style().unpolish(cell)
        cell.style().polish(cell)

    def set_row(self, row, guess, statuses=None):
        for column in range(self.COLUMNS):
            if column < len(guess):
                self.set_letter(row, column, guess[column])

                if statuses and column < len(statuses):
                    self.set_status(row, column, statuses[column])
                else:
                    self.set_status(row, column, "filled")
            else:
                self.clear_letter(row, column)

    def clear_board(self):
        for row_index, row in enumerate(self.word_cells):
            for column_index in range(len(row)):
                self.clear_letter(row_index, column_index)