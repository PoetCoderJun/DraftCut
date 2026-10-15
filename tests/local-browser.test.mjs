import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {findBrowserExecutable, resolveBrowserExecutable} from '../scripts/local_browser.mjs';
import {browserHealth} from '../scripts/browser_health.mjs';

test('a custom browser from bootstrap is used by later entrypoints', () => {
  const folder = mkdtempSync(path.join(tmpdir(), 'draftcut chrome '));
  const binary = path.join(folder, 'Google Chrome');
  const before = process.env.DRAFTCUT_CHROME;
  const oldWrapper = process.env.MOTIONTALK_CHROME;
  try {
    writeFileSync(binary, '#!/bin/sh\nprintf "Google Chrome 123.0.0.0\\n"\n', {mode: 0o755});
    process.env.DRAFTCUT_CHROME = binary;
    assert.equal(findBrowserExecutable(undefined), binary);
    const launcher = resolveBrowserExecutable();
    assert.ok(launcher === binary || launcher.endsWith('/chrome-native.sh'));
    if (launcher !== binary) assert.equal(process.env.MOTIONTALK_CHROME, binary);
    assert.equal(findBrowserExecutable('/explicit/chrome'), '/explicit/chrome');
  } finally {
    if (before === undefined) delete process.env.DRAFTCUT_CHROME; else process.env.DRAFTCUT_CHROME = before;
    if (oldWrapper === undefined) delete process.env.MOTIONTALK_CHROME; else process.env.MOTIONTALK_CHROME = oldWrapper;
    rmSync(folder, {recursive: true});
  }
});

test('managed browser selection fails explicitly', () => {
  assert.throws(() => findBrowserExecutable(undefined, {DRAFTCUT_CHROME: 'managed'}), /local full Chrome/);
});

test('browser health cannot navigate to a remote page', async () => {
  await assert.rejects(browserHealth('/unused/chrome', 'https://example.invalid'), /local file/);
});
