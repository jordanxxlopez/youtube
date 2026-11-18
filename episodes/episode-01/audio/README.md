# Episode 1 — local generated dialogue

The shared dialogue recording is for both the 2D and 3D episode versions. This
folder contains speech and timing data, not a finished video or a final sound
mix. The six viewer-response pauses and authored visual-action holds are
included exactly as specified in `../dialogue.json`.

The extended dialogue and action track measures **9:55.969**. The planned
24 fps edit places a four-second closing card at **9:56–10:00**, after a
31-millisecond transition from the end of speech. That gives an exact
600-second video budget without stretching speech or repeating content.
`validation.json` records this plan separately from the audio's real duration.

## Files

- `episode-01-dialogue.wav`: complete mono 24 kHz, 16-bit PCM dialogue track.
- `episode-01-dialogue.mp3`: compressed listening copy of the same track.
- `lines/`: separate dialogue takes with settings and exact spoken text.
- `scenes/`: individual scene dialogue tracks for editing.
- `timeline.json`: measured scene, line, question-pause, and action timings.
- `../captions/episode-01.en.srt` and `.vtt`: captions using those measured line
  boundaries. Caption splits inside a line use proportional timing and should
  be checked against the performances during the edit.
- `synthesize_episode.py`: reproducible CPU-only synthesis and assembly script.
- `validate_audio.py`: checks audio integrity, script consistency, caption
  layout, and the exact 600-second planned edit budget.

The five voices use existing Kokoro voice packs. They are provisional synthetic
performances; no person was recorded or cloned. No paid API is involved.

| Character | Voice ID | Speed |
| --- | --- | --- |
| Teo | `am_puck` | 0.80 |
| Dani | `af_heart` | 0.80 |
| Neuron guide | `af_bella` | 0.84 |
| Astrocyte guide | `af_nicole` | 0.82 |
| Microglia guide | `am_fenrir` | 0.80 |

## Reproduce

Follow `../audio-tests/README.md` to install the pinned dependencies and download
the official model and stock voice pack, then run:

```sh
/workspace/tools/voice-venv/bin/python synthesize_episode.py --source /workspace/youtube/episodes/episode-01/dialogue.json --models /workspace/tools/voice-models
```

Existing matching line takes are reused; changed dialogue or settings trigger
new takes. Speech is generated offline after the initial downloads. The script
disables ONNX Runtime telemetry and explicitly selects CPU inference.

## Licensing and review

[kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) is MIT licensed;
[Kokoro's model weights](https://huggingface.co/hexgrad/Kokoro-82M) are Apache 2.0.
The corresponding license texts are retained here. Model and voice-pack
download hashes are recorded in `../audio-tests/provenance.json`.

Character-name pronunciation is set to Teo “TEH-oh” and Dani “DAH-nee.” Review
the scientific vocabulary, delivery, and caption placement before publishing.
Scientific names also have explicit phoneme overrides matching the script's
pronunciation guide. The source words and displayed captions remain unchanged.
The stock speech engine provides usable dialogue and distinct voices; it does
not supply facial performance, lip sync, or full character animation.
