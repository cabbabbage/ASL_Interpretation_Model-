from tkinter import *
from tkinter import ttk

class Consent():
    #dunderscore is used in python to denote private variables
    __Username : str
    __age : int
    __UserID : str
    IDNum = -1 #Static variable for ID; will need to change later if not done consecutively

    def __init__(self, Username : str, age : int):
        Consent.IDNum += 1
        self.__UserID = "P" + str(Consent.IDNum)
        self.__Username = Username
        self.__age = age

    def getName(self):
        return self.__Username
    
    def getAge(self):
        return self.__age
    
    def getUserID(self):
        return self.__UserID
    
def makeForm(*args):
    try:
        form = Consent(name.get(), age.get())
        print("Name: " + form.getName())
        print("Age: " + str(form.getAge()))
        print("UID: " + form.getUserID())
        return form
    except ValueError:
        pass


if __name__ == "__main__":
    root = Tk()
    root.title("Consent Form")

    mainframe = ttk.Frame(root, padding="3 3 24 24")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.geometry("400x300")

    name = StringVar()
    name_entry = ttk.Entry(mainframe, width=10, textvariable=name)
    name_entry.grid(column=2, row=1, sticky=(W, E))

    age = IntVar()
    age_entry = ttk.Entry(mainframe, width=2, textvariable=age)
    age_entry.grid(column=2, row=2, sticky=(W, E))

    ttk.Label(mainframe, text="Name:").grid(column=1, row=1, sticky=W)
    ttk.Label(mainframe, text="Age:").grid(column=1, row=2, sticky=W)

    ttk.Button(mainframe, text="Submit", command=makeForm).grid(column=3, row=3, sticky=W)

    for child in mainframe.winfo_children(): 
        child.grid_configure(padx=30, pady=30)

    name_entry.focus()
    age_entry.focus()
    root.bind("<Return>", makeForm)

    root.mainloop()