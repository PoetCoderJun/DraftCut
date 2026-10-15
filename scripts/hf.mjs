#!/usr/bin/env node
import {runCli, isMainModule} from './hyperframes_runtime.mjs';
import {resolveBrowserExecutable} from './local_browser.mjs';

export function diagnosticEnvironment(browser, env = process.env) {
  const configured = Number(env.PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS);
  return {
    HYPERFRAMES_BROWSER_PATH: browser,
    PRODUCER_HEADLESS_SHELL_PATH: browser,
    // The pinned CLI's 10s default can expire on a cold native Chrome launch.
    PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS: String(Number.isFinite(configured) && configured > 0 ? configured : 45000),
  };
}

async function main() {
  const [command, ...args] = process.argv.slice(2);
  const allowed = ['catalog', 'add', 'lint', 'check', 'snapshot', 'preview', 'doctor'];
  if (!command || command === '--help') {
    console.log('Usage: node scripts/hf.mjs catalog|add|lint|check|snapshot|preview|doctor [Hyperframes CLI options]\nBrowser diagnostics use local full Chrome and a 45s navigation budget. Render with render_master.mjs. Use --help after a command for its options.');
  } else if (!allowed.includes(command)) {
    throw new Error(`Unsupported command ${command}. Use render_master.mjs for exports.`);
  } else {
    const needsBrowser = ['snapshot', 'check'].includes(command) && !args.includes('--help');
    const env = needsBrowser ? diagnosticEnvironment(resolveBrowserExecutable()) : {};
    await runCli([command, ...args], {env});
  }
}
if (isMainModule(import.meta.url))
  main().catch(error => {console.error(error.message); process.exitCode = 1;});
