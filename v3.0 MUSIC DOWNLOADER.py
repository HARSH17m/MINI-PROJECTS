import glob
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import yt_dlp
from yt_dlp.utils import sanitize_filename


BASE_DIR = r'D:\Youtube_Downs'
AUDIO_QUALITY = '192'   # kbps. YouTube audio is ~128-160 kbps, so 192 loses nothing
PARALLEL = 3            # songs downloaded at the same time in a playlist


def save_link_to_txt(url):
    os.makedirs(BASE_DIR, exist_ok=True)
    txt_path = os.path.join(BASE_DIR, "links.txt")

    try:
        with open(txt_path, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        print(f"URL saved to: {txt_path}")

    except Exception as e:
        print(f"Failed to save URL: {e}")


def build_opts(outtmpl):
    """Audio only -> MP3, with artist/title tags and square cover art embedded."""
    return {
        # best audio stream only, no video, so no video+audio merge step
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,

        # faster downloading of the stream
        'concurrent_fragment_downloads': 4,

        # thumbnail + tags
        'writethumbnail': True,
        'postprocessors': [
            {   # one quick audio-only conversion to mp3
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': AUDIO_QUALITY,
            },
            {   # thumbnail (webp) -> jpg so it can be embedded in mp3
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
                'when': 'before_dl',
            },
            {   # title, artist (falls back to channel name), etc.
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {   # put the cover art inside the mp3
                'key': 'EmbedThumbnail',
            },
        ],
        # crop the 16:9 thumbnail to a square, like real album art
        'postprocessor_args': {
            'thumbnailsconvertor+ffmpeg_o': [
                '-c:v', 'mjpeg', '-q:v', '2',
                '-vf', "crop='if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'",
            ],
        },

        'ignoreerrors': True,
        'windowsfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }


def download_single_video(url):
    today = datetime.now().strftime("%d-%m-%y")
    os.makedirs(BASE_DIR, exist_ok=True)

    outtmpl = os.path.join(BASE_DIR, f'{today} - %(title)s.%(ext)s')

    print("Downloading...")
    with yt_dlp.YoutubeDL(build_opts(outtmpl)) as ydl:
        ydl.download([url])
    print("Done.")


def get_playlist_entries(url):
    """Fetch the playlist's title and song list without downloading anything."""
    opts = {'extract_flat': True, 'quiet': True, 'ignoreerrors': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = [e for e in (info.get('entries') or []) if e]
    title = info.get('title') or "Playlist"
    return title, entries


def download_one(entry, number, playlist_dir):
    # skip songs already downloaded in an earlier run
    if glob.glob(os.path.join(glob.escape(playlist_dir), f'{number:03d} - *.mp3')):
        return number, "skipped"

    video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"
    outtmpl = os.path.join(playlist_dir, f'{number:03d} - %(title)s.%(ext)s')

    try:
        with yt_dlp.YoutubeDL(build_opts(outtmpl)) as ydl:
            ydl.download([video_url])
        return number, "ok"
    except Exception as e:
        return number, f"failed ({e})"


def download_playlist(url):
    print("Reading playlist...")
    playlist_title, entries = get_playlist_entries(url)

    if not entries:
        print("No videos found in this playlist.")
        return

    # same order as before ('::-1'): reversed, so 001 is the first-added song
    entries.reverse()

    playlist_dir = os.path.join(BASE_DIR, sanitize_filename(playlist_title))
    os.makedirs(playlist_dir, exist_ok=True)

    total = len(entries)
    print(f"Playlist: {playlist_title} ({total} songs)\n")

    done = 0
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = [
            pool.submit(download_one, entry, number, playlist_dir)
            for number, entry in enumerate(entries, start=1)
        ]
        for future in as_completed(futures):
            number, status = future.result()
            done += 1
            print(f"[{done}/{total}] #{number:03d} {status}")

    print(f"\nAll done. Saved in: {playlist_dir}")


if __name__ == "__main__":

    print("\n===== YouTube Music Downloader (MP3) =====")
    print("1. Download Single Song")
    print("2. Download Playlist")

    choice = input("\nSelect Option (1/2): ").strip()

    url = input("Enter URL: ").strip()

    save_link_to_txt(url)

    if choice == "1":
        download_single_video(url)

    elif choice == "2":
        download_playlist(url)

    else:
        print("Invalid Choice")
