import os
import csv
import json

# Load the JSON file
with open('actions.json', 'r') as f:
    data = json.load(f)

# Prepare the CSV file
csv_file = 'action_directory.csv'

# Function to check if video file exists
def video_exists(video_id):
    return os.path.exists(f'videos/{video_id}.mp4')

# Open the CSV file to write data
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)

    # Iterate through each action (e.g., napkin) in the JSON
    for action_data in data:
        action = action_data['gloss']
        row = ["0", action]  # Start the row with "0" and the action

        # Iterate through each instance (video)
        for instance in action_data['instances']:
            video_id = instance['video_id']
            video_filename = f'{video_id}.mp4'

            # Check if the video exists in the "videos" folder
            if video_exists(video_id):
                row.append(video_filename)
            else:
                print(f'{video_filename} does not exist for {action}')

        # Write the row to the CSV file
        writer.writerow(row)

print(f"CSV file '{csv_file}' created successfully.")
