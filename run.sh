#!/bin/bash

# ===== CONFIG =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_PATH="$SCRIPT_DIR/transcribe_whisper_cli.py"

# Default model
MODEL_NAME="ggml-medium"

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
echo "🧠 Model: $MODEL_NAME"
echo "--------------------------------"

python3 "$SCRIPT_PATH" "$INPUT_FILE"

echo "--------------------------------"
echo "✅ Done!"