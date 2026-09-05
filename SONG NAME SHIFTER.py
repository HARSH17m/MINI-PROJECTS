from pathlib import Path
import shutil
import re


def main():
    print("=" * 60)
    print("       SONG NUMBER SHIFT & SAFE RENAME TOOL")
    print("=" * 60)

    # -----------------------------
    # INPUT
    # -----------------------------
    while True:
        try:
            increase_by = int(input("\nNumber to increase by: "))
            break
        except ValueError:
            print("Please enter a valid integer.")

    while True:
        folder_input = input("Files location: ").strip().strip('"')
        source = Path(folder_input)

        if source.is_dir():
            break

        print("That folder does not exist. Please enter a valid path.")

    # Temporary folder is created in the source folder's parent.
    temp = source.parent / "temp"

    if temp.exists():
        print(f"\nERROR: Temporary folder already exists:")
        print(temp)
        print("Please remove/rename it first so existing files are not touched.")
        return

    # Filename format:
    # number - song_name.extension
    pattern = re.compile(r"^(\d+)\s-\s(.+)$")

    # Only files directly inside the selected folder.
    songs = []

    for file in source.iterdir():
        if not file.is_file():
            continue

        match = pattern.match(file.name)
        if match:
            songs.append((file, int(match.group(1)), match.group(2)))

    if not songs:
        print("\nNo files matching 'number - song_name' were found.")
        return

    # Sort by current number, then filename.
    songs.sort(key=lambda x: (x[1], x[0].name.lower()))

    print(f"\nFound {len(songs)} matching song(s).")
    print(f"Temporary location: {temp}")

    # -----------------------------
    # PREVIEW
    # -----------------------------
    print("\n" + "-" * 60)
    print("RENAME PREVIEW")
    print("-" * 60)

    planned = []

    for old_path, number, rest in songs:
        new_number = number + increase_by
        new_name = f"{new_number} - {rest}"
        planned.append((old_path, new_name))
        print(f"{old_path.name}  ->  {new_name}")

    # Check for duplicate target names before moving anything.
    target_names = [new_name.lower() for _, new_name in planned]

    if len(target_names) != len(set(target_names)):
        print("\nERROR: Two or more songs would receive the same filename.")
        print("Nothing has been changed.")
        return

    # Check whether target names already exist in the source folder.
    source_names = {p.name.lower() for p in source.iterdir() if p.is_file()}

    conflicts = []
    original_names = {old.name.lower() for old, _ in planned}

    for old_path, new_name in planned:
        if (
            new_name.lower() in source_names
            and new_name.lower() not in original_names
        ):
            conflicts.append(new_name)

    if conflicts:
        print("\nERROR: These destination filenames already exist:")
        for name in conflicts:
            print(f"  {name}")
        print("\nNothing has been changed.")
        return

    # -----------------------------
    # CONFIRMATION
    # -----------------------------
    answer = input("\nProceed with these changes? [y/N]: ").strip().lower()

    if answer not in ("y", "yes"):
        print("Cancelled. No files were changed.")
        return

    # -----------------------------
    # TEMP TRANSFER + RENAME
    # -----------------------------
    try:
        temp.mkdir()

        moved = []

        for old_path, new_name in planned:
            temp_path = temp / new_name

            # Move and rename in one operation.
            shutil.move(str(old_path), str(temp_path))
            moved.append(temp_path)

            print(f"[OK] {old_path.name}  ->  {new_name}")

        # Verify that every processed file reached temp.
        if len(moved) != len(songs) or any(not p.exists() for p in moved):
            raise RuntimeError("Verification failed: not all files reached temp.")

        print("\nAll songs successfully renamed and transferred to temp.")
        print("Transferring them back to the original folder...")

        # Move renamed songs back to the original folder.
        transferred_back = []

        for temp_path in moved:
            destination = source / temp_path.name

            if destination.exists():
                raise FileExistsError(
                    f"Destination already exists: {destination.name}"
                )

            shutil.move(str(temp_path), str(destination))
            transferred_back.append(destination)

        # Final verification: every renamed song exists in original folder.
        if len(transferred_back) != len(songs):
            raise RuntimeError("Final verification failed.")

        if any(not p.exists() for p in transferred_back):
            raise RuntimeError(
                "Final verification failed: one or more songs are missing."
            )

        # Temp should now be empty.
        if temp.exists():
            remaining = list(temp.iterdir())
            if remaining:
                print("\nWARNING: Temp folder still contains:")
                for item in remaining:
                    print(f"  {item.name}")
                print("Temp folder was NOT deleted.")
            else:
                temp.rmdir()

        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print(f"Processed: {len(songs)} song(s)")
        print(f"Original folder: {source}")

    except Exception as error:
        print("\n" + "=" * 60)
        print("ERROR")
        print("=" * 60)
        print(error)
        print("\nThe program stopped to avoid silently overwriting files.")
        print(f"Temporary folder: {temp}")
        print("Please inspect it before running the program again.")


if __name__ == "__main__":
    main()
