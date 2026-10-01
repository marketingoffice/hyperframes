#!/bin/bash
# final mix: hook VO (n20) on the opening, body VO from V, music only under the cards
set -e
read V T H0 N <<<$(python3 -c "import json;t=json.load(open('timing.json'));print(t['V'],round(t['T'],3),t['H0'],t['N'])")
A=/tmp/claude-0/alex
# level the hook line like the body voice (-16 LUFS speech, compressed, limited)
ffmpeg -nostdin -v error -y -i ../lines/n20.wav -af "acompressor=threshold=-24dB:ratio=2.5:attack=8:release=150:makeup=1,loudnorm=I=-16:TP=-2:LRA=6:linear=true,alimiter=limit=0.84:level=false" -ar 48000 -ac 1 hook.wav
C=$(python3 -c "print(round($V+$N+0.07,3))")
ffmpeg -nostdin -v error -y -f lavfi -t $C -i anullsrc=r=48000:cl=stereo -i $A/t1f.wav -filter_complex "[1:a]aresample=48000,aformat=channel_layouts=stereo[b];[0:a][b]concat=n=2:v=0:a=1[m]" -map "[m]" closebed.wav
VMS=$(python3 -c "print(int(round($V*1000)))"); HMS=$(python3 -c "print(int(round($H0*1000)))")
MO=$(python3 -c "print(round($V-0.9,2))")
ffmpeg -nostdin -v error -y -i $A/musicloop.wav -i vo_new.wav -i closebed.wav -i hook.wav -filter_complex "\
[0:a]atrim=0:$V,asetpts=PTS-STARTPTS,volume='if(lt(t,$H0+7.9),0.089,0.355)':eval=frame,afade=t=in:d=0.6,afade=t=out:st=$MO:d=0.9,apad,atrim=0:$T[m1];\
[2:a]apad,atrim=0:$T[m2];\
[1:a]adelay=$VMS,aformat=channel_layouts=stereo,apad,atrim=0:$T[v];\
[3:a]adelay=$HMS,aformat=channel_layouts=stereo,apad,atrim=0:$T[h];\
[m1][m2][v][h]amix=inputs=4:normalize=0:duration=longest,atrim=0:$T,alimiter=limit=0.89[o]" -map "[o]" -ar 48000 -c:a pcm_s16le mix_new.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 mix_new.wav
