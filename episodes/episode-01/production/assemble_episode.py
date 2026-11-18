#!/usr/bin/env python3
"""Plan or render matching 2D/3D first cuts from measured dialogue timing.

Default: write edit-plan.json and report missing inputs. Add --render only when
the diagram and verified lip-synced performance inputs are ready. Never loops
or stretches character footage/audio. Silent motion tests are not speaking
shots. Each inserted performance requires a matching JSON review sidecar.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys

FPS = 24
WIDTH, HEIGHT = 1280, 720
HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent


def run(command, capture=False):
    return subprocess.run([str(x) for x in command], check=True, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def probe(path):
    value = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams',
                            '-of','json',path],capture=True).stdout)
    video = next((s for s in value['streams'] if s['codec_type']=='video'),None)
    return {'duration':float(value['format'].get('duration',0)),
            'video':video,'streams':value['streams']}


def fingerprint(path):
    stat = path.stat()
    return {'path':str(path),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}


def make_scope(root, timeline, styles):
    """A unique story shot per measured cue, not interchangeable filler clips."""
    diagram_lines={'scene-03-extra-01','scene-06-extra-01','scene-08-line-03'}
    character_reactions={'scene-01-line-02','scene-08-line-02'}
    stage_actions={
        'scene-01':'Gentle catch attempt, amused recovery, and walking into the simulated brain lab',
        'scene-02':'Track the replayed ball, inspect the rear brain region, and invite a viewer answer',
        'scene-03':'Compare the hand gap with the stationary ball and demonstrate changing spatial relationships',
        'scene-04':'React to Dani’s audible and captioned cue, then inspect the temporal region',
        'scene-05':'Rehearse the catch with hands, plan the movement, and walk beside the active network',
        'scene-06':'Discover the cerebellum and trace movement and returning sensory information',
        'scene-07':'Meet three distinct animated cell-guide programs in the simulation display',
        'scene-08':'Return to the lab, complete a gentle catch, and thank the viewer'}
    scenes=[]
    for scene in timeline['scenes']:
        sid=scene['scene_id'];shots=[]
        for index,cue in enumerate((c for c in timeline['cues'] if c['scene_id']==sid),1):
            is_dialogue=cue['kind']=='dialogue'
            speaker=cue.get('speaker')
            is_character=(cue['kind']=='viewer_pause' or
                          (is_dialogue and ((speaker=='TEO' and cue['line_id'] not in diagram_lines)
                           or speaker.endswith('_GUIDE') or cue['line_id'] in character_reactions)))
            visible_speaking=is_character and is_dialogue and speaker!='DANI'
            if is_dialogue:
                narrative=f'{speaker}: {cue["text"]}'
            elif cue['kind']=='viewer_pause':
                narrative=f'Hold the character’s inviting expression and natural body motion for {cue["question_id"]}; leave the full answer space.'
            else:
                narrative=cue.get('action','Progress the authored observation action.')
            shots.append({'shot_id':f'{sid}-shot-{index:02}',
                          'scene_id':sid,'cue_kind':cue['kind'],
                          'line_id':cue.get('line_id'),'speaker':speaker,
                          'start_seconds':cue['start_seconds'],'end_seconds':cue['end_seconds'],
                          'scene_start_seconds':round(cue['start_seconds']-scene['start_seconds'],6),
                          'duration_seconds':cue['duration_seconds'],
                          'kind':'character_performance' if is_character else 'animated_science_cutaway',
                          'visible_speaking':visible_speaking,'narrative_beat':narrative,
                          'staging_context':stage_actions[sid],
                          'performance_requirement':('Fluid body and facial performance, speaking mouth aligned to the approved audio; no frozen-face voice overlay.' if visible_speaking else 'Natural listening/reaction motion with the speaking voice offscreen.' if is_character else 'Purposeful progressing diagram/simulation action; no visible closed-mouth speaking Teo.'),
                          'required_reviews':(['identity','body_motion','expression','timing']+(['lip_sync'] if visible_speaking else [])) if is_character else ['science','timing']})
        char=sum(s['duration_seconds'] for s in shots if s['kind']=='character_performance')
        diag=sum(s['duration_seconds'] for s in shots if s['kind']=='animated_science_cutaway')
        scenes.append({'scene_id':sid,'title':scene['title'],
                       'start_seconds':scene['start_seconds'],'end_seconds':scene['end_seconds'],
                       'duration_seconds':scene['duration_seconds'],
                       'character_seconds':round(char,6),'diagram_seconds':round(diag,6),'shots':shots})
    character=sum(s['character_seconds'] for s in scenes)
    diagram=sum(s['diagram_seconds'] for s in scenes)
    story=timeline['duration_seconds'];story_picture=math.ceil(story*FPS)/FPS;credits=600-story_picture
    native=character*2*17;silent=character*2*5
    return {'schema_version':2,'status':'Production scope only; full episodes are not rendered',
            'episode_id':'episode-01','title':timeline['working_title'],
            'runtime_seconds_per_version':600.0,'story_seconds':story,
            'story_picture_end_seconds':story_picture,
            'subframe_transition_seconds':round(story_picture-story,6),'end_credit_seconds':credits,
            'formats':styles,'shared_voice_timing_source':'audio/timeline.json',
            'character_seconds_per_version':round(character,6),
            'animated_science_seconds_per_version':round(diagram,6),
            'unique_story_shots_per_version':sum(len(s['shots']) for s in scenes),
            'character_approach':'Teo is on screen for most of his dialogue and all six audience questions, with fluid body motion and lip-synced speech; supporting guide voices have their own animated performances.',
            'cutaway_approach':'Science and simulation cutaways advance the actual spoken lesson; no static slide loops or reused character clips to fill time.',
            'voice_continuity_requirement':'Choose one consistent performance/voice method. Native clips with timing different from the guide track cannot be placed over the existing track as if synchronized. New approved takes require a rebuilt measured timeline and captions.',
            'cost_estimates':{
                'rate_source':'Model rates checked by the production lead through Runway on 2026-11-18; estimates are not a quote or spending authorization.',
                'rate_source_url':'https://academy.runwayml.com/models-pricing',
                'gen4_turbo_silent_credits_per_second':5,
                'kling_o3_pro_native_credits_per_second':17,
                'two_versions_character_seconds':round(character*2,6),
                'kling_native_character_seconds_raw_credits':round(native,2),
                'kling_native_rounded_up_credits':math.ceil(native),
                'gen4_silent_character_seconds_raw_credits':round(silent,2),
                'all_1200_seconds_gen4_silent_floor_credits':6000,
                'all_1200_seconds_kling_native_raw_credits':20400,
                'excluded_costs':['Failed takes and retries','Minimum billed clip duration / rounding','Reference-asset processing','Additional lip-sync or performance transfer','Voice consistency work','Upscaling if required'],
                'compatibility':'Gen4 Turbo is silent motion and cannot meet speaking requirements alone. Kling native speech still requires verified identity, consistent voices, lip sync and measured timing. Lower-cost speech/performance models are not assumed available.',
                'locally_rendered_diagrams':'No external model credits for the current locally rendered science diagrams.'},
            'end_card':{'purpose':'Brief episode title, science-source credit and production credit',
                        'content':['The Brain Team Challenge','Science references: see episode notes','Original character design and episode production'],
                        'rule':'Only this explicit short credit card fills the difference to 600 seconds; no speech slowing or narrative filler.'},
            'scenes':scenes}


def make_plan(root, styles):
    timeline_path=root/'audio/timeline.json'
    if not timeline_path.exists():raise ValueError('Measured audio/timeline.json is required.')
    timeline=json.loads(timeline_path.read_text())
    timeline_sha256=hashlib.sha256(timeline_path.read_bytes()).hexdigest()
    story=float(timeline['duration_seconds']);story_picture=math.ceil(story*FPS)/FPS;endcard=600-story_picture
    if not 0 <= endcard <= 15:
        raise ValueError(f'Story is {story:.3f}s; exactly ten minutes requires meaningful retiming, not a long filler card.')
    cursor=0.0
    for scene in timeline['scenes']:
        if abs(scene['start_seconds']-cursor)>.002:raise ValueError('Timeline gap or overlap.')
        cursor=scene['end_seconds']
    if abs(cursor-story)>.002:raise ValueError('Scene coverage does not match audio.')
    scope=make_scope(root,timeline,styles)
    (root/'production/render-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    plan={'schema_version':2,'episode_id':'episode-01','status':'awaiting complete verified character performances',
          'title':timeline['working_title'],'duration_seconds':600.0,
          'story_duration_seconds':story,'story_picture_end_seconds':story_picture,
          'subframe_transition_seconds':round(story_picture-story,6),'end_credit_seconds':endcard,
          'frame_rate':FPS,'width':WIDTH,'height':HEIGHT,
          'timing_source':'audio/timeline.json','timeline_sha256':timeline_sha256,
          'audio':'audio/episode-01-dialogue.wav','captions':'captions/episode-01.en.srt',
          'scope':'production/render-scope.json',
          'performance_sidecar_contract':{
              'path':'motion/{style}/{shot_id}.json, alongside the matching MP4',
              'status':'verified_performance','timeline_sha256':'Must match this plan',
              'voice_sha256':'Must match this plan','shot_id':'Must match the scope',
              'scene_start_seconds':'Must match exact scene-relative shot timing',
              'duration_seconds':'Must cover the shot at original playback speed',
              'reviewed':'All required_reviews in render-scope.json must be true after actual inspection',
              'note':'Silent opening tests do not satisfy speaking shots. Never set review flags just to bypass missing performance.'},
          'principles':['Exactly 600 seconds for each finished version',
                        'Every planned character shot is required, not silently replaced by diagrams',
                        'No time stretching, repeated character loops, or frozen faces under speech',
                        'Use continuous measured diagram time under science cutaways',
                        'Preserve six viewer response pauses','Keep approved canonical master PNGs unchanged'],
          'missing_required_inputs':[],'rejected_performance_inputs':[],'styles':{}}
    voice=root/plan['audio'];voice_hash=hashlib.sha256(voice.read_bytes()).hexdigest() if voice.is_file() else None
    plan['voice_sha256']=voice_hash
    for rel in [plan['audio'],plan['captions']]:
        if not (root/rel).is_file():plan['missing_required_inputs'].append(rel)
    for style in styles:
        scene_edits=[]
        for scene in scope['scenes']:
            sid=scene['scene_id'];diagram=f'diagrams/{style}/{sid}.mp4'
            if not (root/diagram).is_file():plan['missing_required_inputs'].append(diagram)
            edit={'scene_id':sid,'title':scene['title'],
                  'timeline_start_seconds':scene['start_seconds'],'timeline_end_seconds':scene['end_seconds'],
                  'duration_seconds':scene['duration_seconds'],
                  'video_frames':(math.ceil(story*FPS) if scene==scope['scenes'][-1] else round(scene['end_seconds']*FPS))-round(scene['start_seconds']*FPS),
                  'diagram':diagram,'inserts':[],'required_character_shots':[]}
            for shot in scene['shots']:
                if shot['kind']!='character_performance':continue
                rel=f'motion/{style}/{shot["shot_id"]}.mp4';path=root/rel;sidecar=path.with_suffix('.json')
                edit['required_character_shots'].append({'shot_id':shot['shot_id'],'path':rel,
                                                         'visible_speaking':shot['visible_speaking'],
                                                         'duration_seconds':shot['duration_seconds']})
                if not path.is_file():
                    plan['missing_required_inputs'].append(rel);continue
                review=json.loads(sidecar.read_text()) if sidecar.is_file() else {}
                valid=(review.get('status')=='verified_performance' and review.get('shot_id')==shot['shot_id']
                       and review.get('timeline_sha256')==timeline_sha256 and review.get('voice_sha256')==voice_hash
                       and abs(float(review.get('scene_start_seconds',-100))-shot['scene_start_seconds'])<.04
                       and all(review.get('reviewed',{}).get(k) is True for k in shot['required_reviews']))
                if not valid:
                    plan['rejected_performance_inputs'].append({'path':rel,'reason':'Missing reviewed performance against this exact shot/audio/timing'})
                    plan['missing_required_inputs'].append(str(sidecar.relative_to(root)));continue
                media=probe(path);wanted=shot['duration_seconds']
                if not media['video'] or media['duration']<wanted-.04:
                    raise ValueError(f'Performance does not cover its shot: {rel}')
                edit['inserts'].append({'path':rel,'shot_id':shot['shot_id'],
                                       'start_seconds':shot['scene_start_seconds'],
                                       'end_seconds':shot['scene_start_seconds']+wanted,
                                       'duration_seconds':wanted,'source_start_seconds':0.0,
                                       'use_source_audio':False,'performance_review':str(sidecar.relative_to(root))})
            scene_edits.append(edit)
        credit_path=f'production/endcards/{style}.mp4'
        if not (root/credit_path).is_file():plan['missing_required_inputs'].append(credit_path)
        plan['styles'][style]={'output':f'episode-01-{style}-first-cut.mp4','scenes':scene_edits,
                               'planned_character_motion_seconds':scope['character_seconds_per_version'],
                               'verified_character_motion_seconds':round(sum(i['duration_seconds'] for s in scene_edits for i in s['inserts']),6),
                               'end_card':{'path':credit_path,'frames':14400-math.ceil(story*FPS),
                                           'duration_seconds':endcard,'content':scope['end_card']['content']}}
    return plan,timeline


def write_ass(srt_path, output_path):
    def timestamp(text):
        h,m,s_ms=text.strip().split(':');sec,ms=s_ms.split(',')
        value=int(h)*360000+int(m)*6000+int(sec)*100+round(int(ms)/10)
        h,value=divmod(value,360000);m,value=divmod(value,6000);s,cs=divmod(value,100)
        return f'{h}:{m:02}:{s:02}.{cs:02}'
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,30,&H00FFFFFF,&H00FFFFFF,&H001C2429,&H800F171B,0,0,0,0,100,100,0,0,1,2,1,2,70,70,24,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events=[]
    for block in re.split(r'\n\s*\n',srt_path.read_text().strip()):
        lines=block.splitlines()
        if len(lines)<3:continue
        times=lines[1].split(' --> ')
        if len(times)!=2:raise ValueError('Invalid SRT time row.')
        text='\\N'.join(x.replace('\\','\\\\').replace('{','\\{').replace('}','\\}') for x in lines[2:])
        events.append(f'Dialogue: 0,{timestamp(times[0])},{timestamp(times[1])},Default,,0,0,0,,{text}')
    output_path.write_text(header+'\n'.join(events)+'\n')


def render_scene(root, style, scene, cache, threads):
    output=cache/style/(scene['scene_id']+'.mp4')
    output.parent.mkdir(parents=True,exist_ok=True)
    inputs=[root/scene['diagram']]+[root/i['path'] for i in scene['inserts']]
    key=hashlib.sha256(json.dumps({'scene':scene,'inputs':[fingerprint(p) for p in inputs],
                                  'render_revision':1},sort_keys=True).encode()).hexdigest()
    stamp=output.with_suffix('.json')
    if output.exists() and stamp.exists() and json.loads(stamp.read_text()).get('cache_key')==key:
        return output
    media=probe(inputs[0])
    wanted=scene['video_frames']/FPS
    if media['duration'] < wanted-1/FPS-.005:
        raise ValueError(f'Diagram is shorter than scene {scene["scene_id"]}: {media["duration"]} < {wanted}')
    command=['ffmpeg','-y','-hide_banner','-loglevel','error','-filter_complex_threads','1']
    for path in inputs:command+=['-i',path]
    scale=f'fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x13252b,setsar=1,format=yuv420p'
    filters=[f'[0:v]{scale},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={1/FPS:.8f},trim=duration={wanted:.8f}[v0]']
    for n,insert in enumerate(scene['inserts'],1):
        start=insert['start_seconds'];end=insert['end_seconds'];duration=insert['duration_seconds']
        filters.append(f'[{n}:v]{scale},trim=duration={duration:.8f},setpts=PTS-STARTPTS+{start:.8f}/TB[m{n}]')
        filters.append(f'[v{n-1}][m{n}]overlay=eof_action=pass:repeatlast=0:shortest=0:enable=\'gte(t,{start:.8f})*lt(t,{end:.8f})\'[v{n}]')
    command+=['-filter_complex',';'.join(filters),'-map',f'[v{len(scene["inserts"])}]',
              '-an','-frames:v',str(scene['video_frames']),'-r',str(FPS),'-c:v','libx264',
              '-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads',str(threads),output]
    run(command)
    stamp.write_text(json.dumps({'cache_key':key,'scene':scene},indent=2)+'\n')
    return output


def audio_master(root, timeline, cache):
    output=cache/'episode-01-mix.wav';report=cache/'audio-mix-report.json'
    voice=root/'audio/episode-01-dialogue.wav'
    key=hashlib.sha256(json.dumps({'voice':fingerprint(voice),'cues':timeline['cues'],
                                  'output_duration_seconds':600,'revision':2},sort_keys=True).encode()).hexdigest()
    if output.exists() and report.exists() and json.loads(report.read_text()).get('cache_key')==key:
        return output
    module_spec=importlib.util.spec_from_file_location('sound_design',HERE/'sound-design.py')
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    effects=cache/'original-effects.wav'
    module.create_effects(root/'audio/timeline.json',effects)
    mixed=cache/'mix-unmastered.wav'
    run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',voice,'-i',effects,
         '-filter_complex','[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,pan=stereo|c0=c0|c1=c0,apad=whole_dur=600,atrim=duration=600,aresample=48000[a]',
         '-map','[a]','-c:a','pcm_f32le',mixed])
    measured=run(['ffmpeg','-hide_banner','-i',mixed,'-af',
                  'loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture=True)
    match=re.search(r'\{\s*"input_i".*?\}',measured.stderr,re.S)
    if not match:raise ValueError('Could not measure audio loudness.')
    stats=json.loads(match.group())
    if not all(math.isfinite(float(stats[k])) for k in ['input_i','input_tp','input_lra','input_thresh','target_offset']):
        raise ValueError('Audio loudness values are not finite.')
    filt=('loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:print_format=json'
          f':measured_I={stats["input_i"]}:measured_TP={stats["input_tp"]}'
          f':measured_LRA={stats["input_lra"]}:measured_thresh={stats["input_thresh"]}'
          f':offset={stats["target_offset"]}')
    mastered=run(['ffmpeg','-y','-hide_banner','-i',mixed,'-af',filt,'-ar','48000',
                  '-c:a','pcm_s16le',output],capture=True)
    final_match=re.search(r'\{\s*"input_i".*?\}',mastered.stderr,re.S)
    report.write_text(json.dumps({'cache_key':key,'targets':{'integrated_lufs':-16,'true_peak_dbtp':-1.5},
                                 'measured_input':stats,
                                 'mastering_result':json.loads(final_match.group()) if final_match else None,
                                 'processing':'Sparse original effects, two-pass loudness normalization; no time stretching'},indent=2)+'\n')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--styles',nargs='+',choices=['2d','3d'],default=['2d','3d'])
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--threads',type=int,default=3)
    args=parser.parse_args();root=args.root.resolve();production=root/'production'
    production.mkdir(parents=True,exist_ok=True)
    plan,timeline=make_plan(root,args.styles)
    plan_path=production/'edit-plan.json'
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    if not args.render:
        print(json.dumps({'plan':str(plan_path),'duration_seconds':plan['duration_seconds'],
                          'missing_required_inputs':plan['missing_required_inputs'],
                          'status':'No final rendering requested'},indent=2));return
    if plan['missing_required_inputs']:
        raise ValueError('Required inputs missing: '+', '.join(plan['missing_required_inputs']))
    cache=production/'.render-cache';cache.mkdir(exist_ok=True)
    ass=production/'episode-01.en.ass';write_ass(root/plan['captions'],ass)
    master=audio_master(root,timeline,cache)
    outputs=[]
    for style in args.styles:
        print(f'Rendering {style} scene edits',flush=True)
        paths=[render_scene(root,style,s,cache,args.threads) for s in plan['styles'][style]['scenes']]
        credits=plan['styles'][style]['end_card']
        if credits['frames']:
            paths.append(render_scene(root,style,{'scene_id':'end-credits','video_frames':credits['frames'],
                         'duration_seconds':credits['duration_seconds'],'diagram':credits['path'],
                         'inserts':[]},cache,args.threads))
        concat=cache/f'{style}-concat.txt'
        concat.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in paths))
        output=root/plan['styles'][style]['output']
        # Run from production so the subtitle filename needs no filter escaping.
        command=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0',
                 '-i',str(concat),'-i',str(master),'-vf','ass=episode-01.en.ass',
                 '-map','0:v:0','-map','1:a:0','-t',f'{plan["duration_seconds"]:.6f}',
                 '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',
                 '-r',str(FPS),'-threads',str(args.threads),'-c:a','aac','-b:a','192k',
                 '-ar','48000','-ac','2','-movflags','+faststart',str(output)]
        subprocess.run(command,check=True,cwd=production)
        inspected=probe(output)
        if abs(inspected['duration']-plan['duration_seconds']) > .10:
            raise ValueError(f'Unexpected final duration: {output}')
        if not inspected['video'] or inspected['video']['width']!=WIDTH or inspected['video']['height']!=HEIGHT:
            raise ValueError('Unexpected output video dimensions.')
        if not any(s['codec_type']=='audio' for s in inspected['streams']):
            raise ValueError('Final output has no audio stream.')
        outputs.append({'style':style,'path':str(output),'duration_seconds':inspected['duration'],
                        'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        print(json.dumps(outputs[-1]),flush=True)
    plan['status']='rendered first cuts';plan['outputs']=outputs
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')


if __name__=='__main__':
    try:main()
    except (ValueError,subprocess.CalledProcessError) as error:
        print(f'Assembly stopped: {error}',file=sys.stderr);sys.exit(1)
