import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


def transcribe(video, report, speaker_count=None):
    from speakers import find_turns, transcribe_turns, refine_turns, voice_regions
    import numpy as np
    from pywhispercpp.model import Model

    root = Path(__file__).resolve().parent
    model_path = root / "assets" / "ggml-base.bin"
    if not model_path.is_file():
        raise FileNotFoundError("The bundled speech model is missing. Restore the complete app package.")
    if getattr(sys, "frozen", False):
        ffmpeg = next((root / "tools").glob("ffmpeg*"), None)
    else:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg:
        raise FileNotFoundError("The bundled FFmpeg executable is missing.")
    video = Path(video).resolve(strict=True)
    report("Reading audio…")
    with tempfile.TemporaryDirectory(prefix="video-to-text-") as temp:
        pcm = Path(temp) / "audio.f32"
        result = subprocess.run(
            [str(ffmpeg), "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe",
             "-i", str(video), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
             "-f", "f32le", str(pcm)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            detail = result.stderr.decode(errors="replace").strip()
            if "matches no streams" in detail:
                raise ValueError("This video has no audio track.")
            raise ValueError("Could not read the audio. " + detail[-600:])
        if not pcm.stat().st_size:
            raise ValueError("The audio track is empty.")
        report("Loading speech model…")
        model = Model(str(model_path), language="auto", translate=False, print_progress=False,
                      context_params={"use_gpu": False})
        audio = np.memmap(pcm, dtype="<f4", mode="c")
        try:
            report("Identifying speakers…")
            turns = find_turns(audio, model_path.parent, speaker_count)
            spans = refine_turns(audio, voice_regions(turns, len(audio)), model_path.parent)
            report("Transcribing speech…")
            return transcribe_turns(model, audio, spans)
        finally:
            del audio


def save_text(path, content):
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
    try:
        temp.write_text(content.rstrip() + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class Window:
    def __init__(self, root):
        self.root = root
        self.video = None
        self.busy = False
        self.events = queue.Queue()
        root.title("Video to Text")
        root.geometry("800x615")
        root.minsize(570, 440)
        paper, ink, accent = "#f5f4ee", "#103d3c", "#00716d"
        family = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI"
        root.configure(bg=paper)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TButton", font=(family, 11, "bold"), padding=(14, 8),
                        background="#ffffff", foreground=ink, bordercolor="#bdcfc9")
        style.map("TButton", background=[("disabled", "#eeefea"), ("active", "#dcebe7")],
                  foreground=[("disabled", "#707975")])
        style.configure("Action.TButton", background=accent, foreground="white",
                        bordercolor=accent)
        style.map("Action.TButton", background=[("disabled", "#e0e5df"), ("active", "#005952")],
                  foreground=[("disabled", "#626d68")])
        style.configure("TCombobox", fieldbackground="white", foreground=ink, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", "white")],
                  foreground=[("readonly", ink)])
        head = tk.Frame(root, bg=ink, padx=24, pady=16)
        head.pack(fill="x")
        self.logo = tk.PhotoImage(file=str(Path(__file__).resolve().parent / "assets" / "header-logo.png"))
        if sys.platform != "darwin":
            root.iconphoto(True, self.logo)
        tk.Label(head, image=self.logo, bg=ink).pack(side="left", padx=(0, 12))
        tk.Label(head, text="Video to Text", font=(family, 23, "bold"),
                 bg=ink, fg="white").pack(side="left")
        frame = tk.Frame(root, bg=paper, padx=24, pady=16)
        frame.pack(fill="both", expand=True)
        card = tk.Frame(frame, bg="white", padx=14, pady=12, highlightthickness=1,
                        highlightbackground="#ced9d2")
        card.pack(fill="x")
        self.choose = ttk.Button(card, text="Choose Video…", command=self.select)
        self.choose.pack(side="right", padx=(12, 0))
        tk.Label(card, text="Source video", font=(family, 10, "bold"), fg=accent,
                 bg="white").pack(anchor="w")
        self.file_label = tk.Label(card, text="No video selected", anchor="w",
                                   bg="white", fg=ink, font=(family, 13))
        self.file_label.pack(fill="x")
        options = tk.Frame(frame, bg=paper)
        options.pack(fill="x", pady=(12, 18))
        tk.Label(options, text="Number of speakers", font=(family, 11),
                 bg=paper, fg=ink).pack(side="left", padx=(0, 8))
        self.count = ttk.Combobox(options, values=["Auto", *range(1, 9)], width=5, state="readonly")
        self.count.set("2")
        self.count.pack(side="left")
        self.run = ttk.Button(options, text="Transcribe", style="Action.TButton",
                              command=self.start, state="disabled")
        self.run.pack(side="right")
        toolbar = tk.Frame(frame, bg=paper)
        toolbar.pack(fill="x", pady=(0, 8))
        tk.Label(toolbar, text="Transcript", font=(family, 17, "bold"), fg=ink,
                 bg=paper).pack(side="left")
        self.save = ttk.Button(toolbar, text="Save Text…", command=self.export, state="disabled")
        self.save.pack(side="right")
        self.preview = ScrolledText(frame, wrap="word", undo=True, padx=15, pady=12,
                                    height=6, font=(family, 12), bg="white", fg="#203a37",
                                    insertbackground=ink, selectbackground="#bce3d9",
                                    selectforeground=ink, spacing3=5, relief="flat",
                                    highlightthickness=1, highlightbackground="#ced9d2",
                                    highlightcolor=accent, state="disabled")
        self.status = tk.Label(frame, text="Choose a video to begin.", font=(family, 10),
                               anchor="w", bg=paper, fg="#455f58")
        self.status.pack(side="bottom", fill="x", pady=(8, 0))
        self.preview.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def display(self, text):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.edit_reset()
        self.preview.configure(state="normal" if text else "disabled")

    def select(self):
        name = filedialog.askopenfilename(filetypes=[
            ("Videos", ("*.mp4", "*.mov", "*.mkv", "*.avi", "*.m4v", "*.webm")), ("All files", "*")])
        if name:
            self.video = Path(name)
            self.file_label.configure(text=self.video.name)
            self.display("")
            self.status.configure(text="")
            self.run.configure(state="normal")
            self.save.configure(state="disabled")

    def start(self):
        self.busy = True
        for button in (self.choose, self.run, self.save):
            button.configure(state="disabled")
        self.display("")
        self.status.configure(text="Starting…")
        selected = self.count.get()
        speaker_count = None if selected == "Auto" else int(selected)
        self.count.configure(state="disabled")
        threading.Thread(target=self.work, args=(speaker_count,)).start()
        self.root.after(100, self.poll)

    def work(self, speaker_count):
        try:
            result = transcribe(self.video, lambda msg: self.events.put(("status", msg)), speaker_count)
            self.events.put(("done", result))
        except Exception as error:
            self.events.put(("error", str(error)))

    def poll(self):
        while not self.events.empty():
            kind, text = self.events.get()
            if kind == "status":
                self.status.configure(text=text)
                continue
            self.busy = False
            self.count.configure(state="readonly")
            self.choose.configure(state="normal")
            self.run.configure(state="normal")
            if kind == "error":
                self.status.configure(text="Transcription failed.")
                messagebox.showerror("Transcription failed", text)
            else:
                self.display(text)
                self.status.configure(text="Transcript ready. You can edit speaker labels and text before saving." if text else "No speech detected.")
                if text:
                    self.save.configure(state="normal")
        if self.busy:
            self.root.after(100, self.poll)

    def export(self):
        name = filedialog.asksaveasfilename(defaultextension=".txt",
            initialfile=self.video.stem + ".txt", filetypes=[("Text files", "*.txt")])
        if name:
            try:
                save_text(name, self.preview.get("1.0", "end-1c"))
                self.status.configure(text="Saved " + Path(name).name)
            except OSError as error:
                messagebox.showerror("Could not save transcript", str(error))

    def close(self):
        if self.busy:
            messagebox.showinfo("Transcription in progress", "Please wait for the transcript before closing.")
        else:
            self.root.destroy()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--transcribe"]:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--transcribe", nargs=2, required=True, metavar=("VIDEO", "TEXT"))
        parser.add_argument("--speakers", type=int, choices=range(1, 9))
        args = parser.parse_args()
        video, output = args.transcribe
        save_text(output, transcribe(video, lambda msg: None, args.speakers))
    else:
        window = tk.Tk()
        Window(window)
        window.mainloop()
