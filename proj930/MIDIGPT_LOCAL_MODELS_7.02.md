# DNA MIDI Studio 7.02 - Local MIDI-GPT Models

- Vendored MIDI-GPT 0.3.4 source retained.
- Added local checkpoints:
  - yellow_small-final.safetensors
  - yellow_medium-final.safetensors
- Worker now prefers InferenceEngine.from_checkpoint(local_path).
- Hugging Face is only a fallback when a requested local model is missing.
- Fixed undefined n_candidates/candidate_files report bug.
- Fixed MIDI-GPT 0.3.4 run_variations integration: candidate count comes from InferenceConfig.num_candidates and returned score records are unpacked correctly.
- velocity=False and microtiming=False remain defaults so Factory performance authority is preserved.

Validated SHA-256:
acd856168e87c640868ac20cf7523e5912e5171506101fbaebd8eea49a7c4f7c  yellow_medium-final.safetensors
4bd7c021bf1bcc14eb8eb94a242f0d6aaa700950e3888c1bac8140275d63e6ee  yellow_small-final.safetensors

Bridge tests: 4/4 PASS (PYTHONPATH=src pytest tests/test_external_midigpt_bridge.py)
