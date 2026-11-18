# Free local voice auditions

These are generated voice auditions for the first episode, not a permanent
voice lock. Both use existing stock voice packs; no person's voice was cloned.

- `teo-voice-sample.wav`: `am_puck`, American English masculine voice.
- `dani-voice-sample.wav`: `af_heart`, American English feminine voice.
- `provenance.json`: exact spoken text, settings, timings, model/voice hashes,
  source links and limitations.
- `teo-prosody-audition.wav`: a separate 8.7-second opening-line performance at
  about 145 words per minute. The words are unchanged; punctuation suggests
  gathering confidence and surprise in one continuous synthesis pass.
- `teo-prosody-audition.json`: native model-derived phoneme timings and the
  matching word spans for that audition. This export exposes a `duration`
  output, accessed through `Kokoro.create_timed`. These are not the approximate
  SRT subdivisions used for the full draft soundtrack.
- `teo-voice-normal-rate.wav` and `dani-voice-normal-rate.wav`: faster comparison
  auditions. The main voice-sample files use the slower children's pacing.

Speech is synthesized locally on the CPU. It does not require Runway, a paid
API, or a GPU. Model and dependency downloads require network access; subsequent
synthesis works offline. Both audio files use 24 kHz mono, 16-bit PCM WAV.

## Reproduce in this workspace

```sh
python -m venv /workspace/tools/voice-venv
/workspace/tools/voice-venv/bin/pip install -r requirements.txt
mkdir -p /workspace/tools/voice-models
curl -L --fail -o /workspace/tools/voice-models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
curl -L --fail -o /workspace/tools/voice-models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
/workspace/tools/voice-venv/bin/python generate_samples.py
```

Run the commands from this directory. The script's paths are explicit workspace
paths; adapt them when using another computer. It disables ONNX Runtime telemetry
and explicitly selects CPU inference with three worker threads.

## Sources and licensing

The [kokoro-onnx package](https://github.com/thewh1teagle/kokoro-onnx) is MIT
licensed. Its license is retained alongside these instructions. The upstream
[Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M) identifies the model
weights as Apache 2.0 and describes the training data provenance. See the
[published voice notes](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
for the stock voice IDs and known quality limitations.

This removes the paid speech-generation dependency. It does not create character
animation, lip sync, or a finished video. Review the performances and scientific
pronunciations before using them as final dialogue.

The timed audition can support a lip-sync prototype, but it does not create
mouth shapes or a face rig. Its timings are model predictions mapped to the
waveform, not manually verified alignment. Kokoro offers voice, punctuation,
and speed controls; it does not guarantee a particular emotional performance.
