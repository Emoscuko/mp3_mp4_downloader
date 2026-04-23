from __future__ import annotations

import glob
import os
import re
import shutil
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

import yt_dlp

MODE_AUDIO = "audio"
MODE_VIDEO = "video"
MODE_TRANSCRIPT = "transcript"

VIDEO_QUALITIES = ("En Yüksek", "2160p", "1440p", "1080p", "720p", "480p", "360p")
AUDIO_QUALITIES = ("En Yüksek", "320 kbps", "192 kbps", "128 kbps")
TRANSCRIPT_QUALITIES = ("Otomatik",)

PREFERRED_TRANSCRIPT_LANGS = [
    "tr",
    "tr-TR",
    "tr-orig",
    "en",
    "en-US",
    "en-orig",
]

APP_BG = "#141414"
SURFACE = "#202124"
SURFACE_DARK = "#171717"
SURFACE_LIGHT = "#2b2c2f"
TEXT = "#f4f4f5"
MUTED = "#a1a1aa"
ACCENT = "#2dd4bf"
ACCENT_DARK = "#0f766e"
ERROR = "#ef4444"


class UnsupportedPlatformError(ValueError):
    pass


class UnsupportedModeError(ValueError):
    pass


@dataclass(frozen=True)
class PlatformStrategy:
    key: str
    display_name: str
    hosts: tuple[str, ...]
    badge_color: str
    transcript_enabled: bool = False

    def matches_host(self, host: str) -> bool:
        return any(host == allowed or host.endswith(f".{allowed}") for allowed in self.hosts)

    def supported_modes(self) -> tuple[str, ...]:
        modes = [MODE_AUDIO, MODE_VIDEO]
        if self.transcript_enabled:
            modes.append(MODE_TRANSCRIPT)
        return tuple(modes)

    def supports_mode(self, mode: str) -> bool:
        return mode in self.supported_modes()

    def quality_options(self, mode: str) -> tuple[str, ...]:
        if mode == MODE_AUDIO:
            return AUDIO_QUALITIES
        if mode == MODE_VIDEO:
            return VIDEO_QUALITIES
        if mode == MODE_TRANSCRIPT and self.transcript_enabled:
            return TRANSCRIPT_QUALITIES
        return ()

    def build_options(self, folder: str, mode: str, quality: str, progress_hook=None):
        if not self.supports_mode(mode):
            raise UnsupportedModeError(f"{self.display_name} için bu işlem desteklenmiyor.")
        return build_download_options(folder, mode, quality, progress_hook)


class YouTubeStrategy(PlatformStrategy):
    def __init__(self):
        super().__init__(
            key="youtube",
            display_name="YouTube",
            hosts=("youtube.com", "youtu.be"),
            badge_color="#ff4d4d",
            transcript_enabled=True,
        )


class InstagramStrategy(PlatformStrategy):
    def __init__(self):
        super().__init__(
            key="instagram",
            display_name="Instagram",
            hosts=("instagram.com",),
            badge_color="#e4405f",
        )


class TikTokStrategy(PlatformStrategy):
    def __init__(self):
        super().__init__(
            key="tiktok",
            display_name="TikTok",
            hosts=("tiktok.com", "vm.tiktok.com", "vt.tiktok.com"),
            badge_color="#25f4ee",
        )


PLATFORM_STRATEGIES = (YouTubeStrategy(), InstagramStrategy(), TikTokStrategy())


def normalize_url(url: str) -> str:
    value = url.strip()
    if value and "://" not in value:
        return f"https://{value}"
    return value


def extract_host(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    return (parsed.hostname or "").lower().strip(".")


def detect_platform(url: str) -> PlatformStrategy | None:
    host = extract_host(url)
    if not host:
        return None

    for strategy in PLATFORM_STRATEGIES:
        if strategy.matches_host(host):
            return strategy
    return None


def check_ffmpeg():
    """Return True if ffmpeg is available on the system path."""
    return shutil.which("ffmpeg") is not None


def build_common_options(folder: str, progress_hook=None) -> dict:
    options = {
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "windowsfilenames": True,
    }
    if progress_hook:
        options["progress_hooks"] = [progress_hook]
    return options


def build_video_options(quality: str) -> dict:
    if quality not in VIDEO_QUALITIES:
        raise ValueError(f"Desteklenmeyen video kalitesi: {quality}")

    options = {
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
    }
    if quality != "En Yüksek":
        resolution = quality.replace("p", "")
        options["format_sort"] = [f"res:{resolution}", "fps", "br"]
    return options


def build_audio_options(quality: str) -> dict:
    bitrate_by_quality = {
        "En Yüksek": "0",
        "320 kbps": "320",
        "192 kbps": "192",
        "128 kbps": "128",
    }
    if quality not in bitrate_by_quality:
        raise ValueError(f"Desteklenmeyen audio kalitesi: {quality}")

    return {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate_by_quality[quality],
            }
        ],
    }


def build_download_options(folder: str, mode: str, quality: str, progress_hook=None) -> dict:
    options = build_common_options(folder, progress_hook)
    if mode == MODE_VIDEO:
        options.update(build_video_options(quality))
    elif mode == MODE_AUDIO:
        options.update(build_audio_options(quality))
    else:
        raise UnsupportedModeError("Bu işlem medya indirme seçenekleriyle çalışmaz.")
    return options


def download_media(url, folder, strategy, selected_mode, selected_quality, progress_hook=None):
    if not strategy:
        raise UnsupportedPlatformError("Bu link desteklenen platformlardan birine ait değil.")
    if not strategy.supports_mode(selected_mode):
        raise UnsupportedModeError(f"{strategy.display_name} için bu işlem desteklenmiyor.")

    options = strategy.build_options(folder, selected_mode, selected_quality, progress_hook)
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([normalize_url(url)])


def pick_transcript_language(track_map):
    if not track_map:
        return None

    available = list(track_map.keys())
    for lang in PREFERRED_TRANSCRIPT_LANGS:
        if lang in available:
            return lang

    for preferred_base in ("tr", "en"):
        for lang in available:
            normalized = lang.lower().replace("_", "-")
            if normalized == preferred_base or normalized.startswith(f"{preferred_base}-"):
                return lang

    return available[0]


def find_downloaded_subtitle(base_path, language):
    patterns = [
        f"{base_path}.{language}*.vtt",
        f"{base_path}*.vtt",
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[0]
    return None


def convert_vtt_to_text(vtt_path, txt_path):
    lines = []
    with open(vtt_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if (
                not line
                or line == "WEBVTT"
                or line.startswith("NOTE")
                or "-->" in line
                or line.isdigit()
            ):
                continue

            clean = re.sub(r"<[^>]+>", "", line)
            clean = clean.replace("&nbsp;", " ").strip()
            if clean and (not lines or lines[-1] != clean):
                lines.append(clean)

    with open(txt_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def download_transcript(url, folder, status_callback=None):
    notify = status_callback or (lambda _text: None)
    notify("Altyazı bilgisi okunuyor...")

    extract_options = {
        "skip_download": True,
        "quiet": True,
        "noplaylist": True,
        "windowsfilenames": True,
    }
    with yt_dlp.YoutubeDL(extract_options) as ydl:
        info = ydl.extract_info(normalize_url(url), download=False)

    manual_language = pick_transcript_language(info.get("subtitles"))
    automatic_language = None
    if not manual_language:
        automatic_language = pick_transcript_language(info.get("automatic_captions"))
    chosen_language = manual_language or automatic_language

    if not chosen_language:
        raise RuntimeError(
            "Bu videoda kullanılabilir altyazı bulunamadı. "
            "Alternatif olarak videoyu/MP3'ü indirip Whisper ile metne çevirebiliriz."
        )

    options = {
        "skip_download": True,
        "quiet": True,
        "noplaylist": True,
        "windowsfilenames": True,
        "writesubtitles": bool(manual_language),
        "writeautomaticsub": not bool(manual_language),
        "subtitleslangs": [chosen_language],
        "subtitlesformat": "vtt",
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([normalize_url(url)])
        prepared_name = ydl.prepare_filename(info)

    base_path = os.path.splitext(prepared_name)[0]
    vtt_path = find_downloaded_subtitle(base_path, chosen_language)
    if not vtt_path:
        raise RuntimeError("Altyazı dosyası indirildi ama bulunamadı.")

    transcript_path = f"{base_path}.transcript.txt"
    convert_vtt_to_text(vtt_path, transcript_path)
    source_name = "elle eklenmiş altyazı" if manual_language else "otomatik altyazı"
    return transcript_path, source_name, chosen_language


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi Platform Media Downloader")
        self.root.geometry("740x560")
        self.root.minsize(700, 520)
        self.root.configure(bg=APP_BG)

        self.busy = False
        self.current_platform = None
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value=MODE_AUDIO)
        self.quality_var = tk.StringVar(value=AUDIO_QUALITIES[0])
        self.folder_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.mode_buttons = {}

        self.configure_styles()
        self.build_layout()

        self.url_var.trace_add("write", self.update_platform_state)
        self.mode_var.trace_add("write", self.update_quality_state)
        self.update_platform_state()

    def configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Modern.TCombobox",
            fieldbackground=SURFACE_DARK,
            background=SURFACE_DARK,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=SURFACE_LIGHT,
            lightcolor=SURFACE_DARK,
            darkcolor=SURFACE_DARK,
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", SURFACE_DARK), ("disabled", SURFACE)],
            foreground=[("readonly", TEXT), ("disabled", MUTED)],
            selectbackground=[("readonly", SURFACE_DARK)],
            selectforeground=[("readonly", TEXT)],
        )
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=SURFACE_DARK,
            background=ACCENT,
            bordercolor=SURFACE_DARK,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )

    def build_layout(self):
        container = tk.Frame(self.root, bg=APP_BG, padx=28, pady=24)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        header = tk.Frame(container, bg=APP_BG)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="Multi Platform Media Downloader",
            font=("Arial", 22, "bold"),
            bg=APP_BG,
            fg=TEXT,
        ).grid(row=0, column=0, sticky="w")

        self.platform_badge = tk.Label(
            header,
            text="Link bekleniyor",
            font=("Arial", 10, "bold"),
            bg=SURFACE_LIGHT,
            fg=TEXT,
            padx=12,
            pady=6,
        )
        self.platform_badge.grid(row=0, column=1, sticky="e", padx=(16, 0))

        tk.Label(
            container,
            text="YouTube, Instagram veya TikTok linkini yapıştır.",
            font=("Arial", 11),
            bg=APP_BG,
            fg=MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(6, 22))

        self.add_label(container, "Medya Linki").grid(row=2, column=0, sticky="w")
        self.url_entry = tk.Entry(
            container,
            textvariable=self.url_var,
            font=("Arial", 13),
            bg=SURFACE_DARK,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=2,
            highlightbackground=SURFACE_LIGHT,
            highlightcolor=ACCENT,
        )
        self.url_entry.grid(row=3, column=0, sticky="ew", pady=(8, 18), ipady=10)

        options_row = tk.Frame(container, bg=APP_BG)
        options_row.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        options_row.columnconfigure(0, weight=1)
        options_row.columnconfigure(1, weight=1)

        mode_group = tk.Frame(options_row, bg=APP_BG)
        mode_group.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        mode_group.columnconfigure(0, weight=1)

        self.add_label(mode_group, "İşlem").grid(row=0, column=0, sticky="w")
        mode_buttons_frame = tk.Frame(mode_group, bg=APP_BG)
        mode_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        for index, (mode, label) in enumerate(
            ((MODE_AUDIO, "MP3"), (MODE_VIDEO, "MP4"), (MODE_TRANSCRIPT, "Transcript"))
        ):
            button = tk.Radiobutton(
                mode_buttons_frame,
                text=label,
                variable=self.mode_var,
                value=mode,
                indicatoron=False,
                relief="flat",
                bd=0,
                padx=18,
                pady=10,
                font=("Arial", 11, "bold"),
                bg=SURFACE_LIGHT,
                fg=TEXT,
                activebackground=ACCENT_DARK,
                activeforeground=TEXT,
                selectcolor=ACCENT_DARK,
            )
            button.grid(row=0, column=index, sticky="ew", padx=(0, 8))
            mode_buttons_frame.columnconfigure(index, weight=1)
            self.mode_buttons[mode] = button

        quality_group = tk.Frame(options_row, bg=APP_BG)
        quality_group.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        quality_group.columnconfigure(0, weight=1)

        self.quality_label = self.add_label(quality_group, "Kalite")
        self.quality_label.grid(row=0, column=0, sticky="w")
        self.quality_combo = ttk.Combobox(
            quality_group,
            textvariable=self.quality_var,
            values=AUDIO_QUALITIES,
            state="readonly",
            style="Modern.TCombobox",
            font=("Arial", 11),
        )
        self.quality_combo.grid(row=1, column=0, sticky="ew", pady=(8, 0), ipady=6)

        self.quality_note = tk.Label(
            container,
            text="MP3 için kaynak kalitesine en yakın çıktı seçilir.",
            font=("Arial", 10),
            bg=APP_BG,
            fg=MUTED,
        )
        self.quality_note.grid(row=5, column=0, sticky="w", pady=(0, 18))

        self.add_label(container, "Kaydetme Klasörü").grid(row=6, column=0, sticky="w")
        folder_row = tk.Frame(container, bg=APP_BG)
        folder_row.grid(row=7, column=0, sticky="ew", pady=(8, 18))
        folder_row.columnconfigure(0, weight=1)

        self.folder_entry = tk.Entry(
            folder_row,
            textvariable=self.folder_var,
            font=("Arial", 11),
            bg=SURFACE_DARK,
            fg=TEXT,
            readonlybackground=SURFACE_DARK,
            relief="flat",
            highlightthickness=2,
            highlightbackground=SURFACE_LIGHT,
            highlightcolor=ACCENT,
            state="readonly",
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew", ipady=9)

        self.folder_button = tk.Button(
            folder_row,
            text="Seç",
            bg=SURFACE_LIGHT,
            fg=TEXT,
            activebackground=ACCENT_DARK,
            activeforeground=TEXT,
            relief="flat",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=9,
            command=self.choose_folder,
        )
        self.folder_button.grid(row=0, column=1, padx=(10, 0))

        self.download_button = tk.Button(
            container,
            text="MP3 İndir",
            bg=ACCENT_DARK,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="#0f172a",
            disabledforeground=MUTED,
            relief="flat",
            font=("Arial", 12, "bold"),
            padx=18,
            pady=13,
            command=self.start_download,
        )
        self.download_button.grid(row=8, column=0, sticky="ew", pady=(0, 18))

        self.progress_bar = ttk.Progressbar(
            container,
            orient="horizontal",
            mode="determinate",
            style="Modern.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=9, column=0, sticky="ew")

        self.status_label = tk.Label(
            container,
            text="Hazır.",
            font=("Arial", 10),
            bg=APP_BG,
            fg=MUTED,
        )
        self.status_label.grid(row=10, column=0, sticky="w", pady=(12, 0))

    def add_label(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=APP_BG,
            fg=TEXT,
        )

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~"))
        if folder:
            self.folder_var.set(folder)
        self.update_download_state()

    def update_platform_state(self, *_args):
        url = self.url_var.get().strip()
        self.current_platform = detect_platform(url)

        if not url:
            self.set_badge("Link bekleniyor", SURFACE_LIGHT)
            if not self.busy:
                self.set_status("Hazır.")
        elif self.current_platform:
            self.set_badge(self.current_platform.display_name, self.current_platform.badge_color)
            if not self.busy:
                self.set_status(f"{self.current_platform.display_name} linki algılandı.")
        else:
            self.set_badge("Desteklenmiyor", ERROR)
            if not self.busy:
                self.set_status("Yalnızca YouTube, Instagram ve TikTok linkleri destekleniyor.")

        if self.current_platform and not self.current_platform.supports_mode(self.mode_var.get()):
            self.mode_var.set(MODE_AUDIO)
        elif not self.current_platform and self.mode_var.get() == MODE_TRANSCRIPT:
            self.mode_var.set(MODE_AUDIO)

        self.update_quality_state()
        self.update_download_state()

    def update_quality_state(self, *_args):
        mode = self.mode_var.get()
        strategy = self.current_platform

        if strategy and not strategy.supports_mode(mode):
            mode = MODE_AUDIO
            self.mode_var.set(mode)

        qualities = AUDIO_QUALITIES
        quality_state = "readonly"
        note = "MP3 için kaynak kalitesine en yakın çıktı seçilir."
        quality_title = "Audio Kalitesi"

        if mode == MODE_VIDEO:
            qualities = VIDEO_QUALITIES
            note = "Varsayılan seçenek platformdaki en yüksek uygun kaliteyi indirir."
            quality_title = "Video Kalitesi"
        elif mode == MODE_TRANSCRIPT:
            qualities = TRANSCRIPT_QUALITIES
            quality_state = "disabled"
            note = "Transcript yalnızca YouTube altyazıları veya otomatik altyazılarıyla çalışır."
            quality_title = "Transcript"

        self.quality_label.config(text=quality_title)
        effective_quality_state = "disabled" if self.busy else quality_state
        self.quality_combo.configure(values=qualities, state=effective_quality_state)
        if self.quality_var.get() not in qualities:
            self.quality_var.set(qualities[0])
        self.quality_note.config(text=note)

        self.refresh_mode_buttons()
        self.update_button_text()
        self.update_download_state()

    def refresh_mode_buttons(self):
        for mode, button in self.mode_buttons.items():
            supported = self.current_platform.supports_mode(mode) if self.current_platform else mode != MODE_TRANSCRIPT
            selected = self.mode_var.get() == mode
            if not supported or self.busy:
                button.config(state="disabled", bg=SURFACE, fg=MUTED, disabledforeground=MUTED)
            elif selected:
                button.config(state="normal", bg=ACCENT_DARK, fg=TEXT)
            else:
                button.config(state="normal", bg=SURFACE_LIGHT, fg=TEXT)

    def update_button_text(self):
        messages = {
            MODE_AUDIO: "MP3 İndir",
            MODE_VIDEO: "MP4 İndir",
            MODE_TRANSCRIPT: "Transcript Al",
        }
        self.download_button.config(text=messages.get(self.mode_var.get(), "İndir"))

    def update_download_state(self):
        can_download = (
            not self.busy
            and bool(self.url_var.get().strip())
            and self.current_platform is not None
            and self.current_platform.supports_mode(self.mode_var.get())
            and bool(self.folder_var.get().strip())
        )
        self.download_button.config(state="normal" if can_download else "disabled")

    def set_badge(self, text, bg):
        fg = "#101010" if bg == "#25f4ee" else TEXT
        self.platform_badge.config(text=text, bg=bg, fg=fg)

    def set_status(self, text):
        self.status_label.config(text=text)

    def set_progress(self, value):
        self.progress_bar["value"] = value

    def run_on_ui(self, callback, *args, **kwargs):
        self.root.after(0, lambda: callback(*args, **kwargs))

    def set_busy(self, is_busy):
        self.busy = is_busy
        base_state = "disabled" if is_busy else "normal"
        self.url_entry.config(state=base_state)
        self.folder_button.config(state=base_state)
        self.folder_entry.config(state="disabled" if is_busy else "readonly")
        self.refresh_mode_buttons()
        self.update_quality_state()
        self.update_download_state()

    def make_progress_hook(self):
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")

        def progress_hook(data):
            status = data.get("status")
            if status == "downloading":
                percent = data.get("_percent_str", "0%")
                display_percent = ansi_pattern.sub("", percent).strip()
                clean_percent = display_percent.replace("%", "").strip()
                speed = data.get("_speed_str", "Bilinmiyor")
                try:
                    self.run_on_ui(self.set_progress, float(clean_percent))
                except (TypeError, ValueError):
                    total = data.get("total_bytes") or data.get("total_bytes_estimate")
                    downloaded = data.get("downloaded_bytes")
                    if total and downloaded:
                        self.run_on_ui(self.set_progress, downloaded / total * 100)
                self.run_on_ui(self.set_status, f"İndiriliyor: {display_percent} - Hız: {speed}")
            elif status == "finished":
                self.run_on_ui(self.set_status, "İşlem tamamlanıyor... Lütfen bekleyin.")

        return progress_hook

    def start_download(self):
        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()
        mode = self.mode_var.get()
        quality = self.quality_var.get()
        strategy = detect_platform(url)

        if not url:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir link girin.")
            return

        if not strategy:
            messagebox.showerror("Desteklenmeyen Link", "Yalnızca YouTube, Instagram ve TikTok linkleri destekleniyor.")
            return

        if not strategy.supports_mode(mode):
            messagebox.showerror("Desteklenmeyen İşlem", f"{strategy.display_name} için bu işlem desteklenmiyor.")
            return

        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Eksik Bilgi", "Lütfen geçerli bir kaydetme klasörü seçin.")
            return

        if mode in {MODE_AUDIO, MODE_VIDEO} and not check_ffmpeg():
            messagebox.showerror(
                "Eksik Yazılım",
                "FFmpeg bilgisayarınızda bulunamadı.\n\n"
                "MP3 dönüştürme ve MP4 birleştirme için FFmpeg gereklidir. "
                "macOS'ta `brew install ffmpeg` ile yükleyebilirsiniz.",
            )
            return

        self.current_platform = strategy
        self.set_busy(True)
        self.set_progress(0)
        self.set_status("İşlem başlatılıyor...")

        def worker():
            try:
                if mode == MODE_TRANSCRIPT:
                    transcript_path, source_name, language = download_transcript(
                        url,
                        folder,
                        status_callback=lambda text: self.run_on_ui(self.set_status, text),
                    )
                    self.run_on_ui(self.set_progress, 100)
                    self.run_on_ui(self.set_status, f"Transcript hazır: {os.path.basename(transcript_path)}")
                    self.run_on_ui(
                        messagebox.showinfo,
                        "Transcript Hazır",
                        "Transcript başarıyla alındı.\n\n"
                        f"Kaynak: {source_name}\n"
                        f"Dil: {language}\n"
                        f"Dosya: {transcript_path}",
                    )
                else:
                    download_media(url, folder, strategy, mode, quality, self.make_progress_hook())
                    self.run_on_ui(self.set_progress, 100)
                    self.run_on_ui(self.set_status, "Hazır.")
                    self.run_on_ui(messagebox.showinfo, "Başarılı", "İşlem tamamlandı.")
            except Exception as exc:
                self.run_on_ui(messagebox.showerror, "Hata", f"Hata: {exc}")
                self.run_on_ui(self.set_status, "Bir hata oluştu.")
            finally:
                self.run_on_ui(self.set_busy, False)

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
