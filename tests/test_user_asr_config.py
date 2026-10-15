"""One-time config fixtures only. Never inspect or persist real user credentials."""
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import asr_config as config
import configure_asr as setup
import transcribe_audio
from vendor.clean_talking_video.transcribe import dashscope_settings


class UserAsrConfiguration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='draftcut user 配置 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {'HOME': str(self.root / 'home'), 'PATH': os.environ.get('PATH', '')}
        self.file = config.user_config_path(self.env)

    def saved(self, value='fixture-user-key', path=None):
        file = path or self.file
        setup.save_config(file, value)
        return file

    def key(self, file=None, env=None):
        return dashscope_settings(config.load_asr_environment(file, self.env if env is None else env), language=None).api_key

    def test_platform_paths_follow_only_user_configuration(self):
        self.assertEqual(config.user_config_path(self.env, 'darwin'), Path(self.env['HOME']) / 'Library/Application Support/DraftCut/asr.env')
        self.assertEqual(config.user_config_path(self.env, 'linux'), Path(self.env['HOME']) / '.config/draftcut/asr.env')
        self.assertEqual(config.user_config_path({**self.env, 'XDG_CONFIG_HOME': str(self.root / 'xdg')}, 'linux'), self.root / 'xdg/draftcut/asr.env')
        self.assertEqual(config.user_config_path({**self.env, 'APPDATA': str(self.root / 'appdata')}, 'win32'), self.root / 'appdata/DraftCut/asr.env')

    def test_deterministic_selection_and_process_precedence_across_aliases(self):
        self.saved('fixture-user')
        explicit = self.saved('fixture-explicit', self.root / 'explicit.env')
        override = self.saved('fixture-override', self.root / 'override.env')
        self.assertEqual(self.key(), 'fixture-user')
        override_env = {**self.env, 'DRAFTCUT_ASR_CONFIG': str(override)}
        self.assertEqual(self.key(env=override_env), 'fixture-override')
        self.assertEqual(self.key(explicit, override_env), 'fixture-explicit')
        self.assertEqual(self.key(explicit, {**override_env, 'DASHSCOPE_API_KEY': 'fixture-process'}), 'fixture-process')
        with explicit.open('a') as f: f.write('DASHSCOPE_ASR_API_KEY=fixture-file-legacy\nDASHSCOPE_ASR_BASE_URL=https://file.invalid\n')
        env = {**self.env, 'DASHSCOPE_API_KEY': 'fixture-process', 'DASHSCOPE_BASE_URL': 'https://process.invalid'}
        settings = dashscope_settings(config.load_asr_environment(explicit, env), language=None)
        self.assertEqual(settings.api_key, 'fixture-process'); self.assertEqual(settings.base_url, 'https://process.invalid')

    def test_two_projects_automatically_reuse_one_key_without_prompt_or_cloud_call(self):
        self.saved()
        original = Path.cwd()
        try:
            for name in ('project one', '另一个项目'):
                project = self.root / name; project.mkdir()
                (project / '.env').write_text('DASHSCOPE_API_KEY=fixture-must-not-scan')
                source = project / 'source.wav'; source.write_bytes(b'fixture')
                os.chdir(project)
                args = ['asr', '--audio', str(source), '--output-dir', str(project / 'asr'), '--allow-cloud-asr']
                with patch.dict(os.environ, self.env, clear=True), patch.object(sys, 'argv', args), patch.object(subprocess, 'run') as adapter, patch.object(setup.getpass, 'getpass', side_effect=AssertionError('must not prompt')):
                    adapter.return_value.returncode = 0
                    self.assertEqual(transcribe_audio.main(), 0)
                    self.assertEqual(adapter.call_args.kwargs['env']['DASHSCOPE_API_KEY'], 'fixture-user-key')
        finally: os.chdir(original)

    def test_missing_and_invalid_config_status_is_actionable_and_redacted(self):
        missing = config.config_status(environ=self.env)
        self.assertEqual(missing['status'], 'needs_configuration')
        self.assertIn('Configure once', missing['action'])
        self.assertEqual(missing['config_file'], str(self.file))
        self.saved()
        with self.file.open('a') as f: f.write('DASHSCOPE_ASR_POLL_SECONDS=fixture-private-value\n')
        report = config.config_status(environ=self.env)
        self.assertEqual(report['status'], 'invalid_configuration')
        self.assertNotIn('fixture-private-value', json.dumps(report)); self.assertNotIn('fixture-user-key', json.dumps(report))

    def test_private_modes_and_unsafe_permissions_rejected_before_read(self):
        self.saved()
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.file.parent.stat().st_mode), 0o700)
        if os.name != 'posix': return
        self.file.chmod(0o644)
        with patch.object(Path, 'read_text', side_effect=AssertionError('must check permissions before reading')):
            report = config.config_status(environ=self.env)
        self.assertEqual(report['status'], 'invalid_configuration'); self.assertIn('chmod 600', report['action'])

    def test_wrong_owner_and_symlinks_do_not_read_credentials(self):
        self.saved()
        if os.name == 'posix':
            with patch.object(config.os, 'getuid', return_value=os.getuid() + 1), patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
                self.assertEqual(config.config_status(environ=self.env)['status'], 'invalid_configuration')
        link = self.root / 'linked.env'; link.symlink_to(self.file)
        self.assertEqual(config.config_status(link, self.env)['status'], 'invalid_configuration')

    def test_setup_and_install_rechecks_preserve_existing_config(self):
        self.saved(); before = self.file.read_bytes(); modified = self.file.stat().st_mtime_ns
        self.assertFalse(setup.save_config(self.file, 'fixture-unrequested-replacement'))
        import test_bootstrap
        import bootstrap
        stack, repo = test_bootstrap.BootstrapSafety().environment()
        with stack, patch.dict(os.environ, self.env, clear=True), patch.object(bootstrap, 'run', side_effect=['v24.0.0', '11.0.0']):
            report = bootstrap.bootstrap(True, str(repo / 'chrome'))
            self.assertEqual(report['capabilities']['asr']['status'], 'configured_not_verified')
        with patch.dict(os.environ, self.env, clear=True), patch.object(sys, 'argv', ['setup', 'setup']), patch.object(setup.getpass, 'getpass') as ask, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(setup.main(), 0); ask.assert_not_called()
        self.assertEqual(self.file.read_bytes(), before); self.assertEqual(self.file.stat().st_mtime_ns, modified)

    def test_only_explicit_replace_rotates_saved_fixture(self):
        self.saved('fixture-old')
        self.assertTrue(setup.save_config(self.file, 'fixture-new', replace=True))
        self.assertEqual(self.key(), 'fixture-new')
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode), 0o600)

    def test_initial_setup_uses_hidden_input_and_prints_no_key(self):
        out = io.StringIO(); out.isatty = lambda: True
        with patch.dict(os.environ, self.env, clear=True), patch.object(sys, 'argv', ['setup', 'setup']), patch.object(sys.stdin, 'isatty', return_value=True), contextlib.redirect_stdout(out), patch.object(setup.getpass, 'getpass', return_value='fixture-hidden-input') as ask:
            self.assertEqual(setup.main(), 0); ask.assert_called_once()
        self.assertNotIn('fixture-hidden-input', out.getvalue())
        self.assertEqual(self.key(), 'fixture-hidden-input')

    def test_initial_setup_rejects_automation_without_persisting_access(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(sys, 'argv', ['setup', 'setup']), patch.object(sys.stdin, 'isatty', return_value=False), patch.object(setup.getpass, 'getpass') as ask, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit): setup.main()
            ask.assert_not_called(); self.assertFalse(self.file.exists())

    def test_process_key_does_not_create_any_persistent_config_or_consent(self):
        report = config.config_status(environ={**self.env, 'DASHSCOPE_API_KEY': 'fixture-injected'})
        self.assertEqual(report['status'], 'configured_not_verified'); self.assertFalse(report['network_tested'])
        self.assertIn('explicit_consent_required', report['cloud_consent'])
        self.assertFalse(self.file.exists())

    def test_missing_explicit_override_is_not_silently_replaced_with_user_key(self):
        self.saved()
        report = config.config_status(environ={**self.env, 'DRAFTCUT_ASR_CONFIG': str(self.root / 'missing.env')})
        self.assertEqual(report['status'], 'invalid_configuration'); self.assertIn('override', report['action'])

    def test_cli_status_automatically_finds_user_file_from_another_project(self):
        self.saved('fixture-cli-private')
        project = self.root / 'different-project'; project.mkdir()
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/configure_asr.py'), 'status'],
                                cwd=project, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'configured_not_verified')
        self.assertEqual(report['config_file'], str(self.file))
        self.assertNotIn('fixture-cli-private', result.stdout + result.stderr)

    def test_invalid_local_input_is_not_saved(self):
        for value in ('', 'two words', '$(command)', 'line\nvalue'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                setup.save_config(self.file, value)
            self.assertFalse(self.file.exists())

    def test_relative_environment_config_paths_are_rejected(self):
        for key, value in [('HOME', 'relative'), ('DRAFTCUT_ASR_CONFIG', 'relative.env')]:
            report = config.config_status(environ={**self.env, key: value})
            self.assertEqual(report['status'], 'invalid_configuration')

    def test_existing_empty_template_has_an_explicit_repair_action(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text('DASHSCOPE_API_KEY=\n'); self.file.chmod(0o600)
        report = config.config_status(environ=self.env)
        self.assertEqual(report['status'], 'needs_configuration')
        self.assertIn('setup --replace', report['action'])


if __name__ == '__main__': unittest.main()
