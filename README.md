# 🧰 MINI-PROJECTS

A collection of small, practical Python tools I built for my own daily use: downloading YouTube music and playlists, and keeping song files numbered in order.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red)
![Status](https://img.shields.io/badge/status-actively%20updated-brightgreen)

---

## 📑 Contents

- [What's inside](#-whats-inside)
- [Music Downloader: version history](#-music-downloader-version-history)
- [Song Name Shifter](#-song-name-shifter)
- [Requirements and setup](#-requirements-and-setup)
- [How to use](#-how-to-use)
- [Disclaimer](#-disclaimer)
- [About contributions](#-about-contributions)

---

## 📂 What's inside

| File | What it does | Status |
|------|--------------|--------|
| [`v1.0 MUSIC DOWNLOADER.py`](./v1.0%20MUSIC%20DOWNLOADER.py) | First version. Downloads a video or a whole playlist as MP4 | Legacy |
| [`v2.0 MUSIC DOWNLOADER.py`](./v2.0%20MUSIC%20DOWNLOADER.py) | Menu loop, timestamped link history, playlist folders named after the playlist | Legacy |
| [`v3.0 MUSIC DOWNLOADER.py`](./v3.0%20MUSIC%20DOWNLOADER.py) | **Audio-only MP3**, artist tags, cover art, parallel playlist downloads | ✅ Stable |
| [`v4.0 MUSIC DOWNLOADER.py`](./v4.0%20MUSIC%20DOWNLOADER.py) | Everything in v3, plus **smart playlist sync**: downloads only new songs, deletes removed ones, renumbers automatically | ⭐ Latest |
| [`SONG NAME SHIFTER.py`](./SONG%20NAME%20SHIFTER.py) | Safely shifts the numbers in `001 - Song Name` style filenames | ✅ Stable |

---

## 🎵 Music Downloader: version history

All versions save to a local folder (`D:\Youtube_Downs` by default) and log every URL you enter in `links.txt`.

### v1.0: The beginning
- Menu: single video or playlist.
- Downloads the best video + best audio and merges them into **MP4**.
- Playlist files are numbered `001 - Title.mp4`, in **reversed playlist order** (`::-1`), so numbering follows the order songs were added.
- Playlist folder is named with a timestamp (e.g. `2026-01-31_18-45-10`).

### v2.0: Cleaner and safer
- Menu now **loops** until you choose Exit.
- `links.txt` entries now include a **timestamp and type** (`SINGLE` / `PLAYLIST`).
- Playlist folder is named after the **real playlist title**, with Windows-illegal characters cleaned.
- Existing files are never overwritten (`nooverwrites`), and single-video mode ignores the rest of a playlist link.
- Friendly success and error messages.
- Reverse ordering is commented out, so files are numbered in playlist order.

### v3.0: Fast MP3s ⚡
Built for people who only want the music.

- **Audio only.** No video download and no video + audio merge, which is where most of the time went.
- **MP3 at 192 kbps**, which matches YouTube's own audio quality.
- **Artist and title tags** embedded in every file (falls back to the channel name if there is no artist).
- **Square cover art** embedded from the thumbnail, so songs look right in any music app.
- **Parallel downloads**: 3 songs at once in playlists, 4 fragments at once per song.
- Same naming as before: `001 - Song Title.mp3`.

### v4.0: Smart playlist sync 🔄
Everything from v3, plus a playlist option that **syncs your folder with the online playlist** instead of downloading everything again.

| Situation | What v4.0 does |
|-----------|----------------|
| Playlist never downloaded | Downloads every song and numbers them |
| Some songs already downloaded | Downloads **only the new ones** |
| Songs removed from the playlist online | Lists them and asks: **delete** or **move to `_removed`** |
| Songs added or removed | **Renumbers everything** so the order has no gaps |
| Download failed | Run again and only the missing songs are retried |
| File deleted by hand | Downloaded again on the next sync |
| Private or deleted videos in a playlist | Skipped, and your local copy is kept |

**How it keeps track:** each song is remembered by its YouTube video ID in a small `sync_state.json` file inside the playlist folder, and `playlists.json` in the main folder remembers which folder belongs to which playlist. Because of this, renaming and renumbering never confuse it.

**Already have a folder from an older version?** On the first sync, enter that folder's name when asked. v4.0 matches your existing files to the playlist by song name, so nothing is downloaded twice.

**Safety:** if the playlist can't be read or comes back empty, nothing is deleted or changed. A file is never overwritten during renumbering.

**Numbering order:** the playlist is reversed, so the song at the bottom of the YouTube playlist gets `001`.

---

## 🔢 Song Name Shifter

`SONG NAME SHIFTER.py` is a safe bulk-renamer for files named like `12 - Song Name.mp3`.

Use it when you merge folders or add songs and need to push all the numbers up by a fixed amount.

- Asks for **how much to increase** the numbers by and the **folder location**.
- Shows a **full preview** (`old name -> new name`) before touching anything.
- Checks for **duplicate or conflicting names** first and stops if there is any problem.
- Needs your **confirmation** (`y/N`) before changing files.
- Moves files through a temporary folder, verifies that every file arrived, then moves them back. It **never overwrites** a file silently.
- If anything fails, it stops and tells you where your files are.

> 💡 For YouTube playlists, **v4.0** renumbers automatically. The Shifter is still useful for any folder of numbered files.

---

## ⚙️ Requirements and setup

**You need:**

- **Python 3.10 or newer**
- **yt-dlp**
- **ffmpeg** (for MP3 conversion, tags and cover art)

**Install:**

```bash
pip install -U yt-dlp
```

Install ffmpeg:

- Windows: `winget install ffmpeg` (or download it from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to PATH)
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

Check it works:

```bash
ffmpeg -version
```

**Change the save folder:** open the script and edit this line near the top:

```python
BASE_DIR = r'D:\Youtube_Downs'
```

> 🔁 Keep yt-dlp up to date (`pip install -U yt-dlp`). YouTube changes often and old versions stop working.

---

## ▶️ How to use

1. Clone or download this repo.
2. Open a terminal in the folder.
3. Run the version you want:

```bash
python "v4.0 MUSIC DOWNLOADER.py"
```

4. Choose an option:
   - `1` for a single song
   - `2` for a playlist (v4.0 syncs it; run it again later to pick up new songs)
5. Paste the URL and wait for the download.

**Example output (v4.0):**

```text
Playlist : My Favourites
Online   : 148 songs
On device: 131 already downloaded
New      : 17 to download
Removed  : 0 no longer in the playlist
```

**Notes:**

- Private playlists can't be read without your browser cookies. Public and unlisted playlists work as they are.
- Tracks that already exist are skipped, so it is safe to re-run.

---

## ⚠️ Disclaimer

These tools are for **personal use**. Only download content you own, have a licence for, or are otherwise allowed to save. Downloading content from YouTube may violate its Terms of Service, and you are responsible for how you use these scripts. They are not affiliated with YouTube or Google.

---

## 🔒 About contributions

This repository is public so you can **read, learn from and use** the code. It is maintained by me alone, so pull requests may not be reviewed or merged. Feel free to **fork** it and make it your own.

---

<p align="center">Made with ❤️ and Python by <a href="https://github.com/HARSH17m">HARSH17m</a></p>
