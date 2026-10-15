"""Explicit, data-only ASR configuration. Never search for or execute .env files."""
from __future__ import annotations

import os
from pathlib import Path
import re

from vendor.clean_talking_video.transcribe import dashscope_api_key, dashscope_settings

ASR_KEYS = {
    'DASHSCOPE_API_KEY', 'DASHSCOPE_ASR_API_KEY', 'DASHSCOPE_BASE_URL',
    'DASHSCOPE_ASR_BASE_URL', 'DASHSCOPE_ASR_MODEL', 'DASHSCOPE_ASR_POLL_SECONDS',
    'DASHSCOPE_ASR_TIMEOUT_SECONDS',
}


def load_asr_environment(env_file=None, environ=None):
    """Load only the selected file; process variables take precedence over file values."""
    process = dict(os.environ if environ is None else environ)
    values = {}
    if env_file is not None:
        file = Path(env_file).expanduser()
        if not file.is_file():
            raise ValueError('ASR --env-file does not exist or is not a regular file')
        if file.stat().st_size > 65536:
            raise ValueError('ASR --env-file exceeds 64 KiB')
        try:
            lines = file.read_text(encoding='utf-8-sig').splitlines()
        except (OSError, UnicodeError) as exc:
            raise ValueError('Cannot read ASR --env-file as UTF-8') from exc
        for number, line in enumerate(lines, 1):
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
    return {**values, **process}


def asr_capability(environ):
    """Report configuration presence only; no key, endpoint, HTTP request or auth claim."""
    report = {'provider': 'dashscope', 'network_tested': False,
              'local_transcript_import': 'available_without_credentials',
              'cloud_consent': 'required_per_source_before_upload'}
    if not dashscope_api_key(environ):
        return {**report, 'status': 'needs_configuration',
                'action': 'Inject DASHSCOPE_API_KEY securely or select --env-file; a trusted word-timestamp transcript needs no ASR key'}
    try:
        dashscope_settings(environ, language=None)
    except (ValueError, RuntimeError) as exc:
        return {**report, 'status': 'invalid_configuration', 'action': str(exc)}
    return {**report, 'status': 'configured_not_verified',
            'action': 'Configuration is present; account, region, model access and live transcription remain untested'}
