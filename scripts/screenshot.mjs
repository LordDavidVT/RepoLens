import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fixDemoClock, root, startServer } from "./browser_helpers.mjs";

const server = await startServer();
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1,
    locale: "en-US",
    timezoneId: "UTC",
    reducedMotion: "reduce",
  });
  await fixDemoClock(page);
  await page.goto(server.url);
  await page.locator("#commit-chart svg").waitFor();
  await page.evaluate(() => document.fonts.ready);
  await mkdir(path.join(root, "docs", "images"), { recursive: true });
  await page.screenshot({
    path: path.join(root, "docs", "images", "demo-dashboard.png"),
    fullPage: true,
    animations: "disabled",
  });
  console.log("Saved docs/images/demo-dashboard.png using synthetic demo data.");
} finally {
  await browser?.close();
  await server.stop();
}
