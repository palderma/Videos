#!/bin/bash
cd /home/user/ice; N=1190; P=4; C=$(( (N+P-1)/P )); rm -f work/chunk*.mp4
for i in $(seq 0 $((P-1))); do a=$((i*C)); b=$(( (i+1)*C )); [ $b -gt $N ] && b=$N
  python3 scene.py --frames=$a:$b --out=work/chunk$i.mp4 > work/r$i.log 2>&1 &
done; wait
for i in $(seq 0 $((P-1))); do echo "file 'chunk$i.mp4'"; done > work/list.txt
ffmpeg -v error -y -f concat -safe 0 -i work/list.txt -c copy work/video.mp4 && echo done
