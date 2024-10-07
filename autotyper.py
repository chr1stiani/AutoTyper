import tkinter as tk
from tkinter import ttk
import threading
import time
from pynput.keyboard import Key, Controller
import keyboard
import pyautogui
import cv2
import pytesseract
from PIL import Image
import os
import numpy as np

class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoTyper")
        self.is_typing = False
        self.typing_thread = None
        self.keyboard = Controller()

        # Konfigurace mřížky
        self.root.columnconfigure(1, weight=1)

        # Vstupní pole pro text
        self.text_label = ttk.Label(root, text="Text k zadání:")
        self.text_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.text_entry = ttk.Entry(root, width=50)
        self.text_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Vstupní pole pro rychlost
        self.speed_label = ttk.Label(root, text="Rychlost (znaků/s):")
        self.speed_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.speed_entry = ttk.Entry(root, width=10)
        self.speed_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.speed_entry.insert(0, "10")  # výchozí hodnota

        # Tlačítka Start a Stop
        self.start_button = ttk.Button(root, text="Start", command=self.start_typing)
        self.start_button.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_typing, state='disabled')
        self.stop_button.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # Přidáme klávesovou zkratku
        self.setup_hotkey()

        # Auto-seeing feature
        self.coords_label = ttk.Label(root, text="Coordinates (x1,y1,x2,y2):")
        self.coords_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.coords_entry = ttk.Entry(root, width=20)
        self.coords_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        self.capture_button = ttk.Button(root, text="Capture Text", command=self.capture_and_type)
        self.capture_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

    def setup_hotkey(self):
        keyboard.add_hotkey('ctrl+shift+s', self.toggle_typing)

    def toggle_typing(self):
        if self.is_typing:
            self.stop_typing()
        else:
            self.start_typing()

    def start_typing(self):
        if not self.is_typing:
            self.is_typing = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            text = self.text_entry.get()
            try:
                speed = float(self.speed_entry.get())
                delay = 1.0 / speed if speed > 0 else 0.1
            except ValueError:
                delay = 0.1  # výchozí zpoždění při neplatném vstupu
            self.typing_thread = threading.Thread(target=self.type_text, args=(text, delay))
            self.typing_thread.start()

    def type_text(self, text, delay):
        time.sleep(2)  # Krátké zpoždění pro přepnutí na cílové okno
        for char in text:
            if not self.is_typing:
                break
            self.type_char(char)
            time.sleep(delay)
        self.is_typing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def type_char(self, char):
        self.keyboard.press(char)
        self.keyboard.release(char)

    def stop_typing(self):
        self.is_typing = False

    def update_buttons(self):
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def capture_and_type(self):
        coords = self.coords_entry.get().split(',')
        if len(coords) != 4:
            print("Invalid coordinates. Please use format: x1,y1,x2,y2")
            return
        
        x1, y1, x2, y2 = map(int, coords)
        
        # Capture the screen
        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        
        # Convert the image to grayscale
        img_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        
        # Preprocessing
        img_gray = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Use pytesseract to do OCR on the image, specifying Czech language
        text = pytesseract.image_to_string(img_gray, lang='ces', config='--psm 6')
        
        # Set the recognized text to the text entry
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, text.strip())
        
        # Start typing the recognized text
        self.start_typing()

def main():
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print("Tesseract not found. Please install it or correct the path.")
        return

    root = tk.Tk()
    app = AutoTyperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()