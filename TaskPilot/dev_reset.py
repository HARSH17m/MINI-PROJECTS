"""
Reset TaskPilot development files.
"""

import os
import shutil

FILES = [
    "inbox.txt",
    "logbook.txt",
    "error_bin.txt"
]

BACKUP_FOLDER = "backups"


# Clear text files
for file in FILES:

    if os.path.exists(file):

        with open(file, "w", encoding="utf-8") as f:
            pass


# Delete backup folder
if os.path.exists(BACKUP_FOLDER):
    shutil.rmtree(BACKUP_FOLDER)

# Create new backup folder
os.makedirs(BACKUP_FOLDER)

print("TaskPilot reset successfully.")

input("\nPress Enter to Exit...")