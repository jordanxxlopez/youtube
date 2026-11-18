# Full cinematic shot plan — Episode 1

**Draft plan, not generated footage or an approved spend.** Both styles use the same 600-second edit and existing dialogue master. The approved 3D performance test is the acting benchmark; each style retains its own canonical character reference.

The plan contains **95 shots per version: 94 original story shots and one four-second credit shot**. All story shots run 3–10 seconds, compatible with the supplied Kling O3 Pro 3–15-second generation range and fal lip-sync 2–10-second input range. Natural line boundaries are preferred; longer lines continue across motivated camera cuts. All six viewer pauses remain intact.

## Runtime and job quantities

- Finished picture: 596 seconds of story + 4 seconds of credits = **600 seconds per style**.
- Rounded whole-second generation requests: **642 seconds per style / 1284 seconds for both**, before retries, extensions, reference creation or alternate takes. 46 excess seconds per style are trimmed, not used as filler.
- Teo visibly speaks in **41 shots per style**. Processing just those complete edited shots would theoretically use **76 five-second chunks / 380 billable seconds per style**.
- Applying lip sync to every one of the 94 story shots, even those without a visible speaker: **174 five-second chunks / 870 billable seconds per style**. Hypothetically including credits: **175 chunks / 875 seconds**. This is quantity arithmetic, not a provider quote or a reason to process silent/object shots.

Each request preserves the source timing. The final speech ends at 595.968625 seconds; picture reaches the next safe boundary at 596.000, then credits end at exactly 600.000. The JSON uses authoritative integer frame intervals at 24 fps, with no gaps or overlaps.

## Scene progression

| Scene | Edit window | Shots | Staging |
|---|---|---:|---|
| scene-01: A catch becomes a mystery | 00:00.000–00:57.917 | 10 | Entrance and near pedestal rim: establish window left, central projector right, microscope shelf at rear right; catch direction is off-screen left toward Teo. |
| scene-02: The clue from our eyes | 00:57.917–01:56.958 | 10 | Clockwise move around the near pedestal toward its back-facing side; retain the same brain orientation and window-side light. |
| scene-03: Where are my hands? | 01:56.958–03:35.542 | 14 | Open demonstration space beside the near rim; volumetric hand models sit above the pedestal, not on a lecture panel. |
| scene-04: Listen to the clue | 03:35.542–04:34.958 | 10 | Window-side intercom shelf and its sightline to the central brain projection; keep a continuous route back to the catching area. |
| scene-05: Make a plan | 04:34.958–05:41.000 | 10 | Clear catching area in front of the central pedestal; frontal region remains an in-world object behind Teo. |
| scene-06: The rest of the movement team | 05:41.000–07:32.792 | 17 | Lower-back side of brain projection; body-and-arm teaching model grows from the same pedestal, then Teo moves toward the microscope shelf. |
| scene-07: Meet the tiny teammates | 07:32.792–08:45.542 | 12 | Microscope shelf within the established lab; three cell-guide programs are projected teaching objects, not new canonical humanoid characters. |
| scene-08: One catch, a whole team | 08:45.542–09:56.000 | 11 | Return to the original clear catch axis and pedestal; finish toward the open arch without teleporting props or character. |
| Credits | 09:56.000–10:00.000 | 1 | Brief closing composition; no paid character generation needed. |

## Performance and continuity

Teo walks between connected areas of the approved lab, reaches for and handles the physical ball, rehearses hand positions, reacts to discoveries, and speaks with visible facial performance. The ball remains in a single cradle during the exploration, distinct from translucent replay models; the last scene returns to the opening catch axis for one complete catch. Dani remains an off-screen/intercom voice. Cell-guide voices accompany in-world teaching projections, with no invented canonical humanoid designs.

Camera moves, medium/full-body speaking shots, reactions, and close object inserts are specified individually in [cinematic-shot-plan.json](cinematic-shot-plan.json). Every shot records action, camera, environment/prop continuity, source dialogue IDs, visible speaker, generation duration, and lip-processing need. The hologram is an object in the room; fixed portrait panels and lecture-slide staging are excluded.

## Starting frames and lip-sync inputs

Prepare starting frames for each shot from the approved character and lab
references. The approved lab image shows Teo holding the ball; shot-001 instead
requires empty hands awaiting a toss. Use a separate derivative with that
starting pose, keeping the approved image unchanged. Match later starting
frames to their incoming camera, pose, and prop states.

All JSON asset paths resolve from the episode directory. Before lip sync, trim
each generated source to its exact planned 24-fps frame count and extract the
matching master-audio interval. Verify actual media duration and padding; a
10.041-second container is not a valid ten-second input. Preserve the continuous
master soundtrack without stretching it.

## Before a paid batch

Review the simulation/screen/diagram wording in `scene-01-line-04`, `scene-03-extra-01`, `scene-06-extra-01`, and `scene-07-line-01` against the cinematic staging. An in-world projection may support the wording; any revised recording requires updating the timing. Retain the no-shrinking, guide-program, teaching-symbol, and overlapping-brain-activity science clarifications. No dialogue has been rewritten or rerecorded for this plan.

The supplied dialogue timing is measured by line; proposed within-line cuts are not verified word boundaries. Listen or align words before paid speech processing, then adjust adjacent cut frames without introducing gaps or changing the 3–10-second limits. A consistent natural voice workflow and actual provider quote remain to be selected. The connected fal account currently blocks imports and generation because credits are exhausted. This plan performs no uploads, purchases, or generation.
