import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { buildBridgeSummary } from '../scripts/bridge-summary.mjs';

const sourcePath = '/artifacts/output/review/seto_ohashi_manifest.json';
const summaryPath = '/artifacts/output/review/seto_ohashi_summary.json';
const catalogPath = '/artifacts/manifest.json';
const sha = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('text-cad.locale', 'en'); localStorage.setItem('text-cad.theme', 'light'); });
});

test('bridge starts with compact metadata while the full manifest is unavailable and all drawings preload', async ({ page }) => {
  const requested: string[] = [];
  page.on('request', request => requested.push(new URL(request.url()).pathname));
  // The complete JSON remains downloadable, but never belongs on the startup
  // path or on an error-recovery fallback for this compact display contract.
  await page.route(url => url.pathname.endsWith(sourcePath), route => route.abort());
  await page.goto('?model=seto-ohashi&view=3d&environment=day');
  await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
  await expect(page.locator('.bridge-canvas canvas')).toHaveAttribute('data-model-ready', 'true');
  await expect.poll(() => requested.some(path => path.endsWith(summaryPath))).toBe(true);
  const drawings = page.locator('.bridge-drawing img');
  await expect(drawings).toHaveCount(3);
  for (const drawing of await drawings.all()) {
    await expect.poll(() => drawing.evaluate(element => (element as HTMLImageElement).complete
      && (element as HTMLImageElement).naturalWidth > 0)).toBe(true);
  }
  expect(requested.filter(path => path.endsWith(sourcePath))).toEqual([]);
  await expect(page.locator('vite-error-overlay')).toHaveCount(0);
  await expect(page.locator('[role="alert"]')).toHaveCount(0);
});

test('compact startup retains the complete source manifest as an exact named download', async ({ page }) => {
  await page.goto('?model=seto-ohashi&view=3d');
  await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
  await page.getByRole('button', { name: 'Downloads', exact: true }).first().click();
  const pending = page.waitForEvent('download');
  await page.locator('[data-file="output/review/seto_ohashi_manifest.json"] .download-row').click();
  const downloaded = await pending;
  expect(downloaded.suggestedFilename()).toBe('seto_ohashi_manifest.json');
  const path = await downloaded.path();
  expect(path).not.toBeNull();
  const [actual, source] = await Promise.all([readFile(path!), readFile('../output/review/seto_ohashi_manifest.json')]);
  expect(actual.length).toBe(source.length);
  expect(sha(actual)).toBe(sha(source));
});

test('a compact metadata request failure retries locally without fetching the full manifest or reloading 3D', async ({ page }) => {
  let rejectSummary = true, fullRequests = 0;
  page.on('request', request => { if (new URL(request.url()).pathname.endsWith(sourcePath)) fullRequests++; });
  await page.route(url => url.pathname.endsWith(summaryPath), route => rejectSummary
    ? route.fulfill({ status: 503, body: 'Temporarily unavailable' }) : route.continue());
  await page.goto('?model=seto-ohashi&view=3d');
  const status = page.getByRole('status').filter({ hasText: 'The dimension and source record could not be loaded.' });
  await expect(status).toBeAttached();
  const canvas = page.locator('.bridge-canvas canvas');
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  rejectSummary = false;
  await status.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
  await expect(status).toHaveCount(0);
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  expect(fullRequests).toBe(0);
});

test('a well-formed summary from a different source is rejected against the existing artifact catalog and can retry', async ({ page }) => {
  const source = await readFile('../output/review/seto_ohashi_manifest.json');
  const wrongSource = { ...buildBridgeSummary(source).summary, source_manifest_sha256: '0'.repeat(64) };
  let wrong = true, fullRequests = 0;
  page.on('request', request => { if (new URL(request.url()).pathname.endsWith(sourcePath)) fullRequests++; });
  await page.route(url => url.pathname.endsWith(summaryPath), route => wrong
    ? route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(wrongSource) })
    : route.continue());
  await page.goto('?model=seto-ohashi&view=3d');
  const status = page.getByRole('status').filter({ hasText: 'The dimension and source record could not be loaded.' });
  await expect(status).toBeAttached();
  await expect(page.locator('.bridge-parameters dd')).toHaveText(['—', '—', '—', '—']);
  const canvas = page.locator('.bridge-canvas canvas');
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  wrong = false;
  await status.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
  await expect(status).toHaveCount(0);
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  expect(fullRequests).toBe(0);
});

for (const failure of ['stale source binding', 'unavailable catalog'] as const) {
  test(`a correct summary waits for its catalog, rejects ${failure}, and retries without a full-manifest fallback`, async ({ page }) => {
    const correctCatalog = JSON.parse(await readFile('public/artifacts/manifest.json', 'utf8'));
    const fullKey = sourcePath.slice('/artifacts/'.length);
    const staleCatalog = { ...correctCatalog,
      [fullKey]: { ...correctCatalog[fullKey], sha256: '0'.repeat(64) } };
    let broken = true, catalogRequests = 0, fullRequests = 0;
    let releaseCatalog!: () => void;
    const catalogHeld = new Promise<void>(resolve => { releaseCatalog = resolve; });
    page.on('request', request => { if (new URL(request.url()).pathname.endsWith(sourcePath)) fullRequests++; });
    await page.route(url => url.pathname.endsWith(catalogPath), async route => {
      catalogRequests++;
      if (!broken) { await route.continue(); return; }
      // A fast, correct summary alone must not briefly expose unverified
      // dimensions while the independent source catalog is still pending.
      await catalogHeld;
      if (failure === 'stale source binding') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(staleCatalog) });
      } else await route.fulfill({ status: 503, body: 'Artifact catalog temporarily unavailable' });
    });
    const compactReceived = page.waitForResponse(response => new URL(response.url()).pathname.endsWith(summaryPath));
    await page.goto('?model=seto-ohashi&view=3d');
    await (await compactReceived).finished();
    const canvas = page.locator('.bridge-canvas canvas');
    const dimensions = page.locator('.bridge-parameters dd');
    try {
      if (failure === 'stale source binding') await expect(canvas).toHaveAttribute('data-model-ready', 'true');
      else await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
      await expect(dimensions).toHaveText(['—', '—', '—', '—']);
    } finally { releaseCatalog(); }
    const originalCanvas = failure === 'stale source binding' ? await canvas.elementHandle() : null;
    if (failure === 'stale source binding') expect(originalCanvas).not.toBeNull();
    const status = page.getByRole('status').filter({ hasText: 'The dimension and source record could not be loaded.' });
    await expect(status).toBeAttached();
    await expect(dimensions).toHaveText(['—', '—', '—', '—']);
    expect(fullRequests).toBe(0);
    broken = false;
    await status.getByRole('button', { name: 'Retry', exact: true }).click();
    await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
    await expect(status).toHaveCount(0);
    if (failure === 'stale source binding') {
      await expect(canvas).toHaveAttribute('data-model-ready', 'true');
      expect(await originalCanvas!.evaluate(element => element.isConnected)).toBe(true);
    }
    expect(catalogRequests).toBeGreaterThanOrEqual(2);
    expect(fullRequests).toBe(0);
  });
}
