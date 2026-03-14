# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "------------------------------------------"
echo "🚀 Local Whisper Starter"
echo "------------------------------------------"

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first: https://brew.sh"
    exit 1
fi

# 2. Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 Installing FFmpeg..."
    brew install ffmpeg
fi

# 3. Check for whisper-cpp
if ! command -v whisper-cli &> /dev/null; then
    echo "📦 Installing whisper-cpp..."
    brew install whisper-cpp
fi

# 4. Check for Python dependencies
if ! python3 -c "import objc" &> /dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# 5. Check for Model
MODEL_DIR="$HOME/whisper-models"
MODEL_FILE="$MODEL_DIR/ggml-medium.bin"

if [ ! -f "$MODEL_FILE" ]; then
    echo "📥 Downloading multilingual model (medium)..."
    mkdir -p "$MODEL_DIR"
    curl -L -o "$MODEL_FILE" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin"
fi

echo "✅ Environment is ready. Launching app..."
echo "------------------------------------------"

SCRIPT="$DIR/transcribe_whisper_cli.py"

# Use python3 from Homebrew PATH
exec /usr/bin/env python3 "$SCRIPT"
