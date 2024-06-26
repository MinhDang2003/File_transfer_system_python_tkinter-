import tkinter as tk
from tkinter import *
from ServerBackend.serverImplement import Server
from ServerBackend.serverLib import *
import socket
import threading
import sys
import json

host = socket.gethostname()
port = 65432
stop = False


class ServerInstance:
    def __init__(self):
        self.server = Server(host, port)
        self.stopSig = False
        self.current_thead = None

    def __del__(self):
        if self.current_thead is None:
            return
        self.stopSig = True
        self.current_thead.join()
        self.current_thead = None
        self.server.__del__()
        self.server = None

    def hosting(self, server, stopSig):
        server.deploy(stopSig)

    def startHost(self):
        self.stopSig = False
        threadHost = threading.Thread(target=self.hosting, args=(self.server, lambda: self.stopSig))
        threadHost.daemon = False
        self.current_thead = threadHost
        self.current_thead.start()
        return

    def stopHost(self):
        if self.current_thead is None:
            return
        self.stopSig = True
        self.current_thead.join()
        self.current_thead = None
        self.server.undeploy()
        # self.server.__del__()
        # self.server = None


serverIns = ServerInstance()


# Function to switch to Frame 1
def show_frame1():
    frame1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    label1.place(relx=0.5, rely=0.2, anchor=tk.CENTER)
    button_frame1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    frame2.place_forget()
    serverIns.stopHost()


# Function to switch to Frame 2
def show_frame2():
    frame2.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    label2.place(relx=0.5, rely=0.2, anchor=tk.CENTER)
    label3.place(relx=0.1, rely=0.4, anchor=tk.CENTER)
    entry1.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
    button_frame2.place(relx=0.5, rely=0.3, anchor=tk.CENTER)
    button_entry1.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
    outputBox.place(relx=0.5, rely=0.7, anchor=tk.CENTER)
    frame1.place_forget()
    serverIns.startHost()


def checkInput(input):
    lst = input.split(" ", 1)
    print(lst)
    if (len(lst) < 2):
        return "invalid syntax"
    if (lst[0] == "discover"):
        client_name = lst[1]
        if records.count_documents({
            "client_name": client_name
        }) == 0:
            return f"{client_name} does not exist"
        data = []
        file_list = records.find({"client_name": client_name},
                                 {'_id': 0, "IP": 1, "client_name": 1, "port": 1, "file_info": 1})
        for file in file_list:
            data.append(file)
        return data
    if (lst[0] == "ping"):
        if (lst[1] in onlineList):
            return f"{lst[1]} is online"
        return f"{lst[1]} is not online"
    return "invalid syntax"


# Create the main window
root = tk.Tk()
root.title("Frame Navigation Example")
root.minsize(width=600, height=500)
data = tk.StringVar()


def getInput():
    outputBox.configure(state="normal")
    outputBox.delete(0.0, END)
    input = (data.get())
    data1 = checkInput(input)
    if type(data1) == str:
        outputBox.insert(0.0, data1)
    else:
        outputBox.insert(0.0, json.dumps(data1, indent=2))
    outputBox.configure(state="disabled")


# Create Frame 1
frame1 = tk.Frame(root, width=600, height=600, bg="lightblue")
frame1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# Add widgets to Frame 1
label1 = tk.Label(frame1, text="Welcome to Server Deploying", bg="lightblue")
label1.config(font=("Ariel", 30))
label1.place(relx=0.5, rely=0.2, anchor=tk.CENTER)

button_frame1 = tk.Button(frame1, text="Deploy Server", command=show_frame2, width=20, height=5)
button_frame1.config(font=("Ariel", 15))
button_frame1.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# Create Frame 2
frame2 = tk.Frame(root, width=600, height=600)

# Add widgets to Frame 2
label2 = tk.Label(frame2, text="Server Deploying...")
label2.config(font=("Ariel", 15))

button_frame2 = tk.Button(frame2, text="Undeploy Server", command=show_frame1, width=20, height=3)

label3 = tk.Label(frame2, text="Input Command:")
label3.config(font=("Ariel", 10))

entry1 = tk.Entry(frame2, width=60, textvariable=data)

button_entry1 = tk.Button(frame2, text="Submit", width=10, height=2, command=getInput)

outputBox = tk.Text(frame2, width=60, height=15, wrap=WORD)
outputBox.configure(state="disabled")
# Set up initial visibility
show_frame1()

# Run the Tkinter event loop
root.mainloop()
