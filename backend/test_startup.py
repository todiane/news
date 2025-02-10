# /home/djangify/news/backend/test_startup.py

import os
import sys
from pathlib import Path

# Create debug file
debug_path = Path("/home/djangify/news/tmp/debug.txt")
with open(debug_path, "a") as f:
    f.write("\n--- Starting Debug Log ---\n")
    f.write(f"Python Version: {sys.version}\n")
    f.write(f"Python Path: {sys.path}\n")
    f.write(f"Current Directory: {os.getcwd()}\n")
    f.write("Environment Variables:\n")
    for key, value in os.environ.items():
        f.write(f"{key}: {value}\n")