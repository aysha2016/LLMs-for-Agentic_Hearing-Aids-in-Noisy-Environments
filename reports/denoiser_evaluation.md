# Neural Denoiser Evaluation

Date: 2026-02-07
Checkpoint: models/neural_denoiser.pt
Device: cpu

## SNR Results

| Scenario | Input SNR (dB) | Output SNR (dB) | Improvement (dB) |
| --- | --- | --- | --- |
| Quiet Office | 11.55 | 12.59 | 1.04 |
| Noisy Restaurant | 2.55 | 9.56 | 7.01 |
| Street Traffic | -0.33 | 7.26 | 7.59 |
| Music | -0.75 | 1.59 | 2.34 |
| High Frequency Noise | 4.04 | 8.64 | 4.60 |
| Sudden Loud Noise | 0.01 | 5.16 | 5.15 |

## Notes

- Improvements are computed as Output SNR minus Input SNR.
- Evaluation uses the synthetic dataset from examples.synthetic_dataset_demo.
