import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import yt_dlp
from yt_dlp.utils import sanitize_filename

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

import time
import msvcrt      # Windows: detect key press
import winsound    # Windows: notification sound

BASE_DIR = r'D:\Youtube_Downs'
AUDIO_QUALITY = '192'   # kbps
PARALLEL = 3            # songs downloaded at the same time

STATE_FILE = 'sync_state.json'                          # inside each playlist folder
REGISTRY_FILE = os.path.join(BASE_DIR, 'playlists.json')  # playlist id -> folder name
NUM_PREFIX = re.compile(r'^\d+ - ')
UNAVAILABLE_TITLES = ('[Private video]', '[Deleted video]')


# ---------------------------------------------------------------- helpers

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'concurrent_fragment_downloads': 4,

        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': AUDIO_QUALITY,
            },
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
                'when': 'before_dl',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {
                'key': 'EmbedThumbnail',
            },
        ],
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


# ---------------------------------------------------------- single video

def download_single_video(url):
    today = datetime.now().strftime("%d-%m-%y")
    os.makedirs(BASE_DIR, exist_ok=True)

    outtmpl = os.path.join(BASE_DIR, f'{today} - %(title)s.%(ext)s')

    print("Downloading...")
    with yt_dlp.YoutubeDL(build_opts(outtmpl)) as ydl:
        ydl.download([url])
    print("Done.")


# -------------------------------------------------------- playlist: scan

def get_playlist(url):
    """Read the playlist online (no downloading). Returns id, title, entries."""
    opts = {'extract_flat': True, 'quiet': True, 'ignoreerrors': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        return None, None, []

    entries = []
    for e in (info.get('entries') or []):
        if e and e.get('id'):
            entries.append({'id': e['id'], 'title': e.get('title') or e['id']})

    return info.get('id'), info.get('title') or "Playlist", entries


def find_playlist_dir(playlist_id, title):
    """Same playlist -> same folder every time (remembered by playlist id)."""
    os.makedirs(BASE_DIR, exist_ok=True)
    registry = load_json(REGISTRY_FILE, {})

    name = registry.get(playlist_id)

    if not name:
        print(f"\nNew playlist: {title}")
        existing = input("Already have a folder for it? Type its name "
                         "(or press Enter to create a new one): ").strip()
        name = existing or sanitize_filename(title)
        registry[playlist_id] = name
        save_json(REGISTRY_FILE, registry)

    path = os.path.join(BASE_DIR, name)
    os.makedirs(path, exist_ok=True)
    return path


def adopt_existing(playlist_dir, state, entries):
    """
    Folders made by the older versions have no record of which file is which
    video. Match those files to playlist entries by song name, once.
    """
    claimed = {rec['file'] for rec in state.values()}
    loose = {}

    for f in os.listdir(playlist_dir):
        if f.lower().endswith('.mp3') and f not in claimed and not f.startswith('~'):
            base = NUM_PREFIX.sub('', f[:-4])
            loose[base.lower()] = (f, base)

    adopted = 0
    for e in entries:
        if e['id'] in state:
            continue
        key = sanitize_filename(e['title']).lower()
        if key in loose:
            f, base = loose.pop(key)
            state[e['id']] = {'name': base, 'file': f}
            adopted += 1

    if adopted:
        print(f"Recognised {adopted} songs already in the folder.")
    if loose:
        print(f"{len(loose)} files in the folder don't match this playlist "
              f"and will be left untouched.")


# ---------------------------------------------------- playlist: download

def download_one(entry, staging):
    outtmpl = os.path.join(staging, '%(id)s.%(ext)s')
    url = f"https://www.youtube.com/watch?v={entry['id']}"

    try:
        with yt_dlp.YoutubeDL(build_opts(outtmpl)) as ydl:
            info = ydl.extract_info(url, download=True)

        if info and os.path.exists(os.path.join(staging, f"{entry['id']}.mp3")):
            return entry['id'], info.get('title') or entry['title']
    except Exception as e:
        print(f"   error: {e}")

    return entry['id'], None


def renumber(playlist_dir, state, order):
    """
    Give every song its right number (001 = first in `order`).
    Two passes through temporary names so numbers never collide mid-way.
    """
    ours = {rec['file'] for rec in state.values()}
    plan = []

    for n, vid in enumerate(order, start=1):
        name = state[vid]['name']
        target = f"{n:03d} - {name}.mp3"

        # never overwrite a file that isn't ours
        if os.path.exists(os.path.join(playlist_dir, target)) and target not in ours:
            target = f"{n:03d} - {name} (2).mp3"

        if state[vid]['file'] != target:
            plan.append((vid, target))

    for vid, _ in plan:
        tmp = f"~tmp~{vid}.mp3"
        os.rename(os.path.join(playlist_dir, state[vid]['file']),
                  os.path.join(playlist_dir, tmp))
        state[vid]['file'] = tmp

    for vid, target in plan:
        os.rename(os.path.join(playlist_dir, state[vid]['file']),
                  os.path.join(playlist_dir, target))
        state[vid]['file'] = target

    return len(plan)


def tag_songs(playlist_dir, state, order):
    """Write '001 - Name' into the title tag and the track number, so
    phone players show the same numbering as the filenames."""
    for n, vid in enumerate(order, start=1):
        path = os.path.join(playlist_dir, state[vid]['file'])
        wanted = f"{n:03d} - {state[vid]['name']}"

        try:
            try:
                tags = EasyID3(path)
            except ID3NoHeaderError:
                tags = EasyID3()

            # skip files that are already correct
            if (tags.get('title', [''])[0] == wanted
                    and tags.get('tracknumber', [''])[0] == str(n)):
                continue

            tags['title'] = wanted
            tags['tracknumber'] = str(n)
            tags.save(path)

        except Exception as e:
            print(f"   could not tag {state[vid]['file']}: {e}")
            

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def notify():
    """Short three-tone chime."""
    try:
        for freq, dur in ((880, 150), (1100, 150), (1320, 350)):
            winsound.Beep(freq, dur)
    except Exception:
        print('\a')


def show_summary(title, downloaded, failed, removed, total, elapsed, folder):
    os.system('cls')

    print("=" * 44)
    print("            SYNC COMPLETE")
    print("=" * 44)
    print(f"  Playlist   : {title}")
    print(f"  Downloaded : {downloaded}")
    print(f"  Failed     : {failed}")
    print(f"  Removed    : {removed}")
    print(f"  Total songs: {total}")
    print(f"  Time taken : {format_time(elapsed)}")
    print(f"  Folder     : {folder}")
    if failed:
        print("\n  Some songs failed. Run option 2 again to retry them.")
    print("=" * 44)

    notify()

    # discard any keys pressed while downloading, so it doesn't close instantly
    while msvcrt.kbhit():
        msvcrt.getch()

    print("\nPress any key to exit...")
    msvcrt.getch()


def sync_playlist(url):
    start_time = time.time()
    downloaded = 0
    failed = 0
    print("Reading playlist online...")
    playlist_id, title, entries = get_playlist(url)

    # safety: never "sync" against an empty/failed read, it would wipe everything
    if not playlist_id or not entries:
        print("Could not read the playlist (or it is empty). Nothing changed.")
        return

    playlist_dir = find_playlist_dir(playlist_id, title)
    state_path = os.path.join(playlist_dir, STATE_FILE)
    state = load_json(state_path, {})

    # files deleted by hand -> forget them so they get downloaded again
    for vid in [v for v, r in state.items()
                if not os.path.exists(os.path.join(playlist_dir, r['file']))]:
        del state[vid]

    adopt_existing(playlist_dir, state, entries)

    online_ids = {e['id'] for e in entries}
    removed = [vid for vid in state if vid not in online_ids]
    new_songs = [e for e in entries
                 if e['id'] not in state and e['title'] not in UNAVAILABLE_TITLES]
    skipped = [e for e in entries
               if e['id'] not in state and e['title'] in UNAVAILABLE_TITLES]

    print(f"\nPlaylist : {title}")
    print(f"Online   : {len(entries)} songs")
    print(f"On device: {len(state) - len(removed)} already downloaded")
    print(f"New      : {len(new_songs)} to download")
    print(f"Removed  : {len(removed)} no longer in the playlist")
    if skipped:
        print(f"Skipped  : {len(skipped)} private/deleted videos")

    # ---- 1. songs removed online -> remove from device too
    if removed:
        print("\nRemoved from the playlist online:")
        for vid in removed:
            print(f"  - {state[vid]['name']}")

        ans = input("\nDelete these from your device? "
                    "(y = delete, n = move to '_removed' folder): ").strip().lower()

        for vid in removed:
            src = os.path.join(playlist_dir, state[vid]['file'])
            if ans == 'y':
                os.remove(src)
            else:
                trash = os.path.join(playlist_dir, '_removed')
                os.makedirs(trash, exist_ok=True)
                shutil.move(src, os.path.join(trash, state[vid]['file']))
            del state[vid]

        save_json(state_path, state)

    # ---- 2. download only the new songs
    if new_songs:
        staging = os.path.join(playlist_dir, '.staging')
        os.makedirs(staging, exist_ok=True)

        print(f"\nDownloading {len(new_songs)} new songs...\n")
        done = 0
        dl_start = time.time()

        with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
            futures = [pool.submit(download_one, e, staging) for e in new_songs]

            for future in as_completed(futures):
                vid, song_title = future.result()
                done += 1

                eta = (time.time() - dl_start) / done * (len(new_songs) - done)

                if song_title:
                    downloaded += 1
                    temp_name = f"~{vid}.mp3"
                    shutil.move(os.path.join(staging, f"{vid}.mp3"),
                                os.path.join(playlist_dir, temp_name))
                    state[vid] = {'name': sanitize_filename(song_title),
                                  'file': temp_name}
                    print(f"[{done}/{len(new_songs)}] {song_title}   (ETA {format_time(eta)})")
                else:
                    failed += 1
                    print(f"[{done}/{len(new_songs)}] FAILED ({vid})   (ETA {format_time(eta)})")

        shutil.rmtree(staging, ignore_errors=True)
        save_json(state_path, state)

        if failed:
            print(f"\n{failed} songs failed. Run again to retry them.")

    # ---- 3. renumber everything: 001 is the newest song (top of the playlist),
    #         and numbers increase going down toward the oldest song
    order = [e['id'] for e in entries if e['id'] in state]
    changed = renumber(playlist_dir, state, order)
    tag_songs(playlist_dir, state, order)
    save_json(state_path, state)

    print(f"\nRenumbered {changed} files. {len(order)} songs in total.")
    print(f"Saved in: {playlist_dir}")
    
    show_summary(title, downloaded, failed, len(removed), len(order),
                 time.time() - start_time, playlist_dir)


# ------------------------------------------------------------------ main

if __name__ == "__main__":

    print("\n===== YouTube Music Downloader (MP3) =====")
    print("1. Download Single Song")
    print("2. Download / Sync Playlist")

    choice = input("\nSelect Option (1/2): ").strip()

    url = input("Enter URL: ").strip()

    save_link_to_txt(url)

    if choice == "1":
        download_single_video(url)

    elif choice == "2":
        sync_playlist(url)

    else:
        print("Invalid Choice")
