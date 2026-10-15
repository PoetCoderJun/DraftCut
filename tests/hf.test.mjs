import test from 'node:test';
import assert from 'node:assert/strict';
import {diagnosticEnvironment} from '../scripts/hf.mjs';

test('browser diagnostics select the native wrapper and avoid the cold-start 10s timeout', () => {
  assert.deepEqual(diagnosticEnvironment('/native/chrome-wrapper', {}), {
    HYPERFRAMES_BROWSER_PATH: '/native/chrome-wrapper',
    PRODUCER_HEADLESS_SHELL_PATH: '/native/chrome-wrapper',
    PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS: '45000',
  });
});
test('browser diagnostics preserve an explicit navigation budget and reject invalid values', () => {
  assert.equal(diagnosticEnvironment('/chrome', {PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS: '90000'}).PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS, '90000');
  for (const value of ['0', '-1', 'garbage', 'Infinity'])
    assert.equal(diagnosticEnvironment('/chrome', {PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS: value}).PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS, '45000');
});
