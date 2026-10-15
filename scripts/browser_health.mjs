// Exercise the pinned renderer's CDP path; --dump-dom has separate macOS teardown failures.
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {require, isMainModule} from './hyperframes_runtime.mjs';
import {resolveBrowserExecutable} from './local_browser.mjs';

export async function browserHealth(chrome, localPage) {
  const pageUrl = new URL(localPage);
  if (pageUrl.protocol !== 'file:') throw new Error('Browser health only accepts a local file page');
  const launcher = resolveBrowserExecutable(chrome);
  const profile = mkdtempSync(path.join(tmpdir(), 'draftcut-health-chrome-'));
  let browser;
  try {
    const puppeteer = require('puppeteer-core');
    browser = await puppeteer.launch({executablePath: launcher, headless: true,
      userDataDir: profile, timeout: 45000,
      args: ['--disable-gpu', '--disable-background-networking', '--disable-component-update',
        '--disable-default-apps', '--disable-extensions', '--disable-sync', '--no-first-run',
        '--no-default-browser-check', '--metrics-recording-only', '--mute-audio']});
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', request => {
      ['file:', 'data:', 'about:'].includes(new URL(request.url()).protocol) ? request.continue() : request.abort();
    });
    await page.goto(pageUrl.href, {waitUntil: 'load', timeout: 45000});
    const passed = await page.evaluate(() => {
      const probe = document.querySelector('#probe');
      return probe?.dataset.draftcutHealth === 'passed' && probe.style.transform === 'translate(42px, 0px)';
    });
    if (!passed) throw new Error('Local Chrome did not execute the bundled GSAP check');
    const child = browser.process();
    await browser.close(); browser = undefined;
    if (child.exitCode !== 0 || child.signalCode) throw new Error('Local Chrome did not close cleanly');
    return {chrome: 'local CDP full-Chrome + GSAP + clean close passed', render_launcher: launcher};
  } finally {
    try { if (browser) await browser.close(); }
    finally { rmSync(profile, {recursive: true, force: true}); }
  }
}

if (isMainModule(import.meta.url)) {
  const [chrome, page] = process.argv.slice(2);
  browserHealth(chrome, pathToFileURL(path.resolve(page)).href)
    .then(result => console.log(JSON.stringify(result)))
    .catch(() => {console.error('Local Chrome/GSAP automation failed; inspect browser/session permissions. No sandbox protections were disabled.'); process.exitCode = 1;});
}
