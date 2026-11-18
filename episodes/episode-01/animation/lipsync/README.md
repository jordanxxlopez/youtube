# Episode 1 mouth timing candidates

Rhubarb Lip Sync 1.14.0 (MIT) analyzes the existing, unchanged Kokoro line WAVs with each line's exact dialogue as a pronunciation hint. This provides a free local route to reusable mouth animation timing for both character styles. These files are **timing candidates**, not finished animation or verified precision lip sync.

## Files

- `first-line-proof.json`: the successful first 8.35-second line proof (41 mouth cues).
- `lines/<line_id>.json`: upstream Rhubarb output in local line seconds: `mouthCues[].start`, `end`, `value`.
- `dialogue/<line_id>.txt`: the exact input sentence supplied to Rhubarb.
- `episode-mouth-cues.json`: all line metadata; episode-time `cues[]`; and complete `speaker_tracks` for all five characters, including X/rest during silence through 600 seconds.
- `validation.json`: coverage, cue bounds, source consistency and unchanged-audio checks.
- `RHUBARB-source.json` and `RHUBARB-LICENSE.md`: pinned download URL, archive SHA-256 and complete upstream license/third-party notices.

The repository also includes [the compressed combined timing archive](episode-mouth-cues.json.gz). Decompress it to obtain the full `episode-mouth-cues.json`; per-line JSON files can be consumed directly by the local renderer.

## Timing and retargeting

The authoritative audio timeline is `../../audio/timeline.json`. Add its dialogue `start_seconds` to a raw Rhubarb cue's local time. The combined file already performs this conversion. Rhubarb exports centiseconds; the remaining sub-centisecond line tail is rest. Cues follow the 595.968625-second spoken guide and its authored holds, then rest through the 600-second edit. They do not apply to the independent Runway test audio.

A = closed P/B/M; B = narrow consonant/EE; C = open EH/AE; D = wide AA; E = rounded AO/ER; F = puckered UW/OW/W; G = F/V with lower lip near upper teeth; H = long L; X = relaxed closed rest. These labels approximate sound groups, not exact phoneme transcripts.

Map these values to approved mouth assets or facial controls. Preserve the reference face and proportions. Blend brief transitions and visually check closures, vowel shapes, facial expressions and body acting. The timing output alone does not supply artwork, a rig, expressive acting or fluid motion. No character assets were edited by this pipeline.

## Reproduce

Download and extract the pinned official Linux archive in `RHUBARB-source.json`, verify its SHA-256, and make its `rhubarb` binary executable. The supplied script uses only the Python standard library and the Rhubarb executable:

```bash
python episodes/episode-01/animation/lipsync/generate_lipsync.py \
  --episode /workspace/youtube/episodes/episode-01 \
  --rhubarb /workspace/tools/rhubarb/Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb
```

It runs two concurrent line jobs, each limited to two recognizer threads. Individual command:

```bash
rhubarb -q -f json -r pocketSphinx --threads 2 --extendedShapes GHX \
  -d exact-dialogue.txt -o mouth-cues.json existing-line.wav
```

Upstream: https://github.com/DanielSWolf/rhubarb-lip-sync/tree/v1.14.0
