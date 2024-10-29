import cv2
import numpy as np
import os
import mediapipe as mp
import tensorflow as tf
import tkinter as tk
from tkinter import filedialog, messagebox
import csv







# Load actions from actions.csv
def load_actions_from_csv(data_path):
    actions_csv_path = os.path.join(data_path, 'actions.csv')
    actions = []
    if not os.path.exists(actions_csv_path):
        print(f"Error: actions.csv not found in {data_path}")
        return []

    with open(actions_csv_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            actions.append(row[1])  # Adjust index if action names are in a different column
    return np.array(actions)

# Load .keras model file from selected directory
def load_model_from_directory():
    root = tk.Tk()
    root.withdraw()
    data_path = filedialog.askdirectory(title="Select directory containing actions.csv and model file (.keras)")
    if not data_path:
        messagebox.showerror("Error", "No directory selected.")
        return None, None, None
    actions = load_actions_from_csv(data_path)
    if len(actions) == 0:
        return None, None, None

    model_path = None
    for file in os.listdir(data_path):
        if file.endswith(".keras"):
            model_path = os.path.join(data_path, file)
            break
    if not model_path:
        messagebox.showerror("Error", "No model file (.keras) found in the selected directory.")
        return None, None, None
    return data_path, actions, tf.keras.models.load_model(model_path)

# Load model and actions
data_path, actions, model = load_model_from_directory()
if not model:
    print("Failed to load model or actions. Exiting.")
else:
    model.summary()

# Mediapipe setup
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

def mediapipe_detection(image, model):
    """Perform Mediapipe detection on an image."""
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = model.process(image)
    image.flags.writeable = True
    return image, results

def extract_keypoints(results):
    """Extract keypoints from Mediapipe results, excluding all face landmarks except eyebrows."""
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
    
    # Extract only eyebrow landmarks
    if results.face_landmarks:
        eyebrow_indices = [70, 71, 72, 73, 74, 75, 76, 77, 78, 79]
        face = np.array([[results.face_landmarks.landmark[i].x, 
                          results.face_landmarks.landmark[i].y, 
                          results.face_landmarks.landmark[i].z] for i in eyebrow_indices]).flatten()
    else:
        face = np.zeros(10 * 3)
    
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 3)
    
    return np.concatenate([pose, face, lh, rh])

def draw_styled_landmarks(image, results):
    """Draw only pose and hand landmarks on the image."""
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)


# Realtime detection variables
sequence, sentence, predictions = [], [], []
threshold, sequence_length = 0.5, 30

cap = cv2.VideoCapture(0)
with mp_holistic.Holistic(min_detection_confidence=0.7, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Make detections
        image, results = mediapipe_detection(frame, holistic)
        draw_styled_landmarks(image, results)

        # Extract keypoints and update sequence
        keypoints = extract_keypoints(results)
        sequence.append(keypoints)
        sequence = sequence[-sequence_length:]

        # Predict if sequence length is sufficient
        if len(sequence) == sequence_length:
            res = model.predict(np.expand_dims(sequence, axis=0))[0]
            predictions.append(np.argmax(res))

            if np.unique(predictions[-10:])[0] == np.argmax(res) and res[np.argmax(res)] > threshold:
                if len(sentence) == 0 or actions[np.argmax(res)] != sentence[-1]:
                    sentence.append(actions[np.argmax(res)])

            if len(sentence) > 5:
                sentence = sentence[-5:]

        # Display prediction on screen
        cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
        cv2.putText(image, ' '.join(sentence), (3, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Display the available actions
        y_offset = 60  # Start below the main display window
        for i, action in enumerate(actions):
            cv2.putText(image, action, (10, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

        # Show the frame
        cv2.imshow('Realtime LSTM Sign Language Detection', image)

        # Break gracefully
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
