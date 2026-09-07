import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

def build_image_model(input_shape=(192, 192, 3), num_classes=29):
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=None,
    )

    inputs = keras.Input(shape=input_shape)

    x = layers.Rescaling(255.0)(inputs)
    x = preprocess_input(x)

    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(num_classes,activation="softmax")(x)

    return keras.Model(inputs,outputs,name="asl_mobilenetv2"
    )

class SignRecognizer:
    IMAGE_SIZE = (192, 192)
    HAND_PADDING = 0.2

    CONFIDENCE_THRESHOLD = 0.3

    CLASS_NAMES = (
        [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        + ["del", "nothing", "space"]
    )

    IMAGE_MODEL_WEIGHTS_PATH = ("models/asl.weights.h5")

    def __init__(
        self,
        prediction_interval_ms=100,
        debug_save_frames=False,
    ):
        self.prediction_interval_ms = prediction_interval_ms
        self.debug_save_frames = debug_save_frames

        self.image_model = build_image_model(
            input_shape=(*self.IMAGE_SIZE, 3),
            num_classes=len(self.CLASS_NAMES),
        )

        self.image_model.load_weights(self.IMAGE_MODEL_WEIGHTS_PATH)

        self.last_prediction_time = 0

        self.prediction = "Unknown"
        self.confidence = 0.0

    def should_predict(self, current_time_ms):
        return (current_time_ms - self.last_prediction_time >= self.prediction_interval_ms)

    def predict(
        self,
        frame,
        hand_landmarks,
        current_time_ms,
    ):
        if not self.should_predict(current_time_ms):
            return self.prediction, self.confidence

        self.last_prediction_time = current_time_ms

        image_input = self.prepare_image_input(frame, hand_landmarks)

        if image_input is None:
            self.prediction = "Unknown"
            self.confidence = 0.0

            return self.prediction, self.confidence

        predictions = self.image_model.predict(
            image_input,
            verbose=0,
        )[0]

        predicted_index = int(
            np.argmax(predictions)
        )

        confidence = float(
            predictions[predicted_index]
        )

        predicted_label = self.CLASS_NAMES[
            predicted_index
        ]

        self.prediction = self.format_prediction(
            predicted_label,
            confidence,
        )

        self.confidence = confidence

        return self.prediction, self.confidence

    def prepare_image_input(
        self,
        frame,
        hand_landmarks,
    ):
        frame_height, frame_width = frame.shape[:2]

        x_min, y_min, x_max, y_max = (
            self.get_hand_bbox(
                hand_landmarks,
                frame_width,
                frame_height,
            )
        )

        x_min, y_min, x_max, y_max = (
            self.apply_padding(
                x_min,
                y_min,
                x_max,
                y_max,
                frame_width,
                frame_height,
            )
        )

        x_min, y_min, x_max, y_max = (
            self.make_square(
                x_min,
                y_min,
                x_max,
                y_max,
                frame_width,
                frame_height,
            )
        )

        cropped = frame[y_min:y_max,x_min:x_max]

        if cropped.size == 0:
            return None

        hand_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)

        hand_rgb = cv2.resize(
            hand_rgb,
            self.IMAGE_SIZE,
            interpolation=cv2.INTER_AREA,
        )

        if self.debug_save_frames:
            cv2.imwrite(
                "debug_frame.jpg",
                cv2.cvtColor(
                    hand_rgb,
                    cv2.COLOR_RGB2BGR,
                ),
            )

        input_tensor = (hand_rgb.astype(np.float32) / 255.0)

        return np.expand_dims(input_tensor, axis=0)

    def get_hand_bbox(
        self,
        hand_landmarks,
        width,
        height,
    ):
        x_coordinates = [
            landmark.x
            for landmark
            in hand_landmarks.landmark
        ]

        y_coordinates = [
            landmark.y
            for landmark
            in hand_landmarks.landmark
        ]

        x_min = max(
            0,
            int(min(x_coordinates) * width),
        )

        x_max = min(
            width,
            int(max(x_coordinates) * width),
        )

        y_min = max(
            0,
            int(min(y_coordinates) * height),
        )

        y_max = min(
            height,
            int(max(y_coordinates) * height),
        )

        return (x_min, y_min, x_max, y_max)

    def apply_padding(
        self,
        x_min,
        y_min,
        x_max,
        y_max,
        width,
        height,
    ):
        box_width = x_max - x_min
        box_height = y_max - y_min

        padding_x = int(box_width * self.HAND_PADDING)
        padding_y = int(box_height * self.HAND_PADDING)

        x_min = max(0, x_min - padding_x)
        y_min = max(0, y_min - padding_y)
        x_max = min(width, x_max + padding_x)
        y_max = min(height, y_max + padding_y)

        return (x_min, y_min, x_max, y_max)

    def make_square(
        self,
        x_min,
        y_min,
        x_max,
        y_max,
        width,
        height,
    ):
        box_width = x_max - x_min
        box_height = y_max - y_min

        side = max(box_width, box_height)
        side = min(side, width, height)

        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2

        half = side // 2

        x_min = center_x - half
        y_min = center_y - half

        x_max = x_min + side
        y_max = y_min + side

        if x_min < 0:
            x_max -= x_min
            x_min = 0

        if y_min < 0:
            y_max -= y_min
            y_min = 0

        if x_max > width:
            x_min -= x_max - width
            x_max = width

        if y_max > height:
            y_min -= y_max - height
            y_max = height

        x_min = max(0, x_min)
        y_min = max(0, y_min)

        return (x_min, y_min, x_max, y_max)

    def format_prediction(
        self,
        predicted_label,
        confidence,
    ):
        if confidence < self.CONFIDENCE_THRESHOLD:
            return "Unknown"

        if predicted_label == "nothing":
            return "Unknown"

        if predicted_label == "space":
            return "ENTER"

        if predicted_label == "del":
            return "DELETE"

        return predicted_label