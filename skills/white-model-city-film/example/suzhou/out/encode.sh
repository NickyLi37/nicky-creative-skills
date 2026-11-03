#!/bin/zsh
# Encode a frame directory with the final mix (vo/mix_v2.wav: natural-speed narration over the score named in vo/align.json,
# the score dipping only in the speech band and only as far as it competes with the voice).
# Rebuild the mix after changing render/src/vo.js: node vo/build_vo.mjs && .venv/bin/python vo/mix_v2.py
# usage: out/encode.sh <frames_dir> <out.mp4> [x264|x265] [crf]
set -e
cd "$(dirname "$0")/.."
FR=$1; OUT=$2; CODEC=${3:-x264}; CRF=${4:-14}
AF="volume=0.5dB,alimiter=limit=0.9:level=false,aresample=48000"
if [[ $CODEC == x265 ]]; then
  V=(-c:v libx265 -preset slow -crf $CRF -pix_fmt yuv420p10le -tag:v hvc1 -x265-params log-level=error)
else
  V=(-c:v libx264 -preset slow -crf $CRF -pix_fmt yuv420p -profile:v high -movflags +faststart)
fi
ffmpeg -y -loglevel error -stats -framerate 24 -i "$FR/f%05d.png" -i vo/mix_v2.wav \
  -map 0:v -map 1:a -af "$AF" $V -c:a aac -b:a 320k -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,nb_frames -of compact "$OUT"
