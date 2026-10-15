#!/usr/bin/env python3
"""One-time, local, hidden API-key input. Never supply a key in CLI arguments or chat."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import tempfile

from asr_config import config_selection, config_status
from vendor.clean_talking_video.transcribe import DEFAULT_DASHSCOPE_BASE_URL, DEFAULT_DASHSCOPE_MODEL, dashscope_settings


def save_config(file, api_key, *, model=DEFAULT_DASHSCOPE_MODEL, base_url=DEFAULT_DASHSCOPE_BASE_URL, replace=False):
    """Only called after explicit local setup; tests use dummy keys under temporary HOME."""
    file = Path(file)
    if file.is_symlink() or (file.exists() and not file.is_file()):
        raise ValueError('Preserve the existing config path; setup requires a regular non-symlink file')
    if file.exists() and not replace:
        return False
    values = {'DASHSCOPE_API_KEY': api_key.strip(), 'DASHSCOPE_ASR_MODEL': model.strip(),
              'DASHSCOPE_ASR_BASE_URL': base_url.strip()}
    for key, value in values.items():
        if any(c in value for c in "\n\r\x00$`'"):
            raise ValueError(f'{key} must be a literal single-line value; no shell expansion')
    if not values['DASHSCOPE_API_KEY'] or any(c.isspace() for c in values['DASHSCOPE_API_KEY']):
        raise ValueError('API key must be nonempty and contain no whitespace; no file was saved')
    if not values['DASHSCOPE_ASR_MODEL']:
        raise ValueError('ASR model must be nonempty; no file was saved')
    dashscope_settings(values, language=None)  # Local validation only, no account/auth/network.
    new_dir = not file.parent.exists()
    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if new_dir:
        file.parent.chmod(0o700)
    content = '# DraftCut user ASR config. Reused automatically; contains private credentials.\n'
    content += ''.join(f"{key}='{value}'\n" for key, value in values.items())
    # Installation/bootstrap never calls this writer. An explicit replacement is atomic.
    if replace:
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=file.parent, delete=False) as stream:
                temp = Path(stream.name); stream.write(content); stream.flush(); os.fsync(stream.fileno())
            temp.chmod(0o600); os.replace(temp, file)
        finally:
            if temp is not None and temp.exists(): temp.unlink()
    else:
        fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        if os.name == 'posix': os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    setup = sub.add_parser('setup', help='Enter a key once in your own terminal; future projects reuse the private user config')
    setup.add_argument('--config', type=Path, help='Optional explicit config destination; otherwise use the fixed user config')
    setup.add_argument('--replace', action='store_true', help='Only when the user explicitly asks to rotate/change saved configuration')
    setup.add_argument('--model', default=DEFAULT_DASHSCOPE_MODEL)
    setup.add_argument('--base-url', default=DEFAULT_DASHSCOPE_BASE_URL)
    status = sub.add_parser('status', help='Sanitized, local status only; never prints credentials or authenticates')
    status.add_argument('--config', type=Path)
    args = parser.parse_args()
    if args.command == 'status':
        report = config_status(args.config)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['status'] == 'configured_not_verified' else 1
    try:
        file, _ = config_selection(args.config)
    except ValueError as exc:
        parser.error(str(exc))
    if file.exists() and not args.replace:
        print('Existing user ASR configuration preserved; no key was requested. Use status to check it.'); return 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error('Initial credential setup needs the user\'s own interactive terminal or a platform secure-secret input; never pass a key through Agent stdin, arguments or chat')
    api_key = getpass.getpass('DashScope API key (hidden; never send it in chat): ')
    try:
        saved = save_config(file, api_key, model=args.model, base_url=args.base_url, replace=args.replace)
    except (ValueError, OSError) as exc:
        parser.error(str(exc) if isinstance(exc, ValueError) else 'Cannot save user config; check owner permissions')
    print('User ASR configuration saved privately and will be reused across projects. No network/authentication performed.' if saved else 'Existing configuration preserved.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
