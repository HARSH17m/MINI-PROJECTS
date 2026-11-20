"""
=========================================
TaskPilot v1.0
Author : Harsh Mistry
=========================================
"""

import os
import shutil
from datetime import datetime

# ---------- Configuration ----------

VERSION = "1.0.0"

INBOX_FILE = "inbox.txt"
LOGBOOK_FILE = "logbook.txt"
ERROR_FILE = "error_bin.txt"
BACKUP_FOLDER = "backups"

SEPARATOR = "=" * 40

# ---------- Helper Functions ----------

def get_current_date():
    """Return today's date."""
    return datetime.now().strftime("%d %B %Y")

# ---------- Create Required Files ----------

def create_required_files():
    """Create all required files and folders if they don't exist."""

    required_files = (
        INBOX_FILE,
        LOGBOOK_FILE,
        ERROR_FILE,
    )

    for file in required_files:
        if not os.path.exists(file):
            open(file, "w", encoding="utf-8").close()

    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)


# ---------- Create Backup ----------

def create_backup():
    """Create a timestamped backup of inbox.txt."""

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    backup_name = f"backup_{timestamp}.txt"

    backup_path = os.path.join(BACKUP_FOLDER, backup_name)

    shutil.copy2(INBOX_FILE, backup_path)

    return backup_name

# ---------- Clean Old Backups ----------

def clean_old_backups():
    """Delete backup files older than 7 days."""

    today = datetime.now()

    for filename in os.listdir(BACKUP_FOLDER):

        file_path = os.path.join(BACKUP_FOLDER, filename)

        if not os.path.isfile(file_path):
            continue

        try:
            # Remove "backup_" prefix and ".txt" extension
            date_string = filename.replace("backup_", "").replace(".txt", "")

            # Convert filename into datetime
            backup_date = datetime.strptime(date_string, "%Y-%m-%d_%H-%M-%S")

            # Difference in days
            age = (today - backup_date).days

            if age >= 7:
                os.remove(file_path)
                print(f"Deleted old backup: {filename}")

        except ValueError:
            # Ignore files that don't match our backup format
            continue

# ----------- Reads Tasks -----------

def read_tasks():
    """Read all tasks from inbox.txt."""

    with open(INBOX_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    cleaned_tasks = []

    for line in lines:
        task = line.strip()

        if task:
            cleaned_tasks.append(task)

    return cleaned_tasks

# ---------- Classify Tasks ----------

def classify_tasks(task_list):
    """Separate completed, reminder and invalid tasks."""

    tasks = {
        "completed": [],
        "reminders": [],
        "invalid": []
    }

    for task in task_list:

        if task.startswith("-"):
            tasks["completed"].append(task[1:].strip())

        elif task.startswith("+"):
            tasks["reminders"].append(task)

        else:
            tasks["invalid"].append(task)

    return tasks

# ---------- Update Journal ----------

def update_journal(filename, entries):
    """
    Save entries into a journal file.
    Newest date always stays at the top.
    """

    if not entries:
        return

    current_date = get_current_date()

    # Read existing journal
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    # -----------------------------
    # Case 1 : Empty journal
    # -----------------------------
    if not lines:

        new_lines = [
            SEPARATOR,
            current_date,
            SEPARATOR,
            ""
        ]

        for entry in entries:
            new_lines.append(f"• {entry}")

        new_lines.append("")

    # -----------------------------
    # Case 2 : Journal already has data
    # -----------------------------
    else:

        # Today's section already exists
        if len(lines) >= 2 and lines[1] == current_date:

            new_lines = []
            insert_index = len(lines)

            # Find where next section starts
            for index in range(3, len(lines)):
                if lines[index] == SEPARATOR:
                    insert_index = index
                    break

            # Keep today's section
            new_lines.extend(lines[:insert_index])

            # Add new tasks
            for entry in entries:
                new_lines.append(f"• {entry}")

            new_lines.append("")

            # Add remaining journal
            new_lines.extend(lines[insert_index:])

        # Today's section doesn't exist
        else:

            new_lines = [
                SEPARATOR,
                current_date,
                SEPARATOR,
                ""
            ]

            for entry in entries:
                new_lines.append(f"• {entry}")

            new_lines.append("")

            new_lines.extend(lines)

    # Write updated journal
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(new_lines))

# ---------- Sort Reminders ----------

def sort_reminders(reminders):
    """
    Sort reminders according to priority.
    """

    highest = []
    high = []
    medium = []
    normal = []

    for reminder in reminders:

        text = reminder.strip()

        if text.startswith("+ !!!"):
            highest.append(text)

        elif text.startswith("+ !!"):
            high.append(text)

        elif text.startswith("+ !"):
            medium.append(text)

        else:
            normal.append(text)

    return highest + high + medium + normal

# ---------- Rewrite Inbox ----------

def rewrite_inbox(reminders):
    """
    Rewrite inbox.txt with sorted reminder tasks.
    """

    reminders = sort_reminders(reminders)

    with open(INBOX_FILE, "w", encoding="utf-8") as file:

        for reminder in reminders:
            file.write(reminder.strip() + "\n")

# ---------- Initialize ----------

def initialize():
    """Prepare TaskPilot before processing."""

    create_required_files()
    clean_old_backups()

# ---------- Process Tasks ----------

def process_tasks():
    """Process all tasks from inbox."""  

    backup_file = create_backup()

    task_list = read_tasks()

    classified_tasks = classify_tasks(task_list)

    update_journal(LOGBOOK_FILE, classified_tasks["completed"])
    update_journal(ERROR_FILE, classified_tasks["invalid"])

    rewrite_inbox(classified_tasks["reminders"])

    return backup_file, task_list, classified_tasks

# ---------- Summary ----------

def show_summary(backup_file, task_list, tasks):
    """Display processing summary."""

    print("\n" + SEPARATOR)
    print("TaskPilot Summary")
    print(SEPARATOR)

    print(f"Backup File : {backup_file}")
    print(f"Tasks Read  : {len(task_list)}")
    print(f"Completed   : {len(tasks['completed'])}")
    print(f"Reminders   : {len(tasks['reminders'])}")
    print(f"Invalid     : {len(tasks['invalid'])}")

    print("\nTaskPilot finished successfully!")
                    
# ---------- Main ----------

def main():

    print("\n" + SEPARATOR)
    print(f"        TaskPilot v{VERSION}")
    print(SEPARATOR)

    initialize()

    backup_file, task_list, tasks = process_tasks()

    show_summary(backup_file, task_list, tasks)

if __name__ == "__main__":
    main()

    input("\nPress Enter to Exit...")