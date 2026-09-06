#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from dna_midi_studio.suno_like_brain import build_suno_like_plan

def main():
    ap=argparse.ArgumentParser(description='DNA MIDI Studio Suno-like symbolic brain planner')
    ap.add_argument('midi'); ap.add_argument('-o','--output',default=None); ap.add_argument('--data-dir',default='data')
    a=ap.parse_args(); src=Path(a.midi); plan=build_suno_like_plan(src.read_bytes(),src.name,a.data_dir)
    text=json.dumps(plan,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(text,encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
