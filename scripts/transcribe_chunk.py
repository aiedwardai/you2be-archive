#!/usr/bin/env python3
"""Transcribe one 300s chunk of an audio file with faster-whisper small.
Usage: transcribe_chunk.py <audio> <start_sec> <duration_sec> <out_jsonl>
Appends segments (absolute times) as jsonl lines: {"start":..,"end":..,"text":..}
Follows the verified All-In pipeline rules for this machine:
- ffmpeg decodes to f32le 16k mono raw, numpy feeds the model (no decode_audio)
- cpu int8, language=en, vad_filter=True
"""
import json
import os
import subprocess
import sys

os.environ["no_proxy"] = "localhost,127.0.0.1"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["HF_HUB_OFFLINE"] = "1"

import numpy as np
from faster_whisper import WhisperModel


def main() -> int:
    audio, start, dur, out_path = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", audio,
         "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True,
    ).stdout
    samples = np.frombuffer(raw, dtype=np.float32)
    if samples.size == 0:
        return 0
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(samples, language="en", vad_filter=True)
    with open(out_path, "a", encoding="utf-8") as f:
        for seg in segments:
            f.write(json.dumps({
                "start": round(start + seg.start, 2),
                "end": round(start + seg.end, 2),
                "text": seg.text.strip(),
            }, ensure_ascii=False) + "\n")
        f.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
