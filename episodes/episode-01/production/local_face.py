"""Local facial animation of approved source pixels for the episode videos.
Original images are never written. Lip poses are derivative performance shapes.
"""
import sys, math
sys.path.insert(0, '/workspace/tools/video-python')
import cv2
import numpy as np
from PIL import Image
cv2.setNumThreads(1)

CONFIG={
 '2d':{'mouth':(469,178),'angle':-13,'eyes':[(431,136,18,9,-14),(488,123,18,10,-14)]},
 '3d':{'mouth':(470,220),'angle':-14,'eyes':[(436,181,16,9,-12),(488,168,17,10,-14)]},
}
# width, opening, tooth fraction, tongue fraction
POSES={'X':(47,0,0,0),'A':(42,0,0,0),'B':(41,6,.40,0),'C':(39,14,.22,.13),'D':(39,21,.18,.17),
       'E':(29,15,.08,.09),'F':(20,12,0,0),'G':(36,5,.70,0),'H':(36,13,.25,.31)}

class Face:
 def __init__(self,source,style):
  self.original=np.asarray(Image.open(source).convert('RGB')).copy()
  self.c=CONFIG[style]; self.style=style
  cx,cy=self.c['mouth'];self.box=(cx-42,cy-30,cx+43,cy+35)
  x0,y0,x1,y1=self.box;patch=self.original[y0:y1,x0:x1].copy()
  mask=np.zeros(patch.shape[:2],np.uint8)
  cv2.ellipse(mask,(cx-x0,cy-y0),(29,10),self.c['angle'],0,360,255,-1,cv2.LINE_AA)
  self.clean=cv2.inpaint(patch,mask,5,cv2.INPAINT_TELEA)
  self.neutral=patch
  self.mouths={k:self.make_mouth(k) for k in POSES}
  self.eye_patches=[]
  for ex,ey,rx,ry,angle in self.c['eyes']:
   box=(ex-rx-8,ey-ry-7,ex+rx+9,ey+ry+8);xx,yy,xe,ye=box
   p=self.original[yy:ye,xx:xe].copy();m=np.zeros(p.shape[:2],np.uint8)
   cv2.ellipse(m,(ex-xx,ey-yy),(rx+1,ry),angle,0,360,255,-1,cv2.LINE_AA)
   cleaned=cv2.inpaint(p,m,5,cv2.INPAINT_TELEA)
   pts=[]
   for u in np.linspace(-1,1,25):
    px=u*rx;py=2.7*(1-u*u)
    a=math.radians(angle);pts.append((int(ex-xx+px*math.cos(a)-py*math.sin(a)),int(ey-yy+px*math.sin(a)+py*math.cos(a))))
   cv2.polylines(cleaned,[np.array(pts,np.int32)],False,(68,40,28),2,cv2.LINE_AA)
   self.eye_patches.append((box,p,cleaned))
 def make_mouth(self,key):
  if key in ('X','A'):return self.neutral.copy()
  w,h,tooth,tongue=POSES[key];S=4
  patch=cv2.resize(self.clean,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
  cx=(self.c['mouth'][0]-self.box[0])*S;cy=(self.c['mouth'][1]-self.box[1])*S
  # Asymmetric curved lips retain the source portrait's upward corner and tilt.
  shape=np.zeros(patch.shape[:2],np.uint8)
  angle=math.radians(self.c['angle'])
  pts=[]
  for a in np.linspace(0,2*math.pi,90):
   x=w*S*.5*math.cos(a);y=h*S*.5*math.sin(a)+.10*h*S
   pts.append((round(cx+x*math.cos(angle)-y*math.sin(angle)),round(cy+x*math.sin(angle)+y*math.cos(angle))))
  poly=np.array(pts,np.int32)
  cv2.fillPoly(shape,[poly],255,cv2.LINE_AA)
  interior=np.zeros_like(patch);interior[:]=(57,29,26) if self.style=='2d' else (69,34,29)
  # Tiny teeth band, never a new broad grin. Only visible for relevant phonemes.
  yy,xx=np.mgrid[:shape.shape[0],:shape.shape[1]]
  localy=-(xx-cx)*math.sin(angle)+(yy-cy)*math.cos(angle)
  if tooth:
   band=(shape>0)&(localy<(-h*.5+h*tooth+.10*h)*S)
   interior[band]=(226,214,191)
  if tongue:
   band=(shape>0)&(localy>(h*.5-h*tongue+.10*h)*S)
   interior[band]=(157,77,67)
  alpha=shape.astype(np.float32)[...,None]/255
  patch=(patch*(1-alpha)+interior*alpha).astype(np.uint8)
  cv2.polylines(patch,[poly],True,(113,61,43) if self.style=='2d' else (126,72,50),S,cv2.LINE_AA)
  return cv2.resize(patch,(self.box[2]-self.box[0],self.box[3]-self.box[1]),interpolation=cv2.INTER_AREA)
 def apply(self,rgba,bbox,shape='X',previous=None,blend=1.0,blink=0):
  # Layer bbox is in original source coordinates.
  bx,by=bbox[:2]
  result=rgba.copy()
  patch=self.mouths.get(shape,self.neutral)
  if previous and blend<1:patch=cv2.addWeighted(self.mouths.get(previous,self.neutral),1-blend,patch,blend,0)
  x0,y0,x1,y1=self.box
  if x0>=bx and y0>=by and x1<=bx+result.shape[1] and y1<=by+result.shape[0]:
   result[y0-by:y1-by,x0-bx:x1-bx,:3]=patch
  if blink>0:
   for box,orig,closed in self.eye_patches:
    x0,y0,x1,y1=box
    if x0>=bx and y0>=by and x1<=bx+result.shape[1] and y1<=by+result.shape[0]:result[y0-by:y1-by,x0-bx:x1-bx,:3]=cv2.addWeighted(orig,1-blink,closed,blink,0)
  return result

if __name__=='__main__':
 from pathlib import Path
 from PIL import ImageDraw
 root=Path(__file__).resolve().parents[1]
 for style in CONFIG:
  src=root.parent.parent/'characters/teo/images'/f'teo-approved-{style}.png'
  f=Face(src,style);canvas=Image.new('RGB',(6*260,2*250),'#f8f0e6')
  for i,k in enumerate(['X','B','C','D','E','F','G','H']):
   arr=np.dstack([f.original.copy(),np.full(f.original.shape[:2],255,np.uint8)])
   arr=f.apply(arr,(0,0,1024,1536),k,blink=1 if i==7 else 0)
   crop=Image.fromarray(arr).crop((350,70 if style=='2d' else 100,610,320 if style=='2d' else 350)).convert('RGB')
   canvas.paste(crop,((i%6)*260,(i//6)*250));ImageDraw.Draw(canvas).text(((i%6)*260+5,(i//6)*250+225),k,fill='black')
  out=root/'animation/previews'/f'visemes-{style}.jpg';canvas.save(out,quality=92);print(out)
