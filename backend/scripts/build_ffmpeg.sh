#!/usr/bin/env bash
set -euo pipefail

OUT_DIR=".vercel_build_output/bin"
mkdir -p "$OUT_DIR"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading static ffmpeg build..."
curl -k -L "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" -o "$TMPDIR/ffmpeg.tar.xz"

tar -xJf "$TMPDIR/ffmpeg.tar.xz" -C "$TMPDIR"

EXDIR="$(find "$TMPDIR" -maxdepth 1 -type d -name 'ffmpeg-*' | head -n1)"
cp "$EXDIR/ffmpeg" "$OUT_DIR/ffmpeg"
cp "$EXDIR/ffprobe" "$OUT_DIR/ffprobe"
chmod +x "$OUT_DIR/ffmpeg" "$OUT_DIR/ffprobe"

echo "Binaries installed to $OUT_DIR:"
ls -la "$OUT_DIR"
