"""Create candidate mouth timings from existing speech. Never edits audio/artwork."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,subprocess,json,hashlib,time,shutil

parser=argparse.ArgumentParser()
parser.add_argument('--episode',type=Path,default=Path('/workspace/youtube/episodes/episode-01'))
parser.add_argument('--rhubarb',type=Path,default=Path('/workspace/tools/rhubarb/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb'))
args=parser.parse_args()
root=args.episode
out=root/'animation/lipsync'
for folder in ['dialogue','lines']:(out/folder).mkdir(parents=True,exist_ok=True)
script_path=root/'dialogue.json'
timeline_path=root/'audio/timeline.json'
script=json.loads(script_path.read_text())
timeline=json.loads(timeline_path.read_text())
lines={line['id']:line for scene in script['scenes'] for line in scene['lines']}
dialogue_cues=[cue for cue in timeline['cues'] if cue['kind']=='dialogue']
version=subprocess.check_output([str(args.rhubarb),'--version'],text=True).strip()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
original_hashes={cue['line_id']:sha(root/cue['audio_path']) for cue in dialogue_cues}
started=time.monotonic()

def process(cue):
 line_id=cue['line_id'];line=lines[line_id]
 assert line['text']==cue['text']
 audio=root/cue['audio_path'];textfile=out/'dialogue'/(line_id+'.txt');dest=out/'lines'/(line_id+'.json')
 textfile.write_text(line['text']+'\n')
 begin=time.monotonic()
 subprocess.run([str(args.rhubarb),'-q','-f','json','-r','pocketSphinx','--threads','2','--extendedShapes','GHX','-d',str(textfile),'-o',str(dest),str(audio)],check=True,capture_output=True,text=True,timeout=90)
 data=json.loads(dest.read_text())
 previous=0.0
 for mouth in data['mouthCues']:
  assert mouth['value'] in 'ABCDEFGHX'
  assert mouth['start']>=previous-0.000001
  assert mouth['end']>=mouth['start']
  assert mouth['end']<=cue['duration_seconds']+0.011
  previous=mouth['end']
 assert abs(data['metadata']['duration']-cue['duration_seconds'])<=0.011
 return {'line_id':line_id,'speaker':cue['speaker'],'scene_id':cue['scene_id'],'episode_start_seconds':cue['start_seconds'],'episode_end_seconds':cue['end_seconds'],'actual_audio_seconds':cue['duration_seconds'],'rhubarb_seconds':data['metadata']['duration'],'audio_path':cue['audio_path'],'audio_sha256':original_hashes[line_id],'text_path':str(textfile.relative_to(root)),'cue_path':str(dest.relative_to(root)),'cue_count':len(data['mouthCues']),'processing_seconds':round(time.monotonic()-begin,3),'raw':data}
results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 jobs=[pool.submit(process,c) for c in dialogue_cues]
 for job in as_completed(jobs):
  r=job.result();results.append(r)
  print(f"{len(results)}/{len(dialogue_cues)} {r['line_id']}: {r['cue_count']} cues in {r['processing_seconds']}s",flush=True)
results.sort(key=lambda r:r['episode_start_seconds'])
global_cues=[]
for result in results:
 offset=result['episode_start_seconds']
 for cue in result['raw']['mouthCues']:
  global_cues.append({'speaker':result['speaker'],'scene_id':result['scene_id'],'line_id':result['line_id'],'shape':cue['value'],'start_seconds':round(offset+cue['start'],6),'end_seconds':round(offset+cue['end'],6)})
# A complete track per speaker explicitly closes the mouth during every gap.
tracks={}
for speaker in sorted(set(c['speaker'] for c in global_cues)):
 track=[];cursor=0.0
 for cue in [c for c in global_cues if c['speaker']==speaker]:
  if cue['start_seconds']>cursor:
   track.append({'shape':'X','start_seconds':cursor,'end_seconds':cue['start_seconds'],'reason':'No speech from this character'})
  track.append({k:v for k,v in cue.items() if k!='speaker'})
  cursor=cue['end_seconds']
 if cursor<600:track.append({'shape':'X','start_seconds':cursor,'end_seconds':600.0,'reason':'No speech from this character'})
 tracks[speaker]=track
for cue in dialogue_cues:assert sha(root/cue['audio_path'])==original_hashes[cue['line_id']]
legend={'A':'Closed bilabial sounds P/B/M','B':'Narrow opening for many consonants and EE','C':'Open EH/AE and transitions','D':'Wide open AA','E':'Rounded AO/ER and transitions','F':'Puckered UW/OW/W','G':'F/V lip-to-teeth articulation','H':'Long L articulation','X':'Closed relaxed rest'}
report={'schema_version':'1.0','status':'CANDIDATE_TIMINGS_NOT_VISUALLY_APPROVED','tool':version,'recognizer':'pocketSphinx','extended_shapes':'GHX','source_script_sha256':sha(script_path),'source_timeline_sha256':sha(timeline_path),'speech_content_seconds':timeline['duration_seconds'],'planned_delivery_seconds':600.0,'fps_hint':24,'time_unit':'seconds','time_resolution_note':'Rhubarb reports centiseconds. Global cues add measured line offsets. Missing sub-centisecond tails and all non-speaking intervals use X/rest. Times are candidates inferred from audio, not hand-verified phoneme alignment.','line_count':len(results),'mouth_cue_count':len(global_cues),'processing_wall_seconds':round(time.monotonic()-started,3),'shape_legend':legend,'lines':[{k:v for k,v in r.items() if k!='raw'} for r in results],'cues':global_cues,'speaker_tracks':tracks,'sources':['https://github.com/DanielSWolf/rhubarb-lip-sync/tree/v1.14.0','https://github.com/DanielSWolf/rhubarb-lip-sync/releases/tag/v1.14.0'],'limitations':['No image, mesh, mouth drawing, rig, face, or video was created or changed.','These discrete mouth cues need compatible character mouth assets and animation review. They are not a precision lip-sync approval.','The same timing data may drive 2D switches or 3D facial shapes after appropriate retargeting.','Natural motion also needs transition blending, facial expression and body performance; mouth switching alone does not produce acting.','Times are for the unchanged Kokoro guide takes, not the independently generated Runway clips.']}
(out/'episode-mouth-cues.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'validation.json').write_text(json.dumps({'status':'PASS','line_count':len(results),'mouth_cue_count':len(global_cues),'speaker_tracks':len(tracks),'original_audio_hashes_unchanged':True,'checks':['Every line matches the exact script text.','Every cue is ordered, bounded by its input line audio, and uses a known Rhubarb shape.','Each tool duration matches the real line duration within centisecond rounding.','Episode cues use the measured audio timeline offsets.','Every speaker track uses rest during gaps and closes through the end of the planned600-second edit.','No source audio hashes changed.'],'visual_lipsync_status':'UNREVIEWED; no rendered rig or video supplied'},indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['tool','line_count','mouth_cue_count','processing_wall_seconds','status']},indent=2),flush=True)
