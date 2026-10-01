#!/bin/bash
# match TTS track loudness to Alex track, then sum -> vo_new.wav
set -e
I=$(ffmpeg -nostdin -i alex_lv.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
TI=$(ffmpeg -nostdin -i tts_track.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
# both tracks are mostly silence; integrated loudness gating handles it. match speech loudness.
G=$(python3 -c "print($I-($TI))")
echo "alex I=$I tts I=$TI gain=$G"
ffmpeg -nostdin -v error -y -i tts_track.wav -af "volume=${G}dB,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=150:makeup=1,volume=0dB" tts_c.wav
TC=$(ffmpeg -nostdin -i tts_c.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G2=$(python3 -c "print($I-($TC))")
ffmpeg -nostdin -v error -y -i tts_c.wav -af "volume=${G2}dB,alimiter=limit=0.84:level=false" tts_l.wav
ffmpeg -nostdin -v error -y -i alex_lv.wav -i tts_l.wav -filter_complex "amix=inputs=2:normalize=0,alimiter=limit=0.89:level=false" -ar 48000 -ac 1 vo_new.wav
for f in alex_lv.wav tts_l.wav vo_new.wav; do echo "$f $(ffmpeg -nostdin -i $f -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tail -2 | tr -s ' ' | tr '\n' ' ')"; done
