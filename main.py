from Devices.ASL_dev.ASL import ASL
from Utils.consent import Consent  
from Devices.keys import Keyboard
import time
import tkinter as tk
from tkinter import Label, Button
import os
import csv
import random
import sys
from tkinter import Label, Button

# Global variable to control the skip functionality
skip = False

def get_word_sets():
    word_sets = []
    for i in range(1, 4):
        file_path = f'./Experiment_Word_Sets/{i}.txt'
        if os.path.exists(file_path):

            try:
                with open(file_path, 'r') as file:
                    words = file.read().splitlines()
                    word_sets.append(words)
                print(f"Loaded word set from {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        else:
            print(f"File {file_path} not found.")  
    return word_sets

def compare(device, target, consent_form, trial):
    result = device.result
    input_time = device.input_time
    correct = int(device.result == target)
    
    file_path = f"./Experiment Results/{consent_form.getUserID()}/{device.type}/trial_{str(trial)}.csv"
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_exists = os.path.isfile(file_path)
    
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Correct', 'Target', 'Result', 'Input Time (s)'])
            writer.writerow([correct, target, result, input_time])
        #print(f"Comparison result saved to {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
    
    if result == "":
        return True
    return correct


def instructions_and_start(device, trial):
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.title(f"Trial {trial} - {device.type} Device")

        # Define instruction text based on the device type
        if device.type == "ASL":
            instructions_text = (
                "Instructions:\n\n"
                "1. Please sign each word shown on the screen.\n"
                "2. The same word may appear multiple times; continue signing "
                "until the word changes.\n\n"
                "When you are ready, press 'Start Trial' below to begin."
            )
        else:
            instructions_text = (
                "Instructions:\n\n"
                "1. Please type each word displayed on the screen and press 'Enter'.\n"
                "2. The same word may appear multiple times; continue typing "
                "and pressing 'Enter' until the word changes.\n\n"
                "Note: There is no backspace feature.\n\n"
                "When you are ready, press 'Start Trial' below to begin."
            )

        # Create and place the instructions label
        instructions_label = Label(root, text=instructions_text, wraplength=800, font=("Helvetica", 16), justify="left")
        instructions_label.pack(pady=50)

        # Create and place the start button
        def start_trial():
            root.destroy()  # Close the window when the button is clicked

        start_button = Button(root, text="Start Trial", font=("Helvetica", 14), command=start_trial, width=20, height=2)
        start_button.pack(pady=50)

        # Run the Tkinter main loop until the user clicks the button
        root.mainloop()
        print(f"Trial {trial} started for device {device.type}")
    except Exception as e:
        print(f"Error in instructions_and_start for trial {trial}: {e}")



def toggle_skip():
    global skip
    skip = True

def trial_run(consent_form, device, word_sets):
    global skip
    for trial in range(1, 2):
        i = 0
        try:
            word_set = word_sets[trial - 1]
            target_word = word_set[i]
        except IndexError as e:
            print(f"Error accessing word set for trial {trial}: {e}")
            continue

        instructions_and_start(device, trial)  # Show instructions and wait for user to start

        # Tkinter full screen window to display the target word
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            word_label = Label(root, text=target_word, font=("Helvetica", 100), anchor="center")
            word_label.pack(expand=True)

            # Create a skip button at the bottom of the window
            skip_button = Button(root, text="Skip", command=toggle_skip)
            skip_button.pack(side='bottom', pady=20)

            root.update()
        except Exception as e:
            print(f"Error creating Tkinter window for trial {trial}: {e}")
            continue

        device.start()
        running = 0

        while True:
            if i == 10:  # If 10 words have been completed, move to the next trial
                root.destroy()
                print(f"Trial {trial} completed.")
                break

            # Check conditions for skipping or timeout
            if device.get_result() != "" or running > 1000 or skip:
                device.input_time = device.get_time()

                if skip:
                    device.result = "SKIPPED"

                if compare(device, target_word, consent_form, trial) or running > 1000 or skip:
                    print(device.get_result())
                    i += 1
                    if not i == 10:
                        target_word = word_set[i]
                    else:
                        root.destroy()
                        break
                    word_label.config(text=target_word)
                    root.update()
                    skip = False  # Reset skip after handling
                running = 0

                device.start()
            else:
                time.sleep(0.02)
                running += 1

    print("All trials completed.")

    print("All trials completed.")

if True:
    print("Starting...")

    word_sets = get_word_sets()  # Load word sets
    if not word_sets:
        print("No word sets found. Exiting.")
        sys.exit()  # Replaces exit()

    # Initialize consent form (assuming this works without UI)
    consent_form = Consent()
    while not consent_form.isSigned():
        pass

    # Initialize devices and randomize the order
    devices = [ASL(), Keyboard()]  # Testing with just ASL right now
    random.shuffle(devices)

    # Run trials for each device
    trial_run(consent_form, devices[0], word_sets)
    trial_run(consent_form, devices[1], word_sets)
