# Neural training and calibration 9.02

Run `TRAIN_NEURAL_NETWORK.bat`.

Training changes model weights. Calibration does not retrain weights: it validates untouched holdout metrics, authority invariants and promotion gates, then musical thresholds are tuned on VALJA blind A/B and finally on the physical Pa800.

Safety rules:
- GOLD/relationship datasets contain no velocity feature or velocity target.
- Factory remains the only velocity authority.
- New checkpoints train under `models_staging/`.
- Production checkpoints are replaced only with option 6 after PASS.
- Existing production models are copied to `model_backups/` before promotion.
- A model with a lower loss is not automatically musically better; listening and device gates remain required.
