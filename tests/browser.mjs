import { chromium } from "playwright";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fixDemoClock, startServer } from "../scripts/browser_helpers.mjs";

const server = await startServer();
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
    locale: "en-US",
    timezoneId: "UTC",
    acceptDownloads: true,
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("Failed to load resource"))
      errors.push(message.text());
  });
  await fixDemoClock(page);
  await page.goto(server.url);
  await page.locator("#commit-chart svg").waitFor();
  assert.equal(await page.locator(".heat-cell").count(), 168);
  assert.ok(await page.locator("#demo-notice").isVisible());
  assert.ok(
    await page
      .locator(".author-bar span")
      .first()
      .evaluate((bar) => bar.getBoundingClientRect().width > 0),
  );

  await page.locator("#bar-button").click();
  assert.ok((await page.locator(".chart-bar").count()) > 0);
  await page.locator('[data-period="3"]').click();
  await page.locator("#granularity").selectOption("week");
  await page.locator('[data-view="contributors"]').click();
  assert.equal(await page.locator(".commits-panel").isVisible(), false);
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#export-button").click();
  const download = await downloadPromise;
  assert.ok(download.suggestedFilename().startsWith("DEMO-"));
  assert.ok(
    (await readFile(await download.path(), "utf8")).includes(
      '"contributor","commits","share_percent"',
    ),
  );
  await page.locator('[data-view="files"]').click();
  assert.ok(await page.locator(".details-panel").isVisible());
  await page.locator('[data-view="activity"]').click();
  assert.ok(await page.locator(".weekdays-panel").isVisible());
  await page.locator('[data-view="overview"]').click();
  await page.locator("#start-date").fill("2030-01-01");
  await page.locator("#end-date").fill("2030-01-31");
  await page.locator("#apply-dates").click();
  assert.equal(await page.locator("#stat-commits").textContent(), "0");
  assert.ok((await page.locator("#commit-chart").textContent()).includes("No commits"));
  await page.locator("#start-date").fill("2030-02-01");
  await page.locator("#end-date").fill("2030-01-01");
  await page.locator("#apply-dates").click();
  assert.ok((await page.locator("#error-notice").textContent()).includes("start date"));
  await page.locator('[data-period="all"]').click();

  // Mock remote reports: default browser checks never clone or contact a provider.
  const demoReport = await page.evaluate(() => JSON.parse(JSON.stringify(state.report)));
  const realReport = {
    ...demoReport,
    repository: {
      ...demoReport.repository,
      provider: "github",
      host: "github.com",
      name: "example",
      namespace: "example-org",
      url: "https://github.com/example-org/example",
    },
  };
  await page.route("**/api/analyze", (route) =>
    route.fulfill({ status: 202, json: { job_id: "synthetic-test-job" } }),
  );
  await page.route("**/api/jobs/synthetic-test-job", (route) =>
    route.fulfill({ json: { status: "complete", report: realReport } }),
  );
  await page.route("**/api/filter", (route) => {
    const filter = route.request().postDataJSON();
    return route.fulfill({ json: { ...realReport, range: { ...realReport.range, ...filter } } });
  });
  await page.locator("#repo-url").fill("https://github.com/example-org/example");
  await page.locator("#analyze-button").click();
  await page.waitForFunction(
    () => document.querySelector("#provider-badge").textContent === "GITHUB",
  );
  assert.equal(await page.locator("#demo-notice").isVisible(), false);
  await page.locator("#granularity").selectOption("day");
  await page.waitForFunction(() => document.querySelector("#granularity").disabled === false);
  await page.locator("#advanced-toggle").click();
  assert.ok(await page.locator("#advanced-options").isVisible());
  await page.locator("#advanced-toggle").click();
  await page.locator("#methodology-toggle").click();
  assert.ok(await page.locator("#methodology").isVisible());
  await page.locator("#methodology-toggle").click();

  await page.setViewportSize({ width: 390, height: 844 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.locator('[data-view="contributors"]').click();
  assert.ok(await page.locator(".contributors-panel").isVisible());
  assert.deepEqual(errors, []);
  console.log(
    "Offline browser checks passed: charts, filters, navigation, CSV, job states, and mobile layout.",
  );
} finally {
  await browser?.close();
  await server.stop();
}
