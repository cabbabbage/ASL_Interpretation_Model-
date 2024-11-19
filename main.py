from Devices.ASL_dev.ASL import ASL
from Utils.consent import Consent
from Devices.keys import Keyboard
import time
import tkinter as tk
from tkinter import Label
import os
import csv
import random
import sys


def get_word_sets(setup=False):
    word_sets = []
    if setup:
        file_path = './Experiment_Word_Sets/all.txt'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    words = file.read().splitlines()
                    word_sets.append(words)
                print(f"Loaded word set from {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return word_sets

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


def compare(device, target, consent_form, trial, input_time):
    result = device.result
    correct = int(result == target)
    if not result and input_time < 10:
        return correct
    file_path = f"./Experiment Results/{consent_form.get_user_id()}/{device.type}/trial_{str(trial)}.csv"
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_exists = os.path.isfile(file_path)

        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Correct', 'Target', 'Result', 'Input Time (s)'])
            writer.writerow([correct, target, result, input_time])
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
    device.result = ""
    return correct


def instructions_and_start(device, trial):
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.title(f"Trial {trial} - {device.type} Device")

        instructions_text = (
            "Instructions:\n\n"
            "1. Please sign or type each word shown on the screen.\n"
            "2. The same word may appear multiple times; continue until the word changes.\n\n"
            "When you are ready, press 'Start Trial' below to begin."
        )

        instructions_label = Label(root, text=instructions_text, wraplength=800, font=("Helvetica", 16), justify="left")
        instructions_label.pack(pady=50)

        def start_trial():
            root.destroy()

        start_button = tk.Button(root, text="Start Trial", font=("Helvetica", 14), command=start_trial, width=20, height=2)
        start_button.pack(pady=50)

        root.mainloop()
        print(f"Trial {trial} started for device {device.type}")
    except Exception as e:
        print(f"Error in instructions_and_start for trial {trial}: {e}")


def trial_run(consent_form, device, word_sets):
    for trial in range(1, 4):
        i = 0
        try:
            word_set = word_sets[trial - 1]
            target_word = word_set[i]
        except IndexError as e:
            print(f"Error accessing word set for trial {trial}: {e}")
            continue

        instructions_and_start(device, trial)

        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            word_label = Label(root, text=target_word, font=("Helvetica", 100), anchor="center")
            word_label.pack(expand=True)

            root.update()
        except Exception as e:
            print(f"Error creating Tkinter window for trial {trial}: {e}")
            continue

        device.start()
        start_time = time.time()

        while True:
            if i == 10:  # If 10 words have been completed, move to the next trial
                root.destroy()
                print(f"Trial {trial} completed.")
                break

            current_time = time.time()
            elapsed_time = current_time - start_time


            if elapsed_time >= 10 or compare(device, target_word, consent_form, trial, elapsed_time):
                compare(device, target_word, consent_form, trial, elapsed_time)

                i += 1
                if i < len(word_set):
                    target_word = word_set[i]
                    word_label.config(text=target_word)
                    root.update()
                else:
                    root.destroy()
                    break

                device.start()
                start_time = time.time()
            else:
                time.sleep(0.02)

    print("All trials completed.")


if __name__ == "__main__":
    print("Starting...")

    word_sets = get_word_sets(False)
    if not word_sets:
        print("No word sets found. Exiting.")
        sys.exit()

    consent_form = Consent()
    devices = [ASL(True), Keyboard()]  # ASL then keyboard

    trial_run(consent_form, devices[0], word_sets)
    trial_run(consent_form, devices[1], word_sets)
