import tkinter as tk
from gui import MidiEditorApp
import sys
import os

def main():
    root = tk.Tk()

    # Optional: Icon setup if available
    # root.iconbitmap('icon.ico')

    app = MidiEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
