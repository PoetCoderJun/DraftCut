#!/usr/bin/env python3
"""Internal word-timestamp ASR; requires an explicit breath choice and cloud consent."""
import argparse
from pathlib import Path
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--trim-breaths', choices=['yes', 'no'], default='no',
                        help='Legacy option; ASR never edits audio and does not approve the manuscript')
    parser.add_argument('--allow-cloud-asr', action='store_true', help='Only after explicit upload/paid-service authorization')
    parser.add_argument('--language', default='zh')
    parser.add_argument('--prompt', default='')
    args = parser.parse_args()
    if not args.allow_cloud_asr:
        parser.error('Cloud ASR uploads audio and may incur charges. Obtain authorization before --allow-cloud-asr.')
    if not args.audio.is_file():
        parser.error('Audio source does not exist')
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        parser.error('Use a new empty ASR directory; prior artifacts are preserved')
    source = Path(__file__).parent / 'vendor/clean_talking_video/transcribe.py'
    return subprocess.run([sys.executable, str(source), '--input', str(args.audio), '--output-dir', str(args.output_dir),
                           '--language', args.language, '--prompt', args.prompt], check=False).returncode

if __name__ == '__main__':
    raise SystemExit(main())
