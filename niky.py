import sys
import subprocess
import os
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox
import tempfile

# Konfiguračný súbor pre ukladanie nastavení
CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"language": "sk"}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Overenie knižnice gTTS
try:
    from gtts import gTTS
except ImportError:
    print("Knižnica gTTS nie je nainštalovaná. Inštalujem...")
    install("gTTS")
    from gtts import gTTS

# Overenie knižnice python-vlc
try:
    import vlc
except ImportError:
    print("Knižnica python-vlc nie je nainštalovaná. Inštalujem...")
    install("python-vlc")
    import vlc

# Globálne pre prehrávač a dočasný súbor
player = None
current_temp_file = None

# Slovníky s prekladmi UI
translations = {
    "sk": {
         "title": "Niky - Prevod textu na reč",
         "label_text": "Napíš text:",
         "language_label": "Jazyk:",
         "volume_label": "Hlasitosť:",
         "play_button": "Prehrať",
         "stop_button": "Stop",
         "warning_empty": "Prosím, zadaj text.",
         "error_title": "Chyba"
    },
    "en": {
         "title": "Niky - Text-to-Speech",
         "label_text": "Enter text:",
         "language_label": "Language:",
         "volume_label": "Volume:",
         "play_button": "Play",
         "stop_button": "Stop",
         "warning_empty": "Please enter text.",
         "error_title": "Error"
    }
}

# Nastavenie možností jazyka v comboboxe podľa aktuálneho UI jazyka
lang_display_mapping = {
    "sk": {"sk": "Slovenčina", "en": "Angličtina"},
    "en": {"sk": "Slovak", "en": "English"}
}

def speak_text():
    global player, current_temp_file
    stop_text()  # Zastav predchádzajúce prehrávanie

    text = text_input.get("1.0", tk.END).strip()
    if text:
        try:
            # Získaj aktuálny jazyk (kód) z konfiguračného súboru
            lang_code = config.get("language", "sk")
            tts = gTTS(text, lang=lang_code)

            # Vytvor dočasný súbor (delete=False, aby VLC mohol súbor prehrať)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                current_temp_file = fp.name

            tts.save(current_temp_file)
            player = vlc.MediaPlayer(current_temp_file)
            vol_value = volume_scale.get()
            player.audio_set_volume(int(vol_value))
            player.play()
        except Exception as e:
            messagebox.showerror(
                translations[config.get("language", "sk")]["error_title"],
                f"{e}"
            )
    else:
        messagebox.showwarning(
            translations[config.get("language", "sk")]["error_title"],
            translations[config.get("language", "sk")]["warning_empty"]
        )

def stop_text():
    global player, current_temp_file
    if player is not None:
        player.stop()
        player = None
    if current_temp_file and os.path.isfile(current_temp_file):
        os.remove(current_temp_file)
        current_temp_file = None

def update_volume(_=None):
    global player
    if player is not None:
        volume = volume_scale.get()
        player.audio_set_volume(int(volume))

def start_speak_thread():
    threading.Thread(target=speak_text, daemon=True).start()

def start_stop_thread():
    threading.Thread(target=stop_text, daemon=True).start()

def update_ui_language(lang_code):
    # Aktualizácia textov UI podľa vybraného jazyka
    root.title(translations[lang_code]["title"])
    label_text_widget.config(text=translations[lang_code]["label_text"])
    lang_label_widget.config(text=translations[lang_code]["language_label"])
    volume_label_widget.config(text=translations[lang_code]["volume_label"])
    speak_button.config(text=translations[lang_code]["play_button"])
    stop_button.config(text=translations[lang_code]["stop_button"])
    # Aktualizácia možností v comboboxe
    options = list(lang_display_mapping[lang_code].values())
    lang_combo.config(values=options)
    # Nastav combobox na natívny názov aktuálneho jazyka
    lang_var.set(lang_display_mapping[lang_code][lang_code])

def on_language_change(event):
    # Zisti vybraný jazyk podľa comboboxu
    selected_display = lang_var.get()
    current_ui_lang = config.get("language", "sk")
    new_lang = None
    for code, display in lang_display_mapping[current_ui_lang].items():
        if display == selected_display:
            new_lang = code
            break
    if new_lang is not None and new_lang != config.get("language"):
        config["language"] = new_lang
        save_config(config)
        update_ui_language(new_lang)

# Načítaj konfiguráciu (predvolený jazyk je "sk")
config = load_config()

# Vytvor hlavné okno
root = tk.Tk()
root.geometry("460x300")
try:
    style = ttk.Style()
    style.theme_use("clam")
except Exception:
    pass
root.configure(bg="#2e2e2e")

# Hlavný rám s paddingom
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Štítok pre zadanie textu
label_text_widget = ttk.Label(main_frame, text="", foreground="white")
label_text_widget.pack(pady=(0, 5))

# Textové pole
text_input = tk.Text(main_frame, height=5, width=40, bg="#3c3f41", fg="white", wrap=tk.WORD)
text_input.pack()

# Rám pre výber jazyka
lang_frame = ttk.Frame(main_frame)
lang_frame.pack(pady=10, fill=tk.X)
lang_label_widget = ttk.Label(lang_frame, text="", foreground="white")
lang_label_widget.pack(side=tk.LEFT, padx=5)
lang_var = tk.StringVar()
lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, state="readonly")
lang_combo.pack(side=tk.LEFT, padx=5)
lang_combo.bind("<<ComboboxSelected>>", on_language_change)

# Štítok a slider pre hlasitosť
volume_label_widget = ttk.Label(main_frame, text="", foreground="white")
volume_label_widget.pack(pady=(10, 0))
volume_scale = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=update_volume)
volume_scale.set(100)
volume_scale.pack(pady=5, fill=tk.X)

# Rám pre tlačidlá
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=10)
speak_button = ttk.Button(button_frame, text="", command=start_speak_thread)
speak_button.pack(side=tk.LEFT, padx=5)
stop_button = ttk.Button(button_frame, text="", command=start_stop_thread)
stop_button.pack(side=tk.LEFT, padx=5)

# Aktualizuj UI podľa načítaného jazyka
current_lang = config.get("language", "sk")
update_ui_language(current_lang)

root.mainloop()
