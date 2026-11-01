import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('text-cad.locale', 'en'); localStorage.setItem('text-cad.theme', 'light');
  });
});
async function landmark(page: Page, model = 'tokyo-tower', query = '') {
  await page.goto(`?model=${model}&view=3d&environment=day${query}`);
  const canvas = page.locator('.landmark-canvas canvas');
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  await expect.poll(async () => Number(await canvas.getAttribute('data-render-triangles'))).toBeGreaterThan(0);
  await expect(page.locator('vite-error-overlay')).toHaveCount(0);
  await expect(page.locator('[role="alert"]')).toHaveCount(0);
  return canvas;
}
test('Tokyo Tower cameras, visibility, trilingual copy and night lighting', async ({ page }, info) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  const canvas = await landmark(page);
  await expect(canvas).toHaveAttribute('data-model-revision', 'LANDMARK-R07');
  await page.getByRole('button', { name: 'Front', exact: true }).click();
  await expect(canvas).toHaveAttribute('data-camera-view', 'front');
  await expect(canvas).toHaveScreenshot('tokyo-front.png');
  await page.getByRole('button', { name: 'Top deck', exact: true }).click();
  await expect(canvas).toHaveAttribute('data-camera-view', 'top-deck');
  await expect(canvas).toHaveScreenshot('tokyo-top-deck.png');
  const structure = page.getByRole('checkbox', { name: 'Tower lattice', exact: true });
  await structure.uncheck(); await expect(canvas).toHaveAttribute('data-visible-groups', /^((?!structure).)*$/);
  await structure.check(); await expect(canvas).toHaveAttribute('data-visible-groups', /structure/);
  for (const [locale, name] of [['ja', 'トップデッキ'], ['zh', '特别展望台'], ['en', 'Top deck']]) {
    await page.locator('.language-control select').selectOption(locale);
    await expect(page.getByRole('button', { name, exact: true })).toBeVisible();
    await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  }
  await page.getByRole('button', { name: 'Night', exact: true }).click();
  await expect(canvas).toHaveAttribute('data-environment', 'night');
  await expect.poll(async () => Number(await canvas.getAttribute('data-active-local-lights'))).toBeGreaterThan(0);
  await expect(canvas).toHaveScreenshot('tokyo-night.png');
  await info.attach('renderer-diagnostics', { body: JSON.stringify(await canvas.evaluate(c => ({ ...(c as HTMLCanvasElement).dataset })), null, 2), contentType: 'application/json' });
  expect(errors).toEqual([]);
});

test('Skytree starts on the same revision and keeps drawings preloaded', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  const canvas = await landmark(page, 'tokyo-skytree');
  await expect(canvas).toHaveAttribute('data-model-revision', 'LANDMARK-R05');
  await page.getByRole('button', { name: 'Elevation', exact: true }).click();
  await expect(page.locator('.landmark-drawing:not([hidden]) img')).toBeVisible();
  await expect.poll(() => page.locator('.landmark-drawing:not([hidden]) img').evaluate(i => (i as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
  await page.getByRole('button', { name: '3D model', exact: true }).click();
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  expect(errors).toEqual([]);
});

for (const model of ['house', 'apartment', 'river']) test(`${model} opens its real 3D model and drawing`, async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto(`?model=${model}&view=3d&environment=day`);
  const canvas = page.locator('main canvas').first(); await expect(canvas).toBeVisible();
  await expect(page.locator('.scene-host .canvas-message, .river-canvas .canvas-message')).toHaveCount(0);
  await expect.poll(async () => Number(await canvas.getAttribute('data-rendered-frames'))).toBeGreaterThan(1);
  await expect(page.locator('[role="alert"]')).toHaveCount(0);
  const tab = page.locator('.app-header nav button').nth(1); await tab.click();
  if (model === 'river') {
    const drawing = page.locator('.river-drawing:not([hidden]) img');
    await expect(drawing).toBeVisible();
    await expect.poll(() => drawing.evaluate(i => (i as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
  } else {
    const drawing = page.locator('.plan-sheet.plan-vector:visible'); await expect(drawing).toBeVisible();
    await expect.poll(() => drawing.locator('path').count()).toBeGreaterThan(0);
  }
  await expect(page.locator('vite-error-overlay')).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('local photo overlay aligns and exports pinned comparison conditions', async ({ page }, info) => {
  const canvas = await landmark(page);
  await page.getByText('Compare a photo', { exact: true }).click();
  // Our own model screenshot is a functional fixture, not evidence of real-world accuracy.
  const screenshot = await canvas.screenshot();
  await page.getByLabel('Choose reference image', { exact: true }).setInputFiles({ name: 'local-reference.png', mimeType: 'image/png', buffer: screenshot });
  const overlay = page.locator('.reference-image-overlay'); await expect(overlay).toBeVisible();
  await expect(page.getByText('local-reference.png', { exact: true })).toBeVisible();
  await page.getByLabel('Horizontal position', { exact: false }).press('ArrowRight');
  await expect(overlay.locator('img')).toHaveAttribute('style', /translate\(1%, 0%\)/);
  await page.getByLabel('Overlay reference image', { exact: true }).uncheck(); await expect(overlay).toBeHidden();
  await page.getByLabel('Overlay reference image', { exact: true }).check();
  const pending = page.waitForEvent('download'); await page.getByRole('button', { name: 'Save comparison settings', exact: true }).click();
  const download = await pending, path = await download.path(); expect(path).not.toBeNull();
  const record = JSON.parse(await readFile(path!, 'utf8'));
  expect(record.model).toBe('tokyo-tower'); expect(record.revision).toBe('LANDMARK-R07');
  expect(record.reference.sha256).toBe(createHash('sha256').update(screenshot).digest('hex'));
  expect(record.alignment.x).toBe(1); expect(record.camera.pose).toBeTruthy();
  expect(record.controls.model_gl_levels_mm).toEqual([125000, 223550]);
  expect(record.controls.published_guidance_levels_mm).toEqual([150000, 250000]);
  expect(record.perspective_calibrated).toBe(false);
  const pngPending = page.waitForEvent('download'); await page.getByRole('button', { name: 'Save comparison image', exact: true }).click();
  const png = await pngPending; expect(png.suggestedFilename()).toBe('tokyo_tower_comparison.png');
  const bytes = await readFile((await png.path())!);
  expect(bytes.subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  expect(bytes.readUInt32BE(16)).toBe(record.viewport.backing_width);
  expect(bytes.readUInt32BE(20)).toBe(record.viewport.backing_height);
  await info.attach('comparison-export', { body: bytes, contentType: 'image/png' });
  await info.attach('comparison-settings', { body: JSON.stringify(record, null, 2), contentType: 'application/json' });
  await page.getByRole('button', { name: 'Remove image', exact: true }).click(); await expect(overlay).toHaveCount(0);
});

test('Tokyo batching reduces actual renderer calls without changing pixels', async ({ page }, info) => {
  test.skip(info.project.name === 'mobile', 'One controlled desktop benchmark avoids duplicate large model loads.');
  const canvas = await landmark(page, 'tokyo-tower', '&renderBatching=off');
  await page.getByRole('button', { name: 'Front', exact: true }).click();
  await expect(canvas).toHaveScreenshot('tokyo-front.png');
  const before = Number(await canvas.getAttribute('data-render-calls'));
  const originalPixels = await canvas.screenshot();
  await landmark(page); await page.getByRole('button', { name: 'Front', exact: true }).click();
  await expect(canvas).toHaveScreenshot('tokyo-front.png');
  const after = Number(await canvas.getAttribute('data-render-calls')); expect(after).toBeLessThan(before * .8);
  const batchedPixels = await canvas.screenshot();
  const difference = await page.evaluate(async ({ a, b }) => {
    async function pixels(source: string) {
      const img = new Image(); img.src = `data:image/png;base64,${source}`; await img.decode();
      const c = document.createElement('canvas'); c.width = img.naturalWidth; c.height = img.naturalHeight;
      const ctx = c.getContext('2d')!; ctx.drawImage(img, 0, 0); return ctx.getImageData(0, 0, c.width, c.height).data;
    }
    const [one, two] = await Promise.all([pixels(a), pixels(b)]);
    if (one.length !== two.length) return 1;
    let changed = 0;
    for (let i = 0; i < one.length; i += 4) if (Math.max(...[0, 1, 2, 3].map(j => Math.abs(one[i + j] - two[i + j]))) > 12) changed++;
    return changed / (one.length / 4);
  }, { a: originalPixels.toString('base64'), b: batchedPixels.toString('base64') });
  expect(difference).toBeLessThan(.001);
  await info.attach('batching-comparison', { body: JSON.stringify({ before, after, unit: 'actual WebGL renderer.info.render.calls; same front view and default micro mode' }), contentType: 'application/json' });
});

test('model network failure can be retried without a page reload', async ({ page }) => {
  await page.route('**/GLB/tokyo_tower.glb*', route => route.fulfill({ status: 503, body: 'Temporary test failure' }));
  await page.goto('?model=tokyo-tower&view=3d');
  await expect(page.locator('.landmark-canvas [role="alert"]')).toBeVisible();
  await page.unroute('**/GLB/tokyo_tower.glb*');
  await page.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.locator('.landmark-canvas canvas')).toHaveAttribute('data-model-ready', 'true');
  await expect(page.locator('.landmark-canvas [role="alert"]')).toHaveCount(0);
});

test('invalid and corrupt photos are rejected locally', async ({ page }) => {
  await landmark(page); await page.getByText('Compare a photo', { exact: true }).click();
  const input = page.getByLabel('Choose reference image', { exact: true });
  await input.setInputFiles({ name: 'not-a-photo.svg', mimeType: 'image/svg+xml', buffer: Buffer.from('<svg/>') });
  await expect(page.locator('.reference-compare [role="alert"]')).toBeVisible();
  await expect(page.locator('.reference-image-overlay')).toHaveCount(0);
  await input.setInputFiles({ name: 'corrupt.png', mimeType: 'image/png', buffer: Buffer.from('not a PNG') });
  await expect(page.locator('.reference-compare [role="alert"]')).toBeVisible();
  await expect(page.locator('.reference-image-overlay')).toHaveCount(0);
});

test('chunked STEP download reconstructs the exact native CAD bytes', async ({ page }, info) => {
  test.skip(info.project.name === 'mobile', 'Full 209 MB native download is verified once.');
  await landmark(page); await page.getByRole('button', { name: 'Downloads', exact: true }).click();
  const parts: string[] = []; page.on('request', r => { if (r.url().includes('tokyo_tower.step.gz.part-')) parts.push(r.url()); });
  const pending = page.waitForEvent('download'); await page.locator('[data-file="STEP/tokyo_tower.step"] .download-row').click();
  const download = await pending; expect(download.suggestedFilename()).toBe('tokyo_tower.step');
  const path = await download.path(); expect(path).not.toBeNull();
  const hash = createHash('sha256'); for await (const chunk of createReadStream(path!)) hash.update(chunk);
  const manifest = JSON.parse(await readFile(new URL('../public/artifacts/manifest.json', import.meta.url), 'utf8'));
  expect(hash.digest('hex')).toBe(manifest['STEP/tokyo_tower.step'].sha256);
  expect(new Set(parts.map(url => new URL(url).pathname)).size).toBe(2);
});
