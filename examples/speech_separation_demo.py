#!/usr/bin/env python3
"""Demonstrate speaker separation and user-preference selection.

Loads a multi-speaker recording from the `datasets/multispeaker_audio`
folder, applies a simple NMF-based source separation, and then
chooses one of the estimated streams according to a user-specified
preference (e.g. loudest speaker, highest pitch).  The chosen track
and all estimated components are saved for later listening.
"""

import argparse
import os
from pathlib import Path

import numpy as np
from scipy.io import wavfile

# add src to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audio.speech_separation import separate_with_preference


def load_dataset_audio(condition: str, filename: str):
    """Load WAV file from multispeaker dataset directory."""
    path = Path("datasets/multispeaker_audio") / condition / filename
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    sr, audio = wavfile.read(str(path))
    audio = audio.astype(np.float32) / 32767.0
    return sr, audio


def save_audio(audio: np.ndarray, sr: int, output_path: Path):
    # convert back to int16 for compatibility with players
    int16 = np.int16(audio / np.max(np.abs(audio) + 1e-8) * 32767)
    wavfile.write(str(output_path), sr, int16)


def main():
    parser = argparse.ArgumentParser(description="Speech separation demo")
    parser.add_argument("--condition", default="clean",
                        help="Dataset condition (clean, office_noise_12db, etc.)")
    parser.add_argument("--scenario", default="office_4speaker.wav",
                        help="Filename of the scenario to load")
    parser.add_argument("--preference", default="loudest",
                        choices=["loudest", "quietest", "highest_pitch", "lowest_pitch"],
                        help="Which separated speaker to select")
    parser.add_argument("--output-dir", default="output_separation",
                        help="Directory where separated tracks will be written")
    parser.add_argument("--n-sources", type=int, default=2,
                        help="Number of speakers to estimate")

    args = parser.parse_args()

    sr, mix = load_dataset_audio(args.condition, args.scenario)
    print(f"Loaded {args.scenario} ({args.condition}), length {len(mix)/sr:.2f}s")

    chosen, sources = separate_with_preference(
        mix, sr, preference=args.preference, n_sources=args.n_sources
    )

    os.makedirs(args.output_dir, exist_ok=True)
    save_audio(chosen, sr, Path(args.output_dir) / "chosen.wav")

    for idx, src in enumerate(sources, start=1):
        save_audio(src, sr, Path(args.output_dir) / f"component_{idx}.wav")

    print(f"Saved {len(sources)} components and chosen track to {args.output_dir}")

if __name__ == "__main__":
    main()
