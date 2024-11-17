import json
import random
import os

# Paths
json_path = '../Devices/ASL_dev/src/sign_to_prediction_index_map.json'
output_dir = '.'

# Delete existing files if they exist
for file_name in ['1.txt', '2.txt', '3.txt', 'all.txt']:
    file_path = os.path.join(output_dir, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted existing file: {file_path}")

# Load words from JSON
with open(json_path, 'r') as f:
    data = json.load(f)
    words = list(data.keys())

# Write all words to all.txt
all_file_path = os.path.join(output_dir, 'all.txt')
with open(all_file_path, 'w') as f:
    f.write('\n'.join(words))
print(f"Created file: {all_file_path}")

# Make sure there are at least 30 unique words
if len(words) < 30:
    raise ValueError("Not enough unique words in the JSON file to select 30.")

# Randomly select 30 words and split them into 3 sets of 10 words each
random_words = random.sample(words, 30)
random.shuffle(random_words)

word_sets = [random_words[i:i + 10] for i in range(0, 30, 10)]

# Write each set of 10 words to separate files 1.txt, 2.txt, and 3.txt
for i, word_set in enumerate(word_sets, start=1):
    file_path = os.path.join(output_dir, f'{i}.txt')
    with open(file_path, 'w') as f:
        f.write('\n'.join(word_set))
    print(f"Created file: {file_path}")
