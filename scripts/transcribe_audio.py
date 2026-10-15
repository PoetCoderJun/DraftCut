#!/usr/bin/env python3
"""Word-timestamp ASR with explicit configuration and cloud consent."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from asr_config import asr_capability, config_status, load_asr_environment

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--env-file', type=Path, help='Optional override; by default reuse the fixed user ASR config, never scan project .env files')
    parser.add_argument('--check-config', action='store_true', help='Check configuration locally without uploading, authenticating or creating output')
    parser.add_argument('--trim-breaths', choices=['yes', 'no'], default='no',
                        help='Legacy option; ASR never edits audio and does not approve the manuscript')
    parser.add_argument('--allow-cloud-asr', action='store_true', help='Only after explicit upload/paid-service authorization')
    parser.add_argument('--language', default='zh')
    parser.add_argument('--prompt', default='')
    args = parser.parse_args()
    if args.check_config:
        try:
            report = config_status(args.env_file)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['status'] == 'configured_not_verified' else 1
    if not args.allow_cloud_asr:
        parser.error('Cloud ASR uploads audio and may incur charges. Obtain authorization before --allow-cloud-asr.')
    if not args.audio or not args.output_dir:
        parser.error('--audio and --output-dir are required for transcription')
    if not args.audio.is_file():
        parser.error('Audio source does not exist')
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        parser.error('Use a new empty ASR directory; prior artifacts are preserved')
    try:
        env = load_asr_environment(args.env_file)
        config = asr_capability(env)
        if config['status'] != 'configured_not_verified':
            parser.error(config['action'])
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    source = Path(__file__).parent / 'vendor/clean_talking_video/transcribe.py'
    return subprocess.run([sys.executable, str(source), '--input', str(args.audio), '--output-dir', str(args.output_dir),
                           '--language', args.language, '--prompt', args.prompt], env=env, check=False).returncode

if __name__ == '__main__':
    raise SystemExit(main())
