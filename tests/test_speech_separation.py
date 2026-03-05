"""Unit tests for the speech separation utilities."""

import sys
from pathlib import Path
# include project root so that src package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from src.audio.speech_separation import (
    separate_sources,
    select_preferred_source,
    separate_with_preference,
)


def test_separate_two_sine_waves():
    # create mixture of two sine waves at different frequencies
    sr = 8000
    t = np.linspace(0, 1, sr, endpoint=False)
    s1 = np.sin(2 * np.pi * 200 * t).astype(np.float32)
    s2 = 0.5 * np.sin(2 * np.pi * 600 * t).astype(np.float32)
    mix = s1 + s2

    sources = separate_sources(mix, sr, n_sources=2)
    assert isinstance(sources, list)
    assert len(sources) == 2

    # each estimated source should be non-empty and have correct dtype
    for src in sources:
        assert len(src) > 0
        assert src.dtype == np.float32

    # verify that the two outputs are not trivially identical
    diff_norm = np.linalg.norm(sources[0] - sources[1])
    assert diff_norm > 1e-3


def test_preference_selection_basic():
    sr = 8000
    loud = np.ones(sr, dtype=np.float32)
    quiet = np.ones(sr, dtype=np.float32) * 0.1

    chosen = select_preferred_source([loud, quiet], sr, preference="loudest")
    assert chosen is loud

    chosen = select_preferred_source([loud, quiet], sr, preference="quietest")
    assert chosen is quiet

    # make high-pitch vs low-pitch signals
    high = np.sin(2 * np.pi * 1000 * np.linspace(0, 1, sr))
    low = np.sin(2 * np.pi * 100 * np.linspace(0, 1, sr))
    chosen = select_preferred_source([high, low], sr, preference="highest_pitch")
    assert np.allclose(chosen, high, atol=1e-2)
    chosen = select_preferred_source([high, low], sr, preference="lowest_pitch")
    assert np.allclose(chosen, low, atol=1e-2)


def test_separate_with_preference_returns_chosen():
    sr = 8000
    t = np.linspace(0, 1, sr, endpoint=False)
    mix = np.sin(2 * np.pi * 300 * t) + 0.5 * np.sin(2 * np.pi * 700 * t)

    chosen, sources = separate_with_preference(mix, sr, preference="loudest", n_sources=2)
    assert chosen in sources
    assert len(sources) == 2

    # the chosen audio should have higher RMS than at least one other
    rms_vals = [np.sqrt(np.mean(s ** 2)) for s in sources]
    assert np.sqrt(np.mean(chosen ** 2)) == max(rms_vals)
