import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, symlinkSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

test('installed symlink CLI paths execute rather than silently returning success', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'draftcut-cli-symlink-'));
  try {
    for (const name of ['hf.mjs', 'render_master.mjs', 'validate_master.mjs']) {
      const installed = path.join(dir, name);
      symlinkSync(fileURLToPath(new URL('../scripts/' + name, import.meta.url)), installed);
      const output = execFileSync(process.execPath, [installed, '--help'], {encoding: 'utf8'});
      assert.match(output, /Usage:/, name + ' must actually execute from an installed symlink');
    }
  } finally { rmSync(dir, {recursive: true, force: true}); }
});
