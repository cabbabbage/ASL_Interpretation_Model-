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
SEQUENCE_FPS = 30  # Frames per second
FRAME_DELAY = int(1000 / SEQUENCE_FPS)  # Delay in milliseconds

# Define the indices for different landmarks
POSE_LANDMARKS = 33 * 4  # Assuming each pose landmark has 4 values: x, y, z, visibility
FACE_LANDMARKS = 468 * 3  # Each face landmark has 3 values: x, y, z
HAND_LANDMARKS = 21 * 3  # Each hand landmark has 3 values: x, y, z

def visualize_keypoints(keypoints, image_size=(640, 480)):
    """
    Visualizes keypoints on a blank image.

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

        # Function to draw keypoints
        def draw_landmarks(landmarks, color=(0, 255, 0), radius=3):
            for point in landmarks:
                x, y = int(point[0] * width), int(point[1] * height)
                cv2.circle(image, (x, y), radius, color, -1)

        # Draw pose landmarks (white)
        draw_landmarks(pose, color=(255, 255, 255), radius=4)

        # Draw face landmarks (blue)
        draw_landmarks(face, color=(255, 0, 0), radius=2)

        # Draw left hand landmarks (green)
        draw_landmarks(left_hand, color=(0, 255, 0), radius=2)

        # Draw right hand landmarks (red)
        draw_landmarks(right_hand, color=(0, 0, 255), radius=2)

        return image
    except Exception as e:
        print(f"Error in visualize_keypoints: {e}")
        traceback.print_exc()
        # Return a blank image in case of error
        return np.zeros((image_size[1], image_size[0], 3), dtype=np.uint8)

def play_sequences(main_directory):
    """
    Plays each sequence of each action at 30 fps.

    Args:
        main_directory (str): Path to the main directory containing action subdirectories.
    """
    try:
        # Validate main directory
        if not os.path.isdir(main_directory):
            print(f"Error: The directory '{main_directory}' does not exist or is not a directory.")
            return

        # Get list of actions
        actions = [d for d in os.listdir(main_directory)
                   if os.path.isdir(os.path.join(main_directory, d))]
        actions.sort()  # Optional: sort actions alphabetically

        if not actions:
            print(f"No action directories found in '{main_directory}'.")
            return

        print(f"Found {len(actions)} action(s) in '{main_directory}': {actions}")

        for action in actions:
            action_path = os.path.join(main_directory, action)
            print(f"\nProcessing Action: '{action}'")

            # Get list of sequences
            sequences = [d for d in os.listdir(action_path)
                         if os.path.isdir(os.path.join(action_path, d))]
            sequences.sort()  # Optional: sort sequences numerically

            if not sequences:
                print(f"No sequences found in action '{action}'. Skipping to next action.")
                continue

            print(f"Found {len(sequences)} sequence(s) in action '{action}': {sequences}")

            for seq in sequences:
                seq_path = os.path.join(action_path, seq)
                print(f"\nPlaying Sequence: '{seq}' in Action: '{action}'")

                # Get list of frame files
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
                        # Load keypoints
                        keypoints = np.load(frame_file)

                        # Visualize keypoints
                        image = visualize_keypoints(keypoints)

                        # Display the image
                        cv2.imshow('ASL Sequence Playback', image)

                        # Wait for FRAME_DELAY milliseconds or until 'q' is pressed
                        if cv2.waitKey(FRAME_DELAY) & 0xFF == ord('q'):
                            print("Playback interrupted by user.")
                            cv2.destroyAllWindows()
                            sys.exit(0)

                    except Exception as e:
                        print(f"Error loading or displaying frame '{frame_file}': {e}")
                        traceback.print_exc()
                        continue  # Skip to next frame

                print(f"Finished playing sequence '{seq}' in action '{action}'.")

        print("\nAll sequences have been played.")
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"An unexpected error occurred in play_sequences: {e}")
        traceback.print_exc()

def main():
    # Use Tkinter to open a file explorer dialog for directory selection
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open the file explorer dialog
    main_directory = filedialog.askdirectory(title='Select Directory Containing Sequences')

    if not main_directory:
        print("No directory selected. Exiting.")
        return

    play_sequences(main_directory)

if __name__ == '__main__':
    main()
