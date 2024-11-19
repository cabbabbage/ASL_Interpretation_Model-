from Devices.ASL_dev.src.backbone import TFLiteModel, get_model
from Devices.ASL_dev.src.landmarks_extraction import mediapipe_detection, extract_coordinates, load_json_file
from Devices.ASL_dev.src.config import SEQ_LEN, THRESH_HOLD
import numpy as np
import cv2
import mediapipe as mp
import threading


class ASL:
    def __init__(self, display_window=True):
        # Initialize MediaPipe and model paths
        self.mp_holistic = mp.solutions.holistic
        self.type = "ASL"  # Device type identifier for main.py

        # Prediction result and control for continuous prediction
        self.result = ""
        self.predicting = False

        # Load the sign-to-prediction map
        self.s2p_map = {k.lower(): v for k, v in load_json_file("Devices/ASL_dev/src/sign_to_prediction_index_map.json").items()}
        self.p2s_map = {v: k for k, v in self.s2p_map.items()}
        self.encoder = lambda x: self.s2p_map.get(x.lower())
        self.decoder = lambda x: self.p2s_map.get(x)

        # Load models
        self.models_path = ['Devices/ASL_dev/models/islr-fp16-192-8-seed42-fold0-best.h5']
        self.models = [get_model() for _ in self.models_path]
        for model, path in zip(self.models, self.models_path):
            model.load_weights(path, by_name=True, skip_mismatch=True)

        # TFLite model wrapper
        self.tflite_keras_model = TFLiteModel(islr_models=self.models)

        # Display control
        self.display_window = display_window

        # Start the continuous run in a separate thread
        self.run_thread = threading.Thread(target=self.run, daemon=True)
        self.run_thread.start()

    def start(self):
        """
        Start capturing and analyzing frames for ASL recognition.
        """
        self.result = ""
        self.predicting = True

    def get_result(self):
        """
        Get the latest prediction result.
        """
        return self.result

    def run(self):
        """
        Perform real-time ASL recognition using webcam feed continuously.
        """
        sequence_data = []
        cap = cv2.VideoCapture(0)

        # Reduce frame resolution for faster processing
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        with self.mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            frame_skip = 2  # Process every 2nd frame
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Skip frames for faster processing
                frame_count += 1
                if frame_count % frame_skip != 0:
                    continue

                # Flip and process frame
                image = cv2.flip(frame, 1)
                if self.predicting:
                    # Process frame using MediaPipe
                    image, results = mediapipe_detection(image, holistic)

                    try:
                        landmarks = extract_coordinates(results)
                    except Exception:
                        landmarks = np.zeros((468 + 21 + 33 + 21, 3))

                    sequence_data.append(landmarks)

                    # Predict every SEQ_LEN frames
                    if len(sequence_data) == SEQ_LEN:
                        prediction = self.tflite_keras_model(np.array(sequence_data, dtype=np.float32))["outputs"]
                        max_prob = np.max(prediction.numpy(), axis=-1)

                        if max_prob > 0.1:
                            self.result = self.decoder(np.argmax(prediction.numpy(), axis=-1))
                            self.predicting = False  # Stop predicting once result is obtained

                        sequence_data = []  # Clear sequence data after prediction

                # Display window if enabled
                if self.display_window:
                    cv2.putText(image, f"Result: {self.result}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.imshow('Webcam Feed', image)

                # Quit if 'q' key is pressed
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break

            cap.release()
            if self.display_window:
                cv2.destroyAllWindows()
