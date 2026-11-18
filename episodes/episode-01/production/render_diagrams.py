#!/usr/bin/env python3
"""Original animated teaching diagrams for The Brain Team Challenge.

No Teo or other supplied image is read, edited, or redrawn here. Shapes are
original, explicitly simplified teaching diagrams. Front is left in all brain
side views. The lower 110 pixels are reserved for downstream subtitles.

Usage:
  python render_diagrams.py --scene all --style both --duration 8 --preview
  python render_diagrams.py --scene all --style both --timeline ../audio/timeline.json
  python render_diagrams.py --scene 6 --style 3d --duration 75 --output clip.mp4
  python render_diagrams.py --scene all --style both --frames-only

API: render_scene(scene_index, style, duration, path, timeline=None, fps=24).
Full-duration clips begin at scene time zero. With a timeline, visual stages
follow spoken line starts and action beats, never a repeated eight-second loop.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1280, 720, 24
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'diagrams'
FONT_REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
P = {
    'ink': (239, 234, 219), 'muted': (155, 182, 179), 'line': (55, 82, 85),
    'frontal': (191, 120, 105), 'parietal': (193, 164, 105),
    'temporal': (103, 157, 143), 'occipital': (112, 151, 179),
    'cerebellum': (157, 139, 172), 'signal': (222, 186, 119),
    'feedback': (128, 192, 183), 'panel': (17, 43, 48),
}
TITLES = [
    'The brain team challenge', 'Seeing the ball', 'Where are our hands?',
    'Making sense of sound', 'Planning a movement', 'The movement team',
    'Meet the tiny teammates', 'One catch. A whole team.',
]
SUBTITLES = [
    'A gentle catch starts a big question', 'A tour of the occipital lobe',
    'A tour of the parietal lobe', 'A tour of the temporal lobe',
    'A tour of the frontal lobe', 'Cerebellum, spinal cord, nerves, and muscles',
    'Enlarged cell models · Guide programs, not talking cells',
    'Many brain regions and the body cooperate',
]
# Line numbers at which the three visual stages begin.
STAGE_LINES = {1:[1,4,6], 2:[1,2,4], 3:[1,2,4], 4:[1,3,5],
               5:[1,2,7], 6:[1,4,5], 7:[3,5,6], 8:[1,4,6]}

@lru_cache(None)
def font(size=26, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def mix(a,b,t): return tuple(round(x*(1-t)+y*t) for x,y in zip(a,b))
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease(x): x=clamp(x); return x*x*(3-2*x)
def lerp(a,b,u): return a+(b-a)*u

def text(draw, xy, value, size=26, color=None, bold=False, anchor=None):
    draw.text(xy, value, font=font(size,bold), fill=color or P['ink'], anchor=anchor)

def paragraph(draw, xy, lines, size=23, gap=33, color=None):
    for i,line in enumerate(lines): text(draw,(xy[0],xy[1]+i*gap),line,size,color)

def pill(draw, box, value, color=None, size=20):
    color=color or P['muted']
    draw.rounded_rectangle(box, radius=15, fill=(25,52,56), outline=mix(color,(20,42,46),.45), width=1)
    text(draw,((box[0]+box[2])/2,(box[1]+box[3])/2),value,size,color,anchor='mm')

def smooth_closed(points, samples=12):
    result=[]; n=len(points)
    for i in range(n):
        p0,p1,p2,p3=[np.array(points[j%n],dtype=float) for j in (i-1,i,i+1,i+2)]
        for j in range(samples):
            t=j/samples
            q=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            result.append(tuple(q))
    return result

def cubic(points, samples=42):
    a,b,c,d=[np.array(x,dtype=float) for x in points]
    return [tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in np.linspace(0,1,samples)]

def line_path(draw, pts, fill, width=3):
    draw.line(pts,fill=fill,width=width,joint='curve')

def arrow(draw,a,b,color,width=3,head=9):
    draw.line((a,b),fill=color,width=width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0])
    ends=[(b[0]-head*math.cos(ang+x),b[1]-head*math.sin(ang+x)) for x in (-.5,.5)]
    draw.polygon([b,*ends],fill=color)

def pulse_on_path(draw,pts,t,color,r=5,offset=0,speed=.12):
    u=(t*speed+offset)%1
    idx=min(len(pts)-1,int(u*(len(pts)-1)))
    x,y=pts[idx]
    draw.ellipse((x-r-4,y-r-4,x+r+4,y+r+4),fill=mix(color,(17,43,48),.60))
    draw.ellipse((x-r,y-r,x+r,y+r),fill=color)

@lru_cache(None)
def background(style):
    yy,xx=np.mgrid[:H,:W]
    glow=np.exp(-(((xx-500)/820)**2+((yy-270)/520)**2))
    base=np.zeros((H,W,3),dtype=np.uint8)
    for ch,(lo,hi) in enumerate(((8,18),(23,43),(29,48))): base[:,:,ch]=lo+(hi-lo)*glow
    im=Image.fromarray(base,'RGB'); d=ImageDraw.Draw(im)
    for x in range(40,W,48): d.line((x,175,x,595),fill=(24,44,49),width=1)
    for y in range(190,596,48): d.line((50,y,1230,y),fill=(24,44,49),width=1)
    d.line((54,601,1226,601),fill=(39,64,68),width=1)
    # Subtitle region is intentionally free of diagram objects and labels.
    return im

OUTLINE=[(.10,.64),(.025,.50),(.02,.35),(.08,.20),(.21,.075),(.4,.025),(.63,.025),(.82,.09),(.95,.23),(.99,.43),(.96,.60),(.89,.71),(.79,.76),(.69,.83),(.51,.87),(.31,.84),(.16,.74)]
LOBES={
 'frontal':[(-.2,-.2),(.53,-.2),(.52,.19),(.48,.38),(.40,.51),(.49,.60),(.35,.65),(.09,.61),(-.2,.59)],
 'parietal':[(.53,-.2),(.86,-.2),(.84,.17),(.80,.37),(.73,.55),(.49,.60),(.40,.51),(.48,.38),(.52,.19)],
 'occipital':[(.86,-.2),(1.2,-.2),(1.2,.95),(.83,.80),(.73,.55),(.80,.37),(.84,.17)],
 'temporal':[(.09,.61),(.35,.65),(.49,.60),(.73,.55),(.83,.80),(.72,1.0),(.25,1.0),(.09,.80)],
}
CENTERS={'frontal':(.24,.34),'parietal':(.64,.29),'temporal':(.48,.72),'occipital':(.89,.45),'cerebellum':(.81,.99)}
FOLDS=[[(.12,.40),(.19,.31),(.18,.21),(.29,.19)],[(.12,.51),(.21,.44),(.26,.48),(.32,.38)],
       [(.28,.10),(.33,.20),(.31,.30),(.40,.31)],[(.41,.12),(.47,.17),(.40,.23),(.43,.31)],
       [(.56,.13),(.63,.19),(.61,.26),(.69,.30)],[(.69,.12),(.77,.14),(.72,.24),(.76,.31)],
       [(.58,.39),(.62,.48),(.68,.44),(.71,.48)],[(.83,.28),(.90,.32),(.85,.41),(.93,.45)],
       [(.82,.53),(.91,.55),(.84,.63),(.87,.67)],[(.28,.70),(.37,.66),(.42,.77),(.50,.74)],
       [(.51,.66),(.59,.76),(.68,.66),(.72,.74)]]

def shaded_fill(mask,color,style):
    mw,mh=mask.size
    if style=='2d': return Image.new('RGB',(mw,mh),color)
    yy,xx=np.mgrid[:mh,:mw]
    z=np.sqrt(np.maximum(0,1-((xx-mw*.44)/(mw*.66))**2-((yy-mh*.38)/(mh*.62))**2))
    light=.63+.36*z+.16*(1-yy/mh)-.08*xx/mw
    arr=np.clip(np.array(color)[None,None,:]*light[:,:,None],0,255).astype('uint8')
    return Image.fromarray(arr,'RGB')

@lru_cache(maxsize=40)
def brain_layer(style,focus,width=605,height=315):
    # Layer coordinates include stem and cerebellum; cerebrum is height*.78.
    im=Image.new('RGBA',(width+30,height+115),(0,0,0,0))
    cw,ch=width,height
    xy=lambda q:(q[0]*cw+12,q[1]*ch+9)
    outline=[xy(q) for q in smooth_closed(OUTLINE)]
    mask=Image.new('L',im.size,0); md=ImageDraw.Draw(mask);md.polygon(outline,fill=255)
    shadow=mask.filter(ImageFilter.GaussianBlur(11))
    sh=Image.new('RGBA',im.size,(0,0,0,0));sh.putalpha(shadow.point(lambda v:int(v*.45)))
    im.alpha_composite(sh,(4,8))
    for name,poly in LOBES.items():
        lm=Image.new('L',im.size,0);ld=ImageDraw.Draw(lm);ld.polygon([xy(q) for q in poly],fill=255)
        lm=Image.fromarray(np.minimum(np.asarray(lm),np.asarray(mask)))
        color=P[name] if focus in ('all',name) else mix(P[name],(25,53,58),.61)
        fill=shaded_fill(lm,color,style).convert('RGBA');fill.putalpha(lm);im.alpha_composite(fill)
    d=ImageDraw.Draw(im)
    d.line(outline+[outline[0]],fill=(186,204,195,220),width=3,joint='curve')
    for name,poly in LOBES.items():
        ld=Image.new('RGBA',im.size,(0,0,0,0));pd=ImageDraw.Draw(ld)
        pd.line([xy(q) for q in poly+[poly[0]]],fill=(29,61,65,240),width=3,joint='curve')
        alpha=np.minimum(np.asarray(ld.getchannel('A')),np.asarray(mask));ld.putalpha(Image.fromarray(alpha));im.alpha_composite(ld)
    d=ImageDraw.Draw(im)
    for fold in FOLDS:
        line_path(d,cubic([xy(q) for q in fold]),(22,52,57,120),3)
    # Brainstem is anterior (left) of the lower posterior cerebellum.
    stem=[xy(q) for q in [(.60,.79),(.68,.81),(.69,.98),(.65,1.16),(.61,1.20),(.59,1.11),(.62,.94)]]
    d.polygon(stem,fill=(130,156,148,255),outline=(43,73,74,255))
    d.line([xy((.632,1.14)),xy((.632,1.23))],fill=(163,185,167,255),width=11)
    cb=[xy(q) for q in smooth_closed([(.67,.88),(.76,.82),(.9,.86),(.97,.96),(.93,1.1),(.80,1.14),(.68,1.06)])]
    cm=Image.new('L',im.size,0);ImageDraw.Draw(cm).polygon(cb,fill=255)
    cc=P['cerebellum'] if focus in ('all','cerebellum') else mix(P['cerebellum'],(25,53,58),.56)
    cf=shaded_fill(cm,cc,style).convert('RGBA');cf.putalpha(cm);im.alpha_composite(cf)
    d=ImageDraw.Draw(im);d.line(cb+[cb[0]],fill=(111,131,143,255),width=2)
    for i in range(5):
        y=.9+i*.045
        pts=cubic([xy((.71,y)),xy((.78,y-.045)),xy((.88,y+.03)),xy((.92,y+.025))])
        line_path(d,pts,(60,71,88,190),2)
    return im

def draw_brain(im, t, style, focus='all', pos=(85,208), scale=.95, network=True, label=True):
    layer=brain_layer(style,focus)
    if scale!=1: layer=layer.resize((round(layer.width*scale),round(layer.height*scale)),Image.Resampling.LANCZOS)
    im.paste(layer,pos,layer)
    d=ImageDraw.Draw(im)
    def p(q):return (pos[0]+(q[0]*605+12)*scale,pos[1]+(q[1]*315+9)*scale)
    if network:
        # Simultaneous, crossing, bidirectional-looking routes, not a four-lobe chain.
        routes=[('frontal','parietal',.0),('parietal','temporal',.38),('temporal','occipital',.71),('occipital','frontal',.21),('frontal','cerebellum',.56)]
        for a,b,offset in routes:
            pa,pb=p(CENTERS[a]),p(CENTERS[b]);bend=(pa[0]+pb[0])/2
            pts=cubic([pa,(bend,pa[1]-35*scale),(bend,pb[1]+20*scale),pb])
            line_path(d,pts,(84,112,110),2)
            pulse_on_path(d,pts,t,P['signal'] if focus=='all' else (158,180,160),r=3,offset=offset,speed=.08)
    if label:
        text(d,p((.05,-.10)),'FRONT',17,P['muted'],True)
        text(d,p((.84,-.10)),'BACK',17,P['muted'],True)
    return p

def highlight_label(im,p,focus):
    d=ImageDraw.Draw(im)
    labels={'frontal':((.18,.33),'Frontal'), 'parietal':((.59,.28),'Parietal'), 'temporal':((.44,.73),'Temporal'), 'occipital':((.86,.44),'Occipital'),'cerebellum':((.81,.99),'Cerebellum')}
    if focus in labels:
        q,name=labels[focus]; x,y=p(q)
        tw=d.textbbox((0,0),name,font=font(24,True))[2]
        d.rounded_rectangle((x-tw/2-11,y-19,x+tw/2+11,y+20),radius=8,fill=(14,38,44),outline=P[focus],width=2)
        text(d,(x,y),name,24,bold=True,anchor='mm')

def panel(im,title,sub=None):
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((803,205,1225,575),radius=26,fill=P['panel'],outline=(54,83,85),width=2)
    text(d,(831,227),title,27,bold=True)
    if sub: text(d,(831,267),sub,20,P['muted'])
    return d

def draw_ball(im,x,y,r=27,style='2d',color=None):
    color=color or P['signal'];d=ImageDraw.Draw(im)
    d.ellipse((x-r,y-r,x+r,y+r),fill=color,outline=mix(color,(245,240,224),.35),width=2)
    if style=='3d':
        for i in range(6,0,-1):
            rr=r*i/7;cx=x-r*.22;cy=y-r*.25
            d.ellipse((cx-rr*.65,cy-rr*.65,cx+rr*.65,cy+rr*.65),fill=mix(color,(250,237,206),.10+(7-i)*.045))
    d.arc((x-r*.72,y-r*.9,x+r*.72,y+r*.9),78,272,fill=mix(color,(75,68,47),.3),width=2)

def hand(im,x,y,flip=False,style='2d',size=1):
    # Abstract mitten-like catching hand: not Teo, no supplied imagery.
    pts=[(-42,52),(-40,2),(-31,-26),(-20,-32),(-14,-22),(-16,3),(-6,-35),(5,-38),(13,-29),(13,-1),(24,-24),(34,-23),(39,-12),(31,15),(47,-4),(56,1),(56,13),(39,42),(22,57),(23,83),(-28,84)]
    s=-1 if flip else 1
    coords=[(x+s*a*size,y+b*size) for a,b in smooth_closed(pts,5)]
    d=ImageDraw.Draw(im);col=(164,192,181)
    if style=='3d':d.polygon([(a+5,b+7) for a,b in coords],fill=(8,27,32))
    d.polygon(coords,fill=col,outline=(207,218,203))
    d.line([(x+s*-12*size,y+19*size),(x+s*4*size,y+33*size),(x+s*23*size,y+35*size)],fill=(93,130,123),width=2)

def catch_inset(im,t,style,stage=0,small=False,progress=None):
    d=ImageDraw.Draw(im)
    cx=1012; base=444
    # One narrated demonstration progresses and holds; never repeat a catch as filler.
    u=clamp(progress) if progress is not None else clamp(t/5)
    gap=lerp(85,38,ease(u)) if stage>0 else 85
    hand(im,cx-gap,base,False,style,.62)
    hand(im,cx+gap,base,True,style,.62)
    y=lerp(322,425,ease(u))
    if stage==0 and u>.72:y=lerp(425,545,(u-.72)/.28)
    draw_ball(im,cx,y,23,style)
    if stage==0:
        arrow(d,(cx-51,494),(cx+51,494),P['muted'],2,7)
        text(d,(cx,525),'Notice the gap',21,P['muted'],anchor='mm')
    else:
        text(d,(cx,535),'Hands meet the ball',21,P['muted'],anchor='mm')

def eye(im,cx,cy,style):
    d=ImageDraw.Draw(im)
    pts=smooth_closed([(cx-67,cy),(cx-31,cy-30),(cx+23,cy-31),(cx+67,cy),(cx+26,cy+30),(cx-26,cy+30)])
    d.polygon(pts,fill=(224,228,214),outline=(126,164,163))
    d.ellipse((cx-23,cy-23,cx+23,cy+23),fill=(95,149,153),outline=(15,47,55),width=2)
    d.ellipse((cx-10,cy-14,cx+10,cy+14),fill=(15,38,45))
    d.ellipse((cx-8,cy-14,cx-1,cy-7),fill=(244,241,227))

def draw_body(im,t,style,panel_mode=True):
    d=ImageDraw.Draw(im);cx=1012;top=358
    # Diagram body, not a character likeness. Spine, nerves, muscle and return route are distinct.
    d.ellipse((cx-24,top-58,cx+24,top-10),outline=(147,175,167),width=3)
    d.line((cx,top-10,cx,top+98),fill=(87,124,122),width=30)
    d.line((cx-55,top+6,cx+55,top+6),fill=(87,124,122),width=22)
    d.line([(cx-53,top+10),(cx-77,top+60),(cx-94,top+100)],fill=(87,124,122),width=20)
    d.line([(cx+53,top+10),(cx+77,top+60),(cx+94,top+100)],fill=(87,124,122),width=20)
    d.line((cx,top-9,cx,top+94),fill=P['signal'],width=5)
    for sign in (-1,1):
        pts=cubic([(cx,top+6),(cx+sign*57,top+4),(cx+sign*66,top+70),(cx+sign*94,top+100)])
        line_path(d,pts,P['signal'],3);pulse_on_path(d,pts,t,P['signal'],3,offset=0 if sign==1 else .44,speed=.18)
        back=[(x+sign*8,y+8) for x,y in pts][::-1]
        line_path(d,back,P['feedback'],2);pulse_on_path(d,back,t,P['feedback'],3,offset=.3,speed=.15)
    d.ellipse((cx+59,top+25,cx+78,top+64),outline=P['ink'],width=2)
    text(d,(842,475),'Movement signals',20,P['signal'])
    text(d,(842,508),'Body information returns',20,P['feedback'])
    text(d,(842,543),'Spinal cord · Nerves · Muscles',19,P['muted'])

def branched_cell(draw,cx,cy,color,kind='astrocyte',scale=1,style='2d'):
    count=11 if kind=='astrocyte' else 7
    radius=23 if kind=='astrocyte' else 16
    for i in range(count):
        a=2*math.pi*i/count+.17
        length=(61+(i*17)%29)*scale
        elbow=(cx+math.cos(a)*length*.55,cy+math.sin(a)*length*.55)
        tip=(cx+math.cos(a+.12)*length,cy+math.sin(a+.12)*length)
        width=5 if kind=='astrocyte' else 3
        draw.line([(cx,cy),elbow,tip],fill=color,width=width,joint='curve')
        for side in (-1,1):
            end=(elbow[0]+math.cos(a+side*.65)*length*.4,elbow[1]+math.sin(a+side*.65)*length*.4)
            draw.line([elbow,end],fill=color,width=max(2,width-2))
    if style=='3d':draw.ellipse((cx-radius-4,cy-radius+3,cx+radius+3,cy+radius+10),fill=(6,23,27))
    draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=color,outline=mix(color,P['ink'],.28),width=2)
    draw.ellipse((cx-8,cy-8,cx+8,cy+8),fill=mix(color,(20,47,51),.30))

def cells_scene(im,t,style,stage,progress):
    d=ImageDraw.Draw(im)
    names=['Neuron','Astrocyte','Microglia'];colors=[P['signal'],P['temporal'],P['cerebellum']]
    xs=[248,640,1032]
    for i,(x,name,c) in enumerate(zip(xs,names,colors)):
        active=i<=stage
        d.rounded_rectangle((x-180,208,x+180,574),radius=25,fill=P['panel'],outline=c if active else P['line'],width=2)
        text(d,(x,241),name,29,c if active else P['muted'],True,anchor='mm')
    # Neuron cell body, dendrites, a long axon, and visible synaptic gap.
    x,y=183,364;c=colors[0]
    branched_cell(d,x,y,c,'microglia',.65,style)
    axon=cubic([(x+16,y),(x+65,y-33),(x+73,y+38),(x+125,y+19)])
    line_path(d,axon,c,5)
    pulse_on_path(d,axon,t,P['ink'],4,speed=.25)
    d.ellipse((x+128,y+10,x+143,y+25),fill=c)
    d.line((x+154,y-10,x+154,y+42),fill=P['temporal'],width=5)
    for j in range(3):
        u=(t*.25+j*.27)%1
        xx=lerp(x+144,x+151,u);yy=y+17+(j-1)*8
        d.ellipse((xx-2,yy-2,xx+2,yy+2),fill=P['ink'])
    paragraph(d,(94,480),['Electrical + chemical','signals'],22,31)
    # Astrocyte many irregular branches; no five-point-star mascot.
    c=colors[1] if stage>=1 else mix(colors[1],P['panel'],.6)
    branched_cell(d,640,365,c,'astrocyte',.85,style)
    if stage>=1:
        for j in range(4):
            a=j*1.5+t*.12;x=640+math.cos(a)*93;y=365+math.sin(a)*75
            d.ellipse((x-5,y-5,x+5,y+5),fill=mix(c,P['ink'],.35))
    paragraph(d,(487,480),['Supports neurons','and their surroundings'],22,31)
    # Microglial cell approaches cellular debris in a separate inset.
    c=colors[2] if stage>=2 else mix(colors[2],P['panel'],.6)
    branched_cell(d,1006,361,c,'microglia',.76,style)
    if stage>=2:
        # One gradual approach/engulf sequence followed by a stable contextual view.
        u=ease(clamp((progress-.62)/.3))
        for j,(dy,r) in enumerate([(-11,6),(8,8),(24,5)]):
            xx=lerp(1134,1020,u);yy=lerp(360+dy,361+dy*.12,u)
            if u<.98:d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(183,155,126))
        if u>.75:d.ellipse((1001,355,1011,365),outline=P['ink'],width=2)
    paragraph(d,(878,480),['Immune support','Clears cellular debris'],22,31)


def stage_info(scene,t,duration,timeline=None):
    progress=clamp(t/max(duration,1e-6))
    default=[0,.28,.62]
    thresholds=default
    scene_data=None
    if timeline:
        sid=f'scene-{scene:02d}'
        scene_data=next((s for s in timeline.get('scenes',[]) if s.get('scene_id',s.get('id'))==sid),None)
        if scene_data:
            origin=scene_data['start_seconds']
            starts={c.get('line_id'):c['start_seconds']-origin for c in timeline.get('cues',[]) if c.get('scene_id')==sid and c.get('kind')=='dialogue'}
            thresholds=[starts.get(f'{sid}-line-{n:02d}',default[i]*duration)/duration for i,n in enumerate(STAGE_LINES[scene])]
            thresholds[0]=0
    stage=0
    for i,thr in enumerate(thresholds):
        if progress>=thr:stage=i
    return stage,progress


def render_frame(scene_index,style,t,duration,timeline=None):
    if not 1<=scene_index<=8:raise ValueError('scene_index must be 1–8')
    if style not in ('2d','3d'):raise ValueError('style must be 2d or 3d')
    im=background(style).copy();d=ImageDraw.Draw(im)
    text(d,(56,33),'SIMULATION  /  SIMPLIFIED MODEL',18,P['muted'],True)
    text(d,(56,70),TITLES[scene_index-1],42,bold=True)
    text(d,(57,131),SUBTITLES[scene_index-1],23,P['muted'])
    text(d,(1218,42),f'{scene_index:02d} / 08',19,P['muted'],anchor='ra')
    stage,progress=stage_info(scene_index,t,duration,timeline)
    if scene_index==7:
        cells_scene(im,t,style,stage,progress)
        return im
    focus={1:'all',2:'occipital',3:'parietal',4:'temporal',5:'frontal',6:'cerebellum',8:'all'}[scene_index]
    p=draw_brain(im,t,style,focus,pos=(81,224),scale=.93,network=True)
    highlight_label(im,p,focus)
    d=ImageDraw.Draw(im)
    if scene_index in (1,8):
        panel(im,'The gentle catch','Notice hands, ball, and space')
        catch_progress=clamp(progress/.28)
        if scene_index==8:
            catch_progress=clamp((progress-.06)/.28)
            if timeline:
                sid='scene-08'
                sc=next((q for q in timeline.get('scenes',[]) if q.get('scene_id')==sid),None)
                beat=next((q for q in timeline.get('cues',[]) if q.get('scene_id')==sid and q.get('kind')=='action'),None)
                if sc and beat:
                    catch_progress=clamp((t-(beat['start_seconds']-sc['start_seconds']))/beat['duration_seconds'])
        catch_inset(im,t,style,0 if scene_index==1 else 2,progress=catch_progress)
        if stage>=1:
            pill(d,(105,558,412,590),'Many regions cooperate',P['muted'],19)
        if scene_index==8:
            text(d,(438,564),'Brain + body',22,P['signal'],True)
    elif scene_index==2:
        panel(im,'From eyes to brain','A simplified information route')
        eye(im,1013,354,style)
        path=cubic([(1013,394),(1048,422),(965,442),(1013,467)])
        line_path(d,path,P['occipital'],4);pulse_on_path(d,path,t,P['ink'],5,speed=.2)
        pill(d,(892,477,1134,522),'Seeing the ball',P['occipital'],24)
        text(d,(1013,550),'Other regions help, too',20,P['muted'],anchor='mm')
        if stage==2: pill(d,(120,560,631,590),'Tour focus ≠ the only active region',P['muted'],19)
    elif scene_index==3:
        panel(im,'Hands + ball','Compare their positions')
        catch_inset(im,t,style,stage,progress=clamp((progress-(.28 if stage else 0))/.32))
        if stage>=1:pill(d,(130,558,615,590),'Touch + body position + surroundings',P['parietal'],20)
    elif scene_index==4:
        panel(im,'Dani’s spoken cue','Sound also appears as words')
        d.rounded_rectangle((865,324,1160,390),radius=14,fill=(33,66,68),outline=P['temporal'],width=2)
        text(d,(1012,357),'“Ready, Teo.”',30,bold=True,anchor='mm')
        for i in range(9):
            x=912+i*25;a=9+18*(.5+.5*math.sin(t*3+i*.7))
            d.line((x,435-a,x,435+a),fill=P['temporal'],width=7)
        if stage>=2:
            paragraph(d,(842,495),['Hearing this cue is optional.','Catching can use other clues.'],21,31)
        else:text(d,(1012,523),'Temporal regions process sound',20,P['muted'],anchor='mm')
    elif scene_index==5:
        panel(im,'A comfortable plan','A choice of action')
        labels=['Watch','Reach','Catch']
        for i,label in enumerate(labels):
            y=337+i*65
            d.rounded_rectangle((853,y-22,1174,y+28),radius=14,fill=(30,58,61),outline=P['frontal'],width=2)
            d.ellipse((871,y-6,884,y+7),fill=P['frontal'])
            text(d,(907,y+1),label,28,bold=True,anchor='lm')
        if stage>=2:text(d,(1012,548),'Planning works with the team',20,P['muted'],anchor='mm')
    elif scene_index==6:
        panel(im,'Brain ↔ body','Information travels both ways')
        draw_body(im,t,style)
        pill(d,(108,557,665,590),'Cerebellum: coordination + timing',P['cerebellum'],23)
    return im


def load_timeline(path):
    if not path:return None
    data=json.loads(Path(path).read_text())
    if not data.get('scenes'):raise ValueError('timeline must contain scenes')
    return data


def scene_duration(scene,timeline,default):
    if not timeline:return default
    sid=f'scene-{scene:02d}'
    for s in timeline['scenes']:
        if s.get('scene_id',s.get('id'))==sid:return float(s['duration_seconds'])
    raise ValueError(f'{sid} missing from timeline')


def render_scene(scene_index,style,duration,path,timeline=None,fps=FPS):
    """Render an H.264 clip whose clock begins at scene-relative time zero."""
    duration=float(duration)
    if duration<=0:raise ValueError('duration must be positive')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(timeline,(str,Path)):timeline=load_timeline(timeline)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    count=math.ceil(duration*fps)
    try:
        for frame_index in range(count):
            im=render_frame(scene_index,style,frame_index/fps,duration,timeline)
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        ret=proc.wait()
        if ret:raise RuntimeError(f'ffmpeg exited {ret}')
    except BaseException:
        if proc.poll() is None:proc.kill()
        raise
    return {'scene':scene_index,'style':style,'path':str(path),'duration_seconds':count/fps,'requested_seconds':duration,'fps':fps,'frames':count,'size':[W,H]}


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--scene',default='all',choices=['all',*[str(i) for i in range(1,9)]])
    parser.add_argument('--style',default='both',choices=['both','2d','3d'])
    parser.add_argument('--duration',default=8,type=float)
    parser.add_argument('--timeline',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--out-dir',type=Path,default=OUT)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--frames-only',action='store_true')
    parser.add_argument('--fps',type=int,default=FPS)
    args=parser.parse_args()
    scenes=list(range(1,9)) if args.scene=='all' else [int(args.scene)]
    styles=['2d','3d'] if args.style=='both' else [args.style]
    if args.output and len(scenes)*len(styles)!=1:parser.error('--output needs one scene and one style')
    timeline=load_timeline(args.timeline)
    target=args.out_dir/('previews' if args.preview or args.frames_only else '')
    records=[]
    for style in styles:
        for scene in scenes:
            duration=scene_duration(scene,timeline,args.duration)
            if args.preview:duration=args.duration
            frame_path=target/style/f'scene-{scene:02d}.png'
            frame_path.parent.mkdir(parents=True,exist_ok=True)
            render_frame(scene,style,duration*.72,duration,None if args.preview else timeline).save(frame_path)
            if not args.frames_only:
                path=args.output or target/style/f'scene-{scene:02d}.mp4'
                info=render_scene(scene,style,duration,path,None if args.preview else timeline,args.fps)
                records.append(info)
                print(json.dumps(info),flush=True)
    if records:
        manifest_path=target/'render-manifest.json'
        previous=json.loads(manifest_path.read_text()).get('clips',[]) if manifest_path.exists() else []
        combined={item['path']:item for item in previous}
        combined.update({item['path']:item for item in records})
        manifest_path.write_text(json.dumps({'renderer':'render_diagrams.py','original_artwork':True,'subtitle_reserved_pixels':110,'timeline':str(args.timeline) if args.timeline else None,'clips':list(combined.values())},indent=2)+'\n')

if __name__=='__main__':main()
