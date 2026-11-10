import cv2, numpy as np, json
F="/mnt/project-files/بوتوكس الرجال.mp4"
cap=cv2.VideoCapture(F); cc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
out=[];i=0
while True:
    ok,f=cap.read()
    if not ok: break
    if f.shape[0]!=1920: f=cv2.rotate(f,cv2.ROTATE_90_CLOCKWISE)
    if i%5==0:
        g=cv2.cvtColor(cv2.resize(f,(540,960)),cv2.COLOR_BGR2GRAY)
        fs=cc.detectMultiScale(g,1.1,5,minSize=(60,60))
        if len(fs):
            x,y,w,h=max(fs,key=lambda r:r[2]*r[3]); out.append((i/30,float(x+w/2)*2,float(y+h/2)*2,float(w)*2))
    i+=1
json.dump(out,open('face.json','w'))
print(i); json.dump(out,open('face.json','w'))
a=np.array(out); print(len(a)); 
for t in range(0,31,3):
    m=a[(a[:,0]>=t)&(a[:,0]<t+3)]
    if len(m): print(t, m[:,1].mean().round(), m[:,2].mean().round(), m[:,3].mean().round())
