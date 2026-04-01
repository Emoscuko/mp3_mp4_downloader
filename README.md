# YouTube Downloader Ultra

A lightweight, multi-format YouTube downloader built with Python and Tkinter, powered by `yt-dlp`.

## Features
- Download as **MP3** (Automatic audio extraction)
- Download as **MP4** (Selectable qualities from 360p to 1080p and "Best")
- Real-time progress bar and status updates
- Simple and modern UI

## Prerequisites & Installation

The application requires **Python 3.x**, **Tkinter**, and **FFmpeg**.

### 🍏 macOS (Homebrew)
Install the dependencies using [Homebrew](https://brew.sh/):
```bash
brew install python-tk@3.14
brew install ffmpeg
```

### 🪟 Windows
1.  **Python:** Download and install from [python.org](https://www.python.org/). During installation, ensure you check **"Add Python to PATH"** and **"tcl/tk and IDLE"**.
2.  **FFmpeg:**
    - Download the "essentials" build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
    - Extract the folder, and add the `bin` directory (e.g., `C:\ffmpeg\bin`) to your **System Environment Variables (PATH)**.
    - Verify with `ffmpeg -version` in PowerShell/CMD.

### 🐧 Linux (Debian/Ubuntu)
Install the dependencies via your package manager:
```bash
sudo apt update
sudo apt install python3-tk ffmpeg
```
*(For Fedora, use `sudo dnf install python3-tkinter ffmpeg`)*

---

## Setup & Running (All Platforms)

1. **Clone or download the project**
2. **Create and activate a virtual environment:**
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install Python requirements:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```bash
   python main.py
   ```

## Dependencies
- `yt-dlp` - For downloading and processing YouTube content.
- `tkinter` - For the graphical user interface.
- `ffmpeg` - For media conversion and merging.