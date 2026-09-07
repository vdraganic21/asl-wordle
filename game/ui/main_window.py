from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QTimer
from PySide6.QtGui import QIntValidator, QPixmap, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from game_logic import LetterStatus
from ui.board import Board
from ui.camera_view import CameraView
from ui.keyboard import Keyboard

class MainWindow(QMainWindow):
    WINDOW_WIDTH = 1920

    SHARE_COPIED_LABEL_MS = 1500

    HELP_IMAGE_PATH = "assets/help.png"
    HELP_ANIMATION_MS = 250

    def __init__(self, game_logic):
        super().__init__()

        self.game_logic = game_logic

        self.setWindowTitle("ASL Word Game")
        self.setFixedWidth(self.WINDOW_WIDTH)

        self.setup_ui()
        self.refresh_board()

        self.adjustSize()
        self.setFixedHeight(self.height())

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(60, 30, 60, 40)
        main_layout.setSpacing(20)

        self.create_header(main_layout)
        self.create_content(main_layout)

    def create_header(self, parent_layout):
        header_widget = QWidget()
        header_widget.setFixedHeight(50)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        left_section = self.create_left_controls()
        left_section.setFixedWidth(300)

        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.update_title()

        right_spacer = QWidget()
        right_spacer.setFixedWidth(300)

        header_layout.addWidget(
            left_section,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        header_layout.addWidget(
            self.title_label,
            stretch=1
        )

        header_layout.addWidget(right_spacer)
        parent_layout.addWidget(header_widget)

    def create_left_controls(self):
        left_widget = QWidget()

        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        new_game_button = QPushButton("New Game")
        new_game_button.setObjectName("newGameButton")
        new_game_button.clicked.connect(self.start_new_game)

        self.word_id_input = QLineEdit()
        self.word_id_input.setObjectName("wordIdInput")
        self.word_id_input.setPlaceholderText("Word #")
        self.word_id_input.setFixedWidth(70)

        self.word_id_input.setFixedHeight(
            new_game_button.sizeHint().height()
        )

        self.word_id_input.setValidator(
            QIntValidator(1, len(self.game_logic.words))
        )
        self.word_id_input.returnPressed.connect(self.start_new_game)

        left_layout.addWidget(new_game_button)
        left_layout.addWidget(self.word_id_input)

        return left_widget

    def start_new_game(self):
        word_id_text = self.word_id_input.text().strip()

        if word_id_text:
            result = self.game_logic.get_word_by_id(int(word_id_text))

            if result is None:
                return
        else:
            self.game_logic.new_game()

        self.word_id_input.clear()
        self.start_fresh_round()

    def start_fresh_round(self):
        self.board.clear_board()
        self.camera.reset_input_state()
        self.keyboard.reset()
        self.collapse_help_panel()

        self.show_camera_view()

        self.update_title()
        self.refresh_board()

    def update_title(self):
        word_id = self.game_logic.current_word_id

        status = ""

        if self.game_logic.game_over:
            if self.game_logic.won:
                status = " - solved!"
            else:
                status = f" - word was {self.game_logic.current_word.upper()}"

        self.title_label.setText(
            f"ASL Word Game - #{word_id}{status}"
        )

    def create_content(self, parent_layout):
        content_layout = QHBoxLayout()
        content_layout.setSpacing(100)
        content_layout.addStretch()

        board_section = self.create_board_section()
        content_layout.addWidget(board_section)

        camera_section = self.create_camera_section()
        content_layout.addWidget(camera_section)

        content_layout.addStretch()
        parent_layout.addLayout(content_layout)

    def create_board_section(self):
        board_layout = QVBoxLayout()
        board_layout.setSpacing(20)
        board_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.board = Board()
        self.keyboard = Keyboard()

        board_layout.addWidget(
            self.board,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        board_layout.addWidget(
            self.keyboard,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        container = QWidget()
        container.setLayout(board_layout)

        return container

    def create_camera_section(self):
        self.camera_page = self.create_camera_page()
        self.result_page = self.create_result_page()

        self.result_page.hide()

        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.addWidget(self.camera_page)
        section_layout.addWidget(self.result_page)

        container = QWidget()
        container.setLayout(section_layout)

        return container

    def create_camera_page(self):
        camera_layout = QVBoxLayout()
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.setSpacing(15)
        camera_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.camera = CameraView()
        self.camera.letter_confirmed.connect(self.handle_letter_input)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.help_button = QPushButton("Help")
        self.help_button.setObjectName("helpButton")
        self.help_button.setCheckable(True)
        self.help_button.toggled.connect(self.toggle_help_panel)

        button_layout.addWidget(self.help_button)

        self.help_panel = self.create_help_panel()

        camera_layout.addWidget(self.camera)
        camera_layout.addLayout(button_layout)
        camera_layout.addWidget(self.help_panel)

        page = QWidget()
        page.setLayout(camera_layout)

        spacing = camera_layout.spacing()
        button_row_height = self.help_button.sizeHint().height()

        self.camera_column_height = (
            CameraView.HEIGHT
            + spacing
            + button_row_height
            + spacing
            + CameraView.HEIGHT
        )

        page.setFixedSize(CameraView.WIDTH, self.camera_column_height)

        return page

    def create_help_panel(self):
        panel = QLabel()
        panel.setObjectName("helpPanel")
        panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel.setFixedWidth(CameraView.WIDTH)
        panel.setMaximumHeight(0)

        pixmap = QPixmap(self.HELP_IMAGE_PATH)

        if pixmap.isNull():
            panel.setText(f"Add a help image at:\n{self.HELP_IMAGE_PATH}")
        else:
            scaled_pixmap = pixmap.scaled(
                CameraView.WIDTH,
                CameraView.HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            panel.setPixmap(scaled_pixmap)

        return panel

    def toggle_help_panel(self, checked):
        self.help_button.setText("Hide Help" if checked else "Show Help")

        target_height = CameraView.HEIGHT if checked else 0

        animation = QPropertyAnimation(self.help_panel, b"maximumHeight", self)
        animation.setDuration(self.HELP_ANIMATION_MS)
        animation.setStartValue(self.help_panel.maximumHeight())
        animation.setEndValue(target_height)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()

        self._help_animation = animation

    def collapse_help_panel(self):
        self.help_button.blockSignals(True)
        self.help_button.setChecked(False)
        self.help_button.setText("Show Help")
        self.help_button.blockSignals(False)

        self.help_panel.setMaximumHeight(0)

    def create_result_page(self):
        result_layout = QVBoxLayout()
        result_layout.setSpacing(20)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_message_label = QLabel()
        self.result_message_label.setObjectName("resultMessage")
        self.result_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_message_label.setWordWrap(True)

        self.share_button = QPushButton("Share Result")
        self.share_button.setObjectName("shareButton")
        self.share_button.clicked.connect(self.share_result)

        result_layout.addWidget(self.result_message_label)
        result_layout.addWidget(
            self.share_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        page = QWidget()
        page.setLayout(result_layout)
        page.setFixedSize(CameraView.WIDTH, self.camera_column_height)

        return page

    def show_camera_view(self):
        self.result_page.hide()
        self.camera_page.show()
        self.camera.resume()

    def show_win_screen(self):
        attempts_used = len(self.game_logic.attempts)
        max_attempts = self.game_logic.MAX_ATTEMPTS

        self.show_result_screen(
            f"Solved it in {attempts_used}/{max_attempts}!"
        )

    def show_lose_screen(self):
        word = self.game_logic.current_word.upper()

        self.show_result_screen(
            f"Out of attempts! The word was '{word}'."
        )

    def show_result_screen(self, headline):
        self.camera.pause()
        self.collapse_help_panel()

        self.result_message_label.setText(
            f"{headline}\n\n{self.build_share_text()}"
        )

        self.camera_page.hide()
        self.result_page.show()

    def build_share_text(self):
        emoji_by_status = {
            LetterStatus.CORRECT: "🟩",
            LetterStatus.PRESENT: "🟨",
            LetterStatus.ABSENT: "⬛",
        }

        word_id = self.game_logic.current_word_id
        max_attempts = self.game_logic.MAX_ATTEMPTS

        attempts_label = (
            str(len(self.game_logic.attempts))
            if self.game_logic.won
            else "X"
        )

        lines = [f"ASL Word Game #{word_id} {attempts_label}/{max_attempts}"]

        for _, statuses in self.game_logic.attempts:
            row = "".join(
                emoji_by_status[status] for status in statuses
            )
            lines.append(row)

        return "\n".join(lines)

    def share_result(self):
        QApplication.clipboard().setText(self.build_share_text())

        self.share_button.setText("Copied!")

        QTimer.singleShot(
            self.SHARE_COPIED_LABEL_MS,
            lambda: self.share_button.setText("Share Result"),
        )

    def handle_letter_input(self, letter):
        if self.game_logic.game_over:
            return

        if letter == "ENTER":
            statuses = self.game_logic.submit_guess()

            if statuses is None:
                return

        elif letter == "DELETE":
            self.game_logic.delete_letter()

        else:
            self.game_logic.add_letter(letter)

        self.refresh_board()
        self.update_title()

        if self.game_logic.game_over:
            if self.game_logic.won:
                self.show_win_screen()
            else:
                self.show_lose_screen()

    def refresh_board(self):
        for row, (guess, statuses) in enumerate(self.game_logic.attempts):
            self.board.set_row(row, guess, statuses)

        current_row = self.game_logic.current_row

        if current_row < self.game_logic.MAX_ATTEMPTS:
            self.board.set_row(current_row, self.game_logic.current_guess)

        self.keyboard.update_statuses(self.game_logic.get_letter_statuses())

    def keyPressEvent(self, event: QKeyEvent):
        if self.word_id_input.hasFocus():
            super().keyPressEvent(event)
            return

        key = event.key()

        if key == Qt.Key.Key_Backspace:
            self.handle_letter_input("DELETE")
            event.accept()
            return

        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.handle_letter_input("ENTER")
            event.accept()
            return

        text = event.text().upper()

        if len(text) == 1 and text.isalpha():
            self.handle_letter_input(text)
            event.accept()
            return

        super().keyPressEvent(event)