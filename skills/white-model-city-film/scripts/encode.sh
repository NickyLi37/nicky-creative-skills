#!/bin/zsh
# Master: frame directory + final mix -> MP4 (frames named f00000.png, 24 fps).
# usage: encode.sh <frames_dir> <mix.wav> <out.mp4> [x264|x265] [crf]
# The limiter sits at 0.9: AAC overshoots the PCM peak, and at 0.93 a 96k AAC encode reached +0.3 dBTP.
set -e
FR=$1; MIX=$2; OUT=$3; CODEC=${4:-x264}; CRF=${5:-14}
AF="volume=0.5dB,alimiter=limit=0.9:level=false,aresample=48000"
if [[ $CODEC == x265 ]]; then
  V=(-c:v libx265 -preset slow -crf $CRF -pix_fmt yuv420p10le -tag:v hvc1 -x265-params log-level=error)
else
  V=(-c:v libx264 -preset slow -crf $CRF -pix_fmt yuv420p -profile:v high -movflags +faststart)
fi
ffmpeg -y -loglevel error -stats -framerate 24 -i "$FR/f%05d.png" -i "$MIX" \
  -map 0:v -map 1:a -af "$AF" $V -c:a aac -b:a 320k -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,nb_frames -of compact "$OUT"
