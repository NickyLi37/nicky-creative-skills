#!/bin/zsh
# Phone / chat version under a size cap: two-pass x264 at a bitrate computed from the duration.
# usage: encode_phone.sh <frames_dir> <mix.wav> <out.mp4> [height=1080] [cap_MiB=29] [audio_kbps=112]
# 540p previews: height 540, audio 96. The limiter is lower (0.87) because low-bitrate AAC overshoots more.
set -e
FR=$1; MIX=$2; OUT=$3; HT=${4:-1080}; CAP=${5:-29}; AK=${6:-112}
N=$(ls "$FR" | grep -c '^f[0-9]*\.png$')
DUR=$(echo "$N / 24" | bc -l)
VK=$(echo "($CAP * 8388.608 * 0.97) / $DUR - $AK" | bc)   # MiB -> kbit, 3% muxing headroom
echo "frames $N, ${DUR%.*} s, video ${VK} kbps + audio ${AK} kbps"
LOG=$(mktemp -t x264pass)
AF="volume=0.5dB,alimiter=limit=0.87:level=false,aresample=48000"
ffmpeg -y -loglevel error -framerate 24 -i "$FR/f%05d.png" -vf "scale=-2:${HT}:flags=lanczos" \
  -c:v libx264 -preset slow -b:v ${VK}k -pix_fmt yuv420p -pass 1 -passlogfile "$LOG" -an -f mp4 /dev/null
ffmpeg -y -loglevel error -stats -framerate 24 -i "$FR/f%05d.png" -i "$MIX" -vf "scale=-2:${HT}:flags=lanczos" \
  -c:v libx264 -preset slow -b:v ${VK}k -pix_fmt yuv420p -pass 2 -passlogfile "$LOG" \
  -af "$AF" -c:a aac -b:a ${AK}k -movflags +faststart -shortest "$OUT"
rm -f "$LOG"*
ls -la "$OUT"
