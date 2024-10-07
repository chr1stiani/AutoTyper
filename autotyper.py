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
import mouse
from PIL import ImageGrab, ImageTk

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

        # Přidáme klávesové zkratky
        keyboard.add_hotkey('ctrl+shift+f1', self.capture_and_type)
        keyboard.add_hotkey('ctrl+shift+f2', self.start_typing)
        keyboard.add_hotkey('ctrl+shift+f3', self.toggle_auto)

        # Auto-seeing feature
        self.coords_label = ttk.Label(root, text="Coordinates (x1,y1,x2,y2):")
        self.coords_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.coords_entry = ttk.Entry(root, width=20)
        self.coords_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        self.capture_button = ttk.Button(root, text="Capture Text", command=self.capture_and_type)
        self.capture_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

        # Auto feature
        self.auto_frame = ttk.Frame(root)
        self.auto_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        self.auto_label = ttk.Label(self.auto_frame, text="Auto:")
        self.auto_label.pack(side='left')
        
        self.auto_state = tk.StringVar(value="Off")
        self.auto_button = ttk.Button(self.auto_frame, textvariable=self.auto_state, command=self.toggle_auto)
        self.auto_button.pack(side='left', padx=5)

        self.auto_active = False
        self.auto_thread = None

        # Přidání stavového řádku
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=7, column=0, columnspan=2, sticky='ew')

        # Proměnné pro odpočet
        self.countdown_active = False
        self.countdown_thread = None

        # Přidáme proměnnou pro sledování počtu napsaných znaků
        self.chars_typed = 0

        # Přidání tlačítka pro výběr oblasti
        self.select_area_button = ttk.Button(root, text="Vybrat oblast", command=self.start_area_selection)
        self.select_area_button.grid(row=3, column=2, padx=5, pady=5, sticky='ew')

        # Proměnné pro výběr oblasti
        self.selecting_area = False
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.selection_window = None

        # Přidání popisků klávesových zkratek do GUI
        ttk.Label(root, text="Klávesové zkratky:").grid(row=8, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        ttk.Label(root, text="Ctrl+Shift+F1: Zachytit a psát").grid(row=9, column=0, columnspan=2, sticky='w', padx=5)
        ttk.Label(root, text="Ctrl+Shift+F2: Začít psát").grid(row=10, column=0, columnspan=2, sticky='w', padx=5)
        ttk.Label(root, text="Ctrl+Shift+F3: Zapnout/Vypnout auto režim").grid(row=11, column=0, columnspan=2, sticky='w', padx=5)

        # Nezapomeňte přidat tuto metodu do __init__
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
            
            # Spuštění odpočtu před psaním
            self.start_countdown(2, "Psaní začne za")

    def type_text(self, text, delay):
        time.sleep(2)  # Čekání před začátkem psaní
        self.chars_typed = 0
        total_chars = len(text)
        for char in text:
            if not self.is_typing:
                break
            self.type_char(char)
            self.chars_typed += 1
            self.update_typing_status(total_chars)
            time.sleep(delay)
        self.is_typing = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_var.set("Psaní dokončeno")

    def update_typing_status(self, total_chars):
        progress = (self.chars_typed / total_chars) * 100
        self.status_var.set(f"Psaní: {self.chars_typed}/{total_chars} znaků ({progress:.1f}%)")

    def type_char(self, char):
        self.keyboard.press(char)
        self.keyboard.release(char)

    def stop_typing(self):
        self.is_typing = False
        self.countdown_active = False
        if not self.auto_active:
            self.update_buttons()
        self.status_var.set(f"Psaní zastaveno ({self.chars_typed} znaků napsáno)")

    def update_buttons(self):
        if self.is_typing:
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
        else:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
        
        self.auto_button.config(state='normal')
        self.capture_button.config(state='normal' if not self.auto_active else 'disabled')

    def toggle_auto(self):
        if self.auto_active:
            self.stop_auto()
        else:
            self.start_auto()
        self.update_buttons()  # Update button states after toggling

    def start_auto(self):
        self.auto_active = True
        self.auto_state.set("On")
        self.auto_thread = threading.Thread(target=self.auto_loop)
        self.auto_thread.start()
        self.status_var.set("Automatický režim aktivován")

    def stop_auto(self):
        self.auto_active = False
        self.countdown_active = False
        self.auto_state.set("Off")
        self.status_var.set("Automatický režim deaktivován")

    def auto_loop(self):
        while self.auto_active:
            self.capture_and_type()
            while self.is_typing and self.auto_active:
                time.sleep(0.1)
            if not self.auto_active:
                break
            self.start_countdown(1, "Další zachycení za")

    def start_countdown(self, duration, prefix_text):
        if self.countdown_active:
            return
        self.countdown_active = True
        self.countdown_thread = threading.Thread(target=self.countdown, args=(duration, prefix_text))
        self.countdown_thread.start()

    def countdown(self, duration, prefix_text):
        for i in range(duration, 0, -1):
            if not self.countdown_active:
                break
            self.status_var.set(f"{prefix_text} {i:.1f}s")
            time.sleep(0.1)
        self.countdown_active = False

    def capture_and_type(self):
        coords = self.coords_entry.get().split(',')
        if len(coords) != 4:
            print("Neplatné souřadnice. Použijte formát: x1,y1,x2,y2")
            return
        
        x1, y1, x2, y2 = map(int, coords)
        
        # Zachycení obrazovky
        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        
        # Převod obrázku na odstíny šedi
        img_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        
        # Předzpracování obrázku
        img_gray = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Použití pytesseract pro OCR, specifikace českého a anglického jazyka
        text_ces = pytesseract.image_to_string(img_gray, lang='ces', config='--psm 6')
        text_eng = pytesseract.image_to_string(img_gray, lang='eng', config='--psm 6')
        
        # Kombinace výsledků
        text = self.combine_ocr_results(text_ces, text_eng)
        
        # Nastavení rozpoznaného textu do vstupního pole
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, text.strip())
        
        # Spuštění psaní rozpoznaného textu
        self.start_typing()

    def combine_ocr_results(self, text_ces, text_eng):
        # Jednoduchá kombinace výsledků - můžete upravit podle potřeby
        if len(text_eng.strip()) > len(text_ces.strip()):
            return text_eng
        else:
            return text_ces

    def start_area_selection(self):
        self.selecting_area = True
        self.root.iconify()
        self.status_var.set("Klikněte levým tlačítkem pro výběr rohů oblasti. Potvrďte tlačítkem 'Potvrdit výběr'.")
        
        self.selection_window = tk.Toplevel()
        self.selection_window.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        self.selection_window.configure(bg='gray')
        
        self.selection_canvas = tk.Canvas(self.selection_window, highlightthickness=0)
        self.selection_canvas.pack(fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.selection_window)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.confirm_button = tk.Button(self.button_frame, text="Potvrdit výběr", command=self.finish_area_selection)
        self.confirm_button.pack(side=tk.BOTTOM, pady=10)

        self.selection_canvas.bind('<Button-1>', self.on_click)
        self.selection_canvas.bind('<Motion>', self.on_mouse_move)
        self.selection_window.bind('<Escape>', self.cancel_area_selection)

    def on_click(self, event):
        x, y = event.x_root, event.y_root  # Použijeme globální souřadnice události
        if self.start_x is None:
            self.start_x, self.start_y = x, y
            self.status_var.set("První roh vybrán. Klikněte pro výběr druhého rohu.")
        elif self.end_x is None:
            self.end_x, self.end_y = x, y
            self.status_var.set("Oblast vybrána. Potvrďte tlačítkem 'Potvrdit výběr' nebo vyberte znovu.")
        else:
            self.start_x, self.start_y = x, y
            self.end_x = self.end_y = None
            self.status_var.set("Nový první roh vybrán. Klikněte pro výběr druhého rohu.")
        self.update_selection_rectangle()

    def on_mouse_move(self, event):
        if self.start_x is not None:
            self.update_selection_rectangle(event.x_root, event.y_root)

    def update_selection_rectangle(self, current_x=None, current_y=None):
        self.selection_canvas.delete("selection")
        if self.start_x is not None:
            end_x = self.end_x if self.end_x is not None else current_x
            end_y = self.end_y if self.end_y is not None else current_y
            if end_x and end_y:
                # Převedeme globální souřadnice na souřadnice plátna
                canvas_start_x = self.start_x - self.selection_window.winfo_rootx()
                canvas_start_y = self.start_y - self.selection_window.winfo_rooty()
                canvas_end_x = end_x - self.selection_window.winfo_rootx()
                canvas_end_y = end_y - self.selection_window.winfo_rooty()
                
                self.selection_canvas.create_rectangle(
                    canvas_start_x, canvas_start_y, canvas_end_x, canvas_end_y,
                    outline="red", width=2, tags="selection"
                )

    def finish_area_selection(self):
        if self.start_x is not None and self.end_x is not None:
            self.selecting_area = False
            self.update_coords()
            self.selection_window.destroy()
            self.root.deiconify()
            self.status_var.set(f"Oblast vybrána: {self.start_x},{self.start_y},{self.end_x},{self.end_y}")
        else:
            self.status_var.set("Prosím vyberte oba rohy oblasti před potvrzením.")

    def cancel_area_selection(self, event=None):
        if self.selecting_area:
            self.selecting_area = False
            if self.selection_window:
                self.selection_window.destroy()
            self.root.deiconify()
            self.status_var.set("Výběr oblasti zrušen")

    def update_coords(self):
        left = min(self.start_x, self.end_x)
        top = min(self.start_y, self.end_y)
        right = max(self.start_x, self.end_x)
        bottom = max(self.start_y, self.end_y)
        
        coords = f"{left},{top},{right},{bottom}"
        self.coords_entry.delete(0, tk.END)
        self.coords_entry.insert(0, coords)

    def on_closing(self):
        # Odstranění klávesových zkratek před zavřením aplikace
        keyboard.remove_hotkey('ctrl+shift+f1')
        keyboard.remove_hotkey('ctrl+shift+f2')
        keyboard.remove_hotkey('ctrl+shift+f3')
        self.root.destroy()

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

#748, 543, 1789, 638
