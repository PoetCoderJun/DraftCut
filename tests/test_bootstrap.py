import contextlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bootstrap


class BootstrapSafety(unittest.TestCase):
    def environment(self):
        stack = contextlib.ExitStack()
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        for name in ['node', 'npm', 'ffmpeg', 'ffprobe', 'chrome', '.venv/bin/python']:
            p = root / name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text('preserve')
        stack.enter_context(patch.object(bootstrap, 'ROOT', root))
        stack.enter_context(patch.object(bootstrap.sys, 'platform', 'darwin'))
        stack.enter_context(patch.object(bootstrap.shutil, 'which', side_effect=lambda n: str(root / n)))
        stack.enter_context(patch.object(bootstrap, 'python_health', return_value={'version': '3.12.0'}))
        stack.enter_context(patch.object(bootstrap, 'node_health', return_value={'hyperframes': '0.8.30', 'gsap': '3.14.2'}))
        stack.enter_context(patch.object(bootstrap, 'media_health', return_value={'chrome': 'passed'}))
        return stack, root

    def test_missing_system_tool_never_triggers_project_install(self):
        stack, root = self.environment()
        with stack, patch.object(bootstrap.shutil, 'which', return_value=None), patch.object(bootstrap, 'run') as run:
            result = bootstrap.bootstrap(True, str(root / 'chrome'))
            self.assertEqual(result['status'], 'blocked');self.assertFalse(result['actions']);run.assert_not_called()

    def test_healthy_dependencies_are_reused_even_with_install(self):
        stack, root = self.environment()
        with stack, patch.object(bootstrap, 'run', side_effect=['v24.0.0', '11.0.0']) as run:
            result = bootstrap.bootstrap(True, str(root / 'chrome'))
            self.assertEqual(result['status'], 'ready');self.assertEqual(run.call_count, 2)
            self.assertTrue(all('reused healthy' in a for a in result['actions']))
            self.assertEqual((root / '.venv/bin/python').read_text(), 'preserve')

    def test_incompatible_existing_environment_is_preserved(self):
        stack, root = self.environment()
        with stack, patch.object(bootstrap, 'python_health', side_effect=RuntimeError('bad venv')), patch.object(bootstrap, 'run', side_effect=['v24.0.0', '11.0.0', json.dumps({'venv': False, 'version': '3.12.0'})]) as run:
            result = bootstrap.bootstrap(True, str(root / 'chrome'))
            self.assertEqual(result['status'], 'blocked')
            self.assertIn('preserve', result['blockers'][0]);self.assertEqual(run.call_count, 3)
            self.assertEqual((root / '.venv/bin/python').read_text(), 'preserve')

    def test_failed_actual_media_check_cannot_be_ready(self):
        stack, root = self.environment()
        with stack, patch.object(bootstrap, 'run', side_effect=['v24.0.0', '11.0.0']), patch.object(bootstrap, 'media_health', side_effect=RuntimeError('Chrome failed')):
            result = bootstrap.bootstrap(True, str(root / 'chrome'))
            self.assertEqual(result['status'], 'blocked');self.assertEqual(result['blockers'], ['Chrome failed'])


if __name__ == '__main__':
    unittest.main()
