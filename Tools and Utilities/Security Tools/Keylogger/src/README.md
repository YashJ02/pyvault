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

2. **Configure Server URL**

    Update the SERVER_URL variable with your server's upload URL:
    ```
    SERVER_URL = 'https://yourserver.com/upload'
