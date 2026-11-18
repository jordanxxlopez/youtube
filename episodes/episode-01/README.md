# Episode 1 — The Brain Team Challenge

**Current direction, 2026-11-18:** Create a complete ten-minute 2D episode and
a complete ten-minute stylized 3D episode in which the approved Teo naturally
speaks, walks, gestures, and interacts with props inside continuous environments.
The user approved the original full-scene 3D speaking/walking test as the
performance and staging benchmark. The cinematic episodes have not been made.

Start with the [cinematic production brief](production/CINEMATIC_BRIEF.md),
[full-length shot plan](production/CINEMATIC_SHOT_PLAN.md), and
[workflow/pricing findings](production/CINEMATIC_OPTIONS.md).
The benchmark is `motion/3d/performance-test.mp4`, generated with Kling O3 Pro
under task `ca5e3633-9648-452e-9a07-8818a275344b`, with
`keyframes/opening-3d.png` as the scene reference. Benchmark approval does not
select a provider for the full production. Research into alternative AI services
and plugins is authorized. This research pass made no additional paid
generations; a replacement service and its production budget are not yet set.

## Rejected local cuts — retained for provenance

The user rejected both local cutout films and their simulation/lecture-panel
presentation. These are historical drafts, **not accepted deliverables and not
the current production direction**:

- `exports/episode-01-2d.mp4`
- `exports/episode-01-3d-style.mp4`

Both historical outputs are complete 600-second, 720p/24 fps H.264/AAC files
with captions and chapters. Their frame counts, hashes, and sampled visual
checks document their construction; they do not indicate creative acceptance.
Preserve them rather than overwrite them with cinematic versions. The
[delivery manifest](exports/delivery-manifest.json) records their rejection.
Playback files remain in working storage; production sources are retained.
The [local animation documentation](animation/README.md) is historical.

## Existing story and science materials

- [Script and scene directions](script.md)
- [Structured dialogue](dialogue.json)
- [Science notes and sources](science-notes.md)
- [Draft dialogue listening copy](audio/episode-01-dialogue.mp3)
- [Measured draft dialogue timeline](audio/timeline.json)
- [Draft mouth timing and provenance](animation/lipsync/README.md)
- [Draft English captions](captions/episode-01.en.srt)
- [Character appearance and acting rules](../../characters/teo/CHARACTER_LOCK.md)

The existing dialogue and authored holds total 595.968625 seconds. The rejected
cuts used 596 seconds of picture and a four-second closing card. This timing is
provenance for those cuts, not a requirement to reuse their recordings or staging.
Simulation-specific dialogue may need revision for the cinematic treatment;
review it once the production workflow is selected, then regenerate affected
performances, lip sync, captions, and timing. Do not silently substitute a new
voice under an already animated speaking shot.

`production/local_assemble.py` reproduces the rejected cuts only. The earlier
`production/render-scope.json` and `production/edit-plan.json` are historical
proposals, not the current approved shot plan or a purchase authorization.
