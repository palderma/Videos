#!/bin/bash
# full render: 4 parallel chunks -> concat -> mux with the final mix
cd /home/user/klf; O=/home/user/klf/render4; mkdir -p $O; rm -f $O/*.mp4 $O/list.txt
N=$(python3 -c "import kl4_edit as E; print(int(round(E.DUR*30)))"); P=4; C=$(( (N + P - 1) / P ))
for k in $(seq 0 $((P-1))); do python3 kl4_render.py $((k*C)) $(( (k+1)*C < N ? (k+1)*C : N )) $O/part$k.mp4 > $O/log$k.txt 2>&1 & echo "file 'part$k.mp4'" >> $O/list.txt; done
wait
ffmpeg -v error -y -f concat -safe 0 -i $O/list.txt -i /home/user/klf/pkg4/audio/mix_final.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$1"
echo RENDERED "$1"
