import sys
from PIL import Image
a,b,step,out=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
crop=(0,500,1080,1500) if len(sys.argv)<6 else tuple(int(x) for x in sys.argv[5].split(','))
fr=list(range(int(a*30),int(b*30)+1,step))[:16]
w=(crop[2]-crop[0])//3; h=(crop[3]-crop[1])//3
S=Image.new('RGB',(w*4,h*((len(fr)+3)//4)))
for i,f in enumerate(fr):
    im=Image.open('/home/user/gb/work/frames/%05d.png'%f).crop(crop).resize((w,h))
    S.paste(im,((i%4)*w,(i//4)*h))
S.save(out); print(fr)
