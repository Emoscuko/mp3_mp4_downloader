# Multi Platform Media Downloader

A lightweight desktop downloader for YouTube, Instagram, and TikTok links, built with Python, Tkinter, and `yt-dlp`.

## Features
- Detects **YouTube**, **Instagram**, and **TikTok** links automatically.
- Downloads **MP3 audio** with selectable output quality.
- Downloads **MP4 video** with selectable resolution from 360p up to 2160p, plus **En Yüksek** for the best available quality.
- Exports **YouTube transcripts** as `.txt` using manual subtitles first, then automatic captions.
- Shows a platform badge, save folder selector, progress bar, and live status updates.

## Support Notes
- Only public, non-login content is supported in this version.
- Batch downloads, playlists, private posts, and cookie/login flows are out of scope.
- Instagram and TikTok availability can change when platforms update their pages or APIs. The app surfaces those failures as normal download errors from `yt-dlp`.
- Transcript export is intentionally YouTube-only.

## Prerequisites

The application requires **Python 3.10+**, **Tkinter**, and **FFmpeg**.
FFmpeg is required for MP3 conversion and MP4 merging. Transcript export does not require FFmpeg.

### macOS (Homebrew)
```bash
brew install python-tk@3.14
brew install ffmpeg
```

### Windows
1. Install Python from [python.org](https://www.python.org/). During installation, enable **Add Python to PATH** and **tcl/tk and IDLE**.
2. Install FFmpeg:
   - Download the "essentials" build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
   - Extract it and add the `bin` directory, such as `C:\ffmpeg\bin`, to your system `PATH`.
   - Verify with `ffmpeg -version` in PowerShell or CMD.

### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install python3-tk ffmpeg
```

For Fedora:
```bash
sudo dnf install python3-tkinter ffmpeg
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On macOS, if `python3 --version` shows Apple's Python 3.9, create the venv with Homebrew Python instead:
   ```bash
   deactivate  # only if an old venv is active
   mv .venv .venv-py39-backup  # only if .venv was already created with Python 3.9
   /opt/homebrew/bin/python3.14 -m venv .venv
   source .venv/bin/activate
   ```

2. Install Python requirements:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### One-click launch on macOS

After cloning the project, double-click `Run Downloader.command`.
It prepares `.venv` with Homebrew Python 3.10+, installs requirements when needed, and starts the app.

## Quality Behavior
- **Video / En Yüksek** uses the best video and best audio streams available, merged into MP4 when needed.
- **Video / 2160p-360p** asks `yt-dlp` for the closest suitable resolution at or below the selected target when available.
- **Audio / En Yüksek** extracts the best available audio stream and converts it to MP3 with the highest MP3 setting.
- Lower audio bitrates are available when smaller files matter more than maximum quality.

## Development

Run the unit tests with:
```bash
python -m unittest discover -s tests
```

The test suite covers platform detection, YouTube-only transcript support, and `yt-dlp` option generation for audio and video quality choices.
