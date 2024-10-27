import tensorflow as tf
import mediapipe as mp
import cv2
import numpy as np
import time
import os
import threading

class ASL:
    def __init__(self):
        self.result = ""  # Store the single result
        self.model = None
        self.actions = []
        self.type = "ASL"
        self.input_time = 0
        self.start_time = 0
        self.sequence = []
        self.sequence_length = 30
        self.prediction_allowed = False  # Boolean to control when predictions update `self.result`
        self.cap = cv2.VideoCapture(0)  # Open video capture once
        self.running = True  # Control the background thread

        # Start the continuous background thread for video capture and prediction
        self.prediction_thread = threading.Thread(target=self.continuous_predict, daemon=True)
        self.prediction_thread.start()

    def get_time(self):
        return time.time() - self.start_time

    def start(self):
        """Toggle prediction allowing and record start time."""
        self.result = ""
        self.start_time = time.time()
        self.prediction_allowed = True  # Allow prediction to update result

    def get_result(self):
        return self.result

    def stop(self):
        """Stops video capture and thread."""
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

    def load(self, trial):
        model_path = f"./models/{str(trial)}.keras"
        word_set_path = f"./word_sets/{str(trial)}.txt"

        # Load the model
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file {model_path} not found.")
            self.model = tf.keras.models.load_model(model_path)
            print("model: " + model_path)
            print(f"Successfully loaded model for trial {trial}.")
        except Exception as e:
            print(f"Error loading model: {e}")
            return

        # Load the word set
        try:
            if not os.path.exists(word_set_path):
                raise FileNotFoundError(f"Word set file {word_set_path} not found.")
            with open(word_set_path, 'r') as file:
                self.actions = file.read().splitlines()
            print(f"Successfully loaded word set for trial {trial}.")
        except Exception as e:
            print(f"Error loading word set: {e}")
            return


    def extract_keypoints(self, results):
        """Extract keypoints from Mediapipe results, excluding all face landmarks except eyebrows."""
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
        
        # Extract only eyebrow landmarks (adjust indices based on your specific MediaPipe model)
        if results.face_landmarks:
            eyebrow_indices = [70, 71, 72, 73, 74, 75, 76, 77, 78, 79]  # Example indices; adjust if needed
            face = np.array([[results.face_landmarks.landmark[i].x, 
                            results.face_landmarks.landmark[i].y, 
                            results.face_landmarks.landmark[i].z] for i in eyebrow_indices]).flatten()
        else:
            face = np.zeros(10 * 3)  # Size matches number of eyebrow landmarks (adjust based on exact indices used)
        
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 3)
        
        return np.concatenate([pose, face, lh, rh])

    def continuous_predict(self):
        """Continuously run video capture and make predictions without additional adjustments."""
        mp_holistic = mp.solutions.holistic
        sequence_length = 30  # Sequence length to consider for prediction

        if not self.cap.isOpened():
            print("Error: Could not open video stream from camera.")
            return

        with mp_holistic.Holistic(min_detection_confidence=0.3, min_tracking_confidence=0.6) as holistic:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera.")
                    break

                # Perform Mediapipe detection
                try:
                    image, results = self.mediapipe_detection(frame, holistic)
                    if results:
                        keypoints = self.extract_keypoints(results)
                        self.sequence.append(keypoints)
                        self.sequence = self.sequence[-sequence_length:]  # Ensure sequence has a maximum length
                except Exception as e:
                    print(f"Error during Mediapipe detection: {e}")
                    continue

                # Predict if sequence length is sufficient
                if len(self.sequence) == sequence_length and self.prediction_allowed:
                    try:
                        res = self.model.predict(np.expand_dims(self.sequence, axis=0))[0]
                        self.result = self.actions[np.argmax(res)]  # Set the direct prediction as result
                        print(f"Predicted action: {self.result}")
                        self.prediction_allowed = False  # Reset to wait for next `start()`
                    except Exception as e:
                        print(f"Error during prediction: {e}")
                        continue

    def mediapipe_detection(self, image, holistic):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = holistic.process(image)
        return image, results
