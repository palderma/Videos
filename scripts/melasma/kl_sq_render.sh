#!/bin/bash
cd /home/user/klf; O=/home/user/klf/render_sq; mkdir -p $O; rm -f $O/*.mp4 $O/list.txt
N=960; P=4; C=240
for k in 0 1 2 3; do python3 kl_sq.py render $((k*C)) $(( (k+1)*C )) $O/part$k.mp4 > $O/log$k.txt 2>&1 & echo "file 'part$k.mp4'" >> $O/list.txt; done
wait
ffmpeg -v error -y -f concat -safe 0 -i $O/list.txt -i "/mnt/project-files/الكلف جاهز.mp4" -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart "$1"
echo RENDERED "$1"
