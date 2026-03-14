#!/usr/bin/env python3
"""
Local Whisper by mpakdoust (macOS)
Features:
- File picker + Drag & Drop (optional, via tkinterdnd2)
- Convert media -> 16kHz mono WAV via ffmpeg (determinate progress)
- Transcribe via whisper.cpp (whisper-cli) using Metal GPU (indeterminate progress)
- Cancel button that actually stops ffmpeg/whisper
- "Open output folder" button after completion
- Saves .txt and .srt in the same directory as the input file

Requirements:
- Homebrew: brew install ffmpeg whisper-cpp
- Model: ~/whisper-models/ggml-medium.en.bin

Optional (for Drag & Drop):
- pip install tkinterdnd2
"""

import os
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------- YOUR DEFAULTS ----------------
APP_TITLE = "Local Whisper by mpakdoust"

MODEL_PATH = os.path.expanduser("~/whisper-models/ggml-medium.bin")
DELETE_WAV_AFTER_DEFAULT = True

# Output formats (txt + srt + paragraph split)
WHISPER_OUTPUT_FLAGS = ["-otxt", "-osrt", "-pp"]

# Fallback paths for Homebrew (Apple Silicon)
FALLBACK_WHISPER = "/opt/homebrew/bin/whisper-cli"
FALLBACK_FFMPEG = "/opt/homebrew/bin/ffmpeg"
FALLBACK_FFPROBE = "/opt/homebrew/bin/ffprobe"
# ----------------------------------------------


def which_or_fallback(cmd: str, fallback: str | None = None) -> str:
    p = shutil.which(cmd)
    if p:
        return p
    if fallback and Path(fallback).exists():
        return fallback
    raise FileNotFoundError(f"'{cmd}' not found. Please install it or fix PATH.")


def open_folder_in_finder(folder: Path) -> None:
    # macOS Finder
    subprocess.run(["open", str(folder)], check=False)


def get_duration_seconds(ffprobe_path: str, input_path: Path) -> float:
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    try:
        return float(out) if out else 0.0
    except ValueError:
        return 0.0


def normalize_dnd_path(raw: str) -> str:
    """
    tkinterdnd2 often sends:
      - '{/path/with spaces/file.mp4}'
      - or a list of paths separated by spaces
    We'll extract the first path and strip braces.
    """
    s = raw.strip()
    # If it's like "{...}" keep inside
    if s.startswith("{") and "}" in s:
        s = s[1:s.index("}")]
    # If multiple files, take first token (best-effort)
    # But be careful about spaces in paths - braces typically handle those.
    # If no braces and multiple tokens, take first.
    if " " in s and not s.startswith("/"):
        # weird case; just return as-is
        return s
    if " " in s and s.count("/") >= 1 and not raw.strip().startswith("{"):
        # multiple unbraced paths; take first token
        s = s.split(" ")[0]
    return s


class AppBase:
    """Shared logic between Tk and TkinterDnD root windows."""
    def set_status(self, text: str):
        self.status_var.set(text)

    def set_progress(self, value: float, mode: str = "determinate"):
        self.progress.configure(mode=mode)
        if mode == "determinate":
            v = max(0.0, min(100.0, float(value)))
            self.progress["value"] = v
            self.progress_label.set(f"{int(v)}%")
        else:
            self.progress_label.set("Working…")

    def set_selected_file(self, path: str):
        p = Path(path).expanduser().resolve()
        if not p.exists():
            messagebox.showerror("File not found", f"Could not find:\n{p}")
            return
        self.selected_file = p
        self.file_label.config(text=str(self.selected_file))
        self.start_btn.config(state="normal")
        self.open_folder_btn.config(state="disabled")
        self.last_output_dir = None
        self.set_status("Ready to start.")
        self.set_progress(0, "determinate")

    def pick_file(self):
        file_path = filedialog.askopenfilename(
            title="Select video/audio file",
            filetypes=[
                ("Media files", "*.mp4 *.mov *.m4a *.mp3 *.wav *.aac *.flac *.ogg *.webm"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.set_selected_file(file_path)

    def start(self):
        if self.is_running:
            return
        if not self.selected_file:
            messagebox.showwarning("No file", "Please choose (or drag & drop) a file first.")
            return

        self.stop_requested = False
        self.is_running = True
        self.pick_btn.config(state="disabled")
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.open_folder_btn.config(state="disabled")

        self.set_status("Starting…")
        self.set_progress(0, "determinate")

        threading.Thread(target=self.worker, daemon=True).start()

    def cancel(self):
        if not self.is_running:
            return
        self.stop_requested = True
        self.set_status("Canceling…")

        # Kill active subprocess if present
        p = self.active_process
        if p and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
            # If it doesn't stop quickly, force kill
            def force_kill_later():
                try:
                    if p.poll() is None:
                        p.kill()
                except Exception:
                    pass
            self.after(800, force_kill_later)

        # Stop any indeterminate animation
        try:
            self.progress.stop()
        except Exception:
            pass

    def open_output_folder(self):
        if self.last_output_dir and Path(self.last_output_dir).exists():
            open_folder_in_finder(Path(self.last_output_dir))

    def _run_ffmpeg_with_progress(self, ffmpeg_path: str, ffprobe_path: str, input_path: Path, wav_path: Path):
        duration = get_duration_seconds(ffprobe_path, input_path)
        if duration <= 0:
            duration = 1.0

        cmd = [
            ffmpeg_path,
            "-y",
            "-i", str(input_path),
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-progress", "pipe:1",
            "-nostats",
            str(wav_path),
        ]

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.active_process = p

        try:
            if p.stdout:
                for line in p.stdout:
                    if self.stop_requested:
                        raise RuntimeError("Canceled by user.")
                    line = line.strip()
                    if line.startswith("out_time_ms="):
                        ms = int(line.split("=", 1)[1])
                        sec = ms / 1_000_000.0
                        percent = (sec / duration) * 100.0
                        self.after(0, self.set_progress, percent, "determinate")
        finally:
            code = p.wait()
            self.active_process = None

        if self.stop_requested:
            raise RuntimeError("Canceled by user.")
        if code != 0:
            raise RuntimeError(f"ffmpeg failed (exit {code}).")

    def _run_whisper(self, whisper_cli: str, wav_path: Path, out_prefix: Path):
        cmd = [
            whisper_cli,
            "-f", str(wav_path),
            "-m", MODEL_PATH,
            "-l", self.lang_var.get(),
            "-of", str(out_prefix),
            *WHISPER_OUTPUT_FLAGS,
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.active_process = p
        code = p.wait()
        self.active_process = None

        if self.stop_requested:
            raise RuntimeError("Canceled by user.")
        if code != 0:
            raise RuntimeError(f"whisper-cli failed (exit {code}).")

    def worker(self):
        try:
            whisper_cli = which_or_fallback("whisper-cli", FALLBACK_WHISPER)
            ffmpeg = which_or_fallback("ffmpeg", FALLBACK_FFMPEG)
            ffprobe = which_or_fallback("ffprobe", FALLBACK_FFPROBE)

            if not Path(MODEL_PATH).exists():
                raise FileNotFoundError(
                    f"Model not found:\n{MODEL_PATH}\n\nTip: put ggml-medium.bin in ~/whisper-models/"
                )

            inp = self.selected_file
            assert inp is not None

            out_dir = inp.parent
            base = inp.stem

            # WAV temp (same folder)
            wav_path = out_dir / f"{base}__16k_mono.wav"
            out_prefix = out_dir / base

            # 1) Convert
            self.after(0, self.set_status, "Converting to WAV…")
            self.after(0, self.set_progress, 0, "determinate")
            self._run_ffmpeg_with_progress(ffmpeg, ffprobe, inp, wav_path)
            self.after(0, self.set_progress, 100, "determinate")

            # 2) Transcribe
            self.after(0, self.set_status, "Transcribing (GPU / Metal)…")
            self.after(0, self.set_progress, 0, "indeterminate")
            self.after(0, self.progress.start, 12)  # indeterminate animation
            self._run_whisper(whisper_cli, wav_path, out_prefix)
            self.after(0, self.progress.stop)
            self.after(0, self.set_progress, 100, "determinate")

            # Cleanup WAV
            if not self.keep_wav_var.get() and wav_path.exists():
                try:
                    wav_path.unlink()
                except Exception:
                    pass

            # Enable "Open output folder"
            self.last_output_dir = str(out_dir)
            self.after(0, self.open_folder_btn.config, {"state": "normal"})
            self.after(0, self.set_status, "Done ✅")
            self.after(
                0,
                messagebox.showinfo,
                "Done ✅",
                f"Saved in:\n{out_dir}\n\nOutputs:\n- {base}.txt\n- {base}.srt",
            )

        except Exception as e:
            # If user canceled, show gentle message
            if "Canceled by user" in str(e):
                self.after(0, self.set_status, "Canceled.")
                self.after(0, self.set_progress, 0, "determinate")
            else:
                self.after(0, self.set_status, "Error ❌")
                self.after(0, messagebox.showerror, "Error", str(e))
        finally:
            try:
                self.after(0, self.progress.stop)
            except Exception:
                pass
            self.active_process = None
            self.is_running = False
            self.after(0, self.pick_btn.config, {"state": "normal"})
            self.after(0, self.start_btn.config, {"state": "normal"})
            self.after(0, self.cancel_btn.config, {"state": "disabled"})


# -------- Native macOS Drag & Drop (PyObjC) --------
# Uses an invisible NSView overlay — no extra packages needed on
# system Python. For Homebrew Python: pip install pyobjc-framework-Cocoa

def _setup_pyobjc_dnd(tk_root, callback):
    """
    Lay an invisible NSView over the Tkinter window that accepts file drops.
    Calls callback(path: str) on each dropped file path.
    Returns True on success, False if PyObjC is unavailable.
    """
    try:
        import objc
        from AppKit import NSApp, NSView, NSDragOperationCopy, NSFilenamesPboardType

        # Define the ObjC subclass only once (avoid duplicate-registration crash).
        try:
            _Cls = objc.lookUpClass("_WhisperTkDragView")
        except Exception:
            class _WhisperTkDragView(NSView):  # type: ignore[misc]
                def initWithCallback_(self, cb):
                    self = objc.super(_WhisperTkDragView, self).initWithFrame_(((0, 0), (0, 0)))
                    if self is None:
                        return None
                    self._cb = cb
                    self.registerForDraggedTypes_([NSFilenamesPboardType])
                    return self

                # --- NSDraggingDestination protocol ---
                def draggingEntered_(self, sender):
                    return NSDragOperationCopy

                def draggingUpdated_(self, sender):
                    return NSDragOperationCopy

                def prepareForDragOperation_(self, sender):
                    return True

                def performDragOperation_(self, sender):
                    pboard = sender.draggingPasteboard()
                    files = pboard.propertyListForType_(NSFilenamesPboardType)
                    if files and self._cb:
                        self._cb(str(files[0]))
                    return True

                def wantsPeriodicDraggingUpdates(self):
                    return False

                # --- Appearance / hit-testing ---
                def isOpaque(self):
                    return False

                def hitTest_(self, point):
                    # Pass mouse clicks through to Tkinter widgets below.
                    return None

            _Cls = _WhisperTkDragView

        tk_root.update_idletasks()
        title = tk_root.title()
        for ns_win in NSApp.windows():
            if ns_win.title() == title:
                cv = ns_win.contentView()
                drag_view = _Cls.alloc().initWithCallback_(callback)
                drag_view.setFrame_(cv.frame())
                drag_view.setAutoresizingMask_(18)  # WidthSizable | HeightSizable
                cv.addSubview_(drag_view)
                return True
        return False

    except Exception as exc:
        print(f"[DnD] Native setup skipped: {exc}")
        return False
# -----------------------------------------------


class App(tk.Tk, AppBase):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x380")

        # State
        self.selected_file: Path | None = None
        self.last_output_dir: str | None = None
        self.is_running = False
        self.stop_requested = False
        self.active_process: subprocess.Popen | None = None

        # --- UI ---
        top = tk.Frame(self)
        top.pack(fill="x", padx=14, pady=12)

        # Drop zone label (also shows path after selection)
        self.drop_zone = tk.Label(
            top,
            text="📁 Drop a file here or click Choose File…",
            relief="solid",
            bd=2,
            padx=10,
            pady=20,
            anchor="center",
            bg="white",
            fg="#333333",
            font=("Helvetica", 11),
        )
        self.drop_zone.pack(fill="both", expand=True, pady=(0, 8))
        self.drop_zone_default_bg = self.drop_zone.cget("bg")

        self.file_label = tk.Label(top, text="No file selected", anchor="w", font=("Helvetica", 9), fg="#666666")
        self.file_label.pack(fill="x", pady=(4, 8))

        # Buttons row
        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", padx=14, pady=(6, 0))

        self.pick_btn = tk.Button(btn_row, text="Choose File…", command=self.pick_file)
        self.pick_btn.pack(side="left")

        self.start_btn = tk.Button(btn_row, text="Start", command=self.start, state="disabled")
        self.start_btn.pack(side="left", padx=10)

        self.cancel_btn = tk.Button(btn_row, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left")

        self.open_folder_btn = tk.Button(btn_row, text="Open Output Folder", command=self.open_output_folder, state="disabled")
        self.open_folder_btn.pack(side="right")

        self.keep_wav_var = tk.BooleanVar(value=not DELETE_WAV_AFTER_DEFAULT)
        tk.Checkbutton(btn_row, text="Keep WAV file", variable=self.keep_wav_var).pack(side="left", padx=12)

        # Status area
        status_row = tk.Frame(self)
        status_row.pack(fill="x", padx=14, pady=(12, 0))
        
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(status_row, textvariable=self.status_var, anchor="w").pack(side="left")
        
        # Language Selector (Right-aligned)
        tk.Label(status_row, text="Language:").pack(side="right", padx=(10, 5))
        self.lang_var = tk.StringVar(value="auto")
        self.lang_combo = ttk.Combobox(status_row, textvariable=self.lang_var, width=10, state="readonly")
        self.lang_combo['values'] = ("auto", "fa", "en", "de", "fr", "es", "it", "ja", "ko", "zh")
        self.lang_combo.pack(side="right")

        # Progress bar
        pb = tk.Frame(self)
        pb.pack(fill="x", padx=14, pady=10)

        self.progress = ttk.Progressbar(pb, orient="horizontal", mode="determinate", maximum=100)
        self.progress.pack(fill="x")

        self.progress_label = tk.StringVar(value="0%")
        tk.Label(pb, textvariable=self.progress_label, anchor="w").pack(fill="x", pady=(6, 0))

        # Footer
        tk.Label(
            self,
            text=f"Model: {Path(MODEL_PATH).stem}\nOutputs: .txt + .srt (same folder as input) | whisper.cpp (Metal GPU)\nBy Mohammad Pakdoust",
            fg="gray", justify="left", anchor="w",
        ).pack(fill="x", padx=14, pady=(6, 10))

        # Pre-select file if launched with a path argument (e.g. from run.sh)
        import sys
        if len(sys.argv) > 1:
            self.after(100, self.set_selected_file, sys.argv[1])

        # Set up native macOS DnD after the window is visible
        self.after(400, self._init_dnd)

    def _init_dnd(self):
        """Attach a native macOS drag-destination overlay to this window."""
        ok = _setup_pyobjc_dnd(self, self.set_selected_file)
        if not ok:
            self.drop_zone.config(
                text="Choose File…  (drag & drop unavailable — run: pip install pyobjc-framework-Cocoa)"
            )


if __name__ == "__main__":
    App().mainloop()
