# Local Whisper — macOS Transcription App

**By Mohammad Pakdoust**

A native macOS desktop app that transcribes any video or audio file locally using [whisper.cpp](https://github.com/ggerganov/whisper.cpp) and Metal GPU acceleration. No cloud, no API keys — everything runs on your machine.

---

## Features

- 🎙️ **Local transcription** — powered by `whisper.cpp` (Metal GPU on Apple Silicon)
- 📁 **Drag & Drop** — drop any media file anywhere on the window
- 📂 **File picker** — classic open-file dialog as an alternative
- 📊 **Real-time progress** — determinate progress bar during FFmpeg conversion, animated bar during transcription
- ❌ **Cancel button** — actually stops the running process immediately
- 📝 **Two output formats** — `.txt` (clean text) and `.srt` (subtitles with timestamps)
- 📂 **Open Output Folder** — one click to reveal results in Finder
- 🧹 **Auto-cleanup** — temporary WAV file deleted after transcription (optional)

---

## Requirements

### Homebrew packages
```bash
brew install ffmpeg whisper-cpp
```

### Whisper model
Download the model and place it at `~/whisper-models/ggml-medium.en.bin`:
```bash
mkdir -p ~/whisper-models
curl -L -o ~/whisper-models/ggml-medium.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```
> `ggml-medium.bin` is the multilingual model — supports 99 languages including English, Persian, Arabic, French, Spanish, and more. Language is auto-detected.

### Python packages
```bash
pip install pyobjc-framework-Cocoa
```
> Required for native macOS drag-and-drop support.

---

## Getting Started

### Option 1 — Double-click (recommended)
Double-click **`Whisper.command`** in Finder. A Terminal window opens and the GUI launches automatically.

> **First run only:** macOS may block the script. Right-click → Open → Open to allow it.

### Option 2 — Terminal
```bash
python3 transcribe_whisper_cli.py
```

### Option 3 — Terminal with file pre-selected
```bash
./run.sh /path/to/your/video.mp4
```
The GUI opens with the file already loaded and ready to start.

---

## Workflow

1. **Drop** a file onto the window (or click **Choose File…**)
2. Click **Start**
3. Watch the progress bar:
   - `Converting to WAV…` — FFmpeg extracts 16 kHz mono audio
   - `Transcribing (GPU / Metal)…` — whisper.cpp processes the audio
4. A completion dialog confirms the output location
5. Click **Open Output Folder** to view your `.txt` and `.srt` files

---

## Output

Files are saved **in the same folder as the input file**:

| File | Contents |
|---|---|
| `filename.txt` | Full transcript as plain text |
| `filename.srt` | Subtitles with timestamps for video players |

---

## Configuration

Edit the top of `transcribe_whisper_cli.py` to customise:

```python
MODEL_PATH = os.path.expanduser("~/whisper-models/ggml-medium.en.bin")
DELETE_WAV_AFTER_DEFAULT = True   # set False to keep the intermediate WAV
WHISPER_OUTPUT_FLAGS = ["-otxt", "-osrt", "-pp"]  # output formats
```

### Supported input formats
`mp4` · `mov` · `m4a` · `mp3` · `wav` · `aac` · `flac` · `ogg` · `webm`

---

## Project Structure

```
Whisper for videos/
├── Whisper.command              # Double-click launcher (opens Terminal + GUI)
├── run.sh                       # Shell launcher with optional file argument
└── transcribe_whisper_cli.py    # Main GUI application
```

---

## License

MIT — free to use, modify, and distribute.
