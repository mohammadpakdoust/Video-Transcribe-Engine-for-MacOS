#!/bin/bash

# ===== CONFIG =====
SCRIPT_PATH="/Users/mohammadpakdoust/Study/Whisper for videos/transcribe_whisper_cli.py"

# Default model (change if needed)
MODEL="ggml-medium.en"

# ===== CHECK INPUT =====
if [ -z "$1" ]; then
    echo "Usage: ./run_transcribe.sh <audio_or_video_file>"
    exit 1
fi

INPUT_FILE="$1"

# ===== CHECK FILE EXISTS =====
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ File not found: $INPUT_FILE"
    exit 1
fi

echo "🎧 Transcribing: $INPUT_FILE"
echo "🧠 Model: $MODEL"
echo "--------------------------------"

python3 "$SCRIPT_PATH" "$INPUT_FILE"

echo "--------------------------------"
echo "✅ Done!"