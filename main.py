import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import yt_dlp
import threading

def progress_hook(d):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace('%','')
        try:
            progress_bar['value'] = float(p)
            status_label.config(text=f"İndiriliyor: {d.get('_percent_str')} - Hız: {d.get('_speed_str')}")
        except:
            pass
    elif d['status'] == 'finished':
        status_label.config(text="İşlem tamamlanıyor... Lütfen bekleyin.")

def indir():
    url = entry_url.get()
    format_secimi = secim.get()
    kalite_secimi = combo_kalite.get()
    
    if not url:
        messagebox.showwarning("Hata", "Lütfen bir link girin!")
        return

    klasor = filedialog.askdirectory()
    if not klasor: return

    btn_indir.config(state="disabled")
    progress_bar['value'] = 0
    
    def download_thread():
        try:
            # Kalite ayarını belirle
            if kalite_secimi == "En Yüksek":
                video_format = "bestvideo+bestaudio/best"
            else:
                # Seçilen çözünürlüğü ve altındakileri ara
                res = kalite_secimi.replace("p", "")
                video_format = f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"

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
                common_opts.update({'format': video_format})

            with yt_dlp.YoutubeDL(common_opts) as ydl:
                ydl.download([url])
            
            messagebox.showinfo("Başarılı", "İşlem tamamlandı!")
            status_label.config(text="Hazır.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hata: {str(e)}")
        finally:
            btn_indir.config(state="normal")

    threading.Thread(target=download_thread).start()

# --- Arayüz ---
root = tk.Tk()
root.title("YouTube Downloader Ultra")
root.geometry("500x400")

tk.Label(root, text="YouTube URL:", font=("Arial", 10, "bold")).pack(pady=10)
entry_url = tk.Entry(root, width=60)
entry_url.pack(pady=5)

# Format ve Kalite Çerçevesi
frame_options = tk.Frame(root)
frame_options.pack(pady=10)

# Format Seçimi
secim = tk.StringVar(value="mp3")
tk.Radiobutton(frame_options, text="MP3", variable=secim, value="mp3").grid(row=0, column=0, padx=20)
tk.Radiobutton(frame_options, text="MP4", variable=secim, value="mp4").grid(row=0, column=1, padx=20)

# Kalite Seçimi (Dropdown)
tk.Label(root, text="Video Kalitesi (Sadece MP4 için):").pack()
combo_kalite = ttk.Combobox(root, values=["360p", "480p", "720p", "1080p", "En Yüksek"], state="readonly")
combo_kalite.set("1080p")
combo_kalite.pack(pady=5)

btn_indir = tk.Button(root, text="İNDİRMEYİ BAŞLAT", bg="#c4302b", fg="white", font=("Arial", 12, "bold"), width=25, command=indir)
btn_indir.pack(pady=20)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Bekleniyor...", fg="gray")
status_label.pack()

root.mainloop()