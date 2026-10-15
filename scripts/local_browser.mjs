#!/usr/bin/env node
// Use local full Chrome; on Apple Silicon force native Node and Chrome.
import {existsSync} from "node:fs";
import {execFileSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import path from "node:path";

const LOCAL_BROWSER_CANDIDATES = [ // macOS / Linux / Windows
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
];

export const resolveBrowserExecutable = (value) => {
  if (value === "managed") throw new Error("DraftCut requires local full Chrome; managed is not supported.");
  const found = value ? path.resolve(value) : LOCAL_BROWSER_CANDIDATES.find((candidate) => existsSync(candidate));
  if (!found)
    throw new Error(
      "未找到本机完整 Chrome。请安装 Chrome 或用 --browser-executable 指定 Chrome 路径。"
    );
  if (!existsSync(found)) throw new Error(`Chrome executable does not exist: ${found}`);
  const version = execFileSync(found, ["--version"], {encoding: "utf8", timeout: 15000}).trim();
  if (!/^Google Chrome\b/.test(version)) throw new Error(`Expected full Google Chrome, got: ${version}`);
  let appleSilicon = process.platform === "darwin" && process.arch === "arm64";
  if (process.platform === "darwin" && !appleSilicon) {
    appleSilicon = execFileSync("/usr/sbin/sysctl", ["-n", "hw.optional.arm64"], {encoding: "utf8"}).trim() === "1";
  }
  if (appleSilicon && process.arch !== "arm64") {
    throw new Error("Apple Silicon requires native ARM64 Node. Restart this command with an ARM64 Node executable; do not use Rosetta.");
  }
  if (appleSilicon) {
    process.env.MOTIONTALK_CHROME = found;
    return fileURLToPath(new URL("./chrome-native.sh", import.meta.url));
  }
  return found;
};
