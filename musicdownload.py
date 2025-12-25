import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import asyncio
import json
import re
import os
import sys
import webbrowser
from pathlib import Path
from PIL import Image, ImageTk
import qrcode
from pycloudmusic import LoginMusic163, Music163Api
from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.easymp4 import EasyMP4
from mutagen.id3 import TIT2, TPE1, TALB, APIC
from mutagen.mp4 import MP4, MP4Cover
import requests
import inspect
import threading


COOKIE_FILE = "cookie.txt"


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MusicDownloadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐下载器")
        self.root.geometry("700x650")

        # Set window icon
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # No icon available, use default

        self.musicapi = None
        self.cookie = None
        self.song_ids = []
        self.json_file_path = None
        self.is_logged_in = False
        self.quality = "mp3"

        self.setup_ui()
        self.check_saved_cookie()

    def setup_ui(self):
        # Login Section
        login_frame = ttk.LabelFrame(self.root, text="登录", padding=10)
        login_frame.pack(fill="x", padx=10, pady=5)

        self.login_status = ttk.Label(login_frame, text="未登录", foreground="red")
        self.login_status.pack(side="left", padx=5)

        self.login_btn = ttk.Button(login_frame, text="扫码登录", command=self.start_qr_login)
        self.login_btn.pack(side="left", padx=5)

        # QR Code Display
        qr_frame = ttk.Frame(self.root)
        qr_frame.pack(padx=10, pady=5)

        self.qr_label = ttk.Label(qr_frame, text="扫码区域")
        self.qr_label.pack()

        # File Selection Section
        file_frame = ttk.LabelFrame(self.root, text="JSON 文件", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(file_frame, text="拖入文件或点击选择:").pack(side="left", padx=5)

        self.file_label = ttk.Label(file_frame, text="未选择文件", foreground="gray")
        self.file_label.pack(side="left", padx=5)

        ttk.Button(file_frame, text="浏览", command=self.browse_json).pack(side="left", padx=5)

        # Song Count Display
        self.song_count_label = ttk.Label(file_frame, text="")
        self.song_count_label.pack(side="left", padx=10)

        # Quality Selection
        quality_frame = ttk.LabelFrame(self.root, text="音质选择", padding=10)
        quality_frame.pack(fill="x", padx=10, pady=5)

        self.quality_var = tk.StringVar(value="auto")
        ttk.Radiobutton(quality_frame, text="Auto (自动)", variable=self.quality_var, value="auto").pack(side="left", padx=10)
        ttk.Radiobutton(quality_frame, text="MP3 (320k)", variable=self.quality_var, value="mp3").pack(side="left", padx=10)
        ttk.Radiobutton(quality_frame, text="FLAC (无损)", variable=self.quality_var, value="flac").pack(side="left", padx=10)

        # Lyrics Download
        lyric_frame = ttk.LabelFrame(self.root, text="歌词", padding=10)
        lyric_frame.pack(fill="x", padx=10, pady=5)

        self.lyric_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(lyric_frame, text="下载歌词 (.lrc)", variable=self.lyric_var).pack(side="left", padx=10)

        # Download Folder
        folder_frame = ttk.LabelFrame(self.root, text="下载目录", padding=10)
        folder_frame.pack(fill="x", padx=10, pady=5)

        self.folder_label = ttk.Label(folder_frame, text="./download", foreground="blue")
        self.folder_label.pack(side="left", padx=5)

        ttk.Button(folder_frame, text="选择目录", command=self.browse_folder).pack(side="left", padx=5)

        self.download_folder = "./download"

        # Download Button
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.download_btn = ttk.Button(btn_frame, text="开始下载", command=self.start_download, state="disabled")
        self.download_btn.pack()

        # Progress Section
        progress_frame = ttk.LabelFrame(self.root, text="下载进度", padding=10)
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)

        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack()

        # Log Display
        log_frame = ttk.LabelFrame(self.root, text="日志", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True)

        # Links (bottom-right)
        links_frame = ttk.Frame(self.root)
        links_frame.pack(fill="x", padx=10, pady=5)
        github_label = tk.Label(links_frame, text="github", fg="blue", cursor="hand2", font=("Arial", 9))
        github_label.pack(side="right", padx=5)
        github_label.bind("<Button-1>", self.open_github)
        listen1_label = tk.Label(links_frame, text="Listen1", fg="blue", cursor="hand2", font=("Arial", 9))
        listen1_label.pack(side="right")
        listen1_label.bind("<Button-1>", self.open_listen1)

    def open_github(self, event):
        webbrowser.open("https://github.com/FunnyEntity/CloudMusicDownload")

    def open_listen1(self, event):
        webbrowser.open("https://listen1.github.io/listen1/")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def check_saved_cookie(self):
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                    self.cookie = f.read().strip()
                self.log("发现已保存的 cookie，尝试登录...")
                self.verify_cookie()
            except Exception as e:
                self.log(f"读取 cookie 失败: {e}")

    def verify_cookie(self):
        async def _verify():
            try:
                api = Music163Api(self.cookie)
                await api.my()
                self.musicapi = api
                self.is_logged_in = True
                self.root.after(0, self.update_login_status, True)
                self.log("Cookie 登录成功!")
            except Exception as e:
                self.root.after(0, self.update_login_status, False)
                self.log(f"Cookie 已失效: {e}")

        asyncio.run(_verify())

    def update_login_status(self, success):
        if success:
            self.login_status.config(text="已登录", foreground="green")
            self.login_btn.config(state="disabled")
            self.check_ready()
        else:
            self.login_status.config(text="登录失败", foreground="red")
            self.login_btn.config(state="normal")

    def start_qr_login(self):
        self.login_btn.config(state="disabled")
        self.log("正在生成二维码...")

        async def _login():
            try:
                login = LoginMusic163()
                qr_key, qr_url = await login.qr_key()

                # Generate QR code image
                qr = qrcode.QRCode()
                qr.add_data(qr_url)
                qr.make()

                # Save to temp file and display
                img = qr.make_image(fill_color="black", back_color="white")
                temp_path = os.path.join(os.getcwd(), "temp_qr.png")
                img.save(temp_path)

                self.root.after(0, self.display_qr, temp_path)
                self.log("请使用网易云音乐 App 扫描二维码...")

                cookie, api = await login.qr(qr_key)
                self.cookie = cookie
                self.musicapi = api
                self.is_logged_in = True

                # Save cookie
                with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                    f.write(cookie)

                self.root.after(0, self.update_login_status, True)
                self.root.after(0, lambda: self.qr_label.config(text="登录成功!"))
                self.log("登录成功!")

                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass

            except Exception as e:
                self.root.after(0, lambda: self.login_btn.config(state="normal"))
                self.log(f"登录失败: {e}")

        threading.Thread(target=lambda: asyncio.run(_login()), daemon=True).start()

    def display_qr(self, image_path):
        try:
            img = Image.open(image_path)
            img = img.resize((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.qr_label.config(image=photo, text="")
            self.qr_label.image = photo
        except Exception as e:
            self.log(f"显示二维码失败: {e}")

    def browse_json(self):
        file_path = filedialog.askopenfilename(
            title="选择 JSON 文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.load_json(file_path)

    def load_json(self, file_path):
        self.json_file_path = file_path
        self.file_label.config(text=os.path.basename(file_path), foreground="black")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.song_ids = []
            if "current-playing" in data:
                for track in data["current-playing"]:
                    if track.get("source") == "netease":
                        source_url = track.get("source_url", "")
                        match = re.search(r"[?&]id=(\d+)", source_url)
                        if match:
                            self.song_ids.append(int(match.group(1)))

            self.song_count_label.config(text=f"共 {len(self.song_ids)} 首歌曲")
            self.log(f"已加载 {len(self.song_ids)} 首歌曲")
            self.check_ready()

        except Exception as e:
            self.log(f"加载 JSON 失败: {e}")
            self.song_count_label.config(text="加载失败")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择下载目录")
        if folder:
            self.download_folder = folder
            self.folder_label.config(text=folder)
            self.log(f"下载目录: {folder}")

    def check_ready(self):
        if self.is_logged_in and self.song_ids:
            self.download_btn.config(state="normal")

    def safe_filename(self, s):
        safe_chars = " -_.()[]{}'!@#$%^&+=`~"
        return "".join(c if c.isalnum() or c in safe_chars else "_" for c in s).strip()

    def get_first_str(self, val):
        if isinstance(val, list):
            for x in val:
                if x and str(x).strip():
                    return str(x).strip()
            return "unknown"
        return str(val).strip() if val else "unknown"

    def get_real_ext(self, filepath):
        try:
            with open(filepath, "rb") as f:
                header = f.read(16)
            if header.startswith(b'fLaC'):
                return '.flac'
            elif header.startswith(b'ID3') or header[:2] == b'\xFF\xFB':
                return '.mp3'
            elif header.startswith(b'RIFF'):
                return '.wav'
            elif b'M4A' in header or b'isom' in header or b'ftyp' in header:
                return '.m4a'
            else:
                return Path(filepath).suffix
        except Exception:
            return None

    def write_tags(self, filepath, ext, title, artist, album):
        try:
            if ext == '.flac':
                audio = FLAC(filepath)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio.save()
            elif ext == '.mp3':
                audio = MP3(filepath)
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.add(TIT2(encoding=3, text=title))
                audio.tags.add(TPE1(encoding=3, text=artist))
                audio.tags.add(TALB(encoding=3, text=album))
                audio.save()
            elif ext == '.m4a':
                audio = EasyMP4(filepath)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio.save()
        except Exception:
            pass

    def download_cover(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None

    def write_cover(self, filepath, ext, cover_data):
        try:
            if not cover_data:
                return
            if ext == '.flac':
                audio = FLAC(filepath)
                pic = Picture()
                pic.data = cover_data
                pic.type = 3
                pic.mime = "image/jpeg"
                audio.clear_pictures()
                audio.add_picture(pic)
                audio.save()
            elif ext == '.mp3':
                audio = MP3(filepath)
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.version = (2, 3, 0)
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=cover_data
                    )
                )
                audio.save(v2_version=3)
            elif ext == '.m4a':
                audio = MP4(filepath)
                audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()
        except Exception:
            pass

    async def download_lyric(self, music, final_path):
        """Download lyrics for a song and save as .lrc file"""
        try:
            lyric = None
            if hasattr(music, "lyric"):
                if callable(music.lyric):
                    result = music.lyric()
                    if inspect.isawaitable(result):
                        lyric = await result
                    else:
                        lyric = result
                else:
                    lyric = music.lyric

            # Parse lyric data structure
            if isinstance(lyric, dict):
                if "lrc" in lyric and isinstance(lyric["lrc"], dict) and "lyric" in lyric["lrc"]:
                    lyric = lyric["lrc"]["lyric"]
                elif "lyric" in lyric:
                    lyric = lyric["lyric"]
                elif "lrc" in lyric:
                    lyric = lyric["lrc"]
                elif "tlyric" in lyric and isinstance(lyric["tlyric"], dict) and "lyric" in lyric["tlyric"]:
                    lyric = lyric["tlyric"]["lyric"]
                else:
                    lyric = ""

            # Write to .lrc file
            if isinstance(lyric, str) and lyric.strip():
                lrc_path = os.path.splitext(final_path)[0] + ".lrc"
                with open(lrc_path, "w", encoding="utf-8") as f:
                    f.write(lyric)
                return True, os.path.basename(lrc_path)
            return False, None
        except Exception as e:
            return False, str(e)

    def start_download(self):
        self.download_btn.config(state="disabled")
        self.quality = self.quality_var.get()

        async def _download():
            total = len(self.song_ids)
            success_count = 0
            os.makedirs(self.download_folder, exist_ok=True)

            for idx, song_id in enumerate(self.song_ids):
                try:
                    music = await self.musicapi.music(song_id)

                    # Get metadata first (for filename and display)
                    artist = music.artist_str if hasattr(music, 'artist_str') else "unknown"
                    album = music.album_str if hasattr(music, 'album_str') else "unknown"
                    title = music.name[0] if music.name and len(music.name) > 0 else "unknown"

                    # Display progress
                    self.root.after(0, self.update_progress, idx, total, f"正在下载: {artist} - {title}")
                    self.root.after(0, self.log, f"[INFO] 开始下载: {artist} - {title} (ID: {song_id})")

                    # Construct final filename
                    final_name = self.safe_filename(f"{artist} - {album} - {title}")
                    final_path = None
                    real_ext = None

                    # Download - handle auto mode (try FLAC first, fallback to MP3)
                    downloaded = False
                    download_error = None
                    if self.quality == "auto":
                        try:
                            self.root.after(0, self.log, f"[INFO] 尝试 FLAC...")
                            temp_path = await music.play(br=999000)
                            downloaded = True
                            real_ext = self.get_real_ext(temp_path)
                        except Exception as e:
                            download_error = f"FLAC: {e}"
                            self.root.after(0, self.log, f"[INFO] FLAC 失败: {e}, 尝试 MP3...")
                            try:
                                temp_path = await music.play(br=320000)
                                downloaded = True
                                real_ext = self.get_real_ext(temp_path)
                            except Exception as e2:
                                download_error = f"MP3: {e2}"
                                self.root.after(0, self.log, f"[INFO] MP3 也失败: {e2}")
                    elif self.quality == "mp3":
                        temp_path = await music.play(br=320000)
                        downloaded = True
                        real_ext = self.get_real_ext(temp_path)
                    else:  # flac
                        temp_path = await music.play(br=999000)
                        downloaded = True
                        real_ext = self.get_real_ext(temp_path)

                    if not downloaded or not real_ext:
                        self.root.after(0, self.log, f"[FAIL] 下载失败: {song_id} ({download_error})")
                        continue

                    # Construct final path with correct extension
                    final_path = os.path.join(self.download_folder, f"{final_name}{real_ext}")

                    # Check if already exists
                    if os.path.exists(final_path):
                        self.root.after(0, self.log, f"[SKIP] 已存在: {final_name}{real_ext}")
                        # Remove temp file
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                        success_count += 1
                        continue

                    # Move temp file to final location
                    self.root.after(0, self.log, f"[INFO] 保存为: {final_name}{real_ext}")
                    os.rename(temp_path, final_path)

                    # Write tags
                    self.write_tags(final_path, real_ext, title, artist, album)

                    # Download and write cover
                    cover_url = getattr(music, "album_pic_url", None) or getattr(music, "cover_url", None)
                    if cover_url:
                        cover_data = self.download_cover(cover_url)
                        self.write_cover(final_path, real_ext, cover_data)

                    # Download lyrics if enabled
                    if self.lyric_var.get():
                        lyric_success, lyric_result = await self.download_lyric(music, final_path)
                        if lyric_success:
                            self.root.after(0, self.log, f"[OK] 歌词: {lyric_result}")

                    self.root.after(0, self.log, f"[OK] {final_name}{real_ext}")
                    success_count += 1

                except Exception as e:
                    self.root.after(0, self.log, f"[FAIL] {song_id}: {e}")

            self.root.after(0, self.update_progress, total, total, f"下载完成! 成功: {success_count}/{total}")
            self.root.after(0, lambda: self.download_btn.config(state="normal"))

        threading.Thread(target=lambda: asyncio.run(_download()), daemon=True).start()

    def update_progress(self, current, total, message):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current
        self.progress_label.config(text=message)


def main():
    root = tk.Tk()
    app = MusicDownloadGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
