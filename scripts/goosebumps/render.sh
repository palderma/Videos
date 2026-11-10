#!/bin/bash
# render all frames in 4 parallel chunks, then encode (no audio)
cd "$(dirname "$0")"
N=510; OUT=work/frames; rm -rf $OUT; mkdir -p $OUT
P=4; C=$(( (N + P - 1) / P ))
for i in $(seq 0 $((P-1))); do a=$((i*C)); b=$(( (i+1)*C )); [ $b -gt $N ] && b=$N
  python3 gb.py --frames=$a:$b --out=$OUT > work/r$i.log 2>&1 &
done
wait
ls $OUT | wc -l
ffmpeg -v error -y -framerate 30 -i $OUT/%05d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart work/video.mp4
