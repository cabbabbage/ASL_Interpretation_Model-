import keyboard
import time

class Keyboard:
    def __init__(self):
        self.result = ""  # Store the single result
        self.type = "key"
        self.input_time = 0
        self.start_time = 0

    def get_time(self):
        return time.time() - self.start_time

    def get_result(self):
        return self.result

    def start(self):
        """Start listening for keyboard input without showing any UI."""
        self.result = ""
        self.start_time = time.time()

        print("Start typing. Press Enter to submit.")

        input_string = ""
        while True:
            event = keyboard.read_event()  # Capture keyboard events
            if event.event_type == keyboard.KEY_DOWN:  # Only register key down events
                if event.name == 'enter':
                    break  # Stop listening when Enter is pressed
                elif event.name == 'space':
                    input_string += ' '  # Add a space for the spacebar
                else:
                    input_string += event.name  # Add the key to the input string

        self.result = input_string
        self.input_time = self.get_time()
        print(f"Input captured: {self.result}")
        print(f"Time taken: {self.input_time} seconds")
