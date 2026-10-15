import {createRequire} from 'node:module';
import {execFileSync, spawn} from 'node:child_process';
import {readFileSync, realpathSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const skillRoot = fileURLToPath(new URL('../', import.meta.url));
export const require = createRequire(new URL('../package.json', import.meta.url));
export function isMainModule(moduleUrl, scriptPath = process.argv[1]) {
  if (!scriptPath) return false;
  try { return realpathSync(scriptPath) === realpathSync(fileURLToPath(moduleUrl)); }
  catch { return false; }
}
export function cliPath() {
  const pkg = path.join(skillRoot, 'node_modules/hyperframes/package.json');
  let installed;
  try { installed = JSON.parse(readFileSync(pkg, 'utf8')); }
  catch { throw new Error(`Install the pinned runtime first: npm ci --prefix ${skillRoot}`); }
  const expected = JSON.parse(readFileSync(path.join(skillRoot, 'package.json'), 'utf8')).dependencies.hyperframes;
  if (installed.version !== expected) throw new Error(`Hyperframes ${installed.version} differs from pinned ${expected}; run npm ci --prefix ${skillRoot}`);
  return path.resolve(path.dirname(pkg), installed.bin.hyperframes);
}
export function parseArgs(argv, allowed) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') {args.help = true; continue;}
    const key = argv[i].replace(/^--/, '').replaceAll('-', '_');
    if (!argv[i].startsWith('--') || !allowed.includes(key)) throw new Error(`Unknown option: ${argv[i]}`);
    const value = argv[++i];
    if (value === undefined || value.startsWith('--')) throw new Error(`Missing value for ${key}`);
    args[key] = value;
  }
  return args;
}
export function runCli(args, {cwd, env = {}, capture = false, log} = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cliPath(), ...args], {
      cwd, env: {...process.env, HYPERFRAMES_NO_TELEMETRY: '1', ...env},
      stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    });
    let out = '', err = '';
    child.stdout?.on('data', b => {out += b; log?.write(b);});
    child.stderr?.on('data', b => {err += b; log?.write(b);});
    const stop = signal => child.kill(signal);
    const onInt = () => stop('SIGINT'), onTerm = () => stop('SIGTERM');
    process.once('SIGINT', onInt); process.once('SIGTERM', onTerm);
    child.on('error', reject);
    child.on('close', code => {
      process.removeListener('SIGINT', onInt); process.removeListener('SIGTERM', onTerm);
      code === 0 ? resolve(out) : reject(new Error(`Hyperframes exited ${code}: ${err.slice(-3000)}`));
    });
  });
}
export function mediaMetadata(file) {
  const binary = process.env.HYPERFRAMES_FFPROBE_PATH || 'ffprobe';
  return JSON.parse(execFileSync(binary, ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', file], {encoding: 'utf8'}));
}
