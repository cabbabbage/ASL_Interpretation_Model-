"""
Real-time ASL (American Sign Language) Recognition

This class uses a pre-trained TFLite model to perform real-time ASL recognition using webcam feed. It utilizes the MediaPipe library for hand tracking and landmark extraction.

Author: 209sontung

Date: May 2023
"""

from Devices.ASL_dev.src.backbone import TFLiteModel, get_model
from Devices.ASL_dev.src.landmarks_extraction import mediapipe_detection, draw, extract_coordinates, load_json_file
from Devices.ASL_dev.src.config import SEQ_LEN, THRESH_HOLD
import numpy as np
import cv2
import time
import mediapipe as mp
import threading

class ASL:
    def __init__(self):
        # Initialize MediaPipe and model paths
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.type = "ASL"  # Device type identifier for main.py

        # Prediction result, input time, and control for continuous prediction
        self.result = ""
        self.input_time = 0
        self.start_time = 0
        self.predicting = False

        # Load the sign to prediction map
        self.s2p_map = {k.lower(): v for k, v in load_json_file("Devices/ASL_dev/src/sign_to_prediction_index_map.json").items()}
        self.p2s_map = {v: k for k, v in self.s2p_map.items()}
        self.encoder = lambda x: self.s2p_map.get(x.lower())
        self.decoder = lambda x: self.p2s_map.get(x)
        
        # Load models
        self.models_path = ['Devices/ASL_dev/models/islr-fp16-192-8-seed_all42-foldall-last.h5']
        self.models = [get_model() for _ in self.models_path]
        for model, path in zip(self.models, self.models_path):
            model.load_weights(path)
        
        # TFLite model wrapper
        self.tflite_keras_model = TFLiteModel(islr_models=self.models)

        # Start the continuous run in a separate thread
        self.run_thread = threading.Thread(target=self.run, daemon=True)
        self.run_thread.start()

    def start(self):
        """
        Start capturing and analyzing frames for ASL recognition.
        This method initiates the process and sets predicting to True.
        """
        self.result = ""
        self.start_time = time.time()
        self.predicting = True  # Start predicting

    def get_result(self):
        """
        Get the latest prediction result.
        """
        return self.result

    def get_time(self):
        """
        Get the time taken to reach a prediction result.
        """
        self.input_time = time.time() - self.start_time
        return self.input_time

    def run(self):
        """
        Perform real-time ASL recognition using webcam feed continuously.
        """
        sequence_data = []
        cap = cv2.VideoCapture(0)
        
        with self.mp_holistic.Holistic(min_detection_confidence=0.1, min_tracking_confidence=0.1) as holistic:
            print ("*****************************" + str(THRESH_HOLD) + "   YESSS")
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Process frame and detect landmarks if predicting is True
                image = cv2.flip(frame, 1)
                if self.predicting:
                    image, results = mediapipe_detection(image, holistic)
                    
                    # Draw landmarks on hands if detected
                    if results.left_hand_landmarks:
                        self.mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp.solutions.holistic.HAND_CONNECTIONS)
                    if results.right_hand_landmarks:
                        self.mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp.solutions.holistic.HAND_CONNECTIONS)
                    
                    try:
                        landmarks = extract_coordinates(results)
                    except:
                        landmarks = np.zeros((468 + 21 + 33 + 21, 3))

                    sequence_data.append(landmarks)

                    # Generate prediction every SEQ_LEN frames
                    if len(sequence_data) % SEQ_LEN == 0:
                        prediction = self.tflite_keras_model(np.array(sequence_data, dtype=np.float32))["outputs"]
                        
                        if np.max(prediction.numpy(), axis=-1) > .2:
                            self.result = self.decoder(np.argmax(prediction.numpy(), axis=-1))
                            self.input_time = time.time() - self.start_time
                            self.predicting = False  # Stop predicting once result is obtained
                        
                        sequence_data = []  # Clear sequence data after prediction

                # Display result text on the frame
                cv2.putText(image, f"Result: {self.result}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.imshow('Webcam Feed', image)

                # Quit if 'q' key is pressed
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
