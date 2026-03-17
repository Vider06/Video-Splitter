import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess, os, threading, json, shutil

BG = "#0d0d0d"
CARD = "#161616"
ACCENT = "#ff4444"
TEXT = "#f0f0f0"
MUTED = "#555"
BORDER = "#2a2a2a"

class VideoSplitter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("V0RTEX — Video Splitter")
        self.geometry("520x460")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.video_path = tk.StringVar()
        self.ffmpeg_path = tk.StringVar(value=shutil.which("ffmpeg") or "")
        self.parts = tk.IntVar(value=3)
        self.status = tk.StringVar(value="Ready.")
        self._build_ui()
        if not self.ffmpeg_path.get():
            self.status.set("⚠  ffmpeg not in PATH — browse for ffmpeg.exe manually")

    def _build_ui(self):
        tk.Label(self, text="VIDEO SPLITTER", font=("Courier New", 13, "bold"),
                 fg=ACCENT, bg=BG).pack(pady=(22, 4))
        tk.Label(self, text="Split a video into equal parts via ffmpeg",
                 font=("Courier New", 8), fg=MUTED, bg=BG).pack()

        # --- Video file ---
        self._make_card_row("VIDEO FILE", self.video_path, self._browse_video)

        # --- ffmpeg.exe ---
        self._make_card_row("FFMPEG.EXE  (browse if not in PATH)",
                            self.ffmpeg_path, self._browse_ffmpeg, btn_color="#333")

        # --- Parts ---
        card2 = tk.Frame(self, bg=CARD, bd=0, highlightbackground=BORDER, highlightthickness=1)
        card2.pack(fill="x", padx=28, pady=4)
        row2 = tk.Frame(card2, bg=CARD)
        row2.pack(fill="x", padx=14, pady=12)
        tk.Label(row2, text="SPLIT INTO", font=("Courier New", 7, "bold"),
                 fg=MUTED, bg=CARD).pack(side="left")
        for n in (2, 3, 4, 5):
            tk.Radiobutton(row2, text=f"{n} parts", variable=self.parts, value=n,
                           font=("Courier New", 9), fg=TEXT, bg=CARD,
                           activebackground=CARD, activeforeground=ACCENT,
                           selectcolor=CARD, cursor="hand2").pack(side="left", padx=12)

        # --- Progress ---
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor=CARD, background=ACCENT, thickness=4)
        self.progress.pack(fill="x", padx=28, pady=(14, 4))

        tk.Label(self, textvariable=self.status, font=("Courier New", 8),
                 fg=MUTED, bg=BG).pack()

        self.btn_split = tk.Button(self, text="▶  SPLIT VIDEO",
                                   font=("Courier New", 10, "bold"),
                                   bg=ACCENT, fg="white", relief="flat",
                                   cursor="hand2", padx=20, pady=8,
                                   command=self._start_split)
        self.btn_split.pack(pady=(14, 0))

    def _make_card_row(self, label, var, cmd, btn_color=None):
        card = tk.Frame(self, bg=CARD, bd=0, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=28, pady=4)
        tk.Label(card, text=label, font=("Courier New", 7, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(10, 2))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=14, pady=(0, 12))
        tk.Entry(row, textvariable=var, font=("Courier New", 9), bg="#1e1e1e", fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightbackground=BORDER, highlightthickness=1).pack(
                     side="left", fill="x", expand=True, ipady=5)
        tk.Button(row, text="Browse", font=("Courier New", 8, "bold"),
                  bg=btn_color or ACCENT, fg="white", relief="flat", cursor="hand2",
                  padx=10, command=cmd).pack(side="left", padx=(8, 0), ipady=5)

    def _browse_video(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm"), ("All files", "*.*")])
        if path:
            self.video_path.set(path)
            self.status.set(f"Selected: {os.path.basename(path)}")

    def _browse_ffmpeg(self):
        path = filedialog.askopenfilename(
            title="Select ffmpeg.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if path:
            self.ffmpeg_path.set(path)
            self.status.set("ffmpeg set manually ✔")

    def _start_split(self):
        path = self.video_path.get().strip()
        ff = self.ffmpeg_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Select a valid video file."); return
        if not ff or not os.path.isfile(ff):
            messagebox.showerror("Error", "ffmpeg.exe not found.\nBrowse for it manually."); return
        self.btn_split.config(state="disabled")
        self.status.set("Getting duration…")
        threading.Thread(target=self._split_worker, args=(path, ff), daemon=True).start()

    def _split_worker(self, path, ff):
        try:
            ffprobe = ff.replace("ffmpeg.exe", "ffprobe.exe") if "ffmpeg.exe" in ff else "ffprobe"
            probe = subprocess.run(
                [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", path],
                capture_output=True, text=True)
            total = float(json.loads(probe.stdout)["format"]["duration"])
            n = self.parts.get()
            chunk = total / n
            base, ext = os.path.splitext(path)
            out_dir = os.path.dirname(path)

            for i in range(n):
                self.after(0, self.progress.config, {"value": int(i/n*100)})
                self.after(0, self.status.set, f"Splitting part {i+1}/{n}…")
                out = os.path.join(out_dir, f"{os.path.basename(base)}_part{i+1}{ext}")
                subprocess.run([ff, "-y", "-ss", str(i*chunk), "-i", path,
                                "-t", str(chunk), "-c", "copy", out], capture_output=True)

            self.after(0, self.progress.config, {"value": 100})
            self.after(0, self.status.set, f"✔  Done! {n} files in {out_dir}")
            self.after(0, messagebox.showinfo, "Done", f"Split into {n} parts!\n{out_dir}")
        except Exception as e:
            self.after(0, self.status.set, f"Error: {e}")
            self.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.after(0, self.btn_split.config, {"state": "normal"})

if __name__ == "__main__":
    VideoSplitter().mainloop()