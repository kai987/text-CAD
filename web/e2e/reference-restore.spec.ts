import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

async function comparison(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    localStorage.setItem('text-cad.locale', 'en'); localStorage.setItem('text-cad.theme', 'light');
  });
  await page.goto('./?model=tokyo-tower&view=3d');
  const canvas = page.locator('.landmark-canvas canvas[data-model-ready="true"]');
  await expect(canvas).toBeVisible();
  await page.getByRole('button', { name: 'Front', exact: true }).click();
  await page.getByText('Compare a photo', { exact: true }).click();
  const photo = await canvas.screenshot();
  await page.getByLabel('Choose reference image', { exact: true }).setInputFiles({ name: 'same-photo.png', mimeType: 'image/png', buffer: photo });
  await expect(page.getByLabel('Load comparison settings', { exact: true })).toBeEnabled();
  return { canvas, photo };
}
async function exportedRecord(page: import('@playwright/test').Page) {
  const pending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save comparison settings', exact: true }).click();
  const download = await pending;
  return JSON.parse(await readFile((await download.path())!, 'utf8'));
}

test('comparison JSON restores the exact photo alignment, camera framing and paired point measurements', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  const { canvas } = await comparison(page);
  await page.getByRole('button', { name: 'Add matching reference points', exact: true }).click();
  await page.locator('.reference-point-picker').focus(); await page.locator('.reference-point-picker').press('Enter');
  await page.getByRole('button', { name: 'Side', exact: true }).click();
  await expect(page.locator('.reference-point-picker')).toHaveCount(0);
  await expect(page.getByText('The view or viewport changed, so the reference points were cleared.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Front', exact: true }).click();
  await page.getByRole('button', { name: 'Add matching reference points', exact: true }).click();
  const picker = page.locator('.reference-point-picker');
  await picker.focus(); await picker.press('Enter');
  await expect(picker).toHaveAccessibleName('Click the matching point on the model.');
  await picker.press('ArrowRight'); await picker.press('ArrowRight'); await picker.press('Enter');
  await expect(page.locator('.reference-point-overlay')).toHaveAttribute('data-anchor-count', '1');
  const before = await exportedRecord(page);
  expect(before.schema_version).toBe(2);
  expect(before.anchor_points).toHaveLength(1);
  expect(before.camera.pose.verticalSpan).toBeGreaterThan(0);
  await page.getByLabel('Horizontal position', { exact: false }).press('ArrowRight');
  await page.getByRole('button', { name: 'Side', exact: true }).click();
  await expect(page.locator('.reference-point-overlay')).toHaveCount(0);
  await page.getByLabel('Overlay reference image', { exact: true }).uncheck();
  await page.getByLabel('Load comparison settings', { exact: true }).setInputFiles({
    name: 'comparison.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(before)),
  });
  await expect(page.getByText('Restored the photo alignment and camera.', { exact: true })).toBeVisible();
  await expect(canvas).toHaveAttribute('data-camera-view', 'front');
  await expect(page.getByLabel('Overlay reference image', { exact: true })).toBeChecked();
  await expect(page.locator('.reference-image-overlay img')).toHaveAttribute('style', /translate\(0%, 0%\)/);
  await expect(page.locator('.reference-point-overlay')).toHaveAttribute('data-anchor-count', '1');
  const after = await exportedRecord(page);
  expect(after.alignment).toEqual(before.alignment);
  expect(after.anchor_points).toEqual(before.anchor_points);
  for (const field of ['zoom', 'verticalSpan'] as const) expect(after.camera.pose[field]).toBeCloseTo(before.camera.pose[field], 6);
  for (const field of ['position', 'target'] as const) after.camera.pose[field].forEach((n: number, i: number) => expect(n).toBeCloseTo(before.camera.pose[field][i], 6));
  const invalid = { ...before, model: 'tokyo-skytree' };
  await page.getByLabel('Load comparison settings', { exact: true }).setInputFiles({ name: 'wrong-model.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(invalid)) });
  await expect(page.locator('.reference-compare [role="alert"]')).toHaveText('The saved model ID does not match the current model.');
  expect((await exportedRecord(page)).alignment).toEqual(before.alignment);
  expect(errors).toEqual([]);
});

test('a pending comparison import cannot overwrite a newly selected photograph', async ({ page }) => {
  await page.addInitScript(() => {
    const original = File.prototype.text;
    File.prototype.text = function () {
      const result = original.call(this);
      if (this.name !== 'slow-comparison.json') return result;
      return result.then(text => new Promise<string>(resolve => {
        (window as unknown as { releaseComparison: () => void }).releaseComparison = () => resolve(text);
      }));
    };
  });
  const { canvas } = await comparison(page);
  await page.getByLabel('Horizontal position', { exact: false }).press('ArrowRight');
  const before = await exportedRecord(page);
  await page.getByLabel('Load comparison settings', { exact: true }).setInputFiles({ name: 'slow-comparison.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(before)) });
  await page.waitForFunction(() => typeof (window as unknown as { releaseComparison?: unknown }).releaseComparison === 'function');
  await page.getByRole('button', { name: 'Side', exact: true }).click();
  const newPhoto = await canvas.screenshot();
  await page.getByLabel('Choose reference image', { exact: true }).setInputFiles({ name: 'new-photo.png', mimeType: 'image/png', buffer: newPhoto });
  await expect(page.getByText('new-photo.png', { exact: true })).toBeVisible();
  await page.evaluate(() => (window as unknown as { releaseComparison: () => void }).releaseComparison());
  await expect(canvas).toHaveAttribute('data-camera-view', 'side');
  const current = await exportedRecord(page);
  expect(current.reference.name).toBe('new-photo.png');
  expect(current.reference.sha256).not.toBe(before.reference.sha256);
  expect(current.alignment.x).toBe(0);
  await expect(page.getByText('Restored the photo alignment and camera.', { exact: true })).toHaveCount(0);
});

test('recreating the viewer clears old camera points while retaining the selected photo', async ({ page }) => {
  const { canvas } = await comparison(page);
  await page.getByRole('button', { name: 'Add matching reference points', exact: true }).click();
  const picker = page.locator('.reference-point-picker');
  await picker.focus(); await picker.press('Enter'); await picker.press('Enter');
  await expect(page.locator('.reference-point-overlay')).toHaveAttribute('data-anchor-count', '1');
  await canvas.dispatchEvent('webglcontextlost', { cancelable: true });
  await expect(page.getByRole('button', { name: 'Retry', exact: true })).toBeVisible();
  await expect(page.locator('.reference-point-overlay')).toHaveCount(0);
  await page.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.locator('.landmark-canvas canvas[data-model-ready="true"]')).toBeVisible();
  await expect(page.getByText('same-photo.png', { exact: true })).toBeVisible();
  expect((await exportedRecord(page)).anchor_points).toEqual([]);
});

test('cross-revision conditions require explicit confirmation, clear old model points and retain their origin on export', async ({ page }) => {
  await comparison(page);
  const current = await exportedRecord(page);
  const prior = { ...current, revision: 'LANDMARK-R10', model_sha256: 'c'.repeat(64),
    alignment: { ...current.alignment, x: 18 },
    anchor_points: [{ reference: { x: .5, y: .5 }, model: { x: .6, y: .5 } }],
  };
  await page.getByLabel('Load comparison settings', { exact: true }).setInputFiles({ name: 'prior-revision.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(prior)) });
  const confirm = page.getByRole('button', { name: 'Apply photo and camera conditions to this model', exact: true });
  await expect(confirm).toBeVisible();
  expect((await exportedRecord(page)).alignment.x).toBe(0);
  await confirm.click();
  await expect(page.getByText('Applied conditions from another revision. Select fresh model points.', { exact: true })).toBeVisible();
  const adapted = await exportedRecord(page);
  expect(adapted.revision).toBe(current.revision);
  expect(adapted.model_sha256).toBe(current.model_sha256);
  expect(adapted.comparison_origin).toEqual({ revision: 'LANDMARK-R10', model_sha256: 'c'.repeat(64) });
  expect(adapted.anchor_points).toEqual([]);
  expect(adapted.alignment.x).toBe(18);
});
