from ASL import ASL
from consent import Consent  
from keys import Keyboard# Placeholder for consent form
import time
import tkinter as tk
from tkinter import Label, Button
import os
import csv

def get_word_sets():
    word_sets = []
    for i in range(1, 4):
        file_path = f'./word_sets/{i}.txt'
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
    
    file_path = f"./subjects/{consent_form.getUserID()}/{device.type}/trial_{str(trial)}.csv"
    
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
        root.title(f"This is {device.type} trial {trial}/3:")

        # Define instruction text based on the device type
        if device.type == "ASL":
            instructions_text = "ASL instructions go here."
        else:
            instructions_text = "Keyboard instructions go here."

        # Create and place the instructions label
        instructions_label = Label(root, text=instructions_text, wraplength=800)
        instructions_label.pack(pady=50)

        # Create and place the start button
        def start_trial():
            root.destroy()  # Close the window when the button is clicked

        start_button = Button(root, text="Start Trial", command=start_trial)
        start_button.pack(pady=50)

        # Run the Tkinter main loop until the user clicks the button
        root.mainloop()
        print(f"Trial {trial} started for device {device.type}")
    except Exception as e:
        print(f"Error in instructions_and_start for trial {trial}: {e}")

def trial_run(consent_form, device, word_sets):
    for trial in range(1, 4):
        i = 0
        try:
            word_set = word_sets[trial - 1]  # Corrected to 0-based indexing
            target_word = word_set[i]
        except IndexError as e:
            print(f"Error accessing word set for trial {trial}: {e}")
            continue

        instructions_and_start(device, trial)  # Show instructions and wait for user to start

        # Try to load the model if the device has a load function
        try:
            device.load(trial)
        except AttributeError:
            print(f"Device {device.type} does not have a load function.")
        except Exception as e:
            print(f"Error loading model for trial {trial}: {e}")

        # Tkinter full screen window to display the target word
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            word_label = tk.Label(root, text=target_word, font=("Helvetica", 100), anchor="center")
            word_label.pack(expand=True)

            # Ensure the window gets updated properly after start
            root.update()

        except Exception as e:
            print(f"Error creating Tkinter window for trial {trial}: {e}")
            continue

        # Start the trial for the device
        device.start()
        running = 0

        while True:
            if i == 10:  # If 10 words have been completed, move to the next trial
                root.destroy()  # Close the window when trial completes
                print(f"Trial {trial} completed.")
                break

            # If the user has entered a word or has been stuck on the word for 60 seconds
            if device.get_result() != "" or running > 3000:
                running = 0
                device.input_time = device.get_time()

                # Check if the word is correct
                if compare(device, target_word, consent_form, trial):
                    print(device.get_result())
                    i += 1
                    if not i == 10:
                        target_word = word_set[i]
                    else:
                        root.destroy() 
                        break
                        # Update Tkinter to display the new target word
                    word_label.config(text=target_word)
                    root.update()  # Update the window

                    

                device.start()
            else:
                time.sleep(0.02)
                running += 1  # Wait 20ms before checking again

    print("All trials completed.")

if __name__ == "__main__":

    print("Starting...")

    try:

        word_sets = get_word_sets()  # Load word sets
        if not word_sets:
            print("No word sets found. Exiting.")
            exit()

        # Initialize consent form (as per your assumption, this works without UI)
        consent_form = Consent()
        while (not consent_form.isSigned()):
            pass

        # Initialize devices and randomize the order
        devices = [ASL(), Keyboard()]  # Testing with just ASL right now
        import random
        random.shuffle(devices)

        # Run trials for each device
        trial_run(consent_form, devices[0], word_sets)

    except Exception as e:
        print(f"An error occurred: {e}")
