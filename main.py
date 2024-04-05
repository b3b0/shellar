import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import hashlib
import os
import paramiko
import threading
import logging
import re
import uuid
import webbrowser


class NewConnectionDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Host:").grid(row=0)
        tk.Label(master, text="Username:").grid(row=1)
        tk.Label(master, text="Password:").grid(row=2)

        self.host_entry = tk.Entry(master)
        self.username_entry = tk.Entry(master)
        self.password_entry = tk.Entry(master, show='*')

        self.host_entry.grid(row=0, column=1)
        self.username_entry.grid(row=1, column=1)
        self.password_entry.grid(row=2, column=1)

        return self.host_entry

    def apply(self):
        self.result = {
            'host': self.host_entry.get(),
            'username': self.username_entry.get(),
            'password': self.password_entry.get()
        }

global master_password
master_password = None
APP_VERSION = "0.1.1"
APP_NAME = "shellCellar"
APP_DATA_PATH = os.path.expanduser(f"~/.{APP_NAME}")

if not os.path.exists(APP_DATA_PATH):
    os.makedirs(APP_DATA_PATH)

CONFIG_FILE = os.path.join(APP_DATA_PATH, 'app_config.json')
CONNECTIONS_FILE = os.path.join(APP_DATA_PATH, 'connections.json')

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def strip_ansi(text):
    return ansi_escape.sub('', text)

logging.basicConfig(level=logging.DEBUG)

def get_master_password():
    hashed_master_password = config.get('hashed_master_password')
    logging.debug(f"Hashed Master Password: {hashed_master_password}")
    return hashed_master_password

def connect():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]

    host = selected_connection['host']
    username = selected_connection['username']
    password = decrypt_password(selected_connection['password'], get_master_password())

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, username=username, password=password)
        new_tab = ttk.Frame(tabs)
        tabs.add(new_tab, text=host)
        tabs.select(new_tab)

        ssh_output = tk.Text(new_tab, wrap=tk.NONE, state=tk.NORMAL)
        ssh_output.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        command_entry = tk.Entry(new_tab)
        command_entry.pack(fill=tk.X, side=tk.BOTTOM)
        command_entry.focus_set()

        session_active = [True]

        channel = ssh_client.invoke_shell()

        def update_output():
            while session_active[0]:
                if channel.recv_ready():
                    data = channel.recv(1024).decode()
                    data = strip_ansi(data)
                    if "exit" in data:
                        session_active[0] = False
                        root.after(100, lambda: tabs.forget(new_tab))
                    ssh_output.config(state=tk.NORMAL)
                    ssh_output.insert(tk.END, data)
                    ssh_output.see(tk.END)
                    ssh_output.config(state=tk.DISABLED)

        update_thread = threading.Thread(target=update_output)
        update_thread.daemon = True
        update_thread.start()

        command_history = []
        history_index = -1

        def send_command(event):
            global history_index
            if event.keysym == "Return":
                command = command_entry.get()
                channel.send("\r")
                channel.send(command + "\n")
                command_entry.delete(0, tk.END)
                if command.strip():
                    command_history.append(command)
                    history_index = len(command_history)
            elif event.keysym == "Tab":
                command = command_entry.get()
                channel.send(command + "\t\t")
                command_entry.delete(0, tk.END)
                command_entry.focus_set()
                return "break"
            elif event.keysym == "Up":
                if history_index > 0:
                    history_index -= 1
                    command_entry.delete(0, tk.END)
                    command_entry.insert(0, command_history[history_index])
                return "break"
            elif event.keysym == "Down":
                if history_index < len(command_history) - 1:
                    history_index += 1
                    command_entry.delete(0, tk.END)
                    command_entry.insert(0, command_history[history_index])
                elif history_index == len(command_history) - 1:
                    history_index += 1
                    command_entry.delete(0, tk.END)
                return "break"

        command_entry.bind("<Tab>", send_command)
        command_entry.bind("<Return>", send_command)
        command_entry.bind("<Up>", send_command)
        command_entry.bind("<Down>", send_command)



    except paramiko.AuthenticationException:
        messagebox.showerror("Authentication Error", "Authentication failed. Please check your username and password.")
    except Exception as e:
        messagebox.showerror("SSH Connection Error", str(e))



def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        return {'master_password_set': False}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def load_connections():
    if os.path.exists(CONNECTIONS_FILE):
        with open(CONNECTIONS_FILE, 'r') as file:
            return json.load(file)
    else:
        return []

def save_connections(connections):
    with open(CONNECTIONS_FILE, 'w') as file:
        json.dump(connections, file)

def encrypt_password(password, key):
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(password, key * (len(password) // len(key) + 1)))

def decrypt_password(encrypted_password, key):
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(encrypted_password, key * (len(encrypted_password) // len(key) + 1)))

def add_first_connection(master_password):
    print("ADDING FIRST")
    master_password = config['hashed_master_password']
    if not master_password:
        set_master_password()

    dialog = NewConnectionDialog(root, title="New Connection")
    if dialog.result:
        host = dialog.result['host']
        username = dialog.result['username']
        password = dialog.result['password']
        encrypted_password = encrypt_password(password, master_password)
        connections.append({'host': host, 'username': username, 'password': encrypted_password})
        save_connections(connections)


def set_master_password():
    print("SETTING MASTER")
    master_password = simpledialog.askstring("Master Password", "Set a master password:", show='*')
    if master_password:
        hashed_master_password = hashlib.sha256(master_password.encode()).hexdigest()
        config['master_password_set'] = True
        config['hashed_master_password'] = hashed_master_password
        save_config(config)
    else:
        raise Exception("Master password is required")

def verify_master_password():
    input_password = simpledialog.askstring("Master Password", "Enter master password:", show='*')
    if input_password:
        input_hashed = hashlib.sha256(input_password.encode()).hexdigest()
        return input_hashed == config['hashed_master_password']
    else:
        return False

config = load_config()
connections = load_connections()

root = tk.Tk()
root.title(f"{APP_NAME} - {APP_VERSION}")
root.geometry("1200x600")

selected_connection_index = tk.IntVar(value=0)

if not config['master_password_set']:
    print("MASTER NOT SET")
    set_master_password()
    master_password = config['hashed_master_password']
    add_first_connection(master_password)
else:
    input_password = simpledialog.askstring("Master Password", "Enter master password:", show='*')
    if input_password:
        input_hashed = hashlib.sha256(input_password.encode()).hexdigest()
        if input_hashed == config['hashed_master_password']:
            master_password = input_password
        else:
            messagebox.showerror("Error", "Incorrect master password")
            exit()
    else:
        messagebox.showerror("Error", "Master password is required")
        exit()


paned_window = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

left_frame = ttk.Frame(paned_window, width=100)
paned_window.add(left_frame, weight=1)

connections_label = ttk.Label(left_frame, text="Connections")
connections_label.pack(anchor=tk.NW)
connections_frame = ttk.Frame(left_frame)
connections_frame.pack(fill=tk.BOTH, expand=True)
canvas = tk.Canvas(connections_frame)
scrollbar = ttk.Scrollbar(connections_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
radiobuttons_frame = ttk.Frame(canvas)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
canvas.create_window((0, 0), window=radiobuttons_frame, anchor="nw")
radiobuttons_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

editor_frame = ttk.Frame(left_frame)
editor_frame.pack(fill=tk.BOTH, expand=True)
connect_button = ttk.Button(editor_frame, text="Connect", command=connect)
connect_button.grid(row=3, column=0, sticky=tk.W)
host_label = ttk.Label(editor_frame, text="Host:")
host_label.grid(row=0, column=0, sticky=tk.W)
host_entry = ttk.Entry(editor_frame)
host_entry.grid(row=0, column=1, sticky=tk.EW)

username_label = ttk.Label(editor_frame, text="Username:")
username_label.grid(row=1, column=0, sticky=tk.W)
username_entry = ttk.Entry(editor_frame)
username_entry.grid(row=1, column=1, sticky=tk.EW)

password_label = ttk.Label(editor_frame, text="Password:")
password_label.grid(row=2, column=0, sticky=tk.W)
password_entry = ttk.Entry(editor_frame, show="*")
password_entry.grid(row=2, column=1, sticky=tk.EW)

connect_button = ttk.Button(editor_frame, text="Connect", command=connect)
connect_button.grid(row=3, column=1, sticky=tk.E)

right_frame = ttk.Frame(paned_window, width=1100)
paned_window.add(right_frame, weight=10)

tabs = ttk.Notebook(right_frame)
tabs.pack(fill=tk.BOTH, expand=True)

def open_url():
    webbrowser.open_new("https://github.com/b3b0/shellCellar")

tab1 = ttk.Frame(tabs)
tabs.add(tab1, text="Home")

welcome_text = """Welcome back to shellCellar! 
Version 0.1.1

Written by b3b0
"""

welcome_label = tk.Label(tab1, text=welcome_text, justify=tk.CENTER)
welcome_label.pack(padx=10, pady=10)
url_button = ttk.Button(tab1, text="GitHub", command=open_url)
url_button.pack(pady=10)

#image_path = 'icons/shellCellar.iconset/icon_512x512.png'
#image = tk.PhotoImage(file=image_path)
#image = image.subsample(2, 2)

#image_label = tk.Label(tab1, image=image)
#image_label.image = image
#image_label.pack(side=tk.BOTTOM, pady=10)

def save_connection():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]

    selected_connection['host'] = host_entry.get()
    selected_connection['username'] = username_entry.get()
    hashed_master_password = config['hashed_master_password']
    encrypted_password = encrypt_password(password_entry.get(), hashed_master_password)
    selected_connection['password'] = encrypted_password

    save_connections(connections)

    rb = radiobuttons_frame.winfo_children()[selected_index]
    rb.config(text=selected_connection['host'])


save_button = ttk.Button(editor_frame, text="Save", command=save_connection)
save_button.grid(row=3, column=1, sticky=tk.E)

def add_new_connection():
    guid = str(uuid.uuid4())[:5]
    new_connection = {'host': guid, 'username': '', 'password': ''}
    connections.append(new_connection)
    save_connections(connections)

    index = len(connections) - 1
    rb = ttk.Radiobutton(radiobuttons_frame, text=guid, variable=selected_connection_index, value=index, command=update_entries)
    rb.pack(anchor=tk.W)

    selected_connection_index.set(index)

add_button = ttk.Button(editor_frame, text="+", command=add_new_connection)
add_button.grid(row=3, column=2, sticky=tk.E)

def delete_connection():
    selected_index = selected_connection_index.get()
    if selected_index < len(connections):
        response = messagebox.askyesno("Delete Connection", "Are you sure you want to delete this connection?")
        if response:
            del connections[selected_index]
            save_connections(connections)

            for widget in radiobuttons_frame.winfo_children():
                widget.destroy()
            for index, connection in enumerate(connections):
                rb = ttk.Radiobutton(radiobuttons_frame, text=connection['host'], variable=selected_connection_index, value=index, command=update_entries)
                rb.pack(anchor=tk.W)

            if not connections:
                host_entry.delete(0, tk.END)
                username_entry.delete(0, tk.END)
                password_entry.delete(0, tk.END)
                selected_connection_index.set(-1)

delete_button = ttk.Button(editor_frame, text="Delete", command=delete_connection)
delete_button.grid(row=4, column=1, sticky=tk.E)

def update_entries():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]
    host_entry.delete(0, tk.END)
    host_entry.insert(0, selected_connection['host'])
    username_entry.delete(0, tk.END)
    username_entry.insert(0, selected_connection['username'])
    master_password = get_master_password()
    if master_password:
        decrypted_password = decrypt_password(selected_connection['password'], master_password)
        password_entry.delete(0, tk.END)
        password_entry.insert(0, decrypted_password)
    else:
        password_entry.delete(0, tk.END)
    password_entry.config(show="*")

for index, connection in enumerate(connections):
    rb = ttk.Radiobutton(radiobuttons_frame, text=connection['host'], variable=selected_connection_index, value=index, command=update_entries)
    rb.pack(anchor=tk.W)

update_entries()

root.mainloop()