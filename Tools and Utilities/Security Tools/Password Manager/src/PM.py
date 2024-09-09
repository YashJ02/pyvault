import platform
import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os
from cryptography.fernet import Fernet

# Path to the SQLite database file
BASE_DIR = os.path.dirname(__file__)
IDS_DIR = os.path.join(BASE_DIR, 'ids')
DB_FILE = os.path.join(IDS_DIR, 'passwords.db')

# Ensure the ids directory exists
def ensure_ids_dir_exists():
    if not os.path.exists(IDS_DIR):
        os.makedirs(IDS_DIR)
        
# Create the hidden directory if it doesn't exist
def create_hidden_dir():
    system = platform.system()
    if not os.path.exists(IDS_DIR):
        os.makedirs(IDS_DIR)
        if system == 'Windows':
            import ctypes
            try:
                ctypes.windll.kernel32.SetFileAttributesW(IDS_DIR, 2)  # FILE_ATTRIBUTE_HIDDEN
            except Exception as e:
                print(f"Error hiding directory on Windows: {e}")
        elif system == 'Darwin' or system == 'Linux':
            hidden_dir_path = f".{IDS_DIR}"
            try:
                os.rename(IDS_DIR, hidden_dir_path)
            except Exception as e:
                print(f"Error hiding directory on macOS/Linux: {e}")

create_hidden_dir()

# Generate a key for encryption/decryption
def generate_key():
    return Fernet.generate_key()

# Save the key to a file
def save_key(key):
    with open(os.path.join(IDS_DIR, 'key.key'), 'wb') as key_file:
        key_file.write(key)

# Load the key from a file
def load_key():
    with open(os.path.join(IDS_DIR, 'key.key'), 'rb') as key_file:
        return key_file.read()

# Encrypt a message
def encrypt_message(message):
    key = load_key()
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

# Decrypt a message
def decrypt_message(encrypted_message):
    key = load_key()
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_message).decode()
    return decrypted_message

def connect_to_db():
    ensure_ids_dir_exists()
    conn = sqlite3.connect(DB_FILE)
    return conn

def create_tables():
    conn = connect_to_db()
    cursor = conn.cursor()

    # Create table for passwords
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password BLOB NOT NULL
        )
    ''')

    # Create table for settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin TEXT
        )
    ''')

    conn.commit()
    conn.close()

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def set_pin():
    pin = setup_pin_entry.get()
    confirm_pin = setup_confirm_pin_entry.get()

    if pin != confirm_pin:
        messagebox.showwarning("Error", "PINs do not match!")
        return

    hashed_pin = hash_pin(pin)

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO settings (pin) VALUES (?)', (hashed_pin,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "PIN set successfully!")
        setup_window.destroy()
        open_auth_window()
    except sqlite3.IntegrityError:
        messagebox.showwarning("Error", "PIN already set!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def verify_pin(pin):
    hashed_pin = hash_pin(pin)

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT pin FROM settings WHERE pin = ?', (hashed_pin,))
    pin_record = cursor.fetchone()
    conn.close()

    if pin_record:
        auth_window.destroy()
        open_main_application()
    else:
        messagebox.showwarning("Error", "Invalid PIN!")

def numpad_button_click(value):
    current = active_entry.get()
    active_entry.delete(0, tk.END)
    active_entry.insert(0, current + value)

def submit_pin():
    pin = pin_entry.get()
    verify_pin(pin)

def disable_keyboard_input(entry_widget):
    entry_widget.bind('<KeyPress>', lambda e: 'break')

def open_setup_window():
    global setup_window
    setup_window = tk.Tk()
    setup_window.title("Setup PIN")

    tk.Label(setup_window, text="Enter New PIN:").grid(row=0, column=0, padx=10, pady=10)
    global setup_pin_entry
    setup_pin_entry = tk.Entry(setup_window, show='*', width=15)
    setup_pin_entry.grid(row=0, column=1, padx=10, pady=10)
    disable_keyboard_input(setup_pin_entry)

    tk.Label(setup_window, text="Confirm PIN:").grid(row=1, column=0, padx=10, pady=10)
    global setup_confirm_pin_entry
    setup_confirm_pin_entry = tk.Entry(setup_window, show='*', width=15)
    setup_confirm_pin_entry.grid(row=1, column=1, padx=10, pady=10)
    disable_keyboard_input(setup_confirm_pin_entry)

    # Numpad setup
    numpad = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', 'C', '→'
    ]

    for i, num in enumerate(numpad):
        if num == '→':
            btn = tk.Button(setup_window, text=num, command=set_pin, width=10)
        elif num == 'C':
            btn = tk.Button(setup_window, text=num, command=lambda: active_entry.delete(0, tk.END), width=10)
        else:
            btn = tk.Button(setup_window, text=num, command=lambda num=num: numpad_button_click(num), width=10)
        row = (i // 3) + 2
        col = i % 3
        btn.grid(row=row, column=col, padx=5, pady=5)

    # Set active entry to setup_pin_entry initially
    global active_entry
    active_entry = setup_pin_entry

    # Switch between PIN entry and Confirm PIN entry
    setup_pin_entry.bind('<FocusIn>', lambda e: switch_active_entry(setup_pin_entry))
    setup_confirm_pin_entry.bind('<FocusIn>', lambda e: switch_active_entry(setup_confirm_pin_entry))

    setup_window.mainloop()

def open_auth_window():
    global auth_window
    auth_window = tk.Tk()
    auth_window.title("Authentication")

    global pin_entry
    pin_entry = tk.Entry(auth_window, show='*', width=15)
    pin_entry.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
    disable_keyboard_input(pin_entry)

    # Numpad setup
    numpad = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', 'C', '→'
    ]

    for i, num in enumerate(numpad):
        if num == '→':
            btn = tk.Button(auth_window, text=num, command=submit_pin, width=10)
        elif num == 'C':
            btn = tk.Button(auth_window, text=num, command=lambda: pin_entry.delete(0, tk.END), width=10)
        else:
            btn = tk.Button(auth_window, text=num, command=lambda num=num: numpad_button_click(num), width=10)
        row = (i // 3) + 1
        col = i % 3
        btn.grid(row=row, column=col, padx=5, pady=5)

    # Set active entry to pin_entry
    global active_entry
    active_entry = pin_entry

    auth_window.mainloop()

def switch_active_entry(entry_widget):
    global active_entry
    active_entry = entry_widget

def save_password():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if website and username and password:
        encrypted_password = encrypt_message(password)
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)',
                       (website, username, encrypted_password))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Password saved successfully!")
        website_entry.delete(0, tk.END)
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Error", "All fields are required!")

def view_passwords():
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute('SELECT website, username, password FROM passwords')
    records = cursor.fetchall()
    
    conn.close()

    view_window = tk.Toplevel(root)
    view_window.title("Saved Passwords")

    for i, (website, username, encrypted_password) in enumerate(records, start=1):
        decrypted_password = decrypt_message(encrypted_password)
        tk.Label(view_window, text=f"{i}. {website} | {username} | {decrypted_password}").pack()

def open_main_application():
    global root
    root = tk.Tk()
    root.title("Password Manager")

    tk.Label(root, text="Website:").grid(row=0, column=0, padx=10, pady=10)
    global website_entry
    website_entry = tk.Entry(root, width=35)
    website_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(root, text="Username:").grid(row=1, column=0, padx=10, pady=10)
    global username_entry
    username_entry = tk.Entry(root, width=35)
    username_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(root, text="Password:").grid(row=2, column=0, padx=10, pady=10)
    global password_entry
    password_entry = tk.Entry(root, width=35)
    password_entry.grid(row=2, column=1, padx=10, pady=10)

    save_btn = tk.Button(root, text="Save Password", command=save_password)
    save_btn.grid(row=3, column=1, padx=10, pady=10)

    view_btn = tk.Button(root, text="View Saved Passwords", command=view_passwords)
    view_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    print("Main application window opened.")
    root.mainloop()

# Ensure the ids directory exists
ensure_ids_dir_exists()

# Generate and save the encryption key if it doesn't exist
key_file_path = os.path.join(IDS_DIR, 'key.key')
if not os.path.exists(key_file_path):
    key = generate_key()
    save_key(key)

# Start the application
create_tables()
conn = connect_to_db()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM settings')
if cursor.fetchone()[0] == 0:
    conn.close()
    open_setup_window()
else:
    conn.close()
    open_auth_window()
