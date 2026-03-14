# Video-Transcribe-Engine-for-MacOS

A high-performance, local transcription solution for macOS. Leveraging `whisper.cpp` and Metal GPU acceleration, this tool provides a seamless native experience for transcribing video and audio files with zero cloud dependency.

---

## 🚀 Key Features

- **Native macOS Experience:** Smooth, PyObjC-based drag-and-drop interface.
- **Hardware Accelerated:** Optimized for Apple Silicon using Metal for ultra-fast transcription.
- **Multilingual Support:** Powered by Whisper's medium model, supporting 99+ languages with automatic detection.
- **Privacy First:** 100% offline. No data ever leaves your machine.
- **Pro Outputs:** Automatically generates formatted `.txt` and timestamped `.srt` subtitles.
- **One-Click Setup:** Fully automated dependency management for Homebrew, FFmpeg, and Python.

## 🛠 Tech Stack

- **Core:** [whisper.cpp](https://github.com/ggerganov/whisper.cpp) (C/C++ foundation)
- **UI:** Python 3 + Tkinter (themed for macOS)
- **Integration:** PyObjC for native macOS window handling
- **Processing:** FFmpeg for robust media stream extraction

---

## 📦 Requirements

- **macOS** (Optimized for Apple Silicon / M1, M2, M3)
- **Homebrew** (External package manager)
- **Python 3** (Standard with macOS or via Homebrew)

---

## ⚡️ Quick Start (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mohammadpakdoust/whisper-for-videos.git
    cd whisper-for-videos
    ```

2.  **Launch the App:**
    Double-click `Whisper.command` in the Finder.

    > [!IMPORTANT]
    > **First-Time Setup:** The first time you run the app, it will automatically download the multilingual AI model (~1.4 GB) and install necessary components (FFmpeg, whisper-cpp). Please keep the terminal window open until the GUI appears.

3.  **Transcribe:**
    Drag any video or audio file into the window and click **Start**.

---

## 🖥 Manual / CLI Usage

If you prefer using the terminal or want to integrate transcription into your scripts:

```bash
./run.sh path/to/media_file.mp4
```

This will use the same optimized pipeline to generate transcriptions in the source file's directory.

---

## 📊 Supported Formats

| Category | Formats |
| :--- | :--- |
| **Video** | `.mp4`, `.mov`, `.webm`, `.mkv` |
| **Audio** | `.mp3`, `.m4a`, `.wav`, `.aac`, `.flac`, `.ogg` |

---

## ⚖️ License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Mohammad Pakdoust**  
[GitHub Profile](https://github.com/mohammadpakdoust)

---

> [!NOTE]  
> This project was developed to showcase local AI integration on macOS. It focuses on practical usability, hardware optimization, and high-quality transcription outputs.
