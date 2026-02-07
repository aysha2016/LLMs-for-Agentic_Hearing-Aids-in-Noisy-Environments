"""Before/after demo for real speech processing."""

import os
import urllib.request
from urllib.error import URLError
from typing import Tuple

import numpy as np
from scipy.io import wavfile

from src.hearing_aid.controller import HearingAidController
from src.audio.speech_synthesizer import SpeechSynthesizer


SAMPLE_URL = "https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav"
OUTPUT_DIR = "output_audio"
SAMPLE_PATH = os.path.join(OUTPUT_DIR, "sample_speech.wav")
BEFORE_PATH = os.path.join(OUTPUT_DIR, "sample_before.wav")
AFTER_PATH = os.path.join(OUTPUT_DIR, "sample_after.wav")
TARGET_SR = 16000


def _download_sample(path: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return True
    try:
        print(f"Downloading sample speech to {path}...")
        urllib.request.urlretrieve(SAMPLE_URL, path)
        return True
    except URLError:
        return False


def _generate_synthetic_sample(path: str) -> None:
    print("Network unavailable. Generating a local synthetic speech sample...")
    synthesizer = SpeechSynthesizer(sample_rate=TARGET_SR, voice_profile="neutral")
    audio = synthesizer.synthesize_text(
        "This is a short sample sentence for the hearing aid before and after demo.",
        emotion="neutral"
    )
    _save_wav(path, TARGET_SR, audio)


def _to_float32(audio: np.ndarray) -> np.ndarray:
    if audio.dtype == np.int16:
        return (audio.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
    if audio.dtype == np.int32:
        return (audio.astype(np.float32) / 2147483648.0).clip(-1.0, 1.0)
    if audio.dtype == np.uint8:
        return ((audio.astype(np.float32) - 128.0) / 128.0).clip(-1.0, 1.0)
    return audio.astype(np.float32)


def _to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return audio.mean(axis=1)


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    ratio = target_sr / float(orig_sr)
    new_length = int(len(audio) * ratio)
    indices = np.linspace(0, len(audio) - 1, new_length)
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)


def _save_wav(path: str, sample_rate: int, audio: np.ndarray) -> None:
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767.0).astype(np.int16)
    wavfile.write(path, sample_rate, audio_int16)


def prepare_audio(path: str) -> Tuple[np.ndarray, int]:
    sample_rate, audio = wavfile.read(path)
    audio = _to_mono(audio)
    audio = _to_float32(audio)
    audio = _resample(audio, sample_rate, TARGET_SR)
    return audio, TARGET_SR


def main() -> None:
    if not _download_sample(SAMPLE_PATH):
        _generate_synthetic_sample(SAMPLE_PATH)

    audio, sample_rate = prepare_audio(SAMPLE_PATH)
    _save_wav(BEFORE_PATH, sample_rate, audio)

    controller = HearingAidController(sample_rate=sample_rate)
    result = controller.process_audio(audio, use_llm_decision=True, force_decision=True)
    processed = result["processed_audio"]
    _save_wav(AFTER_PATH, sample_rate, processed)

    print("Before/after demo complete:")
    print(f"- Input:  {SAMPLE_PATH}")
    print(f"- Before: {BEFORE_PATH}")
    print(f"- After:  {AFTER_PATH}")


if __name__ == "__main__":
    main()
