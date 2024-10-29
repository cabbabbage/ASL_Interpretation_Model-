from tkinter import *
from tkinter import ttk
import numpy as np
import pandas as pd

class Consent():
    #dunderscore is used in python to denote private variables
    __UserID : str
    __form : any
    __filename : str
    __signed = False

    def __init__(self, filename = "form.csv"):
        try:
            self.__root = Tk()
            self.__filename = filename

            self.__openForm()

            self.__root.title("Consent Form")

            self.__mainframe = ttk.Frame(self.__root, padding="3 3 24 24")
            self.__mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
            self.__root.columnconfigure(0, weight=1)
            self.__root.rowconfigure(0, weight=1)
            self.__root.geometry("400x300")

            self.__name = StringVar()
            self.__name_entry = ttk.Entry(self.__mainframe, width=10, textvariable=self.__name)
            self.__name_entry.grid(column=2, row=1, sticky=(W, E))

            self.__age = IntVar()
            self.__age_entry = ttk.Entry(self.__mainframe, width=2, textvariable=self.__age)
            self.__age_entry.grid(column=2, row=2, sticky=(W, E))


            ttk.Label(self.__mainframe, text="Name:").grid(column=1, row=1, sticky=W)
            ttk.Label(self.__mainframe, text="Age:").grid(column=1, row=2, sticky=W)

            ttk.Button(self.__mainframe, text="Submit", command=self.__makeForm).grid(column=3, row=3, sticky=W)

            for child in self.__mainframe.winfo_children(): 
                child.grid_configure(padx=30, pady=30)

            self.__name_entry.focus()
            self.__age_entry.focus()
            self.__root.bind("<Return>", self.__makeForm)

            self.__root.mainloop()
        except Exception as e:
            print(f"An error occurred during Tkinter window creation for Consent Form: {e}")

    def __openForm(self):
        try:
            self.__form = pd.read_csv(self.__filename, delimiter=',', index_col=0)
        except Exception as e:
            print(f"An error occurred reading from {self.__filename}: {e}")

    def __makeForm(self, *args):
        self.__UserID = "P" + str(len(self.__form))
        info = pd.DataFrame([[self.__UserID, self.__age.get()]])
        self.__savetoForm(info)
        self.__signed = True
        self.__root.destroy()

    def __savetoForm(self, info):
        try:
            print(info)
            info.to_csv(self.__filename, index=False, mode='a', header=False)
        except Exception as e:
            print(f"An error occurred writing to {self.__filename}: {e}")

    def getName(self):
        return self.__name.get()
    
    def getAge(self):
        return self.__age.get()
    
    def getUserID(self):
        return self.__UserID
    
    def isSigned(self):
        return self.__signed
   


if __name__ == "__main__":
    consent = Consent()
