# GitHub AI backends

Primary generative backend: **Metacreation-Lab/MIDI-GPT v0.3.3**.
It is kept in an isolated Python 3.10/3.11 virtual environment so the existing DNA MIDI Studio runtime does not have to change Python versions.

Why this backend: multitrack generation, missing-bar infill, whole-track generation, pretrained checkpoints, controllable sampling, and replay scoring already exist upstream.

Install on Windows: `scripts\install_midigpt_windows.bat`.
The worker is `scripts\midigpt_worker.py`; the project bridge is `dna_midi_studio.external_midigpt.MidiGPTBackend`.

Factory velocity remains authoritative in DNA MIDI Studio. Generated MIDI must still pass the existing role, harmony, Pa800 and independent verification stages before replacing an authorized region.

Other upstream projects retained as research/reference backends: MidiTok, FIGARO and SkyTNT midi-model. Do not duplicate their functionality locally unless the primary backend cannot provide it.
