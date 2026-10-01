#!/bin/bash
# Alex: per-turn gain already applied in build.py; denoise + compress + fixed measured gain to -16 LUFS
set -e
ffmpeg -nostdin -v error -y -i alex_track.wav -af "highpass=f=80,afftdn=nf=-55,acompressor=threshold=-26dB:ratio=2.5:attack=8:release=150:makeup=1" -ar 48000 -c:a pcm_s16le alex_c.wav
I=$(ffmpeg -nostdin -i alex_c.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(-16-($I))")
ffmpeg -nostdin -v error -y -i alex_c.wav -af "volume=${G}dB,alimiter=limit=0.84:level=false" -ar 48000 -c:a pcm_s16le alex_lv.wav
echo "alex I=$I gain=$G"
