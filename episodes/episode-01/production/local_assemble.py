#!/usr/bin/env python3
"""Assemble the complete local animated episode without external services.

--prepare makes the original soundtrack, end card, subtitles and chapters.
--render consumes animation/rendered/{2d,3d}/scene-XX.mp4 and writes complete
600-second exports. Visual inspection is a separate step and is never inferred
from successful encoding. All encoders, decoders and filters use one thread.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from assemble_episode import write_ass

ROOT = Path(__file__).resolve().parents[1]
FPS, WIDTH, HEIGHT, TOTAL = 24, 1280, 720, 600
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def run(command, capture=False):
    return subprocess.run([str(x) for x in command],check=True,text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def inspect(path, count=False):
    command=['ffprobe','-v','error','-threads','1']
    if count:command+=['-count_frames']
    command+=['-show_streams','-show_format','-show_chapters','-of','json',path]
    result=run(command,capture=True)
    if count and result.stderr.strip():
        raise ValueError('Decode errors during full-frame verification: '+result.stderr.strip())
    return json.loads(result.stdout)


def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else REGULAR,size)


def make_endcard(folder):
    """Original typography/diagram graphic; no character artwork is edited."""
    path=folder/'end-card.png'
    im=Image.new('RGB',(WIDTH,HEIGHT),(17,43,48));d=ImageDraw.Draw(im)
    ink=(239,234,219);muted=(155,182,179);gold=(222,186,119)
    d.text((640,130),'TEO · EPISODE 1',font=font(25,True),fill=gold,anchor='mm')
    # A small, original network symbol: an analogy rather than brain anatomy.
    nodes=[(554,245),(609,218),(671,235),(724,210),(615,282),(686,287)]
    for a,b in [(0,1),(1,2),(2,3),(0,4),(1,4),(2,5),(4,5),(3,5)]:
        d.line([nodes[a],nodes[b]],fill=(67,101,103),width=3)
    for x,y in nodes:d.ellipse((x-7,y-7,x+7,y+7),fill=gold)
    d.text((640,365),'The Brain Team Challenge',font=font(48,True),fill=ink,anchor='mm')
    d.text((640,435),'One catch. A whole team.',font=font(30),fill=muted,anchor='mm')
    d.text((640,565),'Science references: Queensland Brain Institute · NICHD · UTHealth · SfN',
           font=font(19),fill=muted,anchor='mm')
    d.text((640,610),'Full science notes and production credits accompany this episode.',
           font=font(18),fill=muted,anchor='mm')
    im.save(path)
    return path


def original_bed(root,folder,timeline):
    rate=24000;sample_count=TOTAL*rate
    bed=np.zeros(sample_count,dtype=np.float32);events=[]
    def note(start,pitch,length=1.45,gain=.005):
        if start<0 or start>=TOTAL:return
        t=np.arange(round(length*rate),dtype=np.float32)/rate
        envelope=np.minimum(t/.025,1)*np.exp(-2.9*t)
        envelope*=np.minimum((length-t)/.12,1)
        sound=(np.sin(2*np.pi*pitch*t)+.18*np.sin(2*np.pi*2*pitch*t))*envelope*gain
        a=round(start*rate);b=min(a+len(sound),sample_count)
        bed[a:b]+=sound[:b-a]
        events.append({'start_seconds':round(start,4),'pitch_hz':pitch,'length_seconds':length,'gain':gain})
    # Sparse original pentatonic phrases; no recorded samples or borrowed tune.
    pitches=[293.6648,369.9944,440.0,493.8833,587.3295]
    for si,scene in enumerate(timeline['scenes']):
        start=scene['start_seconds'];end=scene['end_seconds']
        for pi,offset in enumerate(np.arange(1.2,max(1.3,end-start-3),15.6)):
            base=(si+pi*2)%len(pitches)
            for ni,step in enumerate([0,2,1]):
                note(start+float(offset)+ni*.43,pitches[(base+step)%len(pitches)],1.55,.0045)
    for ni,pitch in enumerate([293.6648,440.0,587.3295]):note(596.2+ni*.36,pitch,2.45,.009)
    # Keep full viewer-answer pauses clear; ramp rather than cut the music.
    answer_windows=[]
    for cue in timeline['cues']:
        if cue['kind']!='viewer_pause':continue
        a=round(cue['start_seconds']*rate);b=round(cue['end_seconds']*rate)
        ramp=round(.32*rate);before=max(0,a-ramp);after=min(sample_count,b+ramp)
        bed[before:a]*=np.linspace(1,0,a-before,endpoint=False,dtype=np.float32)
        bed[a:b]=0
        bed[b:after]*=np.linspace(0,1,after-b,endpoint=False,dtype=np.float32)
        answer_windows.append([cue['start_seconds'],cue['end_seconds']])
    module_spec=importlib.util.spec_from_file_location('sound_design',root/'production/sound-design.py')
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    effects_path=folder/'original-effects.wav'
    module.create_effects(root/'audio/timeline.json',effects_path)
    with wave.open(str(effects_path),'rb') as wav:
        assert wav.getframerate()==rate and wav.getnchannels()==1 and wav.getsampwidth()==2
        effects=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
    bed[:len(effects)]+=effects
    # Effects are action-only; still verify that none entered an answer pause.
    for start,end in answer_windows:
        if np.max(np.abs(bed[round(start*rate):round(end*rate)]))>1e-7:
            raise ValueError('A sound effect overlaps a viewer answer pause.')
    path=folder/'original-music-and-effects.wav'
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes((np.clip(bed,-1,1)*32767).astype('<i2').tobytes())
    report={'origin':'Original procedural tones and soft-contact effects; no external service, samples or music',
            'music_style':'Sparse low-level instrumental pentatonic phrases',
            'duration_seconds':TOTAL,'peak_dbfs':round(20*math.log10(max(float(np.max(np.abs(bed))),1e-12)),2),
            'viewer_answer_windows_silent':answer_windows,'music_events':events,
            'effects_manifest':'original-effects.json','sha256':digest(path)}
    (folder/'sound-design.json').write_text(json.dumps(report,indent=2)+'\n')
    return path,report


def measure_loudness(path):
    result=run(['ffmpeg','-hide_banner','-threads','1','-filter_threads','1','-i',path,
                '-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture=True)
    matches=re.findall(r'\{\s*"input_i".*?\}',result.stderr,re.S)
    if not matches:raise ValueError('Could not measure audio loudness.')
    return json.loads(matches[-1])


def soundtrack(root,folder,timeline):
    voice=root/'audio/episode-01-dialogue.wav';output=folder/'episode-01-master.wav'
    key=hashlib.sha256((digest(voice)+digest(root/'audio/timeline.json')+'local-sound-v1').encode()).hexdigest()
    report_path=folder/'audio-validation.json'
    if output.exists() and report_path.exists():
        report=json.loads(report_path.read_text())
        if report.get('cache_key')==key:return output,report
    bed,sound_report=original_bed(root,folder,timeline)
    premix=folder/'premix.wav'
    run(['ffmpeg','-y','-v','error','-threads','1','-filter_complex_threads','1','-i',voice,'-i',bed,
         '-filter_complex','[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,pan=stereo|c0=c0|c1=c0,apad=whole_dur=600,atrim=duration=600,aresample=48000[a]',
         '-map','[a]','-threads','1','-c:a','pcm_f32le',premix])
    first=measure_loudness(premix)
    if not all(math.isfinite(float(first[k])) for k in ['input_i','input_tp','input_lra','input_thresh','target_offset']):
        raise ValueError('Invalid measured soundtrack levels.')
    filters=('loudnorm=I=-16:TP=-1.5:LRA=7:linear=true'
             f':measured_I={first["input_i"]}:measured_TP={first["input_tp"]}'
             f':measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}'
             f':offset={first["target_offset"]}')
    run(['ffmpeg','-y','-v','error','-threads','1','-filter_threads','1','-i',premix,
         '-af',filters,'-ar','48000','-ac','2','-c:a','pcm_s16le',output])
    final=measure_loudness(output)
    info=inspect(output);duration=float(info['format']['duration'])
    if abs(duration-TOTAL)>.001:raise ValueError('Master soundtrack is not 600 seconds.')
    if float(final['input_tp'])>-.9:raise ValueError('Unexpectedly high master true peak.')
    if not -16.8<=float(final['input_i'])<=-15.2:raise ValueError('Unexpected master loudness.')
    report={'cache_key':key,'duration_seconds':duration,'channels':2,'sample_rate':48000,
            'dialogue_source_sha256':digest(voice),'master_sha256':digest(output),
            'integrated_lufs':float(final['input_i']),'true_peak_dbtp':float(final['input_tp']),
            'loudness_range_lu':float(final['input_lra']),
            'music_effects_peak_dbfs':sound_report['peak_dbfs'],
            'viewer_pause_sound_effects':False,'time_stretching':False,
            'listening_review':'Pending actual listening; measured levels alone do not establish intelligibility',
            'picture_lip_sync_review':'Not assessed by this audio validation'}
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    for label,start in [('opening',0),('science',67),('ending',588)]:
        run(['ffmpeg','-y','-v','error','-threads','1','-ss',str(start),'-i',output,
             '-t','12','-ar','24000','-ac','1',folder/f'listening-{label}.wav'])
    return output,report


def chapter_file(timeline,path):
    def escaped(text):return text.replace('\\','\\\\').replace('=','\\=').replace(';','\\;').replace('#','\\#').replace('\n',' ')
    lines=[';FFMETADATA1','title=The Brain Team Challenge','artist=Teo','language=eng']
    for scene in timeline['scenes']:
        end=596 if scene==timeline['scenes'][-1] else scene['end_seconds']
        lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(scene["start_seconds"]*1000)}',
                f'END={round(end*1000)}','title='+escaped(scene['title'])]
    lines+=['[CHAPTER]','TIMEBASE=1/1000','START=596000','END=600000','title=Credits']
    path.write_text('\n'.join(lines)+'\n')


def prepare(root):
    timeline=json.loads((root/'audio/timeline.json').read_text())
    story=float(timeline['duration_seconds']);picture_end=math.ceil(story*FPS)/FPS
    if not 585<=story<=600:raise ValueError('Ten-minute story audio is not ready.')
    if picture_end!=596.0:raise ValueError('Revisit the authored four-second end card for changed timing.')
    folder=root/'production/local-output';folder.mkdir(parents=True,exist_ok=True)
    exports=root/'exports';exports.mkdir(exist_ok=True)
    master,audio_report=soundtrack(root,folder,timeline)
    card=make_endcard(folder)
    ass=folder/'episode-01.en.ass';write_ass(root/'captions/episode-01.en.srt',ass)
    # Both caption files remain external as well as the readable burn-in.
    shutil.copyfile(root/'captions/episode-01.en.srt',exports/'episode-01.en.srt')
    shutil.copyfile(root/'captions/episode-01.en.vtt',exports/'episode-01.en.vtt')
    chapters=folder/'chapters.ffmetadata';chapter_file(timeline,chapters)
    counts=[]
    for scene in timeline['scenes']:
        end=math.ceil(story*FPS) if scene==timeline['scenes'][-1] else round(scene['end_seconds']*FPS)
        counts.append(end-round(scene['start_seconds']*FPS))
    assert sum(counts)+96==14400
    manifest={'status':'Soundtrack and edit assets prepared; final video rendering/visual review pending',
              'story_audio_seconds':story,'picture_end_seconds':picture_end,'credits_seconds':4.0,
              'total_seconds':600.0,'frames':14400,'frame_rate':24,'scene_frames':counts,
              'audio_validation':audio_report,'external_services_used':False,
              'visual_review':'Pending actual rendered-frame inspection','lip_sync_review':'Pending picture inspection'}
    (folder/'assembly-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return timeline,folder,exports,master,card,ass,chapters,counts,manifest


def render_style(root,style,prepared,preset='veryfast'):
    timeline,folder,exports,master,card,ass,chapters,counts,manifest=prepared
    paths=[root/f'animation/rendered/{style}/{s["scene_id"]}.mp4' for s in timeline['scenes']]
    missing=[str(p) for p in paths if not p.exists()]
    if missing:raise ValueError('Local scene renders still missing: '+', '.join(missing))
    sources=[]
    for path,count in zip(paths,counts):
        info=inspect(path);video=next((s for s in info['streams'] if s['codec_type']=='video'),None)
        if not video:raise ValueError(f'No video stream in {path}')
        if video['width']!=WIDTH or video['height']!=HEIGHT:raise ValueError(f'Wrong source size: {path}')
        available=int(video.get('nb_frames') or round(float(video['duration'])*FPS))
        if available<count:raise ValueError(f'Not enough source frames: {path}, {available} < {count}')
        sources.append({'path':str(path.relative_to(root)),'frames_used':count,'frames_available':available})
    suffix='2d' if style=='2d' else '3d-style';output=exports/f'episode-01-{suffix}.mp4'
    temp=output.with_name(output.stem+'.rendering.mp4')
    command=['ffmpeg','-y','-hide_banner','-loglevel','warning','-filter_complex_threads','1']
    for path in paths:command+=['-threads','1','-i',path]
    command+=['-loop','1','-framerate','24','-threads','1','-i',card,
              '-threads','1','-i',master,'-i',chapters]
    filters=[]
    for index,count in enumerate(counts+[96]):
        filters.append(f'[{index}:v]fps=24,trim=end_frame={count},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{index}]')
    filters.append(''.join(f'[v{i}]' for i in range(9))+'concat=n=9:v=1:a=0[joined]')
    # Relative filter path is stable and avoids unsafe filter-path interpolation.
    filters.append('[joined]ass=episode-01.en.ass[captioned]')
    command+=['-filter_complex',';'.join(filters),'-map','[captioned]','-map','9:a:0',
              '-map_metadata','10','-map_chapters','10','-frames:v','14400','-t','600',
              '-c:v','libx264','-preset',preset,'-crf','20','-pix_fmt','yuv420p','-r','24','-threads','1',
              '-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
              '-metadata:s:a:0','language=eng','-metadata','title=The Brain Team Challenge',
              '-metadata','comment=Original local animation using the approved Teo illustration; English captions included.',
              '-movflags','+faststart','-progress',folder/f'{style}-encode-progress.txt',temp]
    print(f'Encoding full {style} episode: 14,400 frames',flush=True)
    subprocess.run([str(x) for x in command],check=True,cwd=folder)
    # Decode every frame once, rather than assuming the container count is proof.
    info=inspect(temp,count=True);video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    if int(video['nb_frames'])!=14400:raise ValueError('Final video is not 14,400 frames.')
    if int(video['nb_read_frames'])!=14400:raise ValueError('Full-frame decode did not return 14,400 frames.')
    if abs(float(video['duration'])-600)>.001:raise ValueError('Final video is not exactly 600 seconds.')
    if abs(float(audio['duration'])-600)>.05:raise ValueError('Audio does not cover the full episode.')
    if len(info.get('chapters',[]))!=9:raise ValueError('Missing chapter metadata.')
    temp.replace(output)
    report={'status':'Rendered; visual and lip-sync review remain pending',
            'file':str(output.relative_to(root)),'sha256':digest(output),'bytes':output.stat().st_size,
            'duration_seconds':float(video['duration']),'frames':int(video['nb_frames']),
            'decoded_frames':int(video['nb_read_frames']),
            'frame_rate':video['r_frame_rate'],'video_codec':video['codec_name'],
            'audio_codec':audio['codec_name'],'audio_duration_seconds':float(audio['duration']),
            'size':[video['width'],video['height']],'chapters':len(info['chapters']),
            'burned_english_captions':True,'sources':sources,
            'visual_review':'Pending rendered-frame inspection','lip_sync_review':'Pending actual speaking-shot inspection'}
    (exports/f'episode-01-{suffix}.validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--styles',nargs='+',choices=['2d','3d'],default=['2d','3d'])
    parser.add_argument('--preset',default='veryfast',choices=['ultrafast','superfast','veryfast','faster','fast'])
    args=parser.parse_args();prepared=prepare(args.root.resolve())
    print(json.dumps({'audio':str(prepared[3]),'end_card':str(prepared[4]),'frames_each':14400,
                      'audio_validation':prepared[-1]['audio_validation']},indent=2),flush=True)
    if args.render:
        for style in args.styles:render_style(args.root.resolve(),style,prepared,args.preset)
        prepared[-1]['status']='Requested full exports rendered and technically verified; visual review is recorded separately'
        prepared[-1]['rendered_exports']=[str(p.relative_to(args.root.resolve())) for p in prepared[2].glob('episode-01-*.mp4')]
        (prepared[1]/'assembly-manifest.json').write_text(json.dumps(prepared[-1],indent=2)+'\n')
