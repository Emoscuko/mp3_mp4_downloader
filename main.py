import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import yt_dlp
import threading

def progress_hook(d):
    if d['status'] == 'downloading':
        # Yüzdeyi al ve barı güncelle
        p = d.get('_percent_str', '0%').replace('%','')
        try:
            progress_bar['value'] = float(p)
            status_label.config(text=f"İndiriliyor: {d.get('_percent_str')} - Hız: {d.get('_speed_str')}")
        except:
            pass
    elif d['status'] == 'finished':
        status_label.config(text="Dönüştürülüyor... Lütfen bekleyin.")

def indir():
    url = entry_url.get()
    format_secimi = secim.get()
    
    if not url:
        messagebox.showwarning("Hata", "Lütfen bir link girin!")
        return

    klasor = filedialog.askdirectory()
    if not klasor: return

    btn_indir.config(state="disabled")
    progress_bar['value'] = 0
    
    def download_thread():
        try:
            common_opts = {
                'outtmpl': f'{klasor}/%(title)s.%(ext)s',
                'progress_hooks': [progress_hook],
            }

            if format_secimi == "mp3":
                common_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                })
            else:
                common_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})

            with yt_dlp.YoutubeDL(common_opts) as ydl:
                ydl.download([url])
            
            messagebox.showinfo("Başarılı", "İşlem tamamlandı!")
            status_label.config(text="Hazır.")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
        finally:
            btn_indir.config(state="normal")

    threading.Thread(target=download_thread).start()

# --- UI ---
root = tk.Tk()
root.title("YouTube Downloader Pro")
root.geometry("500x350")

tk.Label(root, text="YouTube URL:", font=("Arial", 10, "bold")).pack(pady=10)
entry_url = tk.Entry(root, width=60)
entry_url.pack(pady=5)

secim = tk.StringVar(value="mp3")
frame_radio = tk.Frame(root)
frame_radio.pack(pady=10)
tk.Radiobutton(frame_radio, text="MP3 (Ses)", variable=secim, value="mp3").pack(side="left", padx=20)
tk.Radiobutton(frame_radio, text="MP4 (Video)", variable=secim, value="mp4").pack(side="left", padx=20)

btn_indir = tk.Button(root, text="İNDİR", bg="#c4302b", fg="white", font=("Arial", 12, "bold"), width=20, command=indir)
btn_indir.pack(pady=20)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Bekleniyor...", fg="gray")
status_label.pack()

root.mainloop()