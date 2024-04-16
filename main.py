import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import hashlib
import os
import subprocess
import logging
import re
import uuid
import webbrowser
import requests
import markdown
from tkhtmlview import HTMLLabel

class NewConnectionDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Friendly Name:").grid(row=0)
        tk.Label(master, text="Host:").grid(row=1)
        tk.Label(master, text="Username:").grid(row=2)

        self.friendly_name_entry = tk.Entry(master)
        self.host_entry = tk.Entry(master)
        self.username_entry = tk.Entry(master)

        self.friendly_name_entry.grid(row=0, column=1)
        self.host_entry.grid(row=1, column=1)
        self.username_entry.grid(row=2, column=1)

        return self.friendly_name_entry

    def apply(self):
        self.result = {
            'friendly_name': self.friendly_name_entry.get(),
            'host': self.host_entry.get(),
            'username': self.username_entry.get(),
        }

global master_password
master_password = None
APP_VERSION = "0.2.2"
APP_NAME = "shellar.io"
APP_DATA_PATH = os.path.expanduser(f"~/.{APP_NAME}")

if not os.path.exists(APP_DATA_PATH):
    os.makedirs(APP_DATA_PATH)

CONFIG_FILE = os.path.join(APP_DATA_PATH, 'app_config.json')
CONNECTIONS_FILE = os.path.join(APP_DATA_PATH, 'connections.json')

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def remove_sshpass_from_history():
    history_file_path = os.path.expanduser("~/.zsh_history")
    try:
        with open(history_file_path, "r") as file:
            lines = file.readlines()
        with open(history_file_path, "w") as file:
            for line in lines:
                if "sshpass" not in line:
                    file.write(line)
    except Exception as e:
        logging.error(f"Error removing sshpass from history: {e}")

remove_sshpass_from_history()

def strip_ansi(text):
    return ansi_escape.sub('', text)

logging.basicConfig(level=logging.DEBUG)

def get_master_password():
    hashed_master_password = config.get('hashed_master_password')
    logging.debug(f"Hashed Master Password: {hashed_master_password}")
    return hashed_master_password

def connect():
    if has_unsaved_changes():
        if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Would you like to save them before connecting?"):
            save_connection()
        else:
            update_entries()

    initiate_connection()

def initiate_connection():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]

    username = selected_connection['username']
    host = selected_connection['host']

    tools_path = os.path.expanduser(f"~/.{APP_NAME}/tools")
    script_path = os.path.join(tools_path, "setupKey.sh")

    if not os.path.exists(tools_path):
        os.makedirs(tools_path)

    if not os.path.exists(script_path):
        create_setup_script(script_path)

    applescript_command = f'''
    tell application "Terminal"
        do script "bash \\"{script_path}\\" \\"{username}\\" \\"{host}\\""
        activate
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript_command], check=True)



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

def add_first_connection(master_password):
    print("ADDING FIRST")
    master_password = config['hashed_master_password']
    if not master_password:
        set_master_password()

    dialog = NewConnectionDialog(root, title="New Connection")
    if dialog.result:
        friendly_name = dialog.result['friendly_name']
        host = dialog.result['host']
        username = dialog.result['username']
        connections.append({'friendly_name': friendly_name, 'host': host, 'username': username})
        save_connections(connections)

def set_master_password():
    print("SETTING MASTER")
    master_password = simpledialog.askstring("Master Password", "Set a master password:", show='*')
    confirm_password = simpledialog.askstring("Confirm Master Password", "Confirm master password:", show='*')
    if master_password and confirm_password:
        if master_password == confirm_password:
            hashed_master_password = hashlib.sha256(master_password.encode()).hexdigest()
            config['master_password_set'] = True
            config['hashed_master_password'] = hashed_master_password
            save_config(config)
        else:
            messagebox.showerror("Error", "Passwords do not match. Please try again.")
            set_master_password()
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
root.geometry("800x600")

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

left_frame = ttk.Frame(paned_window, width=60)
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
friendly_name_label = ttk.Label(editor_frame, text="Friendly Name:")
friendly_name_entry = ttk.Entry(editor_frame)
host_label = ttk.Label(editor_frame, text="Host:")
host_label.grid(row=0, column=0, sticky=tk.W)
host_entry = ttk.Entry(editor_frame)
host_entry.grid(row=0, column=1, sticky=tk.EW)
username_label = ttk.Label(editor_frame, text="Username:")
username_label.grid(row=1, column=0, sticky=tk.W)
username_entry = ttk.Entry(editor_frame)
username_entry.grid(row=1, column=1, sticky=tk.EW)

connect_button = ttk.Button(editor_frame, text="Connect", command=connect)
connect_button.grid(row=3, column=1, sticky=tk.E)

right_frame = ttk.Frame(paned_window, width=600)
paned_window.add(right_frame, weight=10)

tabs = ttk.Notebook(right_frame)
tabs.pack(fill=tk.BOTH, expand=True)

def open_url():
    webbrowser.open_new("https://github.com/b3b0/shellar.io")

tab1 = ttk.Frame(tabs)
tabs.add(tab1, text="Home")

def load_readme(tab):
    url = "https://raw.githubusercontent.com/b3b0/shellar.io/main/README.md"
    response = requests.get(url)
    if response.status_code == 200:
        readme_content = response.text
        html_content = markdown.markdown(readme_content)  # Convert Markdown to HTML
        readme_label = HTMLLabel(tab, html=html_content, background="white")
        readme_label.pack(fill="both", expand=True)
    else:
        error_label = tk.Label(tab, text="Failed to load README.md", font=("Helvetica", 16))
        error_label.pack(pady=20)

readme_html = load_readme(tab1)

def save_connection():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]

    selected_connection['friendly_name'] = friendly_name_entry.get()
    selected_connection['host'] = host_entry.get()
    selected_connection['username'] = username_entry.get()

    save_connections(connections)

    rb = radiobuttons_frame.winfo_children()[selected_index]
    rb.config(text=selected_connection['friendly_name'])

save_button = ttk.Button(editor_frame, text="Save", command=save_connection)
save_button.grid(row=3, column=1, sticky=tk.E)

def add_new_connection():
    guid = str(uuid.uuid4())[:5]
    new_connection = {'host': guid, 'username': ''}
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
                selected_connection_index.set(-1)

delete_button = ttk.Button(editor_frame, text="Delete", command=delete_connection)
delete_button.grid(row=4, column=1, sticky=tk.E)

def update_entries():
    """ Update entry widgets with the selected connection details. """
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]
    friendly_name_entry.delete(0, tk.END)
    friendly_name_entry.insert(0, selected_connection.get('friendly_name', ''))
    host_entry.delete(0, tk.END)
    host_entry.insert(0, selected_connection['host'])
    username_entry.delete(0, tk.END)
    username_entry.insert(0, selected_connection['username'])

for index, connection in enumerate(connections):
    rb = ttk.Radiobutton(radiobuttons_frame, text=connection.get('friendly_name', connection['host']), variable=selected_connection_index, value=index)
    rb.pack(anchor=tk.W)
    rb.bind("<Button-1>", lambda event, idx=index: selected_connection_index.set(idx) or update_entries())
    rb.bind("<Double-1>", lambda event, idx=index: selected_connection_index.set(idx) or connect()) 

if connections:
    update_entries()

def has_unsaved_changes():
    selected_index = selected_connection_index.get()
    selected_connection = connections[selected_index]
    current_details = {
        'friendly_name': friendly_name_entry.get(),
        'host': host_entry.get(),
        'username': username_entry.get(),
    }

    return any(current_details[key] != selected_connection[key] for key in current_details)


def create_setup_script(script_path):
    """ Creates the SSH setup script if it doesn't exist. """
    with open(script_path, "w") as script_file:
        script_file.write("""#!/bin/bash
clear
setup_success=true

if [ ! -f ~/.ssh/id_rsa ]; then
    echo "No SSH key found. Generating a new one..."
    if ! command -v ssh-keygen &> /dev/null; then
        echo "ssh-keygen not found. Please install it using your package manager."
        setup_success=false
    else
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    fi
fi

if [ "$setup_success" = true ]; then
    echo "Trying to authenticate with the server using the SSH key..."
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no "$1@$2" exit

    if [ $? -ne 0 ]; then
        echo "Authentication failed. Attempting to copy SSH key to the server..."
        if ! command -v ssh-copy-id &> /dev/null; then
            echo "ssh-copy-id not found. Please install it using your package manager."
            setup_success=false
        else
            ssh-copy-id "$1@$2"
        fi
    fi
fi

if [ "$setup_success" = true ]; then
    echo "Connecting to $2 as $1..."
    ssh "$1@$2"
else
    echo "SSH setup failed. Please resolve the issues and try again."
fi
""")
    os.chmod(script_path, 0o755)

def update_editor_frame_layout():
    add_button.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
    friendly_name_label.grid(row=1, column=0, sticky=tk.W)
    friendly_name_entry.grid(row=1, column=1, sticky=tk.EW)
    host_label.grid(row=2, column=0, sticky=tk.W)
    host_entry.grid(row=2, column=1, sticky=tk.EW)
    username_label.grid(row=3, column=0, sticky=tk.W)
    username_entry.grid(row=3, column=1, sticky=tk.EW)
    save_button.grid(row=5, column=0, sticky=tk.W)
    delete_button.grid(row=6, column=0, sticky=tk.E)
    connect_button.grid(row=0, column=1, sticky=tk.E)

update_editor_frame_layout()
root.bind("<Destroy>", lambda event: remove_sshpass_from_history())
root.mainloop()