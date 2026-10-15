#!/usr/bin/env python3
"""Agent-owned local dependency setup and honest, offline media health checks."""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(args, *, cwd=ROOT, timeout=120):
    env = {**os.environ, 'HYPERFRAMES_NO_TELEMETRY': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'}
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env, text=True,
                       capture_output=True, timeout=timeout)
    if p.returncode:
        # Do not copy registry configuration, credentials, or complete installer logs into reports.
        raise RuntimeError(f'{Path(str(args[0])).name} {args[1] if len(args)>1 else ""} exited {p.returncode}')
    return p.stdout.strip()


def version_tuple(value):
    match = re.match(r'^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?', value)
    if not match:
        raise ValueError('Unrecognized version')
    return tuple(int(x or 0) for x in match.groups())


def satisfies(version, clauses):
    actual = version_tuple(version)
    for operator, target in re.findall(r'(>=|<=|==|>|<)\s*([\d.]+)', clauses):
        expected = version_tuple(target)
        if not {'>=': actual >= expected, '<=': actual <= expected,
                '==': actual == expected, '>': actual > expected, '<': actual < expected}[operator]:
            return False
    return True


def python_health(executable):
    script = ('import sys,json,importlib.metadata as m; '
              'print(json.dumps({"version":sys.version.split()[0],"venv":sys.prefix!=sys.base_prefix,'
              '"packages":{n:m.version(n) for n in ["requests","requests-toolbelt","urllib3"]}}))')
    info = json.loads(run([executable, '-c', script]))
    if version_tuple(info['version']) < (3, 10, 0) or not info['venv']:
        raise RuntimeError('Use a project virtual environment with Python 3.10+')
    for line in (ROOT / 'requirements.txt').read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_-]+)([<>=\d., ]+)', line)
        if not match or not satisfies(info['packages'].get(match[1], ''), match[2]):
            raise RuntimeError('Python packages do not satisfy requirements.txt')
    run([executable, '-m', 'pip', 'check'])
    # Import the adapters locally; no source recording, credentials, or network request is used.
    run([executable, '-c', 'import requests, requests_toolbelt, urllib3'])
    return info


def node_health(node, npm):
    package = json.loads((ROOT / 'package.json').read_text())
    expected = package['dependencies']
    for name, required in expected.items():
        actual = json.loads((ROOT / 'node_modules' / name / 'package.json').read_text())['version']
        if actual != required:
            raise RuntimeError(f'{name} differs from the pinned version')
    run([npm, 'ls', '--all', '--omit=dev', '--json'])
    script = ("import {cliPath,require} from './scripts/hyperframes_runtime.mjs';"
              "require('gsap'); console.log(cliPath());")
    cli = run([node, '--input-type=module', '-e', script])
    run([node, cli, '--version'])
    return expected


def media_health(ffmpeg, ffprobe, chrome, node):
    script = ("import {resolveBrowserExecutable} from './scripts/local_browser.mjs';"
              "console.log(resolveBrowserExecutable(process.argv[1]));")
    # This also checks native ARM64 Node on Apple Silicon and verifies full Chrome.
    launcher = run([node, '--input-type=module', '-e', script, chrome])
    with tempfile.TemporaryDirectory(prefix='draftcut-health-') as temp:
        folder = Path(temp)
        sample = folder / 'check.mp4'
        run([ffmpeg, '-v', 'error', '-xerror', '-f', 'lavfi', '-i', 'color=s=64x64:r=30:d=0.2',
             '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '0.2', '-c:v', 'libx264',
             '-c:a', 'aac', '-y', sample])
        run([ffmpeg, '-v', 'error', '-xerror', '-i', sample, '-f', 'null', '-'])
        streams = json.loads(run([ffprobe, '-v', 'error', '-show_streams', '-of', 'json', sample]))['streams']
        if {s.get('codec_name') for s in streams} != {'h264', 'aac'}:
            raise RuntimeError('Local H.264/AAC encode/decode check failed')
        page = folder / 'check.html'
        gsap = html.escape((ROOT / 'node_modules/gsap/dist/gsap.min.js').as_uri(), quote=True)
        page.write_text(f'<!doctype html><meta charset="utf-8"><div id="probe">DraftCut</div>'
                        f'<script src="{gsap}"></script><script>'
                        'gsap.set("#probe",{x:42});document.querySelector("#probe").dataset.draftcutHealth="passed";'
                        '</script>')
        dom = run([chrome, '--headless=new', '--disable-gpu', '--no-first-run',
                   '--no-default-browser-check', '--disable-background-networking', '--disable-component-update',
                   '--disable-default-apps', '--disable-extensions', '--disable-sync', '--metrics-recording-only',
                   '--mute-audio', f'--user-data-dir={folder / "chrome-profile"}', '--dump-dom', page.as_uri()], timeout=45)
        if 'data-draftcut-health="passed"' not in dom:
            raise RuntimeError('Full Chrome did not execute local GSAP')
    return {'ffmpeg': 'local H.264/AAC encode and full decode passed',
            'chrome': 'local headless full-Chrome + GSAP passed', 'render_launcher': launcher}


def bootstrap(install=False, chrome_override=None):
    report = {'schema': 'draftcut.bootstrap.v1', 'status': 'blocked', 'repository': str(ROOT),
              'actions': [], 'checks': {}, 'blockers': [],
              'scope': 'local dependency and media checks; no cloud ASR, approvals, real-media or creative certification'}
    checks = report['checks']
    if sys.platform not in ('darwin', 'linux'):
        report['blockers'].append('Current workflow needs macOS/Linux POSIX support; no new platform installation attempted')
        return report
    if sys.version_info < (3, 10):
        report['blockers'].append('Agent must select/install Python 3.10+ and rerun this script')
        return report
    checks['python_host'] = {'status': 'passed', 'version': sys.version.split()[0], 'path': sys.executable}
    node, npm, ffmpeg, ffprobe = (shutil.which(n) for n in ('node', 'npm', 'ffmpeg', 'ffprobe'))
    chrome = chrome_override or next((str(p) for p in (
        Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        Path('/usr/bin/google-chrome'), Path('/usr/bin/google-chrome-stable')) if p.is_file()), None)
    if not chrome:
        chrome = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    for name, executable in [('node', node), ('npm', npm), ('ffmpeg', ffmpeg), ('ffprobe', ffprobe), ('chrome', chrome)]:
        if not executable or not Path(executable).is_file():
            report['blockers'].append(f'Agent must select/install {name} using the existing trusted system package manager')
    if report['blockers']:
        return report
    try:
        node_version = run([node, '--version'])
        if version_tuple(node_version) < (22, 0, 0):
            raise RuntimeError('Agent must select/install Node.js 22+; existing runtime was preserved')
        checks['node'] = {'status': 'passed', 'version': node_version, 'path': node}
        checks['npm'] = {'status': 'passed', 'version': run([npm, '--version']), 'path': npm}
        venv = ROOT / '.venv'
        python = venv / 'bin/python'
        if not venv.exists() and install:
            run([sys.executable, '-m', 'venv', venv]);report['actions'].append('created project .venv')
        if not python.is_file():
            raise RuntimeError('Project .venv is missing/incomplete; use --install (do not overwrite an existing incomplete environment)')
        try:
            packages = python_health(python)
            report['actions'].append('reused healthy project Python dependencies')
        except (RuntimeError, ValueError, KeyError, OSError):
            if not install:
                raise RuntimeError('Python dependency check failed; Agent should rerun with --install')
            # Never replace a directory or global interpreter presented as the project virtualenv.
            identity = json.loads(run([python, '-c', 'import sys,json;print(json.dumps({"venv":sys.prefix!=sys.base_prefix,"version":sys.version.split()[0]}))']))
            if not identity['venv'] or version_tuple(identity['version']) < (3, 10, 0):
                raise RuntimeError('Existing .venv is incompatible; preserve it and use a clean checkout with Python 3.10+')
            run([python, '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt'], timeout=600)
            report['actions'].append('installed Python requirements in project .venv')
            packages = python_health(python)
        checks['python_environment'] = {'status': 'passed', 'path': str(python), **packages}
        try:
            packages = node_health(node, npm)
            report['actions'].append('reused healthy pinned Node dependencies')
        except (RuntimeError, ValueError, KeyError, OSError):
            if not install:
                raise RuntimeError('Pinned Node dependency check failed; Agent should rerun with --install')
            run([npm, 'ci', '--no-audit', '--no-fund'], timeout=600)
            report['actions'].append('installed locked Node dependencies with npm ci')
            packages = node_health(node, npm)
        checks['node_dependencies'] = {'status': 'passed', 'versions': packages}
        checks['media'] = {'status': 'passed', **media_health(ffmpeg, ffprobe, chrome, node)}
        report['runtime'] = {'python': str(python), 'node': node, 'chrome': chrome,
                             'path_prefix': [str(venv / 'bin'), str(Path(node).parent)]}
        report['status'] = 'ready'
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        report['blockers'].append(str(error) if not isinstance(error, subprocess.TimeoutExpired) else 'Local install/health command timed out; inspect the environment before retrying')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Install missing project dependencies; reuse already healthy ones')
    parser.add_argument('--browser-executable', help='Existing full Google Chrome path; never downloads a browser')
    args = parser.parse_args()
    report = bootstrap(args.install, args.browser_executable)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'ready' else 1


if __name__ == '__main__':
    raise SystemExit(main())
