import time, numpy as np, cv2
from PIL import Image
import ice_fx as I
A="/mnt/project-files/style-guide/assets/templates/"
bg=np.array(Image.open(A+"خلفية-عنابي-9x16.png").convert("RGB"),np.float32)
fr=np.array(Image.open(A+"frame-9x16.png").convert("RGBA"),np.float32)
C=bg*(1-fr[...,3:]/255)+fr[...,:3]*fr[...,3:]/255
C8=C.astype(np.uint8); cv2.putText(C8,"TEST CONTENT",(200,1000),cv2.FONT_HERSHEY_SIMPLEX,3,(255,255,255),8,cv2.LINE_AA); C=C8.astype(np.float32)
EVS=[I.Ev("melt",2.9,4.4,1,origins=[(540,1000,1.0)],crack_at=2.55,crack_origin=(540,1000)),
     I.Ev("freeze",6.9,7.7,2)]
outs=[]
for t in [1.0,2.75,3.3,3.7,4.1,4.6,7.2,7.5]:
    t0=time.time(); o=I.render(C,None,t,EVS,glint=lambda t:(t-0.9)*2200); print(t,round(time.time()-t0,2))
    outs.append(cv2.resize(o,(360,640)))
s=np.hstack(outs[:4]); s2=np.hstack(outs[4:]); Image.fromarray(np.vstack([s,s2]).astype(np.uint8)).save("work/t1.png")
Image.fromarray(o.astype(np.uint8)).save("work/full.png")
o=I.render(C,None,3.5,EVS); Image.fromarray(o[700:1300,200:900].astype(np.uint8)).save("work/crop.png")
