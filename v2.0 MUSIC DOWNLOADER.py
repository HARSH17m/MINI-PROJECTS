import yt_dlp
import os
from datetime import datetime


BASE_DIR = r'D:\Youtube_Downs'
LINKS_FILE = os.path.join(BASE_DIR, "links.txt")


def get_timestamp():
    return datetime.now().strftime("%d-%m-%y %H:%M:%S")


def save_link_to_txt(url, download_type):
    try:
        os.makedirs(BASE_DIR, exist_ok=True)

        with open(LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{get_timestamp()}] [{download_type}] {url}\n")

        print(f"URL saved to: {LINKS_FILE}")

    except Exception as e:
        print(f"Failed to save URL: {e}")


def get_common_options():
    return {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'windowsfilenames': True,
    }


# SINGLE VIDEO

def download_single_video(url):

    today = datetime.now().strftime("%d-%m-%y")

    ydl_opts = get_common_options()

    ydl_opts.update({
        'outtmpl': os.path.join(
            BASE_DIR,
            f'{today} - %(title)s.%(ext)s'
        ),

        # Make sure a playlist URL only downloads the requested video.
        'noplaylist': True,

        # Continue instead of crashing the whole program.
        'ignoreerrors': True,

        # Don't overwrite an existing file.
        'nooverwrites': True,
    })

    print("\nStarting single video download...\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        if result == 0:
            print("\nDownload completed successfully.")
        else:
            print("\nDownload completed with errors.")

    except Exception as e:
        print(f"\nDownload failed: {e}")



# PLAYLIST

def download_playlist(url):

    # First extract playlist information.
    info_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        playlist_title = info.get('title')

        if not playlist_title:
            playlist_title = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

    except Exception as e:
        print(f"\nCould not determine playlist name: {e}")

        playlist_title = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

    # Remove characters that Windows doesn't allow in folder names.
    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:
        playlist_title = playlist_title.replace(char, '_')

    playlist_dir = os.path.join(BASE_DIR, playlist_title)

    os.makedirs(playlist_dir, exist_ok=True)

    ydl_opts = get_common_options()

    ydl_opts.update({
        'outtmpl': os.path.join(
            playlist_dir,
            '%(autonumber)03d - %(title)s.%(ext)s'
        ),

        #'playlist_items': '::-1',

        'ignoreerrors': True,

        'nooverwrites': True,
    })

    print(f"\nPlaylist: {playlist_title}")
    print(f"Saving to: {playlist_dir}")
    print("\nStarting playlist download...\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        if result == 0:
            print("\nPlaylist downloaded successfully.")
        else:
            print("\nPlaylist download completed with errors.")

    except Exception as e:
        print(f"\nPlaylist download failed: {e}")



# MAIN MENU


def main():

    os.makedirs(BASE_DIR, exist_ok=True)

    while True:

        print("\n")
        print("<>" * 45)
        print("          YOUTUBE DOWNLOADER")
        print("<>" * 45)

        print("1. Download Single Video")
        print("2. Download Playlist")
        print("3. Exit")

        choice = input("\nSelect Option (1/2/3): ").strip()

        if choice == "3":
            print("\nGoodbye...")
            break

        if choice not in ("1", "2"):
            print("\nInvalid choice. Please select 1, 2, or 3.")
            continue

        url = input("\nEnter URL: ").strip()

        if not url:
            print("URL cannot be empty.")
            continue

        if choice == "1":

            save_link_to_txt(url, "SINGLE")

            download_single_video(url)

        elif choice == "2":

            save_link_to_txt(url, "PLAYLIST")

            download_playlist(url)

        print("\n" + "-" * 45)
        input("Press ENTER to return to menu...")



# PROGRAM START


if __name__ == "__main__":
    main()

