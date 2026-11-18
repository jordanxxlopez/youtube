"""Local CPU narration production. No paid APIs; no source files modified."""
from pathlib import Path
from dataclasses import asdict
import argparse, json, hashlib, time, re, textwrap, importlib.metadata, subprocess
import numpy as np
import soundfile as sf
import onnxruntime as ort
from kokoro_onnx import Kokoro

ort.disable_telemetry_events()
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,default=Path('/workspace/youtube/episodes/episode-01/dialogue.json'))
parser.add_argument('--models',type=Path,default=Path('/workspace/tools/voice-models'))
args=parser.parse_args()
base=args.source.parent
out=base/'audio'
line_dir=out/'lines'
line_dir.mkdir(parents=True,exist_ok=True)
(base/'captions').mkdir(parents=True,exist_ok=True)
doc=json.loads(args.source.read_text())
source_sha=hashlib.sha256(args.source.read_bytes()).hexdigest()
VOICE_MAP={
 'TEO':{'voice_id':'am_puck','speed':0.80},
 'DANI':{'voice_id':'af_heart','speed':0.80},
 'NEURON_GUIDE':{'voice_id':'af_bella','speed':0.84},
 'ASTROCYTE_GUIDE':{'voice_id':'af_nicole','speed':0.82},
 'MICROGLIA_GUIDE':{'voice_id':'am_fenrir','speed':0.80}
}
options=ort.SessionOptions()
options.intra_op_num_threads=3
options.inter_op_num_threads=1
session=ort.InferenceSession(str(args.models/'kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
k=Kokoro.from_session(session,str(args.models/'voices-v1.0.bin'))
SR=24000
pieces=[]
cues=[]
scenes=[]
captions=[]
cursor=0
started_all=time.monotonic()

def add_audio(audio):
 global cursor
 pieces.append(audio)
 cursor+=len(audio)

def silence(seconds):
 add_audio(np.zeros(round(seconds*SR),dtype=np.float32))

SCIENCE_OVERRIDES={
 'occipital':'ɑkˈsɪpɪtəl',
 'parietal':'pəɹˈaɪətəl',
 'cerebrum':'səɹˈiːbɹəm',
 'cerebellum':'sˌɛɹəbˈɛləm',
 'neurons':'nˈʊɹɑːnz',
 'neuron':'nˈʊɹɑːn',
 'astrocytes':'ˈæstɹoʊsˌaɪts',
 'astrocyte':'ˈæstɹoʊsˌaɪt',
 'microglial':'mˌaɪkɹoʊɡlˈiːəl',
 'microglia':'mˌaɪkɹoʊɡlˈiːə',
}
def pronunciation(text):
 # Preserve the displayed script. Scientific names use the script's pronunciation guide.
 phonemes=k.tokenizer.phonemize(text,'en-us')
 pairs=[('Teo','tˈɛoʊ'),('Dani','dˈɑːni')]+list(SCIENCE_OVERRIDES.items())
 for name,target in pairs:
  if re.search(r'\b'+re.escape(name)+r'\b',text,re.I):
   source=k.tokenizer.phonemize(name,'en-us').strip()
   phonemes=phonemes.replace(source,target)
 return phonemes

def caption_chunks(text):
 # Exactly one or two 40-character lines per caption. Line audio provides the
 # measured timing anchors; internal splits are proportional estimates.
 wrapped=textwrap.wrap(text,width=40,break_long_words=False,break_on_hyphens=False)
 return [' '.join(wrapped[i:i+2]) for i in range(0,len(wrapped),2)]

def subtime(seconds,sep=','):
 ms=round(seconds*1000)
 h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'

for scene in doc['scenes']:
 scene_start=cursor/SR
 beats={}
 for b in scene.get('action_beats',[]):beats.setdefault(b['after_line_id'],[]).append(b)
 for li,line in enumerate(scene['lines']):
  voice=VOICE_MAP[line['speaker']]
  wav_path=line_dir/(line['id']+'.wav')
  info_path=line_dir/(line['id']+'.json')
  key=hashlib.sha256(json.dumps({'text':line['text'],'voice':voice,'pronunciation_version':2 if any(re.search(r'\b'+re.escape(term)+r'\b',line['text'],re.I) for term in SCIENCE_OVERRIDES) else 1},sort_keys=True).encode()).hexdigest()
  cached=json.loads(info_path.read_text()) if info_path.exists() else None
  if wav_path.exists() and cached and cached['cache_key']==key:
   audio,sr=sf.read(wav_path,dtype='float32')
   elapsed=0
  else:
   started=time.monotonic()
   phonemes=pronunciation(line['text'])
   audio,sr,native_timings=k.create_timed(phonemes,voice=voice['voice_id'],speed=voice['speed'],lang='en-us',is_phonemes=True)
   # Normalize peaks gently to ensure character voices have comparable presence.
   peak=float(np.max(np.abs(audio)))
   if peak>0: audio=audio*min(1.8,0.72/peak)
   sf.write(wav_path,audio,sr,subtype='PCM_16')
   audio,sr=sf.read(wav_path,dtype='float32')
   elapsed=time.monotonic()-started
   cached={'cache_key':key,'line_id':line['id'],'speaker':line['speaker'],'text':line['text'],**voice,'duration_seconds':len(audio)/sr,'phonemes':phonemes,'native_phoneme_timings':[asdict(t) for t in native_timings],'sample_rate':sr,'generation_seconds':elapsed}
   info_path.write_text(json.dumps(cached,indent=2)+'\n')
  assert sr==SR
  start=cursor/SR
  add_audio(audio)
  end=cursor/SR
  cue={'kind':'dialogue','scene_id':scene['id'],'line_id':line['id'],'speaker':line['speaker'],'text':line['text'],'start_seconds':round(start,6),'end_seconds':round(end,6),'duration_seconds':round(end-start,6),'audio_path':str(wav_path.relative_to(base)),'native_phoneme_timings_available':bool(cached.get('native_phoneme_timings')),**voice}
  cues.append(cue)
  chunks=caption_chunks(line['text'])
  weights=[max(1,len(re.findall(r"[A-Za-z]+",s))) for s in chunks]
  total=sum(weights)
  t=start
  for chunk,w in zip(chunks,weights):
   next_t=t+(end-start)*w/total
   captions.append({'start':t,'end':next_t,'text':'\n'.join(textwrap.wrap(chunk,width=40,break_long_words=False,break_on_hyphens=False)),'line_id':line['id']})
   t=next_t
  pause=float(line.get('pause_after_seconds',0))
  if pause:
   pstart=cursor/SR
   silence(pause)
   cues.append({'kind':'viewer_pause','scene_id':scene['id'],'after_line_id':line['id'],'question_id':line.get('viewer_question_id'),'start_seconds':pstart,'end_seconds':cursor/SR,'duration_seconds':pause})
   captions[-1]['end']=cursor/SR
  for beat in beats.get(line['id'],[]):
   bstart=cursor/SR
   silence(float(beat['seconds']))
   cues.append({'kind':'action','scene_id':scene['id'],'after_line_id':line['id'],'start_seconds':bstart,'end_seconds':cursor/SR,'duration_seconds':beat['seconds'],'action':beat['action'],'sound_direction':beat['sound']})
  print(f"{line['id']} {end-start:.2f}s ({elapsed:.2f}s render), timeline {cursor/SR:.2f}s",flush=True)
 scenes.append({'scene_id':scene['id'],'title':scene['title'],'start_seconds':round(scene_start,6),'end_seconds':round(cursor/SR,6),'duration_seconds':round(cursor/SR-scene_start,6)})
track=np.concatenate(pieces)
sf.write(out/'episode-01-dialogue.wav',track,SR,subtype='PCM_16')
scene_dir=out/'scenes'
scene_dir.mkdir(exist_ok=True)
for scene in scenes:
 scene_path=scene_dir/(scene['scene_id']+'.wav')
 a=round(scene['start_seconds']*SR)
 b=round(scene['end_seconds']*SR)
 sf.write(scene_path,track[a:b],SR,subtype='PCM_16')
 scene['audio_path']=str(scene_path.relative_to(base))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(out/'episode-01-dialogue.wav'),'-codec:a','libmp3lame','-q:a','2',str(out/'episode-01-dialogue.mp3')],check=True)
spoken=sum(c['duration_seconds'] for c in cues if c['kind']=='dialogue')
metadata={
 'episode_id':doc['metadata']['episode_id'],'working_title':doc['metadata']['working_title'],
 'status':'Generated dialogue soundtrack; not a finished video or fully mixed soundtrack',
 'source_dialogue_sha256':source_sha,'source_dialogue':'../dialogue.json',
 'sample_rate':SR,'channels':1,'sample_format':'PCM_16',
 'duration_seconds':round(len(track)/SR,6),'spoken_duration_seconds':round(spoken,6),
 'explicit_action_and_question_seconds':sum(c['duration_seconds'] for c in cues if c['kind']!='dialogue'),
 'spoken_word_count':doc['metadata']['spoken_word_count'],
 'actual_spoken_words_per_minute':round(doc['metadata']['spoken_word_count']/spoken*60,2),
 'extra_padding_seconds':0,'full_render_wall_seconds':round(time.monotonic()-started_all,3),
 'voice_map':VOICE_MAP,'engine':'Kokoro 82M v1.0 / kokoro-onnx, CPUExecutionProvider',
 'voice_status':'Provisional stock synthetic voices, no voice cloning',
 'timing_precision':'Dialogue line boundaries and action/question pauses are measured exactly. Caption subdivisions within lines are proportional word-count estimates, not forced alignment.',
 'pronunciation':'Character and scientific term phoneme overrides follow the script pronunciation guide. Acoustic realization still requires listening review.',
 'scientific_pronunciation_overrides':SCIENCE_OVERRIDES,
 'audio_processing':'Per-line peak level adjustment capped at +5.1 dB; no artificial time padding or time stretching.',
 'package_versions':{n:importlib.metadata.version(n) for n in ['kokoro-onnx','onnxruntime','numpy','soundfile']},
 'scenes':scenes,'cues':cues,
 'sources':[
  {'url':'https://github.com/thewh1teagle/kokoro-onnx','license':'MIT'},
  {'url':'https://huggingface.co/hexgrad/Kokoro-82M','license':'Apache-2.0'},
  {'url':'https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md','role':'Voice IDs and limitations'}
 ]
}
(out/'timeline.json').write_text(json.dumps(metadata,indent=2)+'\n')
srt='\n\n'.join(f"{i}\n{subtime(c['start'])} --> {subtime(c['end'])}\n{c['text']}" for i,c in enumerate(captions,1))+'\n'
(base/'captions'/'episode-01.en.srt').write_text(srt)
vtt='WEBVTT\n\n'+'\n\n'.join(f"{subtime(c['start'],'.')} --> {subtime(c['end'],'.')}\n{c['text']}" for c in captions)+'\n'
(base/'captions'/'episode-01.en.vtt').write_text(vtt)
print(json.dumps({k:v for k,v in metadata.items() if k not in ['scenes','cues','sources','voice_map']},indent=2),flush=True)
