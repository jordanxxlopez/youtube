from pathlib import Path
import json,re,hashlib
from dataclasses import asdict
import soundfile as sf,numpy as np,onnxruntime as ort
from kokoro_onnx import Kokoro
ort.disable_telemetry_events()
root=Path('/workspace/youtube/episodes/episode-01/audio-tests')
opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
sess=ort.InferenceSession('/workspace/tools/voice-models/kokoro-v1.0.onnx',sess_options=opts,providers=['CPUExecutionProvider'])
k=Kokoro.from_session(sess,'/workspace/tools/voice-models/voices-v1.0.bin')
original="One soft ball. Two hands. I can do this. Oh! That was almost a catch. Dani, can we try that again?"
performed="One soft ball... two hands. I can do this! Oh! That was almost a catch. Dani, can we try that again?"
ph=k.tokenizer.phonemize(performed,'en-us').replace(k.tokenizer.phonemize('Dani','en-us').strip(),'dˈɑːni')
a,sr,timings=k.create_timed(ph,voice='am_puck',speed=0.77,lang='en-us',is_phonemes=True)
p=root/'teo-prosody-audition.wav';sf.write(p,a,sr,subtype='PCM_16')
info={'status':'Prosody audition; provisional local synthetic performance, not final voice casting','original_text':original,'spoken_words':performed,'change':'Same words; punctuation changed to suggest a little gathering confidence followed by surprise. One continuous synthesis pass preserves flow.','voice_id':'am_puck','speed':0.77,'duration_seconds':len(a)/sr,'words_per_minute':len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",performed))/(len(a)/sr)*60,'sample_rate':sr,'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'phonemes':ph,'model_outputs':[{'name':o.name,'shape':o.shape,'type':o.type} for o in sess.get_outputs()],'has_native_phoneme_timings':k.has_timings,'alignment_note':'Native per-phoneme timing comes from the model duration output, mapped to the generated waveform by kokoro-onnx and adjusted for trimming and inserted pauses. This is model-derived timing, not human-verified forced alignment. Existing full-episode SRT timing remains approximate within each line and must not be reused as a lip-sync track.', 'phoneme_timings':[asdict(t) for t in timings],'performance_limits':'Kokoro responds to text, punctuation, voice and rate; it does not provide explicit emotional acting control or a guaranteed requested performance.'}
groups=[];group=[]
for item in info['phoneme_timings']:
 if item['phoneme'].isspace():
  if group:groups.append(group);group=[]
 else:group.append(item)
if group:groups.append(group)
words=performed.split()
if len(groups)==len(words):
 info['word_timings']=[]
 for word,group in zip(words,groups):
  sounds=[t for t in group if t['phoneme'] not in '.,!?;:ˈˌː']
  info['word_timings'].append({'word':word,'phonemes':''.join(t['phoneme'] for t in group),'start':sounds[0]['start'],'end':sounds[-1]['end']})
 info['word_timing_method']='The whitespace-delimited phoneme groups map one-to-one to the spoken words in this audition. Native model-duration boundaries omit punctuation/stress-only spans; no proportional placement.'
else:
 info['word_timing_method']='No word mapping emitted because native phoneme group count differs from the text word count. Use native phoneme timing directly.'
(root/'teo-prosody-audition.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps({k:v for k,v in info.items() if k not in ['phoneme_timings','phonemes']},indent=2))
print('Native phoneme entries:',len(timings))
