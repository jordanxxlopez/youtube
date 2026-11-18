# Episode 1 — The Brain Team Challenge

The deliverables are a **ten-minute 2D video and a ten-minute 3D-style video**
using the existing approved Teo artwork. The local pipeline preserves the
canonical PNGs and animates derived layers, mouth poses, blinking, gentle
head/body movement and small articulated steps. It uses no external video
service. The shaded version animates the approved illustration; it is not a
newly modeled, fully rotatable 3D character.

## Playback and source

Final working playback files:

- `exports/episode-01-2d.mp4`
- `exports/episode-01-3d-style.mp4`

Both outputs are 1280 × 720, 24 fps, H.264/AAC with English captions and chapter
metadata. Final export validation records duration, decoded frames, hashes
and review limits. Playback files are delivered in the conversation and kept
in working storage; the repository contains the reproducible production sources.

- [Local animation pipeline](animation/README.md)
- [Script and scene directions](script.md)
- [Structured dialogue](dialogue.json)
- [Science notes and sources](science-notes.md)
- [Full dialogue listening copy](audio/episode-01-dialogue.mp3)
- [Measured dialogue timeline](audio/timeline.json)
- [Mouth timing and provenance](animation/lipsync/README.md)
- [English captions](captions/episode-01.en.srt)
- [Character appearance and acting rules](../../characters/teo/CHARACTER_LOCK.md)

The measured dialogue and authored action holds total 595.968625 seconds.
Cumulative scene boundaries reach 596 seconds of picture; a four-second closing
card completes exactly 600 seconds, 14,400 frames. Voices are not stretched and
short video tests are not repeated to fill the runtime.

## Animation and review

The output is an illustrated educational first cut with limited cutout
animation. The source images supply one view and hands-in-pockets poses, so
body movement remains modest. Dialogue uses recorded stock synthetic voices.
Rhubarb's audio-derived mouth cues drive visible speaking poses with brief
blended transitions. Pauses return to the approved resting expression.
Automated timing and sampled frame inspection do not replace a complete
human audiovisual review of naturalness and precise articulation.

The earlier external-generation cost/shot proposal remains in
`production/render-scope.json` and `production/edit-plan.json` as historical
planning. It is not a dependency, purchase request, or blocker for the local
pipeline. `production/local_assemble.py` is the current delivery path.
