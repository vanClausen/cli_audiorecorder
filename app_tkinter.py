from cli_audiorecorder import AudioRecorder
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import subprocess

def start_recording():
    url = entry_url.get().strip()
    if url == "":
        messagebox.showerror("Error", "Please enter a valid URL")
        return

    filename = entry_filename.get().strip()
    if filename == "":
        messagebox.showerror("Error", "Please enter a valid filename")
        return

    try:
        duration = int(entry_duration.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid duration in seconds")
        return

    try:
        blocksize = int(entry_blocksize.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid blocksize in kb")
        return

    lbl_status.config(text = "Recording...", fg="red")
    btn_record.config(state = 'disabled')
    threading.Thread(target=run_record_task, args=(url, filename, duration, blocksize), daemon=True).start()

def update_ui_status(message):
    def set_status(text, color):
        lbl_status.config(text=text, fg=color)

    if message == "start":
        root.after(0, set_status,"Connect to stream...", "green")
    elif message == "writing":
        root.after(0, set_status, "Recording...", "red")
    elif message == "success":
        root.after(0, set_status, "Recording finished!", "green")
    elif message == "fail":
        root.after(0, set_status, "Error while recording!", "red")

def run_record_task(url, filename, duration, blocksize):
    recorder = AudioRecorder(url, filename, duration, blocksize, None, status_callback=update_ui_status)
    recorder.record()

    def enable_button(state):
        btn_record.config(state=state)

    root.after(0, enable_button, 'normal')

def list_recorded_streams():
    current_path = os.getcwd()

    if sys.platform == "win32":
        # Windows
        os.startfile(current_path)
    elif sys.platform == "darwin":
        # macOS
        subprocess.Popen(["open", current_path])
    else:
        # Linux / other (posix)
        subprocess.Popen(["xdg-open", current_path])

# GUI
root = tk.Tk()
root.title("Radio Stream Recorder")
root.geometry("400x325")
root.padx = 20
root.pady = 20

# URL
tk.Label(root, text="Stream URL:").pack()
entry_url = tk.Entry(root, width=50)
entry_url.pack(pady=5)

# Filename
tk.Label(root, text="Filename:").pack()
entry_filename = tk.Entry(root, width=50)
entry_filename.insert(0, "myRadio")
entry_filename.pack(pady=5)

# Duration
tk.Label(root, text="Duration (seconds):").pack()
entry_duration = tk.Entry(root, width=50)
entry_duration.insert(0, "10")
entry_duration.pack(pady=5)

# Blocksize
tk.Label(root, text="Blocksize (kb):").pack()
entry_blocksize = tk.Entry(root, width=50)
entry_blocksize.insert(0, "1024")
entry_blocksize.pack(pady=5)

# Record Button
btn_record = tk.Button(root, text="🔴 Start recording", command=start_recording)
btn_record.pack(pady=10)

# Status Label
lbl_status = tk.Label(root, text="Ready")
lbl_status.pack()

btn_listfiles = tk.Button(root, text="Open saved stream directory", command=list_recorded_streams)
btn_listfiles.pack(pady=10)

root.mainloop()