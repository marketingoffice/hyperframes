#!/bin/bash
# Raw render is already ~-14 LUFS; just trim and true-peak limit, then share copy.
set -e
IN=$1; OUT=$2
ffmpeg -nostdin -v error -y -i "$IN" -c:v copy -af "volume=-0.3dB,alimiter=limit=0.8:attack=4:release=80:level=disabled" -ar 48000 -c:a aac -b:a 256k -movflags +faststart "$OUT.mp4"
ffmpeg -nostdin -v error -y -i "$OUT.mp4" -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$OUT-share.mp4"
ffmpeg -nostdin -i "$OUT.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2
ls -la "$OUT.mp4" "$OUT-share.mp4"
