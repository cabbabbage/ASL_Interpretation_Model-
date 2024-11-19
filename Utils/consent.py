from tkinter import *
from tkinter import ttk

class Consent:
    def __init__(self):
        # Initialize the Tkinter window
        self.__root = Tk()
        self.__root.title("Consent Form")

        # Configure the main frame
        self.__mainframe = ttk.Frame(self.__root, padding="10 10 20 20")
        self.__mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.__root.columnconfigure(0, weight=1)
        self.__root.rowconfigure(0, weight=1)
        self.__root.geometry("300x150")

        # Initialize UserID and the input variable
        self.__UserID = None
        self.__participant_number = StringVar()

        # Create UI elements
        ttk.Label(self.__mainframe, text="Participant number:").grid(column=1, row=1, sticky=W)
        self.__participant_entry = ttk.Entry(self.__mainframe, width=15, textvariable=self.__participant_number)
        self.__participant_entry.grid(column=2, row=1, sticky=(W, E))

        ttk.Button(self.__mainframe, text="Submit", command=self.__set_user_id).grid(column=2, row=2, sticky=E)

        # Add padding to all children in the main frame
        for child in self.__mainframe.winfo_children():
            child.grid_configure(padx=10, pady=10)

        # Focus on the entry field and bind Enter key to submission
        self.__participant_entry.focus()
        self.__root.bind("<Return>", self.__set_user_id)

        # Start the Tkinter main loop
        self.__root.mainloop()

    def __set_user_id(self, *args):
        """Set the UserID based on the participant number input."""
        participant_number = self.__participant_number.get().strip()
        if participant_number.isdigit():  # Ensure input is a valid number
            self.__UserID = "P" + participant_number
            self.__root.destroy()  # Close the window
        else:
            # Show a warning if input is not a number
            self.__participant_entry.delete(0, END)
            self.__participant_entry.insert(0, "Invalid input")

    def get_user_id(self):
        """Return the UserID."""
        return self.__UserID


if __name__ == "__main__":
    consent = Consent()
    print("UserID:", consent.get_user_id())
