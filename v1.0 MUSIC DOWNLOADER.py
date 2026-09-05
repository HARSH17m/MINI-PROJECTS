import yt_dlp
import os
from datetime import datetime


BASE_DIR = r'D:\Youtube_Downs'


def save_link_to_txt(url):
    txt_path = os.path.join(BASE_DIR, "links.txt")

    try:
        with open(txt_path, "a", encoding="utf-8") as f:
            f.write(url + "\n")

        print(f"URL saved to: {txt_path}")

    except Exception as e:
        print(f"Failed to save URL: {e}")


def download_single_video(url):
    today = datetime.now().strftime("%d-%m-%y")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',

        'outtmpl': os.path.join(
            BASE_DIR,
            f'{today} - %(title)s.%(ext)s'
        ),

        'ignoreerrors': True,
        'windowsfilenames': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_playlist(url, playlist_name):
    playlist_dir = os.path.join(BASE_DIR, playlist_name)

    os.makedirs(playlist_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',

        'outtmpl': os.path.join(
            playlist_dir,
            '%(autonumber)03d - %(title)s.%(ext)s'
        ),

        'playlist_items': '::-1',

        'ignoreerrors': True,
        'windowsfilenames': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":

    print("\n===== YouTube Downloader =====")
    print("1. Download Single Video")
    print("2. Download Playlist")

    choice = input("\nSelect Option (1/2): ").strip()

    url = input("Enter URL: ").strip()

    save_link_to_txt(url)

    if choice == "1":
        download_single_video(url)

    elif choice == "2":
        cust_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        playlist_name = cust_timestamp
        download_playlist(url, playlist_name)

    else:
        print("Invalid Choice")
