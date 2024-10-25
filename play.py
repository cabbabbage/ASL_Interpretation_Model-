#!/usr/bin/env python3

import os
import numpy as np
import cv2
import glob
import sys
import traceback
import tkinter as tk
from tkinter import filedialog

# Constants
SEQUENCE_FPS = 30  # Slow down playback by a factor of 10
FRAME_DELAY = int(1000 / SEQUENCE_FPS)  # Delay in milliseconds

# Define the indices for different landmarks
POSE_LANDMARKS = 33 * 4  # Assuming each pose landmark has 4 values: x, y, z, visibility
FACE_LANDMARKS = 468 * 3  # Each face landmark has 3 values: x, y, z
HAND_LANDMARKS = 21 * 3  # Each hand landmark has 3 values: x, y, z

def visualize_keypoints(keypoints, image_size=(640, 480)):
    """
    Visualizes keypoints on a blank image and displays average hand positions.

    Args:
        keypoints (np.ndarray): Flattened array of keypoints.
        image_size (tuple): Size of the output image (width, height).

    Returns:
        np.ndarray: Image with keypoints drawn.
    """
    try:
        width, height = image_size
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Extract pose, face, and hand keypoints
        pose = keypoints[:POSE_LANDMARKS].reshape(-1, 4)  # x, y, z, visibility
        face = keypoints[POSE_LANDMARKS:POSE_LANDMARKS + FACE_LANDMARKS].reshape(-1, 3)  # x, y, z
        left_hand = keypoints[POSE_LANDMARKS + FACE_LANDMARKS:
                              POSE_LANDMARKS + FACE_LANDMARKS + HAND_LANDMARKS].reshape(-1, 3)  # x, y, z
        right_hand = keypoints[POSE_LANDMARKS + FACE_LANDMARKS + HAND_LANDMARKS:
                               POSE_LANDMARKS + FACE_LANDMARKS + 2 * HAND_LANDMARKS].reshape(-1, 3)  # x, y, z

        # Only remove rows where all elements are zero
        left_hand = left_hand[~np.all(left_hand == 0, axis=1)]
        right_hand = right_hand[~np.all(right_hand == 0, axis=1)]

        # Calculate average x, y for left and right hands if data is present
        avg_left_x, avg_left_y = "N/A", "N/A"
        avg_right_x, avg_right_y = "N/A", "N/A"

        if len(left_hand) > 0:
            avg_left_x = np.mean(left_hand[:, 0])
            avg_left_y = np.mean(left_hand[:, 1])

        if len(right_hand) > 0:
            avg_right_x = np.mean(right_hand[:, 0])
            avg_right_y = np.mean(right_hand[:, 1])

        # Only convert to screen coordinates if they are valid numbers
        if avg_left_x != "N/A" and avg_left_y != "N/A":
            avg_left_x, avg_left_y = int(avg_left_x * width), int(avg_left_y * height)
        if avg_right_x != "N/A" and avg_right_y != "N/A":
            avg_right_x, avg_right_y = int(avg_right_x * width), int(avg_right_y * height)

        # Function to draw keypoints
        def draw_landmarks(landmarks, color=(0, 255, 0), radius=3, visibility=None):
            for i, point in enumerate(landmarks):
                if visibility is not None and visibility[i] < 0.5:
                    continue
                x, y = int(np.clip(point[0], 0, 1) * width), int(np.clip(point[1], 0, 1) * height)
                cv2.circle(image, (x, y), radius, color, -1)

        # Draw pose landmarks (white), filtering with visibility score
        pose_landmarks = pose[:, :3]
        visibility = pose[:, 3]
        draw_landmarks(pose_landmarks, color=(255, 255, 255), radius=4, visibility=visibility)

        # Draw face landmarks (blue)
        draw_landmarks(face, color=(255, 0, 0), radius=2)

        # Draw left hand landmarks (green)
        draw_landmarks(left_hand, color=(0, 255, 0), radius=2)

        # Draw right hand landmarks (red)
        draw_landmarks(right_hand, color=(0, 0, 255), radius=2)

        # Display the average hand positions as text
        cv2.putText(image, f'Left Hand Avg X: {avg_left_x}, Y: {avg_left_y}', (10, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(image, f'Right Hand Avg X: {avg_right_x}, Y: {avg_right_y}', (10, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

        return image
    except Exception as e:
        print(f"Error in visualize_keypoints: {e}")
        traceback.print_exc()
        return np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8)



def play_sequences(main_directory):
    try:
        if not os.path.isdir(main_directory):
            print(f"Error: The directory '{main_directory}' does not exist or is not a directory.")
            return

        actions = [d for d in os.listdir(main_directory)
                   if os.path.isdir(os.path.join(main_directory, d))]
        actions.sort()

        if not actions:
            print(f"No action directories found in '{main_directory}'.")
            return

        print(f"Found {len(actions)} action(s) in '{main_directory}': {actions}")

        for action in actions:
            action_path = os.path.join(main_directory, action)
            print(f"\nProcessing Action: '{action}'")

            sequences = [d for d in os.listdir(action_path)
                         if os.path.isdir(os.path.join(action_path, d))]
            sequences.sort()

            if not sequences:
                print(f"No sequences found in action '{action}'. Skipping to next action.")
                continue

            print(f"Found {len(sequences)} sequence(s) in action '{action}': {sequences}")

            for seq in sequences:
                seq_path = os.path.join(action_path, seq)
                print(f"\nPlaying Sequence: '{seq}' in Action: '{action}'")

                frame_files = sorted(
                    glob.glob(os.path.join(seq_path, 'frame_*.npy')),
                    key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
                )

                if not frame_files:
                    print(f"No frame files found in sequence '{seq}'. Skipping to next sequence.")
                    continue

                print(f"Found {len(frame_files)} frame(s) in sequence '{seq}'.")

                for frame_file in frame_files:
                    try:
                        keypoints = np.load(frame_file)
                        image = visualize_keypoints(keypoints)

                        # Display the image
                        cv2.imshow('ASL Sequence Playback', image)

                        if cv2.waitKey(FRAME_DELAY) & 0xFF == ord('q'):
                            print("Playback interrupted by user.")
                            cv2.destroyAllWindows()
                            sys.exit(0)

                    except Exception as e:
                        print(f"Error loading or displaying frame '{frame_file}': {e}")
                        traceback.print_exc()
                        continue

                print(f"Finished playing sequence '{seq}' in action '{action}'.")

        print("\nAll sequences have been played.")
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"An unexpected error occurred in play_sequences: {e}")
        traceback.print_exc()

def main():
    root = tk.Tk()
    root.withdraw()

    main_directory = filedialog.askdirectory(title='Select Directory Containing Sequences', initialdir='./Model_data')

    if not main_directory:
        print("No directory selected. Exiting.")
        return

    play_sequences(main_directory)

if __name__ == '__main__':
    main()
