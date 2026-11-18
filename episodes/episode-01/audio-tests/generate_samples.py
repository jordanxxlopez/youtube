from pathlib import Path
import json, time, hashlib, importlib.metadata
import numpy as np
import soundfile as sf
import onnxruntime as ort
from kokoro_onnx import Kokoro

ort.disable_telemetry_events()

ROOT=Path('/workspace/youtube/episodes/episode-01/audio-tests')
MODELS=Path('/workspace/tools/voice-models')
options=ort.SessionOptions()
options.intra_op_num_threads=3
options.inter_op_num_threads=1
session=ort.InferenceSession(str(MODELS/'kokoro-v1.0.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
k=Kokoro.from_session(session,str(MODELS/'voices-v1.0.bin'))
items=[
    {'character':'Teo','voice_id':'am_puck','speed':0.80,'file':'teo-voice-sample.wav','text':"Hey, I'm Teo! Catching a ball looks easy, right? But inside your brain, a whole team is getting ready. Come on, let's meet them!"},
    {'character':'Dani','voice_id':'af_heart','speed':0.80,'file':'dani-voice-sample.wav','text':"Welcome to the Brain Dome, Teo. This is a model we can explore together. Your brain's different parts work as a team, all the time."}
]
for item in items:
    started=time.monotonic()
    samples,sr=k.create(item['text'],voice=item['voice_id'],speed=item['speed'],lang='en-us')
    sf.write(ROOT/item['file'],samples,sr,subtype='PCM_16')
    item['sample_rate']=sr
    item['duration_seconds']=round(len(samples)/sr,3)
    item['generation_seconds']=round(time.monotonic()-started,3)
    item['peak_amplitude']=float(np.max(np.abs(samples)))
    item['sha256']=hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()
    print(json.dumps(item),flush=True)
metadata={
    'created_on':'2026-11-18',
    'status':'voice_audition_not_final_character_voice_lock',
    'engine':'Kokoro 82M v1.0 via kokoro-onnx',
    'inference':'CPUExecutionProvider, entirely local after model download',
    'network_calls_for_synthesis':False,
    'paid_api_calls':False,
    'voices':'Stock synthetic voice packs; no personal recording or voice clone used',
    'package_versions':{n:importlib.metadata.version(n) for n in ['kokoro-onnx','onnxruntime','numpy','soundfile','phonemizer','espeakng-loader']},
    'sources':[
        {'url':'https://github.com/thewh1teagle/kokoro-onnx','role':'CPU inference package and official download instructions','license':'MIT'},
        {'url':'https://huggingface.co/hexgrad/Kokoro-82M','role':'Upstream model card','license':'Apache-2.0'},
        {'url':'https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md','role':'Voice metadata and quality limitations'},
    ],
    'downloaded_model':{'url':'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx','sha256':hashlib.sha256((MODELS/'kokoro-v1.0.onnx').read_bytes()).hexdigest()},
    'downloaded_voices':{'url':'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin','sha256':hashlib.sha256((MODELS/'voices-v1.0.bin').read_bytes()).hexdigest()},
    'limitations':['Synthetic speech is an audition for naturalness, not a human voice recording.','Very short utterances and long chunks can reduce prosody quality; render dialogue in sensible sentence groups.','Scientific terms and character-name pronunciation need review.','No emotional acting or lipsync is inferred from this audio alone.'],
    'samples':items
}
(ROOT/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
