#!/usr/bin/env python3
"""Render full episode scenes locally from the approved Teo artwork and voice cues.
The two appearances use original source pixels; the 3D-style pass is animated
illustration, not a newly modeled 3D character. No external video service.
"""
import sys, json, math, bisect, argparse, subprocess, time, hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/tools/video-python')
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from local_face import Face
cv2.setNumThreads(1)
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS=1280,720,24
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TITLES=['The Brain Team Challenge','Seeing the ball','Where are our hands?','Making sense of sound','Planning a movement','The movement team','Meet the tiny teammates','One catch. A whole team.']
CLUES=['A catch begins a mystery','Occipital · seeing','Parietal · touch and space','Temporal · sound','Frontal · planning','Cerebellum · coordination','Cells have different roles','Many parts work together']

def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def trans(x,y):return np.array([[1,0,x],[0,1,y],[0,0,1]],float)
def rot(deg,pivot):
 a=math.radians(deg);return trans(*pivot)@np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])@trans(-pivot[0],-pivot[1])
def scale_xy(sx,sy):return np.diag([sx,sy,1.])
def paste_warp(frame,rgba,bbox,matrix,clip_y=600):
 h,w=rgba.shape[:2];m=matrix@trans(bbox[0],bbox[1]);corn=m@np.array([[0,w,w,0],[0,0,h,h],[1,1,1,1]])
 x0=max(0,int(np.floor(corn[0].min()))-1);y0=max(0,int(np.floor(corn[1].min()))-1)
 x1=min(W,int(np.ceil(corn[0].max()))+1);y1=min(clip_y,int(np.ceil(corn[1].max()))+1)
 if x1<=x0 or y1<=y0:return
 mm=(trans(-x0,-y0)@m)[:2]
 warped=cv2.warpAffine(rgba,mm,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 alpha=warped[:,:,3:4].astype(np.float32)/255
 region=frame[y0:y1,x0:x1]
 region[:]=(warped[:,:,:3]*alpha+region*(1-alpha)).astype(np.uint8)

class Character:
 def __init__(self,style):
  self.style=style;self.dir=ROOT/'animation/rig-assets'/style;self.rig=json.loads((self.dir/'rig.json').read_text())
  self.layers={}
  for name in ['leg-left','leg-right','upper-body-no-head','head']:
   meta=self.rig['layers'][name];self.layers[name]=(np.asarray(Image.open(self.dir/meta['crop']).convert('RGBA')).copy(),meta)
  source=ROOT.parent.parent/'characters/teo/images'/f'teo-approved-{style}.png'
  self.face=Face(source,style)
  cut=np.asarray(Image.open(self.dir/'teo-cutout.png').convert('RGBA')).copy()
  self.neck_box=(448,225,552,330) if style=='2d' else (446,264,556,353)
  nx,ny,nr,nb=self.neck_box;self.neck=cut[ny:nb,nx:nr].copy()
 def draw(self,frame,t,shape,prev,blend,wide=False,walk=0,emphasis=0):
  # Camera staging. Full-body for short arrivals; waist-up for readable dialogue.
  sc=.32 if wide else .65;tx=232+walk*35;ty=111 if wide else 111-(32 if self.style=='3d' else 0)
  gait=math.sin(t*math.tau*1.15);bob=(abs(gait)*3 if walk else 0)+1.0*math.sin(t*2.0)
  global_m=trans(tx,ty-bob)@scale_xy(sc,sc)@trans(-480,0)
  lean=.35*math.sin(t*.72)+.3*emphasis
  body=rot(lean,(480,760))
  for name,sign in [('leg-left',1),('leg-right',-1)]:
   arr,meta=self.layers[name];angle=(2.6*gait*sign*walk if wide else .10*math.sin(t*.72))
   # Small heel lift and alternating steps maintain the supplied fixed view.
   lift=-max(0,gait*sign)*7*walk
   mat=global_m@trans(0,lift)@rot(angle,meta['pivot'])
   paste_warp(frame,arr,meta['bbox'],mat)
  arr,meta=self.layers['upper-body-no-head'];paste_warp(frame,arr,meta['bbox'],global_m@body)
  paste_warp(frame,self.neck,self.neck_box,global_m@body)
  arr,meta=self.layers['head']
  blinktime=(t+.8)%4.6;blink=math.sin(math.pi*blinktime/.20)**2 if blinktime<.20 else 0
  face=self.face.apply(arr,meta['bbox'],shape,prev,blend,blink)
  nod=.65*math.sin(t*1.6)+.4*emphasis
  paste_warp(frame,face,meta['bbox'],global_m@body@rot(nod,meta['pivot']))

class Composer:
 def __init__(self,style):
  self.style=style;self.character=Character(style)
  self.timeline=json.loads((ROOT/'audio/timeline.json').read_text());self.cues=self.timeline['cues']
  self.starts=[c['start_seconds'] for c in self.cues];self.lips={};self.pages={}
  for cue in self.cues:
   if cue.get('speaker')=='TEO':
    p=ROOT/'animation/lipsync/lines'/f"{cue['line_id']}.json"
    if p.exists():
     j=json.loads(p.read_text());a=j['mouthCues'];self.lips[cue['line_id']]=(a,[c['start'] for c in a])
  for i in range(8):self.pages[i+1]=self.make_page(i+1)
 def make_page(self,scene):
  im=Image.new('RGB',(W,H),(10,27,33));d=ImageDraw.Draw(im)
  d.rounded_rectangle((32,108,429,603),radius=23,fill=(248,239,225),outline=(57,88,88),width=2)
  # Quiet warm studio gradient behind the original character artwork.
  arr=np.asarray(im).copy();yy,xx=np.mgrid[110:601,34:428];light=np.exp(-(((xx-205)/310)**2+((yy-295)/450)**2))
  for ch,base in enumerate([239,228,212]):arr[110:601,34:428,ch]=(base+(255-base)*light*.45).astype(np.uint8)
  im=Image.fromarray(arr);d=ImageDraw.Draw(im)
  d.text((45,26),TITLES[scene-1],font=ImageFont.truetype(BOLD,37),fill=(240,233,215))
  d.text((47,75),CLUES[scene-1],font=ImageFont.truetype(FONT,20),fill=(151,184,180))
  d.rounded_rectangle((451,111,1251,602),radius=18,fill=(17,43,48),outline=(50,79,82),width=2)
  # Reserve the entire caption band; subtitles are applied once at assembly.
  d.rectangle((0,610,W,H),fill=(9,23,29));d.line((46,610,1234,610),fill=(43,69,72),width=1)
  return np.asarray(im).copy()
 def cue(self,t):
  idx=max(0,bisect.bisect_right(self.starts,t)-1);return self.cues[idx],idx
 def mouth(self,cue,t):
  line=cue.get('line_id');data=self.lips.get(line)
  if data is None:
   p=ROOT/'animation/lipsync/lines'/f'{line}.json'
   if not p.exists():raise FileNotFoundError(f'Missing actual voice mouth cues: {p}')
   a=json.loads(p.read_text())['mouthCues'];data=(a,[c['start'] for c in a]);self.lips[line]=data
  cues,starts=data;u=t-cue['start_seconds'];idx=max(0,bisect.bisect_right(starts,u)-1);c=cues[idx]
  if u>=c['end']+.03:return 'X','X',1
  previous=cues[idx-1]['value'] if idx else 'X'
  blend=smooth((u-c['start'])/.055)
  return c['value'],previous,blend
 def frame(self,diagram,scene,t,local_t):
  cue,idx=self.cue(t)
  speaking=cue.get('speaker')=='TEO' and t<cue['end_seconds']
  paused=cue['kind']=='viewer_pause'
  # Use the host with his actual recorded lines, plus quiet response holds.
  host=speaking or paused
  if not host:
   frame=diagram.copy()
   # Small voice label identifies offscreen intercom / representational cell guides.
   if cue.get('speaker'):
    names={'DANI':'Dani · intercom','NEURON_GUIDE':'Neuron guide','ASTROCYTE_GUIDE':'Astrocyte guide','MICROGLIA_GUIDE':'Microglia guide'}
    label=names.get(cue['speaker'],'')
    if label:
     img=Image.fromarray(frame);d=ImageDraw.Draw(img);ft=ImageFont.truetype(FONT,18);width=d.textlength(label,font=ft)+28
     d.rounded_rectangle((1240-width,105,1240,139),radius=11,fill=(26,53,57),outline=(71,99,100));d.text((1254-width,111),label,font=ft,fill=(224,220,201));frame=np.asarray(img).copy()
   return frame
  frame=self.pages[scene].copy()
  # Science panel advances continuously while the host speaks, never an eight-second loop.
  # Keep the full original labels and explanatory stages at a legible 800px width.
  small=cv2.resize(diagram[:605],(790,373),interpolation=cv2.INTER_AREA)
  frame[160:533,456:1246]=small
  # Label the panel and use an unobtrusive scene-progress line.
  cv2.line(frame,(476,570),(1225,570),(43,74,76),2,cv2.LINE_AA)
  scene_meta=self.timeline['scenes'][scene-1]
  progress=min(1,local_t/scene_meta['duration_seconds'])
  cv2.line(frame,(476,570),(476+int(749*progress),570),(183,156,100),2,cv2.LINE_AA)
  line_u=t-cue['start_seconds']
  # Two short in-place arrival steps use the existing whole-body artwork.
  walking=speaking and ('Come with me' in cue.get('text','') or (cue.get('line_id','').endswith('line-01') and scene in [1,2,4,5,8]))
  wide=walking and line_u<2.8
  walk=(smooth(line_u/.35)*smooth((2.8-line_u)/.45)) if wide else 0
  if wide:
   cv2.ellipse(frame,(232+int(walk*35),593),(94,8),0,0,360,(203,193,174),-1,cv2.LINE_AA)
  shape,prev,blend=self.mouth(cue,t) if speaking else ('X','X',1)
  # Audio-derived mouth poses coexist with restrained independent head/body acting.
  emphasis=.6*math.sin((line_u+.1)*4.4) if speaking else 0
  self.character.draw(frame,t,shape,prev,blend,wide,walk,emphasis)
  if paused:
   img=Image.fromarray(frame);d=ImageDraw.Draw(img)
   d.rounded_rectangle((669,118,1023,153),radius=14,fill=(54,79,78))
   d.text((846,135),'Your turn — think it through',font=ImageFont.truetype(FONT,18),fill=(239,228,200),anchor='mm')
   frame=np.asarray(img).copy()
   for k in range(3):
    col=(214,181,114) if line_u>=k else (81,101,98)
    cv2.circle(frame,(824+k*24,585),4,col,-1,cv2.LINE_AA)
  return frame

 def render(self,scene,duration=None,output=None):
  meta=self.timeline['scenes'][scene-1];start=meta['start_seconds'];dur=duration or meta['duration_seconds'];frames=math.ceil(dur*FPS)
  src=ROOT/'diagrams'/self.style/f'scene-{scene:02d}.mp4'
  if not src.exists():raise FileNotFoundError(src)
  cap=cv2.VideoCapture(str(src));cap.set(cv2.CAP_PROP_N_THREADS,1) if hasattr(cv2,'CAP_PROP_N_THREADS') else None
  out=Path(output) if output else ROOT/'animation/rendered'/self.style/f'scene-{scene:02d}.mp4';out.parent.mkdir(parents=True,exist_ok=True)
  tmp=out.with_name(out.stem+'.partial.mp4')
  proc=subprocess.Popen(['ffmpeg','-y','-v','error','-threads','1','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','1','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)],stdin=subprocess.PIPE)
  then=time.monotonic();prevframe=None
  for n in range(frames):
   ok,bgr=cap.read()
   if not ok:
    if prevframe is None:raise RuntimeError('Empty science video')
    diagram=prevframe
   else:diagram=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);prevframe=diagram
   frame=self.frame(diagram,scene,start+n/FPS,n/FPS)
   proc.stdin.write(frame.tobytes())
  proc.stdin.close();ret=proc.wait();cap.release()
  if ret:raise RuntimeError(f'ffmpeg failed {ret}')
  tmp.replace(out)
  receipt={'style':self.style,'scene_id':meta['scene_id'],'frames':frames,'fps':FPS,'duration_seconds':frames/FPS,'original_voice_start_seconds':start,'source_art_sha256':self.character.rig['source_sha256'],'mouth_timing_method':'Rhubarb per-line recorded audio plus exact transcript; 55ms pose blending','body_motion':'Original pixel cutout with limited articulated steps, head/body weight shifts, breathing and blinking','render_seconds':round(time.monotonic()-then,2),'status':'rendered locally; visual review required','external_video_service_calls':0}
  out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'output':str(out),**receipt}),flush=True)
  return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--style',choices=['2d','3d','both'],default='both');p.add_argument('--scene',default='all');p.add_argument('--duration',type=float);p.add_argument('--output');p.add_argument('--still',type=float);args=p.parse_args()
 for style in (['2d','3d'] if args.style=='both' else [args.style]):
  c=Composer(style)
  for scene in (range(1,9) if args.scene=='all' else [int(args.scene)]):
   if args.still is not None:
    m=c.timeline['scenes'][scene-1];cap=cv2.VideoCapture(str(ROOT/'diagrams'/style/f'scene-{scene:02d}.mp4'));cap.set(cv2.CAP_PROP_POS_MSEC,args.still*1000);ok,bgr=cap.read();cap.release()
    if not ok:raise RuntimeError('Cannot read preview')
    frame=c.frame(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),scene,m['start_seconds']+args.still,args.still);out=Path(args.output or ROOT/'animation/previews'/f'local-{style}-{scene:02d}.jpg');Image.fromarray(frame).save(out,quality=94);print(out)
   else:c.render(scene,args.duration,args.output)
