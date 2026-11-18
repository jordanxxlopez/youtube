# Cinematic production routes

Researched November 18, 2026. These are capability findings and planning
estimates, not completed renders or an approved spending budget. Follow
[the cinematic brief](CINEMATIC_BRIEF.md) and preserve both approved Teo designs.

## Recommended: the benchmark model through fal

The user's selected performance test used Kling O3 Pro through Runway. fal
hosts the same model, making it the closest researched alternative host.
Using the same model does not guarantee identical output or perfect continuity.

[Kling O3 Pro on fal](https://fal.ai/models/fal-ai/kling-video/o3/pro/image-to-video)
accepts a starting image, optional ending image, action prompt, and audio
generation controls. Published base rates are $0.112 per second without native
audio and $0.14 with it. One pass of 600 generated seconds with native audio is
$84 per version, or $168 for both. This is a generation floor, not the finished
production price: retries, unused footage, reference options, and separate
lip-sync processing can add cost.

For a consistent prerecorded performance, generate the acting to the dialogue's
duration and emphasis, then use uploaded-audio lip sync. fal exposes a
[Kling LipSync API](https://fal.ai/models/fal-ai/kling-video/lipsync/audio-to-video/api)
with video and audio inputs. Its current wrapper accepts 2–10-second source
videos at 720p/1080p; native Kling's broader capabilities must not be assumed
available through this wrapper. The pricing page's billing sentence and
marketing table disagree about units, so verify an actual quote before batching.
Face detection and preservation of Teo's face must be checked in both styles.

The fal plugin became connected during research. Live schema reads confirmed
Kling O3 Pro image-to-video (3–15 seconds), Kling LipSync (2–10-second source
video), and LTX-2.3 audio-to-video are exposed. Live pricing returned $0.14 per
second for O3 Pro, $0.10 per second for LTX, and $0.014 per billing unit for
LipSync. The LipSync unit-to-duration rule is not clarified by that API, so its
full-film price remains an estimate. Configuration-specific charges may differ.
Importing the approved opening reference returned a billing block: the
connected account reported exhausted credits, with uploads and generation
unavailable. Browse/schema/pricing calls remain available. No import or paid
generation succeeded in this research pass. Resume only after the user resolves
the credit block; then check readiness and retain the existing source images.

## Alternative: LTX with the exact voice as input

[LTX-2.3 audio-to-video on fal](https://fal.ai/models/fal-ai/ltx-2.3/audio-to-video)
accepts recorded audio, a scene image, and a prompt. It generates scene motion
conditioned on the actual recording. Listed cost is $0.10 per generated second:
$60 per ten-minute version, or $120 for both before retries and other work.
Its quality with Teo has not been verified against the user's Kling benchmark.
The live fal schema calls this endpoint Pro and limits Pro input audio to ten
seconds; do not apply the direct provider's twenty-second limit to fal.

The [direct LTX API](https://docs.ltx.io/api-documentation/api-reference/async-video-generation/submit-audio-to-video)
offers 2–20-second audio-driven shots at 720p/1080p. Its separate
[direct pricing](https://docs.ltx.io/pricing/) is $0.06/sec at 720p and $0.10/sec
at 1080p for LTX-2.3 Pro audio-to-video. Direct API funds, fal billing, and LTX
Studio subscriptions are distinct; do not mix their prices or credit allowances.

## Estimate for the current full-length shot plan

The [95-shot plan](CINEMATIC_SHOT_PLAN.md) covers exactly 600 seconds per
version. Whole-second generation requests total 642 seconds per version,
including footage trimmed at edit boundaries, or 1,284 seconds for both.
The connected fal estimate is **$179.76** at its returned $0.14/sec base rate.
The published audio-off rate would imply **$143.81**, with a separate lip-sync
pass. Neither is a final configured quote or a complete production budget.
Both exclude retries, new scene references, voice revisions, and lip-sync costs.
Do not render all 1,284 seconds until the credit block is resolved, the voice
workflow is settled, and the spending cap is established.

## Production structure

Build two complete 600-second edits from cinematic acting shots. Short model
output limits apply to individual shots, not the finished episode. Prepare
separate scene references for each approved style, consistent environments,
prop positions, screen direction, and entrances/exits. Keep a single approved
voice performance per character across cuts and both versions. Finalize its
rhythm, pauses, emphasis, and emotion before final lip sync; music and effects
can be mixed afterward. Review identity, movement, interactions, mouth timing,
and continuity throughout each take, not only the first and last frames.

Revise the existing script's staging before production: action must unfold
inside the story environments, rather than surrounding a stationary presenter
with diagrams. Retain accurate science and meaningful viewer participation.

Long duration alone is not sufficient: HeyGen's
[Avatar IV/V motion controls](https://help.heygen.com/en/articles/12805098-fine-tune-avatar-gestures-and-movements-with-custom-motion-prompts-avatar-iv-v)
do not direct walking, prop actions, or scene changes. Hedra Character 3's long
talking-character support likewise does not establish the full cinematic
performance requested. They are not substitutes for this production brief.
