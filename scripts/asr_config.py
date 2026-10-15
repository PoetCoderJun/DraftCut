"""Reusable user-level ASR configuration; never scan projects or execute .env files."""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import sys

from vendor.clean_talking_video.transcribe import dashscope_api_key, dashscope_settings

ASR_KEYS = {
    'DASHSCOPE_API_KEY', 'DASHSCOPE_ASR_API_KEY', 'DASHSCOPE_BASE_URL',
    'DASHSCOPE_ASR_BASE_URL', 'DASHSCOPE_ASR_MODEL', 'DASHSCOPE_ASR_POLL_SECONDS',
    'DASHSCOPE_ASR_TIMEOUT_SECONDS',
}


def user_config_path(environ=None, platform=None):
    env = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    home = Path(env.get('HOME') or Path.home())
    if not home.is_absolute():
        raise ValueError('HOME must be an absolute user-directory path')
    if platform == 'darwin':
        return home / 'Library/Application Support/DraftCut/asr.env'
    if platform == 'win32':
        base = Path(env.get('APPDATA') or home / 'AppData/Roaming')
        if not base.is_absolute():
            raise ValueError('APPDATA must be an absolute user-config path')
        return base / 'DraftCut/asr.env'
    base = Path(env.get('XDG_CONFIG_HOME') or home / '.config')
    if not base.is_absolute():
        raise ValueError('XDG_CONFIG_HOME must be an absolute path')
    return base / 'draftcut/asr.env'


def config_selection(env_file=None, environ=None):
    env = os.environ if environ is None else environ
    selected = env_file if env_file is not None else (env.get('DRAFTCUT_ASR_CONFIG') or None)
    if selected is None:
        return user_config_path(env), 'user'
    raw = str(selected)
    if raw == '~' or raw.startswith('~/'):
        raw = str(Path(env.get('HOME') or Path.home()) / raw[2:])
    file = Path(raw)
    if env_file is None and not file.is_absolute():
        raise ValueError('DRAFTCUT_ASR_CONFIG must select an absolute file path')
    return file.absolute(), 'explicit' if env_file is not None else 'override'


def read_config_file(file):
    """Check access before reading; callers never receive raw errors containing values."""
    if file.is_symlink() or not file.is_file():
        raise ValueError('ASR config must be a regular file, not a symlink')
    info = file.stat()
    if os.name == 'posix' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise ValueError('ASR config must be owned by this user and private (chmod 600 on the selected config file)')
    if info.st_size > 65536:
        raise ValueError('ASR config exceeds 64 KiB')
    try:
        return file.read_text(encoding='utf-8-sig').splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError('Cannot read ASR config as UTF-8') from exc


def load_asr_environment(env_file=None, environ=None):
    """Process variables > selected override OR fixed user file. No checkout discovery."""
    process = dict(os.environ if environ is None else environ)
    values = {}
    file, source = config_selection(env_file, process)
    if file.exists() or file.is_symlink():
        for number, line in enumerate(read_config_file(file), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.fullmatch(r'(?:export\s+)?([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(.*)', line)
            if not match:
                raise ValueError(f'Invalid ASR env assignment at line {number}; use KEY=VALUE')
            key, value = match.groups()
            if key not in ASR_KEYS:
                continue
            if value.startswith(('"', "'")):
                quoted = re.fullmatch(r"(['\"])(.*?)\1\s*(?:#.*)?", value)
                if not quoted:
                    raise ValueError(f'Invalid quoted {key} at line {number}')
                value = quoted.group(2)
            else:
                value = re.split(r'\s+#', value, maxsplit=1)[0].strip()
            # Shell expansion is intentionally unsupported, including inside quotes.
            if '$' in value or '`' in value or '\x00' in value:
                raise ValueError(f'{key} must be a literal value; shell expansion is unsupported')
            values[key] = value
        # A file's legacy alias must not override an injected primary credential (or vice versa).
        if dashscope_api_key(process):
            values.pop('DASHSCOPE_API_KEY', None)
            values.pop('DASHSCOPE_ASR_API_KEY', None)
        if process.get('DASHSCOPE_ASR_BASE_URL') or process.get('DASHSCOPE_BASE_URL'):
            values.pop('DASHSCOPE_ASR_BASE_URL', None)
            values.pop('DASHSCOPE_BASE_URL', None)
    elif source != 'user':
        raise ValueError('Selected ASR config file does not exist; fix the override or use the reusable user config')
    return {**values, **process}


def asr_capability(environ):
    """Report configuration presence only; no key, endpoint, HTTP request or auth claim."""
    report = {'provider': 'dashscope', 'network_tested': False,
              'local_transcript_import': 'available_without_credentials',
              'cloud_consent': 'explicit_consent_required; reuse an existing authorization when its scope covers this source'}
    if not dashscope_api_key(environ):
        return {**report, 'status': 'needs_configuration',
                'action': 'Configure once with configure_asr.py setup in your own terminal, or inject DASHSCOPE_API_KEY securely. Future projects reuse it automatically; --env-file is an optional override. A trusted word-timestamp transcript needs no ASR key'}
    try:
        dashscope_settings(environ, language=None)
    except (ValueError, RuntimeError) as exc:
        return {**report, 'status': 'invalid_configuration', 'action': str(exc)}
    return {**report, 'status': 'configured_not_verified',
            'action': 'Configuration is present; account, region, model access and live transcription remain untested'}


def config_status(env_file=None, environ=None):
    """Agent-facing status. No key, config contents, URL or network/authentication."""
    process = dict(os.environ if environ is None else environ)
    selection = {}
    try:
        file, source = config_selection(env_file, process)
        selection = {'config_file': str(file), 'file_selection': source}
        result = asr_capability(load_asr_environment(env_file, process))
        if result['status'] == 'needs_configuration' and file.is_file():
            result['action'] = 'Selected config has no API key. Use configure_asr.py setup --replace in your own terminal to fill it once, or inject a key securely; existing contents are preserved until explicit replacement.'
        return {**result, **selection,
                'process_credentials_present': bool(dashscope_api_key(process))}
    except ValueError as exc:
        return {**selection, 'provider': 'dashscope', 'status': 'invalid_configuration', 'network_tested': False,
                'action': str(exc)}
    except OSError:
        return {**selection, 'provider': 'dashscope', 'status': 'invalid_configuration', 'network_tested': False,
                'action': 'Cannot access selected ASR config; check the file path and owner permissions'}
