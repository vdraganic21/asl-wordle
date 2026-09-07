import sys
from PySide6.QtWidgets import QApplication
from game_logic import GameLogic
from ui.main_window import MainWindow

def load_styles(app):
    with open("styles/main.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

def main():
    app = QApplication(sys.argv)

    load_styles(app)

    game_logic = GameLogic()

    window = MainWindow(game_logic)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()