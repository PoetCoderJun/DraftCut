"""First-run config checks use synthetic keys and never contact a provider."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from asr_config import asr_capability, load_asr_environment
from vendor.clean_talking_video.transcribe import dashscope_settings
import transcribe_audio


class FirstRunConfig(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        config = patch('asr_config.user_config_path', return_value=Path(self.home.name) / 'asr.env')
        config.start(); self.addCleanup(config.stop)

    def test_missing_configuration_is_actionable_without_output_or_network(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True), patch.object(subprocess, 'run') as run:
            output = Path(folder) / 'new-asr'
            source = Path(folder) / 'source.wav'; source.write_bytes(b'fixture')
            args = ['asr', '--audio', str(source), '--output-dir', str(output), '--allow-cloud-asr']
            with patch.object(sys, 'argv', args), contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit): transcribe_audio.main()
            self.assertIn('DASHSCOPE_API_KEY', err.getvalue())
            self.assertIn('--env-file', err.getvalue())
            self.assertFalse(output.exists()); run.assert_not_called()

    def test_check_config_needs_no_media_or_consent_and_never_calls_a_subprocess(self):
        with patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'synthetic-secret'}, clear=True), patch.object(sys, 'argv', ['asr', '--check-config']), patch.object(subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(transcribe_audio.main(), 0)
            report = json.loads(out.getvalue())
            self.assertEqual(report['status'], 'configured_not_verified')
            self.assertFalse(report['network_tested']); run.assert_not_called()
            self.assertNotIn('synthetic-secret', out.getvalue())

    def test_explicit_file_with_unicode_spaces_and_process_precedence(self):
        with tempfile.TemporaryDirectory(prefix='配置 空格 ') as folder:
            file = Path(folder) / 'private.env'
            file.write_text("export DASHSCOPE_API_KEY='file-primary'\nDASHSCOPE_ASR_API_KEY=legacy-file\nDASHSCOPE_ASR_MODEL=custom # comment\nUNRELATED_SECRET=not-forwarded\n")
            file.chmod(0o600)
            result = load_asr_environment(file, {'DASHSCOPE_API_KEY': 'process-primary'})
            self.assertEqual(dashscope_settings(result, language=None).api_key, 'process-primary')
            self.assertEqual(result['DASHSCOPE_ASR_MODEL'], 'custom')
            self.assertNotIn('UNRELATED_SECRET', result)

    def test_no_implicit_discovery_in_cwd_or_home(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / '.env'; file.write_text('DASHSCOPE_API_KEY=must-not-load')
            before = Path.cwd()
            try:
                os.chdir(folder)
                self.assertEqual(asr_capability(load_asr_environment(environ={'HOME': folder}))['status'], 'needs_configuration')
            finally: os.chdir(before)

    def test_shell_syntax_never_executes_or_leaks(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'executed'
            for value in [f'$(touch {marker})', f'`touch {marker}`', '${PRIVATE_KEY}']:
                file = Path(folder) / 'private.env'; file.write_text('DASHSCOPE_API_KEY=' + value)
                file.chmod(0o600)
                with self.assertRaises(ValueError) as error: load_asr_environment(file, {})
                self.assertNotIn(value, str(error.exception)); self.assertFalse(marker.exists())

    def test_configuration_errors_redact_values(self):
        for key, value in [('DASHSCOPE_ASR_POLL_SECONDS', 'synthetic-secret'), ('DASHSCOPE_ASR_TIMEOUT_SECONDS', 'NaN'), ('DASHSCOPE_ASR_POLL_SECONDS', '0'), ('DASHSCOPE_ASR_TIMEOUT_SECONDS', 'inf'), ('DASHSCOPE_ASR_BASE_URL', 'https://user:synthetic-secret@example.invalid')]:
            report = asr_capability({'DASHSCOPE_API_KEY': 'synthetic-key', key: value})
            self.assertEqual(report['status'], 'invalid_configuration')
            self.assertNotIn('synthetic-secret', json.dumps(report)); self.assertNotIn('synthetic-key', json.dumps(report))

    def test_whitespace_legacy_key_falls_back_to_primary(self):
        self.assertEqual(dashscope_settings({'DASHSCOPE_ASR_API_KEY': ' ', 'DASHSCOPE_API_KEY': 'primary'}, language=None).api_key, 'primary')

    def test_valid_explicit_config_reaches_adapter_with_same_interpreter(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / '输入 文件.wav'; source.write_bytes(b'fixture')
            config = Path(folder) / 'settings.env'; config.write_text('DASHSCOPE_API_KEY=synthetic-file\n')
            config.chmod(0o600)
            output = Path(folder) / 'new-asr'
            args = ['asr', '--audio', str(source), '--output-dir', str(output), '--env-file', str(config), '--allow-cloud-asr']
            with patch.dict(os.environ, {}, clear=True), patch.object(sys, 'argv', args), patch.object(subprocess, 'run') as run:
                run.return_value.returncode = 0
                self.assertEqual(transcribe_audio.main(), 0)
                self.assertEqual(run.call_args.args[0][0], sys.executable)
                self.assertEqual(run.call_args.kwargs['env']['DASHSCOPE_API_KEY'], 'synthetic-file')
                self.assertFalse(output.exists())  # mocked adapter; not a live ASR success


if __name__ == '__main__': unittest.main()
