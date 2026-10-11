import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export async function startServer() {
  const executable = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const processHandle = spawn(executable, ["-B", "app.py", "--port", "0"], {
    cwd: root,
    stdio: ["ignore", "pipe", "ignore"],
  });
  const url = await new Promise((resolve, reject) => {
    let output = "";
    const timeout = setTimeout(() => {
      processHandle.kill();
      reject(new Error("The local server did not start within 10 seconds."));
    }, 10000);
    processHandle.once("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    processHandle.once("exit", (code) => {
      clearTimeout(timeout);
      reject(new Error(`The local server exited before startup (${code}).`));
    });
    processHandle.stdout.on("data", (chunk) => {
      output += chunk.toString();
      const match = output.match(/http:\/\/localhost:\d+/);
      if (match) {
        clearTimeout(timeout);
        resolve(match[0]);
      }
    });
  });
  return {
    url,
    async stop() {
      if (processHandle.exitCode !== null) return;
      await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          processHandle.kill("SIGKILL");
        }, 5000);
        processHandle.once("exit", () => {
          clearTimeout(timeout);
          resolve();
        });
        processHandle.kill(process.platform === "win32" ? "SIGTERM" : "SIGINT");
      });
    },
  };
}

export async function fixDemoClock(page) {
  await page.addInitScript(() => {
    const OriginalDate = Date;
    const fixedTime = OriginalDate.parse("2026-09-30T12:00:00Z");
    class DemoDate extends OriginalDate {
      constructor(...args) {
        super(...(args.length ? args : [fixedTime]));
      }
      static now() {
        return fixedTime;
      }
    }
    globalThis.Date = DemoDate;
  });
}
