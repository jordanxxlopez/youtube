# Local episode animation

This pipeline uses the exact approved 2D and 3D-style Teo artwork. It creates
limited cutout animation with speaking mouths, blinking, small head and body
movements, and gentle articulated steps. The shaded version is an animated
illustration, not a new 3D model. No external video-generation service is used.

The approved PNGs remain unchanged. Artwork is segmented into alpha layers
without changing its RGB pixels. Local facial-performance derivatives replace
the resting mouth during speech and briefly close the eyes during blinks.
These are performance frames, not replacement character designs.

## Inputs

- The two immutable images under `characters/teo/images/`.
- The full recorded dialogue and measured `../audio/timeline.json`.
- `lipsync/lines/`: recording-derived Rhubarb mouth cues for all 72 lines.
- Scientific diagrams driven by the same dialogue and action timestamps.

## Reproduce from the repository root

The renderer requires Python, NumPy, Pillow, SciPy, OpenCV, and FFmpeg with
libx264 and libass. The tested OpenCV package is `opencv-python-headless==5.1.0.95`.
Install dependencies in a dedicated environment. The local scripts also check
`/workspace/tools/video-python` for the package installed during production.

1. Recreate the WAV dialogue using `audio/synthesize_episode.py` and its pinned
   voice/model dependencies if the working WAV files are absent. Preserve the
   measured timings; changing the performance requires regenerating timing.
2. Run `python episodes/episode-01/animation/prepare_assets.py` to derive the
   original-pixel cutout layers and pivots. Verify the canonical image hashes.
3. Existing Rhubarb timing files are included. To regenerate them from the same
   takes, follow `lipsync/README.md` and its pinned official download/license.
4. Run `python episodes/episode-01/production/render_diagrams.py --scene all
   --style both --timeline episodes/episode-01/audio/timeline.json` (one shell
   command, without the line break) to render progressing science backgrounds.
5. Run `python episodes/episode-01/production/local_render.py --style both
   --scene all` to composite all eight scenes for each appearance.
6. Run `python episodes/episode-01/production/local_assemble.py --render
   --styles 2d 3d` to mix voices with original sparse sound cues, burn English
   captions, add chapter metadata, and export the two complete videos.

Final working outputs are `../exports/episode-01-2d.mp4` and
`../exports/episode-01-3d-style.mp4`. Each contains 14,400 frames at 24 fps: 596
seconds of story picture, then a four-second closing card. The dialogue and
planned action holds occupy 595.968625 seconds. Cumulative scene frame boundaries
avoid drift from rounding every scene independently.

## Review boundaries

The source artwork provides one view and hands-in-pockets poses. Motion stays
modest to avoid inventing concealed body parts or changing the character.
Automatic mouth poses approximate speech and need visual review; expressive
performance is more than a sequence of phoneme labels. The complete videos
are an illustrated educational first cut, not full three-dimensional character
animation or fully hand-drawn frame-by-frame acting.

Large WAV masters, intermediate videos, and reproducible PNG layers remain
working assets. Keep final playback files separate from the source repository
unless a distribution destination is explicitly chosen.
