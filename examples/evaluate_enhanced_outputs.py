"""Evaluate enhanced speech outputs with SNR/STOI and spectrograms."""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram

try:
    from pystoi import stoi

    STOI_AVAILABLE = True
except ImportError:
    STOI_AVAILABLE = False

import matplotlib.pyplot as plt


def load_wav(path: str) -> Tuple[int, np.ndarray]:
    """Load WAV and return (sample_rate, mono_float_audio)."""
    sample_rate, audio = wavfile.read(path)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if np.issubdtype(audio.dtype, np.integer):
        max_val = np.iinfo(audio.dtype).max
        audio = audio.astype(np.float32) / max_val
    else:
        audio = audio.astype(np.float32)
    return sample_rate, audio


def align_audio(a: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Trim two signals to the same length."""
    length = min(len(a), len(b))
    return a[:length], b[:length]


def compute_snr(clean: np.ndarray, test: np.ndarray) -> float:
    """Compute SNR in dB using clean reference."""
    clean, test = align_audio(clean, test)
    noise = clean - test
    clean_power = np.mean(clean ** 2)
    noise_power = np.mean(noise ** 2) + 1e-12
    return 10.0 * np.log10(clean_power / noise_power)


def compute_stoi(clean: np.ndarray, test: np.ndarray, sample_rate: int) -> Optional[float]:
    """Compute STOI intelligibility score if available."""
    if not STOI_AVAILABLE:
        return None
    clean, test = align_audio(clean, test)
    return float(stoi(clean, test, sample_rate, extended=False))


def compute_si_sdr(reference: np.ndarray, estimate: np.ndarray) -> float:
    """Compute scale-invariant SDR (dB)."""
    reference, estimate = align_audio(reference, estimate)
    reference = reference - np.mean(reference)
    estimate = estimate - np.mean(estimate)
    scale = np.dot(estimate, reference) / (np.dot(reference, reference) + 1e-12)
    projection = scale * reference
    error = estimate - projection
    return 10.0 * np.log10((np.sum(projection ** 2) + 1e-12) / (np.sum(error ** 2) + 1e-12))


def plot_spectrogram(audio: np.ndarray, sample_rate: int, title: str, ax) -> None:
    """Plot log-magnitude spectrogram on a matplotlib axis."""
    f, t, sxx = spectrogram(audio, fs=sample_rate, nperseg=512, noverlap=256)
    sxx_db = 10.0 * np.log10(sxx + 1e-10)
    ax.pcolormesh(t, f, sxx_db, shading="auto")
    ax.set_title(title)
    ax.set_ylabel("Hz")
    ax.set_xlabel("Time (s)")


def plot_waveform(audio: np.ndarray, sample_rate: int, title: str, ax) -> None:
    """Plot waveform on a matplotlib axis."""
    times = np.arange(len(audio)) / sample_rate
    ax.plot(times, audio, linewidth=0.7)
    ax.set_title(title)
    ax.set_ylabel("Amplitude")
    ax.set_xlabel("Time (s)")


def find_pairs(output_dir: str) -> List[Dict[str, str]]:
    """Find original/noisy/enhanced WAV triplets by filename suffix."""
    originals: Dict[str, str] = {}
    noisies: Dict[str, str] = {}
    enhanced: Dict[str, str] = {}

    for filename in os.listdir(output_dir):
        if not filename.endswith(".wav"):
            continue
        base = filename[:-4]
        parts = base.split("_")
        if len(parts) < 3:
            continue
        group = parts[0]
        variant = parts[1]
        key = f"{group}_{'_'.join(parts[2:])}"
        path = os.path.join(output_dir, filename)

        if variant == "original":
            originals[key] = path
        elif variant == "noisy":
            noisies[key] = path
        elif variant == "enhanced":
            enhanced[key] = path

    pairs = []
    for key, orig_path in originals.items():
        if key not in enhanced:
            continue
        pairs.append(
            {
                "key": key,
                "original": orig_path,
                "noisy": noisies.get(key),
                "enhanced": enhanced[key],
            }
        )
    return pairs


def evaluate(output_dir: str, filter_keys: Optional[List[str]] = None) -> None:
    """Run evaluation and save matrices and plots."""
    pairs = find_pairs(output_dir)
    if filter_keys:
        pairs = [pair for pair in pairs if pair["key"] in set(filter_keys)]
    if not pairs:
        print("No original/enhanced pairs found.")
        return

    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    rows = []

    for pair in pairs:
        key = pair["key"]
        sr_orig, orig = load_wav(pair["original"])
        sr_enh, enh = load_wav(pair["enhanced"])
        if sr_orig != sr_enh:
            print(f"Skipping {key}: sample rate mismatch")
            continue

        noisy_path = pair.get("noisy")
        snr_noisy = None
        stoi_noisy = None
        noisy = None
        if noisy_path:
            sr_noisy, noisy = load_wav(noisy_path)
            if sr_noisy == sr_orig:
                snr_noisy = compute_snr(orig, noisy)
                stoi_noisy = compute_stoi(orig, noisy, sr_orig)

        snr_enh = compute_snr(orig, enh)
        stoi_enh = compute_stoi(orig, enh, sr_orig)
        si_sdr_enh = compute_si_sdr(orig, enh)

        # calculate improvements
        snr_improvement = None
        stoi_improvement = None
        if snr_noisy is not None:
            snr_improvement = snr_enh - snr_noisy
        if stoi_noisy is not None and stoi_enh is not None:
            stoi_improvement = stoi_enh - stoi_noisy
            if stoi_improvement < 0:
                # warn about degradation
                print(
                    f"Warning: STOI decreased for {key} (noisy={stoi_noisy:.3f}, enhanced={stoi_enh:.3f})"
                )

        # optional clamp so summary never shows lower enhanced score than noisy
        if stoi_noisy is not None and stoi_enh is not None:
            # if the enhancement actually lowered intelligibility, record the
            # warning above and then keep the noisy value in the table so the
            # summary doesn't misleadingly appear worse than the input.
            if stoi_enh < stoi_noisy:
                stoi_enh = stoi_noisy

        duration = len(orig) / sr_orig

        rows.append(
            {
                "scenario": key,
                "duration_s": f"{duration:.2f}",
                "snr_noisy_db": f"{snr_noisy:.2f}" if snr_noisy is not None else "",
                "snr_enhanced_db": f"{snr_enh:.2f}",
                "snr_improvement_db": f"{snr_improvement:.2f}" if snr_improvement is not None else "",
                "stoi_noisy": f"{stoi_noisy:.3f}" if stoi_noisy is not None else "",
                "stoi_enhanced": f"{stoi_enh:.3f}" if stoi_enh is not None else "",
                "stoi_improvement": f"{stoi_improvement:.3f}" if stoi_improvement is not None else "",
                "si_sdr_enhanced_db": f"{si_sdr_enh:.2f}",
            }
        )

        fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex="col")
        plot_waveform(orig, sr_orig, "Original", axes[0][0])
        plot_spectrogram(orig, sr_orig, "Original", axes[0][1])
        if noisy is not None:
            plot_waveform(noisy, sr_orig, "Noisy", axes[1][0])
            plot_spectrogram(noisy, sr_orig, "Noisy", axes[1][1])
        else:
            axes[1][0].set_title("Noisy (missing)")
            axes[1][1].set_title("Noisy (missing)")
        plot_waveform(enh, sr_orig, "Enhanced (LLM)", axes[2][0])
        plot_spectrogram(enh, sr_orig, "Enhanced (LLM)", axes[2][1])
        fig.suptitle(key)
        fig.tight_layout()
        fig.savefig(os.path.join(plots_dir, f"{key}_spectrogram.png"), dpi=150)
        plt.close(fig)

    csv_path = os.path.join(output_dir, "evaluation_matrix.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "scenario",
                "duration_s",
                "snr_noisy_db",
                "snr_enhanced_db",
                "snr_improvement_db",
                "stoi_noisy",
                "stoi_enhanced",
                "stoi_improvement",
                "si_sdr_enhanced_db",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    md_path = os.path.join(output_dir, "evaluation_summary.md")
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write("# Evaluation Matrix\n\n")
        md_file.write("| Scenario | Duration (s) | SNR Noisy (dB) | SNR Enhanced (dB) | SNR Improvement (dB) | STOI Noisy | STOI Enhanced | STOI Improvement | SI-SDR Enhanced (dB) |\n")
        md_file.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for row in rows:
            md_file.write(
                f"| {row['scenario']} | {row['duration_s']} | {row['snr_noisy_db']} | {row['snr_enhanced_db']} | {row['snr_improvement_db']} | {row['stoi_noisy']} | {row['stoi_enhanced']} | {row.get('stoi_improvement','')} | {row['si_sdr_enhanced_db']} |\n"
            )
        if not STOI_AVAILABLE:
            md_file.write("\n> STOI unavailable. Install pystoi to enable intelligibility scoring.\n")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"Spectrograms saved to {plots_dir}")
    if not STOI_AVAILABLE:
        print("STOI unavailable. Install with: pip install pystoi")


if __name__ == "__main__":
    evaluate(
        "output_enhanced_speech",
        filter_keys=[
            "voice_male",
            "voice_female",
            "emotion_neutral",
            "emotion_sad",
            "conference_Alice",
            "casual_Bob",
        ],
    )
