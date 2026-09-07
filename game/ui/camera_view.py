import time

import cv2
import mediapipe as mp

from recognition.sign_recognizer import SignRecognizer

from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import QImage, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

class CameraView(QWidget):
    WIDTH = 640
    HEIGHT = 420
    BOX_PADDING = 20

    CAMERA_INTERVAL_MS = 10
    PREDICTION_INTERVAL_MS = 100
    HOLD_DURATION_MS = 1000
    MIN_CONFIDENCE_FOR_INPUT = 0.3

    letter_confirmed = Signal(str)

    def __init__(self):
        super().__init__()

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setObjectName("cameraView")

        self.capture = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )

        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.recognizer = SignRecognizer(
            prediction_interval_ms=self.PREDICTION_INTERVAL_MS,
            debug_save_frames=True,
        )

        self.frame = None
        self.hand_bbox = None

        self.prediction = "Unknown"
        self.confidence = 0.0

        self.reset_input_state()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(self.CAMERA_INTERVAL_MS)

    def reset_input_state(self):
        self.held_prediction = None
        self.held_since_ms = None
        self.awaiting_release = False
        self.hold_progress = 0.0

    def pause(self):
        self.timer.stop()

    def resume(self):
        if not self.timer.isActive():
            self.timer.start(self.CAMERA_INTERVAL_MS)

    def get_status_color(self):
        confidence_percent = self.confidence * 100

        if confidence_percent > 50:
            return Qt.GlobalColor.green

        if confidence_percent >= 30:
            return Qt.GlobalColor.yellow

        return Qt.GlobalColor.red

    def update_camera(self):
        success, frame = self.capture.read()

        if not success:
            return

        current_time_ms = self.get_current_time_ms()
        frame = self.prepare_frame(frame)

        results = self.detect_hands(frame)

        self.process_detection(
            frame,
            results,
            current_time_ms
        )

        self.process_gesture_input(current_time_ms)

        self.frame = frame
        self.update()

    def get_current_time_ms(self):
        return int(time.monotonic() * 1000)

    def prepare_frame(self, frame):
        return cv2.flip(frame, 1)

    def detect_hands(self, frame):
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        return self.hands.process(rgb_frame)

    def process_detection(
        self,
        frame,
        results,
        current_time_ms
    ):
        self.hand_bbox = None

        if not results.multi_hand_landmarks:
            self.reset_prediction()
            return

        hand_landmarks = results.multi_hand_landmarks[0]

        self.hand_bbox = self.get_hand_boundbox(
            hand_landmarks,
            frame
        )

        self.predict_hand_sign(
            frame,
            hand_landmarks,
            current_time_ms
        )


    def get_hand_boundbox(self, hand_landmarks, frame):
        frame_height, frame_width, _ = frame.shape

        x_coordinates = [
            int(landmark.x * frame_width)
            for landmark in hand_landmarks.landmark
        ]

        y_coordinates = [
            int(landmark.y * frame_height)
            for landmark in hand_landmarks.landmark
        ]

        return (
            max(min(x_coordinates), 0),
            max(min(y_coordinates), 0),
            min(max(x_coordinates), frame_width),
            min(max(y_coordinates), frame_height),
        )

    def predict_hand_sign(
        self,
        frame,
        hand_landmarks,
        current_time_ms
    ):
        self.prediction, self.confidence = (
            self.recognizer.predict(
                frame,
                hand_landmarks,
                current_time_ms,
            )
        )

    def reset_prediction(self):
        self.prediction = "Unknown"
        self.confidence = 0.0

    def process_gesture_input(self, current_time_ms):
        is_confident_gesture = (
            self.prediction != "Unknown"
            and self.confidence >= self.MIN_CONFIDENCE_FOR_INPUT
        )

        if not is_confident_gesture:
            self.reset_input_state()
            return

        if self.awaiting_release:
            return

        if self.prediction != self.held_prediction:
            self.held_prediction = self.prediction
            self.held_since_ms = current_time_ms

        hold_duration = current_time_ms - self.held_since_ms
        self.hold_progress = min(hold_duration / self.HOLD_DURATION_MS, 1.0)

        if hold_duration >= self.HOLD_DURATION_MS:
            self.letter_confirmed.emit(self.held_prediction)
            self.awaiting_release = True
            self.hold_progress = 1.0

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.frame is None:
            painter.fillRect(
                self.rect(),
                Qt.GlobalColor.black
            )
            return

        frame = self.frame
        frame_height, frame_width, _ = frame.shape

        image = QImage(
            frame.data,
            frame_width,
            frame_height,
            frame.strides[0],
            QImage.Format.Format_BGR888,
        )

        scaled_size = image.size().scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

        x_offset = (self.width() - scaled_size.width()) // 2

        y_offset = (self.height() - scaled_size.height()) // 2

        image_rect = QRectF(
            x_offset,
            y_offset,
            scaled_size.width(),
            scaled_size.height()
        )

        painter.fillRect(
            self.rect(),
            Qt.GlobalColor.white
        )

        painter.drawImage(image_rect, image)

        if self.hand_bbox is None:
            return

        x_min, y_min, x_max, y_max = self.hand_bbox

        scale_x = (scaled_size.width() / frame_width)
        scale_y = (scaled_size.height() / frame_height)

        x = int(x_min * scale_x + x_offset)
        y = int(y_min * scale_y + y_offset)

        width = int((x_max - x_min) * scale_x)
        height = int((y_max - y_min) * scale_y)

        x -= self.BOX_PADDING
        y -= self.BOX_PADDING

        width += self.BOX_PADDING * 2
        height += self.BOX_PADDING * 2

        x = max(0, x)
        y = max(0, y)

        width = min(width, self.width() - x)
        height = min(height, self.height() - y)

        color = self.get_status_color()

        pen = QPen(color)
        pen.setWidth(1)

        painter.setPen(pen)
        painter.drawRect(
            x,
            y,
            width,
            height
        )

        font = QFont()
        font.setPointSize(16)

        painter.setFont(font)
        painter.setPen(color)

        confidence_percent = self.confidence * 100

        prediction_text = (f"{self.prediction}   "f"{confidence_percent:.0f}%")

        painter.drawText(x,max(20, y - 8),prediction_text,)

        if self.hold_progress > 0:
            bar_height = 4
            bar_y = y + height + 4

            painter.setPen(Qt.PenStyle.NoPen)

            painter.setBrush(Qt.GlobalColor.lightGray)
            painter.drawRect(x, bar_y, width, bar_height)

            painter.setBrush(color)
            painter.drawRect(
                x,
                bar_y,
                int(width * self.hold_progress),
                bar_height,
            )

    def closeEvent(self, event):
        self.timer.stop()

        if self.capture.isOpened():
            self.capture.release()

        self.hands.close()

        event.accept()