#!/usr/bin/env python3

import os
import numpy as np
import glob
import csv
from dtw import dtw
from sklearn_extra.cluster import KMedoids
import traceback

# Constants and variables
DATA_PATH = './actions'  # Or your data path
CSV_FILE = 'action_directory.csv'
NUM_LANDMARKS_HAND = 21 * 3  # Assuming each hand has 21 landmarks with x, y, z coordinates

def process_all_sequences():
    """Process all sequences: interpolate missing keypoints, compare and filter sequences."""
    try:
        # Load the CSV file
        print("Loading CSV file...")
        with open(CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            rows = list(reader)

        actions_to_update = []  # To track the rows that need updating to "2"

        # Loop through all actions listed in the CSV
        for row_idx, row in enumerate(rows):
            if row[0] == "2":
                print(f"Action '{row[1]}' has already been processed. Skipping...")
                continue  # Skip actions that have already been processed

            # Process the action if it has a "1"
            if row[0] == "1":
                action = row[1]
                print(f"\nProcessing action: '{action}'")

                action_path = os.path.join(DATA_PATH, action)

                # Check if action directory exists
                if not os.path.exists(action_path):
                    print(f"Action directory '{action_path}' does not exist. Skipping action.")
                    continue

                # Find all the sequences for the action
                sequence_dirs = sorted(glob.glob(os.path.join(action_path, 'seq_*')))
                print(f"Found {len(sequence_dirs)} sequences for action '{action}'.")

                action_sequences = []

                for seq_idx, sequence_dir in enumerate(sequence_dirs):
                    print(f"\nProcessing sequence {seq_idx} in action '{action}'...")
                    # Find all the frame files for the sequence
                    frame_files = sorted(
                        glob.glob(os.path.join(sequence_dir, 'frame_*.npy')),
                        key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
                    )
                    print(f"Found {len(frame_files)} frames in sequence {seq_idx}.")

                    if not frame_files:
                        print(f"No frames found in sequence {seq_idx}. Skipping sequence.")
                        continue

                    # Load all the frames into a list
                    try:
                        sequence = [np.load(frame_file) for frame_file in frame_files]
                    except Exception as e:
                        print(f"Error loading frames in sequence {seq_idx}: {e}")
                        continue

                    # Interpolate missing data in the sequence
                    print(f"Interpolating missing data in sequence {seq_idx}...")
                    sequence = interpolate_sequence(sequence)

                    # Save the updated frames back
                    for idx, frame_file in enumerate(frame_files):
                        np.save(frame_file, sequence[idx])

                    action_sequences.append(np.array(sequence))

                if not action_sequences:
                    print(f"No valid sequences found for action '{action}'. Skipping action.")
                    continue

                # Now, find the representative sequence
                try:
                    print(f"\nFinding representative sequence for action '{action}'...")
                    flattened_sequences = [seq.flatten() for seq in action_sequences]
                    X = np.array(flattened_sequences)
                    # Apply K-Medoids clustering with n_clusters=1 to find the medoid
                    kmedoids = KMedoids(n_clusters=1, metric='euclidean', random_state=0).fit(X)
                    medoid_index = kmedoids.medoid_indices_[0]
                    representative_sequence = action_sequences[medoid_index]
                except Exception as e:
                    print(f"Error finding representative sequence for action '{action}': {e}")
                    traceback.print_exc()
                    continue

                # Filter each sequence
                for idx, seq in enumerate(action_sequences):
                    print(f"\nFiltering sequence {idx} in action '{action}'...")
                    try:
                        filtered_seq = filter_sequence(seq, representative_sequence)

                        # Save the filtered sequence
                        seq_output_path = os.path.join(action_path, f'seq_{idx}')
                        os.makedirs(seq_output_path, exist_ok=True)
                        for frame_idx, frame in enumerate(filtered_seq):
                            if frame is not None:  # Only save non-None frames
                                frame_output_path = os.path.join(seq_output_path, f'frame_{frame_idx}.npy')
                                np.save(frame_output_path, frame)
                    except Exception as e:
                        print(f"Error filtering sequence {idx} in action '{action}': {e}")
                        traceback.print_exc()
                        continue

                # Mark the action as successfully processed by changing "1" to "2"
                rows[row_idx][0] = "2"
                actions_to_update.append(action)

        # Write the updated CSV back to the file if there were any changes
        if actions_to_update:
            with open(CSV_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            print(f"\nSuccessfully updated the CSV for actions: {', '.join(actions_to_update)}")
        else:
            print("\nNo actions were processed or updated.")

        print("\nAll sequences processed: interpolation, comparing, and filtering completed.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()

def interpolate_sequence(sequence):
    """Interpolate missing keypoints in the sequence."""
    try:
        for i in range(1, len(sequence) - 1):
            # Define the range for left and right hand keypoints
            lh_start = 33 * 4 + 468 * 3
            lh_end = lh_start + NUM_LANDMARKS_HAND
            rh_start = lh_end
            rh_end = rh_start + NUM_LANDMARKS_HAND

            # For each keypoint in the hand (x, y, z)
            for idx in range(lh_start, lh_end, 3):
                if np.all(sequence[i][idx:idx + 3] == 0):  # Check if current keypoint is missing (x, y, z are all 0)
                    prev_idx = next_idx = None

                    # Find the previous valid frame with data
                    for j in range(i - 1, -1, -1):
                        if not np.all(sequence[j][idx:idx + 3] == 0):
                            prev_idx = j
                            break

                    # Find the next valid frame with data
                    for j in range(i + 1, len(sequence)):
                        if not np.all(sequence[j][idx:idx + 3] == 0):
                            next_idx = j
                            break

                    # If valid start and end frames are found, interpolate
                    if prev_idx is not None and next_idx is not None:
                        for interp_idx in range(prev_idx + 1, next_idx):
                            alpha = (interp_idx - prev_idx) / (next_idx - prev_idx)
                            sequence[interp_idx][idx:idx + 3] = (1 - alpha) * sequence[prev_idx][idx:idx + 3] + alpha * sequence[next_idx][idx:idx + 3]

            # Repeat for right hand keypoints
            for idx in range(rh_start, rh_end, 3):
                if np.all(sequence[i][idx:idx + 3] == 0):
                    prev_idx = next_idx = None

                    # Find the previous valid frame with data
                    for j in range(i - 1, -1, -1):
                        if not np.all(sequence[j][idx:idx + 3] == 0):
                            prev_idx = j
                            break

                    # Find the next valid frame with data
                    for j in range(i + 1, len(sequence)):
                        if not np.all(sequence[j][idx:idx + 3] == 0):
                            next_idx = j
                            break

                    # If valid start and end frames are found, interpolate
                    if prev_idx is not None and next_idx is not None:
                        for interp_idx in range(prev_idx + 1, next_idx):
                            alpha = (interp_idx - prev_idx) / (next_idx - prev_idx)
                            sequence[interp_idx][idx:idx + 3] = (1 - alpha) * sequence[prev_idx][idx:idx + 3] + alpha * sequence[next_idx][idx:idx + 3]

        return sequence
    except Exception as e:
        print(f"Error during interpolation: {e}")
        traceback.print_exc()
        return sequence

from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

def filter_sequence(seq, representative_sequence):
    """Filter the sequence using DTW to align with the representative sequence."""
    try:
        # Compute DTW between the sequence and representative sequence
        distance, path = fastdtw(seq, representative_sequence, dist=euclidean)

        # Extract the matching subsequence
        indices_seq = [index[0] for index in path]  # Indices in the original sequence

        # Find the longest continuous segment in indices_seq
        segments = []
        start = indices_seq[0]
        prev = indices_seq[0]
        for idx_seq in indices_seq[1:]:
            if idx_seq == prev + 1:
                prev = idx_seq
            else:
                segments.append((start, prev))
                start = idx_seq
                prev = idx_seq
        segments.append((start, prev))

        # Find the segment with the maximum length (most complete)
        longest_segment = max(segments, key=lambda x: x[1] - x[0])

        # Extract the subsequence corresponding to the longest segment
        start_idx, end_idx = longest_segment

        # Set frames outside the matching subsequence to None (making them invisible)
        filtered_seq = [None if i < start_idx or i > end_idx else seq[i] for i in range(len(seq))]

        print(f"Filtered sequence length: {len([f for f in filtered_seq if f is not None])} frames (non-matching frames removed)")
        return filtered_seq
    except Exception as e:
        print(f"Error during filtering: {e}")
        traceback.print_exc()
        return seq  # Return original sequence if error occurs


if __name__ == '__main__':
    process_all_sequences()
