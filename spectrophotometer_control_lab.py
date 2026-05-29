import socket
import tkinter as tk
from tkinter import messagebox
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
import threading
import paramiko


PI_HOST = "Pi hostname" # or IP address; change as appropriate
PI_PORT = 22
PI_USER = "Pi username" # change as appropriate
PI_PASSWORD = "PI_USER's Password" # change as appropriate

REMOTE_WATCH_FOLDER = "/home/PI_USER/path_to_folder"  # change as appropriate
LOCAL_DOWNLOAD_FOLDER = r"C:\path_to_folder" # change as appropriate

os.makedirs(LOCAL_DOWNLOAD_FOLDER, exist_ok=True)

def process_csv(filepath):
    df = pd.read_csv(filepath)
    x = df["Index"]
    y = df["Absorbance"]
    plt.figure()
    plt.scatter(x, y)
    plt.xlabel("Index")
    plt.ylabel("Absorbance")
    plt.title(os.path.basename(filepath))
    plt.show()

def start_watcher():
    seen_files = set()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(PI_HOST, port=PI_PORT, username=PI_USER, password=PI_PASSWORD)
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"SSH connection failed: {e}")
        return
    print("Watching Pi outbox for new spectra...")
    while True:
        try:
            files = sftp.listdir(REMOTE_WATCH_FOLDER)
            for f in files:
                if not f.endswith(".csv"):
                    continue
                if f in seen_files:
                    continue
                remote_path = f"{REMOTE_WATCH_FOLDER}/{f}"
                local_path = os.path.join(LOCAL_DOWNLOAD_FOLDER, f)
                print(f"New spectrum detected: {f}")
                time.sleep(1)
                sftp.get(remote_path, local_path)
                try:
                    process_csv(local_path)
                except Exception as e:
                    print(f"Error processing file: {e}")
                seen_files.add(f)
        except Exception as e:
            print(f"Watcher error: {e}")
        time.sleep(2)

def blank():
    HOST = 'strawberry-pie'
    PORT = 5000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.sendall("blank".encode())
            s.recv(1024)
        except ConnectionRefusedError:
            messagebox.showerror("Connection Error", "Cannot connect to Pi.")

def sample():
    HOST = 'strawberry-pie'
    PORT = 5000
    name = entry.get()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.sendall(str(name).encode())
            s.recv(1024)
        except ConnectionRefusedError:
            messagebox.showerror("Connection Error", "Cannot connect to Pi.")

root = tk.Tk()
root.title("Spectrophotometer Control")
tk.Label(root, text="On startup you must run a blank before a sample").pack(padx=10, pady=5)
button = tk.Button(root, text="Blank", command=blank)
button.pack(padx=10, pady=10)
tk.Label(root, text="What is the name of the sample?").pack(padx=10, pady=5)
entry = tk.Entry(root)
entry.pack(padx=10, pady=5)
button = tk.Button(root, text="Sample", command=sample)
button.pack(padx=10, pady=10)

watcher_thread = threading.Thread(target=start_watcher, daemon=True)
watcher_thread.start()

root.mainloop()
