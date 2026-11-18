#!/usr/bin/env python3
"""Make sparse, original interface/soft-ball effects; no samples or music."""
from pathlib import Path
import argparse
import json
import wave
import numpy as np


def create_effects(timeline_path, output_path):
    timeline = json.loads(Path(timeline_path).read_text())
    rate = 24000
    track = np.zeros(round(timeline['duration_seconds'] * rate), dtype=np.float32)
    events = []
    for cue in timeline['cues']:
        if cue['kind'] != 'action':
            continue
        start = cue['start_seconds'] + 0.08
        # Explicit action holds only. Never fill the three-second answer pauses.
        duration = min(0.52, cue['duration_seconds'] - 0.12)
        if duration <= 0:
            continue
        t = np.arange(round(duration * rate), dtype=np.float64) / rate
        if cue['scene_id'] == 'scene-01':
            # A restrained soft contact, synthesized from a decaying low tone.
            wave_data = (np.sin(2*np.pi*(105*t - 28*t*t)) * np.exp(-17*t)
                         + .2*np.sin(2*np.pi*62*t)*np.exp(-22*t))
            kind = 'soft_contact'
            gain = .032
        else:
            pitch = 550 if cue['scene_id'] != 'scene-08' else 660
            wave_data = (np.sin(2*np.pi*pitch*t)*np.exp(-8*t)
                         + .28*np.sin(2*np.pi*pitch*1.5*t)*np.exp(-12*t))
            kind = 'quiet_marker_chime'
            gain = .012
        # Gentle onset; no impulses/clicks. The effects sit well below dialogue.
        wave_data *= np.minimum(t/.014, 1.0) * gain
        a = round(start*rate)
        b = min(a+len(wave_data), len(track))
        track[a:b] += wave_data[:b-a]
        events.append({'scene_id':cue['scene_id'],'start_seconds':start,
                       'duration_seconds':duration,'kind':kind,'peak_gain':gain})
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes((np.clip(track, -1, 1)*32767).astype('<i2').tobytes())
    manifest = {'origin':'Original procedural sine-wave effects; no samples or music',
                'sample_rate':rate,'duration_seconds':len(track)/rate,
                'viewer_pause_effects':False,'events':events}
    output_path.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(create_effects(args.timeline,args.output),indent=2))
