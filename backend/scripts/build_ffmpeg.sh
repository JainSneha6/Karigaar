#!/usr/bin/env bash
set -euo pipefail

# Destination inside the Vercel build output so it gets included in the deployment
OUT_DIR=".vercel_build_output/bin"
mkdir -p "$OUT_DIR"

# Temporary workspace
TMPDIR="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "Downloading static ffmpeg build (amd64)..."

# Download (John Van Sickle's static builds - x86_64)
curl -L "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" -o "$TMPDIR/ffmpeg.tar.xz"

# Extract into temp
tar -xJ -C "$TMPDIR" -f "$TMPDIR/ffmpeg.tar.xz"

# Find the extracted folder (pattern: ffmpeg-*-amd64-static)
EXDIR="$(find "$TMPDIR" -maxdepth 1 -type d -name "ffmpeg-*-amd64-static" | head -n1)"
if [ -z "$EXDIR" ]; then
  echo "Failed to find extracted ffmpeg folder"
  exit 1
fi

# Copy ffmpeg and ffprobe into output dir
cp "$EXDIR/ffmpeg" "$OUT_DIR/ffmpeg"
cp "$EXDIR/ffprobe" "$OUT_DIR/ffprobe"

# Make executable
chmod +x "$OUT_DIR/ffmpeg" "$OUT_DIR/ffprobe"

echo "ffmpeg + ffprobe copied to $OUT_DIR"
ls -la "$OUT_DIR"
